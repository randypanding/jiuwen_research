from __future__ import annotations

import dataclasses

from swarmfoundry.schema import SCHEMA_VERSION
from swarmfoundry.schema.base import (
    SchemaError,
    check_id,
    check_schema_version,
    require,
)

OBS_CLOSED = "closed"
OBS_SILENCE = "silence"
OBS_DIVERGENCE = "divergence"
OBS_TIER_INSUFFICIENT = "tier_insufficient"
OBS_SPEC_ORACLE_CONFLICT = "spec_oracle_conflict"
OBS_INSUFFICIENT_INSTANCES = "insufficient_instances"
OBSERVATIONS = (
    OBS_CLOSED,
    OBS_SILENCE,
    OBS_DIVERGENCE,
    OBS_TIER_INSUFFICIENT,
    OBS_SPEC_ORACLE_CONFLICT,
    OBS_INSUFFICIENT_INSTANCES,
)


@dataclasses.dataclass(frozen=True)
class MeasurementEvent:
    """Contract C11: the instrument reading of an N-fan-out (structure.md §6)."""

    event_id: str
    spec_delta_id: str
    observation: str
    n_instances: int
    n_passed: int
    diff_empty: bool
    detail: str = ""
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "spec_delta_id": self.spec_delta_id,
            "observation": self.observation,
            "n_instances": self.n_instances,
            "n_passed": self.n_passed,
            "diff_empty": self.diff_empty,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MeasurementEvent":
        where = "MeasurementEvent"
        check_schema_version(data, where)
        observation = require(data, "observation", str, where)
        if observation not in OBSERVATIONS:
            raise SchemaError(f"{where}: observation must be one of {OBSERVATIONS}")
        return cls(
            event_id=check_id(require(data, "event_id", str, where), where),
            spec_delta_id=require(data, "spec_delta_id", str, where),
            observation=observation,
            n_instances=require(data, "n_instances", int, where),
            n_passed=require(data, "n_passed", int, where),
            diff_empty=require(data, "diff_empty", bool, where),
            detail=data.get("detail", ""),
        )


def classify_measurement(n_instances: int, n_passed: int, diff_empty: bool, upgraded_tier_failed: bool = False) -> str:
    """Deterministic mapping of a fan-out reading onto structure.md §6 table."""
    if n_instances < 3 and n_passed < n_instances:
        return OBS_INSUFFICIENT_INSTANCES
    if n_passed == n_instances:
        return OBS_CLOSED if diff_empty else OBS_SILENCE
    if n_passed == 0:
        return OBS_SPEC_ORACLE_CONFLICT if upgraded_tier_failed else OBS_TIER_INSUFFICIENT
    return OBS_DIVERGENCE
