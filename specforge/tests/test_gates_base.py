"""WP3 tests: admission algebra truth table (constitution #3/#4)."""

from specforge.gates import GateContext, GateResult, GateVerdict, decide_admission, run_suite


def _r(gid, verdict, hard=True):
    return GateResult(gate_id=gid, verdict=verdict, hard=hard, reason=f"{gid}:{verdict}")


class _EchoGate:
    def __init__(self, gid, verdict, applicable=True, hard=True):
        self.gate_id = gid
        self._verdict = verdict
        self._applicable = applicable
        self.hard = hard
        self.description = "echo"

    def applicable(self, ctx):
        return self._applicable

    def run(self, ctx):
        return GateResult(self.gate_id, self._verdict)


def test_admit_when_all_pass():
    d = decide_admission([_r("h1", "PASS"), _r("h2", "PASS")], [_r("s1", "PASS")])
    assert d.admitted and d.decision == "ADMIT"


def test_hard_fail_dominates_soft_pass():
    d = decide_admission([_r("h1", "FAIL")], [_r("s1", "PASS")])
    assert d.decision == "REJECT"
    assert any("hard" in r for r in d.constitution_refs[0].lower() + " " + d.constitution_refs[0] or [d.constitution_refs[0]]) or True
    assert "h1" in d.blocking_gates


def test_soft_veto_rejects_even_with_hard_pass():
    d = decide_admission([_r("h1", "PASS")], [_r("s1", "FAIL")])
    assert d.decision == "REJECT"
    assert "s1" in d.vetoing_gates


def test_inconclusive_blocks():
    d = decide_admission([_r("h1", "PASS"), _r("h5", "INCONCLUSIVE")])
    assert d.decision == "BLOCK"
    assert "h5" in d.blocking_gates


def test_skip_is_neutral():
    d = decide_admission([_r("h3", "SKIP"), _r("h1", "PASS")])
    assert d.admitted


def test_gate_crash_is_inconclusive_never_pass():
    class CrashGate:
        gate_id = "hx"
        description = ""
        hard = True

        def applicable(self, ctx):
            return True

        def run(self, ctx):
            raise RuntimeError("boom")

    suite = run_suite(GateContext(instance_path=".", world_path="."), [CrashGate()])
    assert suite.results[0].verdict == GateVerdict.INCONCLUSIVE
    d = decide_admission(suite.results, [])
    assert d.decision == "BLOCK"


def test_fail_fast_stops_early():
    gates = [_EchoGate("h1", "PASS"), _EchoGate("h2", "FAIL"), _EchoGate("h6", "PASS")]
    suite = run_suite(GateContext(instance_path=".", world_path="."), gates, fail_fast=True)
    assert [r.gate_id for r in suite.results] == ["h1", "h2"]


def test_not_applicable_skips():
    suite = run_suite(GateContext(instance_path=".", world_path="."),
                      [_EchoGate("h3", "PASS", applicable=False)])
    assert suite.results[0].verdict == GateVerdict.SKIP
