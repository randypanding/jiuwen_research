"""R 级注册表：可再生性分级与允许操作（structure.md §5）。

R 级由 spec 声明（registry 文件），不由 agent 自行判断——
保证"存在例外"本身仍在单一真值内。
"""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RLevel(str, Enum):
    R0 = "R0"  # 一次性实例：可 fan-out 再生、整体丢弃
    R1 = "R1"  # 锚定制品：可再生，须先派生 spec-delta，再生后过契约兼容门 H4
    R2 = "R2"  # 契约制品：只能演进不能重写；破坏性变更须显式版本化
    R3 = "R3"  # 冻结制品：禁 fan-out/丢弃；仅前向追加；黄金输出锁定


#: 每个 R 级允许的操作集合（准入相变约束的机械投影）
ALLOWED_OPERATIONS: dict[RLevel, frozenset[str]] = {
    RLevel.R0: frozenset({"fanout", "discard", "regenerate", "refactor"}),
    RLevel.R1: frozenset({"regenerate_with_contract_gate", "evolve", "refactor"}),
    RLevel.R2: frozenset({"evolve", "version_bump"}),
    RLevel.R3: frozenset({"append_only", "golden_update_with_approval"}),
}

#: 门禁要求矩阵：准入该 R 级制品时必须启用的硬门禁（H 代号）
REQUIRED_GATES: dict[RLevel, frozenset[str]] = {
    RLevel.R0: frozenset({"H1", "H2", "H3", "H6"}),
    RLevel.R1: frozenset({"H1", "H2", "H3", "H4", "H6", "H7"}),
    RLevel.R2: frozenset({"H1", "H2", "H3", "H4", "H6", "H7"}),
    RLevel.R3: frozenset({"H1", "H2", "H4", "H5", "H6", "H7"}),
}


class OperationError(Exception):
    """对某 R 级制品执行了不允许的操作（INV11 的机械执行）。"""

    def __init__(self, path: str, r_level: RLevel, op: str):
        self.path = path
        self.r_level = r_level
        self.op = op
        super().__init__(
            f"operation '{op}' not allowed on {r_level.value} artifact '{path}'; "
            f"allowed={sorted(ALLOWED_OPERATIONS[r_level])}"
        )


@dataclass
class ArtifactRule:
    pattern: str          # 相对 world 仓库根的 glob 路径模式
    r_level: RLevel
    golden_locked: bool = False   # R3 逐行敏感制品（加密/金额/并发原语）
    rationale: str = ""

    def matches(self, path: str) -> bool:
        return fnmatch.fnmatch(path, self.pattern)


@dataclass
class RRegistry:
    """R 级注册表。首条命中规则生效；未命中默认 R0（可丢弃）。"""
    rules: list[ArtifactRule] = field(default_factory=list)

    def classify(self, path: str) -> RLevel:
        for rule in self.rules:
            if rule.matches(path):
                return rule.r_level
        return RLevel.R0

    def rule_for(self, path: str) -> Optional[ArtifactRule]:
        for rule in self.rules:
            if rule.matches(path):
                return rule
        return None

    def check_operation(self, path: str, op: str) -> None:
        """操作合法性检查：fan-out/丢弃前必须调用（INV11）。"""
        lvl = self.classify(path)
        if op not in ALLOWED_OPERATIONS[lvl]:
            raise OperationError(path, lvl, op)

    def required_gates(self, paths: list[str]) -> frozenset[str]:
        """一批涉及制品的并集门禁要求。"""
        need: set[str] = set()
        for p in paths:
            need |= REQUIRED_GATES[self.classify(p)]
        return frozenset(need)

    def to_dict(self) -> dict:
        return {
            "rules": [
                {
                    "pattern": r.pattern,
                    "r_level": r.r_level.value,
                    "golden_locked": r.golden_locked,
                    "rationale": r.rationale,
                }
                for r in self.rules
            ]
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RRegistry":
        return cls(
            rules=[
                ArtifactRule(
                    pattern=r["pattern"],
                    r_level=RLevel(r["r_level"]),
                    golden_locked=r.get("golden_locked", False),
                    rationale=r.get("rationale", ""),
                )
                for r in d.get("rules", [])
            ]
        )
