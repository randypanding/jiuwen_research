from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from opc.schemas.common import BaseSchema, Verdict, canonical_json_bytes, sha256_hex
from opc.schemas.oracle import ScenarioSpec

SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict, "enumerate": enumerate,
    "float": float, "frozenset": frozenset, "int": int, "len": len, "list": list, "max": max,
    "min": min, "range": range, "repr": repr, "round": round, "set": set, "sorted": sorted,
    "str": str, "sum": sum, "tuple": tuple, "zip": zip, "isinstance": isinstance, "Exception": Exception,
}

_RUNNER_SNIPPET = textwrap.dedent(
    """
    import importlib, json, sys
    sys.path.insert(0, {instance_dir!r})
    module_name, _, func_name = {entrypoint!r}.partition(":")
    module = importlib.import_module(module_name)
    fn = getattr(module, func_name) if func_name else module
    result = fn(**json.loads({inputs_json!r}))
    print(json.dumps({{"result": result}}, default=str, sort_keys=True))
    """
)


class _Box(BaseSchema):
    value: Any


def load_scenarios(holdout_dir: str | Path) -> list[ScenarioSpec]:
    holdout_dir = Path(holdout_dir)
    scenarios: list[ScenarioSpec] = []
    for path in sorted(holdout_dir.rglob("SCN-*.yaml")):
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        scenarios.append(ScenarioSpec.model_validate(data))
    return scenarios


def redact(obj: Any, paths: list[str]) -> Any:
    if not paths:
        return obj
    data = json.loads(json.dumps(obj, default=str))
    for path in paths:
        keys = path.split(".")
        node = data
        for key in keys[:-1]:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                break
        else:
            if isinstance(node, dict):
                node.pop(keys[-1], None)
    return data


def invoke_entrypoint(
    instance_dir: str,
    entrypoint: str,
    inputs: dict[str, Any],
    timeout_s: float,
    python_executable: str | None = None,
) -> tuple[Any, str]:
    script = _RUNNER_SNIPPET.format(
        instance_dir=instance_dir,
        entrypoint=entrypoint,
        inputs_json=json.dumps(inputs, default=str),
    )
    try:
        proc = subprocess.run(
            [python_executable or sys.executable, "-I", "-c", script],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            cwd=instance_dir,
        )
    except subprocess.TimeoutExpired:
        return None, "timeout"
    if proc.returncode != 0:
        return None, f"crash: {proc.stderr.strip()[-400:]}"
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])["result"], ""
    except (json.JSONDecodeError, IndexError, KeyError) as e:
        return None, f"unparseable output: {e}"


class ScenarioResult(BaseModel):
    scenario_id: str
    status: Verdict
    detail: str = ""
    output_hash: str = ""


class ScenarioRunner:
    """Executes holdout scenarios against an instance in isolated subprocesses.

    The runner is a verifier-side device: scenario content never reaches the
    builder; the instance only experiences a documented entrypoint call.
    """

    def __init__(self, python_executable: str | None = None):
        self.python = python_executable or sys.executable

    def run(self, scenario: ScenarioSpec, instance_dir: str | Path) -> ScenarioResult:
        instance_dir = str(Path(instance_dir).resolve())
        if scenario.oracle_type == "rubric":
            return ScenarioResult(
                scenario_id=scenario.scenario_id,
                status=Verdict.INCONCLUSIVE,
                detail="rubric scenarios are judged by S, not executed",
            )
        if scenario.oracle_type == "metamorphic":
            return self._run_metamorphic(scenario, instance_dir)
        result, err = self._invoke(scenario, instance_dir, scenario.inputs)
        if err:
            return ScenarioResult(scenario_id=scenario.scenario_id, status=Verdict.FAIL, detail=err)
        norm = redact(result, scenario.redact)
        output_hash = sha256_hex(canonical_json_bytes(_Box(value=norm)))
        failures = self._check(scenario, norm)
        if failures:
            return ScenarioResult(
                scenario_id=scenario.scenario_id,
                status=Verdict.FAIL,
                detail="; ".join(failures),
                output_hash=output_hash,
            )
        return ScenarioResult(scenario_id=scenario.scenario_id, status=Verdict.PASS, output_hash=output_hash)

    def _invoke(
        self, scenario: ScenarioSpec, instance_dir: str, inputs: dict[str, Any]
    ) -> tuple[Any, str]:
        return invoke_entrypoint(
            instance_dir, scenario.entrypoint, inputs, scenario.timeout_s, self.python
        )

    def _check(self, scenario: ScenarioSpec, norm: Any) -> list[str]:
        failures: list[str] = []
        for key, expected_value in scenario.expected.items():
            actual = norm.get(key) if isinstance(norm, dict) else norm
            if actual != expected_value:
                failures.append(f"expected[{key}]={expected_value!r} actual={actual!r}")
        for expr in scenario.assertions:
            try:
                ok = bool(
                    eval(  # noqa: S307 - architect-owned, trusted expressions only
                        expr,
                        {"__builtins__": SAFE_BUILTINS},
                        {"result": norm, "inputs": scenario.inputs},
                    )
                )
            except Exception as e:  # noqa: BLE001
                failures.append(f"assertion {expr!r} raised {e!r}")
                continue
            if not ok:
                failures.append(f"assertion failed: {expr!r}")
        return failures

    def _run_metamorphic(self, scenario: ScenarioSpec, instance_dir: str) -> ScenarioResult:
        outputs = []
        for leg in ("r1", "r2"):
            result, err = self._invoke(scenario, instance_dir, scenario.inputs.get(leg, {}))
            if err:
                return ScenarioResult(scenario_id=scenario.scenario_id, status=Verdict.FAIL, detail=f"{leg}: {err}")
            outputs.append(result)
        try:
            ok = bool(
                eval(  # noqa: S307 - architect-owned, trusted expression
                    scenario.metamorphic_relation,
                    {"__builtins__": SAFE_BUILTINS},
                    {"r1": outputs[0], "r2": outputs[1], "inputs": scenario.inputs},
                )
            )
        except Exception as e:  # noqa: BLE001
            return ScenarioResult(scenario_id=scenario.scenario_id, status=Verdict.FAIL, detail=f"relation raised {e!r}")
        if not ok:
            return ScenarioResult(
                scenario_id=scenario.scenario_id,
                status=Verdict.FAIL,
                detail=f"metamorphic relation violated: {scenario.metamorphic_relation}",
            )
        return ScenarioResult(scenario_id=scenario.scenario_id, status=Verdict.PASS)


def run_scenario_file(scenario_path: str | Path, instance_dir: str | Path) -> ScenarioResult:
    with Path(scenario_path).open("r", encoding="utf-8") as f:
        scenario = ScenarioSpec.model_validate(yaml.safe_load(f))
    return ScenarioRunner().run(scenario, instance_dir)
