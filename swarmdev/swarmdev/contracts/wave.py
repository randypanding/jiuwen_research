from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

from swarmdev.contracts.r_level import RLevel


class WaveState(str, Enum):
    PLANNED = "planned"
    COLLECTING = "collecting"      # fan-out 生成中
    ADJUDICATING = "adjudicating"  # 门禁与测量判别中
    COMMITTING = "committing"      # 准入事务提交中
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"


class FanoutPolicy(BaseModel):
    n_target: int = Field(default=1, ge=1, le=8, description="N 自适应，硬顶 8")
    uncertainty_signals: dict[str, float] = Field(
        default_factory=dict,
        description="触发 fan-out 的不确定度信号：rework_rate/domain_novelty/r_level_risk",
    )


class WaveTask(BaseModel):
    """再生单元（RU）任务。粒度由 architect 裁定。"""

    ru_id: str
    spec_delta_ref: str
    artifact_ids: list[str] = Field(default_factory=list)
    r_level: RLevel = RLevel.R0
    fanout: FanoutPolicy = Field(default_factory=FanoutPolicy)
    interface_freeze_ref: Optional[str] = None

    @model_validator(mode="after")
    def _r3_no_fanout(self) -> "WaveTask":
        # R3 禁止 fan-out（宪法不变量 11）
        if self.r_level >= RLevel.R3 and self.fanout.n_target > 1:
            raise ValueError("R3 artifacts forbid fan-out (n_target must be 1)")
        return self


class Wave(BaseModel):
    """波次 = 接口冻结窗口 + 独立可验证的 spec-delta 割集 + 准入事务边界。"""

    wave_id: str
    epoch: int = 1
    spec_delta_ids: list[str]
    tasks: list[WaveTask] = Field(default_factory=list)
    state: WaveState = WaveState.PLANNED

    def transition(self, new_state: WaveState) -> None:
        order = [
            WaveState.PLANNED, WaveState.COLLECTING, WaveState.ADJUDICATING,
            WaveState.COMMITTING, WaveState.COMMITTED,
        ]
        if new_state == WaveState.ROLLED_BACK:
            if self.state in (WaveState.COMMITTED,):
                raise ValueError("committed wave cannot roll back; use forward fix")
            self.state = new_state
            return
        if self.state not in order or new_state not in order:
            raise ValueError(f"invalid transition {self.state} -> {new_state}")
        if order.index(new_state) != order.index(self.state) + 1:
            raise ValueError(f"non-sequential transition {self.state} -> {new_state}")
        self.state = new_state


class AdmitDecision(BaseModel):
    decision: Literal["admit", "reject", "inconclusive"]
    reasons: list[str] = Field(default_factory=list)
    chosen_instance_id: Optional[str] = None
