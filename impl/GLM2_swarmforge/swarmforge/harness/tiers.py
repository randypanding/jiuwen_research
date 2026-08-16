"""模型档位表：RU-L / RU-M / RU-H 三档 + 角色档位地板。

INV14：判别方档位不得低于生成方 —— validate_tier_config 机械校验。
落地到 openjiuwen：TeamAgentSpec.model_pool（round_robin/by_model_name/router/
intelli_router 四策略），roles.build_model_pool() 生成配置片段。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..constitution import ConstitutionViolation


class ModelTier(str, Enum):
    RU_L = "RU-L"   # 低档：cartographer、摘要、机械分类
    RU_M = "RU-M"   # 中档：builder 默认档
    RU_H = "RU-H"   # 高档：architect、judge、升级后的 builder


TIER_ORDER = {ModelTier.RU_L: 0, ModelTier.RU_M: 1, ModelTier.RU_H: 2}


def tier_at_least(a: ModelTier, b: ModelTier) -> bool:
    return TIER_ORDER[a] >= TIER_ORDER[b]


#: 角色档位地板（generation/judgement 分列）
ROLE_TIER_FLOOR: dict[str, dict[str, ModelTier]] = {
    # role: {"generation": ..., "judgement": ...}（无该职能则省略）
    "leader": {"generation": ModelTier.RU_M},
    "architect": {"generation": ModelTier.RU_H},
    "builder": {"generation": ModelTier.RU_M},
    "verifier": {"judgement": ModelTier.RU_H},
    "spec_moderator": {"judgement": ModelTier.RU_H},
    "spec_steward": {"judgement": ModelTier.RU_H},
    "reconciler": {"generation": ModelTier.RU_M, "judgement": ModelTier.RU_M},
    "cartographer": {"generation": ModelTier.RU_L},
    "critic": {"generation": ModelTier.RU_H},
    "refactor": {"generation": ModelTier.RU_M},
    "moderator": {"generation": ModelTier.RU_L},
    "deep_agent": {"generation": ModelTier.RU_H},
    "calibration_leader": {"generation": ModelTier.RU_M},
    "judge": {"judgement": ModelTier.RU_H},
}


@dataclass
class TierAssignment:
    role: str
    builder_tier: ModelTier
    judge_tier: ModelTier


def validate_tier_assignment(assignment: TierAssignment) -> None:
    """INV14：judge 档位 >= builder 档位。"""
    if not tier_at_least(assignment.judge_tier, assignment.builder_tier):
        raise ConstitutionViolation(
            "INV14",
            f"judge tier {assignment.judge_tier.value} < builder tier "
            f"{assignment.builder_tier.value}",
        )


def role_floor(role: str, function: str) -> ModelTier:
    entry = ROLE_TIER_FLOOR.get(role, {})
    return entry.get(function, ModelTier.RU_M)
