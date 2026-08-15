import pytest

from swarmfoundry.schema.envelope import (
    METHOD_ADMISSION_DECISION,
    METHOD_GATE_RESULT,
    METHOD_JUDGE_VERDICT,
    METHOD_TASK_ASSIGN,
    ProtocolViolation,
    SwarmEnvelope,
    assert_information_asymmetry,
)


def _env(sender, recipient, method, payload=None):
    return SwarmEnvelope(
        envelope_id="e-x",
        sender_role=sender,
        recipient_role=recipient,
        method=method,
        payload=payload or {},
    )


def test_builder_cannot_receive_verdicts():
    for m in (METHOD_GATE_RESULT, METHOD_JUDGE_VERDICT, METHOD_ADMISSION_DECISION):
        with pytest.raises(ProtocolViolation):
            assert_information_asymmetry(_env("verifier", "builder", m))


def test_builder_cannot_discriminate():
    for m in (METHOD_GATE_RESULT, METHOD_JUDGE_VERDICT, METHOD_ADMISSION_DECISION):
        with pytest.raises(ProtocolViolation):
            assert_information_asymmetry(_env("builder", "leader", m))


def test_holdout_material_blocked_for_builder():
    with pytest.raises(ProtocolViolation):
        assert_information_asymmetry(
            _env("leader", "builder", METHOD_TASK_ASSIGN, {"bundle": {"holdout_scenarios": ["ho-1"]}})
        )


def test_normal_task_assignment_allowed():
    assert_information_asymmetry(
        _env("leader", "builder", METHOD_TASK_ASSIGN, {"task_id": "t1", "spec_ref": "spec-delta-1"})
    )


def test_verifier_to_leader_admission_allowed():
    assert_information_asymmetry(_env("verifier", "leader", METHOD_ADMISSION_DECISION, {"admitted": True}))
