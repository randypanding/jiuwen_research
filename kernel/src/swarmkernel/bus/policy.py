"""Information-asymmetry policy (PDR-001 §7).

The asymmetry rules are expressed as a **capability matrix over artefact
classes**, not as prompt text. A prompt asking an agent not to look at the
holdout is a request; a bus that refuses to deliver the holdout is a mechanism.

Two capabilities per (role, artefact class): ``READ`` and ``WRITE``. Absence is
denial — the matrix is a whitelist, so a newly added artefact class is
invisible to every role until someone deliberately grants it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..contracts.base import ArtifactClass as A
from ..contracts.base import Role as R

__all__ = ["Capability", "PolicyDecision", "AsymmetryPolicy", "DEFAULT_MATRIX"]


class Capability(str, Enum):
    READ = "read"
    WRITE = "write"


#: ``(role, artefact class) -> capabilities``.
#:
#: Design notes on the non-obvious cells:
#:
#: * ``BUILDER`` has **no** access to ``ORACLE_HOLDOUT`` in either direction.
#:   This is the single most important cell in the table.
#: * ``BUILDER`` cannot read ``JUDGE_VERDICT`` either: knowing how you are
#:   scored is enough to optimise for the score rather than the goal.
#: * ``VERIFIER`` cannot write ``SPEC_L2``. A verifier who can edit the contract
#:   can make any implementation correct by rewriting what correct means.
#: * ``JUDGE`` cannot read ``INSTANCE`` provenance beyond the anonymised report;
#:   it reads ``INSTANCE_REPORT`` (which forbids authorship hints) but not
#:   ``INSTANCE``.
#: * ``ARCHITECT`` writes L2 but cannot write ``ORACLE_HOLDOUT``: whoever
#:   defines the contract must not also define the secret exam.
#: * ``TEAM_MEMORY`` is writable only by ``SPEC_STEWARD`` and ``LEADER``:
#:   temporary builders write no memory (PDR-001 §7.3).
DEFAULT_MATRIX: dict[tuple[R, A], frozenset[Capability]] = {}


def _grant(role: R, artifact: A, *caps: Capability) -> None:
    DEFAULT_MATRIX[(role, artifact)] = frozenset(caps)


_RW = (Capability.READ, Capability.WRITE)
_RO = (Capability.READ,)

# --- human ------------------------------------------------------------------
for _a in A:
    _grant(R.HUMAN, _a, *_RW)

# --- leader -----------------------------------------------------------------
for _a in (
    A.CONSTITUTION, A.SPEC_L1, A.SPEC_L2, A.SPEC_DELTA, A.RLEVEL_REGISTRY,
    A.INTERFACE_SURFACE, A.INSTANCE_REPORT, A.GATE_REPORT, A.JUDGE_VERDICT,
    A.DIFFERENTIAL_REPORT, A.EVIDENCE_RECEIPT, A.HEALTH_METRICS, A.WAVE_MANIFEST,
):
    _grant(R.LEADER, _a, *_RO)
_grant(R.LEADER, A.WAVE_MANIFEST, *_RW)
_grant(R.LEADER, A.TEAM_MEMORY, *_RW)
_grant(R.LEADER, A.RULE_PROPOSAL, *_RO)

# --- architect --------------------------------------------------------------
_grant(R.ARCHITECT, A.CONSTITUTION, *_RO)
_grant(R.ARCHITECT, A.SPEC_L1, *_RO)
_grant(R.ARCHITECT, A.SPEC_L2, *_RW)
_grant(R.ARCHITECT, A.SPEC_DELTA, *_RW)
_grant(R.ARCHITECT, A.RLEVEL_REGISTRY, *_RW)
_grant(R.ARCHITECT, A.INTERFACE_SURFACE, *_RW)
_grant(R.ARCHITECT, A.ORACLE_PUBLIC, *_RO)
_grant(R.ARCHITECT, A.GATE_REPORT, *_RO)
_grant(R.ARCHITECT, A.DIFFERENTIAL_REPORT, *_RO)
_grant(R.ARCHITECT, A.WAVE_MANIFEST, *_RO)
_grant(R.ARCHITECT, A.RULE_PROPOSAL, *_RW)

# --- builder (the constrained role) ----------------------------------------
_grant(R.BUILDER, A.CONSTITUTION, *_RO)
_grant(R.BUILDER, A.SPEC_L1, *_RO)
_grant(R.BUILDER, A.SPEC_L2, *_RO)
_grant(R.BUILDER, A.SPEC_L3, *_RW)
_grant(R.BUILDER, A.SPEC_DELTA, *_RO)
_grant(R.BUILDER, A.RLEVEL_REGISTRY, *_RO)
_grant(R.BUILDER, A.INTERFACE_SURFACE, *_RO)
_grant(R.BUILDER, A.ORACLE_PUBLIC, *_RO)
_grant(R.BUILDER, A.INSTANCE, *_RW)
_grant(R.BUILDER, A.RULE_PROPOSAL, Capability.WRITE)
# Deliberately absent: ORACLE_HOLDOUT, JUDGE_VERDICT, DIFFERENTIAL_REPORT,
# INSTANCE_REPORT (other builders'), TEAM_MEMORY, GATE_REPORT of peers.

# --- verifier ---------------------------------------------------------------
_grant(R.VERIFIER, A.CONSTITUTION, *_RO)
_grant(R.VERIFIER, A.SPEC_L1, *_RO)
_grant(R.VERIFIER, A.SPEC_L2, *_RO)
_grant(R.VERIFIER, A.SPEC_DELTA, *_RO)
_grant(R.VERIFIER, A.RLEVEL_REGISTRY, *_RO)
_grant(R.VERIFIER, A.INTERFACE_SURFACE, *_RO)
_grant(R.VERIFIER, A.ORACLE_PUBLIC, *_RW)
_grant(R.VERIFIER, A.ORACLE_HOLDOUT, *_RW)
_grant(R.VERIFIER, A.INSTANCE, *_RO)
_grant(R.VERIFIER, A.INSTANCE_REPORT, *_RW)
_grant(R.VERIFIER, A.GATE_REPORT, *_RW)
_grant(R.VERIFIER, A.DIFFERENTIAL_REPORT, *_RW)
_grant(R.VERIFIER, A.EVIDENCE_RECEIPT, *_RW)
_grant(R.VERIFIER, A.RULE_PROPOSAL, Capability.WRITE)

# --- judge ------------------------------------------------------------------
_grant(R.JUDGE, A.CONSTITUTION, *_RO)
_grant(R.JUDGE, A.SPEC_L1, *_RO)
_grant(R.JUDGE, A.SPEC_L2, *_RO)
_grant(R.JUDGE, A.ORACLE_HOLDOUT, *_RO)
_grant(R.JUDGE, A.INSTANCE_REPORT, *_RO)
_grant(R.JUDGE, A.GATE_REPORT, *_RO)
_grant(R.JUDGE, A.JUDGE_VERDICT, *_RW)

# --- spec moderator / steward ----------------------------------------------
_grant(R.SPEC_MODERATOR, A.CONSTITUTION, *_RO)
_grant(R.SPEC_MODERATOR, A.SPEC_L1, *_RO)
_grant(R.SPEC_MODERATOR, A.SPEC_L2, *_RO)
_grant(R.SPEC_MODERATOR, A.SPEC_DELTA, *_RW)
_grant(R.SPEC_MODERATOR, A.RLEVEL_REGISTRY, *_RO)
_grant(R.SPEC_MODERATOR, A.RULE_PROPOSAL, *_RW)
_grant(R.SPEC_MODERATOR, A.HEALTH_METRICS, *_RO)

_grant(R.SPEC_STEWARD, A.SPEC_L1, *_RW)
_grant(R.SPEC_STEWARD, A.SPEC_L2, *_RW)
_grant(R.SPEC_STEWARD, A.SPEC_DELTA, *_RW)
_grant(R.SPEC_STEWARD, A.RLEVEL_REGISTRY, *_RW)
_grant(R.SPEC_STEWARD, A.TEAM_MEMORY, *_RW)
_grant(R.SPEC_STEWARD, A.CONSTITUTION, *_RO)

# --- supporting roles -------------------------------------------------------
for _role in (R.RECONCILER, R.CARTOGRAPHER, R.CRITIC, R.REFACTOR, R.MODERATOR, R.DEEP_AGENT):
    _grant(_role, A.CONSTITUTION, *_RO)
    _grant(_role, A.SPEC_L1, *_RO)
    _grant(_role, A.SPEC_L2, *_RO)
    _grant(_role, A.INTERFACE_SURFACE, *_RO)
    _grant(_role, A.RULE_PROPOSAL, Capability.WRITE)

_grant(R.RECONCILER, A.SPEC_L3, *_RW)
_grant(R.RECONCILER, A.INSTANCE, *_RW)
_grant(R.RECONCILER, A.DIFFERENTIAL_REPORT, *_RO)
_grant(R.CARTOGRAPHER, A.INTERFACE_SURFACE, *_RW)
_grant(R.CARTOGRAPHER, A.SPEC_L3, *_RO)
_grant(R.CRITIC, A.GATE_REPORT, *_RO)
_grant(R.CRITIC, A.INSTANCE_REPORT, *_RO)
_grant(R.REFACTOR, A.SPEC_L3, *_RW)
_grant(R.REFACTOR, A.INSTANCE, *_RW)
_grant(R.REFACTOR, A.ORACLE_PUBLIC, *_RO)
_grant(R.MODERATOR, A.HEALTH_METRICS, *_RW)
_grant(R.MODERATOR, A.RULE_PROPOSAL, *_RW)
_grant(R.DEEP_AGENT, A.HEALTH_METRICS, *_RO)
_grant(R.DEEP_AGENT, A.EVIDENCE_RECEIPT, *_RO)
_grant(R.DEEP_AGENT, A.RULE_PROPOSAL, *_RW)

del _a, _role


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str = ""

    def __bool__(self) -> bool:  # pragma: no cover - trivial
        return self.allowed


class AsymmetryPolicy:
    """Whitelist enforcement plus the four structural separations of §7.3."""

    def __init__(
        self,
        matrix: dict[tuple[R, A], frozenset[Capability]] | None = None,
        *,
        temporary_roles: frozenset[R] = frozenset({R.BUILDER, R.REFACTOR, R.RECONCILER}),
    ) -> None:
        self.matrix = dict(matrix if matrix is not None else DEFAULT_MATRIX)
        self.temporary_roles = temporary_roles

    def capabilities(self, role: R, artifact: A) -> frozenset[Capability]:
        return self.matrix.get((role, artifact), frozenset())

    def can(self, role: R, artifact: A, capability: Capability) -> PolicyDecision:
        caps = self.capabilities(role, artifact)
        if capability in caps:
            return PolicyDecision(True)
        return PolicyDecision(
            False,
            f"role {role.value!r} has no {capability.value} capability on "
            f"artefact class {artifact.value!r}",
        )

    def can_read(self, role: R, artifact: A) -> PolicyDecision:
        return self.can(role, artifact, Capability.READ)

    def can_write(self, role: R, artifact: A) -> PolicyDecision:
        if artifact is A.TEAM_MEMORY and role in self.temporary_roles:
            return PolicyDecision(
                False,
                f"temporary role {role.value!r} may not write team memory "
                "(PDR-001 §7.3): a role that dissolves cannot own durable claims",
            )
        return self.can(role, artifact, Capability.WRITE)

    # -- structural separations ---------------------------------------------

    def check_separation(
        self,
        *,
        sender_role: R,
        sender_identity: str,
        recipient_role: R | None,
        recipient_identity: str | None,
        artifact: A,
        subject_identity: str | None = None,
    ) -> PolicyDecision:
        """Identity-level rules that the capability matrix cannot express."""

        if (
            artifact is A.JUDGE_VERDICT
            and subject_identity is not None
            and sender_identity == subject_identity
        ):
            return PolicyDecision(
                False,
                "self-review: a judge may not evaluate an instance it authored",
            )
        # "Subject" is the agent the artefact is *about*, taken from the
        # envelope's addressee -- not the subscriber that happens to receive a
        # broadcast copy. Conflating the two would stop an author from ever
        # seeing its own broadcast, which is noise rather than separation.
        if (
            artifact in (A.ORACLE_HOLDOUT, A.ORACLE_PUBLIC)
            and sender_role is R.VERIFIER
            and subject_identity is not None
            and sender_identity == subject_identity
        ):
            return PolicyDecision(
                False, "the author of an oracle may not also be its subject"
            )
        if artifact is A.ORACLE_HOLDOUT and recipient_role is R.BUILDER:
            return PolicyDecision(
                False,
                "holdout oracle may never be routed to a builder (PDR-001 §7.1)",
            )
        return PolicyDecision(True)
