from __future__ import annotations

from swarmfoundry.schema.gates import GATE_H8, GateResult, STATUS_FAIL, STATUS_PASS
from swarmfoundry.gates.base import Gate
from swarmfoundry.gates.context import GateContext


class H8CostGate(Gate):
    """H8: cost/resource budget. Accumulated token & spend accounting for this
    spec-delta must stay within configured ceilings; overrun = fail (TCO
    research: budget ceiling with auto-stop)."""

    gate_id = GATE_H8

    def run(self, ctx: GateContext) -> GateResult:
        cfg = ctx.gate_config(self.gate_id)
        max_tokens = cfg.get("max_total_tokens")
        max_spend = cfg.get("max_spend_units")
        total_tokens = ctx.costs.tokens_in + ctx.costs.tokens_out
        evidence = [
            f"tokens_in={ctx.costs.tokens_in} tokens_out={ctx.costs.tokens_out} spend={ctx.costs.spend_units}"
        ]
        failed = False
        if max_tokens is not None and total_tokens > int(max_tokens):
            failed = True
            evidence.append(f"token budget exceeded: {total_tokens} > {max_tokens}")
        if max_spend is not None and ctx.costs.spend_units > float(max_spend):
            failed = True
            evidence.append(f"spend budget exceeded: {ctx.costs.spend_units} > {max_spend}")
        if not failed:
            evidence.append("within budget")
        return GateResult(
            gate_id=self.gate_id,
            status=STATUS_FAIL if failed else STATUS_PASS,
            evidence=tuple(evidence),
            details={"total_tokens": total_tokens, "spend_units": ctx.costs.spend_units},
        )
