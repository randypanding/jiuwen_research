"""Governance contracts — health metrics, downgrade triggers, rule proposals.

PDR-001 §13 requires the paradigm to carry its own failure detection. These
types make the retreat conditions executable: :func:`HealthMetrics.downgrades`
returns the triggered downgrades, and a downgrade is always *a stage rollback*,
never a relaxation of the criteria.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field, model_validator

from .base import ArtifactClass, Contract, Role, utcnow


class MigrationStage(str, Enum):
    """PDR-001 §12. Per-domain, not global."""

    M0_HARVEST = "M0"
    M1_ANCHOR = "M1"
    M2_REGENERATE = "M2"
    M3_FACTORY = "M3"

    @property
    def index(self) -> int:
        return ["M0", "M1", "M2", "M3"].index(self.value)

    def previous(self) -> "MigrationStage":
        return MigrationStage(["M0", "M1", "M2", "M3"][max(self.index - 1, 0)])


class DowngradeTrigger(str, Enum):
    ESCAPED_DEFECTS = "escaped_defects"
    JUDGE_CALIBRATION = "judge_calibration"
    DRIFT_STORM = "drift_storm"
    COST_OVERRUN = "cost_overrun"
    ORACLE_CONFLICT = "oracle_conflict"


class HealthThresholds(Contract):
    """Frozen for a session. Changing these is a rule change, not an operation."""

    ARTIFACT_CLASS = ArtifactClass.HEALTH_METRICS

    max_escaped_defect_rate: float = Field(default=0.02, ge=0.0, le=1.0)
    min_judge_agreement: float = Field(default=0.80, ge=0.0, le=1.0)
    max_drift_alert_density: float = Field(
        default=0.15, description="Alerts per admitted unit per wave."
    )
    max_drift_repair_latency_h: float = 24.0
    max_cost_per_admission: float = Field(default=1.0, description="Normalised to budget.")
    min_closure_improvement: float = 0.0
    max_repeated_infeasible: int = 2
    min_witness_coverage_for_m1: float = 0.7
    min_witness_coverage_for_m2: float = 0.85


class HealthMetrics(Contract):
    """The full observable set of PDR-001 §13, plus the downgrade evaluation."""

    ARTIFACT_CLASS = ArtifactClass.HEALTH_METRICS
    CONTRACT_VERSION = "1.0.0"

    domain: str
    stage: MigrationStage = MigrationStage.M0_HARVEST
    window_waves: int = Field(default=1, ge=1)

    spec_closure: float = Field(default=0.0, ge=0.0, le=1.0)
    spec_entropy: float = Field(
        default=0.0, description="Silence+ambiguity events per spec-delta."
    )
    witness_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    unverifiable_clause_count: int = 0
    escaped_defect_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    drift_alert_density: float = 0.0
    drift_repair_latency_h: float = 0.0
    judge_calibration_agreement: float = Field(default=1.0, ge=0.0, le=1.0)
    judge_abstention_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    rework_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    cost_per_admission: float = 0.0
    closure_delta: float = 0.0
    repeated_infeasible_clauses: int = 0
    observed_at: datetime = Field(default_factory=utcnow)

    def downgrades(self, t: HealthThresholds) -> list[DowngradeTrigger]:
        """Evaluate §13's five retreat conditions. Any hit rolls the stage back."""

        hits: list[DowngradeTrigger] = []
        if self.escaped_defect_rate > t.max_escaped_defect_rate:
            hits.append(DowngradeTrigger.ESCAPED_DEFECTS)
        if self.judge_calibration_agreement < t.min_judge_agreement:
            hits.append(DowngradeTrigger.JUDGE_CALIBRATION)
        if (
            self.drift_alert_density > t.max_drift_alert_density
            and self.drift_repair_latency_h > t.max_drift_repair_latency_h
        ):
            hits.append(DowngradeTrigger.DRIFT_STORM)
        if (
            self.cost_per_admission > t.max_cost_per_admission
            and self.closure_delta <= t.min_closure_improvement
        ):
            hits.append(DowngradeTrigger.COST_OVERRUN)
        if self.repeated_infeasible_clauses > t.max_repeated_infeasible:
            hits.append(DowngradeTrigger.ORACLE_CONFLICT)
        return hits

    def next_stage(self, t: HealthThresholds) -> MigrationStage:
        """Downgrade is always a stage rollback, never a criterion change."""

        return self.stage.previous() if self.downgrades(t) else self.stage

    def may_advance_to(self, target: MigrationStage, t: HealthThresholds) -> bool:
        """Advancement preconditions of §12. Never skip a stage."""

        if target.index != self.stage.index + 1:
            return False
        if self.downgrades(t):
            return False
        if target is MigrationStage.M1_ANCHOR:
            return self.witness_coverage >= t.min_witness_coverage_for_m1
        if target is MigrationStage.M2_REGENERATE:
            return (
                self.witness_coverage >= t.min_witness_coverage_for_m2
                and self.escaped_defect_rate <= t.max_escaped_defect_rate
                and self.judge_calibration_agreement >= t.min_judge_agreement
            )
        if target is MigrationStage.M3_FACTORY:
            return (
                self.witness_coverage >= t.min_witness_coverage_for_m2
                and self.escaped_defect_rate == 0.0
                and self.spec_closure >= 0.9
            )
        return False


class ProposalKind(str, Enum):
    MODEL_TIER_POLICY = "model_tier_policy"
    RU_LEVEL_CHANGE = "ru_level_change"
    RULE_CHANGE = "rule_change"
    HARNESS_OPTIMISATION = "harness_optimisation"
    THRESHOLD_CHANGE = "threshold_change"


class RuleChangeProposal(Contract):
    """The only legal path for the system to change itself (constitution §6/§8).

    Deep agents propose; humans approve; changes take effect *in the next
    session*. ``effective_session_id`` must differ from ``observed_session_id``
    and that is checked here, not in a runbook.
    """

    ARTIFACT_CLASS = ArtifactClass.RULE_PROPOSAL
    CONTRACT_VERSION = "1.0.0"

    proposal_id: str
    kind: ProposalKind
    title: str
    motivation: str
    case_ids: list[str] = Field(
        default_factory=list,
        description="Concrete cases that produced consequences. Constitution §8: "
        "exceptions are never decided live; they become cases.",
    )
    proposed_change: dict = Field(default_factory=dict)
    proposed_by: Role = Role.DEEP_AGENT
    observed_session_id: str
    effective_session_id: str | None = None
    human_approved: bool = False
    approved_by: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    @model_validator(mode="after")
    def _no_self_activation(self) -> "RuleChangeProposal":
        if self.proposed_by not in (Role.DEEP_AGENT, Role.SPEC_STEWARD, Role.HUMAN):
            raise ValueError(
                f"{self.proposed_by.value} may not propose rule changes; only deep "
                "agent / spec steward / human may (PDR-001 §10)"
            )
        if self.human_approved and not self.approved_by:
            raise ValueError("approval must name the approver")
        if self.human_approved and not self.effective_session_id:
            raise ValueError("an approved proposal must name the session it activates in")
        if (
            self.effective_session_id
            and self.effective_session_id == self.observed_session_id
        ):
            raise ValueError(
                "a rule change may not take effect in the session that observed it; "
                "criteria changing mid-measurement makes all measurements "
                "incomparable (constitution §6)"
            )
        if not self.case_ids and self.kind is not ProposalKind.HARNESS_OPTIMISATION:
            raise ValueError("rule changes must be grounded in at least one case")
        return self
