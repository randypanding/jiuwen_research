from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, model_validator

from swarmdev.contracts import Role


class ModelTier(str, Enum):
    L = "L"
    M = "M"
    H = "H"

    @property
    def rank(self) -> int:
        return {"L": 0, "M": 1, "H": 2}[self.value]


class TierPolicyError(ValueError):
    pass


class TierAssignment(BaseModel):
    """模型档位分配。宪法不变量 14：判别方档位不得低于生成方。"""

    builder: ModelTier = ModelTier.M
    judge: ModelTier = ModelTier.M
    verifier: ModelTier = ModelTier.M
    spec_moderator: ModelTier = ModelTier.M
    leader: ModelTier = ModelTier.M
    architect: ModelTier = ModelTier.H
    cartographer: ModelTier = ModelTier.L

    @model_validator(mode="after")
    def _judge_not_weaker(self) -> "TierAssignment":
        if self.judge.rank < self.builder.rank:
            raise TierPolicyError(
                f"judge tier {self.judge.value} weaker than builder tier {self.builder.value}"
            )
        if self.verifier.rank < self.builder.rank:
            raise TierPolicyError("verifier tier weaker than builder tier")
        return self


ROLE_DEFAULTS: dict[Role, ModelTier] = {
    Role.BUILDER: ModelTier.M,
    Role.JUDGE: ModelTier.M,
    Role.CARTOGRAPHER: ModelTier.L,
    Role.ARCHITECT: ModelTier.H,
}
