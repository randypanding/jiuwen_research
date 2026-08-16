from __future__ import annotations

import time

from swarmdev.contracts import GateOutcome, OracleBundle
from swarmdev.contracts.receipt import GateStatus

from swarmdev.gates.protocol import GateContext
from swarmdev.oracle.holdout_store import HoldoutStore
from swarmdev.oracle.scenario_runner import ScenarioRunner


class HoldoutGate:
    gate_id = "H3"

    def __init__(self, store_or_bundle: HoldoutStore | OracleBundle | None = None):
        self.store_or_bundle = store_or_bundle
        self.runner = ScenarioRunner()

    def run(self, ctx: GateContext) -> GateOutcome:
        started = time.monotonic()
        source = self.store_or_bundle if self.store_or_bundle is not None else ctx.bundle
        if source is None:
            return GateOutcome(
                gate_id=self.gate_id,
                status=GateStatus.BLOCKED,
                details="no oracle bundle or holdout store provided",
                duration_s=time.monotonic() - started,
            )
        if isinstance(source, HoldoutStore):
            # PDR-001 §7：holdout 对 builder 不可见，读取必须持能力令牌
            token = ctx.extra.get("token")
            if token is None:
                return GateOutcome(
                    gate_id=self.gate_id,
                    status=GateStatus.BLOCKED,
                    details="capability token required to read holdout store",
                    duration_s=time.monotonic() - started,
                )
            scenarios = source.get(token)
        else:
            scenarios = source.scenarios
        failures = []
        for scenario in scenarios:
            result = self.runner.run(scenario, ctx.workspace)
            if not result.passed:
                failures.append(f"{scenario.scenario_id}: {result.details or 'expectation failed'}")
        if failures:
            return GateOutcome(
                gate_id=self.gate_id,
                status=GateStatus.FAIL,
                details="failed scenarios: " + "; ".join(failures),
                duration_s=time.monotonic() - started,
            )
        return GateOutcome(
            gate_id=self.gate_id,
            status=GateStatus.PASS,
            details=f"{len(scenarios)} holdout scenario(s) passed",
            duration_s=time.monotonic() - started,
        )
