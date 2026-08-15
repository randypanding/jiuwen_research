import hashlib

import pytest

from swarmdev.admission import AdmissionOrchestrator, BuiltInstance
from swarmdev.contracts import (
    CapabilityError,
    ContractBus,
    EnvelopeKind,
    GateOutcome,
    JudgeVerdict,
    RLevel,
    Role,
    SoftVerdict,
    SpecDoc,
    Wave,
    WaveState,
    WaveTask,
    make_token,
)
from swarmdev.contracts.receipt import GateStatus


def _spec():
    return SpecDoc(spec_id="SPEC-demo-0001", domain="demo", version="1.0.0",
                   l1_intent="demo intent")


def _wave(n=2, r_level=RLevel.R0, ru_id="RU-1"):
    return Wave(wave_id="WAVE-test-0001", spec_delta_ids=["DLT-1"],
                tasks=[WaveTask(ru_id=ru_id, spec_delta_ref="DLT-1",
                                r_level=r_level, fanout={"n_target": n})])


def make_builder(costs=(100, 100, 100), tier="L"):
    def factory(task, i):
        return BuiltInstance(instance_id=f"INST-{task.ru_id}-{i}",
                             instance_dir=f"/tmp/inst-{task.ru_id}-{i}",
                             tier=tier,
                             cost_tokens=costs[i] if i < len(costs) else 100)
    return factory


def make_gates(details_by_instance=None, fail_instances=(), drop_gates=()):
    def executor(built, task):
        outs = []
        for gi in range(1, 9):
            gate_id = f"H{gi}"
            if gate_id in drop_gates:
                continue
            if built.instance_id in fail_instances:
                status = GateStatus.FAIL
            else:
                status = GateStatus.PASS
            details = "ok"
            if details_by_instance is not None:
                details = details_by_instance.get(built.instance_id, "ok")
            outs.append(GateOutcome(gate_id=gate_id, status=status, details=details))
        return outs
    return executor


def test_all_pass_closed_admitted():
    orch = AdmissionOrchestrator(make_builder(costs=(120, 80)), make_gates())
    wave = _wave(n=2)
    outcome = orch.execute_wave(wave, _spec(), None)
    assert outcome.admitted is True
    assert outcome.final_state == WaveState.COMMITTED
    assert wave.state == WaveState.COMMITTED
    assert outcome.outcomes == {"RU-1": "CLOSED"}
    (receipt,) = outcome.receipts
    assert receipt.admitted is True
    assert receipt.chosen_instance_id == "INST-RU-1-1"
    assert receipt.commit_ref == "sha:" + hashlib.sha256(b"INST-RU-1-1").hexdigest()[:12]
    assert receipt.rollback_ref is None
    assert [d.instance_id for d in receipt.discarded_instances] == ["INST-RU-1-0"]
    conclusion = receipt.discarded_instances[0].measurement_conclusion
    assert conclusion.startswith("CLOSED") and len(conclusion) > len("CLOSED")
    assert len(receipt.hard_gate_outcomes) == 8


def test_behavioral_difference_silence_rolled_back():
    details = {"INST-RU-1-0": "sort: timsort", "INST-RU-1-1": "sort: quicksort"}
    orch = AdmissionOrchestrator(make_builder(), make_gates(details_by_instance=details))
    wave = _wave(n=2)
    outcome = orch.execute_wave(wave, _spec(), None)
    assert outcome.outcomes == {"RU-1": "SILENCE"}
    assert outcome.admitted is False
    assert outcome.final_state == WaveState.ROLLED_BACK
    assert wave.state == WaveState.ROLLED_BACK
    (receipt,) = outcome.receipts
    assert receipt.admitted is False
    assert receipt.commit_ref is None
    assert receipt.rollback_ref == "rollback:WAVE-test-0001"
    assert receipt.chosen_instance_id == "INST-RU-1-0"


def test_all_fail_spec_oracle_conflict_rolled_back():
    orch = AdmissionOrchestrator(
        make_builder(),
        make_gates(fail_instances={"INST-RU-1-0", "INST-RU-1-1", "INST-RU-1-2"}))
    wave = _wave(n=3)
    outcome = orch.execute_wave(wave, _spec(), None)
    assert outcome.outcomes == {"RU-1": "SPEC_ORACLE_CONFLICT"}
    assert outcome.admitted is False
    assert outcome.final_state == WaveState.ROLLED_BACK
    (receipt,) = outcome.receipts
    assert receipt.admitted is False
    assert receipt.rollback_ref == "rollback:WAVE-test-0001"
    assert len(receipt.discarded_instances) == 2
    assert all(d.measurement_conclusion for d in receipt.discarded_instances)


def test_soft_judge_veto_blocks_admission():
    def judge(built, task):
        return [SoftVerdict(rubric_id="RUB-1",
                            judge=JudgeVerdict(verdict="veto", reasons=["unreadable"]))]

    orch = AdmissionOrchestrator(make_builder(), make_gates(), soft_judge=judge)
    wave = _wave(n=2)
    outcome = orch.execute_wave(wave, _spec(), None)
    assert outcome.outcomes == {"RU-1": "CLOSED"}
    assert outcome.admitted is False
    assert outcome.final_state == WaveState.ROLLED_BACK
    (receipt,) = outcome.receipts
    assert receipt.admitted is False
    assert receipt.hard_pass is True
    assert receipt.soft_pass is False


def test_r3_missing_h5_blocks_admission():
    orch = AdmissionOrchestrator(make_builder(costs=(100,)), make_gates(drop_gates=("H5",)))
    wave = _wave(n=1, r_level=RLevel.R3)
    outcome = orch.execute_wave(wave, _spec(), None)
    assert outcome.outcomes == {"RU-1": "CLOSED"}
    assert outcome.admitted is False
    assert outcome.final_state == WaveState.ROLLED_BACK


def test_r3_with_h5_admits():
    orch = AdmissionOrchestrator(make_builder(costs=(100,)), make_gates())
    wave = _wave(n=1, r_level=RLevel.R3)
    outcome = orch.execute_wave(wave, _spec(), None)
    assert outcome.admitted is True
    assert outcome.final_state == WaveState.COMMITTED


def test_drift_check_false_blocks_admission():
    orch = AdmissionOrchestrator(make_builder(), make_gates(), drift_check=lambda: False)
    wave = _wave(n=2)
    outcome = orch.execute_wave(wave, _spec(), None)
    assert outcome.outcomes == {"RU-1": "CLOSED"}
    assert outcome.admitted is False
    assert outcome.final_state == WaveState.ROLLED_BACK
    assert outcome.receipts[0].drift_check_passed is False


def test_bus_audit_invariants():
    bus = ContractBus()

    def judge(built, task):
        return [SoftVerdict(rubric_id="RUB-1", judge=JudgeVerdict(verdict="no_veto"))]

    orch = AdmissionOrchestrator(make_builder(costs=(120, 80)), make_gates(),
                                 soft_judge=judge, bus=bus)
    wave = _wave(n=2)
    outcome = orch.execute_wave(wave, _spec(), None)
    assert outcome.admitted is True

    audit = bus.audit_stream()
    assert audit
    kinds = {env.kind for env in audit}
    assert EnvelopeKind.SPEC_ASSIGNMENT in kinds
    assert EnvelopeKind.INSTANCE_SUBMISSION in kinds
    assert EnvelopeKind.GATE_RESULTS in kinds
    assert EnvelopeKind.MEASUREMENT_REPORT in kinds
    assert EnvelopeKind.JUDGE_REQUEST in kinds
    assert EnvelopeKind.ADMISSION_RECEIPT in kinds
    assert EnvelopeKind.HOLDOUT_RESULTS not in kinds

    for env in audit:
        if env.kind in (EnvelopeKind.HOLDOUT_RESULTS, EnvelopeKind.JUDGE_REQUEST):
            assert Role.BUILDER not in env.recipients

    for env in audit:
        if env.kind == EnvelopeKind.SPEC_ASSIGNMENT:
            assert set(env.payload) == {"spec_id", "version", "ru_id", "l1_intent"}
            assert "scenarios" not in env.payload

    builder_token = make_token(Role.BUILDER, "INST-RU-1-0", wave.wave_id)
    with pytest.raises(CapabilityError):
        bus.publish(builder_token, EnvelopeKind.GATE_RESULTS, {}, [Role.LEADER])
