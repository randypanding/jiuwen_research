"""H8: cost / resource / performance budget gate."""
from __future__ import annotations

from typing import Any

from .base import GateContext, GateResult, GateVerdict


class H8BudgetGate:
    gate_id = "h8"
    description = "cost/resource/performance budget"
    hard = True

    def __init__(self, default_cost_usd: float = 10.0, default_wall_s: float = 3600.0):
        self.default_cost_usd = default_cost_usd
        self.default_wall_s = default_wall_s

    def applicable(self, ctx: GateContext) -> bool:
        return True

    def run(self, ctx: GateContext) -> GateResult:
        budget = dict(ctx.budget or {})
        cost_limit = budget.get("cost_usd", self.default_cost_usd)
        wall_limit = budget.get("wall_s", self.default_wall_s)
        spent = ctx.extra.get("cost_usd", 0.0)
        wall = ctx.extra.get("wall_s", 0.0)
        evidence: dict[str, Any] = {
            "cost_usd": {"limit": cost_limit, "spent": spent},
            "wall_s": {"limit": wall_limit, "spent": wall},
        }
        if spent > cost_limit:
            return GateResult(self.gate_id, GateVerdict.FAIL,
                              reason=f"cost ${spent:.2f} exceeds budget ${cost_limit:.2f}", evidence=evidence)
        if wall > wall_limit:
            return GateResult(self.gate_id, GateVerdict.FAIL,
                              reason=f"wall time {wall:.0f}s exceeds budget {wall_limit:.0f}s", evidence=evidence)
        return GateResult(self.gate_id, GateVerdict.PASS, reason="within budget", evidence=evidence)
