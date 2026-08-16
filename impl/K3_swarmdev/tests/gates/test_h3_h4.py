import json
import sys

import pytest

from swarmdev.contracts import CapabilityError, HoldoutScenario, OracleBundle, Role, make_token
from swarmdev.contracts.oracle import Expectation
from swarmdev.contracts.receipt import GateStatus
from swarmdev.gates import ContractGate, HoldoutGate, extract_surface
from swarmdev.oracle import HoldoutStore

IMPL = "def compute(x):\n    return x * 2\n"
RUN_SCRIPT = "from impl import compute\nprint(compute(3))\n"
SURFACE_SRC = "def compute(x):\n    return x * 2\n\n\nclass Helper:\n    pass\n"


def _bundle(exit_code=0, stdout_regex=r"^6$") -> OracleBundle:
    scenario = HoldoutScenario(
        scenario_id="SCN-1",
        spec_clause_ids=["CL-A1"],
        title="compute doubled",
        run_command=f"{sys.executable} run_holdout.py",
        expectation=Expectation(exit_code=exit_code, stdout_regex=stdout_regex),
    )
    return OracleBundle(
        bundle_id="BND-1", spec_id="SPEC-demo-0001", spec_version="1.0.0", scenarios=[scenario]
    )


def _write_instance(ctx):
    (ctx.workspace / "impl.py").write_text(IMPL)
    (ctx.workspace / "run_holdout.py").write_text(RUN_SCRIPT)


def test_holdout_gate_pass(make_ctx):
    ctx = make_ctx()
    _write_instance(ctx)
    outcome = HoldoutGate(_bundle()).run(ctx)
    assert outcome.status == GateStatus.PASS
    assert outcome.gate_id == "H3"


def test_holdout_gate_fail_lists_scenario(make_ctx):
    ctx = make_ctx()
    _write_instance(ctx)
    outcome = HoldoutGate(_bundle(exit_code=1)).run(ctx)
    assert outcome.status == GateStatus.FAIL
    assert "SCN-1" in outcome.details


def test_holdout_gate_with_store_and_verifier_token(make_ctx):
    ctx = make_ctx()
    _write_instance(ctx)
    ctx.extra["token"] = make_token(Role.VERIFIER, "v-1", "s1")
    outcome = HoldoutGate(HoldoutStore(_bundle())).run(ctx)
    assert outcome.status == GateStatus.PASS


def test_holdout_gate_builder_token_rejected(make_ctx):
    ctx = make_ctx()
    _write_instance(ctx)
    ctx.extra["token"] = make_token(Role.BUILDER, "b-1", "s1")
    with pytest.raises(CapabilityError):
        HoldoutGate(HoldoutStore(_bundle())).run(ctx)


def test_holdout_gate_store_without_token_blocked(make_ctx):
    ctx = make_ctx()
    _write_instance(ctx)
    outcome = HoldoutGate(HoldoutStore(_bundle())).run(ctx)
    assert outcome.status == GateStatus.BLOCKED


def test_holdout_gate_falls_back_to_ctx_bundle(make_ctx):
    ctx = make_ctx(bundle=_bundle())
    _write_instance(ctx)
    outcome = HoldoutGate().run(ctx)
    assert outcome.status == GateStatus.PASS


def test_holdout_gate_blocked_without_source(make_ctx):
    outcome = HoldoutGate().run(make_ctx())
    assert outcome.status == GateStatus.BLOCKED


def test_extract_surface_lists_public_names(make_ctx):
    ctx = make_ctx()
    (ctx.instance_dir / "impl.py").write_text(SURFACE_SRC)
    assert extract_surface(ctx.instance_dir) == {"impl.py": ["compute", "x", "Helper"]}


def test_extract_surface_skips_private_names(make_ctx):
    ctx = make_ctx()
    (ctx.instance_dir / "impl.py").write_text(
        "def _hidden():\n    pass\n\n\ndef visible(a, _b):\n    return a\n\n\nclass _Private:\n    pass\n"
    )
    assert extract_surface(ctx.instance_dir) == {"impl.py": ["visible", "a"]}


def test_contract_gate_baseline_records_surface(make_ctx):
    ctx = make_ctx()
    (ctx.instance_dir / "impl.py").write_text(SURFACE_SRC)
    outcome = ContractGate().run(ctx)
    assert outcome.status == GateStatus.PASS
    assert outcome.evidence_refs == ["surface:baseline-recorded"]
    assert json.loads(outcome.details)["impl.py"] == ["compute", "x", "Helper"]


def test_contract_gate_removed_function_fails(make_ctx):
    ctx = make_ctx(surface_snapshot={"impl.py": ["compute", "x", "Helper"]})
    (ctx.instance_dir / "impl.py").write_text("class Helper:\n    pass\n")
    outcome = ContractGate().run(ctx)
    assert outcome.status == GateStatus.FAIL
    assert outcome.gate_id == "H4"
    assert "impl.py:compute" in outcome.details


def test_contract_gate_added_function_passes(make_ctx):
    ctx = make_ctx(surface_snapshot={"impl.py": ["compute"]})
    (ctx.instance_dir / "impl.py").write_text(SURFACE_SRC)
    outcome = ContractGate().run(ctx)
    assert outcome.status == GateStatus.PASS
