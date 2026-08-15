from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import ClassVar, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from swarmdev.contracts.oracle import JudgeVerdict
from swarmdev.contracts.r_level import RLevel


class GateStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"
    INCONCLUSIVE = "inconclusive"
    SKIPPED = "skipped"


class GateOutcome(BaseModel):
    gate_id: str  # H1..H8
    status: GateStatus
    evidence_refs: list[str] = Field(default_factory=list)
    details: str = ""
    duration_s: float = 0.0

    @property
    def passed(self) -> bool:
        return self.status == GateStatus.PASS


class SoftVerdict(BaseModel):
    rubric_id: str
    judge: JudgeVerdict


class DiscardedInstance(BaseModel):
    instance_id: str
    measurement_conclusion: str = Field(
        description="被丢弃实例仍须留下其测量结论（宪法不变量 2）"
    )


class EvidenceReceipt(BaseModel):
    """PR = 准入事务 + 证据收据（PDR-001 §9）。"""

    receipt_id: str
    wave_id: str
    spec_id: str
    spec_delta_ref: str
    r_level: RLevel
    chosen_instance_id: str
    discarded_instances: list[DiscardedInstance] = Field(default_factory=list)
    hard_gate_outcomes: list[GateOutcome] = Field(default_factory=list)
    soft_verdicts: list[SoftVerdict] = Field(default_factory=list)
    differential_conclusion: str = ""
    drift_check_passed: bool = False
    admitted: bool = False
    commit_ref: Optional[str] = Field(default=None, description="准入提交点（原子性）")
    rollback_ref: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    REQUIRED_GATES: ClassVar[tuple[str, ...]] = ("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8")

    @property
    def hard_pass(self) -> bool:
        return all(o.passed for o in self.hard_gate_outcomes)

    @property
    def soft_pass(self) -> bool:
        # 软门禁是单调否决器：任一 veto 即不过；abstain 不放行也不阻断（转人工）
        return all(sv.judge.verdict != "veto" for sv in self.soft_verdicts)

    @model_validator(mode="after")
    def _admission_algebra(self) -> "EvidenceReceipt":
        # Admit = H ∧ S；硬门禁不过，软门禁通过无效（宪法不变量 4）
        if self.admitted:
            if not self.hard_pass:
                raise ValueError("admitted=True but hard gates failed")
            if not self.soft_pass:
                raise ValueError("admitted=True but soft verdict contains veto")
            gates_seen = {o.gate_id for o in self.hard_gate_outcomes}
            missing = [g for g in self.REQUIRED_GATES if g not in gates_seen]
            if missing:
                raise ValueError(f"receipt missing hard gate outcomes: {missing}")
        return self
