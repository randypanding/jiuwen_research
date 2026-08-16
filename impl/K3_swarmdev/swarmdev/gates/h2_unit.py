from __future__ import annotations

import hashlib
import subprocess
import time
from pathlib import Path

from swarmdev.contracts import GateOutcome
from swarmdev.contracts.receipt import GateStatus

from swarmdev.gates.protocol import GateContext


class OwnershipGuard:
    def __init__(self) -> None:
        self._snapshot: dict[str, str] = {}

    def snapshot(self, paths: list[Path]) -> dict[str, str]:
        hashes = {str(path): self._hash(path) for path in paths}
        self._snapshot = dict(hashes)
        return hashes

    def verify(self, paths: list[Path]) -> list[Path]:
        changed = []
        for path in paths:
            if self._snapshot.get(str(path)) != self._hash(path):
                changed.append(path)
        return changed

    @staticmethod
    def _hash(path: Path) -> str:
        try:
            return hashlib.sha256(Path(path).read_bytes()).hexdigest()
        except FileNotFoundError:
            return "missing"


class UnitGate:
    gate_id = "H2"

    def __init__(self, test_command: list[str], oracle_files: list[Path] | None = None):
        self.test_command = list(test_command)
        self.oracle_files = list(oracle_files or [])
        self.guard = OwnershipGuard()

    def run(self, ctx: GateContext) -> GateOutcome:
        started = time.monotonic()
        if self.oracle_files:
            self.guard.snapshot(self.oracle_files)
        proc = subprocess.run(self.test_command, cwd=ctx.workspace, capture_output=True, text=True)
        tampered = self.guard.verify(self.oracle_files) if self.oracle_files else []
        if tampered:
            # PDR-001：agent 不得修改测试/oracle 文件，篡改即否决
            return GateOutcome(
                gate_id=self.gate_id,
                status=GateStatus.FAIL,
                details="oracle/test files were modified: " + ", ".join(str(p) for p in tampered),
                duration_s=time.monotonic() - started,
            )
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout or "").strip()[-500:]
            return GateOutcome(
                gate_id=self.gate_id,
                status=GateStatus.FAIL,
                details=f"test command failed: {self.test_command}\nstderr tail: {tail}",
                duration_s=time.monotonic() - started,
            )
        return GateOutcome(
            gate_id=self.gate_id,
            status=GateStatus.PASS,
            details=f"unit tests passed ({len(self.oracle_files)} oracle file(s) intact)",
            duration_s=time.monotonic() - started,
        )
