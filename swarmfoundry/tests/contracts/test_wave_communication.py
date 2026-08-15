"""Contract-communication tests.

These tests exercise the *communication contracts* between work packages over
the reference bus (C10 transport semantics), exactly as the production swarm
will exchange them through agent-core TeamRuntime / jiuwenswarm E2AEnvelope:

  architect -> leader        wave plan (C09)
  leader    -> builder       task.assign (wave task slice, no holdout material)
  builder   -> leader        task.instances_ready
  leader    -> verifier      verify.request (full gate context incl. holdouts)
  verifier  -> leader        gate.result (H1..H8) + admission.decision (C03)
  leader    -> spec_moderator measurement.event (C11) when divergence found
  leader    -> *             receipt.registered (C04)

Every hop is schema-validated by SwarmEnvelope.from_dict and the
information-asymmetry policy is enforced by the bus itself.
"""

import pytest

from swarmfoundry.comm.bus import BusError, SwarmBus
from swarmfoundry.schema.envelope import (
    METHOD_ADMISSION_DECISION,
    METHOD_GATE_RESULT,
    METHOD_MEASUREMENT_EVENT,
    METHOD_RECEIPT_REGISTERED,
    METHOD_TASK_ASSIGN,
    METHOD_TASK_INSTANCES_READY,
    METHOD_VERIFY_REQUEST,
    SwarmEnvelope,
)
from swarmfoundry.schema.events import OBS_SILENCE, MeasurementEvent, classify_measurement
from swarmfoundry.schema.gates import AdmissionDecision
from swarmfoundry.schema.receipt import EvidenceReceipt
from swarmfoundry.schema.wave import WavePlan


@pytest.fixture()
def fixtures(tmp_path):
    from swarmfoundry.selftest import _write_instance, _write_spec_repo, _write_suite
    from swarmfoundry.specrepo.loader import SpecRepo
    from swarmfoundry.specrepo.seal import reseal
    from swarmfoundry.contracts.extract import dump_surface, extract_surface

    spec_root = tmp_path / "specrepo"
    spec_root.mkdir()
    _write_spec_repo(spec_root)
    repo = SpecRepo(spec_root)
    reseal(repo)
    holdout = tmp_path / "holdout"
    _write_suite(holdout)
    inst_a = tmp_path / "inst-a"
    inst_b = tmp_path / "inst-b"
    inst_c = tmp_path / "inst-c"
    _write_instance(inst_a, round_expr="round(a / b, 6)")
    _write_instance(inst_b, round_expr="round(a / b, 6)")
    _write_instance(inst_c, round_expr="int(a / b)")
    baseline = tmp_path / "baseline" / "calc.surface.json"
    dump_surface(extract_surface(inst_a, "calc"), baseline)
    return {
        "repo": repo,
        "holdout": holdout,
        "inst_a": inst_a,
        "inst_b": inst_b,
        "inst_c": inst_c,
        "baseline": baseline,
        "receipts": tmp_path / "receipts",
    }


def _gate_config():
    return {"gates": {"H2": {"commands": [["python3", "-c", "print('ok')"]]}, "H8": {"max_total_tokens": 10**6}}}


def test_wave_lifecycle_communication_happy_path(fixtures):
    from swarmfoundry.gates.context import GateContext
    from swarmfoundry.gates.runner import GateRunner, build_receipt, register_receipt
    from swarmfoundry.schema import SCHEMA_VERSION
    from swarmfoundry.schema.judge import JudgeVerdict

    bus = SwarmBus()
    trace: list[str] = []
    admitted_holder: dict = {}

    wave = WavePlan.from_dict(
        {
            "schema_version": SCHEMA_VERSION,
            "wave_id": "wave-comm-1",
            "interface_freeze": ["calc"],
            "budget_units": 500.0,
            "tasks": [{"task_id": "t1", "spec_delta_id": "delta-comm", "r_level": "R0", "n_fanout": 2}],
        }
    )

    def leader_on_assign_ready(env: SwarmEnvelope):
        trace.append("leader:instances_ready")
        assert env.payload["task_id"] == "t1"
        SwarmEnvelope.from_dict(env.to_dict())
        bus.send(
            sender_role="leader",
            recipient_role="verifier",
            method=METHOD_VERIFY_REQUEST,
            payload={
                "task_id": "t1",
                "instance_ids": env.payload["instance_ids"],
            },
            correlation_id="t1",
        )

    def verifier_on_request(env: SwarmEnvelope):
        trace.append("verifier:verify_request")
        ctx = GateContext(
            instance_dir=fixtures["inst_a"],
            instance_id="inst-a",
            spec_repo=fixtures["repo"],
            config=_gate_config(),
            r_level="R0",
            holdout_dirs=(fixtures["holdout"],),
            sibling_instances=(fixtures["inst_b"],),
            diff_suite_dir=fixtures["holdout"],
            judge_verdicts=(
                JudgeVerdict("judge-1", "famX", "no_veto", "clean", ()),
                JudgeVerdict("judge-2", "famY", "no_veto", "clean", ()),
            ),
            builder_model_family="famZ",
        )
        decision = GateRunner().decide(ctx)
        bus.send(
            sender_role="verifier",
            recipient_role="leader",
            method=METHOD_GATE_RESULT,
            payload={"task_id": "t1", "gates": [g.to_dict() for g in decision.hard_results]},
            correlation_id="t1",
        )
        bus.send(
            sender_role="verifier",
            recipient_role="leader",
            method=METHOD_ADMISSION_DECISION,
            payload=decision.to_dict(),
            correlation_id="t1",
        )

    def leader_on_admission(env: SwarmEnvelope):
        trace.append("leader:admission")
        decision = AdmissionDecision.from_dict(env.payload)
        admitted_holder["admitted"] = decision.admitted
        ctx = GateContext(
            instance_dir=fixtures["inst_a"],
            instance_id="inst-a",
            spec_repo=fixtures["repo"],
            config=_gate_config(),
            r_level="R0",
        )
        receipt = build_receipt(
            wave_id=wave.wave_id, spec_delta_id="delta-comm", ctx=ctx, decision=decision, diff_conclusion="equivalent"
        )
        path = register_receipt(receipt, fixtures["receipts"])
        EvidenceReceipt.from_dict(__import__("json").loads(path.read_text()))
        bus.send(
            sender_role="leader",
            recipient_role="spec_moderator",
            method=METHOD_RECEIPT_REGISTERED,
            payload={"receipt_id": receipt.receipt_id, "admitted": decision.admitted},
            correlation_id="t1",
        )

    def moderator_on_receipt(env: SwarmEnvelope):
        trace.append("moderator:receipt")
        assert EvidenceReceipt  # schema import contract for the moderation side

    bus.subscribe("builder", METHOD_TASK_ASSIGN, lambda env: trace.append("builder:task_assigned"))
    bus.subscribe("leader", METHOD_TASK_INSTANCES_READY, leader_on_assign_ready)
    bus.subscribe("verifier", METHOD_VERIFY_REQUEST, verifier_on_request)
    bus.subscribe("leader", METHOD_GATE_RESULT, lambda env: trace.append("leader:gate_result"))
    bus.subscribe("leader", METHOD_ADMISSION_DECISION, leader_on_admission)
    bus.subscribe("spec_moderator", METHOD_RECEIPT_REGISTERED, moderator_on_receipt)

    bus.send(
        sender_role="leader",
        recipient_role="builder",
        method=METHOD_TASK_ASSIGN,
        payload={"task_id": "t1", "spec_delta_ref": "delta-comm", "n_fanout": 2},
        correlation_id="t1",
    )
    assert bus.ledger[0].method == METHOD_TASK_ASSIGN

    bus.send(
        sender_role="builder",
        recipient_role="leader",
        method=METHOD_TASK_INSTANCES_READY,
        payload={"task_id": "t1", "instance_ids": ["inst-a", "inst-b"]},
        correlation_id="t1",
    )

    assert trace == ["builder:task_assigned", "leader:instances_ready", "verifier:verify_request", "leader:gate_result", "leader:admission", "moderator:receipt"]
    assert admitted_holder["admitted"] is True
    assert all(e.correlation_id == "t1" for e in bus.ledger)
    assert [e.method for e in bus.ledger] == [
        METHOD_TASK_ASSIGN,
        METHOD_TASK_INSTANCES_READY,
        METHOD_VERIFY_REQUEST,
        METHOD_GATE_RESULT,
        METHOD_ADMISSION_DECISION,
        METHOD_RECEIPT_REGISTERED,
    ]


def test_divergence_triggers_measurement_event_to_moderator(fixtures):
    from swarmfoundry.gates.context import GateContext
    from swarmfoundry.gates.runner import GateRunner
    from swarmfoundry.oracle.diff import diff_instances
    from swarmfoundry.oracle.runner import load_suite

    bus = SwarmBus()
    events: list[MeasurementEvent] = []
    bus.subscribe("spec_moderator", METHOD_MEASUREMENT_EVENT, lambda env: events.append(MeasurementEvent.from_dict(env.payload)))

    ctx = GateContext(
        instance_dir=fixtures["inst_c"],
        instance_id="inst-c",
        spec_repo=fixtures["repo"],
        config=_gate_config(),
        r_level="R0",
        holdout_dirs=(fixtures["holdout"],),
        sibling_instances=(fixtures["inst_a"],),
        diff_suite_dir=fixtures["holdout"],
    )
    decision = GateRunner().decide(ctx)
    assert not decision.admitted

    report = diff_instances(load_suite(fixtures["holdout"]), fixtures["holdout"], fixtures["inst_c"], fixtures["inst_a"])
    assert report.divergences

    # structure.md §6: with <3 instances and a failure present, the reading is
    # 'insufficient' — the leader must top up the fan-out to >=3 before judging.
    assert classify_measurement(2, 1, False) == "insufficient_instances"
    # after topping up to N=3 with the same divergent behavior:
    observation = classify_measurement(3, 1, False)
    assert observation == "divergence"
    event = MeasurementEvent(
        event_id="meas-1",
        spec_delta_id="delta-comm",
        observation=observation,
        n_instances=3,
        n_passed=1,
        diff_empty=False,
        detail=f"H5 blocked: {len(report.divergences)} divergences",
    )
    bus.send(
        sender_role="leader",
        recipient_role="spec_moderator",
        method=METHOD_MEASUREMENT_EVENT,
        payload=event.to_dict(),
        correlation_id="t1",
    )
    assert len(events) == 1 and events[0].observation == "divergence" and events[0].n_instances == 3


def test_builder_cannot_emit_gate_results_over_bus(fixtures):
    bus = SwarmBus()
    bus.subscribe("leader", METHOD_GATE_RESULT, lambda env: None)
    from swarmfoundry.schema.envelope import ProtocolViolation

    with pytest.raises(ProtocolViolation):
        bus.send(
            sender_role="builder",
            recipient_role="leader",
            method=METHOD_GATE_RESULT,
            payload={"gates": []},
        )
    assert bus.ledger == []


def test_task_assign_carrying_holdout_leaks_blocked(fixtures):
    bus = SwarmBus()
    bus.subscribe("builder", METHOD_TASK_ASSIGN, lambda env: None)
    from swarmfoundry.schema.envelope import ProtocolViolation

    with pytest.raises(ProtocolViolation):
        bus.send(
            sender_role="leader",
            recipient_role="builder",
            method=METHOD_TASK_ASSIGN,
            payload={"task_id": "t1", "bundle": {"holdout_scenarios": "calc-holdout-suite"}},
        )


def test_unknown_route_fails_loudly(fixtures):
    bus = SwarmBus()
    with pytest.raises(BusError):
        bus.send(sender_role="leader", recipient_role="cartographer", method=METHOD_TASK_ASSIGN, payload={})
