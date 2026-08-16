from __future__ import annotations

import subprocess
from pathlib import Path

from swarmfoundry.schema.gates import GATE_H5, GateResult, STATUS_FAIL, STATUS_PASS
from swarmfoundry.gates.base import Gate
from swarmfoundry.gates.context import GateContext
from swarmfoundry.oracle.diff import diff_instances
from swarmfoundry.oracle.golden import compare_golden
from swarmfoundry.oracle.runner import load_suite


class H5DiffGate(Gate):
    """H5: inter-instance differential testing + R3 golden outputs.
    N=1: not applicable (recorded; spec-entropy is sampled by periodic N=3
    calibration waves instead). N>=2: pairwise diff must be empty, otherwise
    the reading is 'spec silence' and admission is blocked until the spec
    moderator adjudicates (registers dontcare or issues spec-delta)."""

    gate_id = GATE_H5

    def run(self, ctx: GateContext) -> GateResult:
        evidence: list[str] = []
        failed = False

        siblings = [Path(p) for p in ctx.sibling_instances]
        if not siblings:
            evidence.append("N=1: differential gate not applicable for this admission")
        elif ctx.diff_suite_dir is None:
            return GateResult(
                gate_id=self.gate_id,
                status=STATUS_FAIL,
                evidence=["N>=2 instances require a diff suite; none provided (fail-closed)"],
            )
        else:
            suite = load_suite(Path(ctx.diff_suite_dir))
            dontcares = tuple(ctx.gate_config(self.gate_id).get("dontcare_paths", []))
            for i, sib in enumerate(siblings):
                report = diff_instances(suite, Path(ctx.diff_suite_dir), ctx.instance_dir, sib, dontcares)
                evidence.append(
                    f"diff vs instance[{i}] ({sib.name}): {report.equivalence}, inputs_run={report.inputs_run}, divergences={len(report.divergences)}"
                )
                for d in report.divergences[:10]:
                    evidence.append(f"  DIVERGE {d.input_id} @ {d.path}: {d.a_value} vs {d.b_value}")
                if report.divergences:
                    failed = True

        for gc in ctx.golden_checks:
            name = gc.get("name", "golden")
            golden_path = Path(gc["golden"])
            argv = gc["argv"]
            proc = subprocess.run(
                argv,
                cwd=str(ctx.instance_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=float(gc.get("timeout_s", 120)),
            )
            if proc.returncode != 0:
                failed = True
                evidence.append(f"golden {name}: producer command failed exit={proc.returncode}")
                continue
            ok, detail = compare_golden(proc.stdout.decode("utf-8", errors="replace"), golden_path)
            evidence.append(f"golden {name}: {detail}")
            if not ok:
                failed = True

        return GateResult(
            gate_id=self.gate_id,
            status=STATUS_FAIL if failed else STATUS_PASS,
            evidence=tuple(evidence),
            details={"siblings": len(siblings), "golden_checks": len(ctx.golden_checks)},
        )
