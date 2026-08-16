from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from swarmfoundry.schema.gates import HARD_GATES, SOFT_GATES, AdmissionDecision, GateResult, admit
from swarmfoundry.schema.receipt import CostRecord, DiscardedMeasurement, EvidenceReceipt
from swarmfoundry.gates.base import Gate
from swarmfoundry.gates.context import GateContext
from swarmfoundry.gates.h1_build import H1BuildGate
from swarmfoundry.gates.h2_unit import H2UnitTestGate
from swarmfoundry.gates.h3_holdout import H3HoldoutGate
from swarmfoundry.gates.h4_contract import H4ContractGate
from swarmfoundry.gates.h5_diff import H5DiffGate
from swarmfoundry.gates.h6_guard import H6GuardGate
from swarmfoundry.gates.h7_drift import H7DriftGate
from swarmfoundry.gates.h8_cost import H8CostGate
from swarmfoundry.gates.judge import SJudgeGate

DEFAULT_HARD: dict[str, type[Gate]] = {
    "H1": H1BuildGate,
    "H2": H2UnitTestGate,
    "H3": H3HoldoutGate,
    "H4": H4ContractGate,
    "H5": H5DiffGate,
    "H6": H6GuardGate,
    "H7": H7DriftGate,
    "H8": H8CostGate,
}


class GateRunner:
    """Executes the gate algebra Admit = ∧H ∧ ∧S. Gates run in deterministic
    order; every gate always runs (no short-circuit) so the evidence receipt is
    complete regardless of outcome."""

    def __init__(self, hard: list[Gate] | None = None, soft: list[Gate] | None = None):
        self.hard = hard if hard is not None else [cls() for _, cls in sorted(DEFAULT_HARD.items())]
        self.soft = soft if soft is not None else [SJudgeGate()]

    def run_all(self, ctx: GateContext) -> tuple[list[GateResult], list[GateResult]]:
        hard = [g.safe_run(ctx) for g in self.hard]
        soft = [g.safe_run(ctx) for g in self.soft]
        return hard, soft

    def decide(self, ctx: GateContext) -> AdmissionDecision:
        hard, soft = self.run_all(ctx)
        return admit(hard, soft, ctx.instance_id)


def build_receipt(
    *,
    wave_id: str,
    spec_delta_id: str,
    ctx: GateContext,
    decision: AdmissionDecision,
    diff_conclusion: str,
    discarded: list[DiscardedMeasurement] | None = None,
    notes: str = "",
) -> EvidenceReceipt:
    drift_clean = all(
        g.status == "pass" for g in decision.hard_results if g.gate_id == "H7"
    )
    return EvidenceReceipt(
        receipt_id=f"rcpt-{uuid.uuid4().hex[:12]}",
        wave_id=wave_id,
        spec_delta_id=spec_delta_id,
        instance_id=ctx.instance_id,
        r_level=ctx.r_level,
        admission=decision,
        diff_conclusion=diff_conclusion,
        drift_clean=drift_clean,
        cost=ctx.costs,
        discarded=tuple(discarded or []),
        notes=notes,
    )


def register_receipt(receipt: EvidenceReceipt, receipts_dir: Path) -> Path:
    receipts_dir = Path(receipts_dir)
    receipts_dir.mkdir(parents=True, exist_ok=True)
    path = receipts_dir / f"{receipt.receipt_id}.json"
    path.write_text(json.dumps(receipt.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path
