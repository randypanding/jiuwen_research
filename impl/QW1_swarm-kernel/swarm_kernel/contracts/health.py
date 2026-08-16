from __future__ import annotations

from enum import Enum

from pydantic import Field

from .base import ContractModel, new_id, utc_now_iso


class MigrationStage(str, Enum):
    M0_HARVEST = "M0"
    M1_ANCHOR = "M1"
    M2_REGENERATE = "M2"
    M3_FACTORY = "M3"


class HealthSnapshot(ContractModel):
    contract_name: str = "HealthSnapshot"
    snapshot_id: str = Field(default_factory=lambda: new_id("hs"))
    period: str = ""
    stage: MigrationStage = MigrationStage.M0_HARVEST
    closure_rate: float = 0.0
    spec_entropy_events_per_delta: float = 0.0
    witness_coverage: float = 0.0
    unverifiable_clauses: int = 0
    escape_defect_rate: float = 0.0
    drift_alert_rate: float = 0.0
    judge_calibration_kappa: float = 0.0
    judge_abstention_rate: float = 0.0
    rework_rate: float = 0.0
    admission_cost_tokens: float = 0.0
    ts: str = Field(default_factory=utc_now_iso)
