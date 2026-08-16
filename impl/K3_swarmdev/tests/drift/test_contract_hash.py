from swarmdev.contracts import L2Clause, SpecDoc
from swarmdev.drift import ContractHashStore, hash_clause


def _clause(guarantees=("a+b==b+a",), clause_id="CL-X1", title="add"):
    return L2Clause(clause_id=clause_id, title=title, assumes=["ints"],
                    guarantees=list(guarantees), invariants=["total"])


def _spec(clauses):
    return SpecDoc(spec_id="SPEC-d-0001", domain="demo", version="1.0.0",
                   l1_intent="demo", l2_clauses=clauses)


def test_hash_stable_and_order_independent():
    c1 = _clause()
    c2 = L2Clause(clause_id="CL-X1", title="add", invariants=["total"],
                  assumes=["ints"], guarantees=["a+b==b+a"])
    assert hash_clause(c1) == hash_clause(c1)
    assert hash_clause(c1) == hash_clause(c2)
    assert len(hash_clause(c1)) == 64


def test_hash_changes_with_guarantee():
    assert hash_clause(_clause()) != hash_clause(_clause(("a+b==a+b",)))


def test_store_record_and_load(tmp_path):
    store = ContractHashStore(tmp_path / "hashes.json")
    assert store.load() == {}
    store.record(_spec([_clause(), L2Clause(clause_id="CL-X2", title="sub")]))
    loaded = store.load()
    assert loaded["SPEC-d-0001"]["CL-X1"] == hash_clause(_clause())
    assert "CL-X2" in loaded["SPEC-d-0001"]


def test_diff_changed(tmp_path):
    store = ContractHashStore(tmp_path / "hashes.json")
    store.record(_spec([_clause()]))
    mutated = _spec([_clause(guarantees=("a+b==a+b",))])
    assert store.diff(mutated) == [("CL-X1", "changed")]


def test_diff_added_removed(tmp_path):
    store = ContractHashStore(tmp_path / "hashes.json")
    store.record(_spec([_clause(), L2Clause(clause_id="CL-X2", title="sub")]))
    updated = _spec([_clause(), L2Clause(clause_id="CL-X3", title="mul")])
    assert store.diff(updated) == [("CL-X2", "removed"), ("CL-X3", "added")]


def test_diff_unknown_spec_is_empty(tmp_path):
    store = ContractHashStore(tmp_path / "hashes.json")
    store.record(_spec([_clause()]))
    other = SpecDoc(spec_id="SPEC-other", domain="d", version="1.0.0",
                    l1_intent="i", l2_clauses=[_clause()])
    assert store.diff(other) == []


def test_record_merges_specs(tmp_path):
    store = ContractHashStore(tmp_path / "hashes.json")
    store.record(_spec([_clause()]))
    other = SpecDoc(spec_id="SPEC-other", domain="d", version="1.0.0",
                    l1_intent="i", l2_clauses=[_clause(clause_id="CL-Y1")])
    store.record(other)
    loaded = store.load()
    assert set(loaded) == {"SPEC-d-0001", "SPEC-other"}
