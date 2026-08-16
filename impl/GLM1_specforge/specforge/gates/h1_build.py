"""H1: build / type / static analysis floor."""
from __future__ import annotations

from typing import Any

from .base import GateContext, GateResult, GateVerdict
from .shell import run_command

DEFAULT_CMDS: list[list[str]] = [
    ["python", "-m", "compileall", "-q", "."],
]


class H1BuildGate:
    gate_id = "h1"
    description = "build/type/static floor via allowlisted commands"
    hard = True

    def __init__(self, commands: list[list[str]] | None = None, timeout: float = 300.0):
        self.commands = commands if commands is not None else DEFAULT_CMDS
        self.timeout = timeout

    def applicable(self, ctx: GateContext) -> bool:
        return True

    def run(self, ctx: GateContext) -> GateResult:
        ev: dict[str, Any] = {}
        for argv in self.commands:
            cmd_key = " ".join(argv)
            try:
                res = run_command(argv, cwd=ctx.instance_path, timeout=self.timeout)
            except PermissionError as e:
                return GateResult(self.gate_id, GateVerdict.INCONCLUSIVE,
                                  reason=f"command not allowed: {e}", evidence={"cmd": cmd_key})
            ev[cmd_key] = {"returncode": res.returncode, "timed_out": res.timed_out,
                           "duration_s": round(res.duration_s, 3),
                           "stderr_tail": res.stderr[-2000:]}
            if res.timed_out:
                return GateResult(self.gate_id, GateVerdict.FAIL,
                                  reason=f"{cmd_key} timed out after {self.timeout}s", evidence=ev)
            if res.returncode != 0:
                return GateResult(self.gate_id, GateVerdict.FAIL,
                                  reason=f"{cmd_key} exited {res.returncode}", evidence=ev)
        return GateResult(self.gate_id, GateVerdict.PASS, evidence=ev)
