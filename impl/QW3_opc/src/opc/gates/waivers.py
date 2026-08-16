from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml
from pydantic import Field, field_validator

from opc.schemas.common import BaseSchema


class WaiverEntry(BaseSchema):
    """A pre-approved, time-boxed exception.

    Exceptions are never decided on the spot: a waiver is a rule-change
    artifact approved by a human, registered with an owner and an expiry.
    Expired or out-of-scope waivers are inert.
    """

    waiver_id: str
    gate: str
    scope: str = Field(description="'*' or a contract id or r_level the waiver applies to")
    reason: str
    approver: str
    expires_at: datetime

    @field_validator("waiver_id")
    @classmethod
    def _wid(cls, v: str) -> str:
        if not v.startswith("WVR-"):
            raise ValueError("waiver_id must start with 'WVR-'")
        return v

    def active(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return expires > now

    def covers(self, gate: str, contract_id: str, r_level: str) -> bool:
        if self.gate != gate:
            return False
        return self.scope in ("*", contract_id, r_level)


def load_waivers(path: str | Path) -> list[WaiverEntry]:
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return [WaiverEntry.model_validate(entry) for entry in data.get("waivers", [])]


def find_valid_waiver(
    waivers: list[WaiverEntry], gate: str, contract_id: str, r_level: str
) -> WaiverEntry | None:
    for waiver in waivers:
        if waiver.active() and waiver.covers(gate, contract_id, r_level):
            return waiver
    return None
