from __future__ import annotations

from enum import IntEnum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class RLevel(IntEnum):
    """可再生性分级（PDR-001 §5）。R 级由 spec 声明，不由 agent 自行判断。"""

    R0 = 0  # 一次性实例：可 fan-out 再生、整体丢弃
    R1 = 1  # 锚定制品：可再生但须 spec-delta + 契约兼容门
    R2 = 2  # 契约制品：只演进不重写，破坏性变更须显式版本化 + 人类批准
    R3 = 3  # 冻结制品：禁止 fan-out 与丢弃，仅前向追加 + 黄金输出锁定


class RArtifact(BaseModel):
    artifact_id: str
    path_pattern: str
    level: RLevel
    declared_by_spec: str
    notes: str = ""

    @model_validator(mode="after")
    def _frozen_needs_golden(self) -> "RArtifact":
        return self


class RRegistry(BaseModel):
    artifacts: list[RArtifact] = Field(default_factory=list)

    def register(self, artifact: RArtifact) -> None:
        for a in self.artifacts:
            if a.artifact_id == artifact.artifact_id:
                raise ValueError(f"artifact already registered: {artifact.artifact_id}")
        self.artifacts.append(artifact)

    def get(self, artifact_id: str) -> Optional[RArtifact]:
        for a in self.artifacts:
            if a.artifact_id == artifact_id:
                return a
        return None

    def level_of(self, artifact_id: str) -> RLevel:
        a = self.get(artifact_id)
        if a is None:
            # 未登记制品默认 R0（可丢弃），与『实例默认一次性』一致
            return RLevel.R0
        return a.level

    @staticmethod
    def fanout_allowed(level: RLevel) -> bool:
        # R3 禁止 fan-out 与丢弃（宪法不变量 11）
        return level < RLevel.R3

    @staticmethod
    def discard_allowed(level: RLevel) -> bool:
        return level <= RLevel.R1

    @staticmethod
    def requires_human_approval(level: RLevel) -> bool:
        return level >= RLevel.R2
