from __future__ import annotations

import subprocess
import time

from swarmfoundry.schema.gates import GATE_H1, GateResult, STATUS_FAIL, STATUS_PASS
from swarmfoundry.gates.base import Gate
from swarmfoundry.gates.context import GateContext


class H1BuildGate(Gate):
    """H1: build / type / static-analysis floor. Command-driven so each domain
    can bind its own toolchain; exit code is the only truth."""

    gate_id = GATE_H1

    def run(self, ctx: GateContext) -> GateResult:
        cfg = ctx.gate_config(self.gate_id)
        commands = cfg.get("commands") or [["python3", "-m", "compileall", "-q", "."]]
        evidence: list[str] = []
        failed = False
        for cmd in commands:
            start = time.monotonic()
            proc = subprocess.run(
                cmd,
                cwd=str(ctx.instance_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=float(cfg.get("timeout_s", 300)),
            )
            dur = int((time.monotonic() - start) * 1000)
            line = f"$ {' '.join(cmd)} -> exit {proc.returncode} ({dur}ms)"
            evidence.append(line)
            if proc.returncode != 0:
                failed = True
                tail = proc.stdout.decode("utf-8", errors="replace")[-800:]
                evidence.append(tail)
        return GateResult(
            gate_id=self.gate_id,
            status=STATUS_FAIL if failed else STATUS_PASS,
            evidence=tuple(evidence),
            details={"commands": commands},
        )
