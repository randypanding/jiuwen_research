from __future__ import annotations

from typing import Optional, Sequence

from swarm_kernel.contracts.base import Verdict
from swarm_kernel.contracts.gates import GateId, GateResult, GateSuiteResult

from .base import EXIT_FAIL, EXIT_INCONCLUSIVE, EXIT_PASS, GATE_ORDER, GateContext
from .hard_gates import GATE_IMPLS


def run_suite(ctx: GateContext, gates: Optional[Sequence[GateId]] = None) -> GateSuiteResult:
    suite = GateSuiteResult(instance_id=ctx.instance_dir.name)
    for gate_id in gates or GATE_ORDER:
        impl = GATE_IMPLS[gate_id]
        result = impl(ctx)
        suite.results.append(result)
    return suite


def suite_exit_code(suite: GateSuiteResult) -> int:
    m = suite.by_gate()
    if any(r.verdict == Verdict.FAIL for r in suite.results):
        return EXIT_FAIL
    if not suite.hard_pass:
        return EXIT_INCONCLUSIVE
    return EXIT_PASS
