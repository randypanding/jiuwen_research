"""Sandboxed instance runner for differential testing.

Protocol: an instance is a command that reads JSON-lines (one input object per
line) from stdin and writes one JSON object per line to stdout. Environment is
normalized (constitution #16: execution separated from generation).
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

ENV_ALLOWLIST = {"PATH", "HOME", "LANG", "LC_ALL", "TZ", "PYTHONHASHSEED", "PYTHONIOENCODING"}


@dataclass
class ExecRecord:
    input: dict[str, Any]
    output: Any = None
    exit_code: Optional[int] = None
    timed_out: bool = False
    duration_s: float = 0.0
    stderr_tail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "input": self.input,
            "output": self.output,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "duration_s": self.duration_s,
            "stderr_tail": self.stderr_tail[-500:],
        }


class InstanceRunError(RuntimeError):
    pass


def run_instance(
    argv: list[str],
    inputs: list[dict[str, Any]],
    *,
    cwd: str = ".",
    timeout_per_input: float = 10.0,
    extra_env: Optional[dict[str, str]] = None,
) -> list[ExecRecord]:
    """Run one input per fresh process: crash containment + per-input records.

    Protocol: a single JSON object on stdin -> a single JSON object (one line)
    on stdout. Exit code != 0 or missing/unparsable output marks that record.
    """
    records: list[ExecRecord] = []
    env = {k: v for k, v in os.environ.items() if k in ENV_ALLOWLIST}
    env["PYTHONHASHSEED"] = "0"
    if extra_env:
        env.update(extra_env)
    for inp in inputs:
        t0 = time.time()
        rec = ExecRecord(input=inp)
        try:
            proc = subprocess.run(
                argv, input=json.dumps(inp, ensure_ascii=False), cwd=cwd, env=env,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                timeout=timeout_per_input,
            )
            rec.exit_code = proc.returncode
            rec.stderr_tail = (proc.stderr or "")[-500:]
            lines = [ln for ln in (proc.stdout or "").splitlines() if ln.strip()]
            if lines:
                try:
                    rec.output = json.loads(lines[-1])
                except json.JSONDecodeError:
                    rec.output = {"__nonjson__": lines[-1][:200]}
            else:
                rec.output = {"__missing__": True}
                rec.exit_code = proc.returncode if proc.returncode != 0 else -1
        except subprocess.TimeoutExpired as e:
            rec.timed_out = True
            rec.exit_code = None
            err = ""
            if e.stderr:
                err = e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr
            rec.stderr_tail = (err or "")[-500:]
        except FileNotFoundError as e:
            raise InstanceRunError(f"instance command not found: {argv[0]}") from e
        rec.duration_s = time.time() - t0
        records.append(rec)
    return records


def write_runner_script(path: str | Path, handler_expr: str) -> None:
    """Write a canonical JSON-line runner for a python function, e.g.
    handler_expr = "demo_adder.good:run"  (module:function, read input dict, return value)."""
    script = f'''#!/usr/bin/env python3
import json, sys
from {handler_expr.split(":")[0]} import {handler_expr.split(":")[1]} as _fn
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    obj = json.loads(line)
    result = _fn(**obj) if isinstance(obj, dict) else _fn(obj)
    print(json.dumps(result, ensure_ascii=False, default=str))
'''
    Path(path).write_text(script, encoding="utf-8")
    os.chmod(path, 0o755)
