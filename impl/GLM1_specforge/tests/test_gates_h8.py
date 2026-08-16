"""H8 budget gate: cost/wall-time ceilings."""
from __future__ import annotations

from specforge.gates import GateContext
from specforge.gates.base import GateVerdict
from specforge.gates.h8_budget import H8BudgetGate


def _ctx(budget=None, extra=None) -> GateContext:
    return GateContext(instance_path=".", world_path=".", budget=budget, extra=extra or {})


def test_h8_pass_within_budget():
    res = H8BudgetGate().run(_ctx(extra={"cost_usd": 3.2, "wall_s": 120}))
    assert res.verdict == GateVerdict.PASS
    assert res.evidence["cost_usd"] == {"limit": 10.0, "spent": 3.2}


def test_h8_fail_cost_overrun():
    res = H8BudgetGate().run(_ctx(extra={"cost_usd": 42.0, "wall_s": 10}))
    assert res.verdict == GateVerdict.FAIL
    assert "cost" in res.reason


def test_h8_fail_wall_overrun():
    res = H8BudgetGate().run(_ctx(extra={"cost_usd": 1.0, "wall_s": 99999}))
    assert res.verdict == GateVerdict.FAIL
    assert "wall" in res.reason


def test_h8_custom_limits():
    res = H8BudgetGate().run(_ctx(budget={"cost_usd": 0.5, "wall_s": 60},
                                  extra={"cost_usd": 0.6, "wall_s": 10}))
    assert res.verdict == GateVerdict.FAIL  # 0.6 > 0.5 custom cost limit


def test_h8_boundary_exact_limit_passes():
    res = H8BudgetGate().run(_ctx(budget={"cost_usd": 1.0}, extra={"cost_usd": 1.0}))
    assert res.verdict == GateVerdict.PASS


def test_h8_defaults_when_no_telemetry():
    """Zero spend against defaults must pass and still emit full evidence."""
    res = H8BudgetGate().run(_ctx())
    assert res.verdict == GateVerdict.PASS
    assert res.evidence["wall_s"]["limit"] == 3600.0
