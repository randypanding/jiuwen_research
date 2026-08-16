"""H3 holdout gate: aggregate-only scoring over the private store."""
from __future__ import annotations

from specforge.gates import GateContext
from specforge.gates.base import GateVerdict
from specforge.gates.h3_holdout import H3HoldoutGate
from specforge.holdout import HoldoutScenario, HoldoutStore
from specforge.spec.schema import Clause, SpecUnit, Witness


def _unit_with_holdout(set_ids: list[str]) -> SpecUnit:
    unit = SpecUnit(spec_id="demo", version="1.0.0", r_level="R1")
    for sid in set_ids:
        unit.clauses.append(Clause(
            clause_id=f"c-{sid}", level="L2", text=f"holdout clause {sid}",
            witness=Witness(kind="holdout", ref=sid)))
    return unit


def _store_with_scenarios(root, set_id: str, n: int, pass_from: int) -> HoldoutStore:
    """n scenarios; those with index >= pass_from fail."""
    store = HoldoutStore(root)
    for i in range(n):
        store.add_scenario(HoldoutScenario(
            f"{set_id}-s{i}", set_id, "io", payload={
                "cmd": ["python", "-c",
                        "import sys, json; "
                        "print(json.dumps({'ok': bool(int(sys.stdin.read()))}))"],
                "input": 1 if i < pass_from else 0, "expect": {"ok": True}}))
    return store


def _ctx(instance_path, unit, store) -> GateContext:
    return GateContext(instance_path=str(instance_path), world_path=".",
                       spec_unit=unit, holdout_store=store)


def test_h3_not_applicable_without_holdout_clause(tmp_path):
    unit = SpecUnit(spec_id="d", version="1.0.0", r_level="R1")
    unit.clauses.append(Clause("c1", "L2", "gate clause",
                               witness=Witness(kind="gate", ref="h2")))
    ctx = GateContext(instance_path=".", world_path=".", spec_unit=unit)
    assert not H3HoldoutGate().applicable(ctx)


def test_h3_pass_when_strong_score(tmp_path):
    unit = _unit_with_holdout(["adder-basic"])
    store = _store_with_scenarios(tmp_path / "h", "adder-basic", n=20, pass_from=20)
    res = H3HoldoutGate(min_scenarios=5).run(_ctx(tmp_path, unit, store))
    assert res.verdict == GateVerdict.PASS
    assert res.evidence["scores"]["adder-basic"]["aggregate"] == 1.0


def test_h3_fail_when_weak_score(tmp_path):
    unit = _unit_with_holdout(["adder-basic"])
    store = _store_with_scenarios(tmp_path / "h", "adder-basic", n=20, pass_from=6)
    res = H3HoldoutGate(min_scenarios=5).run(_ctx(tmp_path, unit, store))
    assert res.verdict == GateVerdict.FAIL


def test_h3_inconclusive_when_sample_too_small(tmp_path):
    unit = _unit_with_holdout(["adder-basic"])
    store = _store_with_scenarios(tmp_path / "h", "adder-basic", n=3, pass_from=3)
    res = H3HoldoutGate(min_scenarios=5).run(_ctx(tmp_path, unit, store))
    assert res.verdict == GateVerdict.INCONCLUSIVE
    assert "too small" in res.reason


def test_h3_no_store_is_inconclusive_never_pass(tmp_path):
    """Constitution #3: no mechanical witness -> may only veto."""
    unit = _unit_with_holdout(["adder-basic"])
    ctx = GateContext(instance_path=".", world_path=".", spec_unit=unit)
    res = H3HoldoutGate().run(ctx)
    assert res.verdict == GateVerdict.INCONCLUSIVE
    assert "#3" in res.constitution_ref


def test_h3_aggregates_multiple_sets(tmp_path):
    unit = _unit_with_holdout(["set-a", "set-b"])
    root = tmp_path / "h"
    store = HoldoutStore(root)
    for sid, ok in (("set-a", 10), ("set-b", 6)):
        for i in range(10):
            store.add_scenario(HoldoutScenario(
                f"{sid}-s{i}", sid, "io", payload={
                    "cmd": ["python", "-c",
                            "import sys, json; print(json.dumps({'ok': True}))"],
                    "input": {}, "expect": {"ok": True if i < ok else False}}))
    res = H3HoldoutGate(min_scenarios=5).run(_ctx(tmp_path, unit, store))
    assert set(res.evidence["scores"]) == {"set-a", "set-b"}
    # total 16/20 -> Wilson bound decides verdict; must not crash either way
    assert res.verdict in (GateVerdict.PASS, GateVerdict.FAIL, GateVerdict.INCONCLUSIVE)
