"""WP3 tests: statistical gates (Wilson / pass^k / SPRT)."""
import pytest

from specforge.gates import (
    k_of_n_gate,
    required_reruns,
    sprt_gate,
    threshold_gate,
    wilson_lower,
    zero_failure_upper_bound,
)


def test_wilson_lower_basic():
    assert wilson_lower(0, 0) == 0.0
    assert wilson_lower(100, 100) > 0.95
    # 7/10 gives a low lower bound despite 70% point estimate
    lb = wilson_lower(7, 10)
    assert 0.35 < lb < 0.92


def test_threshold_gate_three_way():
    assert threshold_gate(100, 100, 0.9).verdict == "PASS"
    # clearly below: FAIL
    assert threshold_gate(2, 10, 0.9).verdict == "FAIL"
    # borderline with few samples: INCONCLUSIVE (never silently clear)
    v = threshold_gate(9, 10, 0.9)
    assert v.verdict == "INCONCLUSIVE"
    v0 = threshold_gate(0, 0, 0.9)
    assert v0.verdict == "INCONCLUSIVE"


def test_k_of_n():
    assert k_of_n_gate([True, True, True], 3).verdict == "PASS"
    assert k_of_n_gate([True, True, False], 3).verdict == "FAIL"
    assert k_of_n_gate([True, True], 3).verdict == "INCONCLUSIVE"


def test_sprt():
    # clearly good sequence -> PASS
    seq = [True] * 30
    assert sprt_gate(seq, p0=0.7, p1=0.9).verdict == "PASS"
    # clearly bad -> FAIL
    seq_bad = [False] * 20
    assert sprt_gate(seq_bad, p0=0.7, p1=0.9).verdict == "FAIL"
    # mixed/short -> INCONCLUSIVE
    assert sprt_gate([True, False, True], p0=0.7, p1=0.9).verdict == "INCONCLUSIVE"
    with pytest.raises(ValueError):
        sprt_gate([], p0=0.9, p1=0.7)


def test_rerun_budget_math():
    # rule of three: 3 green runs => failure upper bound ~ 1 (99% conf ~ 1.53)
    ub = zero_failure_upper_bound(3, confidence=0.95)
    assert 0.9 < ub < 1.1
    n = required_reruns(1e-3, confidence=0.95)
    assert 2900 < n < 4000  # ~3000 from the research formula


def test_sprt_requires_ordered_p():
    with pytest.raises(ValueError):
        sprt_gate([True], p0=0.9, p1=0.5)
