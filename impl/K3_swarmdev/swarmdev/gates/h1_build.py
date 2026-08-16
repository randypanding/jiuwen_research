from __future__ import annotations

import subprocess
import time

from swarmdev.contracts import GateOutcome
from swarmdev.contracts.receipt import GateStatus

from swarmdev.gates.protocol import GateContext


class BuildGate:
    gate_id = "H1"

    def __init__(self, commands: list[list[str]]):
        self.commands = [list(cmd) for cmd in commands]

    def run(self, ctx: GateContext) -> GateOutcome:
        started = time.monotonic()
        for cmd in self.commands:
            proc = subprocess.run(cmd, cwd=ctx.workspace, capture_output=True, text=True)
            if proc.returncode != 0:
                tail = (proc.stderr or proc.stdout or "").strip()[-500:]
                return GateOutcome(
                    gate_id=self.gate_id,
                    status=GateStatus.FAIL,
                    details=f"build command failed: {cmd}\nstderr tail: {tail}",
                    duration_s=time.monotonic() - started,
                )
        return GateOutcome(
            gate_id=self.gate_id,
            status=GateStatus.PASS,
            details=f"{len(self.commands)} build command(s) succeeded",
            duration_s=time.monotonic() - started,
        )
