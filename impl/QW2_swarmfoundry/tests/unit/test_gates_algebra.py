import pytest

from swarmfoundry.schema.gates import (
    GATE_H1,
    GATE_H2,
    GATE_H3,
    GATE_H4,
    GATE_H5,
    GATE_H6,
    GATE_H7,
    GATE_H8,
    HARD_GATES,
    GateResult,
    admit,
)
from swarmfoundry.schema.gates import GateAlgebraError


def _hard(status="pass"):
    return [GateResult(gate_id=g, status=status) for g in HARD_GATES]


def _soft(status="pass"):
    return [GateResult(gate_id="S", status=status)]


def test_all_green_admits():
    d = admit(_hard(), _soft(), "inst-1")
    assert d.admitted


def test_any_hard_failure_blocks():
    for gid in HARD_GATES:
        results = _hard()
        results = [GateResult(gate_id=r.gate_id, status="fail" if r.gate_id == gid else "pass") for r in results]
        assert not admit(results, _soft(), "inst-1").admitted


def test_soft_veto_blocks_even_when_hard_green():
    d = admit(_hard(), _soft("fail"), "inst-1")
    assert not d.admitted


def test_soft_gate_can_never_rescue_hard_failure():
    d = admit(_hard("fail"), _soft("pass"), "inst-1")
    assert not d.admitted


def test_missing_gate_fails_closed():
    partial = _hard()[1:]
    d = admit(partial, _soft(), "inst-1")
    assert not d.admitted
    assert "missing gates" in d.rule


def test_error_status_is_not_pass():
    results = [GateResult(gate_id=g, status="error" if g == GATE_H3 else "pass") for g in HARD_GATES]
    assert not admit(results, _soft(), "inst-1").admitted


def test_unknown_gate_rejected():
    with pytest.raises(GateAlgebraError):
        admit([GateResult(gate_id="H9", status="pass")], [], "inst-1")
    with pytest.raises(GateAlgebraError):
        admit([], [GateResult(gate_id="H1", status="pass")], "inst-1")
