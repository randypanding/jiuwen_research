import subprocess
import sys
from pathlib import Path

from swarmdev.contracts import RLevel
from swarmdev.contracts.receipt import GateStatus
from swarmdev.gates import BudgetGate, DifferentialGate, DriftGate, InvariantGate
from swarmdev.oracle import DifferentialEngine, GoldenManifest, GoldenStore, RunOutput

IMPL_DOUBLE = "def compute(x):\n    return x * 2\n"
IMPL_DEVIANT = "def compute(x):\n    if x == 2:\n        return 99\n    return x * 2\n"

_RUNNER_CODE = (
    "import sys\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "from impl import compute\n"
    "print(compute(int(sys.argv[2])))\n"
)


def _runner(instance_dir: Path, inp: str) -> RunOutput:
    proc = subprocess.run(
        [sys.executable, "-c", _RUNNER_CODE, str(instance_dir), inp],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return RunOutput(exit_code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


def _factory(values):
    it = iter(values)
    return lambda: next(it)


def _manifest(approved_by="human:alice") -> GoldenManifest:
    return GoldenManifest(spec_hash="h1", seed="seed-1", lock_hash="lock-1", approved_by=approved_by)


def test_diff_gate_identical_instances_pass(make_ctx, tmp_path):
    a = tmp_path / "inst_a"
    b = tmp_path / "inst_b"
    a.mkdir()
    b.mkdir()
    (a / "impl.py").write_text(IMPL_DOUBLE)
    (b / "impl.py").write_text(IMPL_DOUBLE)
    dirs = {"a": a, "b": b}
    ctx = make_ctx(instance_dir=a, extra={"instance_dirs": dirs})
    gate = DifferentialGate(DifferentialEngine(_runner), _factory(["1", "2"]), 2)
    outcome = gate.run(ctx)
    assert outcome.status == GateStatus.PASS
    assert outcome.gate_id == "H5"
    assert "no divergence" in outcome.details


def test_diff_gate_divergence_pinpoints_input(make_ctx, tmp_path):
    a = tmp_path / "inst_a"
    b = tmp_path / "inst_b"
    a.mkdir()
    b.mkdir()
    (a / "impl.py").write_text(IMPL_DOUBLE)
    (b / "impl.py").write_text(IMPL_DEVIANT)
    dirs = {"a": a, "b": b}
    ctx = make_ctx(instance_dir=a, extra={"instance_dirs": dirs})
    gate = DifferentialGate(DifferentialEngine(_runner), _factory(["1", "2"]), 2)
    outcome = gate.run(ctx)
    assert outcome.status == GateStatus.FAIL
    assert "input 2" in outcome.details
    assert "input 1" not in outcome.details


def test_diff_gate_r3_golden_flow(make_ctx, tmp_path):
    a = tmp_path / "inst_a"
    b = tmp_path / "inst_b"
    a.mkdir()
    b.mkdir()
    (a / "impl.py").write_text(IMPL_DOUBLE)
    (b / "impl.py").write_text(IMPL_DOUBLE)
    dirs = {"a": a, "b": b}
    ctx = make_ctx(instance_dir=a, r_level=RLevel.R3, extra={"instance_dirs": dirs})
    store = GoldenStore(tmp_path / "golden")
    engine = DifferentialEngine(_runner)

    missing = DifferentialGate(
        engine, _factory(["1", "2"]), 2, golden_store=store, golden_artifact_id="ART-out"
    ).run(ctx)
    assert missing.status == GateStatus.FAIL
    assert "missing_snapshot" in missing.details

    template = DifferentialGate(engine, _factory(["1", "2"]), 2)
    content = template.golden_content(dirs, ["1", "2"])
    store.save("ART-out", content, _manifest())

    locked = DifferentialGate(
        engine, _factory(["1", "2"]), 2, golden_store=store, golden_artifact_id="ART-out"
    ).run(ctx)
    assert locked.status == GateStatus.PASS
    assert "golden:ART-out" in locked.evidence_refs


def test_diff_gate_r3_requires_golden_store(make_ctx, tmp_path):
    ctx = make_ctx(instance_dir=tmp_path, r_level=RLevel.R3)
    gate = DifferentialGate(DifferentialEngine(_runner), _factory(["1"]), 1)
    outcome = gate.run(ctx)
    assert outcome.status == GateStatus.FAIL
    assert "golden" in outcome.details.lower()


def test_invariant_gate_clean_pass(make_ctx):
    ctx = make_ctx()
    (ctx.instance_dir / "impl.py").write_text(
        "import os\n\n\ndef compute(x):\n    return x * 2\n"
    )
    gate = InvariantGate(dangerous_patterns=[r"eval\s*\(", r"os\.system"], import_allowlist=["os"])
    outcome = gate.run(ctx)
    assert outcome.status == GateStatus.PASS
    assert outcome.gate_id == "H6"


def test_invariant_gate_os_system_fail(make_ctx):
    ctx = make_ctx()
    (ctx.instance_dir / "impl.py").write_text("import os\n\nos.system('ls')\n")
    gate = InvariantGate(dangerous_patterns=[r"os\.system"], import_allowlist=["os"])
    outcome = gate.run(ctx)
    assert outcome.status == GateStatus.FAIL
    assert "impl.py" in outcome.details
    assert r"os\.system" in outcome.details


def test_invariant_gate_eval_fail(make_ctx):
    ctx = make_ctx()
    (ctx.instance_dir / "impl.py").write_text("def f(s):\n    return eval(s)\n")
    gate = InvariantGate(dangerous_patterns=[r"eval\s*\("])
    outcome = gate.run(ctx)
    assert outcome.status == GateStatus.FAIL
    assert "eval" in outcome.details


def test_invariant_gate_import_outside_allowlist_fail(make_ctx):
    ctx = make_ctx()
    (ctx.instance_dir / "impl.py").write_text("import socket\nimport os\n\nfrom json import dumps\n")
    gate = InvariantGate(dangerous_patterns=[], import_allowlist=["os", "json"])
    outcome = gate.run(ctx)
    assert outcome.status == GateStatus.FAIL
    assert "import socket" in outcome.details


def test_invariant_gate_no_allowlist_skips_import_check(make_ctx):
    ctx = make_ctx()
    (ctx.instance_dir / "impl.py").write_text("import socket\n")
    gate = InvariantGate(dangerous_patterns=[r"os\.system"], import_allowlist=None)
    assert gate.run(ctx).status == GateStatus.PASS


def test_drift_gate_pass_and_fail(make_ctx):
    ctx = make_ctx()
    assert DriftGate(lambda c: (True, "clean")).run(ctx).status == GateStatus.PASS
    outcome = DriftGate(lambda c: (False, "terminology drift in CL-A1")).run(ctx)
    assert outcome.status == GateStatus.FAIL
    assert outcome.gate_id == "H7"
    assert "terminology drift" in outcome.details


def test_budget_gate_pass(make_ctx):
    ctx = make_ctx(cost_record={"tokens": 500, "duration_s": 10.0})
    outcome = BudgetGate(max_tokens=1000, max_duration_s=60.0).run(ctx)
    assert outcome.status == GateStatus.PASS
    assert outcome.gate_id == "H8"


def test_budget_gate_tokens_over_fail(make_ctx):
    ctx = make_ctx(cost_record={"tokens": 2000, "duration_s": 10.0})
    outcome = BudgetGate(max_tokens=1000).run(ctx)
    assert outcome.status == GateStatus.FAIL
    assert "tokens" in outcome.details


def test_budget_gate_duration_over_fail(make_ctx):
    ctx = make_ctx(cost_record={"tokens": 10, "duration_s": 120.0})
    outcome = BudgetGate(max_duration_s=60.0).run(ctx)
    assert outcome.status == GateStatus.FAIL
    assert "duration" in outcome.details


def test_budget_gate_missing_record_inconclusive(make_ctx):
    outcome = BudgetGate(max_tokens=1).run(make_ctx())
    assert outcome.status == GateStatus.INCONCLUSIVE
    assert "cost record missing" in outcome.details
