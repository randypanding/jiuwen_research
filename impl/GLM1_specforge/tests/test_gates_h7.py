"""WP3 tests: H7 drift gate (anchors, coverage, contract hash)."""
import pathlib

from specforge.contracts import extract_module
from specforge.gates import GateContext, H7DriftGate
from specforge.gates.base import GateVerdict
from specforge.spec import parse_spec

SPEC = pathlib.Path(__file__).parents[1] / "examples" / "demo_adder" / "spec.md"


def _make_instance(tmp_path, anchors=True, missing_artifact=False):
    unit = parse_spec(path=str(SPEC))
    pkg = tmp_path / "demo_adder"
    pkg.mkdir()
    src = (pathlib.Path(__file__).parents[1] / "examples" / "demo_adder" / "good.py").read_text(
        encoding="utf-8")
    if not anchors:
        import re

        src = re.sub(r"\s*spec:REQ-[A-Z0-9-]+", "", src)  # strip anchors, keep code valid
    (pkg / "good.py").write_text(src, encoding="utf-8")
    (pkg / "broken.py").write_text(
        (pathlib.Path(__file__).parents[1] / "examples" / "demo_adder" / "broken.py").read_text(
            encoding="utf-8"), encoding="utf-8")
    unit.artifacts = ["demo_adder/good.py"] if not missing_artifact else ["demo_adder/gone.py"]
    snap = extract_module(src, "good")
    return GateContext(instance_path=str(tmp_path), world_path=".", spec_unit=unit,
                       surface_new=snap)


def test_h7_pass_with_full_anchor_coverage(tmp_path):
    ctx = _make_instance(tmp_path)
    res = H7DriftGate(min_coverage=0.99).run(ctx)
    assert res.verdict == GateVerdict.PASS, res.reason


def test_h7_missing_artifact_fails(tmp_path):
    ctx = _make_instance(tmp_path, missing_artifact=True)
    res = H7DriftGate().run(ctx)
    assert res.verdict == GateVerdict.FAIL
    assert "missing" in res.reason.lower()


def test_h7_low_coverage_inconclusive(tmp_path):
    ctx = _make_instance(tmp_path, anchors=False)
    # no anchors -> coverage 0, no orphans
    res = H7DriftGate(min_coverage=0.5).run(ctx)
    assert res.verdict == GateVerdict.INCONCLUSIVE


def test_h7_orphan_anchor_fails(tmp_path):
    ctx = _make_instance(tmp_path)
    pkg = tmp_path / "demo_adder"
    (pkg / "good.py").write_text(
        (pkg / "good.py").read_text(encoding="utf-8") + "\n# spec:REQ-GHOST-9\n", encoding="utf-8")
    res = H7DriftGate().run(ctx)
    assert res.verdict == GateVerdict.FAIL
    assert "REQ-GHOST-9" in res.reason


def test_h7_contract_hash_drift(tmp_path):
    ctx = _make_instance(tmp_path)
    ctx.spec_unit.contract["surface_hash"] = "deadbeef" * 8
    res = H7DriftGate().run(ctx)
    assert res.verdict == GateVerdict.FAIL
    assert "drift" in res.reason.lower()
