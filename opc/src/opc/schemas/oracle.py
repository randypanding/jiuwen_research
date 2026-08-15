from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, field_validator

from opc.schemas.common import BaseSchema, Verdict

SCENARIO_ID_RE = __import__("re").compile(r"^SCN-[A-Za-z0-9_-]+$")


class ScenarioSpec(BaseSchema):
    """A holdout scenario: part of the oracle body, invisible to builders.

    oracle_type:
      executable   - inputs run against the instance; assertions are mechanical (H3 main body)
      metamorphic  - no exact oracle; a metamorphic relation must hold (fallback oracle)
      rubric       - judged by the judge workflow (soft gate input, still needs a hard witness elsewhere)
    """

    scenario_id: str
    oracle_type: Literal["executable", "metamorphic", "rubric"] = "executable"
    domain: str = ""
    visibility: Literal["holdout", "public"] = "holdout"
    entrypoint: str = Field(default="main", description="callable/module the instance exposes for the run")
    inputs: dict[str, Any] = Field(default_factory=dict)
    expected: dict[str, Any] = Field(default_factory=dict)
    assertions: list[str] = Field(
        default_factory=list,
        description="python expressions evaluated with {'result': r, 'inputs': i} in scope",
    )
    metamorphic_relation: str = ""
    canary: str = Field(
        default="",
        description="secret marker; presence inside a builder workspace proves holdout leakage",
    )
    redact: list[str] = Field(
        default_factory=list,
        description="dotted output paths stripped before comparison (non-deterministic fields)",
    )
    timeout_s: float = 30.0
    clause_refs: list[str] = Field(default_factory=list)

    @field_validator("scenario_id")
    @classmethod
    def _sid(cls, v: str) -> str:
        if not SCENARIO_ID_RE.match(v):
            raise ValueError(f"invalid scenario id {v!r}")
        return v


class JudgeSample(BaseSchema):
    sample_index: int
    verdict: Literal["reject", "no_reject"]
    reasons: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class JudgeVerdict(BaseSchema):
    """Soft gate output. The judge may only reject or not reject.

    It never emits 'exempt hard gates'; abstention (inconsistent samples)
    counts as rejection of admission, per the monotone-veto algebra.
    """

    verdict: Verdict
    abstained: bool = False
    samples: list[JudgeSample] = Field(default_factory=list)
    rubric_id: str = ""
    judge_model: str = ""
    position_swapped_consistent: bool | None = None
    reasons: list[str] = Field(default_factory=list)

    @classmethod
    def from_samples(
        cls,
        samples: list[JudgeSample],
        rubric_id: str = "",
        judge_model: str = "",
        position_swapped_consistent: bool | None = None,
    ) -> "JudgeVerdict":
        if not samples:
            return cls(
                verdict=Verdict.INCONCLUSIVE,
                abstained=True,
                samples=samples,
                rubric_id=rubric_id,
                judge_model=judge_model,
                position_swapped_consistent=position_swapped_consistent,
                reasons=["no judge samples"],
            )
        rejects = sum(1 for s in samples if s.verdict == "reject")
        majority_reject = rejects * 2 > len(samples)
        split = 0 < rejects < len(samples)
        if position_swapped_consistent is False:
            return cls(
                verdict=Verdict.INCONCLUSIVE,
                abstained=True,
                samples=samples,
                rubric_id=rubric_id,
                judge_model=judge_model,
                position_swapped_consistent=False,
                reasons=["position bias detected: swapped-order verdicts disagree; sample discarded"],
            )
        if majority_reject:
            reasons = sorted({r for s in samples if s.verdict == "reject" for r in s.reasons})
            return cls(
                verdict=Verdict.FAIL,
                samples=samples,
                rubric_id=rubric_id,
                judge_model=judge_model,
                position_swapped_consistent=position_swapped_consistent,
                reasons=reasons,
            )
        if split:
            return cls(
                verdict=Verdict.INCONCLUSIVE,
                abstained=True,
                samples=samples,
                rubric_id=rubric_id,
                judge_model=judge_model,
                position_swapped_consistent=position_swapped_consistent,
                reasons=["judge samples split; abstain rather than admit"],
            )
        return cls(
            verdict=Verdict.PASS,
            samples=samples,
            rubric_id=rubric_id,
            judge_model=judge_model,
            position_swapped_consistent=position_swapped_consistent,
            reasons=[],
        )
