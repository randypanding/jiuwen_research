from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class Expectation(BaseModel):
    exit_code: Optional[int] = None
    stdout_regex: Optional[str] = None
    stderr_regex: Optional[str] = None
    files_exist: list[str] = Field(default_factory=list)
    files_contain: dict[str, str] = Field(default_factory=dict, description="path -> regex")


class HoldoutScenario(BaseModel):
    """端到端场景（holdout）。对 builder 不可见；定期轮换防『考穿』。"""

    scenario_id: str
    spec_clause_ids: list[str]
    title: str
    setup_commands: list[str] = Field(default_factory=list)
    run_command: str
    cwd: Optional[str] = None
    env: dict[str, str] = Field(default_factory=dict)
    timeout_s: float = 120.0
    expectation: Expectation = Field(default_factory=Expectation)
    rotation_epoch: int = 0
    confidential: bool = True


class RubricLevel(BaseModel):
    level: int
    label: str
    observable_criteria: str


class RubricDimension(BaseModel):
    dimension_id: str
    description: str
    levels: list[RubricLevel]
    weight: float = 1.0


class JudgeRubric(BaseModel):
    """软门禁 rubric。一个 rubric 只评一个目标；逐维度先推理后结构化输出。"""

    rubric_id: str
    target_description: str
    dimensions: list[RubricDimension]
    abstain_allowed: bool = True
    evidence_required: bool = True


class CalibrationItem(BaseModel):
    item_id: str
    artifact_summary: str
    gold_verdict: Literal["veto", "no_veto", "abstain"]
    note: str = ""


class OracleBundle(BaseModel):
    """判据包 = holdout 场景 + rubric + 校准集引用。由 architect 持有、verifier 执行。"""

    bundle_id: str
    spec_id: str
    spec_version: str
    scenarios: list[HoldoutScenario] = Field(default_factory=list)
    rubrics: list[JudgeRubric] = Field(default_factory=list)
    calibration_items: list[CalibrationItem] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @model_validator(mode="after")
    def _unique_scenario_ids(self) -> "OracleBundle":
        ids = [s.scenario_id for s in self.scenarios]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate scenario_id")
        return self

    def scenarios_for_clause(self, clause_id: str) -> list[HoldoutScenario]:
        return [s for s in self.scenarios if clause_id in s.spec_clause_ids]


class JudgeVerdict(BaseModel):
    """judge 只输出『否决+理由』或『不否决』；永不输出『豁免硬门禁』。"""

    verdict: Literal["veto", "no_veto", "abstain"]
    reasons: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    samples: int = 1
    agreement_ratio: float = 1.0

    @model_validator(mode="after")
    def _evidence_policy(self) -> "JudgeVerdict":
        if self.verdict == "veto" and not self.reasons:
            raise ValueError("veto requires reasons")
        return self
