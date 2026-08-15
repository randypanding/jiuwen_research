"""H1 build gate: allowlisted build/type/static floor."""
from __future__ import annotations

from specforge.gates import GateContext
from specforge.gates.base import GateVerdict
from specforge.gates.h1_build import H1BuildGate
from specforge.gates.shell import run_command


def _ctx(path) -> GateContext:
    return GateContext(instance_path=str(path), world_path=".")


def test_h1_pass_on_clean_tree(tmp_project):
    res = H1BuildGate().run(_ctx(tmp_project))
    assert res.verdict == GateVerdict.PASS
    # evidence contains the executed command and its exit code
    key = "python -m compileall -q ."
    assert key in res.evidence
    assert res.evidence[key]["returncode"] == 0


def test_h1_fail_on_syntax_error(tmp_path):
    bad = tmp_path / "pkg"
    bad.mkdir()
    (bad / "broken.py").write_text("def f(:\n  pass\n", encoding="utf-8")
    res = H1BuildGate().run(_ctx(tmp_path))
    assert res.verdict == GateVerdict.FAIL
    assert "exited" in res.reason


def test_h1_disallowed_command_is_inconclusive(tmp_path):
    """Commands outside the allowlist must be refused, never run (fail-closed)."""

    gate = H1BuildGate(commands=[["curl", "http://evil.example"]])
    res = gate.run(_ctx(tmp_path))
    assert res.verdict == GateVerdict.INCONCLUSIVE
    assert "not allowed" in res.reason


def test_h1_timeout_fails(tmp_path):
    gate = H1BuildGate(
        commands=[["python", "-c", "import time; time.sleep(5)"]], timeout=0.5)
    res = gate.run(_ctx(tmp_path))
    assert res.verdict == GateVerdict.FAIL
    assert "timed out" in res.reason


def test_h1_first_failure_short_circuits(tmp_path):
    (tmp_path / "a.py").write_text("def f(:\n", encoding="utf-8")
    ran = {"second": False}
    gate = H1BuildGate(commands=[
        ["python", "-c", "raise SystemExit(3)"],
        ["python", "-c", "ran['second']=True; raise SystemExit(0)"],
    ])
    res = gate.run(_ctx(tmp_path))
    assert res.verdict == GateVerdict.FAIL
    assert len(res.evidence) == 1  # second command never recorded
    assert not ran["second"]


def test_shell_runner_reports_timeout_and_streams(tmp_path):
    res = run_command(["python", "-c", "import sys; print('out'); print('err', file=sys.stderr); sys.exit(2)"],
                      cwd=str(tmp_path))
    assert res.returncode == 2
    assert "out" in res.stdout
    assert "err" in res.stderr
    assert not res.timed_out
