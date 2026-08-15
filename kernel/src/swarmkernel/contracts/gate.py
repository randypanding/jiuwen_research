"""Gate & admission contracts — PDR-001 §8, the gate algebra.

``Admit(instance) = H(instance) ∧ S(instance)``

The central design constraint: **a soft gate must not be able to admit
anything, ever.** Rather than documenting that, the types make it unsayable —
:class:`SoftVerdict` has no ``PASS`` member. Its only values are ``VETO``,
``NO_VETO`` and ``ABSTAIN``, and :func:`swarmkernel.gates.algebra.admit`
computes the conjunction from a hard report that has no access to soft results.
There is no code path through which a soft result can raise a hard failure.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from .base import ArtifactClass, Contract, Role, utcnow


class GateStatus(str, Enum):
    """Hard gate outcome. ``ERROR`` is a failure, never a skip."""

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    """The gate could not run. Treated as FAIL: an unrunnable gate is not a gate."""
    NOT_APPLICABLE = "not_applicable"
    """Declared inapplicable by the R-level registry, not by the instance."""

    @property
    def admits(self) -> bool:
        return self in (GateStatus.PASS, GateStatus.NOT_APPLICABLE)


class GateId(str, Enum):
    H1_BUILD = "H1"
    H2_UNIT_PROPERTY = "H2"
    H3_HOLDOUT = "H3"
    H4_SURFACE = "H4"
    H5_DIFFERENTIAL = "H5"
    H6_INVARIANT = "H6"
    H7_DRIFT = "H7"
    H8_BUDGET = "H8"
    S_JUDGE = "S"

    @property
    def is_hard(self) -> bool:
        return self is not GateId.S_JUDGE


class Finding(Contract):
    """One concrete, citable reason. Every failure must produce at least one."""

    ARTIFACT_CLASS = ArtifactClass.GATE_REPORT

    code: str = Field(description="Stable machine code, e.g. 'H4.SYMBOL_REMOVED'.")
    message: str
    clause_ids: list[str] = Field(default_factory=list)
    location: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    severity: str = Field(default="error", description="error | warning | info")


class GateResult(Contract):
    """Result of one hard gate on one instance."""

    ARTIFACT_CLASS = ArtifactClass.GATE_REPORT

    gate: GateId
    status: GateStatus
    findings: list[Finding] = Field(default_factory=list)
    duration_ms: float = 0.0
    detail: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _failure_must_be_explained(self) -> "GateResult":
        if self.status in (GateStatus.FAIL, GateStatus.ERROR) and not self.findings:
            raise ValueError(
                f"{self.gate.value} failed without a finding; an unexplained gate "
                "failure cannot be acted on and cannot enter an evidence receipt"
            )
        if not self.gate.is_hard:
            raise ValueError("GateResult carries hard gates only; use SoftGateResult")
        return self


class SoftVerdict(str, Enum):
    """Note the absence of a PASS member. This is intentional and load-bearing."""

    VETO = "veto"
    NO_VETO = "no_veto"
    ABSTAIN = "abstain"

    @property
    def vetoes(self) -> bool:
        return self is SoftVerdict.VETO


class JudgeSample(Contract):
    """One independent judge sample. Multiple samples are aggregated."""

    ARTIFACT_CLASS = ArtifactClass.JUDGE_VERDICT

    criterion_id: str
    verdict: SoftVerdict
    citation: str | None = None
    rationale: str = ""
    presentation_order: int = 0
    """Recorded so position-bias control can be audited after the fact."""

    @model_validator(mode="after")
    def _veto_needs_citation(self) -> "JudgeSample":
        if self.verdict is SoftVerdict.VETO and not self.citation:
            raise ValueError(
                "a veto without a citation is discarded (PDR-001 §8: judges must "
                "cite evidence)"
            )
        return self


class SoftGateResult(Contract):
    """Aggregated soft gate outcome. Can only ever remove an instance."""

    ARTIFACT_CLASS = ArtifactClass.JUDGE_VERDICT
    CONTRACT_VERSION = "1.0.0"

    gate: GateId = GateId.S_JUDGE
    verdict: SoftVerdict = SoftVerdict.NO_VETO
    samples: list[JudgeSample] = Field(default_factory=list)
    judge_model_tier: int = 1
    builder_model_tier: int = 1
    calibration_agreement: float | None = None
    abstention_rate: float = 0.0
    findings: list[Finding] = Field(default_factory=list)
    disabled_reason: str | None = Field(
        default=None,
        description="When calibration falls below threshold the soft gate is "
        "*disabled* (§13 downgrade 2) — which weakens nothing, because it can "
        "only veto.",
    )

    @model_validator(mode="after")
    def _judge_not_weaker_than_builder(self) -> "SoftGateResult":
        if self.judge_model_tier < self.builder_model_tier:
            raise ValueError(
                f"judge tier {self.judge_model_tier} < builder tier "
                f"{self.builder_model_tier}; constitution §14 forbids the "
                "discriminator being weaker than the generator"
            )
        return self


class HardGateReport(Contract):
    """The conjunction of all hard gates for one instance."""

    ARTIFACT_CLASS = ArtifactClass.GATE_REPORT
    CONTRACT_VERSION = "1.0.0"

    instance_id: str
    unit_id: str
    results: list[GateResult] = Field(default_factory=list)
    produced_at: datetime = Field(default_factory=utcnow)

    REQUIRED_GATES: tuple[GateId, ...] = ()

    def result(self, gate: GateId) -> GateResult | None:
        return next((r for r in self.results if r.gate is gate), None)

    @property
    def passed(self) -> bool:
        """Missing gate == not passed. Silence is never consent."""

        required = {g for g in GateId if g.is_hard}
        seen = {r.gate for r in self.results}
        if required - seen:
            return False
        return all(r.status.admits for r in self.results)

    @property
    def failures(self) -> list[GateResult]:
        return [r for r in self.results if not r.status.admits]

    @property
    def missing_gates(self) -> list[GateId]:
        seen = {r.gate for r in self.results}
        return sorted({g for g in GateId if g.is_hard} - seen, key=lambda g: g.value)


class AdmissionDecision(Contract):
    """The atomic admission transaction outcome (PDR-001 §9)."""

    ARTIFACT_CLASS = ArtifactClass.GATE_REPORT
    CONTRACT_VERSION = "1.0.0"

    instance_id: str
    unit_id: str
    admitted: bool
    hard_passed: bool
    soft_vetoed: bool
    reasons: list[Finding] = Field(default_factory=list)
    decided_at: datetime = Field(default_factory=utcnow)
    decided_by: Role = Role.VERIFIER

    @model_validator(mode="after")
    def _algebra_holds(self) -> "AdmissionDecision":
        """Structural restatement of ``Admit = H ∧ S``.

        Constructing an ``AdmissionDecision`` that violates the algebra raises.
        This means an out-of-band actor cannot forge an admission record even if
        it bypasses :func:`swarmkernel.gates.algebra.admit`.
        """

        expected = self.hard_passed and not self.soft_vetoed
        if self.admitted != expected:
            raise ValueError(
                f"admission algebra violated: hard_passed={self.hard_passed}, "
                f"soft_vetoed={self.soft_vetoed} implies admitted={expected}, "
                f"got {self.admitted}"
            )
        if not self.admitted and not self.reasons:
            raise ValueError("a rejection must carry at least one reason")
        return self
