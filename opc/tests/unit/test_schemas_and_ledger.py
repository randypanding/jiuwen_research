from __future__ import annotations

from datetime import datetime, timedelta, timezone

from hypothesis import given, settings
from hypothesis import strategies as st

from opc.schemas.common import Verdict, content_hash
from opc.schemas.evidence import EvidenceReceipt, LedgerEntry
from opc.schemas.gates import AdmissionVerdict, GateReport
from opc.schemas.oracle import JudgeSample, JudgeVerdict
from opc.schemas.spec import Clause, ContractSpec, WitnessBinding
from opc.gates.waivers import WaiverEntry, find_valid_waiver
from opc.world.ledger import AdmissionLedger


def _receipt(selected: str = "inst-a", admitted: bool = True) -> EvidenceReceipt:
    return EvidenceReceipt(
        receipt_id=f"RCPT-WAVE-1-{selected}",
        wave_id="WAVE-1",
        spec_delta_ref="deadbeef",
        r_level="R1",
        selected_instance=selected,
        admitted=admitted,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def test_verdict_algebra_hard_and_soft_required():
    passing = GateReport(gate="H1", verdict=Verdict.PASS)
    verdict = AdmissionVerdict.decide({f"H{i}": passing for i in range(1, 9)}, None)
    assert not verdict.admitted
    assert "S" in verdict.blocking_gates or verdict.soft_verdict is Verdict.INCONCLUSIVE


def test_verdict_algebra_missing_gate_blocks():
    passing = GateReport(gate="H1", verdict=Verdict.PASS)
    soft = GateReport(gate="S", verdict=Verdict.PASS)
    verdict = AdmissionVerdict.decide({"H1": passing}, soft, required_hard=("H1", "H2"))
    assert not verdict.admitted
    assert "H2" in verdict.blocking_gates


def test_verdict_algebra_soft_gate_is_monotone_veto():
    reports = {f"H{i}": GateReport(gate=f"H{i}", verdict=Verdict.PASS) for i in range(1, 9)}
    veto = GateReport(gate="S", verdict=Verdict.FAIL)
    verdict = AdmissionVerdict.decide(reports, veto)
    assert not verdict.admitted
    assert "S" in verdict.blocking_gates


def test_verdict_algebra_admit_when_all_pass():
    reports = {f"H{i}": GateReport(gate=f"H{i}", verdict=Verdict.PASS) for i in range(1, 9)}
    soft = GateReport(gate="S", verdict=Verdict.PASS)
    verdict = AdmissionVerdict.decide(reports, soft)
    assert verdict.admitted
    assert verdict.blocking_gates == []


def test_judge_majority_reject():
    samples = [
        JudgeSample(sample_index=0, verdict="reject", reasons=["rubric 2 violated"], evidence=["claim X"]),
        JudgeSample(sample_index=1, verdict="reject", reasons=["rubric 2 violated"], evidence=["claim X"]),
        JudgeSample(sample_index=2, verdict="no_reject", reasons=[], evidence=["claim Y"]),
    ]
    verdict = JudgeVerdict.from_samples(samples)
    assert verdict.verdict is Verdict.FAIL
    assert "rubric 2 violated" in verdict.reasons


def test_judge_split_panel_abstains():
    samples = [
        JudgeSample(sample_index=0, verdict="reject", reasons=["r"], evidence=["e"]),
        JudgeSample(sample_index=1, verdict="no_reject", reasons=[], evidence=["e"]),
    ]
    verdict = JudgeVerdict.from_samples(samples)
    assert verdict.verdict is Verdict.INCONCLUSIVE
    assert verdict.abstained


def test_judge_position_inconsistency_abstains():
    samples = [JudgeSample(sample_index=0, verdict="no_reject", reasons=[], evidence=["e"])]
    verdict = JudgeVerdict.from_samples(samples, position_swapped_consistent=False)
    assert verdict.verdict is Verdict.INCONCLUSIVE
    assert verdict.abstained


def test_clause_verifiability():
    clause = Clause(id="REQ-x-001", layer="L2", text="t", witnesses=[WitnessBinding(clause_id="REQ-x-001", gate="S", target="rubric")])
    assert not clause.is_verifiable
    clause.witnesses.append(WitnessBinding(clause_id="REQ-x-001", gate="H2", target="test_a"))
    assert clause.is_verifiable


def test_contract_content_hash_stable():
    data = {
        "contract_id": "CTR-x",
        "version": "1.0.0",
        "r_level": "R0",
        "domain": "d",
    }
    a = ContractSpec.model_validate(data)
    b = ContractSpec.model_validate(dict(reversed(list(data.items()))))
    assert content_hash(a) == content_hash(b)


def test_waiver_expiry_and_scope():
    future = datetime.now(timezone.utc) + timedelta(days=1)
    past = datetime.now(timezone.utc) - timedelta(days=1)
    active = WaiverEntry(waiver_id="WVR-1", gate="H5", scope="*", reason="r", approver="human", expires_at=future)
    expired = WaiverEntry(waiver_id="WVR-2", gate="H5", scope="*", reason="r", approver="human", expires_at=past)
    scoped = WaiverEntry(waiver_id="WVR-3", gate="H5", scope="CTR-other", reason="r", approver="human", expires_at=future)
    assert find_valid_waiver([active], "H5", "CTR-x", "R0") is active
    assert find_valid_waiver([expired], "H5", "CTR-x", "R0") is None
    assert find_valid_waiver([scoped], "H5", "CTR-x", "R0") is None
    assert find_valid_waiver([scoped], "H5", "CTR-other", "R0") is scoped


@given(selected=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("L", "N"))))
@settings(max_examples=25)
def test_receipt_digest_deterministic(selected: str):
    receipt = _receipt(selected=f"inst-{selected}")
    assert receipt.digest() == _receipt(selected=f"inst-{selected}").digest()


def test_ledger_entry_genesis_shape():
    assert LedgerEntry.genesis() == "sha256:" + "0" * 64


def test_admission_ledger_roundtrip(tmp_path):
    ledger = AdmissionLedger(tmp_path / "ledger.jsonl")
    ledger.append(_receipt("inst-a"))
    ledger.append(_receipt("inst-b"))
    ok, problems = ledger.verify()
    assert ok, problems
    assert ledger.receipts_count() == 2


def test_admission_ledger_detects_tamper(tmp_path):
    ledger = AdmissionLedger(tmp_path / "ledger.jsonl")
    ledger.append(_receipt("inst-a"))
    ledger.append(_receipt("inst-b"))
    lines = (tmp_path / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
    first = LedgerEntry.model_validate_json(lines[0])
    first.receipt_digest = "sha256:" + "f" * 64
    lines[0] = first.model_dump_json()
    (tmp_path / "ledger.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    ok, problems = AdmissionLedger(tmp_path / "ledger.jsonl").verify()
    assert not ok
    assert any("tampered" in p or "broken link" in p for p in problems)
