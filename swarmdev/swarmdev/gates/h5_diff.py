from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Callable

from swarmdev.contracts import GateOutcome, RLevel
from swarmdev.contracts.receipt import GateStatus

from swarmdev.gates.protocol import GateContext
from swarmdev.oracle.diff_engine import DifferentialEngine, default_normalize
from swarmdev.oracle.golden import GoldenStore


class DifferentialGate:
    gate_id = "H5"

    def __init__(
        self,
        engine: DifferentialEngine,
        input_factory: Callable[[], str],
        n_inputs: int,
        golden_store: GoldenStore | None = None,
        golden_artifact_id: str | None = None,
    ):
        self.engine = engine
        self.input_factory = input_factory
        self.n_inputs = n_inputs
        self.golden_store = golden_store
        self.golden_artifact_id = golden_artifact_id

    def run(self, ctx: GateContext) -> GateOutcome:
        started = time.monotonic()
        inputs = [self.input_factory() for _ in range(self.n_inputs)]
        instance_dirs: dict[str, Path] = ctx.extra.get("instance_dirs") or {
            ctx.instance_id: ctx.instance_dir
        }
        if ctx.r_level == RLevel.R3:
            # PDR-001：R3 冻结制品仅前向追加 + 黄金输出锁定
            if self.golden_store is None or self.golden_artifact_id is None:
                return GateOutcome(
                    gate_id=self.gate_id,
                    status=GateStatus.FAIL,
                    details="R3 requires golden_store and golden_artifact_id",
                    duration_s=time.monotonic() - started,
                )
            content = self.golden_content(instance_dirs, inputs)
            verdict = self.golden_store.compare(self.golden_artifact_id, content)
            if verdict.match:
                return GateOutcome(
                    gate_id=self.gate_id,
                    status=GateStatus.PASS,
                    evidence_refs=[f"golden:{self.golden_artifact_id}"],
                    details="golden output matched",
                    duration_s=time.monotonic() - started,
                )
            return GateOutcome(
                gate_id=self.gate_id,
                status=GateStatus.FAIL,
                details=f"golden check failed: {verdict.reason}",
                duration_s=time.monotonic() - started,
            )
        report = self.engine.compare_instances(instance_dirs, inputs)
        if report.passed:
            return GateOutcome(
                gate_id=self.gate_id,
                status=GateStatus.PASS,
                details=f"{report.inputs_run} input(s), no divergence",
                duration_s=time.monotonic() - started,
            )
        lines = [
            f"input {d.input_repr}: " + json.dumps(d.outputs, sort_keys=True)
            for d in report.divergences
        ]
        return GateOutcome(
            gate_id=self.gate_id,
            status=GateStatus.FAIL,
            details="divergences: " + "; ".join(lines),
            duration_s=time.monotonic() - started,
        )

    def golden_content(self, instance_dirs: dict[str, Path], inputs: list[str]) -> str:
        table: dict[str, str] = {}
        for instance_id in sorted(instance_dirs):
            for inp in inputs:
                output = self.engine.runner(instance_dirs[instance_id], inp)
                table[f"{instance_id}|{inp}"] = default_normalize(output)
        return json.dumps(table, sort_keys=True)
