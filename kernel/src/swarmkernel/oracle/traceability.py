"""Spec<->code traceability and drift detection (H7).

Three-stage funnel, cheapest first (research 05):

    L0 anchor resolution   -> does the anchor still point at code?
    L1 digest comparison   -> did the anchored code change since the spec did?
    L2 structural analysis -> did the *contract-bearing* structure change?
    L3 semantic analysis   -> escalation hook, off by default

L3 is a hook, not an implementation: semantic drift detection needs a model, and
a model's opinion may veto but never admit. The default engine runs L0-L2 only
and is fully deterministic.

Two failure modes are kept distinct because their fixes are different: an
**orphan** clause (spec text with no code) means the work was not done; a
**stale** anchor (code changed under a clause) means the spec was not updated.

The drift baseline is passed in rather than stored on :class:`Anchor`. An
anchor that carried its own "expected digest" would let whoever edits the code
also edit the expectation in the same commit, which is exactly the drift the
gate exists to catch. The baseline is owned by the spec repository and is
updated only when a clause revision changes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterable, Mapping, Sequence

from ..contracts.base import digest_of
from ..contracts.spec import Anchor, Clause, ClauseStatus, SpecDocument

__all__ = [
    "DriftKind",
    "DriftFinding",
    "TraceabilityEngine",
    "AnchorResolver",
    "Exemption",
    "BLOCKING_KINDS",
    "build_baseline",
    "anchors_from_source",
]

ANCHOR_COMMENT = re.compile(r"@spec[:\s]+([A-Za-z0-9._\-]+)")


class DriftKind(str, Enum):
    ORPHAN_CLAUSE = "orphan_clause"
    """A clause binds no anchor at all: the contract exists only on paper."""

    DANGLING_ANCHOR = "dangling_anchor"
    """The anchor names a file/symbol that no longer exists."""

    STALE_ANCHOR = "stale_anchor"
    """Anchored file changed but the clause revision did not."""

    STRUCTURAL_DRIFT = "structural_drift"
    """The anchored symbol's contract-bearing structure changed."""

    UNANCHORED_CODE = "unanchored_code"
    """Contract-bearing code with no clause behind it: undeclared surface."""

    SEMANTIC_DRIFT = "semantic_drift"
    """Escalation-only. Advisory unless a human confirms."""


#: Kinds that block admission. ``ORPHAN_CLAUSE`` and ``UNANCHORED_CODE`` warn
#: first (research 05: warn-before-block, or the gate simply gets switched off).
BLOCKING_KINDS = frozenset(
    {DriftKind.DANGLING_ANCHOR, DriftKind.STALE_ANCHOR, DriftKind.STRUCTURAL_DRIFT}
)


@dataclass(frozen=True)
class Exemption:
    """An exemption without an owner and an expiry is a permanent hole. Both
    are mandatory and the engine enforces the expiry."""

    target: str
    kind: DriftKind
    owner: str
    expires_on: str
    reason: str

    def active(self, today: str) -> bool:
        return today <= self.expires_on


@dataclass(frozen=True)
class DriftFinding:
    kind: DriftKind
    target: str
    message: str
    clause_id: str | None = None
    exempted: bool = False

    @property
    def blocking(self) -> bool:
        return (self.kind in BLOCKING_KINDS) and not self.exempted


class AnchorResolver:
    """Resolves an :class:`Anchor` against a snapshot of the codebase.

    ``sources`` maps path -> file text. ``symbols`` maps ``path::symbol`` ->
    that symbol's normalised structural signature. Both are plain mappings, so
    the engine is testable with no filesystem and no VCS.
    """

    def __init__(
        self,
        sources: Mapping[str, str],
        symbols: Mapping[str, str] | None = None,
    ) -> None:
        self.sources = dict(sources)
        self.symbols = dict(symbols or {})

    def exists(self, anchor: Anchor) -> bool:
        if anchor.path not in self.sources:
            return False
        if anchor.symbol:
            return anchor.key() in self.symbols
        return True

    def content_digest(self, anchor: Anchor) -> str:
        if anchor.symbol:
            return digest_of(self.symbols.get(anchor.key(), ""))
        return digest_of(self.sources.get(anchor.path, ""))

    def structural_digest(self, anchor: Anchor) -> str:
        if anchor.symbol:
            return digest_of(self.symbols.get(anchor.key(), ""))
        return ""

    def declared_clause_ids(self) -> set[str]:
        """Clause ids referenced by ``# @spec: <id>`` markers in the sources."""

        found: set[str] = set()
        for text in self.sources.values():
            for match in ANCHOR_COMMENT.finditer(text):
                found.add(match.group(1))
        return found


def build_baseline(spec: SpecDocument, resolver: AnchorResolver) -> dict[str, str]:
    """Snapshot every anchor's digest. Called by spec tooling, never by CI."""

    out: dict[str, str] = {}
    for clause in spec.clauses:
        for anchor in clause.anchors:
            out[f"{clause.id}@{anchor.key()}"] = resolver.content_digest(anchor)
    return out


@dataclass
class TraceabilityEngine:
    resolver: AnchorResolver
    baseline: Mapping[str, str] = field(default_factory=dict)
    """``"<clause id>@<anchor key>" -> digest`` recorded when the clause was last
    revised. A key absent from the baseline means "never snapshotted", which is
    reported as un-checkable rather than silently treated as clean."""

    exemptions: Sequence[Exemption] = ()
    today: str = "1970-01-01"
    semantic_check: Callable[[Clause, str], bool] | None = None
    contract_bearing_symbols: set[str] = field(default_factory=set)

    def _exempt(self, target: str, kind: DriftKind) -> bool:
        return any(
            e.target == target and e.kind == kind and e.active(self.today)
            for e in self.exemptions
        )

    def expired_exemptions(self) -> list[Exemption]:
        return [e for e in self.exemptions if not e.active(self.today)]

    def check(self, spec: SpecDocument) -> list[DriftFinding]:
        findings: list[DriftFinding] = []

        for clause in spec.clauses:
            if clause.status is not ClauseStatus.ACTIVE:
                continue
            if not clause.anchors:
                findings.append(
                    DriftFinding(
                        kind=DriftKind.ORPHAN_CLAUSE,
                        target=clause.id,
                        clause_id=clause.id,
                        message=f"clause {clause.id} has no code anchor",
                        exempted=self._exempt(clause.id, DriftKind.ORPHAN_CLAUSE),
                    )
                )
                continue
            for anchor in clause.anchors:
                key = f"{clause.id}@{anchor.key()}"
                if not self.resolver.exists(anchor):
                    findings.append(
                        DriftFinding(
                            kind=DriftKind.DANGLING_ANCHOR,
                            target=key,
                            clause_id=clause.id,
                            message=f"anchor {anchor.key()} does not resolve",
                            exempted=self._exempt(key, DriftKind.DANGLING_ANCHOR),
                        )
                    )
                    continue
                recorded = self.baseline.get(key)
                current = self.resolver.content_digest(anchor)
                if recorded is not None and recorded != current:
                    kind = (
                        DriftKind.STRUCTURAL_DRIFT
                        if anchor.symbol
                        else DriftKind.STALE_ANCHOR
                    )
                    findings.append(
                        DriftFinding(
                            kind=kind,
                            target=key,
                            clause_id=clause.id,
                            message=(
                                f"code behind {anchor.key()} changed but clause "
                                f"{clause.id} (revision {clause.revision[:12]}) did not"
                            ),
                            exempted=self._exempt(key, kind),
                        )
                    )
                elif self.semantic_check is not None and recorded is not None:
                    if not self.semantic_check(
                        clause, self.resolver.structural_digest(anchor)
                    ):
                        findings.append(
                            DriftFinding(
                                kind=DriftKind.SEMANTIC_DRIFT,
                                target=key,
                                clause_id=clause.id,
                                message="semantic drift suspected; advisory only",
                                exempted=self._exempt(key, DriftKind.SEMANTIC_DRIFT),
                            )
                        )

        declared = {
            a.key()
            for c in spec.clauses
            if c.status is ClauseStatus.ACTIVE
            for a in c.anchors
        }
        for symbol in sorted(self.contract_bearing_symbols):
            if symbol not in declared:
                findings.append(
                    DriftFinding(
                        kind=DriftKind.UNANCHORED_CODE,
                        target=symbol,
                        message=f"{symbol} is contract-bearing but no clause claims it",
                        exempted=self._exempt(symbol, DriftKind.UNANCHORED_CODE),
                    )
                )
        return findings

    def coverage(self, spec: SpecDocument) -> float:
        """Fraction of active clauses with at least one *resolving* anchor."""

        active = [c for c in spec.clauses if c.status is ClauseStatus.ACTIVE]
        if not active:
            return 1.0
        ok = sum(1 for c in active if any(self.resolver.exists(a) for a in c.anchors))
        return ok / len(active)


def anchors_from_source(sources: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    """Scan source text for ``# @spec: L2-FOO-001`` markers.

    Used to cross-check that the code agrees with the spec about which clause
    governs it — drift can point in either direction.
    """

    out: list[tuple[str, str]] = []
    for path, text in sources:
        for match in ANCHOR_COMMENT.finditer(text):
            out.append((match.group(1), path))
    return out
