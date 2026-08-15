from __future__ import annotations

from swarmdev.contracts import GateOutcome
from swarmdev.contracts.receipt import GateStatus

from swarmdev.gates.protocol import Gate, GateContext, VALID_GATE_IDS


class GateRunner:
    def __init__(self, gates: list[Gate], fail_fast: bool = True):
        seen: set[str] = set()
        for gate in gates:
            gate_id = gate.gate_id
            if gate_id not in VALID_GATE_IDS:
                raise ValueError(f"unknown gate_id: {gate_id}")
            if gate_id in seen:
                raise ValueError(f"duplicate gate_id: {gate_id}")
            seen.add(gate_id)
        self.gates = list(gates)
        self.fail_fast = fail_fast

    def run(self, ctx: GateContext) -> list[GateOutcome]:
        outcomes: list[GateOutcome] = []
        for gate in self.gates:
            outcome = gate.run(ctx)
            outcomes.append(outcome)
            if self.fail_fast and outcome.status in (GateStatus.FAIL, GateStatus.BLOCKED):
                break
        return outcomes
