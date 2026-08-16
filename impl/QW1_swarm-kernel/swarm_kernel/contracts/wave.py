from __future__ import annotations

from enum import Enum

from pydantic import Field

from .base import ContractModel, new_id, utc_now_iso


class WaveStage(str, Enum):
    COLLECTING = "collecting"
    ADJUDICATING = "adjudicating"
    COMMITTING = "committing"
    COMMITTED = "committed"
    COMPENSATING = "compensating"
    ROLLED_BACK = "rolled_back"


class FrozenInterface(ContractModel):
    contract_name: str = "FrozenInterface"
    interface_id: str
    contract_digest: str
    r_level: str = "R1"


class WavePlan(ContractModel):
    contract_name: str = "WavePlan"
    wave_id: str = Field(default_factory=lambda: new_id("wave"))
    epoch: int = 1
    spec_id: str
    delta_ids: list[str] = Field(default_factory=list)
    frozen_interfaces: list[FrozenInterface] = Field(default_factory=list)
    stage: WaveStage = WaveStage.COLLECTING
    created_by: str = "architect"
    ts: str = Field(default_factory=utc_now_iso)

    def frontier_digest(self) -> str:
        parts = sorted(f"{fi.interface_id}:{fi.contract_digest}" for fi in self.frozen_interfaces)
        joined = "|".join(parts) + f"#{self.epoch}"
        import hashlib

        return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]
