import pytest

from swarmdev.contracts import (
    CAPABILITY_MATRIX, CapabilityError, CapabilityToken, ContractBus,
    DeltaEntry, DeltaOp, EnvelopeKind, EvidenceReceipt, GateOutcome,
    HoldoutScenario, JudgeVerdict, L2Clause, OracleBundle, RArtifact,
    RLevel, RRegistry, Role, SoftVerdict, SpecDelta, SpecDoc, TargetKind,
    VisibilityError, Wave, WaveState, WaveTask, WitnessRef, make_token,
)
from swarmdev.contracts.receipt import DiscardedInstance, GateStatus
from swarmdev.contracts.spec_delta import Compatibility
from swarmdev.contracts.spec_doc import DontCareEntry, WitnessKind


def _spec() -> SpecDoc:
    return SpecDoc(
        spec_id="SPEC-demo-0001", domain="demo", version="1.0.0",
        l1_intent="demo intent",
        l2_clauses=[
            L2Clause(clause_id="CL-A1", title="add", guarantees=["a+b==b+a"],
                     witnesses=[WitnessRef(kind=WitnessKind.HOLDOUT_SCENARIO, ref_id="SCN-1")]),
        ],
        dont_care=[DontCareEntry(entry_id="DC-1", clause_id="CL-A1", description="order free",
                                 precondition_domain="any", out_of_domain_behavior="blocking")],
    )


def test_spec_witness_coverage_and_unverifiable():
    s = _spec()
    assert s.witness_coverage() == 1.0
    s.l2_clauses.append(L2Clause(clause_id="CL-B1", title="no witness"))
    assert s.witness_coverage() == 0.5
    assert [c.clause_id for c in s.unverifiable_clauses()] == ["CL-B1"]


def test_spec_rejects_unknown_clause_in_dont_care():
    with pytest.raises(ValueError):
        SpecDoc(spec_id="SPEC-x", domain="d", version="1.0.0", l1_intent="i",
                dont_care=[DontCareEntry(entry_id="DC", clause_id="CL-ZZ",
                                         description="x", precondition_domain="p")])


def test_semver_enforced():
    with pytest.raises(ValueError):
        SpecDoc(spec_id="SPEC-x", domain="d", version="v1.0", l1_intent="i")


def test_r_registry_rules():
    reg = RRegistry()
    reg.register(RArtifact(artifact_id="ART-1", path_pattern="db/migrations/*",
                           level=RLevel.R3, declared_by_spec="SPEC-demo-0001"))
    assert reg.level_of("ART-1") == RLevel.R3
    assert reg.level_of("UNKNOWN") == RLevel.R0
    assert not RRegistry.fanout_allowed(RLevel.R3)
    assert not RRegistry.discard_allowed(RLevel.R2)
    assert RRegistry.requires_human_approval(RLevel.R2)


def test_r3_wave_task_forbids_fanout():
    with pytest.raises(ValueError):
        WaveTask(ru_id="RU-1", spec_delta_ref="DLT-1", r_level=RLevel.R3,
                 fanout={"n_target": 3})


def test_spec_delta_semver_policy():
    entry = DeltaEntry(entry_id="E1", op=DeltaOp.REMOVE, target_kind=TargetKind.GUARANTEE,
                       target_id="CL-A1.g1", compatibility=Compatibility.NBC,
                       requires_human_approval=True)
    d = SpecDelta(delta_id="DLT-1", spec_id="SPEC-demo-0001",
                  from_version="1.2.0", to_version="2.0.0", entries=[entry])
    assert d.is_breaking
    with pytest.raises(ValueError):
        SpecDelta(delta_id="DLT-2", spec_id="s", from_version="1.0.0",
                  to_version="1.1.0", entries=[entry])
    bc = DeltaEntry(entry_id="E2", op=DeltaOp.ADD, target_kind=TargetKind.CLAUSE,
                    target_id="CL-NEW", compatibility=Compatibility.BC)
    with pytest.raises(ValueError):
        SpecDelta(delta_id="DLT-3", spec_id="s", from_version="1.0.0",
                  to_version="2.0.0", entries=[bc])
    ok = SpecDelta(delta_id="DLT-4", spec_id="s", from_version="1.0.0",
                   to_version="1.1.0", entries=[bc])
    assert not ok.is_breaking


def test_judge_verdict_cannot_veto_without_reasons():
    with pytest.raises(ValueError):
        JudgeVerdict(verdict="veto")


def test_receipt_admission_algebra():
    outs = [GateOutcome(gate_id=f"H{i}", status=GateStatus.PASS) for i in range(1, 9)]
    r = EvidenceReceipt(receipt_id="RCPT-1", wave_id="WAVE-1", spec_id="SPEC-demo-0001",
                        spec_delta_ref="DLT-1", r_level=RLevel.R0,
                        chosen_instance_id="INST-1", hard_gate_outcomes=outs,
                        soft_verdicts=[SoftVerdict(rubric_id="RUB-1",
                                                   judge=JudgeVerdict(verdict="no_veto"))],
                        drift_check_passed=True, admitted=True, commit_ref="sha:abc")
    assert r.hard_pass and r.soft_pass
    outs2 = list(outs)
    outs2[2] = GateOutcome(gate_id="H3", status=GateStatus.FAIL)
    with pytest.raises(ValueError):
        EvidenceReceipt(receipt_id="RCPT-2", wave_id="W", spec_id="s",
                        spec_delta_ref="d", r_level=RLevel.R0,
                        chosen_instance_id="i", hard_gate_outcomes=outs2,
                        admitted=True)
    vetoed = EvidenceReceipt(receipt_id="RCPT-3", wave_id="W", spec_id="s",
                             spec_delta_ref="d", r_level=RLevel.R0,
                             chosen_instance_id="i", hard_gate_outcomes=outs,
                             soft_verdicts=[SoftVerdict(rubric_id="R",
                                                        judge=JudgeVerdict(verdict="veto",
                                                                           reasons=["bad"]))],
                             admitted=False)
    assert vetoed.hard_pass and not vetoed.soft_pass


def test_wave_state_machine():
    w = Wave(wave_id="WAVE-1", spec_delta_ids=["DLT-1"])
    w.transition(WaveState.COLLECTING)
    with pytest.raises(ValueError):
        w.transition(WaveState.COMMITTED)
    w.transition(WaveState.ADJUDICATING)
    w.transition(WaveState.ROLLED_BACK)
    assert w.state == WaveState.ROLLED_BACK


def test_capability_matrix_invariants():
    assert Role.BUILDER not in CAPABILITY_MATRIX["holdout.read"]
    assert Role.BUILDER not in CAPABILITY_MATRIX["judge.execute"]
    assert Role.BUILDER not in CAPABILITY_MATRIX["memory.write"]
    assert Role.JUDGE in CAPABILITY_MATRIX["judge.verdict.write"]
    assert CAPABILITY_MATRIX["rule.approve"] == frozenset({Role.HUMAN})


def test_bus_visibility_enforcement():
    bus = ContractBus()
    architect = make_token(Role.ARCHITECT, "arch-1", session_id="s1")
    builder = make_token(Role.BUILDER, "b-1", session_id="s1")
    verifier = make_token(Role.VERIFIER, "v-1", session_id="s1")
    bus.publish(architect, EnvelopeKind.WAVE_PLAN, {"wave": "W1"}, [Role.LEADER])
    with pytest.raises(VisibilityError):
        bus.publish(architect, EnvelopeKind.HOLDOUT_RESULTS, {"scn": "..."}, [Role.BUILDER])
    with pytest.raises(CapabilityError):
        bus.publish(builder, EnvelopeKind.GATE_RESULTS, {}, [Role.LEADER])
    bus.publish(verifier, EnvelopeKind.HOLDOUT_RESULTS, {"scn": "secret"},
                [Role.VERIFIER, Role.ARCHITECT])
    with pytest.raises(VisibilityError):
        bus.query(builder, EnvelopeKind.HOLDOUT_RESULTS)
    seen = bus.query(make_token(Role.ARCHITECT, "arch-1", "s1"), EnvelopeKind.HOLDOUT_RESULTS)
    assert len(seen) == 1
