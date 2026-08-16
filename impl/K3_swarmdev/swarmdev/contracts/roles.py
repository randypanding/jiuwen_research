from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet


class Role(str, Enum):
    HUMAN = "human"
    LEADER = "leader"
    ARCHITECT = "architect"
    BUILDER = "builder"
    VERIFIER = "verifier"
    JUDGE = "judge"
    SPEC_MODERATOR = "spec_moderator"
    SPEC_STEWARD = "spec_steward"
    RECONCILER = "reconciler"
    CARTOGRAPHER = "cartographer"
    CRITIC = "critic"
    REFACTOR = "refactor"
    MODERATOR = "moderator"
    DEEP_AGENT = "deep_agent"


_SPEC_READERS = {
    Role.HUMAN, Role.LEADER, Role.ARCHITECT, Role.BUILDER, Role.VERIFIER,
    Role.SPEC_MODERATOR, Role.SPEC_STEWARD, Role.RECONCILER, Role.CRITIC,
    Role.REFACTOR, Role.MODERATOR, Role.DEEP_AGENT,
}

# PDR-001 §7 信息不对称纪律的可执行投影。
# 每条权限的授权集合即宪法级不变量，任何实现不得放宽。
CAPABILITY_MATRIX: dict[str, FrozenSet[Role]] = {
    "spec.l1.write": frozenset({Role.HUMAN}),
    "spec.l2.write": frozenset({Role.HUMAN, Role.ARCHITECT, Role.SPEC_MODERATOR, Role.SPEC_STEWARD}),
    "spec.l3.write": frozenset({Role.ARCHITECT, Role.BUILDER, Role.REFACTOR}),
    "spec.read": frozenset(_SPEC_READERS),
    # holdout 场景对 builder / leader 不可见（消除 reward hacking 的信息前提）
    "holdout.read": frozenset({Role.ARCHITECT, Role.VERIFIER, Role.JUDGE, Role.CRITIC, Role.HUMAN}),
    "holdout.write": frozenset({Role.ARCHITECT, Role.CRITIC, Role.HUMAN}),
    "oracle.write": frozenset({Role.ARCHITECT, Role.CRITIC, Role.HUMAN}),
    # 生成者不得参与判别
    "judge.execute": frozenset({Role.JUDGE, Role.VERIFIER}),
    "judge.verdict.write": frozenset({Role.JUDGE}),
    "gate.execute": frozenset({Role.VERIFIER}),
    # 临时 builder 不写任何长期记忆；实现细节入团队记忆须判别侧裁定
    "memory.write": frozenset({Role.SPEC_MODERATOR, Role.LEADER, Role.HUMAN}),
    "admission.decide": frozenset({Role.LEADER, Role.VERIFIER}),
    "admission.rollback": frozenset({Role.LEADER, Role.RECONCILER}),
    "wave.plan": frozenset({Role.ARCHITECT}),
    "instance.build": frozenset({Role.BUILDER}),
    "instance.discard": frozenset({Role.LEADER, Role.VERIFIER}),
    "drift.report": frozenset({Role.RECONCILER}),
    "rule.proposal": frozenset({Role.DEEP_AGENT, Role.HUMAN}),
    "rule.approve": frozenset({Role.HUMAN}),
}


class CapabilityError(PermissionError):
    def __init__(self, role: "Role", perm: str):
        super().__init__(f"role '{role.value}' lacks capability '{perm}'")
        self.role = role
        self.perm = perm


@dataclass(frozen=True)
class CapabilityToken:
    role: Role
    subject_id: str
    session_id: str
    extra_perms: FrozenSet[str] = field(default_factory=frozenset)

    def has(self, perm: str) -> bool:
        allowed = CAPABILITY_MATRIX.get(perm)
        if allowed is None:
            raise ValueError(f"unknown capability: {perm}")
        return self.role in allowed or perm in self.extra_perms

    def require(self, perm: str) -> None:
        if not self.has(perm):
            raise CapabilityError(self.role, perm)


def make_token(role: Role, subject_id: str, session_id: str) -> CapabilityToken:
    return CapabilityToken(role=role, subject_id=subject_id, session_id=session_id)
