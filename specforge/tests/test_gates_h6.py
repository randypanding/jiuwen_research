"""WP3 tests: H6 guardrail gate (dangerous patterns)."""
from specforge.gates import GateContext, H6GuardrailGate, scan_source
from specforge.gates.base import GateVerdict


def test_scan_dangerous_calls():
    findings = scan_source("x = eval(input())\n", "a.py")
    assert any(f["kind"] == "dangerous_call" and f["severity"] == "CRITICAL" for f in findings)


def test_scan_shell_true():
    src = "import subprocess\nsubprocess.run(['ls'], shell=True)\n"
    findings = scan_source(src, "b.py")
    assert any(f["kind"] == "shell_true" and f["severity"] == "CRITICAL" for f in findings)


def test_scan_shell_false_ok():
    src = "import subprocess\nsubprocess.run(['ls', '-l'], shell=False)\n"
    findings = scan_source(src, "c.py")
    assert not [f for f in findings if f["severity"] == "CRITICAL"]


def test_scan_hardcoded_secret():
    src = 'API_KEY = "sk-abcdef1234567890abcdef"\n'
    findings = scan_source(src, "d.py")
    assert any(f["kind"] == "hardcoded_secret" for f in findings)


def _ctx(tmp_path):
    return GateContext(instance_path=str(tmp_path), world_path=".")


def test_h6_clean_project(tmp_path):
    (tmp_path / "ok.py").write_text("def f(x):\n    return x + 1\n", encoding="utf-8")
    res = H6GuardrailGate().run(_ctx(tmp_path))
    assert res.verdict == GateVerdict.PASS


def test_h6_fails_on_eval(tmp_path):
    (tmp_path / "evil.py").write_text("y = exec('1+1')\n", encoding="utf-8")
    res = H6GuardrailGate().run(_ctx(tmp_path))
    assert res.verdict == GateVerdict.FAIL
    assert "dangerous" in res.reason.lower() or "guardrail" in res.reason.lower()


def test_h6_dependency_allowlist(tmp_path):
    (tmp_path / "requirements.txt").write_text("pyyaml\nrequests\n", encoding="utf-8")
    res = H6GuardrailGate(dependency_allowlist={"pyyaml"}).run(_ctx(tmp_path))
    assert res.verdict == GateVerdict.FAIL
    assert "requests" in res.reason
