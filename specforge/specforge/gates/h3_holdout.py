"""H3: holdout scenario suite gate (aggregated score only)."""
from __future__ import annotations

from typing import Any

from .base import GateContext, GateResult, GateVerdict


class H3HoldoutGate:
    gate_id = "h3"
    description = "scenario holdout suite via private store (aggregate score only)"
    hard = True

    def __init__(self, score_threshold: float = 0.8, min_scenarios: int = 5,
                 theta: float = 0.75, z: float = 1.96):
        self.score_threshold = score_threshold
        self.min_scenarios = min_scenarios
        self.theta = theta
        self.z = z

    def applicable(self, ctx: GateContext) -> bool:
        unit = ctx.spec_unit
        if unit is None:
            return False
        return any(c.witness and c.witness.kind == "holdout" for c in unit.machine_clauses())

    def run(self, ctx: GateContext) -> GateResult:
        store = ctx.holdout_store
        if store is None:
            return GateResult(self.gate_id, GateVerdict.INCONCLUSIVE,
                              reason="no holdout store wired into gate context",
                              constitution_ref="#3 无机械见证的条款只能否决，不能放行")
        unit = ctx.spec_unit
        sets = sorted({c.witness.ref for c in unit.machine_clauses()
                       if c.witness and c.witness.kind == "holdout"})
        evidence: dict[str, Any] = {"sets": sets, "scores": {}}
        if not sets:
            return GateResult(self.gate_id, GateVerdict.SKIP, reason="no holdout sets bound")
        total_pass = 0
        total_n = 0
        for s in sets:
            score = store.evaluate(ctx.instance_path, set_id=s)
            evidence["scores"][s] = {"aggregate": score.aggregate, "passed": score.passed,
                                     "total": score.total, "dimensions": score.dimensions}
            total_pass += score.passed
            total_n += score.total
        if total_n < self.min_scenarios:
            return GateResult(self.gate_id, GateVerdict.INCONCLUSIVE,
                              reason=f"holdout sample too small ({total_n} < {self.min_scenarios})",
                              evidence=evidence)
        from .stats import threshold_gate

        sv = threshold_gate(total_pass, total_n, self.theta, self.z)
        evidence["stat"] = {"verdict": sv.verdict, "statistic": sv.statistic, "detail": sv.detail}
        verdict_map = {"PASS": GateVerdict.PASS, "FAIL": GateVerdict.FAIL,
                       "INCONCLUSIVE": GateVerdict.INCONCLUSIVE}
        return GateResult(self.gate_id, verdict_map[sv.verdict],
                          reason=sv.detail, evidence=evidence)
