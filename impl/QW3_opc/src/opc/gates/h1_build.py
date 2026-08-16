from __future__ import annotations

import shutil
import subprocess
import time

from opc.gates.base import Gate, GateContext, check, worst
from opc.schemas.common import Verdict
from opc.schemas.gates import CheckResult, GateReport

class H1BuildGate(Gate):
    """H1: build / syntax / static analysis - the structural floor."""

    gate_id = "H1"

    def run(self, ctx: GateContext) -> GateReport:
        started = time.monotonic()
        checks: list[CheckResult] = []

        compile_proc = subprocess.run(
            [ctx.python, "-m", "compileall", "-q", "-j", "0", str(ctx.instance_dir)],
            capture_output=True,
            text=True,
        )
        checks.append(
            check(
                "h1.compileall",
                compile_proc.returncode == 0,
                compile_proc.stderr.strip()[-400:] if compile_proc.returncode else "syntax ok",
            )
        )

        ruff = shutil.which("ruff")
        if ruff:
            ruff_proc = subprocess.run(
                [ruff, "check", "--select", "E9,F", "--output-format=concise", str(ctx.instance_dir)],
                capture_output=True,
                text=True,
            )
            checks.append(
                check(
                    "h1.ruff",
                    ruff_proc.returncode == 0,
                    ruff_proc.stdout.strip()[-400:] if ruff_proc.returncode else "lint clean",
                )
            )
        else:
            checks.append(
                CheckResult(
                    id="h1.ruff",
                    status=Verdict.INCONCLUSIVE,
                    detail="ruff not installed; static analysis skipped (must be present in CI image)",
                )
            )

        verdict = worst([c.status for c in checks])
        return self.report(ctx, verdict, checks, started)
