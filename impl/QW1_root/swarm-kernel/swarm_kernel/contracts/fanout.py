from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import Field, model_validator

from .base import ContractModel, RLevel, Role, new_id, utc_now_iso


class FanoutRequest(ContractModel):
    contract_name: str = "FanoutRequest"
    fanout_id: str = Field(default_factory=lambda: new_id("fo"))
    wave_id: str
    delta_id: str
    r_level: RLevel = RLevel.R0
    n_instances: int = 1
    seed: int = 0
    interface_freeze_digest: str = ""
    ts: str = Field(default_factory=utc_now_iso)

    @model_validator(mode="after")
    def r3_no_fanout(self) -> "FanoutRequest":
        if self.r_level == RLevel.R3 and self.n_instances != 1:
            raise ValueError("R3 artifacts forbid fan-out: n_instances must be 1")
        if self.n_instances < 1 or self.n_instances > 8:
            raise ValueError("n_instances must be within [1, 8]")
        return self


class InstanceSubmission(ContractModel):
    contract_name: str = "InstanceSubmission"
    instance_id: str = Field(default_factory=lambda: new_id("inst"))
    fanout_id: str
    delta_id: str
    builder_role: Role = Role.BUILDER
    artifact_path: str
    contract_surface_digest: str = ""
    resource_report: dict[str, float] = Field(default_factory=dict)
    ts: str = Field(default_factory=utc_now_iso)


class DiscardedInstance(ContractModel):
    contract_name: str = "DiscardedInstance"
    instance_id: str
    measurement_conclusion: str


class MeasurementClassification(str, Enum):
    CLOSED = "closed"
    SILENCE = "silence"
    DIVERGENCE = "divergence"
    TIER_UPGRADE_REQUIRED = "tier_upgrade_required"
    SPEC_ORACLE_CONFLICT = "spec_oracle_conflict"
    INSUFFICIENT_SAMPLES = "insufficient_samples"


class MeasurementEvent(ContractModel):
    contract_name: str = "MeasurementEvent"
    event_id: str = Field(default_factory=lambda: new_id("me"))
    fanout_id: str
    delta_id: str
    n_instances: int
    pass_count: int
    fail_count: int
    divergence_detected: bool = False
    divergence_inputs: list[str] = Field(default_factory=list)
    classification: MeasurementClassification
    stronger_tier_succeeded: Optional[bool] = None
    ts: str = Field(default_factory=utc_now_iso)
