import sys

from swarmdev.contracts.receipt import GateStatus
from swarmdev.gates import BuildGate, OwnershipGuard, UnitGate

IMPL = "def compute(x):\n    return x * 2\n"


def test_build_gate_pass(make_ctx):
    ctx = make_ctx()
    (ctx.workspace / "impl.py").write_text(IMPL)
    gate = BuildGate([[sys.executable, "-m", "py_compile", "impl.py"]])
    outcome = gate.run(ctx)
    assert outcome.status == GateStatus.PASS
    assert outcome.gate_id == "H1"
    assert outcome.duration_s >= 0


def test_build_gate_fail_reports_command_and_stderr_tail(make_ctx):
    ctx = make_ctx()
    gate = BuildGate(
        [[sys.executable, "-c", "import sys; sys.stderr.write('boom-build-error'); sys.exit(3)"]]
    )
    outcome = gate.run(ctx)
    assert outcome.status == GateStatus.FAIL
    assert "boom-build-error" in outcome.details
    assert "py" in outcome.details


def test_build_gate_second_command_fails(make_ctx):
    ctx = make_ctx()
    (ctx.workspace / "impl.py").write_text(IMPL)
    gate = BuildGate(
        [
            [sys.executable, "-m", "py_compile", "impl.py"],
            [sys.executable, "-c", "import sys; sys.exit(1)"],
        ]
    )
    outcome = gate.run(ctx)
    assert outcome.status == GateStatus.FAIL


def test_unit_gate_pass(make_ctx):
    ctx = make_ctx()
    (ctx.workspace / "impl.py").write_text(IMPL)
    (ctx.workspace / "test_impl.py").write_text(
        "from impl import compute\nassert compute(21) == 42\n"
    )
    gate = UnitGate(test_command=[sys.executable, "test_impl.py"])
    outcome = gate.run(ctx)
    assert outcome.status == GateStatus.PASS
    assert outcome.gate_id == "H2"


def test_unit_gate_fail_on_test_failure(make_ctx):
    ctx = make_ctx()
    (ctx.workspace / "impl.py").write_text(IMPL)
    (ctx.workspace / "test_bad.py").write_text(
        "import sys\nfrom impl import compute\nassert compute(2) == 5\nsys.exit(0)\n"
    )
    gate = UnitGate(test_command=[sys.executable, "test_bad.py"])
    outcome = gate.run(ctx)
    assert outcome.status == GateStatus.FAIL
    assert "test command failed" in outcome.details


def test_unit_gate_fail_when_oracle_file_tampered(make_ctx):
    ctx = make_ctx()
    (ctx.workspace / "impl.py").write_text(IMPL)
    oracle = ctx.workspace / "oracle.txt"
    oracle.write_text("gold")
    (ctx.workspace / "bad_test.py").write_text(
        "from pathlib import Path\nPath('oracle.txt').write_text('hacked')\n"
    )
    gate = UnitGate(test_command=[sys.executable, "bad_test.py"], oracle_files=[oracle])
    outcome = gate.run(ctx)
    assert outcome.status == GateStatus.FAIL
    assert "oracle.txt" in outcome.details


def test_unit_gate_pass_with_oracle_intact(make_ctx):
    ctx = make_ctx()
    (ctx.workspace / "impl.py").write_text(IMPL)
    oracle = ctx.workspace / "oracle.txt"
    oracle.write_text("gold")
    (ctx.workspace / "read_oracle.py").write_text(
        "from pathlib import Path\nassert Path('oracle.txt').read_text() == 'gold'\n"
    )
    gate = UnitGate(test_command=[sys.executable, "read_oracle.py"], oracle_files=[oracle])
    outcome = gate.run(ctx)
    assert outcome.status == GateStatus.PASS


def test_ownership_guard_detects_change_and_deletion(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("alpha")
    b.write_text("beta")
    guard = OwnershipGuard()
    snap = guard.snapshot([a, b])
    assert set(snap) == {str(a), str(b)}
    assert snap[str(a)] != snap[str(b)]
    assert guard.verify([a, b]) == []
    a.write_text("tampered")
    assert guard.verify([a, b]) == [a]
    b.unlink()
    changed = guard.verify([a, b])
    assert a in changed and b in changed
