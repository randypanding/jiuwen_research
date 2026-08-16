from __future__ import annotations

import json

import pytest

from swarm_kernel.contracts import (
    CONTRACT_REGISTRY,
    BCClass,
    ChangeOp,
    ClauseChange,
    ContractEnvelope,
    Confidentiality,
    EvidenceReceipt,
    FanoutRequest,
    GateId,
    GateResult,
    GateSuiteResult,
    JudgeVerdict,
    JudgeVerdictKind,
    RLevel,
    Role,
    RuleProposal,
    ProposalStatus,
    SpecDelta,
    SpecDoc,
    Verdict,
)
from swarm_kernel.spec_repo.versioning import classify_change, next_version, validate_version_policy


def test_contract_registry_roundtrip() -> None:
    for name, cls in CONTRACT_REGISTRY.items():
        schema = cls.model_json_schema()
        assert schema.get("type") == "object" or "$defs" in schema or "properties" in schema, name


def test_envelope_seal_and_verify() -> None:
    env = ContractEnvelope(schema_name="SpecDelta", producer_role=Role.ARCHITECT, payload={"delta_id": "sd-1"})
    env.seal()
    assert env.verify_seal()
    env.payload["delta_id"] = "sd-tampered"
    assert not env.verify_seal()


def test_r3_fanout_forbidden() -> None:
    with pytest.raises(ValueError):
        FanoutRequest(wave_id="wave-1", delta_id="sd-1", r_level=RLevel.R3, n_instances=3)
    ok = FanoutRequest(wave_id="wave-1", delta_id="sd-1", r_level=RLevel.R3, n_instances=1)
    assert ok.n_instances == 1


def test_fanout_bound() -> None:
    with pytest.raises(ValueError):
        FanoutRequest(wave_id="wave-1", delta_id="sd-1", n_instances=9)


def test_gate_suite_hard_pass_requires_all_gates() -> None:
    suite = GateSuiteResult(instance_id="x")
    for g in list(GateId)[:-1]:
        suite.results.append(GateResult(gate_id=g, verdict=Verdict.PASS))
    assert not suite.hard_pass
    assert GateId.H8_BUDGET in suite.blocking_gates()
    suite.results.append(GateResult(gate_id=GateId.H8_BUDGET, verdict=Verdict.PASS))
    assert suite.hard_pass


def test_inconclusive_is_not_pass() -> None:
    suite = GateSuiteResult(instance_id="x")
    for g in GateId:
        suite.results.append(GateResult(gate_id=g, verdict=Verdict.PASS))
    suite.results[0] = GateResult(gate_id=GateId.H1_BUILD, verdict=Verdict.INCONCLUSIVE)
    assert not suite.hard_pass


def test_judge_verdict_has_no_exemption_channel() -> None:
    jv = JudgeVerdict(rubric_id="rub-1", instance_id="inst-1", kind=JudgeVerdictKind.NO_VETO)
    data = jv.model_dump(mode="json")
    assert "exempt_hard_gates" not in data
    assert "waiver" not in data


def test_rule_proposal_never_applies_current_session() -> None:
    rp = RuleProposal(rule_text="raise N to 5 for crypto modules")
    assert rp.may_apply_current_session is False
    with pytest.raises(ValueError):
        RuleProposal(rule_text="x", status=ProposalStatus.EFFECTIVE_NEXT_SESSION)


def test_spec_delta_human_approval_on_nbc() -> None:
    delta = SpecDelta(
        spec_id="toy-clamp",
        base_spec_version="1.0.0",
        new_spec_version="2.0.0",
        changes=[ClauseChange(clause_id="REQ-TOY-002", op=ChangeOp.MODIFY, bc_class=BCClass.NBC)],
    )
    assert delta.requires_human_approval


def test_semver_policy() -> None:
    delta_nbc = SpecDelta(
        spec_id="s",
        base_spec_version="1.2.3",
        new_spec_version="2.0.0",
        changes=[ClauseChange(clause_id="A", op=ChangeOp.MODIFY, bc_class=BCClass.NBC)],
    )
    assert next_version("1.2.3", delta_nbc) == "2.0.0"
    ok, _ = validate_version_policy("1.2.3", "2.0.0", delta_nbc)
    assert ok
    bad, reason = validate_version_policy("1.2.3", "1.3.0", delta_nbc)
    assert not bad and "major" in reason
    delta_bc = SpecDelta(
        spec_id="s",
        base_spec_version="1.2.3",
        new_spec_version="1.3.0",
        changes=[ClauseChange(clause_id="B", op=ChangeOp.ADD, bc_class=BCClass.BC)],
    )
    assert next_version("1.2.3", delta_bc) == "1.3.0"


def test_classify_change_breaking_on_removal() -> None:
    assert classify_change({"clamp", "helper"}, {"clamp"}) == BCClass.NBC
    assert classify_change({"clamp"}, {"clamp", "helper"}) == BCClass.BC


def test_spec_doc_verifiability(spec_path) -> None:
    spec = SpecDoc.model_validate_json(spec_path.read_text(encoding="utf-8"))
    assert spec.unverifiable_clauses() == []
    clause = spec.clause_map()["REQ-TOY-002"]
    assert clause.anchor().startswith("@spec REQ-TOY-002 #")


def test_receipt_completeness_requires_hard_pass_and_clean_drift() -> None:
    suite = GateSuiteResult(instance_id="good")
    for g in GateId:
        suite.results.append(GateResult(gate_id=g, verdict=Verdict.PASS))
    receipt = EvidenceReceipt(wave_id="wave-1", delta_id="sd-1", r_level=RLevel.R1, chosen_instance_id="good", gate_suite=suite)
    assert receipt.complete
    suite.results[2] = GateResult(gate_id=GateId.H3_HOLDOUT, verdict=Verdict.FAIL)
    assert not receipt.complete
