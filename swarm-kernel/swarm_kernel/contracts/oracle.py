from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import Field, field_validator

from .base import Confidentiality, ContractModel, RLevel, new_id, utc_now_iso
from .gates import GateSuiteResult


class ScenarioGrading(str, Enum):
    FAIL_TO_PASS = "FAIL_TO_PASS"
    PASS_TO_PASS = "PASS_TO_PASS"


class HoldoutScenario(ContractModel):
    contract_name: str = "HoldoutScenario"
    scenario_id: str
    title: str = ""
    inputs: dict[str, Any] = Field(default_factory=dict)
    expectation: dict[str, Any] = Field(default_factory=dict)
    grading: ScenarioGrading = ScenarioGrading.FAIL_TO_PASS
    r_binding: RLevel = RLevel.R0
    confidentiality: Confidentiality = Confidentiality.HOLDOUT
    tags: list[str] = Field(default_factory=list)


class ScenarioOutcome(ContractModel):
    contract_name: str = "ScenarioOutcome"
    scenario_id: str
    grading: ScenarioGrading
    passed: bool
    first_attempt: bool = True
    actual: Optional[Any] = None
    message: str = ""
    duration_ms: int = 0


class RubricItem(ContractModel):
    contract_name: str = "RubricItem"
    item_id: str
    criterion: str
    weight: float = 1.0
    evidence_required: bool = True


class BiasControls(ContractModel):
    contract_name: str = "BiasControls"
    position_swap: bool = True
    anonymize: bool = True
    samples: int = 3
    abstain_on_disagreement: bool = True
    min_calibration_kappa: float = 0.6


class Rubric(ContractModel):
    contract_name: str = "Rubric"
    rubric_id: str
    items: list[RubricItem] = Field(default_factory=list)
    bias: BiasControls = Field(default_factory=BiasControls)
    calibration_set_ref: str = ""
    confidentiality: Confidentiality = Confidentiality.JUDGE_INTERNAL


class JudgeVerdictKind(str, Enum):
    VETO = "veto"
    NO_VETO = "no_veto"
    ABSTAIN = "abstain"


class EvidenceCitation(ContractModel):
    contract_name: str = "EvidenceCitation"
    locator: str
    quote: str = ""


class JudgeVerdict(ContractModel):
    contract_name: str = "JudgeVerdict"
    verdict_id: str = Field(default_factory=lambda: new_id("jv"))
    rubric_id: str
    instance_id: str
    kind: JudgeVerdictKind
    reasons: list[str] = Field(default_factory=list)
    citations: list[EvidenceCitation] = Field(default_factory=list)
    samples_used: int = 0
    ts: str = Field(default_factory=utc_now_iso)

    @field_validator("kind")
    @classmethod
    def no_exemption(cls, v: JudgeVerdictKind) -> JudgeVerdictKind:
        return v

    @property
    def vetoes(self) -> bool:
        return self.kind == JudgeVerdictKind.VETO
