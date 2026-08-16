from __future__ import annotations

from pathlib import Path

from swarm_kernel.admission.transaction import AdmissionTransaction
from swarm_kernel.contracts.fanout import FanoutRequest, MeasurementClassification
from swarm_kernel.contracts.base import RLevel
from swarm_kernel.contracts.oracle import JudgeVerdict, JudgeVerdictKind
from swarm_kernel.contracts.spec import SpecDoc
from swarm_kernel.contracts.wave import FrozenInterface, WavePlan
from swarm_kernel.pipeline import run_fanout_pipeline
from swarm_kernel.spec_repo.registry import ClauseRegistry


def make_wave(spec_path) -> WavePlan:
    spec = SpecDoc.model_validate_json(spec_path.read_text(encoding="utf-8"))
    return WavePlan(spec_id=spec.spec_id, epoch=1, delta_ids=["sd-toy-001"], frozen_interfaces=[])


def test_e2e_closed_path_admits(instance, oracle_dir, spec_path, tmp_path) -> None:
    registry = ClauseRegistry(SpecDoc.model_validate_json(spec_path.read_text(encoding="utf-8")))
    fanout = FanoutRequest(wave_id="wave-1", delta_id="sd-toy-001", r_level=RLevel.R1, n_instances=2, seed=42)
    verdict = JudgeVerdict(rubric_id="rub-toy", instance_id="good", kind=JudgeVerdictKind.NO_VETO)
    outcome = run_fanout_pipeline(
        fanout=fanout,
        instances=[instance("good"), instance("good2")],
        oracle_dir=oracle_dir,
        registry=registry,
        work_root=tmp_path / "world",
        out_dir=tmp_path / "out",
        judge_verdicts={"good": verdict},
        wave=make_wave(spec_path),
    )
    assert outcome.measurement is not None
    assert outcome.measurement.classification == MeasurementClassification.CLOSED
    assert outcome.admitted, outcome.hold_reason or (outcome.decision.reasons if outcome.decision else "")
    assert outcome.chosen_instance == "good"
    tx = AdmissionTransaction(tmp_path / "world")
    assert (tx.world / "good" / "EVIDENCE.json").exists()
    assert (tx.world / "good" / "clamp_impl.py").exists()
    ok, _ = tx.verify_ledger_chain()
    assert ok
    assert len(outcome.suites) == 2


def test_e2e_silence_path_blocks_admission(instance, oracle_dir, spec_path, tmp_path) -> None:
    registry = ClauseRegistry(SpecDoc.model_validate_json(spec_path.read_text(encoding="utf-8")))
    fanout = FanoutRequest(wave_id="wave-1", delta_id="sd-toy-002", r_level=RLevel.R1, n_instances=2, seed=42)
    outcome = run_fanout_pipeline(
        fanout=fanout,
        instances=[instance("divergent_a"), instance("divergent_b")],
        oracle_dir=oracle_dir,
        registry=registry,
        work_root=tmp_path / "world",
        out_dir=tmp_path / "out",
        wave=make_wave(spec_path),
    )
    assert outcome.measurement is not None
    assert outcome.measurement.classification == MeasurementClassification.SILENCE
    assert not outcome.admitted
    assert "don't-care" in outcome.hold_reason
    tx = AdmissionTransaction(tmp_path / "world")
    assert list(tx.world.iterdir()) == []


def test_e2e_failing_instance_never_admitted(instance, oracle_dir, spec_path, tmp_path) -> None:
    registry = ClauseRegistry(SpecDoc.model_validate_json(spec_path.read_text(encoding="utf-8")))
    fanout = FanoutRequest(wave_id="wave-1", delta_id="sd-toy-003", r_level=RLevel.R0, n_instances=1, seed=42)
    outcome = run_fanout_pipeline(
        fanout=fanout,
        instances=[instance("bad")],
        oracle_dir=oracle_dir,
        registry=registry,
        work_root=tmp_path / "world",
        out_dir=tmp_path / "out",
        wave=make_wave(spec_path),
    )
    assert not outcome.admitted
    assert outcome.measurement is not None
    assert outcome.measurement.classification == MeasurementClassification.INSUFFICIENT_SAMPLES
    assert "regenerate" in outcome.hold_reason
    tx = AdmissionTransaction(tmp_path / "world")
    assert list(tx.world.iterdir()) == []


def test_e2e_rollback_after_admission(instance, oracle_dir, spec_path, tmp_path) -> None:
    registry = ClauseRegistry(SpecDoc.model_validate_json(spec_path.read_text(encoding="utf-8")))
    fanout = FanoutRequest(wave_id="wave-1", delta_id="sd-toy-004", r_level=RLevel.R1, n_instances=2, seed=42)
    outcome = run_fanout_pipeline(
        fanout=fanout,
        instances=[instance("good"), instance("good2")],
        oracle_dir=oracle_dir,
        registry=registry,
        work_root=tmp_path / "world",
        out_dir=tmp_path / "out",
        wave=make_wave(spec_path),
    )
    assert outcome.admitted
    tx = AdmissionTransaction(tmp_path / "world")
    rb = tx.rollback(outcome.decision.transaction_id)
    assert rb.admit
    assert not (tx.world / "good").exists()
    ok, _ = tx.verify_ledger_chain()
    assert ok
