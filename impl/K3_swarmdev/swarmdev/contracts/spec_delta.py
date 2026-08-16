from __future__ import annotations

import re
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator

_SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class DeltaOp(str, Enum):
    ADD = "add"
    REMOVE = "remove"
    MODIFY = "modify"
    DEPRECATE = "deprecate"


class TargetKind(str, Enum):
    CLAUSE = "clause"
    ASSUME = "assume"
    GUARANTEE = "guarantee"
    INVARIANT = "invariant"
    DONT_CARE = "dont_care"
    INTERFACE = "interface"
    WITNESS = "witness"


class Compatibility(str, Enum):
    BC = "bc"    # 向后兼容
    NBC = "nbc"  # 破坏兼容


class DeltaEntry(BaseModel):
    entry_id: str
    op: DeltaOp
    target_kind: TargetKind
    target_id: str
    compatibility: Compatibility
    detail: str = ""
    requires_human_approval: bool = False


def _parse(v: str) -> tuple[int, int, int]:
    m = _SEMVER.match(v)
    if not m:
        raise ValueError(f"not semver: {v}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


class SpecDelta(BaseModel):
    """结构化 spec diff（非文本 diff）。破坏性变更分类 + SemVer 强制校验。"""

    delta_id: str
    spec_id: str
    from_version: str
    to_version: str
    entries: list[DeltaEntry] = Field(default_factory=list)
    approved_by: Optional[str] = None

    @property
    def is_breaking(self) -> bool:
        return any(e.compatibility == Compatibility.NBC for e in self.entries)

    @model_validator(mode="after")
    def _check_version_move(self) -> "SpecDelta":
        f = _parse(self.from_version)
        t = _parse(self.to_version)
        if t <= f:
            raise ValueError("to_version must be greater than from_version")
        if self.is_breaking:
            # NBC 必须升 major
            if t[0] <= f[0]:
                raise ValueError(
                    f"breaking delta requires major bump: {self.from_version} -> {self.to_version}"
                )
            if not any(e.requires_human_approval for e in self.entries if e.compatibility == Compatibility.NBC):
                raise ValueError("NBC entries must require human approval")
        elif t[0] > f[0]:
            raise ValueError("non-breaking delta must not bump major version")
        return self
