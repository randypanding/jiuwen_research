"""WP3 tests: H2 mutation audit (oracle signal strength) + shell runner."""
import pytest

from specforge.difftest import run_instance
from specforge.gates import GateContext, H2TestsGate, generate_mutants, run_command
from specforge.gates.base import GateVerdict
from specforge.spec import parse_spec


def test_generate_mutants_deterministic_and_valid():
    src = "def f(a, b):\n    return a + b\n"
    m1 = generate_mutants(src, max_mutants=4, seed=7)
    m2 = generate_mutants(src, max_mutants=4, seed=7)
    assert m1 == m2
    assert len(m1) >= 1
    lineno, old, new, mutated = m1[0]
    assert old == "Add" and new == "Sub"
    assert "-" in mutated and "+" not in mutated.split("return")[1]


def test_generate_mutants_skips_strings():
    src = 'def f():\n    s = "a + b"\n    return 1\n'
    m = generate_mutants(src, max_mutants=4, seed=1)
    # the string line must not be mutated (comment/string stripping guard)
    for _, _, _, mutated in m:
        assert '"a + b"' in mutated
    # and a file whose only operators live in strings yields no mutants
    only_str = 'def f():\n    s = "a + b"\n'
    assert generate_mutants(only_str, max_mutants=4, seed=1) == []


def test_generate_mutants_only_anchored():
    src = (
        'def f(a, b):  # spec:REQ-X-1\n'
        '    unused = a - b\n'
        '    return a + b  # spec:REQ-X-2\n'
    )
    m = generate_mutants(src, max_mutants=8, seed=0, only_anchored=True)
    linenos = {ln for ln, _, _, _ in m}
    assert linenos == {3}, f"only anchored line mutated, got {linenos}"


@pytest.mark.contract
def test_h2_strong_tests_pass(tmp_project):
    unit = parse_spec(path=str(
        __import__("pathlib").Path(__file__).parents[1] / "examples" / "demo_adder" / "spec.md"))
    ctx = GateContext(instance_path=str(tmp_project), world_path=".",
                      spec_unit=unit, config={"artifacts": ["demo_adder/good.py"]})
    gate = H2TestsGate(mutation_score_threshold=0.6, max_mutants=3, mutation_seed=3)
    res = gate.run(ctx)
    assert res.verdict == GateVerdict.PASS, res.evidence.get("mutation")


@pytest.mark.contract
def test_h2_weak_tests_fail(tmp_project_weak_tests):
    unit = parse_spec(path=str(
        __import__("pathlib").Path(__file__).parents[1] / "examples" / "demo_adder" / "spec.md"))
    ctx = GateContext(instance_path=str(tmp_project_weak_tests), world_path=".",
                      spec_unit=unit, config={"artifacts": ["demo_adder/good.py"]})
    gate = H2TestsGate(mutation_score_threshold=0.7, max_mutants=3, mutation_seed=3)
    res = gate.run(ctx)
    assert res.verdict == GateVerdict.FAIL
    assert "weak oracle" in res.reason or "mutation score" in res.reason


def test_shell_runner_allowlist():
    with pytest.raises(PermissionError):
        run_command(["curl", "http://evil"], cwd=".")


def test_shell_runner_timeout(tmp_path):
    script = tmp_path / "slow.py"
    script.write_text("import time\ntime.sleep(5)\n", encoding="utf-8")
    res = run_command(["python", str(script)], cwd=str(tmp_path), timeout=1.0)
    assert res.timed_out and not res.ok


def test_run_instance_protocol(tmp_path):
    """Contract: JSON-line in/out via stdin/stdout (difftest runner)."""
    script = tmp_path / "echo.py"
    script.write_text(
        "import sys, json\n"
        "for line in sys.stdin:\n"
        "    obj = json.loads(line)\n"
        "    print(json.dumps({'sum': obj['a'] + obj['b']}))\n",
        encoding="utf-8")
    recs = run_instance(["python", str(script)], [{"a": 1, "b": 2}, {"a": -1, "b": 1}],
                        cwd=str(tmp_path))
    assert recs[0].output == {"sum": 3}
    assert recs[1].output == {"sum": 0}
    assert not recs[0].timed_out


def test_run_instance_timeout(tmp_path):
    script = tmp_path / "hang.py"
    script.write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
    recs = run_instance(["python", str(script)], [{"a": 1}], cwd=str(tmp_path),
                        timeout_per_input=0.5)
    assert recs[0].timed_out
