from __future__ import annotations

import time

from swarmdev.contracts import GateOutcome
from swarmdev.contracts.receipt import GateStatus

from swarmdev.gates.protocol import GateContext


class BudgetGate:
    gate_id = "H8"

    def __init__(self, max_tokens: int | None = None, max_duration_s: float | None = None):
        self.max_tokens = max_tokens
        self.max_duration_s = max_duration_s

    def run(self, ctx: GateContext) -> GateOutcome:
        started = time.monotonic()
        record = ctx.cost_record
        if record is None:
            return GateOutcome(
                gate_id=self.gate_id,
                status=GateStatus.INCONCLUSIVE,
                details="cost record missing",
                duration_s=time.monotonic() - started,
            )
        tokens = record.get("tokens", 0)
        duration = record.get("duration_s", 0.0)
        violations = []
        if self.max_tokens is not None and tokens > self.max_tokens:
            violations.append(f"tokens {tokens} > max {self.max_tokens}")
        if self.max_duration_s is not None and duration > self.max_duration_s:
            violations.append(f"duration_s {duration} > max {self.max_duration_s}")
        if violations:
            return GateOutcome(
                gate_id=self.gate_id,
                status=GateStatus.FAIL,
                details="; ".join(violations),
                duration_s=time.monotonic() - started,
            )
        return GateOutcome(
            gate_id=self.gate_id,
            status=GateStatus.PASS,
            details=f"tokens={tokens} duration_s={duration}",
            duration_s=time.monotonic() - started,
        )
