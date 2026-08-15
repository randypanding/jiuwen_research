"""WP1 tests: linter (witness binding, unverifiable, uniqueness, R levels)."""
from specforge.spec import SpecUnit, lint_spec, machine_clause_coverage, parse_spec
from specforge.spec.rlevels import RRegistry
from tests.conftest import GATE_IDS, HOLDOUT_IDS


def _unit(clauses):
    u = SpecUnit(spec_id="u.x", version="1.0.0", r_level="R0", clauses=clauses)
    return u


def test_unbound_witness_marks_advisory():
    from specforge.spec.schema import Clause
    u = _unit([Clause(clause_id="C1", level="L2", text="must be fast")])
    rep = lint_spec(u, gate_ids=GATE_IDS, holdout_ids=HOLDOUT_IDS)
    assert not rep.ok
    assert any(e.code == "SPEC002" for e in rep.errors)
    assert u.clauses[0].advisory_only is True


def test_unknown_witness_reference():
    from specforge.spec.schema import Clause, Witness
    u = _unit([Clause(clause_id="C1", level="L1", text="t", witness=Witness("gate", "h9"))])
    rep = lint_spec(u, gate_ids=GATE_IDS, holdout_ids=HOLDOUT_IDS)
    assert any(e.code == "SPEC003" for e in rep.errors)


def test_valid_witness_passes():
    from specforge.spec.schema import Clause, Witness
    u = _unit([Clause(clause_id="C1", level="L2", text="t", witness=Witness("gate", "h2"))])
    u.artifacts = ["a.py"]
    rep = lint_spec(u, gate_ids=GATE_IDS, holdout_ids=HOLDOUT_IDS)
    assert rep.ok
    assert u.clauses[0].advisory_only is False


def test_duplicate_clause_ids():
    from specforge.spec.schema import Clause, Witness
    c = Clause(clause_id="C1", level="L1", text="t", witness=Witness("holdout", "adder-basic"))
    u = _unit([c, Clause(clause_id="C1", level="L1", text="t2",
                         witness=Witness("holdout", "adder-basic"))])
    rep = lint_spec(u, gate_ids=GATE_IDS, holdout_ids=HOLDOUT_IDS)
    assert any(e.code == "SPEC001" for e in rep.errors)


def test_l2_requires_artifacts():
    from specforge.spec.schema import Clause, Witness
    u = _unit([Clause(clause_id="C1", level="L2", text="t", witness=Witness("gate", "h4"))])
    u.artifacts = []
    rep = lint_spec(u)
    assert any(e.code == "SPEC004" for e in rep.errors)


def test_coverage_metric(demo_spec_path):
    unit = parse_spec(path=demo_spec_path)
    # all machine clauses bound in the demo spec
    cov = machine_clause_coverage(unit)
    assert cov == 1.0


def test_registry_classify():
    reg = RRegistry(rules={"migrations/*": "R3", "api/**": "R2"}, default="R0")
    assert reg.classify("migrations/0001.sql") == "R3"
    assert reg.classify("api/v1/foo.py") == "R2"
    assert reg.classify("src/util.py") == "R0"
    assert reg.classify("src/util.py", unit_default="R1") == "R1"
    assert not reg.fanout_allowed("R3")
    assert reg.requires_human("R2")
