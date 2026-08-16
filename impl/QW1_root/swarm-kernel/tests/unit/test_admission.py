from __future__ import annotations

import json
import shutil

import pytest

from swarm_kernel.admission.transaction import AdmissionTransaction
from swarm_kernel.contracts.admission import DriftCheckSummary, EvidenceReceipt
from swarm_kernel.contracts.base import Verdict
from swarm_kernel.contracts.fanout import DiscardedInstance
from swarm_kernel.contracts.gates import GateId, GateResult, GateSuiteResult
from swarm_kernel.contracts.oracle import JudgeVerdict, JudgeVerdictKind
from swarm_kernel.contracts.base import RLevel


def make_suite_pass(instance_id: str) -> GateSuiteResult:
    suite = GateSuiteResult(instance_id=instance_id)
    for g in GateId:
        suite.results.append(GateResult(gate_id=g, verdict=Verdict.PASS))
    return suite


def make_receipt(instance_id: str, suite: GateSuiteResult | None = None, veto: bool = False) -> EvidenceReceipt:
    verdict = JudgeVerdict(rubric_id="rub-1", instance_id=instance_id, kind=JudgeVerdictKind.VETO if veto else JudgeVerdictKind.NO_VETO)
    return EvidenceReceipt(
        wave_id="wave-1",
        delta_id="sd-1",
        r_level=RLevel.R1,
        chosen_instance_id=instance_id,
        discarded=[DiscardedInstance(instance_id="other", measurement_conclusion="silence on inverted bounds")],
        gate_suite=suite or make_suite_pass(instance_id),
        judge_verdict=verdict,
        drift_check=DriftCheckSummary(ok=2),
        measurement_conclusion="closed",
    )


def stage_instance(work_root, instance, name: str | None = None) -> str:
    tx = AdmissionTransaction(work_root)
    target = tx.staging / (name or instance.name)
    shutil.copytree(instance, target, dirs_exist_ok=True)
    return target.name


def test_admit_commits_with_evidence(instance, work_root) -> None:
    name = stage_instance(work_root, instance("good"))
    tx = AdmissionTransaction(work_root)
    receipt = make_receipt(name)
    decision = tx.admit(receipt)
    assert decision.admit, decision.reasons
    evidence = tx.world / name / "EVIDENCE.json"
    assert evidence.exists()
    loaded = EvidenceReceipt.model_validate_json(evidence.read_text(encoding="utf-8"))
    assert loaded.chosen_instance_id == name
    ok, bad_tx = tx.verify_ledger_chain()
    assert ok


def test_admit_refuses_failed_hard_gates(instance, work_root) -> None:
    name = stage_instance(work_root, instance("bad"))
    tx = AdmissionTransaction(work_root)
    suite = make_suite_pass(name)
    suite.results[2] = GateResult(gate_id=GateId.H3_HOLDOUT, verdict=Verdict.FAIL)
    decision = tx.admit(make_receipt(name, suite=suite))
    assert not decision.admit
    assert any("H3" in r for r in decision.reasons)
    assert not (tx.world / name).exists()


def test_admit_refuses_soft_veto(instance, work_root) -> None:
    name = stage_instance(work_root, instance("good"))
    tx = AdmissionTransaction(work_root)
    decision = tx.admit(make_receipt(name, veto=True))
    assert not decision.admit
    assert any("veto" in r for r in decision.reasons)


def test_rollback_restores_absent_state(instance, work_root) -> None:
    name = stage_instance(work_root, instance("good"))
    tx = AdmissionTransaction(work_root)
    decision = tx.admit(make_receipt(name))
    assert decision.admit
    rb = tx.rollback(decision.transaction_id)
    assert rb.admit
    assert not (tx.world / name).exists()
    ok, _ = tx.verify_ledger_chain()
    assert ok


def test_rollback_restores_previous_content(instance, work_root) -> None:
    name = stage_instance(work_root, instance("good"))
    tx = AdmissionTransaction(work_root)
    d1 = tx.admit(make_receipt(name))
    marker = tx.world / name / "MARKER.txt"
    marker.write_text("world-state-v1", encoding="utf-8")
    name2 = stage_instance(work_root, instance("good"), name=name)
    d2 = tx.admit(make_receipt(name))
    assert d2.admit
    rb = tx.rollback(d2.transaction_id)
    assert rb.admit
    assert (tx.world / name / "MARKER.txt").read_text(encoding="utf-8") == "world-state-v1"


def test_ledger_tamper_detected(instance, work_root) -> None:
    name = stage_instance(work_root, instance("good"))
    tx = AdmissionTransaction(work_root)
    tx.admit(make_receipt(name))
    lines = tx.ledger_path.read_text(encoding="utf-8").splitlines()
    tampered = json.loads(lines[0])
    tampered["instance_id"] = "evil"
    tx.ledger_path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
    ok, bad_tx = tx.verify_ledger_chain()
    assert not ok
