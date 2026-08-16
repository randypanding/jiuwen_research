"""JudgeModel protocol + deterministic FakeJudge for tests."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

from .rubric import Rubric

PASS, FAIL, ABSTAIN = "pass", "fail", "abstain"


@dataclass
class JudgeVerdict:
    verdict: str                    # pass | fail | abstain
    score: float
    reasons: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    raw: str = ""

    @property
    def abstained(self) -> bool:
        return self.verdict == ABSTAIN

    def to_dict(self) -> dict[str, Any]:
        return {"verdict": self.verdict, "score": self.score,
                "reasons": self.reasons, "evidence": self.evidence}


class JudgeModel(Protocol):
    """LLM adapter contract. Judge tier must be >= builder tier (constitution #14)."""

    model_id: str
    tier: str  # "RU-L" | "RU-M" | "RU-H"

    def score(self, rubric: Rubric, item: dict[str, Any]) -> JudgeVerdict: ...


class EchoJudge:
    """Deterministic judge used in tests: scans item for keywords.

    rules: {keyword: (verdict, score)}; first hit wins; abstain on no hit.
    """

    def __init__(self, rules: dict[str, tuple[str, float]], model_id: str = "fake-judge",
                 tier: str = "RU-H"):
        self.rules = rules
        self.model_id = model_id
        self.tier = tier

    def score(self, rubric: Rubric, item: dict[str, Any]) -> JudgeVerdict:
        text = item.get("content", "") if isinstance(item, dict) else str(item)
        for kw, (verdict, sc) in self.rules.items():
            if kw in text:
                return JudgeVerdict(verdict, sc,
                                    reasons=[f"matched {kw!r}"],
                                    evidence=[f"item contains {kw!r}"])
        return JudgeVerdict(ABSTAIN, 0.0, reasons=["no rule matched"], evidence=[])


def parse_verdict_json(raw: str) -> JudgeVerdict:
    """Extract the LAST JSON object from a CoT-style response."""
    matches = re.findall(r"\{[^{}]*\"verdict\"[^{}]*\}", raw, re.DOTALL)
    if not matches:
        return JudgeVerdict(ABSTAIN, 0.0, reasons=["unparseable judge output"], raw=raw)
    import json

    try:
        d = json.loads(matches[-1])
    except json.JSONDecodeError:
        return JudgeVerdict(ABSTAIN, 0.0, reasons=["invalid JSON in judge output"], raw=raw)
    verdict = str(d.get("verdict", ABSTAIN)).lower()
    if verdict not in (PASS, FAIL, ABSTAIN):
        verdict = ABSTAIN
    ev = d.get("evidence") or []
    rs = d.get("reasons") or []
    if not isinstance(ev, list):
        ev = [str(ev)]
    if not isinstance(rs, list):
        rs = [str(rs)]
    return JudgeVerdict(verdict, float(d.get("score", 0.0)), reasons=rs, evidence=ev, raw=raw)


TIER_ORDER = {"RU-L": 0, "RU-M": 1, "RU-H": 2}


def assert_tier_ok(judge_tier: str, builder_tier: str) -> None:
    if TIER_ORDER.get(judge_tier, -1) < TIER_ORDER.get(builder_tier, 99):
        raise PermissionError(
            f"constitution #14 violated: judge tier {judge_tier} < builder tier {builder_tier}")


def assert_independence(judge_model_id: str, builder_model_id: str,
                        family_table: Optional[dict[str, str]] = None) -> None:
    """Model relationship checks: same model / same family / derived -> violation."""
    if judge_model_id == builder_model_id:
        raise PermissionError(f"constitution #5 violated: judge {judge_model_id} == builder")
    family_table = family_table or {}
    jf = family_table.get(judge_model_id)
    bf = family_table.get(builder_model_id)
    if jf and bf and jf == bf:
        raise PermissionError(
            f"constitution #5 violated: judge/builder share family {jf}")
    if (jf and jf in builder_model_id) or (bf and bf in judge_model_id):
        raise PermissionError("constitution #5 violated: possible derivation relationship")
