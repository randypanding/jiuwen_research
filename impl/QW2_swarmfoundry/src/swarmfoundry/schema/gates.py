from __future__ import annotations

import dataclasses
import time

from swarmfoundry.schema import SCHEMA_VERSION
from swarmfoundry.schema.base import (
    SchemaError,
    check_id,
    check_schema_version,
    require,
    require_list,
)

GATE_H1 = "H1"
GATE_H2 = "H2"
GATE_H3 = "H3"
GATE_H4 = "H4"
GATE_H5 = "H5"
GATE_H6 = "H6"
GATE_H7 = "H7"
GATE_H8 = "H8"
GATE_S = "S"

HARD_GATES = (GATE_H1, GATE_H2, GATE_H3, GATE_H4, GATE_H5, GATE_H6, GATE_H7, GATE_H8)
SOFT_GATES = (GATE_S,)

STATUS_PASS = "pass"
STATUS_FAIL = "fail"
STATUS_ERROR = "error"
STATUS_SKIP = "skip"
GATE_STATUSES = (STATUS_PASS, STATUS_FAIL, STATUS_ERROR, STATUS_SKIP)


@dataclasses.dataclass(frozen=True)
class GateResult:
    gate_id: str
    status: str
    evidence: tuple[str, ...] = ()
    details: dict = dataclasses.field(default_factory=dict)
    duration_ms: int = 0
    ts: float = 0.0
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "status": self.status,
            "evidence": list(self.evidence),
            "details": self.details,
            "duration_ms": self.duration_ms,
            "ts": self.ts,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GateResult":
        where = "GateResult"
        check_schema_version(data, where)
        gate_id = require(data, "gate_id", str, where)
        status = require(data, "status", str, where)
        if status not in GATE_STATUSES:
            raise SchemaError(f"{where}: status must be one of {GATE_STATUSES}")
        return cls(
            gate_id=gate_id,
            status=status,
            evidence=tuple(require_list(data, "evidence", where)),
            details=data.get("details", {}),
            duration_ms=int(data.get("duration_ms", 0)),
            ts=float(data.get("ts", 0.0)),
        )


@dataclasses.dataclass(frozen=True)
class AdmissionDecision:
    admitted: bool
    hard_results: tuple[GateResult, ...]
    soft_results: tuple[GateResult, ...]
    rule: str
    instance_id: str
    ts: float = dataclasses.field(default_factory=time.time)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "admitted": self.admitted,
            "rule": self.rule,
            "instance_id": self.instance_id,
            "ts": self.ts,
            "hard_results": [g.to_dict() for g in self.hard_results],
            "soft_results": [g.to_dict() for g in self.soft_results],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AdmissionDecision":
        where = "AdmissionDecision"
        check_schema_version(data, where)
        return cls(
            admitted=require(data, "admitted", bool, where),
            rule=require(data, "rule", str, where),
            instance_id=require(data, "instance_id", str, where),
            ts=float(data.get("ts", 0.0)),
            hard_results=tuple(GateResult.from_dict(g) for g in require_list(data, "hard_results", where)),
            soft_results=tuple(GateResult.from_dict(g) for g in require_list(data, "soft_results", where)),
        )

    def failed_gates(self) -> list[str]:
        out = [g.gate_id for g in self.hard_results if g.status != STATUS_PASS]
        out += [g.gate_id for g in self.soft_results if g.status != STATUS_PASS]
        return out


class GateAlgebraError(SchemaError):
    pass


def admit(hard_results: list[GateResult], soft_results: list[GateResult], instance_id: str) -> AdmissionDecision:
    """Admit(instance) = ∧H ∧ ∧S. Both sides are pure veto devices; fail-closed on
    missing, skipped or errored gates (a gate that cannot testify cannot admit)."""
    for g in hard_results:
        if g.gate_id not in HARD_GATES:
            raise GateAlgebraError(f"unknown hard gate {g.gate_id}")
    for g in soft_results:
        if g.gate_id not in SOFT_GATES:
            raise GateAlgebraError(f"unknown soft gate {g.gate_id}")
    present_hard = {g.gate_id for g in hard_results}
    missing = [gid for gid in HARD_GATES if gid not in present_hard]
    admitted = not missing and all(g.status == STATUS_PASS for g in hard_results)
    admitted = admitted and all(g.status == STATUS_PASS for g in soft_results)
    if missing:
        rule = f"Admit = ∧H ∧ ∧S; fail-closed: missing gates {missing}"
    else:
        rule = "Admit = ∧H ∧ ∧S; soft gates are monotone vetoers and never rescue"
    return AdmissionDecision(
        admitted=admitted,
        hard_results=tuple(hard_results),
        soft_results=tuple(soft_results),
        rule=rule,
        instance_id=check_id(instance_id, "AdmissionDecision"),
    )
