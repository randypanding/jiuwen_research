"""Admission algebra: ``Admit = H ∧ S``.

This module is a few dozen lines guarding the single most important decision in
the platform. It is written as a standalone pure function so that it can be
property-tested exhaustively and read by a human in one sitting.

Two properties are enforced and tested:

* **Monotonicity of the veto.** For any hard report ``H``, ``admit(H, VETO)``
  is False. The soft gate can only ever remove.
* **No rescue.** For any soft verdict ``S``, if ``H`` is not fully passed then
  ``admit(H, S)`` is False. Nothing outside the hard gates can create
  admissibility.
"""

from __future__ import annotations

from typing import Sequence

from ..contracts.base import Role
from ..contracts.gate import (
    AdmissionDecision,
    Finding,
    GateId,
    GateResult,
    HardGateReport,
    SoftGateResult,
    SoftVerdict,
)
from ..contracts.oracle import JudgeProtocol
from ..contracts.spec import RLevel

__all__ = ["REQUIRED_GATES", "build_hard_report", "admit", "decide"]


#: Every hard gate is required for every unit. There is no per-level opt-out:
#: a gate that is optional is a gate that is off. H5 stays required at R0 and
#: reports "not applicable" from inside the gate, so the *decision* to skip is
#: recorded as evidence instead of as an absence.
REQUIRED_GATES: tuple[GateId, ...] = tuple(
    sorted((g for g in GateId if g.is_hard), key=lambda g: g.value)
)


def build_hard_report(
    unit_id: str, instance_id: str, results: Sequence[GateResult]
) -> HardGateReport:
    return HardGateReport(
        unit_id=unit_id,
        instance_id=instance_id,
        results=list(results),
        REQUIRED_GATES=REQUIRED_GATES,
    )


def admit(hard: HardGateReport, soft: SoftGateResult | None) -> bool:
    """The whole decision.

    ``soft is None`` means the soft gate did not run. That is not a veto — and
    it is not a pass either, because a soft gate can never produce one. Only the
    hard report can make something admissible.
    """

    if not hard.passed:
        return False
    if soft is not None and soft.verdict is SoftVerdict.VETO:
        return False
    return True


def decide(
    *,
    unit_id: str,
    instance_id: str,
    r_level: RLevel,
    results: Sequence[GateResult],
    soft: SoftGateResult | None,
    human_approved: bool = False,
    judge_protocol: JudgeProtocol | None = None,
    decided_by: Role = Role.VERIFIER,
) -> AdmissionDecision:
    """Admission transaction, governance included.

    ``judge_protocol`` is the holdout oracle's protocol itself — the D6
    declaration is read straight from ``required_for_admission``, not mirrored
    through a boolean, so a harness cannot forget to forward it. When the
    protocol declares the soft gate mandatory and it did not run, the decision
    blocks with ``ADMIT.SOFT_GATE_MISSING``. When no protocol is supplied (or
    it declares the soft gate optional) a missing soft gate neither blocks nor
    rescues — only the hard report can make something admissible.
    """

    soft_required = (
        judge_protocol is not None and judge_protocol.required_for_admission
    )
    hard = build_hard_report(unit_id, instance_id, results)
    hard_passed = hard.passed
    soft_vetoed = soft is not None and soft.verdict is SoftVerdict.VETO
    soft_missing_declared_required = soft_required and soft is None
    admitted = admit(hard, soft) and not soft_missing_declared_required

    reasons: list[Finding] = []
    if not hard_passed:
        missing = [g.value for g in hard.missing_gates]
        if missing:
            reasons.append(
                Finding(
                    code="ADMIT.GATE_MISSING",
                    message=f"hard gates never ran: {missing}",
                )
            )
        for r in hard.failures:
            reasons.append(
                Finding(
                    code="ADMIT.GATE_FAILED",
                    message=f"{r.gate.value} {r.status.value}: "
                    + "; ".join(f.code for f in r.findings),
                    clause_ids=sorted({c for f in r.findings for c in f.clause_ids}),
                )
            )
    if soft_vetoed and soft is not None:
        citations = sorted(
            {s.citation for s in soft.samples if s.verdict is SoftVerdict.VETO and s.citation}
        )
        reasons.append(
            Finding(
                code="ADMIT.SOFT_VETO",
                message="soft gate vetoed: " + ("; ".join(citations) or "<uncited>"),
            )
        )
    if soft_missing_declared_required:
        reasons.append(
            Finding(
                code="ADMIT.SOFT_GATE_MISSING",
                message=(
                    "the judge protocol declares the soft gate required for "
                    "admission, but no soft-gate result was supplied (D6: the "
                    "declaration decides, not the runtime)"
                ),
            )
        )
        # Bookkeeping, not a measurement: the pure algebra (H ∧ S) stays intact
        # and the declared requirement is recorded as hard_passed=False purely
        # so the contract's algebra validator holds. The operational outcome
        # correctly reads INCONCLUSIVE — no hard gate measured a defect.
        hard_passed = False
        admitted = False

    if admitted and r_level.requires_human_approval and not human_approved:
        # A governance precondition, not a gate failure. It is applied after the
        # algebra so the algebra stays a pure conjunction and remains provable.
        # hard_passed=False is bookkeeping so the contract's algebra validator
        # holds; the outcome maps to INCONCLUSIVE (a pending signature is an
        # unfinished process, not a measured defect).
        hard_passed = False
        admitted = False
        reasons.append(
            Finding(
                code="ADMIT.HUMAN_APPROVAL_REQUIRED",
                message=(
                    f"{r_level.value} requires recorded human approval before "
                    "admission (PDR-001 §4)"
                ),
            )
        )

    return AdmissionDecision(
        unit_id=unit_id,
        instance_id=instance_id,
        admitted=admitted,
        hard_passed=hard_passed,
        soft_vetoed=soft_vetoed,
        reasons=reasons,
        decided_by=decided_by,
    )
