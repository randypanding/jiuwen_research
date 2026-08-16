from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import Field

from .base import ContractModel, Verdict, new_id, utc_now_iso


class GateId(str, Enum):
    H1_BUILD = "H1"
    H2_UNIT = "H2"
    H3_HOLDOUT = "H3"
    H4_CONTRACT_SURFACE = "H4"
    H5_DIFFERENTIAL = "H5"
    H6_INVARIANTS = "H6"
    H7_DRIFT = "H7"
    H8_BUDGET = "H8"


HARD_GATES = [g for g in GateId]


class WitnessRef(ContractModel):
    contract_name: str = "WitnessRef"
    kind: str
    locator: str
    content_sha256: str = ""


class GateResult(ContractModel):
    contract_name: str = "GateResult"
    result_id: str = Field(default_factory=lambda: new_id("gr"))
    gate_id: GateId
    verdict: Verdict
    attempts: int = 1
    duration_ms: int = 0
    witness_refs: list[WitnessRef] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)
    ts: str = Field(default_factory=utc_now_iso)

    @property
    def passed(self) -> bool:
        return self.verdict == Verdict.PASS


class GateSuiteResult(ContractModel):
    contract_name: str = "GateSuiteResult"
    suite_id: str = Field(default_factory=lambda: new_id("gs"))
    instance_id: str
    results: list[GateResult] = Field(default_factory=list)

    def by_gate(self) -> dict[GateId, GateResult]:
        return {r.gate_id: r for r in self.results}

    @property
    def hard_pass(self) -> bool:
        m = self.by_gate()
        return all(g in m and m[g].verdict == Verdict.PASS for g in HARD_GATES)

    def blocking_gates(self) -> list[GateId]:
        m = self.by_gate()
        out = []
        for g in HARD_GATES:
            r = m.get(g)
            if r is None or r.verdict != Verdict.PASS:
                out.append(g)
        return out
