from __future__ import annotations

import dataclasses

from swarmfoundry.schema import SCHEMA_VERSION
from swarmfoundry.schema.base import (
    SchemaError,
    check_id,
    check_schema_version,
    require,
    require_list,
)

VERDICT_VETO = "veto"
VERDICT_NO_VETO = "no_veto"
VERDICT_ABSTAIN = "abstain"
JUDGE_VERDICTS = (VERDICT_VETO, VERDICT_NO_VETO, VERDICT_ABSTAIN)


@dataclasses.dataclass(frozen=True)
class JudgeVerdict:
    judge_id: str
    model_family: str
    verdict: str
    reasons: str
    evidence_refs: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "judge_id": self.judge_id,
            "model_family": self.model_family,
            "verdict": self.verdict,
            "reasons": self.reasons,
            "evidence_refs": list(self.evidence_refs),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "JudgeVerdict":
        where = "JudgeVerdict"
        check_schema_version(data, where)
        verdict = require(data, "verdict", str, where)
        if verdict not in JUDGE_VERDICTS:
            raise SchemaError(f"{where}: verdict must be one of {JUDGE_VERDICTS}")
        return cls(
            judge_id=check_id(require(data, "judge_id", str, where), where),
            model_family=require(data, "model_family", str, where),
            verdict=verdict,
            reasons=require(data, "reasons", str, where),
            evidence_refs=tuple(require_list(data, "evidence_refs", where)),
        )


class JudgePanelError(SchemaError):
    pass


@dataclasses.dataclass(frozen=True)
class PanelDecision:
    vetoed: bool
    counted: int
    abstained: int
    invalidated: int
    reasons: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "vetoed": self.vetoed,
            "counted": self.counted,
            "abstained": self.abstained,
            "invalidated": self.invalidated,
            "reasons": list(self.reasons),
        }


def aggregate_panel(
    verdicts: list[JudgeVerdict],
    builder_model_family: str,
    min_valid: int = 2,
) -> PanelDecision:
    """Soft gate aggregation. Judges output veto/no_veto/abstain only; a judge can
    never rescue a hard-gate failure. Self-review (judge model family == builder
    model family) invalidates the verdict. Fewer than `min_valid` valid verdicts
    fails closed (vetoed)."""
    counted = 0
    abstained = 0
    invalidated = 0
    vetoed = False
    reasons: list[str] = []
    seen_judges: set[str] = set()
    for v in verdicts:
        if v.judge_id in seen_judges:
            invalidated += 1
            reasons.append(f"duplicate judge {v.judge_id} invalidated")
            continue
        seen_judges.add(v.judge_id)
        if v.model_family == builder_model_family:
            invalidated += 1
            reasons.append(f"judge {v.judge_id} shares builder model family '{builder_model_family}': self-review forbidden")
            continue
        if v.verdict == VERDICT_ABSTAIN:
            abstained += 1
            reasons.append(f"judge {v.judge_id} abstained")
            continue
        counted += 1
        if v.verdict == VERDICT_VETO:
            vetoed = True
            reasons.append(f"judge {v.judge_id} vetoed: {v.reasons}")
    if counted < min_valid:
        vetoed = True
        reasons.append(f"fail-closed: only {counted} valid verdicts < required {min_valid}")
    return PanelDecision(
        vetoed=vetoed,
        counted=counted,
        abstained=abstained,
        invalidated=invalidated,
        reasons=tuple(reasons),
    )
