from __future__ import annotations

import abc
import time

from swarmfoundry.schema.gates import GateResult, STATUS_ERROR
from swarmfoundry.gates.context import GateContext


class Gate(abc.ABC):
    gate_id: str = "H?"

    @abc.abstractmethod
    def run(self, ctx: GateContext) -> GateResult:
        ...

    def safe_run(self, ctx: GateContext) -> GateResult:
        start = time.monotonic()
        try:
            res = self.run(ctx)
            if res.duration_ms == 0:
                res = GateResult(
                    gate_id=res.gate_id,
                    status=res.status,
                    evidence=res.evidence,
                    details=res.details,
                    duration_ms=int((time.monotonic() - start) * 1000),
                    ts=time.time(),
                )
            return res
        except Exception as e:
            return GateResult(
                gate_id=self.gate_id,
                status=STATUS_ERROR,
                evidence=[],
                details={"error": f"{type(e).__name__}: {e}"},
                duration_ms=int((time.monotonic() - start) * 1000),
                ts=time.time(),
            )
