"""WP6 tests: holdout isolation (information asymmetry, canaries, aggregation)."""
import json
import os
import stat

import pytest

from specforge.holdout import (
    BuilderView,
    HoldoutAccessError,
    HoldoutScenario,
    HoldoutStore,
    audit_builder_view,
    new_canary,
    scan_canaries,
)


@pytest.fixture
def store(tmp_path):
    s = HoldoutStore(tmp_path / "holdout")
    s.add_scenario(HoldoutScenario("s1", "adder-basic", "io", payload={
        "cmd": ["python", "-c", "import sys,json; print(json.dumps({'sum': 2}))"],
        "input": {"a": 1, "b": 1}, "expect": {"sum": 2}}))
    s.add_scenario(HoldoutScenario("s2", "adder-basic", "io", payload={
        "cmd": ["python", "-c", "import sys,json; print(json.dumps({'sum': -1}))"],
        "input": {"a": -2, "b": 1}, "expect": {"sum": -1}}))
    return s


def test_scenarios_stored_privately(store, tmp_path):
    p = tmp_path / "holdout" / "adder-basic" / "scenarios.jsonl"
    assert p.exists()
    mode = stat.S_IMODE(os.stat(p).st_mode)
    assert mode & 0o077 == 0, "scenario file must not be group/world readable"


def test_builder_view_has_no_read_api(store):
    view = BuilderView(store)
    exposed = audit_builder_view(view)
    assert exposed == [], f"BuilderView must not expose: {exposed}"
    assert not hasattr(view, "scenarios")
    assert not hasattr(view, "evaluate")


def test_builder_view_describe_is_metadata_only(store):
    view = BuilderView(store)
    d = view.describe()
    assert d["sets"]["adder-basic"]["count"] == 2
    assert "kinds" in d["sets"]["adder-basic"]
    # no scenario payload content anywhere
    assert "expect" not in json.dumps(d)


def test_canary_leak_detection(store):
    canaries = store.canaries("adder-basic")
    assert len(canaries) == 2
    view = BuilderView(store)
    leaked = " ".join(canaries)
    with pytest.raises(HoldoutAccessError):
        view.publish_notice(f"leaking {leaked}")
    # clean text passes
    assert view.publish_notice("clean summary") == "clean summary"


def test_scan_canaries_direct():
    c = new_canary()
    assert c.startswith("JWHD-")
    assert scan_canaries(f"text {c} more", {c, "JWHD-OTHER"}) == [c]


def test_evaluate_returns_aggregates_only(store, tmp_path):
    inst = tmp_path / "instance"
    inst.mkdir()
    score = store.evaluate(str(inst), "adder-basic")
    assert 0.0 <= score.aggregate <= 1.0
    assert score.total == 2
    d = score.to_dict()
    assert set(d) == {"set_id", "aggregate", "passed", "total", "dimensions"}


def test_rotation_log(store):
    store.retire_scenario("adder-basic", "s1")
    events = [e["event"] for e in store.rotation_log]
    assert "add" in events and "retire" in events
    assert len(store.scenarios("adder-basic")) == 1
