from __future__ import annotations

import re
import subprocess
import time

from swarmfoundry.schema.gates import GATE_H2, GateResult, STATUS_FAIL, STATUS_PASS
from swarmfoundry.gates.base import Gate
from swarmfoundry.gates.context import GateContext

_ASSERT_RE = re.compile(r"\bassert\b|\.assert|assertEqual|assertTrue|expect\(")


class H2UnitTestGate(Gate):
    """H2: unit & property tests. Additionally counts *effective assertions*
    (oracle-research practice 3: self-written tests without assertions do not
    count as evidence)."""

    gate_id = GATE_H2

    def run(self, ctx: GateContext) -> GateResult:
        cfg = ctx.gate_config(self.gate_id)
        commands = cfg.get("commands") or [["python3", "-m", "pytest", "-q"]]
        min_assertions = int(cfg.get("min_effective_assertions", 0))
        evidence: list[str] = []
        failed = False
        for cmd in commands:
            start = time.monotonic()
            proc = subprocess.run(
                cmd,
                cwd=str(ctx.instance_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=float(cfg.get("timeout_s", 600)),
            )
            dur = int((time.monotonic() - start) * 1000)
            evidence.append(f"$ {' '.join(cmd)} -> exit {proc.returncode} ({dur}ms)")
            if proc.returncode != 0:
                failed = True
                evidence.append(proc.stdout.decode("utf-8", errors="replace")[-800:])
        assertion_count = 0
        for p in ctx.instance_dir.rglob("*.py"):
            if ".venv" in p.parts:
                continue
            try:
                assertion_count += len(_ASSERT_RE.findall(p.read_text(encoding="utf-8", errors="replace")))
            except OSError:
                continue
        if min_assertions and assertion_count < min_assertions:
            failed = True
            evidence.append(f"effective assertions {assertion_count} < required {min_assertions}")
        return GateResult(
            gate_id=self.gate_id,
            status=STATUS_FAIL if failed else STATUS_PASS,
            evidence=tuple(evidence),
            details={"effective_assertions": assertion_count},
        )
