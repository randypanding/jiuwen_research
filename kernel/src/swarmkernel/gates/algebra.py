"""Admission algebra: ``Admit = H and S``.

This module is thirty lines of logic guarding the single most important
decision in the platform. It is written as a standalone pure function so that
it can be proved, property-tested, and read by a human in one sitting.

Two properties are enforced and tested exhaustively:

* **Monotonicity of the veto.** For any hard report ``H`` and soft verdict
  ``S``, ``admit(H, VETO) == False``. The soft gate can only ever remove.
* **No rescue.** For any ``S``, if ``H`` is not fully passed then
  ``admit(H, S) == False``. Nothing outside the hard gates can create
  admissibility.
"""

from __future__ import annotations

from typing import Sequence

from ..contracts.gate import (
    AdmissionDecision,
    GateId,
    GateResult,
    HardGateReport,
    SoftGateResult,
    SoftVerdict,
)
from ..contracts.spec import RLevel

__all__ = ["REQUIRED_GATES_BY_RLEVEL", "build_hard_report", "admit", "decide"]


#: Which hard gates are mandatory at each regenerability level.
#:
#: H5 is meaningless for R0 (no fan-out, nothing to compare against), and R3
#: additionally requires the golden path inside H5. Everything else is required
#: everywhere: a gate that is optional is a gate that is off.
REQUIRED_GATES_BY_RLEVEL: dict[RLevel, frozenset[GateId]] = {
    RLevel.R0: frozenset({GateId.H1_BUILD, GateId.H2_UNIT_PROPERTY, GateId.H3_HOLDOUT, GateId.H4_SURFACE, GateId.H6_INVARIANT, GateId.H7_DRIFT, GateId.H8_BUDGET}),
    RLevel.R1: frozenset({GateId.H1_BUILD, GateId.H2_UNIT_PROPERTY, GateId.H3_HOLDOUT, GateId.H4_SURFACE, GateId.H5_DIFFERENTIAL, GateId.H6_INVARIANT, GateId.H7_DRIFT, GateId.H8_BUDGET}),
    RLevel.R2: frozenset({GateId.H1_BUILD, GateId.H2_UNIT_PROPERTY, GateId.H3_HOLDOUT, GateId.H4_SURFACE, GateId.H5_DIFFERENTIAL, GateId.H6_INVARIANT, GateId.H7_DRIFT, GateId.H8_BUDGET}),
    RLevel.R3: frozenset({GateId.H1_BUILD, GateId.H2_UNIT_PROPERTY, GateId.H3_HOLDOUT, GateId.H4_SURFACE, GateId.H5_DIFFERENTIAL, GateId.H6_INVARIANT, GateId.H7_DRIFT, GateId.H8_BUDGET}),
}


def build_hard_report(
    unit_id: str,
    instance_id: str,
    results: Sequence[GateResult],
    r_level: RLevel,
) -> HardGateReport:
    return HardGateReport(
        unit_id=unit_id,
        instance_id=instance_id,
        results=list(results),
        required=sorted(REQUIRED_GATES_BY_RLEVEL[r_level], key=lambda g: g.value),
    )


def admit(hard: HardGateReport, soft: SoftGateResult | None) -> bool:
    """The whole decision. ``None`` soft result means the soft gate did not run,
    which is not a veto — but it is also not a pass, because it cannot be: only
    the hard report can produce admissibility."""

    if not hard.passed:
        return False
    if soft is not None and soft.verdict is SoftVerdict.VETO:
        return False
    return True


def decide(
    *,
    unit_id: str,
    instance_id: str,
    wave_id: str,
    r_level: RLevel,
    results: Sequence[GateResult],
    soft: SoftGateResult | None,
    human_approved: bool = False,
) -> AdmissionDecision:
    hard = build_hard_report(unit_id, instance_id, results, r_level)
    admitted = admit(hard, soft)

    reasons: list[str] = []
    if not hard.passed:
        missing = sorted(g.value for g in hard.missing_gates())
        failed = sorted(r.gate_id.value for r in hard.failures())
        if missing:
            reasons.append(f"hard gates never ran: {missing}")
        if failed:
            reasons.append(f"hard gates failed: {failed}")
    if soft is not None and soft.verdict is SoftVerdict.VETO:
        reasons.append(
            "soft gate vetoed: "
            + "; ".join(
                sorted({c for s in soft.vetoes() for c in s.citations}) or ["<uncited>"]
            )
        )
    if admitted and r_level.requires_human_approval and not human_approved:
        # Not a veto and not a gate failure: a governance precondition. It is
        # applied *after* the algebra so that the algebra stays a pure
        # conjunction and remains provable.
        admitted = False
        reasons.append(
            f"{r_level.value} requires recorded human approval before admission"
        )

    return AdmissionDecision(
        unit_id=unit_id,
        instance_id=instance_id,
        wave_id=wave_id,
        hard_report=hard,
        soft_result=soft,
        admitted=admitted,
        reasons=reasons,
        human_approved=human_approved,
    )
