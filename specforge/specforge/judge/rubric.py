"""Rubric: four-part prompt contract (llm-as-judge best practices).

1. task description + evaluation dimension (one dimension per rubric)
2. level-by-level discriminating descriptions
3. CoT-first then structured JSON verdict (reasons + evidence mandatory)
4. bias constraints declaration (length/style/self-preference warnings)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

BIAS_DECLARATION = (
    "Bias constraints: length is not quality; style is not substance; do not reward "
    "fluency over correctness; cite concrete evidence for every reason; abstain when "
    "evidence is insufficient rather than guess."
)


@dataclass
class RubricLevel:
    score: float
    description: str


@dataclass
class Rubric:
    rubric_id: str
    dimension: str
    task: str
    levels: list[RubricLevel] = field(default_factory=list)
    evidence_required: bool = True
    allow_abstain: bool = True
    bias_declaration: str = BIAS_DECLARATION
    pass_score: float = 0.7

    def to_dict(self) -> dict[str, Any]:
        return {
            "rubric_id": self.rubric_id, "dimension": self.dimension, "task": self.task,
            "levels": [{"score": lv.score, "description": lv.description} for lv in self.levels],
            "evidence_required": self.evidence_required, "allow_abstain": self.allow_abstain,
            "bias_declaration": self.bias_declaration, "pass_score": self.pass_score,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Rubric":
        levels = [RubricLevel(**lv) for lv in d.get("levels", [])]
        return cls(
            rubric_id=d["rubric_id"], dimension=d["dimension"], task=d["task"],
            levels=levels, evidence_required=d.get("evidence_required", True),
            allow_abstain=d.get("allow_abstain", True),
            bias_declaration=d.get("bias_declaration", BIAS_DECLARATION),
            pass_score=d.get("pass_score", 0.7),
        )

    def render_prompt(self, item: dict[str, Any]) -> str:
        lines = [f"# Task: {self.task}", f"# Dimension under evaluation: {self.dimension} (only this one)", ""]
        lines.append("# Rating scale:")
        for lv in sorted(self.levels, key=lambda x: -x.score):
            lines.append(f"  {lv.score}: {lv.description}")
        lines.append("")
        lines.append(f"# Subject under evaluation:\n{item.get('content', item)}")
        lines.append("")
        lines.append("# Output requirements: reason step by step first, then output JSON:")
        lines.append('  {"verdict": "pass|fail|abstain", "score": <float>, '
                     '"reasons": [<string>], "evidence": [<string>]}')
        lines.append(f"# {self.bias_declaration}")
        if self.evidence_required:
            lines.append("# Every reason MUST cite at least one piece of evidence, otherwise the verdict is invalid.")
        return "\n".join(lines)
