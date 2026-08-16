from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from swarm_kernel.admission.transaction import AdmissionTransaction
from swarm_kernel.contracts.admission import AdmissionDecision, DriftCheckSummary, EvidenceReceipt
from swarm_kernel.contracts.base import RLevel, Verdict
from swarm_kernel.contracts.fanout import DiscardedInstance, FanoutRequest, MeasurementClassification, MeasurementEvent
from swarm_kernel.contracts.gates import GateId, GateSuiteResult
from swarm_kernel.contracts.oracle import JudgeVerdict
from swarm_kernel.contracts.wave import WavePlan
from swarm_kernel.diff.engine import DiffReport, run_differential
from swarm_kernel.gates.base import GateConfig, GateContext
from swarm_kernel.gates.runner import run_suite
from swarm_kernel.measure.engine import classify_fanout
from swarm_kernel.spec_repo.registry import ClauseRegistry

NON_DIFF_GATES = [g for g in GateId if g != GateId.H5_DIFFERENTIAL]


@dataclass
class PipelineOutcome:
    fanout: FanoutRequest
    suites: dict[str, GateSuiteResult] = field(default_factory=dict)
    per_instance_pass: dict[str, bool] = field(default_factory=dict)
    diff_report: Optional[DiffReport] = None
    measurement: Optional[MeasurementEvent] = None
    decision: Optional[AdmissionDecision] = None
    chosen_instance: str = ""
    hold_reason: str = ""

    @property
    def admitted(self) -> bool:
        return self.decision is not None and self.decision.admit


def _instance_pass_excluding_diff(suite: GateSuiteResult) -> bool:
    m = suite.by_gate()
    return all(g in m and m[g].verdict == Verdict.PASS for g in NON_DIFF_GATES)


def run_fanout_pipeline(
    fanout: FanoutRequest,
    instances: list[Path],
    oracle_dir: Path,
    registry: Optional[ClauseRegistry],
    work_root: Path,
    out_dir: Path,
    judge_verdicts: Optional[dict[str, JudgeVerdict]] = None,
    wave: Optional[WavePlan] = None,
    config: Optional[GateConfig] = None,
) -> PipelineOutcome:
    outcome = PipelineOutcome(fanout=fanout)
    judge_verdicts = judge_verdicts or {}
    config = config or GateConfig()
    out_dir.mkdir(parents=True, exist_ok=True)
    if len(instances) != fanout.n_instances:
        raise ValueError(f"fanout expects {fanout.n_instances} instances, got {len(instances)}")
    for inst in instances:
        ctx = GateContext(
            instance_dir=inst,
            oracle_dir=oracle_dir,
            registry=registry,
            out_dir=out_dir / inst.name,
            wave=wave,
            config=config,
            peer_instances=list(instances),
            diff_seed=fanout.seed,
        )
        suite = run_suite(ctx)
        outcome.suites[inst.name] = suite
        outcome.per_instance_pass[inst.name] = _instance_pass_excluding_diff(suite)
    if len(instances) >= 2:
        outcome.diff_report = run_differential(instances, oracle_dir, seed=fanout.seed)
        divergence = outcome.diff_report.divergent
        divergence_inputs = [str(i) for i in outcome.diff_report.divergent_inputs[:5]]
    else:
        divergence = False
        divergence_inputs = []
    outcome.measurement = classify_fanout(
        fanout.fanout_id,
        fanout.delta_id,
        outcome.per_instance_pass,
        divergence_detected=divergence,
        divergence_inputs=divergence_inputs,
    )
    cls = outcome.measurement.classification
    if cls == MeasurementClassification.INSUFFICIENT_SAMPLES:
        outcome.hold_reason = "regenerate: samples insufficient, fan out to >=3"
        return outcome
    if cls == MeasurementClassification.DIVERGENCE:
        outcome.hold_reason = "spec_moderator: ambiguity detected, converge spec"
        return outcome
    if cls == MeasurementClassification.TIER_UPGRADE_REQUIRED:
        outcome.hold_reason = "tier_upgrade: retry with stronger model tier"
        return outcome
    if cls == MeasurementClassification.SPEC_ORACLE_CONFLICT:
        outcome.hold_reason = "escalate: spec-oracle conflict, steward+architect review"
        return outcome
    if cls == MeasurementClassification.SILENCE:
        outcome.hold_reason = "spec_moderator: silence detected, register don't-care or add clause before admission"
        return outcome
    passing = sorted(name for name, ok in outcome.per_instance_pass.items() if ok)
    if not passing:
        outcome.hold_reason = "no passing instance"
        return outcome
    chosen = passing[0]
    outcome.chosen_instance = chosen
    suite = outcome.suites[chosen]
    h7 = suite.by_gate().get(GateId.H7_DRIFT)
    drift_summary = DriftCheckSummary(
        stale=int(h7.details.get("stale", 0)) if h7 else 0,
        orphan=int(h7.details.get("orphan", 0)) if h7 else 0,
        unimplemented=int(h7.details.get("unimplemented", 0)) if h7 else 0,
        ok=int(h7.details.get("ok", 0)) if h7 else 0,
    )
    discarded = [
        DiscardedInstance(instance_id=name, measurement_conclusion="discarded after closure; behavior equivalent on oracle+diff corpus")
        for name in passing
        if name != chosen
    ]
    receipt = EvidenceReceipt(
        wave_id=fanout.wave_id,
        delta_id=fanout.delta_id,
        r_level=fanout.r_level,
        chosen_instance_id=chosen,
        discarded=discarded,
        gate_suite=suite,
        judge_verdict=judge_verdicts.get(chosen),
        diff_conclusion="empty" if not divergence else "present",
        drift_check=drift_summary,
        measurement_conclusion=cls.value,
    )
    tx = AdmissionTransaction(work_root)
    import shutil

    shutil.copytree(instances[[i.name for i in instances].index(chosen)], tx.staging / chosen, dirs_exist_ok=True)
    outcome.decision = tx.admit(receipt)
    if not outcome.decision.admit:
        outcome.hold_reason = f"admission refused: {outcome.decision.reasons}"
    return outcome
