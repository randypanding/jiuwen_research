from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from swarmdev.contracts.oracle import Expectation, HoldoutScenario


class ScenarioResult(BaseModel):
    scenario_id: str
    passed: bool
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    details: str = ""
    duration_s: float = 0.0


class ScenarioRunner:
    def run(self, scenario: HoldoutScenario, workspace: Path) -> ScenarioResult:
        started = time.monotonic()
        workspace = Path(workspace)
        if scenario.cwd is None:
            cwd = workspace
        elif Path(scenario.cwd).is_absolute():
            cwd = Path(scenario.cwd)
        else:
            cwd = workspace / scenario.cwd
        env = {**os.environ, **scenario.env}

        def finish(
            passed: bool,
            exit_code: int | None = None,
            stdout: str = "",
            stderr: str = "",
            details: str = "",
        ) -> ScenarioResult:
            return ScenarioResult(
                scenario_id=scenario.scenario_id,
                passed=passed,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                details=details,
                duration_s=time.monotonic() - started,
            )

        for command in scenario.setup_commands:
            try:
                proc = subprocess.run(
                    command, shell=True, cwd=cwd, env=env,
                    capture_output=True, text=True, timeout=scenario.timeout_s,
                )
            except subprocess.TimeoutExpired:
                return finish(False, details=f"timeout in setup command: {command}")
            if proc.returncode != 0:
                return finish(
                    False,
                    exit_code=proc.returncode,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    details=f"setup command failed: {command} (exit {proc.returncode})",
                )
        try:
            proc = subprocess.run(
                scenario.run_command, shell=True, cwd=cwd, env=env,
                capture_output=True, text=True, timeout=scenario.timeout_s,
            )
        except subprocess.TimeoutExpired:
            return finish(
                False,
                details=f"timeout after {scenario.timeout_s}s: {scenario.run_command}",
            )
        failures = self._check(scenario.expectation, proc.returncode, proc.stdout, proc.stderr, cwd)
        return finish(
            not failures,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            details="; ".join(failures),
        )

    @staticmethod
    def _check(
        expectation: Expectation,
        exit_code: int,
        stdout: str,
        stderr: str,
        cwd: Path,
    ) -> list[str]:
        failures = []
        if expectation.exit_code is not None and exit_code != expectation.exit_code:
            failures.append(f"exit_code {exit_code} != expected {expectation.exit_code}")
        if expectation.stdout_regex is not None and re.search(expectation.stdout_regex, stdout) is None:
            failures.append(f"stdout does not match regex {expectation.stdout_regex!r}")
        if expectation.stderr_regex is not None and re.search(expectation.stderr_regex, stderr) is None:
            failures.append(f"stderr does not match regex {expectation.stderr_regex!r}")
        for rel in expectation.files_exist:
            if not (cwd / rel).exists():
                failures.append(f"missing file {rel}")
        for rel, pattern in expectation.files_contain.items():
            path = cwd / rel
            if not path.exists():
                failures.append(f"missing file {rel}")
                continue
            if re.search(pattern, path.read_text(encoding="utf-8")) is None:
                failures.append(f"file {rel} does not match regex {pattern!r}")
        return failures
