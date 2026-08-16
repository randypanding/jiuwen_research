from __future__ import annotations

import dataclasses
import json
import os
import re
import subprocess
import time
from pathlib import Path

from swarmfoundry.schema.oracle import (
    ORACLE_EXIT_CODE,
    ORACLE_GOLDEN_FILE,
    ORACLE_JSON_ASSERT,
    ORACLE_PROPERTY_SCRIPT,
    ORACLE_STDOUT_REGEX,
    Scenario,
    ScenarioResult,
    ScenarioSuite,
)

REQUIRED_MANIFEST_KEYS = ("PYTHONHASHSEED", "TZ", "SEED")


class OracleError(RuntimeError):
    pass


@dataclasses.dataclass(frozen=True)
class RunOutput:
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    manifest_ok: bool


def _clean_env(manifest: dict) -> dict:
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", "/tmp"),
        "LANG": "C.UTF-8",
    }
    env.update({k: str(v) for k, v in manifest.items()})
    return env


def check_manifest(suite: ScenarioSuite) -> list[str]:
    missing = [k for k in REQUIRED_MANIFEST_KEYS if k not in suite.env_manifest]
    return missing


def run_entrypoint(suite: ScenarioSuite, instance_dir: Path, input_text: str, timeout_s: float) -> RunOutput:
    cmd = suite.entrypoint.replace("{instance}", str(Path(instance_dir).resolve()))
    start = time.monotonic()
    proc = subprocess.run(
        cmd,
        shell=True,
        input=input_text.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_s,
        cwd=str(Path(instance_dir).resolve()),
        env=_clean_env(suite.env_manifest),
    )
    dur = int((time.monotonic() - start) * 1000)
    return RunOutput(
        exit_code=proc.returncode,
        stdout=proc.stdout.decode("utf-8", errors="replace"),
        stderr=proc.stderr.decode("utf-8", errors="replace"),
        duration_ms=dur,
        manifest_ok=not check_manifest(suite),
    )


def _json_path_get(doc, path: str):
    cur = doc
    for part in path.split("."):
        if part == "":
            continue
        if isinstance(cur, list):
            cur = cur[int(part)]
        elif isinstance(cur, dict):
            if part not in cur:
                raise KeyError(part)
            cur = cur[part]
        else:
            raise KeyError(part)
    return cur


def evaluate_scenario(suite: ScenarioSuite, sc: Scenario, out: RunOutput, suite_dir: Path) -> ScenarioResult:
    if not out.manifest_ok:
        return ScenarioResult(sc.id, False, f"env manifest missing keys: {check_manifest(suite)}", out.duration_ms)
    if sc.kind == ORACLE_EXIT_CODE:
        want = int(sc.expected) if sc.expected else 0
        ok = out.exit_code == want
        return ScenarioResult(sc.id, ok, f"exit_code={out.exit_code} want={want}", out.duration_ms)
    if sc.kind == ORACLE_STDOUT_REGEX:
        ok = re.search(sc.expected, out.stdout) is not None
        return ScenarioResult(sc.id, ok, f"regex {'matched' if ok else 'not matched'}", out.duration_ms)
    if sc.kind == ORACLE_JSON_ASSERT:
        try:
            doc = json.loads(out.stdout)
            expected = json.loads(sc.expected)
            for path, want in expected.items():
                got = _json_path_get(doc, path)
                if got != want:
                    return ScenarioResult(sc.id, False, f"json_assert {path}: got {got!r} want {want!r}", out.duration_ms)
            return ScenarioResult(sc.id, True, "json_assert all paths matched", out.duration_ms)
        except Exception as e:
            return ScenarioResult(sc.id, False, f"json_assert error: {e}", out.duration_ms)
    if sc.kind == ORACLE_GOLDEN_FILE:
        from swarmfoundry.oracle.golden import compare_golden

        ok, detail = compare_golden(out.stdout, suite_dir / sc.expected)
        return ScenarioResult(sc.id, ok, detail, out.duration_ms)
    if sc.kind == ORACLE_PROPERTY_SCRIPT:
        script = suite_dir / sc.expected
        env = _clean_env(suite.env_manifest)
        env.update(
            {
                "SCENARIO_STDOUT": out.stdout,
                "SCENARIO_EXIT_CODE": str(out.exit_code),
            }
        )
        try:
            prop = subprocess.run(
                ["python3", str(script)],
                input=out.stdout.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=sc.timeout_s,
                env=env,
            )
            ok = prop.returncode == 0
            detail = prop.stderr.decode("utf-8", errors="replace")[:300] if not ok else "property held"
            return ScenarioResult(sc.id, ok, detail, out.duration_ms)
        except Exception as e:
            return ScenarioResult(sc.id, False, f"property script error: {e}", out.duration_ms)
    return ScenarioResult(sc.id, False, f"unknown oracle kind {sc.kind}", out.duration_ms)


def run_suite(suite: ScenarioSuite, instance_dir: Path, suite_dir: Path) -> list[ScenarioResult]:
    results: list[ScenarioResult] = []
    for sc in suite.scenarios:
        input_path = suite_dir / sc.input_file
        if not input_path.is_file():
            results.append(ScenarioResult(sc.id, False, f"input file missing: {sc.input_file}"))
            continue
        try:
            out = run_entrypoint(suite, instance_dir, input_path.read_text(encoding="utf-8"), sc.timeout_s)
        except subprocess.TimeoutExpired:
            results.append(ScenarioResult(sc.id, False, f"timeout after {sc.timeout_s}s"))
            continue
        except Exception as e:
            results.append(ScenarioResult(sc.id, False, f"entrypoint error: {e}"))
            continue
        results.append(evaluate_scenario(suite, sc, out, suite_dir))
    return results


def load_suite(suite_dir: Path) -> ScenarioSuite:
    suite_dir = Path(suite_dir)
    manifest = suite_dir / "suite.json"
    if not manifest.is_file():
        raise OracleError(f"suite manifest missing: {manifest}")
    return ScenarioSuite.from_dict(json.loads(manifest.read_text(encoding="utf-8")))
