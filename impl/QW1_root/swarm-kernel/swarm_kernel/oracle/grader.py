from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional

import yaml
from pydantic import ValidationError

from swarm_kernel.contracts.oracle import HoldoutScenario, ScenarioGrading, ScenarioOutcome


class OracleLoadError(Exception):
    pass


def load_scenarios(oracle_dir: str | Path) -> list[HoldoutScenario]:
    path = Path(oracle_dir)
    scenarios: list[HoldoutScenario] = []
    for fp in sorted(path.glob("scenarios/*.yaml")) + sorted(path.glob("scenarios/*.yml")):
        raw = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
        for item in raw.get("scenarios", []):
            try:
                scenarios.append(HoldoutScenario.model_validate(item))
            except ValidationError as e:
                raise OracleLoadError(f"invalid scenario in {fp}: {e}") from e
    return scenarios


def _fresh_load_local_modules(instance_dir: str | Path) -> None:
    inst = Path(instance_dir)
    for fp in sorted(inst.glob("*.py")):
        if fp.name == "swarm_entry.py":
            continue
        unique = f"{fp.stem}__{inst.name}"
        spec = importlib.util.spec_from_file_location(unique, fp)
        if spec is None or spec.loader is None:
            raise OracleLoadError(f"cannot load {fp}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[unique] = module
        spec.loader.exec_module(module)
        sys.modules[fp.stem] = module


def load_instance_adapter(instance_dir: str | Path) -> Callable[[dict[str, Any]], Any]:
    entry = Path(instance_dir) / "swarm_entry.py"
    if not entry.exists():
        raise OracleLoadError(f"instance {instance_dir} lacks swarm_entry.py")
    _fresh_load_local_modules(instance_dir)
    spec = importlib.util.spec_from_file_location(f"swarm_entry_{Path(instance_dir).name}", entry)
    if spec is None or spec.loader is None:
        raise OracleLoadError("cannot load swarm_entry.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if not hasattr(module, "run"):
        raise OracleLoadError("swarm_entry.py must define run(inputs: dict)")
    return module.run


def _match_expectation(expectation: dict[str, Any], actual: Any) -> tuple[bool, str]:
    if "equals" in expectation:
        ok = actual == expectation["equals"]
        return ok, "" if ok else f"expected {expectation['equals']!r}, got {actual!r}"
    if "approx" in expectation:
        target = float(expectation["approx"]["value"])
        tol = float(expectation["approx"].get("tol", 1e-9))
        try:
            ok = abs(float(actual) - target) <= tol
        except (TypeError, ValueError):
            return False, f"non-numeric actual {actual!r}"
        return ok, "" if ok else f"expected ~{target}±{tol}, got {actual!r}"
    if "contains" in expectation:
        ok = expectation["contains"] in str(actual)
        return ok, "" if ok else f"expected to contain {expectation['contains']!r}"
    if "json_equals" in expectation:
        try:
            norm_actual = json.loads(json.dumps(actual, sort_keys=True))
        except (TypeError, ValueError):
            norm_actual = actual
        ok = norm_actual == expectation["json_equals"]
        return ok, "" if ok else f"json mismatch: {actual!r}"
    return False, f"unknown expectation shape: {sorted(expectation.keys())}"


class ScenarioGrader:
    def __init__(self, scenarios: list[HoldoutScenario]) -> None:
        self.scenarios = scenarios

    def grade(self, instance_dir: str | Path) -> tuple[list[ScenarioOutcome], bool]:
        run = load_instance_adapter(instance_dir)
        outcomes: list[ScenarioOutcome] = []
        for sc in self.scenarios:
            try:
                actual = run(dict(sc.inputs))
                ok, msg = _match_expectation(sc.expectation, actual)
            except Exception as e:
                actual = None
                ok, msg = False, f"runtime error: {e}"
            outcomes.append(
                ScenarioOutcome(
                    scenario_id=sc.scenario_id,
                    grading=sc.grading,
                    passed=ok,
                    first_attempt=True,
                    actual=repr(actual)[:500],
                    message=msg,
                )
            )
        required = [o for o in outcomes if o.grading == ScenarioGrading.FAIL_TO_PASS]
        regression = [o for o in outcomes if o.grading == ScenarioGrading.PASS_TO_PASS]
        suite_pass = all(o.passed for o in required) and all(o.passed for o in regression) and bool(required or regression)
        return outcomes, suite_pass
