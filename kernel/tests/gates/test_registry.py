"""Gate execution policy (D17): run-everything by default, staged fail-fast.

M0/M1 run every gate and record every measurement — the org is still
calibrating. From M2 on, gates run in ascending cost order and stop at the
first blocker; the un-run gates then surface as *missing* in the hard report,
which the fail-closed algebra (D3) already blocks on.
"""

from __future__ import annotations

import pytest

from swarmkernel.contracts.gate import Finding, GateId, GateResult, GateStatus
from swarmkernel.contracts.governance import MigrationStage
from swarmkernel.gates.base import GateContext, GateRegistry


class FakeGate:
    def __init__(self, gate_id: GateId, status: GateStatus, cost: int) -> None:
        self.gate_id = gate_id
        self.name = gate_id.value
        self.relative_cost = cost
        self.status = status
        self.ran = False

    def run(self, ctx: GateContext) -> GateResult:
        self.ran = True
        findings = (
            []
            if self.status is GateStatus.PASS
            else [Finding(code=f"{self.gate_id.value}.X", message="broken")]
        )
        return GateResult(gate=self.gate_id, status=self.status, findings=findings)


def registry(*gates: FakeGate) -> GateRegistry:
    return GateRegistry(gates)


@pytest.fixture
def ctx() -> GateContext:
    return GateContext(unit_id="U", instance_id="i")


def test_default_runs_everything_even_when_a_gate_fails(ctx):
    a = FakeGate(GateId.H1_BUILD, GateStatus.FAIL, 1)
    b = FakeGate(GateId.H5_DIFFERENTIAL, GateStatus.PASS, 5)
    results = registry(a, b).run_all(ctx)
    assert a.ran and b.ran
    assert len(results) == 2


def test_fail_fast_stops_at_the_first_blocker_in_cost_order(ctx):
    """H5 (cost 5) would fail, but H1 (cost 1) fails first and cheaper: the
    expensive gate is never paid for."""

    h1 = FakeGate(GateId.H1_BUILD, GateStatus.FAIL, 1)
    h5 = FakeGate(GateId.H5_DIFFERENTIAL, GateStatus.FAIL, 5)
    results = registry(h5, h1).run_all(ctx, fail_fast=True)
    assert h1.ran and not h5.ran
    assert [r.gate for r in results] == [GateId.H1_BUILD]


def test_fail_fast_runs_all_when_everything_passes(ctx):
    gates = [
        FakeGate(GateId.H1_BUILD, GateStatus.PASS, 1),
        FakeGate(GateId.H5_DIFFERENTIAL, GateStatus.PASS, 5),
    ]
    results = registry(*gates).run_all(ctx, fail_fast=True)
    assert all(g.ran for g in gates)
    assert [r.gate for r in results] == sorted(
        (g.gate_id for g in gates), key=lambda g: g.value
    )


def test_fail_fast_pays_cheap_green_gates_before_the_expensive_red_one(ctx):
    """Cost-ascending order: the cheap green gates still record their
    measurement before the expensive red one stops the run."""

    h8 = FakeGate(GateId.H8_BUDGET, GateStatus.PASS, 1)
    h1 = FakeGate(GateId.H1_BUILD, GateStatus.PASS, 1)
    h2 = FakeGate(GateId.H2_UNIT_PROPERTY, GateStatus.PASS, 2)
    h5 = FakeGate(GateId.H5_DIFFERENTIAL, GateStatus.FAIL, 5)
    results = registry(h5, h2, h1, h8).run_all(ctx, fail_fast=True)
    assert h8.ran and h1.ran and h2.ran and h5.ran
    # Report order stays by gate id (stable for readers); cost order only
    # governed *execution*.
    assert [r.gate for r in results] == sorted(
        (GateId.H1_BUILD, GateId.H2_UNIT_PROPERTY, GateId.H5_DIFFERENTIAL, GateId.H8_BUDGET),
        key=lambda g: g.value,
    )


@pytest.mark.parametrize(
    "stage,expect_all",
    [
        (MigrationStage.M0_HARVEST, True),
        (MigrationStage.M1_ANCHOR, True),
        (MigrationStage.M2_REGENERATE, False),
        (MigrationStage.M3_FACTORY, False),
    ],
)
def test_stage_policy(ctx, stage, expect_all):
    """D17: M0/M1 collect every measurement; M2+ stop at the first blocker."""

    blocker = FakeGate(GateId.H1_BUILD, GateStatus.FAIL, 1)
    expensive = FakeGate(GateId.H5_DIFFERENTIAL, GateStatus.PASS, 5)
    registry(blocker, expensive).run_for_stage(ctx, stage)
    assert blocker.ran
    assert expensive.ran is expect_all


# ------------------------------------------------ real-gate cost discipline


def test_every_real_gate_declares_relative_cost():
    """Regression: the real gates once carried only a ``#:`` comment where the
    attribute belonged, so every cost silently defaulted to 3 and fail-fast
    ordering degenerated to gate-id alphabetical — while FakeGate-based tests
    (which hand-set the attribute) masked the defect entirely. Every gate in
    the default registry must declare a real int."""

    from swarmkernel.gates.hard import default_registry

    reg = default_registry()
    for gate in reg.ids():
        g = reg.get(gate)
        assert hasattr(g, "relative_cost"), (
            f"{type(g).__name__} declares no relative_cost; D17 fail-fast "
            "ordering would silently degrade"
        )
        assert isinstance(g.relative_cost, int) and g.relative_cost >= 1


def test_real_gate_cost_order_is_not_alphabetical():
    """The point of the costs: H5 (differential, 5) and H3 (holdout, 4) run
    after the cheap static checks, not before them by id accident."""

    from swarmkernel.gates.hard import default_registry

    reg = default_registry()
    costed = sorted(
        ((reg.get(g).relative_cost, g.value) for g in reg.ids())
    )
    cheapest = [v for c, v in costed if c == costed[0][0]]
    assert "H1" in cheapest[0]
    assert costed[-1][1] == "H5"  # the differential is the most expensive
