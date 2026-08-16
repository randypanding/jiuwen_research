from __future__ import annotations

from swarm_kernel.gates.base import wilson_bounds, wilson_verdict


def test_wilson_bounds_shape() -> None:
    lo, hi = wilson_bounds(3, 3)
    assert 0.0 <= lo <= hi <= 1.0
    lo0, hi0 = wilson_bounds(0, 3)
    assert lo0 >= 0.0
    assert hi0 < 0.7


def test_all_pass_is_pass() -> None:
    assert wilson_verdict(3, 3) == "pass"


def test_all_fail_is_fail() -> None:
    assert wilson_verdict(0, 3) == "fail"


def test_mixed_small_sample_is_inconclusive() -> None:
    assert wilson_verdict(2, 3) == "inconclusive"
    assert wilson_verdict(1, 3) == "inconclusive"


def test_single_attempt_is_deterministic() -> None:
    assert wilson_verdict(1, 1) == "pass"
    assert wilson_verdict(0, 1) == "fail"


def test_zero_samples_inconclusive() -> None:
    assert wilson_verdict(0, 0) == "inconclusive"
