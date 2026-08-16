from swarmdev.contracts import L2Clause, SpecDoc, WitnessRef
from swarmdev.contracts.spec_doc import WitnessKind
from swarmdev.drift import ContractHashStore, DriftDetector


def _spec(clauses):
    return SpecDoc(spec_id="SPEC-d-0001", domain="demo", version="1.0.0",
                   l1_intent="demo", l2_clauses=clauses)


def _witnessed(clause_id="CL-A1"):
    return L2Clause(clause_id=clause_id, title="t", guarantees=["g"],
                    witnesses=[WitnessRef(kind=WitnessKind.HARD_GATE,
                                          ref_id="G1", gate_id="H2")])


def test_unknown_tag_is_hard(tmp_path):
    (tmp_path / "a.py").write_text("# @REQ-CL-GHOST@ @REQ-CL-A1@", encoding="utf-8")
    report = DriftDetector(None).detect(_spec([_witnessed()]), tmp_path)
    assert report.clean is False
    kinds = [(e.kind, e.severity) for e in report.events]
    assert ("unknown_tag_reference", "hard") in kinds
    ghost = next(e for e in report.events if e.kind == "unknown_tag_reference")
    assert "CL-GHOST" in ghost.detail


def test_hash_change_is_hard(tmp_path):
    code = tmp_path / "code"
    code.mkdir()
    (code / "a.py").write_text("# @REQ-CL-A1@", encoding="utf-8")
    store = ContractHashStore(tmp_path / "hashes.json")
    store.record(_spec([_witnessed()]))
    mutated = _spec([L2Clause(clause_id="CL-A1", title="t", guarantees=["g changed"],
                              witnesses=[WitnessRef(kind=WitnessKind.HARD_GATE,
                                                    ref_id="G1", gate_id="H2")])])
    report = DriftDetector(store).detect(mutated, code)
    assert report.clean is False
    assert any(e.kind == "clause_hash_changed" and e.severity == "hard"
               and "CL-A1" in e.detail for e in report.events)


def test_missing_implementation_tag_is_advisory(tmp_path):
    report = DriftDetector(None).detect(_spec([_witnessed()]), tmp_path)
    assert report.clean is True
    assert len(report.events) == 1
    event = report.events[0]
    assert event.kind == "missing_implementation_tag"
    assert event.severity == "advisory"


def test_unwitnessed_clause_without_tag_is_fine(tmp_path):
    spec = _spec([L2Clause(clause_id="CL-B1", title="no witness")])
    report = DriftDetector(None).detect(spec, tmp_path)
    assert report.clean is True
    assert report.events == []


def test_clean_scenario(tmp_path):
    code = tmp_path / "code"
    code.mkdir()
    (code / "a.py").write_text("# @REQ-CL-A1@\n", encoding="utf-8")
    store = ContractHashStore(tmp_path / "hashes.json")
    spec = _spec([_witnessed()])
    store.record(spec)
    report = DriftDetector(store).detect(spec, code)
    assert report.clean is True
    assert report.events == []
