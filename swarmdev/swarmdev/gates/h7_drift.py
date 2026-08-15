from __future__ import annotations

import time
from typing import Callable

from swarmdev.contracts import GateOutcome
from swarmdev.contracts.receipt import GateStatus

from swarmdev.gates.protocol import GateContext


class DriftGate:
    gate_id = "H7"

    def __init__(self, detector: Callable[[GateContext], tuple[bool, str]]):
        self.detector = detector

    def run(self, ctx: GateContext) -> GateOutcome:
        started = time.monotonic()
        clean, detail = self.detector(ctx)
        if clean:
            return GateOutcome(
                gate_id=self.gate_id,
                status=GateStatus.PASS,
                details=detail or "no drift",
                duration_s=time.monotonic() - started,
            )
        return GateOutcome(
            gate_id=self.gate_id,
            status=GateStatus.FAIL,
            details=detail or "drift detected",
            duration_s=time.monotonic() - started,
        )
