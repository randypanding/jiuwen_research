"""Restricted command runner for gates (H1/H2): allowlist + timeout + exit code."""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional

ALLOWED_BINARIES = {"ruff", "mypy", "pytest", "python", "python3", "pip"}


@dataclass
class CommandResult:
    argv: list[str]
    returncode: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    duration_s: float = 0.0
    truncated: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out


MAX_OUTPUT = 200_000


def _trunc(s: str) -> tuple[str, bool]:
    if len(s) > MAX_OUTPUT:
        return s[:MAX_OUTPUT], True
    return s, False


def run_command(argv: list[str], *, cwd: str, timeout: float = 120.0,
                env: Optional[dict[str, str]] = None) -> CommandResult:
    if not argv:
        raise ValueError("empty argv")
    exe = shutil.which(argv[0])
    if exe is None or argv[0] not in ALLOWED_BINARIES:
        raise PermissionError(f"command {argv[0]!r} not in gate allowlist {sorted(ALLOWED_BINARIES)}")
    import os
    import time

    t0 = time.time()
    merged_env = {k: v for k, v in os.environ.items()
                  if k in ("PATH", "HOME", "LANG", "LC_ALL", "TZ", "PYTHONDONTWRITEBYTECODE", "PYTHONPATH")}
    if env:
        merged_env.update(env)
    try:
        proc = subprocess.run(
            [exe, *argv[1:]], cwd=cwd, timeout=timeout, env=merged_env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        out, t1 = proc.stdout or "", proc.stderr or ""
        so, co = _trunc(out)
        se, ce = _trunc(t1)
        return CommandResult(argv=argv, returncode=proc.returncode,
                             stdout=so, stderr=se,
                             duration_s=time.time() - t0, truncated=co or ce)
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        return CommandResult(argv=argv, returncode=-1, stdout=out[:MAX_OUTPUT], stderr=err[:MAX_OUTPUT],
                             timed_out=True, duration_s=time.time() - t0)
