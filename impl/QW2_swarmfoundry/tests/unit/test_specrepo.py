import json

import pytest

from swarmfoundry.specrepo.loader import SpecRepo, SpecRepoError
from swarmfoundry.specrepo.seal import reseal, seal_clause
from swarmfoundry.specrepo.coverage import witness_coverage
from swarmfoundry.selftest import _write_spec_repo


def _repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _write_spec_repo(root)
    return SpecRepo(root)


def test_repo_validates_and_lists_domains(tmp_path):
    repo = _repo(tmp_path)
    assert repo.list_domains() == ["calc"]
    assert repo.validate_all() == []


def test_missing_file_raises(tmp_path):
    repo = SpecRepo(tmp_path)
    with pytest.raises(SpecRepoError):
        repo.load_domain("nope")


def test_seal_stable_and_sensitive(tmp_path):
    repo = _repo(tmp_path)
    spec = repo.load_domain("calc")
    c = spec.clause("CALC-CORE-001")
    h1 = seal_clause(c)
    from swarmfoundry.schema.spec import Clause

    cosmetic = Clause(
        id=c.id, level=c.level, statement="compute(op,a,b)  returns   exact arithmetic results for add/sub.", r_level=c.r_level, witnesses=c.witnesses
    )
    assert seal_clause(cosmetic) == h1, "whitespace-only change must not re-seal"
    semantic = Clause(id=c.id, level=c.level, statement=c.statement + " Always.", r_level=c.r_level, witnesses=c.witnesses)
    assert seal_clause(semantic) != h1


def test_reseal_records_and_detects_tampering(tmp_path):
    repo = _repo(tmp_path)
    reseal(repo)
    spec_path = repo.root / "domains" / "calc" / "spec.json"
    data = json.loads(spec_path.read_text())
    data["clauses"][0]["statement"] += " (tampered)"
    spec_path.write_text(json.dumps(data))
    from swarmfoundry.gates.context import GateContext
    from swarmfoundry.gates.h7_drift import H7DriftGate
    from swarmfoundry.selftest import _write_instance

    inst = tmp_path / "inst"
    _write_instance(inst, round_expr="round(a / b, 6)")
    ctx = GateContext(instance_dir=inst, instance_id="i", spec_repo=repo)
    res = H7DriftGate().run(ctx)
    assert res.status == "fail"
    assert any("seal drift" in e for e in res.evidence)


def test_witness_coverage_report(tmp_path):
    repo = _repo(tmp_path)
    spec = repo.load_domain("calc")
    report = witness_coverage(spec)
    assert report.total_normative == 3
    assert report.covered == 3
    assert report.coverage == 1.0


def test_unverifiable_clause_lowers_coverage(tmp_path):
    repo = _repo(tmp_path)
    spec_path = repo.root / "domains" / "calc" / "spec.json"
    data = json.loads(spec_path.read_text())
    data["clauses"].append(
        {"id": "CALC-PERF-004", "level": "L1", "statement": "should feel fast", "witnesses": []}
    )
    spec_path.write_text(json.dumps(data))
    spec = repo.load_domain("calc")
    report = witness_coverage(spec)
    assert report.unverifiable == 1
    assert report.coverage == pytest.approx(3 / 4)
    assert "CALC-PERF-004" in report.unverifiable_ids


def test_registry_references_unknown_clause(tmp_path):
    repo = _repo(tmp_path)
    reg_path = repo.root / "registry" / "artifacts.json"
    data = json.loads(reg_path.read_text())
    data["artifacts"].append({"path": "x/", "r_level": "R0", "clauses": ["CALC-GHOST-999"]})
    reg_path.write_text(json.dumps(data))
    problems = repo.validate_all()
    assert any("unknown clause" in p for p in problems)
