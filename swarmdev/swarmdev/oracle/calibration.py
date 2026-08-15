from __future__ import annotations

from pydantic import BaseModel

from swarmdev.contracts import CalibrationItem, JudgeRubric, RubricDimension
from swarmdev.contracts.oracle import RubricLevel

from swarmdev.oracle.judge import JudgeWorkflow

_VERDICT_TO_INT = {"veto": 0, "no_veto": 1, "abstain": 2}


def cohen_kappa(a: list[int], b: list[int]) -> float:
    if len(a) != len(b):
        raise ValueError("rating lists must have equal length")
    n = len(a)
    if n == 0:
        raise ValueError("rating lists must not be empty")
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    categories = set(a) | set(b)
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in categories)
    if pe == 1:
        return 1.0
    return (po - pe) / (1 - pe)


class CalibrationReport(BaseModel):
    kappa: float
    raw_agreement: float
    enabled: bool


class JudgeCalibrator:
    def __init__(self, workflow: JudgeWorkflow, threshold: float = 0.6):
        self.workflow = workflow
        self.threshold = threshold

    @staticmethod
    def _calibration_rubric() -> JudgeRubric:
        return JudgeRubric(
            rubric_id="RUB-CALIBRATION",
            target_description="calibration probe artifact",
            dimensions=[
                RubricDimension(
                    dimension_id="D-CAL",
                    description="veto clearly broken artifacts, pass sound ones",
                    levels=[
                        RubricLevel(
                            level=0,
                            label="veto",
                            observable_criteria="artifact is clearly broken",
                        ),
                        RubricLevel(
                            level=1,
                            label="no_veto",
                            observable_criteria="artifact is sound",
                        ),
                    ],
                )
            ],
            evidence_required=False,
        )

    def calibrate(self, items: list[CalibrationItem]) -> CalibrationReport:
        if not items:
            return CalibrationReport(kappa=0.0, raw_agreement=0.0, enabled=False)
        rubric = self._calibration_rubric()
        preds: list[int] = []
        golds: list[int] = []
        for item in items:
            verdict = self.workflow.evaluate(rubric, item.artifact_summary, [])
            preds.append(_VERDICT_TO_INT[verdict.verdict])
            golds.append(_VERDICT_TO_INT[item.gold_verdict])
        raw_agreement = sum(1 for x, y in zip(preds, golds) if x == y) / len(items)
        kappa = cohen_kappa(preds, golds)
        return CalibrationReport(
            kappa=kappa, raw_agreement=raw_agreement, enabled=kappa >= self.threshold
        )
