"""WP4 cross-component test: measurement table -> H5 verdict bridging + corpus."""
from specforge.difftest import ExecRecord, InstanceRecords, run_measurement, verdict_from_records
from specforge.gates import GateContext, H5DifftestGate
from specforge.gates.base import GateVerdict


def _inst(iid, sums, oracle=True):
    recs = [ExecRecord(input={"a": k, "b": 1}, output={"sum": s}) for k, s in sums]
    return InstanceRecords(instance_id=iid, records=recs, oracle_passed=oracle)


def test_verdict_from_records_matches_engine():
    insts = [
        _inst("a", [(1, 2), (2, 3)]),
        _inst("b", [(1, 2), (2, 3)]),
    ]
    m1 = run_measurement(insts)
    m2 = verdict_from_records(insts)
    assert m1.verdict == m2.verdict == "CLOSED"


def test_h5_pass_on_closed(tmp_path):
    insts = [
        _inst("a", [(1, 2), (2, 3)]),
        _inst("b", [(1, 2), (2, 3)]),
    ]
    ctx = GateContext(instance_path=".", world_path=".", difftest_records=insts)
    res = H5DifftestGate().run(ctx)
    assert res.verdict == GateVerdict.PASS


def test_h5_inconclusive_on_silence(tmp_path):
    insts = [
        _inst("a", [(1, 2), (2, 3)]),
        _inst("b", [(1, 2), (2, 4)]),
    ]
    ctx = GateContext(instance_path=".", world_path=".", difftest_records=insts)
    res = H5DifftestGate().run(ctx)
    assert res.verdict == GateVerdict.INCONCLUSIVE
    assert "moderator" in res.reason


def test_h5_silence_outside_dc_region(tmp_path):
    insts = [
        _inst("a", [(1, 2)]),
        _inst("b", [(1, 5)]),
    ]
    import pathlib

    from specforge.spec import parse_spec
    unit = parse_spec(path=str(pathlib.Path(__file__).parents[1] / "examples" /
                               "demo_adder" / "spec.md"))
    ctx = GateContext(instance_path=".", world_path=".", difftest_records=insts,
                      spec_unit=unit)
    # demo spec's only dc region is debug_log; sum divergence is outside -> SILENCE
    res = H5DifftestGate().run(ctx)
    assert res.verdict == GateVerdict.INCONCLUSIVE


def test_h5_inconclusive_when_nothing_available():
    ctx = GateContext(instance_path=".", world_path=".")
    res = H5DifftestGate().run(ctx)
    assert res.verdict == GateVerdict.INCONCLUSIVE
