from __future__ import annotations

import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from opc.schemas.common import Verdict
from opc.schemas.gates import CheckResult, GateReport
from opc.schemas.spec import SpecRepoManifest


@dataclass
class GateContext:
    instance_id: str
    instance_dir: Path
    spec_dir: Path
    manifest: SpecRepoManifest
    wave_id: str = ""
    contract_id: str = ""
    holdout_dir: Path | None = None
    baseline_dir: Path | None = None
    sibling_instances: dict[str, Path] = field(default_factory=dict)
    corpus_file: Path | None = None
    golden_dir: Path | None = None
    policy_file: Path | None = None
    python: str = field(default_factory=lambda: sys.executable)
    extra: dict[str, Any] = field(default_factory=dict)

    def policy(self) -> dict[str, Any]:
        if self.policy_file is None or not Path(self.policy_file).exists():
            return {}
        import yaml

        with Path(self.policy_file).open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def contract(self):
        if not self.contract_id:
            return None
        return self.manifest.contract_by_id(self.contract_id)

    def r_level(self):
        contract = self.contract()
        return contract.r_level if contract else None


class Gate(ABC):
    gate_id: str = "H0"

    @abstractmethod
    def run(self, ctx: GateContext) -> GateReport: ...

    def report(
        self,
        ctx: GateContext,
        verdict: Verdict,
        checks: list[CheckResult],
        started: float,
        artifacts: dict[str, str] | None = None,
    ) -> GateReport:
        return GateReport(
            gate=self.gate_id,
            verdict=verdict,
            checks=checks,
            instance_id=ctx.instance_id,
            wave_id=ctx.wave_id,
            duration_s=round(time.monotonic() - started, 4),
            artifacts=artifacts or {},
        )


def worst(verdicts: list[Verdict]) -> Verdict:
    if any(v is Verdict.FAIL for v in verdicts):
        return Verdict.FAIL
    if any(v is Verdict.INCONCLUSIVE for v in verdicts):
        return Verdict.INCONCLUSIVE
    return Verdict.PASS


def check(check_id: str, ok: bool, detail: str = "") -> CheckResult:
    return CheckResult(id=check_id, status=Verdict.PASS if ok else Verdict.FAIL, detail=detail)
