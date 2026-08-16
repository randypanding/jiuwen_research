"""Wave, fan-out and receipt contracts — PDR-001 §9 and §6.

A wave is redefined by the paradigm as *interface freeze window + independently
verifiable spec-delta cut + one admission transaction boundary*. All three are
represented explicitly so that a leader has nothing left to improvise.
"""

from __future__ import annotations

import math
from datetime import datetime
from enum import Enum

from pydantic import Field, model_validator

from .base import ArtifactClass, Contract, Role, utcnow
from .instance import DivergenceVerdict
from .spec import RLevel


class UncertaintySignal(Contract):
    """Inputs to adaptive fan-out. N is a measurement parameter, not a constant
    (PDR-001 §6, bounding failure mode G5 = token cost)."""

    ARTIFACT_CLASS = ArtifactClass.WAVE_MANIFEST

    novel_domain: bool = False
    new_clause_count: int = 0
    historical_rework_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    blast_radius: int = Field(default=0, ge=0, description="Downstream consumer count.")
    r_level: RLevel = RLevel.R0
    prior_verdict: DivergenceVerdict | None = None

    def score(self) -> float:
        """Bounded [0, 1] uncertainty score. Deterministic and unit-testable."""

        s = 0.0
        s += 0.25 if self.novel_domain else 0.0
        s += 0.20 * min(self.new_clause_count / 5.0, 1.0)
        s += 0.20 * self.historical_rework_rate
        s += 0.15 * min(self.blast_radius / 5.0, 1.0)
        s += {"R0": 0.0, "R1": 0.05, "R2": 0.10, "R3": 0.20}[self.r_level.value]
        if self.prior_verdict in (
            DivergenceVerdict.SILENCE,
            DivergenceVerdict.AMBIGUITY,
        ):
            s += 0.20
        return min(s, 1.0)


class FanoutPlan(Contract):
    """How many independent instances to sample, and why."""

    ARTIFACT_CLASS = ArtifactClass.WAVE_MANIFEST

    unit_id: str
    n: int = Field(ge=1)
    reason: str = ""
    signal: UncertaintySignal = Field(default_factory=UncertaintySignal)
    audit_sample: bool = Field(
        default=False,
        description="Periodic N>=3 calibration run on an otherwise N=1 unit.",
    )

    @classmethod
    def decide(
        cls, unit_id: str, signal: UncertaintySignal, *, audit_sample: bool = False
    ) -> "FanoutPlan":
        """The single, closed decision function for N.

        R3 never fans out (§5: frozen artefacts forbid re-sampling). Audit
        samples force N>=3 so that spec entropy is measurable even on units that
        normally run N=1.
        """

        if signal.r_level is RLevel.R3:
            return cls(
                unit_id=unit_id, n=1, reason="R3 frozen: fan-out forbidden", signal=signal
            )
        score = signal.score()
        if audit_sample:
            n = max(3, math.ceil(1 + 4 * score))
            return cls(
                unit_id=unit_id,
                n=n,
                reason=f"audit sample, score={score:.2f}",
                signal=signal,
                audit_sample=True,
            )
        if score < 0.25:
            n = 1
        elif score < 0.55:
            n = 3
        elif score < 0.8:
            n = 5
        else:
            n = 7
        return cls(unit_id=unit_id, n=n, reason=f"score={score:.2f}", signal=signal)

    @model_validator(mode="after")
    def _r3_never_fans_out(self) -> "FanoutPlan":
        if self.signal.r_level is RLevel.R3 and self.n > 1:
            raise ValueError("R3 artefacts must never be fanned out (PDR-001 §5)")
        return self


class PipelineKind(str, Enum):
    """The two physically separated pipelines of PDR-001 §7."""

    DELIVERY = "A"
    """Goal: admit one instance."""
    CALIBRATION = "B"
    """Goal: reduce spec entropy. All code is discarded, even on success."""


class WaveStatus(str, Enum):
    PLANNED = "planned"
    FROZEN = "frozen"
    RUNNING = "running"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"


class WaveManifest(Contract):
    """Interface freeze window + spec-delta cut + transaction boundary."""

    ARTIFACT_CLASS = ArtifactClass.WAVE_MANIFEST
    CONTRACT_VERSION = "1.0.0"

    wave_id: str
    pipeline: PipelineKind = PipelineKind.DELIVERY
    spec_id: str
    spec_version: str
    delta_ids: list[str] = Field(default_factory=list)
    unit_ids: list[str] = Field(default_factory=list)
    frozen_surface_digest: str = Field(
        description="The interface horizon. Any change to it inside the window "
        "invalidates every in-flight instance."
    )
    fanout: list[FanoutPlan] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list, description="Upstream wave ids.")
    status: WaveStatus = WaveStatus.PLANNED
    checkpoint_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    @model_validator(mode="after")
    def _fanout_covers_units(self) -> "WaveManifest":
        planned = {f.unit_id for f in self.fanout}
        missing = set(self.unit_ids) - planned
        if missing:
            raise ValueError(f"units without a fan-out plan: {sorted(missing)}")
        if self.pipeline is PipelineKind.CALIBRATION and self.status is WaveStatus.COMMITTED:
            raise ValueError(
                "pipeline B never commits code; a calibration wave that reaches "
                "COMMITTED has merged the two pipelines (PDR-001 §7)"
            )
        return self


class EvidenceReceipt(Contract):
    """The redefined PR (PDR-001 §9): an admission transaction + evidence.

    Kept *not* because anyone reviews it, but for atomicity, rollback and audit.
    Everything a future auditor needs to reconstruct the decision must be here,
    because the code that produced it may no longer exist.
    """

    ARTIFACT_CLASS = ArtifactClass.EVIDENCE_RECEIPT
    CONTRACT_VERSION = "1.0.0"

    receipt_id: str
    wave_id: str
    unit_id: str
    r_level: RLevel
    spec_id: str
    spec_version: str
    delta_ids: list[str] = Field(default_factory=list)

    selected_instance_id: str | None = None
    discarded_instance_ids: list[str] = Field(default_factory=list)
    differential_report_id: str | None = None
    differential_verdict: DivergenceVerdict | None = None

    hard_gate_digest: str | None = None
    soft_gate_digest: str | None = None
    drift_clean: bool = False
    admitted: bool = False

    human_approval_by: str | None = None
    human_approval_reason: str | None = None

    produced_at: datetime = Field(default_factory=utcnow)
    produced_by: Role = Role.VERIFIER

    @model_validator(mode="after")
    def _receipt_completeness(self) -> "EvidenceReceipt":
        if self.admitted:
            if not self.selected_instance_id:
                raise ValueError("an admitted receipt must name the selected instance")
            if not self.hard_gate_digest:
                raise ValueError("an admitted receipt must reference the hard gate report")
            if not self.drift_clean:
                raise ValueError(
                    "admission with unresolved spec drift is forbidden "
                    "(constitution §10)"
                )
            if self.r_level.requires_human_approval and not self.human_approval_by:
                raise ValueError(
                    f"{self.r_level.value} requires explicit human approval "
                    "(PDR-001 §5)"
                )
        if self.discarded_instance_ids and not self.differential_report_id:
            raise ValueError(
                "discarded instances must leave their measurement behind "
                "(constitution §2)"
            )
        return self
