from __future__ import annotations

import time
from pathlib import Path

from opc.gates.base import Gate, GateContext, check, worst
from opc.oracle.scenarios import ScenarioRunner, load_scenarios
from opc.schemas.common import Verdict
from opc.schemas.gates import CheckResult, GateReport


class H3HoldoutGate(Gate):
    """H3: holdout scenario suite - the oracle body, invisible to builders.

    Required scenarios are derived ONLY from the spec's witness bindings
    (gate == H3); scenario files themselves live outside the builder's
    workspace. Missing holdout witness files are a hard failure: admitting
    without an oracle is the paradigm's single fatal misuse.
    """

    gate_id = "H3"

    def run(self, ctx: GateContext) -> GateReport:
        started = time.monotonic()
        checks: list[CheckResult] = []
        contract = ctx.contract()

        required: set[str] = set()
        if contract is not None:
            for clause in contract.clauses:
                for witness in clause.witnesses:
                    if witness.gate == "H3":
                        required.add(witness.target)
        if not required:
            checks.append(
                check("h3.required_scenarios", False, "contract binds no H3 holdout witness; refuse to admit")
            )
            return self.report(ctx, Verdict.FAIL, checks, started)

        if ctx.holdout_dir is None or not Path(ctx.holdout_dir).exists():
            checks.append(check("h3.holdout_store", False, "holdout store unavailable to verifier"))
            return self.report(ctx, Verdict.FAIL, checks, started)

        scenarios = {s.scenario_id: s for s in load_scenarios(ctx.holdout_dir)}
        missing = sorted(required - scenarios.keys())
        checks.append(
            check("h3.holdout_store", not missing, f"missing scenario files: {missing}" if missing else f"{len(required)} scenarios bound")
        )
        for builder_leak in (ctx.instance_dir / "spec_oracle_leak_marker",):
            if builder_leak.exists():
                checks.append(check("h3.isolation", False, "holdout material found inside builder workspace"))

        runner = ScenarioRunner(python_executable=ctx.python)
        for scenario_id in sorted(required & scenarios.keys()):
            result = runner.run(scenarios[scenario_id], ctx.instance_dir)
            checks.append(check(f"h3.{scenario_id}", result.status is Verdict.PASS, result.detail))

        return self.report(ctx, worst([c.status for c in checks]), checks, started)
