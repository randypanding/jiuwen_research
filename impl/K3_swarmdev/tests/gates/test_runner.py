import sys

import pytest

from swarmdev.contracts import GateOutcome
from swarmdev.contracts.receipt import GateStatus
from swarmdev.gates import BuildGate, GateRunner


class FakeGate:
    def __init__(self, gate_id: str, status: GateStatus):
        self.gate_id = gate_id
        self.status = status
        self.calls = 0

    def run(self, ctx):
        self.calls += 1
        return GateOutcome(gate_id=self.gate_id, status=self.status)


def test_runner_fail_fast_stops_after_fail(make_ctx):
    h1 = FakeGate("H1", GateStatus.FAIL)
    h2 = FakeGate("H2", GateStatus.PASS)
    outcomes = GateRunner([h1, h2], fail_fast=True).run(make_ctx())
    assert [o.gate_id for o in outcomes] == ["H1"]
    assert outcomes[0].status == GateStatus.FAIL
    assert h1.calls == 1
    assert h2.calls == 0


def test_runner_fail_fast_stops_on_blocked(make_ctx):
    h1 = FakeGate("H1", GateStatus.BLOCKED)
    h2 = FakeGate("H2", GateStatus.PASS)
    outcomes = GateRunner([h1, h2]).run(make_ctx())
    assert len(outcomes) == 1
    assert h2.calls == 0


def test_runner_inconclusive_does_not_stop(make_ctx):
    h1 = FakeGate("H1", GateStatus.INCONCLUSIVE)
    h2 = FakeGate("H2", GateStatus.PASS)
    outcomes = GateRunner([h1, h2]).run(make_ctx())
    assert [o.gate_id for o in outcomes] == ["H1", "H2"]


def test_runner_no_fail_fast_runs_all(make_ctx):
    h1 = FakeGate("H1", GateStatus.FAIL)
    h2 = FakeGate("H2", GateStatus.PASS)
    outcomes = GateRunner([h1, h2], fail_fast=False).run(make_ctx())
    assert [o.gate_id for o in outcomes] == ["H1", "H2"]
    assert h2.calls == 1


def test_runner_rejects_duplicate_gate_id():
    with pytest.raises(ValueError, match="duplicate"):
        GateRunner([FakeGate("H1", GateStatus.PASS), FakeGate("H1", GateStatus.PASS)])


def test_runner_rejects_unknown_gate_id():
    with pytest.raises(ValueError, match="unknown"):
        GateRunner([FakeGate("H9", GateStatus.PASS)])


def test_runner_real_h1_fail_skips_h2(make_ctx):
    ctx = make_ctx()
    h1 = BuildGate([[sys.executable, "-c", "import sys; sys.exit(1)"]])
    h2 = FakeGate("H2", GateStatus.PASS)
    outcomes = GateRunner([h1, h2]).run(ctx)
    assert len(outcomes) == 1
    assert outcomes[0].gate_id == "H1"
    assert outcomes[0].status == GateStatus.FAIL
    assert h2.calls == 0
