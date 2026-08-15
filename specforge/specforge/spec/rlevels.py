"""Renewability levels R0..R3 (PDR-001 section 5).

R levels are declared by spec, never judged by agents. The registry maps
artifact path patterns to levels; spec frontmatter `r_level` sets the unit
default for artifacts not listed.
"""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

LEVELS = ("R0", "R1", "R2", "R3")

SEMANTICS = {
    "R0": "一次性实例：fan-out 再生、整体丢弃、refactor 重写",
    "R1": "锚定制品：再生须先派生 spec-delta，再生后过契约兼容门",
    "R2": "契约制品：只能演进不能重写；破坏性变更须显式版本化+人工批准",
    "R3": "冻结制品：禁止 fan-out 与丢弃；仅前向追加；黄金输出锁定",
}


@dataclass
class RRegistry:
    """Path pattern -> R level, loaded from spec/registry.yaml or built inline."""

    rules: list[tuple[str, str]] = field(default_factory=list)  # (pattern, level)
    default: str = "R0"

    def __post_init__(self) -> None:
        if isinstance(self.rules, dict):  # accept mapping form
            self.rules = [(str(p), str(lv)) for p, lv in self.rules.items()]
        for _, lvl in self.rules:
            if lvl not in LEVELS:
                raise ValueError(f"r_level {lvl!r} invalid in registry")
        if self.default not in LEVELS:
            raise ValueError(f"default r_level {self.default!r} invalid")

    @classmethod
    def load(cls, path: str | Path) -> "RRegistry":
        import yaml

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        rules = [(str(p), str(lv)) for p, lv in (data.get("rules") or {}).items()]
        default = str(data.get("default", "R0"))
        return cls(rules=rules, default=default)

    def classify(self, artifact_path: str, unit_default: Optional[str] = None) -> str:
        for pattern, lvl in self.rules:
            if fnmatch.fnmatch(artifact_path, pattern):
                return lvl
        return unit_default or self.default

    def unit_level(self, spec_unit_r_level: str) -> str:
        if spec_unit_r_level not in LEVELS:
            raise ValueError(f"r_level {spec_unit_r_level!r} invalid")
        return spec_unit_r_level

    def fanout_allowed(self, level: str) -> bool:
        return level in ("R0", "R1")

    def requires_human(self, level: str) -> bool:
        return level in ("R2", "R3")
