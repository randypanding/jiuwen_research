from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from opc.schemas.common import BaseSchema, content_hash


class Topic(str, Enum):
    TASK_ASSIGN = "task.assign"
    INSTANCE_SUBMIT = "instance.submit"
    GATE_REPORT = "gate.report"
    MEASUREMENT_REPORT = "measurement.report"
    SPEC_CONVERGE = "spec.converge"
    DRIFT_ALARM = "drift.alarm"
    PROPOSAL_SUBMIT = "proposal.submit"
    ADMIT_COMMIT = "admit.commit"
    WAIVER_REQUEST = "waiver.request"


ROLES = (
    "leader",
    "architect",
    "builder",
    "verifier",
    "spec_moderator",
    "spec_steward",
    "reconciler",
    "cartographer",
    "critic",
    "refactor",
    "moderator",
    "deep_agent",
    "human_gateway",
    "world",
)


class Envelope(BaseSchema):
    """The only legal inter-contract message carrier.

    Routing legality (who may talk to whom about what) is enforced by the
    bus, not by the envelope itself; see opc.world.bus.ROUTING_TABLE.
    """

    envelope_id: str = Field(default_factory=lambda: "ENV-" + uuid.uuid4().hex[:16])
    topic: Topic
    src_role: str
    dst_role: str
    wave_id: str = ""
    causation_id: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("src_role", "dst_role")
    @classmethod
    def _roles(cls, v: str) -> str:
        if v not in ROLES:
            raise ValueError(f"unknown role {v!r}; must be one of {ROLES}")
        return v

    def digest(self) -> str:
        return content_hash(self)
