from __future__ import annotations

from swarm_kernel.contracts.fanout import MeasurementClassification, MeasurementEvent
from swarm_kernel.contracts.health import MigrationStage
from swarm_kernel.contracts.oracle import JudgeVerdict, JudgeVerdictKind
from swarm_kernel.contracts.spec import SpecDoc
from swarm_kernel.measure.health import EventLog, compute_health


def test_health_computation(tmp_path, spec_path) -> None:
    log = EventLog(tmp_path / "events.jsonl")
    log.append("measurement", MeasurementEvent(fanout_id="fo-1", delta_id="sd-1", n_instances=3, pass_count=3, fail_count=0, classification=MeasurementClassification.CLOSED).model_dump(mode="json"))
    log.append("measurement", MeasurementEvent(fanout_id="fo-2", delta_id="sd-2", n_instances=3, pass_count=3, fail_count=0, divergence_detected=True, classification=MeasurementClassification.SILENCE).model_dump(mode="json"))
    log.append("judge_verdict", JudgeVerdict(rubric_id="r", instance_id="i", kind=JudgeVerdictKind.NO_VETO).model_dump(mode="json"))
    log.append("judge_verdict", JudgeVerdict(rubric_id="r", instance_id="i2", kind=JudgeVerdictKind.ABSTAIN).model_dump(mode="json"))
    log.append("judge_calibration", {"kappa": 0.72})
    log.append("admitted", {"instance": "i"})
    log.append("admitted", {"instance": "i2"})
    log.append("escaped_defect", {"instance": "i2"})
    log.append("cost", {"tokens": 12345})
    spec = SpecDoc.model_validate_json(spec_path.read_text(encoding="utf-8"))
    snap = compute_health(log, spec=spec, stage=MigrationStage.M1_ANCHOR, period="2026-W33")
    assert snap.closure_rate == 0.5
    assert snap.spec_entropy_events_per_delta == 0.5
    assert snap.witness_coverage == 1.0
    assert snap.unverifiable_clauses == 0
    assert snap.escape_defect_rate == 0.5
    assert snap.judge_calibration_kappa == 0.72
    assert snap.judge_abstention_rate == 0.5
    assert snap.admission_cost_tokens == 12345
    assert snap.stage == MigrationStage.M1_ANCHOR


def test_health_empty_log(tmp_path) -> None:
    log = EventLog(tmp_path / "events.jsonl")
    snap = compute_health(log)
    assert snap.closure_rate == 0.0
    assert snap.witness_coverage == 0.0
