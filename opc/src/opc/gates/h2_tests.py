from __future__ import annotations

import ast
import subprocess
import time
from pathlib import Path

from opc.gates.base import Gate, GateContext, check
from opc.schemas.common import Verdict
from opc.schemas.gates import CheckResult, GateReport


def _test_functions(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    found: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            found.append(node)
    return found


def _has_effective_assertion(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for node in ast.walk(func):
        if isinstance(node, ast.Assert):
            return True
        if isinstance(node, ast.Call):
            name = ""
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name.startswith("assert") or name in {"fail", "raises", "pytest"}:
                return True
    return False


def scan_oracle_signals(instance_dir: Path) -> tuple[int, int, list[str]]:
    """Static audit of agent-written tests: how many actually assert anything.

    Research anchor: ~80% of agent-written tests carry no effective assertion
    ('All Smoke, No Alarm'). Test count is NOT verification strength; only
    assertion-bearing tests count toward H2.
    """

    total = 0
    weak: list[str] = []
    for path in sorted(instance_dir.rglob("test_*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for func in _test_functions(tree):
            total += 1
            if not _has_effective_assertion(func):
                weak.append(f"{path.relative_to(instance_dir)}::{func.name}")
    return total, len(weak), weak


class H2TestsGate(Gate):
    """H2: unit + property tests, with oracle-signal quality audit."""

    gate_id = "H2"

    def run(self, ctx: GateContext) -> GateReport:
        started = time.monotonic()
        checks: list[CheckResult] = []

        pytest_proc = subprocess.run(
            [ctx.python, "-m", "pytest", str(ctx.instance_dir), "-q", "--tb=line", "-p", "no:cacheprovider"],
            capture_output=True,
            text=True,
            timeout=600,
        )
        exit_code = pytest_proc.returncode
        if exit_code == 0:
            checks.append(check("h2.pytest", True, pytest_proc.stdout.strip()[-200:]))
        elif exit_code == 5:
            checks.append(check("h2.pytest", False, "no tests collected: an instance without tests has no gate"))
        else:
            checks.append(check("h2.pytest", False, pytest_proc.stdout.strip()[-400:]))

        total, weak_count, weak_names = scan_oracle_signals(ctx.instance_dir)
        if total == 0:
            checks.append(check("h2.oracle_signal", False, "no test functions found"))
        elif weak_count == total:
            checks.append(
                check(
                    "h2.oracle_signal",
                    False,
                    f"all {total} tests lack effective assertions (smoke without alarm): {weak_names[:5]}",
                )
            )
        else:
            checks.append(
                check(
                    "h2.oracle_signal",
                    True,
                    f"{total - weak_count}/{total} tests carry effective assertions; weak: {weak_names[:5]}",
                )
            )

        verdict = Verdict.PASS if all(c.status is Verdict.PASS for c in checks) else Verdict.FAIL
        return self.report(ctx, verdict, checks, started)
