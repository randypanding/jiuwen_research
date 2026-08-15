import pytest

from swarmfoundry.schema import SCHEMA_VERSION
from swarmfoundry.schema.base import SchemaError
from swarmfoundry.schema.spec import (
    Clause,
    DontCareEntry,
    RRegistry,
    SpecDomain,
    WitnessBinding,
)
from swarmfoundry.schema.gates import AdmissionDecision, GateResult, admit
from swarmfoundry.schema.receipt import CostRecord, EvidenceReceipt
from swarmfoundry.schema.surface import ContractSurface, SurfaceDiff, SymbolSurface
from swarmfoundry.schema.oracle import ScenarioSuite
from swarmfoundry.schema.diff import DiffReport
from swarmfoundry.schema.judge import JudgeVerdict
from swarmfoundry.schema.wave import WavePlan, WaveTask
from swarmfoundry.schema.envelope import SwarmEnvelope, METHOD_TASK_ASSIGN
from swarmfoundry.schema.events import MeasurementEvent
from swarmfoundry.schema.metrics import HealthMetrics
from swarmfoundry.schema.proposal import RuleProposal


def test_c01_spec_roundtrip():
    clause = Clause(
        id="AUTH-SESSION-001",
        level="L2",
        statement="Session tokens expire after 24h.",
        r_level="R2",
        witnesses=(WitnessBinding("hard_gate", "H2"), WitnessBinding("holdout_scenario", "ho-expiry")),
    )
    spec = SpecDomain(
        domain="auth",
        version=3,
        intent="Auth domain intent.",
        clauses=(clause,),
        dontcares=(DontCareEntry("dc-1", "AUTH-SESSION-001", "output_freedom", "token string format"),),
    )
    reparsed = SpecDomain.from_dict(spec.to_dict())
    assert reparsed == spec
    assert clause.has_mechanical_witness()


def test_c01_clause_id_format_enforced():
    with pytest.raises(SchemaError):
        Clause.from_dict({"id": "bad id", "level": "L2", "statement": "x"}, "t")


def test_c01_unverifiable_clause_detection():
    clause = Clause(
        id="AUTH-X-001",
        level="L2",
        statement="should be fast",
        witnesses=(WitnessBinding("judge_rubric", "rubric-1"),),
    )
    assert not clause.has_mechanical_witness()
    assert clause.effective_status() == "unverifiable"


def test_c02_registry_r3_requires_golden():
    with pytest.raises(SchemaError):
        RRegistry.from_dict(
            {
                "schema_version": SCHEMA_VERSION,
                "artifacts": [{"path": "crypto/", "r_level": "R3", "clauses": ["AUTH-X-001"]}],
            }
        )
    reg = RRegistry.from_dict(
        {
            "schema_version": SCHEMA_VERSION,
            "artifacts": [
                {"path": "crypto/", "r_level": "R3", "clauses": ["AUTH-X-001"], "golden_ref": "g/golden"},
                {"path": "crypto/aes/", "r_level": "R2", "clauses": []},
            ],
        }
    )
    assert reg.r_level_of("crypto/aes/x.py") == "R2"
    assert reg.r_level_of("crypto/other.py") == "R3"
    assert reg.r_level_of("unrelated.py") is None


def test_c03_gate_algebra_shapes():
    g = GateResult(gate_id="H1", status="pass", evidence=("a",))
    reparsed = GateResult.from_dict(g.to_dict())
    assert reparsed.gate_id == "H1"
    d = AdmissionDecision(
        admitted=True, hard_results=(g,), soft_results=(), rule="r", instance_id="inst-1"
    )
    assert AdmissionDecision.from_dict(d.to_dict()).admitted


def test_c04_receipt_roundtrip():
    g = GateResult(gate_id="H1", status="pass")
    d = admit([g] + [GateResult(gate_id=x, status="pass") for x in ("H2", "H3", "H4", "H5", "H6", "H7", "H8")], [GateResult(gate_id="S", status="pass")], "inst-1")
    r = EvidenceReceipt(
        receipt_id="rcpt-x",
        wave_id="wave-1",
        spec_delta_id="delta-1",
        instance_id="inst-1",
        r_level="R1",
        admission=d,
        diff_conclusion="equivalent",
        drift_clean=True,
        cost=CostRecord(10, 20, 0.5),
    )
    reparsed = EvidenceReceipt.from_dict(r.to_dict())
    assert reparsed.admission.admitted and reparsed.cost.spend_units == 0.5


def test_c05_surface_roundtrip():
    s = ContractSurface(module="m", symbols=(SymbolSurface("m.f", "function", "(a)"),))
    assert ContractSurface.from_dict(s.to_dict()) == s
    d = SurfaceDiff(module="m", changes=())
    assert SurfaceDiff.from_dict(d.to_dict()) == d


def test_c06_suite_roundtrip():
    suite = ScenarioSuite(
        suite_id="s1",
        entrypoint="python3 {instance}/main.py",
        scenarios=(),
        holdout=True,
        env_manifest={"PYTHONHASHSEED": "0", "TZ": "UTC", "SEED": "1"},
    )
    assert ScenarioSuite.from_dict(suite.to_dict()).holdout


def test_c07_diff_roundtrip():
    r = DiffReport(instance_a="a", instance_b="b", inputs_run=3, equivalence="equivalent")
    assert DiffReport.from_dict(r.to_dict()).equivalence == "equivalent"


def test_c08_judge_roundtrip():
    v = JudgeVerdict(judge_id="j1", model_family="fam", verdict="abstain", reasons="unsure")
    assert JudgeVerdict.from_dict(v.to_dict()).verdict == "abstain"
    with pytest.raises(SchemaError):
        JudgeVerdict.from_dict(
            {"schema_version": SCHEMA_VERSION, "judge_id": "j", "model_family": "f", "verdict": "approve", "reasons": ""}
        )


def test_c09_wave_validation():
    plan = WavePlan.from_dict(
        {
            "schema_version": SCHEMA_VERSION,
            "wave_id": "wave-1",
            "interface_freeze": ["calc"],
            "budget_units": 100.0,
            "tasks": [
                {"task_id": "t1", "spec_delta_id": "d1", "r_level": "R0", "n_fanout": 3},
                {"task_id": "t2", "spec_delta_id": "d2", "r_level": "R1", "n_fanout": 1, "depends_on": ["t1"]},
            ],
        }
    )
    assert [t.task_id for t in plan.ready_tasks()] == ["t1"]
    with pytest.raises(SchemaError):
        WavePlan.from_dict(
            {
                "schema_version": SCHEMA_VERSION,
                "wave_id": "wave-2",
                "interface_freeze": [],
                "budget_units": 1.0,
                "tasks": [
                    {"task_id": "a", "spec_delta_id": "d", "r_level": "R0", "n_fanout": 1, "depends_on": ["b"]},
                    {"task_id": "b", "spec_delta_id": "d", "r_level": "R0", "n_fanout": 1, "depends_on": ["a"]},
                ],
            }
        )
    with pytest.raises(SchemaError):
        WaveTask.from_dict({"task_id": "t", "spec_delta_id": "d", "r_level": "R0", "n_fanout": 99}, "t")


def test_c10_envelope_roundtrip_and_unknown_method():
    env = SwarmEnvelope(
        envelope_id="e1",
        sender_role="leader",
        recipient_role="builder",
        method=METHOD_TASK_ASSIGN,
        payload={"task_id": "t1"},
    )
    assert SwarmEnvelope.from_dict(env.to_dict()).payload["task_id"] == "t1"
    with pytest.raises(SchemaError):
        SwarmEnvelope.from_dict(env.to_dict() | {"method": "chat.send"})
    with pytest.raises(SchemaError):
        SwarmEnvelope.from_dict(env.to_dict() | {"sender_role": "manager"})


def test_c11_measurement_roundtrip():
    e = MeasurementEvent(
        event_id="m1", spec_delta_id="d1", observation="silence", n_instances=3, n_passed=3, diff_empty=False
    )
    assert MeasurementEvent.from_dict(e.to_dict()).observation == "silence"


def test_c12_metrics_roundtrip():
    m = HealthMetrics(
        window="2026-W33",
        closure_rate=0.7,
        spec_entropy=0.2,
        witness_coverage=0.9,
        unverifiable_clauses=1,
        escape_defect_rate=0.0,
        drift_alerts=0,
        drift_fix_latency_h=0.0,
        judge_kappa=0.8,
        judge_abstain_rate=0.1,
        rework_rate=0.15,
        unit_admission_cost=12.5,
    )
    assert HealthMetrics.from_dict(m.to_dict()).judge_kappa == 0.8


def test_c13_proposal_roundtrip():
    p = RuleProposal(
        proposal_id="rp-1",
        kind="rule_change",
        content="raise N for crypto domain",
        rationale="escape defects",
        status="human_approved",
        effective_session="session-2",
    )
    assert RuleProposal.from_dict(p.to_dict()).may_apply("session-2")
    assert not p.may_apply("session-1")


def test_schema_version_mismatch_rejected():
    env = SwarmEnvelope(
        envelope_id="e1", sender_role="leader", recipient_role="builder", method=METHOD_TASK_ASSIGN, payload={}
    )
    with pytest.raises(SchemaError):
        SwarmEnvelope.from_dict(env.to_dict() | {"schema_version": "0.0.1"})
