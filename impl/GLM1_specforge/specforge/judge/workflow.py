"""Judge workflow: k-sample majority vote, pairwise order swap, abstain handling.

Judge only outputs veto-or-not. It NEVER waives hard gates (constitution #4).
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from .model import ABSTAIN, PASS, JudgeModel
from .rubric import Rubric


@dataclass
class SoftGateResult:
    gate_id: str
    verdict: str = ""     # PASS | FAIL | INCONCLUSIVE | SKIP (GateVerdict-compatible)
    votes: list[str] = field(default_factory=list)
    reason: str = ""
    judge_model: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"gate_id": self.gate_id, "verdict": self.verdict, "votes": self.votes,
                "reason": self.reason, "judge_model": self.judge_model}


def run_judge(model: JudgeModel, rubric: Rubric, item: dict[str, Any],
              k: int = 3, abstain_limit: float = 1 / 3) -> SoftGateResult:
    votes: list[str] = []
    for _ in range(max(1, k)):
        v = model.score(rubric, item)
        votes.append(v.verdict)
    counts = Counter(v for v in votes if v != ABSTAIN)
    abstains = votes.count(ABSTAIN)
    base = SoftGateResult(gate_id=f"s:{rubric.rubric_id}", votes=votes, judge_model=getattr(model, "model_id", ""))
    if abstains / len(votes) > abstain_limit:
        base.verdict = "INCONCLUSIVE"
        base.reason = f"abstain rate {abstains}/{len(votes)} exceeds limit"
        return base
    if not counts:
        base.verdict = "INCONCLUSIVE"
        base.reason = "all abstained"
        return base
    top, n = counts.most_common(1)[0]
    if n <= len(votes) - n:  # no strict majority among non-abstain
        base.verdict = "INCONCLUSIVE"
        base.reason = f"split vote {dict(counts)}"
        return base
    base.verdict = "PASS" if top == PASS else "FAIL"
    base.reason = f"majority {top} ({n}/{len(votes)} votes)"
    return base


def pairwise(model: JudgeModel, rubric: Rubric, a: dict[str, Any], b: dict[str, Any]) -> str:
    """Pairwise comparison with forced order swap; disagreement -> 'tie' (not counted)."""
    v1 = _pair_call(model, rubric, a, b)   # a first
    v2 = _pair_call(model, rubric, b, a)   # b first (swapped)
    if v1 == v2:
        return v1
    return "tie"


def _pair_call(model: JudgeModel, rubric: Rubric, first: dict[str, Any], second: dict[str, Any]) -> str:
    item = {"content": f"OPTION-A:\n{first.get('content', first)}\n\nOPTION-B:\n{second.get('content', second)}"}
    v = model.score(rubric, item)
    if v.verdict == "pass":
        return "a>b"
    if v.verdict == "fail":
        return "b>a"
    return "tie"


def veto_only_gate(soft: SoftGateResult) -> str:
    """Judge is a monotone veto: never rescue. Map to gate verdict semantics."""
    return soft.verdict  # PASS means "no veto"; FAIL means veto; INCONCLUSIVE blocks
