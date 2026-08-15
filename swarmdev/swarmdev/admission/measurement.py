from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel

_TIER_ORDER = {"L": 0, "M": 1, "H": 2}


class InstanceGateResult(BaseModel):
    instance_id: str
    gates_passed: bool
    tier: Literal["L", "M", "H"]


class Outcome(str, Enum):
    CLOSED = "closed"
    SILENCE = "silence"
    DIVERGENCE = "divergence"
    TIER_GAP = "tier_gap"
    SPEC_ORACLE_CONFLICT = "spec_oracle_conflict"
    INSUFFICIENT = "insufficient"


def classify_fanout(results: list[InstanceGateResult], has_divergence: bool,
                    min_samples: int = 3) -> Outcome:
    if not results:
        return Outcome.INSUFFICIENT
    if len(results) < min_samples and any(not r.gates_passed for r in results):
        return Outcome.INSUFFICIENT
    if all(r.gates_passed for r in results):
        return Outcome.SILENCE if has_divergence else Outcome.CLOSED
    base = min(_TIER_ORDER[r.tier] for r in results)
    base_has_pass = any(r.gates_passed for r in results if _TIER_ORDER[r.tier] == base)
    if not base_has_pass:
        higher_has_pass = any(
            r.gates_passed and _TIER_ORDER[r.tier] > base for r in results
        )
        if higher_has_pass:
            return Outcome.TIER_GAP
        return Outcome.SPEC_ORACLE_CONFLICT
    return Outcome.DIVERGENCE
