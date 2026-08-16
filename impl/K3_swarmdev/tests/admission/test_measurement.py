import pytest

from swarmdev.admission import InstanceGateResult, Outcome, classify_fanout


def _r(instance_id, passed, tier="L"):
    return InstanceGateResult(instance_id=instance_id, gates_passed=passed, tier=tier)


def test_insufficient_when_under_min_samples_with_failure():
    results = [_r("I-0", True), _r("I-1", False)]
    assert classify_fanout(results, has_divergence=False) == Outcome.INSUFFICIENT


def test_closed_all_pass_no_divergence():
    results = [_r("I-0", True), _r("I-1", True), _r("I-2", True)]
    assert classify_fanout(results, has_divergence=False) == Outcome.CLOSED


def test_silence_all_pass_with_divergence():
    results = [_r("I-0", True), _r("I-1", True), _r("I-2", True)]
    assert classify_fanout(results, has_divergence=True) == Outcome.SILENCE


def test_divergence_mixed_pass_fail():
    results = [_r("I-0", True), _r("I-1", False), _r("I-2", True)]
    assert classify_fanout(results, has_divergence=False) == Outcome.DIVERGENCE


def test_tier_gap_low_tier_all_fail_high_tier_pass():
    results = [_r("I-0", False, "L"), _r("I-1", False, "L"), _r("I-2", True, "H")]
    assert classify_fanout(results, has_divergence=False) == Outcome.TIER_GAP


def test_spec_oracle_conflict_all_fail():
    results = [_r("I-0", False), _r("I-1", False), _r("I-2", False)]
    assert classify_fanout(results, has_divergence=False) == Outcome.SPEC_ORACLE_CONFLICT


def test_all_fail_with_failed_higher_tier_is_conflict():
    results = [_r("I-0", False, "L"), _r("I-1", False, "L"), _r("I-2", False, "H")]
    assert classify_fanout(results, has_divergence=False) == Outcome.SPEC_ORACLE_CONFLICT


def test_empty_results_is_insufficient():
    assert classify_fanout([], has_divergence=False) == Outcome.INSUFFICIENT


def test_invalid_tier_rejected_by_schema():
    with pytest.raises(ValueError):
        InstanceGateResult(instance_id="I-0", gates_passed=True, tier="X")
