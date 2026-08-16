from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from swarmdev.contracts import OracleBundle
from swarmdev.drift.contract_hash import ContractHashStore
from swarmdev.drift.detector import DriftDetector
from swarmdev.gates.h1_build import BuildGate
from swarmdev.gates.h2_unit import UnitGate
from swarmdev.gates.h3_holdout import HoldoutGate
from swarmdev.gates.h4_contract import ContractGate
from swarmdev.gates.h5_diff import DifferentialGate
from swarmdev.gates.h6_invariant import InvariantGate
from swarmdev.gates.h7_drift import DriftGate
from swarmdev.gates.h8_budget import BudgetGate
from swarmdev.gates.protocol import GateContext
from swarmdev.gates.runner import GateRunner
from swarmdev.oracle.diff_engine import DifferentialEngine


def drift_detector_callable(
    detector: DriftDetector,
) -> Callable[[GateContext], tuple[bool, str]]:
    def _detect(ctx: GateContext) -> tuple[bool, str]:
        report = detector.detect(ctx.spec, Path(ctx.instance_dir))
        detail = "; ".join(f"{e.kind}:{e.detail}" for e in report.events) or "no drift"
        return report.clean, detail

    return _detect


def build_gate_runner(
    build_commands: list[list[str]],
    test_command: list[str],
    bundle: Optional[OracleBundle] = None,
    oracle_files: Optional[list[Path]] = None,
    diff_engine: Optional[DifferentialEngine] = None,
    diff_inputs: Optional[list[str]] = None,
    golden_store=None,
    golden_artifact_id: Optional[str] = None,
    dangerous_patterns: Optional[list[str]] = None,
    import_allowlist: Optional[list[str]] = None,
    max_tokens: Optional[int] = None,
    max_duration_s: Optional[float] = None,
    drift_detector: Optional[DriftDetector] = None,
    fail_fast: bool = True,
) -> GateRunner:
    gates = [
        BuildGate(build_commands),
        UnitGate(test_command, oracle_files=oracle_files),
        HoldoutGate(bundle),
        ContractGate(),
    ]
    if diff_engine is not None:
        pool = list(diff_inputs or [])
        cursor = {"i": 0}

        def _next_input() -> str:
            if not pool:
                return ""
            value = pool[cursor["i"] % len(pool)]
            cursor["i"] += 1
            return value

        gates.append(DifferentialGate(diff_engine, _next_input, n_inputs=len(pool),
                                      golden_store=golden_store,
                                      golden_artifact_id=golden_artifact_id))
    gates.append(InvariantGate(dangerous_patterns or [], import_allowlist=import_allowlist))
    if drift_detector is not None:
        gates.append(DriftGate(drift_detector_callable(drift_detector)))
    gates.append(BudgetGate(max_tokens=max_tokens, max_duration_s=max_duration_s))
    return GateRunner(gates, fail_fast=fail_fast)
