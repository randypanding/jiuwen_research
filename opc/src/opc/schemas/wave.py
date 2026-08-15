from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from opc.schemas.common import BaseSchema, RLevel


class InstanceRecord(BaseSchema):
    instance_id: str
    builder_id: str
    workspace_hash: str = Field(default="", description="sha256 of the sanitized workspace bundle the builder saw")
    status: Literal["building", "submitted", "qualified", "selected", "discarded", "rejected"] = "building"
    measurement_note: str = Field(
        default="",
        description="mandatory for discarded instances: what the discard measured about the spec",
    )


class WaveManifest(BaseSchema):
    """A wave = interface-freeze window + independent spec-delta cutset + one admission transaction boundary."""

    wave_id: str
    epoch: int = 1
    spec_version: str
    contract_ids: list[str] = Field(default_factory=list)
    spec_delta_refs: list[str] = Field(default_factory=list)
    fanout_n: int = Field(default=1, ge=1, le=8)
    r_levels: dict[str, RLevel] = Field(default_factory=dict)
    interface_frozen: bool = True
    status: Literal["collecting", "judging", "committed", "aborted"] = "collecting"

    @field_validator("wave_id")
    @classmethod
    def _wid(cls, v: str) -> str:
        if not v.startswith("WAVE-"):
            raise ValueError("wave_id must start with 'WAVE-'")
        return v


class AdmissionTransaction(BaseSchema):
    """The atomic commit unit: instances are buffered in the wave staging area
    and become visible in the world only at commit point."""

    wave_id: str
    receipts: list[str] = Field(default_factory=list)
    committed: bool = False
    compensated: bool = False
    commit_hash: str = ""
    rollback_reason: str = ""
