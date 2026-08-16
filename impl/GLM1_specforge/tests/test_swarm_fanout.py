"""WP10/WP13 tests: adaptive fan-out."""
import pytest

from specforge.swarm import EarlyStopPolicy, fanout_plan, plan_from_delta, uncertainty


def test_uncertainty_weighted():
    u = uncertainty(rework=0.5, novelty=0.5, risk=0.5)
    assert u == 0.5
    assert uncertainty(1.0, 1.0, 1.0) == 1.0
    assert uncertainty(0, 0, 0) == 0.0


def test_fanout_tiers():
    assert fanout_plan(0.1) == 1
    assert fanout_plan(0.5) == 3
    assert fanout_plan(0.9) == 6
    assert fanout_plan(1.0) <= 8  # hard cap


def test_r3_forbids_fanout():
    assert fanout_plan(0.9, r_level="R3") == 1


def test_plan_from_delta():
    delta = {"risk": 0.8, "novelty": 0.8, "r_level": "R0"}
    n, u = plan_from_delta(delta, rework_rate=0.5)
    expected_u = 0.4 * 0.5 + 0.3 * 0.8 + 0.3 * 0.8  # = 0.68 -> middle band
    assert u == pytest.approx(expected_u, abs=0.01)
    assert n == 3
    n2, _ = plan_from_delta({"risk": 0.9, "novelty": 0.9, "r_level": "R0"},
                            rework_rate=0.5)  # U=0.74 -> high band
    assert n2 == 6


def test_early_stop_policy():
    p = EarlyStopPolicy(k=2)
    assert not p.should_stop(1, 1)
    assert p.should_stop(2, 2)
    assert not p.should_stop(2, 1)  # not identical passes
    assert not p.should_stop(5, 5, r_level="R3")  # R3: never early stop


def test_early_stop_disabled():
    p = EarlyStopPolicy(k=2, enabled=False)
    assert not p.should_stop(10, 10)
