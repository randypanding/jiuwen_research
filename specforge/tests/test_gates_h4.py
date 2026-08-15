"""WP3 cross-component test: H4 contract gate <-> WP1 semver + WP2 diff."""
import pathlib

from specforge.contracts import extract_module
from specforge.gates import GateContext, H4ContractGate
from specforge.gates.base import GateVerdict
from specforge.spec import SpecDelta, parse_spec

SPEC = pathlib.Path(__file__).parents[1] / "examples" / "demo_adder" / "spec.md"


def _ctx(tmp_path, new_src, old_src=None, old_ver="1.0.0", new_ver="1.1.0", r="R0"):
    unit = parse_spec(path=str(SPEC))
    unit.version = new_ver          # instance carries the NEW spec version
    unit.artifacts = ["pkg/mod.py"]
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "mod.py").write_text(new_src, encoding="utf-8")
    unit.r_level = r
    delta = SpecDelta(spec_id=unit.spec_id, old_version=old_ver, new_version=new_ver,
                      r_level=r, artifacts=unit.artifacts)
    old_snap = extract_module(old_src, "mod") if old_src else None
    new_snap = extract_module(new_src, "mod")
    return GateContext(instance_path=str(tmp_path), world_path=".", spec_unit=unit,
                       spec_delta=delta, surface_old=old_snap, surface_new=new_snap)


V1 = "def add(a: int, b: int) -> int:\n    return a + b\n"


def test_h4_pass_on_additive_with_minor_bump(tmp_path):
    v2 = V1 + "\ndef extra(q=0):\n    return q\n"
    ctx = _ctx(tmp_path, v2, V1, new_ver="1.1.0")
    res = H4ContractGate().run(ctx)
    assert res.verdict == GateVerdict.PASS


def test_h4_fail_breaking_without_major_bump(tmp_path):
    v2 = V1.replace("def add(a: int, b: int) -> int:", "def add(a: int) -> int:")
    ctx = _ctx(tmp_path, v2, V1, new_ver="1.1.0")  # breaking but minor bump!
    res = H4ContractGate().run(ctx)
    assert res.verdict == GateVerdict.FAIL
    assert "major" in res.reason


def test_h4_pass_breaking_with_major_bump(tmp_path):
    v2 = V1.replace("def add(a: int, b: int) -> int:", "def add(a: int) -> int:")
    ctx = _ctx(tmp_path, v2, V1, old_ver="1.0.0", new_ver="2.0.0")
    res = H4ContractGate().run(ctx)
    assert res.verdict == GateVerdict.PASS


def test_h4_r2_change_escalates_to_human(tmp_path):
    v2 = V1.replace("LIMIT_N = 1", "LIMIT_N = 1") + "\nX = 1\n"
    ctx = _ctx(tmp_path, v2, V1, new_ver="1.1.0", r="R2")
    res = H4ContractGate().run(ctx)
    assert res.verdict == GateVerdict.INCONCLUSIVE
    assert "human" in res.reason


def test_h4_new_unit_no_old_surface(tmp_path):
    ctx = _ctx(tmp_path, V1, old_src=None, old_ver="0.0.0", new_ver="1.0.0")
    res = H4ContractGate().run(ctx)
    assert res.verdict == GateVerdict.PASS
