from __future__ import annotations

import re
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

_SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
_CLAUSE_ID = re.compile(r"^CL-[A-Z0-9][A-Z0-9_-]*$")


class ValidationState(str, Enum):
    DRAFT = "draft"
    PARSED = "parsed"
    MODEL_CHECKED = "model_checked"
    HUMAN_CONFIRMED = "human_confirmed"


class WitnessKind(str, Enum):
    HARD_GATE = "hard_gate"
    HOLDOUT_SCENARIO = "holdout_scenario"
    GOLDEN_OUTPUT = "golden_output"
    DIFFERENTIAL = "differential"


class WitnessRef(BaseModel):
    kind: WitnessKind
    ref_id: str
    gate_id: Optional[str] = None


class DontCareEntry(BaseModel):
    """spec 必须能表达『未定义即自由』(PDR-001 §6)。"""

    entry_id: str
    clause_id: str
    description: str
    precondition_domain: str = Field(description="该自由度适用的前置域描述")
    out_of_domain_behavior: Literal["arbitrary", "blocking"] = Field(
        description="前置域外的行为必须二选一写明：任意结果 or 阻塞"
    )


class L2Clause(BaseModel):
    """L2 开发契约条款：assume/guarantee/invariant 结构 + 见证绑定义务。"""

    clause_id: str
    title: str
    assumes: list[str] = Field(default_factory=list)
    guarantees: list[str] = Field(default_factory=list)
    invariants: list[str] = Field(default_factory=list)
    witnesses: list[WitnessRef] = Field(default_factory=list)
    validation_state: ValidationState = ValidationState.DRAFT
    r_level_declared: Optional[str] = None

    @field_validator("clause_id")
    @classmethod
    def _check_clause_id(cls, v: str) -> str:
        if not _CLAUSE_ID.match(v):
            raise ValueError(f"clause_id must match {_CLAUSE_ID.pattern}: {v}")
        return v

    @property
    def is_verifiable(self) -> bool:
        # PDR-001 §8：每条 L2 条款必须绑定 ≥1 个硬见证或 holdout 场景，
        # 否则标记 unverifiable，只能作为 advisory，不得作为放行依据。
        return len(self.witnesses) > 0


class SpecDoc(BaseModel):
    """规范三层载体（PDR-001 §9）。L1/L2 同文档、L3 链接外部文件。"""

    spec_id: str
    domain: str
    version: str
    l1_intent: str = Field(description="L1 业务意图：为什么、给谁、成功是什么")
    l1_approved_by: Optional[str] = None
    l2_clauses: list[L2Clause] = Field(default_factory=list)
    l3_links: list[str] = Field(default_factory=list, description="L3 实现说明文件链接")
    dont_care: list[DontCareEntry] = Field(default_factory=list)

    @field_validator("version")
    @classmethod
    def _check_semver(cls, v: str) -> str:
        if not _SEMVER.match(v):
            raise ValueError(f"version must be semver x.y.z: {v}")
        return v

    @model_validator(mode="after")
    def _check_dont_care_refs(self) -> "SpecDoc":
        clause_ids = {c.clause_id for c in self.l2_clauses}
        for dc in self.dont_care:
            if dc.clause_id not in clause_ids:
                raise ValueError(f"dont_care {dc.entry_id} references unknown clause {dc.clause_id}")
        ids = [c.clause_id for c in self.l2_clauses]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate clause_id in l2_clauses")
        return self

    def clause(self, clause_id: str) -> L2Clause:
        for c in self.l2_clauses:
            if c.clause_id == clause_id:
                return c
        raise KeyError(clause_id)

    def unverifiable_clauses(self) -> list[L2Clause]:
        return [c for c in self.l2_clauses if not c.is_verifiable]

    def witness_coverage(self) -> float:
        if not self.l2_clauses:
            return 1.0
        return sum(1 for c in self.l2_clauses if c.is_verifiable) / len(self.l2_clauses)
