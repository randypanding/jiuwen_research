"""Spec<->code traceability and drift detection (H7).

Three-stage funnel, cheapest first (research 05 / rec_05):

    L0 anchor resolution   -> does the anchor still point at code?
    L1 digest comparison   -> did the anchored code change since the spec did?
    L2 structural analysis -> did the *contract-bearing* structure change?
    L3 semantic analysis   -> escalation hook, off by default

Stage L3 is a hook, not an implementation: DocPrism-style semantic drift needs a
model, and a model's opinion may veto but never admit. The default engine runs
L0-L2 only and is fully deterministic.

Two failure modes are treated as *different*, because the fixes are different:
an **orphan** clause (spec text with no code) means the work was not done; a
**stale** anchor (code changed under a clause) means the spec was not updated.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterable, Mapping, Sequence

from ..contracts.base import digest_of
from ..contracts.spec import Anchor, Clause, SpecDocument

__all__ = [
    "DriftKind",
    "DriftFinding",
    "TraceabilityEngine",
    "AnchorResolver",
    "Exemption",
]

ANCHOR_COMMENT = re.compile(r"@spec[:\s]+([A-Za-z0-9._\-]+)")


class DriftKind(str, Enum):
    ORPHAN_CLAUSE = "orphan_clause"
    """A clause binds no anchor at all: the contract exists only on paper."""

    DANGLING_ANCHOR = "dangling_anchor"
    """The anchor names a file/symbol that no longer exists."""

    STALE_ANCHOR = "stale_anchor"
    """Anchored code changed but the clause revision did not."""

    STRUCTURAL_DRIFT = "structural_drift"
    """The anchored symbol's signature changed while the clause stayed put."""

    UNANCHORED_CODE = "unanchored_code"
    """Contract-bearing code with no clause behind it: undeclared surface."""

    SEMANTIC_DRIFT = "semantic_drift"
    """Escalation-only. Advisory unless a human confirms."""


_BLOCKING = {
    DriftKind.DANGLING_ANCHOR,
    DriftKind.STALE_ANCHOR,
    DriftKind.STRUCTURAL_DRIFT,
}


@dataclass(frozen=True)
class Exemption:
    """An exemption without an owner and an expiry is a permanent hole. Both
    fields are mandatory and the engine enforces expiry."""

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
    anchor_ref: str | None = None
    exempted: bool = False

    @property
    def blocking(self) -> bool:
        return (self.kind in _BLOCKING) and not self.exempted


class AnchorResolver:
    """Resolves an :class:`Anchor` against a snapshot of the codebase.

    ``sources`` maps a path to its text; ``symbols`` maps ``path::symbol`` to
    the symbol's normalised structural digest. Both are supplied by the caller
    so the engine is testable with no filesystem.
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
            return f"{anchor.path}::{anchor.symbol}" in self.symbols
        return True

    def content_digest(self, anchor: Anchor) -> str:
        if anchor.symbol:
            return digest_of(self.symbols.get(f"{anchor.path}::{anchor.symbol}", ""))
        return digest_of(self.sources.get(anchor.path, ""))

    def structural_digest(self, anchor: Anchor) -> str:
        if anchor.symbol:
            return self.symbols.get(f"{anchor.path}::{anchor.symbol}", "")
        return ""

    def anchored_symbols(self) -> set[str]:
        found: set[str] = set()
        for path, text in self.sources.items():
            for match in ANCHOR_COMMENT.finditer(text):
                found.add(match.group(1))
        return found


@dataclass
class TraceabilityEngine:
    resolver: AnchorResolver
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
        anchored_clause_ids: set[str] = set()

        for clause in spec.clauses:
            anchors = [a for a in spec.anchors if a.clause_id == clause.id]
            if not anchors:
                if clause.status.value in ("draft", "deprecated", "retired"):
                    continue
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
            anchored_clause_ids.add(clause.id)
            for anchor in anchors:
                ref = anchor.ref()
                if not self.resolver.exists(anchor):
                    findings.append(
                        DriftFinding(
                            kind=DriftKind.DANGLING_ANCHOR,
                            target=ref,
                            clause_id=clause.id,
                            anchor_ref=ref,
                            message=f"anchor {ref} does not resolve",
                            exempted=self._exempt(ref, DriftKind.DANGLING_ANCHOR),
                        )
                    )
                    continue
                current = self.resolver.content_digest(anchor)
                if anchor.code_digest and anchor.code_digest != current:
                    structural = self.resolver.structural_digest(anchor)
                    kind = (
                        DriftKind.STRUCTURAL_DRIFT
                        if anchor.structural_digest
                        and structural != anchor.structural_digest
                        else DriftKind.STALE_ANCHOR
                    )
                    findings.append(
                        DriftFinding(
                            kind=kind,
                            target=ref,
                            clause_id=clause.id,
                            anchor_ref=ref,
                            message=(
                                f"code behind {ref} changed but clause {clause.id} "
                                f"(revision {clause.revision()[:12]}) did not"
                            ),
                            exempted=self._exempt(ref, kind),
                        )
                    )
                elif self.semantic_check is not None:
                    if not self.semantic_check(clause, self.resolver.structural_digest(anchor)):
                        findings.append(
                            DriftFinding(
                                kind=DriftKind.SEMANTIC_DRIFT,
                                target=ref,
                                clause_id=clause.id,
                                anchor_ref=ref,
                                message="semantic drift suspected; advisory only",
                                exempted=self._exempt(ref, DriftKind.SEMANTIC_DRIFT),
                            )
                        )

        declared = {a.ref() for a in spec.anchors}
        for symbol in sorted(self.contract_bearing_symbols):
            if symbol not in declared:
                findings.append(
                    DriftFinding(
                        kind=DriftKind.UNANCHORED_CODE,
                        target=symbol,
                        message=(
                            f"{symbol} is contract-bearing but no clause claims it"
                        ),
                        exempted=self._exempt(symbol, DriftKind.UNANCHORED_CODE),
                    )
                )
        return findings

    def coverage(self, spec: SpecDocument) -> float:
        """Fraction of active clauses with at least one resolving anchor."""

        active = [c for c in spec.clauses if c.status.value == "active"]
        if not active:
            return 1.0
        anchored = {a.clause_id for a in spec.anchors if self.resolver.exists(a)}
        return sum(1 for c in active if c.id in anchored) / len(active)


def build_anchor(
    clause_id: str,
    path: str,
    symbol: str | None,
    resolver: AnchorResolver,
) -> Anchor:
    """Convenience for the spec-authoring tool: snapshot both digests now."""

    probe = Anchor(clause_id=clause_id, path=path, symbol=symbol)
    return Anchor(
        clause_id=clause_id,
        path=path,
        symbol=symbol,
        code_digest=resolver.content_digest(probe),
        structural_digest=resolver.structural_digest(probe),
    )


def anchors_from_source(
    sources: Iterable[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Scan source text for ``# @spec: L2-FOO-001`` markers."""

    out: list[tuple[str, str]] = []
    for path, text in sources:
        for match in ANCHOR_COMMENT.finditer(text):
            out.append((match.group(1), path))
    return out
