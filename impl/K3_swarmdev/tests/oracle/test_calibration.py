import json

import pytest

from swarmdev.contracts import CalibrationItem
from swarmdev.oracle import JudgeCalibrator, JudgeWorkflow, cohen_kappa


def test_kappa_perfect_agreement():
    assert cohen_kappa([0, 1, 2], [0, 1, 2]) == 1.0


def test_kappa_known_value():
    assert cohen_kappa([0, 0, 1, 1, 2], [0, 1, 1, 1, 2]) == pytest.approx(0.6875)


def test_kappa_pe_equals_one_returns_one():
    assert cohen_kappa([1, 1, 1], [1, 1, 1]) == 1.0


def test_kappa_length_mismatch_raises():
    with pytest.raises(ValueError):
        cohen_kappa([0, 1], [0])


def _verdict_model(prompt: str) -> str:
    if "VETO-CASE" in prompt:
        return json.dumps({"verdict": "veto", "reasons": ["broken"], "evidence_refs": []})
    if "SKIP-CASE" in prompt:
        return json.dumps({"verdict": "abstain", "reasons": [], "evidence_refs": []})
    return json.dumps({"verdict": "no_veto", "reasons": [], "evidence_refs": []})


def test_calibrator_enabled_on_agreement():
    workflow = JudgeWorkflow(_verdict_model, samples=3)
    calibrator = JudgeCalibrator(workflow)
    items = [
        CalibrationItem(item_id="C1", artifact_summary="VETO-CASE", gold_verdict="veto"),
        CalibrationItem(item_id="C2", artifact_summary="PASS-CASE", gold_verdict="no_veto"),
        CalibrationItem(item_id="C3", artifact_summary="SKIP-CASE", gold_verdict="abstain"),
    ]
    report = calibrator.calibrate(items)
    assert report.kappa == pytest.approx(1.0)
    assert report.raw_agreement == pytest.approx(1.0)
    assert report.enabled


def test_calibrator_disabled_on_confusion():
    constant_no_veto = JudgeWorkflow(
        lambda prompt: json.dumps({"verdict": "no_veto", "reasons": [], "evidence_refs": []}),
        samples=3,
    )
    calibrator = JudgeCalibrator(constant_no_veto)
    items = [
        CalibrationItem(item_id="C1", artifact_summary="VETO-CASE", gold_verdict="veto"),
        CalibrationItem(item_id="C2", artifact_summary="PASS-CASE", gold_verdict="no_veto"),
    ]
    report = calibrator.calibrate(items)
    assert report.kappa == pytest.approx(0.0)
    assert report.raw_agreement == pytest.approx(0.5)
    assert not report.enabled
