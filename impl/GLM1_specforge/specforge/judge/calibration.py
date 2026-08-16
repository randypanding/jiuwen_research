"""Judge calibration: Cohen's kappa + monitoring signals (llm-as-judge research).

kappa >= 0.6 required before a judge goes live; 8 warning signals monitored.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .model import ABSTAIN, JudgeModel
from .rubric import Rubric

KAPPA_GATE = 0.6


def cohens_kappa(a: list[str], b: list[str]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("kappa requires equal non-empty label lists")
    labels = sorted(set(a) | set(b))
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((a.count(lab) / n) * (b.count(lab) / n) for lab in labels)
    if pe == 1.0:
        return 1.0 if po == 1.0 else 0.0
    return (po - pe) / (1 - pe)


@dataclass
class CalibrationItem:
    item: dict[str, Any]
    gold: str  # expected verdict: pass|fail


@dataclass
class CalibrationReport:
    judge_model: str
    n_items: int
    agreement: float
    kappa: float
    abstain_rate: float
    ready: bool
    signals: list[str] = field(default_factory=list)
    confusion: dict[str, dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "judge_model": self.judge_model, "n_items": self.n_items,
            "agreement": self.agreement, "kappa": self.kappa,
            "abstain_rate": self.abstain_rate, "ready": self.ready,
            "signals": self.signals, "confusion": self.confusion,
        }


def calibrate(model: JudgeModel, rubric: Rubric, labeled: list[CalibrationItem]) -> CalibrationReport:
    preds: list[str] = []
    for li in labeled:
        v = model.score(rubric, li.item)
        preds.append(v.verdict)
    golds = [li.gold for li in labeled]
    n = len(labeled)
    agreement = sum(1 for p, g in zip(preds, golds) if p == g) / n if n else 0.0
    abstain_rate = preds.count(ABSTAIN) / n if n else 0.0
    try:
        kappa = cohens_kappa(preds, golds)
    except ValueError:
        kappa = 0.0
    confusion: dict[str, dict[str, int]] = {}
    for p, g in zip(preds, golds):
        confusion.setdefault(g, {}).setdefault(p, 0)
        confusion[g][p] += 1

    signals: list[str] = []
    if kappa < KAPPA_GATE:
        signals.append(f"kappa {kappa:.3f} < {KAPPA_GATE}: not ready")
    if abstain_rate > 0.2:
        signals.append(f"abstain rate {abstain_rate:.2f} > 0.2")
    if agreement - kappa > 0.2:
        signals.append(f"agreement-kappa gap {agreement - kappa:.2f} > 0.2 (class imbalance illusion)")
    if n < 30:
        signals.append(f"calibration set too small ({n} < 30)")

    return CalibrationReport(
        judge_model=getattr(model, "model_id", "?"), n_items=n, agreement=agreement,
        kappa=kappa, abstain_rate=abstain_rate, ready=kappa >= KAPPA_GATE and abstain_rate <= 0.2,
        signals=signals, confusion=confusion)


WARNING_SIGNALS = [
    "order-flip rate abnormal",
    "kappa-exact gap > 20pp",
    "length monotonically inflates score",
    "long-doc variance spikes",
    "cannot point at failing turn",
    "renaming flips code verdicts",
    "verbose wins but humans disagree",
    "metadata leaks into verdicts",
]
