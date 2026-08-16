"""WP5 tests: golden store (manifest gate, approval flow, CI write ban)."""
import pytest

from specforge.golden import GoldenManifest, GoldenStore, compute_deps_hash


def _records(sums):
    return [{"input": {"a": i}, "output": {"sum": s}} for i, s in sums]


def test_missing_golden(tmp_path):
    store = GoldenStore(tmp_path)
    r = store.compare("u.x", _records([(1, 2)]))
    assert r.verdict == "MISSING"


def test_manifest_gate_blocks_on_mismatch(tmp_path):
    store = GoldenStore(tmp_path)
    man = GoldenManifest(code_version="abc", seed=1)
    man.approved_by, man.approval_reason, man.update_label = "alice", "initial", "intent-change"
    # NOTE: write directly for test setup via approve_update (not CI mode)
    import os

    os.environ.pop("CI", None)
    store.approve_update("u.x", _records([(1, 2)]), man,
                         approver="alice", reason="initial baseline",
                         update_label="intent-change", allow_ci=True)
    # same-content manifest -> MATCH
    r = store.compare("u.x", _records([(1, 2)]), expected_manifest=man)
    assert r.verdict == "MATCH"
    # different seed -> comparability premise broken
    drifted = GoldenManifest(code_version="abc", seed=2)
    r2 = store.compare("u.x", _records([(1, 2)]), expected_manifest=drifted)
    assert r2.verdict == "INCONCLUSIVE"
    assert "manifest" in r2.detail


def test_mismatch_on_value_change(tmp_path):
    store = GoldenStore(tmp_path)
    man = GoldenManifest(code_version="v1", seed=1)
    import os

    os.environ.pop("CI", None)
    store.approve_update("u.x", _records([(1, 2), (2, 4)]), man, approver="a", reason="r",
                         update_label="intent-change", allow_ci=True)
    r = store.compare("u.x", _records([(1, 2), (2, 5)]))
    assert r.verdict == "MISMATCH"
    assert r.diff_paths


def test_ci_never_writes_golden(tmp_path, monkeypatch):
    store = GoldenStore(tmp_path)
    monkeypatch.setenv("CI", "true")
    with pytest.raises(PermissionError):
        store.approve_update("u.x", _records([(1, 2)]), GoldenManifest(),
                             approver="ci-bot", reason="auto", update_label="bugfix")


def test_update_requires_approver_and_label(tmp_path):
    store = GoldenStore(tmp_path)
    with pytest.raises(ValueError):
        store.approve_update("u.x", _records([(1, 2)]), GoldenManifest(),
                             approver="", reason="x", update_label="bugfix")
    with pytest.raises(ValueError):
        store.approve_update("u.x", _records([(1, 2)]), GoldenManifest(),
                             approver="a", reason="x", update_label="weird-label")


def test_update_archives_previous(tmp_path):
    import json

    store = GoldenStore(tmp_path / "g")
    man = GoldenManifest(code_version="v1")
    store.approve_update("u.x", _records([(1, 2)]), man, approver="a", reason="r",
                         update_label="intent-change", allow_ci=True)
    store.approve_update("u.x", _records([(1, 3)]), man, approver="a", reason="fix",
                         update_label="bugfix", allow_ci=True)
    d = tmp_path / "g" / "u.x".replace("/", "__")
    archived = [p for p in d.iterdir() if p.name.startswith("golden.") and p.suffix == ".jsonl"]
    assert archived, "previous golden must be archived"
    current = [json.loads(x) for x in (d / "golden.jsonl").read_text().splitlines()]
    assert current[0]["output"]["sum"] == 3
    assert json.loads((d / "manifest.json").read_text())["update_label"] == "bugfix"


def test_deps_hash():
    assert compute_deps_hash("pyyaml") == compute_deps_hash("pyyaml")
    assert compute_deps_hash("pyyaml") != compute_deps_hash("pyyaml2")
