from __future__ import annotations

import json
import time

from opc.gates.base import Gate, GateContext, check, worst
from opc.schemas.common import Verdict
from opc.schemas.gates import CheckResult, GateReport

USAGE_FILE = "usage.json"
BENCH_FILE = "bench.json"


class H8BudgetGate(Gate):
    """H8: cost / resource / performance budget.

    Evidence files are produced by the harness (token accounting from LLM
    traces, latency from the scenario runs). Missing evidence is
    INCONCLUSIVE, never PASS: an admission without cost receipts cannot be
    economically audited.
    """

    gate_id = "H8"

    def run(self, ctx: GateContext) -> GateReport:
        started = time.monotonic()
        checks: list[CheckResult] = []
        budget = ctx.policy().get("budget", {})
        if not budget:
            checks.append(
                CheckResult(id="h8.policy", status=Verdict.INCONCLUSIVE, detail="no budget policy configured")
            )
            return self.report(ctx, Verdict.INCONCLUSIVE, checks, started)
        checks.append(check("h8.policy", True))

        usage_path = ctx.instance_dir / USAGE_FILE
        if not usage_path.exists():
            checks.append(CheckResult(id="h8.usage", status=Verdict.INCONCLUSIVE, detail="usage.json missing: no token accounting evidence"))
        else:
            usage = json.loads(usage_path.read_text(encoding="utf-8"))
            prompt_tokens = int(usage.get("prompt_tokens", 0))
            completion_tokens = int(usage.get("completion_tokens", 0))
            checks.append(
                check(
                    "h8.prompt_tokens",
                    prompt_tokens <= int(budget.get("max_prompt_tokens", float("inf"))),
                    f"prompt_tokens={prompt_tokens} limit={budget.get('max_prompt_tokens')}",
                )
            )
            checks.append(
                check(
                    "h8.completion_tokens",
                    completion_tokens <= int(budget.get("max_completion_tokens", float("inf"))),
                    f"completion_tokens={completion_tokens} limit={budget.get('max_completion_tokens')}",
                )
            )

        bench_path = ctx.instance_dir / BENCH_FILE
        if "max_p95_latency_ms" in budget:
            if not bench_path.exists():
                checks.append(CheckResult(id="h8.latency", status=Verdict.INCONCLUSIVE, detail="bench.json missing"))
            else:
                bench = json.loads(bench_path.read_text(encoding="utf-8"))
                p95 = float(bench.get("p95_latency_ms", float("inf")))
                checks.append(
                    check(
                        "h8.latency",
                        p95 <= float(budget["max_p95_latency_ms"]),
                        f"p95_latency_ms={p95} limit={budget['max_p95_latency_ms']}",
                    )
                )

        return self.report(ctx, worst([c.status for c in checks]), checks, started)
