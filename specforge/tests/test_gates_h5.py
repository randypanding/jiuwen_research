"""H5 differential / golden gate: measurement-table verdict -> admission verdict."""
from __future__ import annotations

from specforge.difftest.engine import InstanceRecords
from specforge.difftest.runner import ExecRecord
from specforge.gates import GateContext
from specforge.gates.base import GateVerdict
from specforge.gates.h5_difftest import H5DifftestGate
from specforge.golden.store import GoldenManifest, GoldenStore
from specforge.spec.schema import DontCare, SpecUnit


def _rec(inp: dict, out: dict) -> ExecRecord:
    r = ExecRecord(input=inp)
    r.output = out
    r.exit_code = 0
    return r


def _unit(dc: dict[str, str] | None = None) -> SpecUnit:
    unit = SpecUnit(spec_id="demo", version="1.0.0", r_level="R1")
    for region, kind in (dc or {}).items():
        unit.dont_cares.append(DontCare(dc_id=f"dc-{region}", kind=kind, region=region))
    return unit


def _ctx(records=None, unit=None, golden=None, extra=None) -> GateContext:
    return GateContext(instance_path=".", world_path=".", spec_unit=unit,
                       golden_store=golden, difftest_records=records,
                       extra=extra or {})


def test_h5_closed_admits(tmp_path):
    recs = [InstanceRecords(f"i{i}", [_rec({"a": 1}, {"sum": 2})]) for i in range(3)]
    res = H5DifftestGate().run(_ctx(records=recs, unit=_unit()))
    assert res.verdict == GateVerdict.PASS


def test_h5_silence_dc_admits(tmp_path):
    dc = {"debug_log.*": "unspecified"}
    mk = lambda v: InstanceRecords(v, [_rec({"a": 1}, {"sum": 2, "debug_log": v})])  # noqa: E731
    res = H5DifftestGate().run(_ctx(records=[mk("A"), mk("B"), mk("C")], unit=_unit(dc)))
    assert res.verdict == GateVerdict.PASS


def test_h5_undefined_divergence_rejects(tmp_path):
    dc = {"sum.*": "undefined"}
    mk = lambda v: InstanceRecords(v, [_rec({"a": 1}, {"sum": v})])  # noqa: E731
    res = H5DifftestGate().run(_ctx(records=[mk(2), mk(3), mk(2)], unit=_unit(dc)))
    assert res.verdict == GateVerdict.FAIL
    assert "#10" in res.constitution_ref


def test_h5_silence_blocks_not_rejects(tmp_path):
    """Unregistered divergence -> INCONCLUSIVE (route to moderator), never silent pass."""
    mk = lambda v: InstanceRecords(v, [_rec({"a": 1}, {"sum": v})])  # noqa: E731
    res = H5DifftestGate().run(_ctx(records=[mk(2), mk(3), mk(2)], unit=_unit()))
    assert res.verdict == GateVerdict.INCONCLUSIVE
    assert "#9" in res.constitution_ref


def test_h5_ambiguous_blocks(tmp_path):
    ok = InstanceRecords("ok", [_rec({"a": 1}, {"sum": 2})], oracle_passed=True)
    bad = InstanceRecords("bad", [_rec({"a": 1}, {"sum": 2})], oracle_passed=False)
    res = H5DifftestGate().run(_ctx(records=[ok, bad, ok], unit=_unit()))
    assert res.verdict == GateVerdict.INCONCLUSIVE


def _seed_golden(store: GoldenStore, unit_id: str, output: dict) -> None:
    store.approve_update(
        unit_id, [{"input": {"a": 1}, "output": output}], GoldenManifest(code_version="v1"),
        approver="steward", reason="seed", update_label="intent-change", allow_ci=True)


def test_h5_golden_match_passes(tmp_path):
    store = GoldenStore(tmp_path / "golden")
    unit = _unit()
    _seed_golden(store, unit.spec_id, {"sum": 2})
    res = H5DifftestGate().run(_ctx(
        unit=unit, golden=store,
        extra={"golden_records": [{"input": {"a": 1}, "output": {"sum": 2}}]}))
    assert res.verdict == GateVerdict.PASS


def test_h5_golden_mismatch_fails(tmp_path):
    store = GoldenStore(tmp_path / "golden")
    unit = _unit()
    _seed_golden(store, unit.spec_id, {"sum": 2})
    res = H5DifftestGate().run(_ctx(
        unit=unit, golden=store,
        extra={"golden_records": [{"input": {"a": 1}, "output": {"sum": 99}}]}))
    assert res.verdict == GateVerdict.FAIL


def test_h5_golden_missing_records_inconclusive(tmp_path):
    store = GoldenStore(tmp_path / "golden")
    unit = _unit()
    _seed_golden(store, unit.spec_id, {"sum": 2})
    res = H5DifftestGate().run(_ctx(unit=unit, golden=store, extra={}))
    assert res.verdict == GateVerdict.INCONCLUSIVE


def test_h5_no_witness_inconclusive():
    """Neither records nor golden store -> constitution #3: veto only."""
    res = H5DifftestGate().run(_ctx())
    assert res.verdict == GateVerdict.INCONCLUSIVE
    assert "#3" in res.constitution_ref


def test_h5_applicability():
    assert not H5DifftestGate().applicable(_ctx())
    assert H5DifftestGate().applicable(_ctx(records=[InstanceRecords("x", [])]))
    assert H5DifftestGate().applicable(_ctx(golden=object()))
