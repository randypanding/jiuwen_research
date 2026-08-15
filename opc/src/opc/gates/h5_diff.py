from __future__ import annotations

import json
import time
from pathlib import Path

from opc.diff.engine import DiffEngine
from opc.gates.base import Gate, GateContext, check, worst
from opc.oracle.scenarios import invoke_entrypoint, redact
from opc.schemas.common import Verdict
from opc.schemas.gates import CheckResult, GateReport


class H5DiffGate(Gate):
    """H5: instance differential / golden-output gate.

    Two modes:
      * golden mode (R3 frozen artifacts): compare normalized outputs byte-
        exact against locked golden files;
      * fan-out mode (N >= 2): behavioural differential across same-source
        instances over a shared corpus; divergences outside registered
        don't-care scopes are FAIL (spec silence candidate).

    With N == 1 and no golden artifacts the gate reports INCONCLUSIVE; only
    a registered, human-approved waiver can admit that state.
    """

    gate_id = "H5"

    def run(self, ctx: GateContext) -> GateReport:
        started = time.monotonic()
        checks: list[CheckResult] = []
        contract = ctx.contract()
        dont_care_scopes = [d.scope for d in contract.dont_care] if contract else []
        redactions = list(ctx.extra.get("redactions", []))

        golden_used = False
        if contract and contract.frozen_outputs:
            golden_used = True
            if ctx.golden_dir is None or not Path(ctx.golden_dir).exists():
                checks.append(check("h5.golden", False, "R3 contract declares frozen_outputs but golden store is missing"))
            else:
                for golden_path in sorted(Path(ctx.golden_dir).glob("*.golden.json")):
                    spec = json.loads(golden_path.read_text(encoding="utf-8"))
                    result, err = invoke_entrypoint(
                        str(ctx.instance_dir),
                        spec.get("entrypoint", "main"),
                        spec.get("inputs", {}),
                        float(spec.get("timeout_s", 30.0)),
                        ctx.python,
                    )
                    if err:
                        checks.append(check(f"h5.golden.{golden_path.stem}", False, err))
                        continue
                    norm = redact(result, spec.get("redact", []) + redactions)
                    expected = spec.get("expected")
                    ok = json.dumps(norm, sort_keys=True, default=str) == json.dumps(
                        expected, sort_keys=True, default=str
                    )
                    checks.append(
                        check(
                            f"h5.golden.{golden_path.stem}",
                            ok,
                            "" if ok else f"golden mismatch: got {json.dumps(norm, default=str)[:200]}",
                        )
                    )

        instances = {k: v for k, v in ctx.sibling_instances.items()}
        if len(instances) >= 2 and ctx.corpus_file is not None:
            corpus = json.loads(Path(ctx.corpus_file).read_text(encoding="utf-8"))
            entrypoint = ctx.extra.get("entrypoint", "main:run")
            report = DiffEngine(python_executable=ctx.python).run(
                instances=instances,
                entrypoint=entrypoint,
                corpus=corpus,
                redactions=redactions,
                dont_care_scopes=dont_care_scopes,
                min_instances=int(ctx.extra.get("min_instances", 3)),
            )
            checks.append(
                check(
                    "h5.diff",
                    report.verdict is Verdict.PASS,
                    f"{report.note}; divergences={len(report.divergences)} dont_care={report.dont_care_divergences}",
                )
            )
            if report.verdict is Verdict.INCONCLUSIVE:
                checks[-1].status = Verdict.INCONCLUSIVE
        elif not golden_used:
            checks.append(
                CheckResult(
                    id="h5.diff",
                    status=Verdict.INCONCLUSIVE,
                    detail=(
                        "N=1 and no golden artifacts: silence cannot be measured; "
                        "admission requires an explicit waiver or raising N >= 3"
                    ),
                )
            )

        return self.report(ctx, worst([c.status for c in checks]), checks, started)
