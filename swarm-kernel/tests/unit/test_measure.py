from __future__ import annotations

from swarm_kernel.contracts.fanout import MeasurementClassification
from swarm_kernel.measure.engine import classify_fanout


def test_closed_when_all_pass_and_no_divergence() -> None:
    ev = classify_fanout("fo-1", "sd-1", {"a": True, "b": True, "c": True}, divergence_detected=False)
    assert ev.classification == MeasurementClassification.CLOSED


def test_silence_when_all_pass_but_divergence() -> None:
    ev = classify_fanout("fo-1", "sd-1", {"a": True, "b": True, "c": True}, divergence_detected=True, divergence_inputs=["x=1"])
    assert ev.classification == MeasurementClassification.SILENCE
    assert ev.divergence_inputs == ["x=1"]


def test_divergence_when_partial_pass() -> None:
    ev = classify_fanout("fo-1", "sd-1", {"a": True, "b": False, "c": True}, divergence_detected=False)
    assert ev.classification == MeasurementClassification.DIVERGENCE


def test_tier_upgrade_when_all_fail_then_strong_succeeds() -> None:
    ev = classify_fanout("fo-1", "sd-1", {"a": False, "b": False, "c": False}, divergence_detected=False, stronger_tier_succeeded=True)
    assert ev.classification == MeasurementClassification.TIER_UPGRADE_REQUIRED


def test_conflict_when_all_fail_even_strong() -> None:
    ev = classify_fanout("fo-1", "sd-1", {"a": False, "b": False, "c": False}, divergence_detected=False, stronger_tier_succeeded=False)
    assert ev.classification == MeasurementClassification.SPEC_ORACLE_CONFLICT


def test_insufficient_samples_below_three_with_failure() -> None:
    ev = classify_fanout("fo-1", "sd-1", {"a": True, "b": False}, divergence_detected=False)
    assert ev.classification == MeasurementClassification.INSUFFICIENT_SAMPLES


def test_two_instances_all_pass_can_be_closed() -> None:
    ev = classify_fanout("fo-1", "sd-1", {"a": True, "b": True}, divergence_detected=False)
    assert ev.classification == MeasurementClassification.CLOSED
