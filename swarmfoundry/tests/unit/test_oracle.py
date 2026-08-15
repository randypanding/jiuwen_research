import json
from pathlib import Path

import pytest

from swarmfoundry.oracle.runner import check_manifest, load_suite, run_suite
from swarmfoundry.oracle.golden import GoldenError, compare_golden, update_golden
from swarmfoundry.selftest import _write_instance, _write_suite


def test_suite_fails_closed_without_env_manifest(tmp_path):
    suite_dir = tmp_path / "suite"
    _write_suite(suite_dir)
    manifest = json.loads((suite_dir / "suite.json").read_text())
    manifest["env_manifest"] = {"TZ": "UTC"}
    (suite_dir / "suite.json").write_text(json.dumps(manifest))
    inst = tmp_path / "inst"
    _write_instance(inst, round_expr="round(a / b, 6)")
    suite = load_suite(suite_dir)
    assert check_manifest(suite) == ["PYTHONHASHSEED", "SEED"]
    results = run_suite(suite, inst, suite_dir)
    assert results and all(not r.passed for r in results)
    assert "manifest" in results[0].detail


def test_suite_all_kinds_pass(tmp_path):
    suite_dir = tmp_path / "suite"
    _write_suite(suite_dir)
    inst = tmp_path / "inst"
    _write_instance(inst, round_expr="round(a / b, 6)")
    suite = load_suite(suite_dir)
    results = run_suite(suite, inst, suite_dir)
    assert all(r.passed for r in results), [r.detail for r in results]


def test_suite_detects_wrong_behavior(tmp_path):
    suite_dir = tmp_path / "suite"
    _write_suite(suite_dir)
    inst = tmp_path / "inst"
    _write_instance(inst, round_expr="a * b")
    suite = load_suite(suite_dir)
    results = {r.scenario_id: r for r in run_suite(suite, inst, suite_dir)}
    assert results["ho-add-basic"].passed
    assert not results["ho-div-exact"].passed


def test_golden_compare_and_redaction(tmp_path):
    golden = tmp_path / "out.golden"
    golden.write_text("value: <redacted>\n")
    info = tmp_path / "out.r3info"
    info.write_text(json.dumps({"clause_ids": ["X-Y-001"], "redactions": [r"ts=\d+"], "approval_history": []}))
    ok, detail = compare_golden("value: ts=12345\n", golden)
    assert ok, detail
    ok2, _ = compare_golden("value: different\n", golden)
    assert not ok2


def test_golden_without_manifest_rejected(tmp_path):
    golden = tmp_path / "lonely.golden"
    golden.write_text("x")
    with pytest.raises(GoldenError):
        compare_golden("x", golden)


def test_golden_update_requires_human_approval(tmp_path):
    golden = tmp_path / "abi.golden"
    with pytest.raises(GoldenError):
        update_golden(golden, "new", ["X-Y-001"], human_approval="", approver="")
    update_golden(golden, "new\n", ["X-Y-001"], human_approval="token-set", approver="human-1")
    assert golden.read_text() == "new\n"
    info = json.loads((tmp_path / "abi.r3info").read_text())
    assert info["approval_history"][0]["approver"] == "human-1"
