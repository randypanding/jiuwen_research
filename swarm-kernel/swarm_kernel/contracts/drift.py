from __future__ import annotations

from enum import Enum

from pydantic import Field

from .base import ContractModel, new_id, utc_now_iso


class AnchorState(str, Enum):
    OK = "ok"
    STALE = "stale"
    ORPHAN = "orphan"
    UNIMPLEMENTED = "unimplemented"


class AnchorRecord(ContractModel):
    contract_name: str = "AnchorRecord"
    clause_id: str
    anchor_hash: str
    file: str
    line: int = 0
    state: AnchorState = AnchorState.OK
    expected_hash: str = ""


class DriftSeverity(str, Enum):
    HARD_BLOCK = "hard_block"
    WARNING = "warning"


class DriftEvent(ContractModel):
    contract_name: str = "DriftEvent"
    event_id: str = Field(default_factory=lambda: new_id("drift"))
    spec_id: str
    records: list[AnchorRecord] = Field(default_factory=list)
    severity: DriftSeverity = DriftSeverity.HARD_BLOCK
    ts: str = Field(default_factory=utc_now_iso)

    @property
    def blocking(self) -> bool:
        return any(r.state in (AnchorState.STALE, AnchorState.ORPHAN, AnchorState.UNIMPLEMENTED) for r in self.records)
