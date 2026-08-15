from __future__ import annotations

import json
import math
from collections import Counter
from typing import Callable, Protocol

from swarmdev.contracts import JudgeRubric, JudgeVerdict


class JudgeModel(Protocol):
    def __call__(self, prompt: str) -> str: ...


_VALID_VERDICTS = ("veto", "no_veto", "abstain")


class JudgeWorkflow:
    def __init__(self, model: Callable[[str], str], samples: int = 3):
        self.model = model
        self.samples = samples

    def _build_prompt(self, rubric: JudgeRubric, artifact_summary: str, evidence: list[str]) -> str:
        lines = [
            "You are a strict verifier. Judge the artifact against the rubric.",
            f"Target: {rubric.target_description}",
            "Dimensions:",
        ]
        for dim in rubric.dimensions:
            lines.append(f"- {dim.dimension_id} (weight {dim.weight}): {dim.description}")
            for level in dim.levels:
                lines.append(f"  level {level.level} [{level.label}]: {level.observable_criteria}")
        if rubric.abstain_allowed:
            lines.append("Abstain is allowed when evidence is insufficient.")
        lines.append(f"Artifact summary: {artifact_summary}")
        lines.append("Evidence refs: " + json.dumps(list(evidence)))
        lines.append(
            'Respond ONLY with JSON: '
            '{"verdict": "veto"|"no_veto"|"abstain", "reasons": [...], "evidence_refs": [...]}'
        )
        return "\n".join(lines)

    def evaluate(
        self, rubric: JudgeRubric, artifact_summary: str, evidence: list[str]
    ) -> JudgeVerdict:
        prompt = self._build_prompt(rubric, artifact_summary, evidence)
        votes: list[str] = []
        parsed: list[dict] = []
        for _ in range(self.samples):
            try:
                payload = json.loads(self.model(prompt))
            except (json.JSONDecodeError, TypeError, ValueError):
                votes.append("abstain")
                continue
            if not isinstance(payload, dict) or payload.get("verdict") not in _VALID_VERDICTS:
                votes.append("abstain")
                continue
            votes.append(payload["verdict"])
            parsed.append(payload)
        counts = Counter(votes)
        majority_needed = math.ceil(self.samples / 2)
        agreement_ratio = counts.most_common(1)[0][1] / self.samples
        if counts.get("veto", 0) >= majority_needed:
            verdict = "veto"
        elif counts.get("no_veto", 0) >= majority_needed:
            verdict = "no_veto"
        else:
            verdict = "abstain"
        reasons: list[str] = []
        evidence_refs: list[str] = []
        for payload in parsed:
            if payload.get("verdict") == "veto":
                reasons.extend(str(r) for r in payload.get("reasons", []))
            evidence_refs.extend(str(ref) for ref in payload.get("evidence_refs", []))
        reasons = list(dict.fromkeys(reasons))
        evidence_refs = list(dict.fromkeys(evidence_refs))
        if verdict == "veto" and rubric.evidence_required and not evidence_refs:
            verdict = "abstain"
            reasons = reasons or ["veto downgraded to abstain: evidence required but missing"]
        if verdict == "veto" and not reasons:
            reasons = ["majority veto without explicit reasons"]
        return JudgeVerdict(
            verdict=verdict,
            reasons=reasons,
            evidence_refs=evidence_refs,
            samples=self.samples,
            agreement_ratio=agreement_ratio,
        )

    def compare_pairwise(self, a_summary: str, b_summary: str) -> dict:
        def ask(first: str, second: str) -> str | None:
            prompt = "\n".join(
                [
                    "Compare two artifacts and pick the better one.",
                    f"FIRST: {first}",
                    f"SECOND: {second}",
                    'Respond ONLY with JSON: {"winner": "first"|"second"}',
                ]
            )
            try:
                payload = json.loads(self.model(prompt))
            except (json.JSONDecodeError, TypeError, ValueError):
                return None
            if not isinstance(payload, dict):
                return None
            winner = payload.get("winner")
            return winner if winner in ("first", "second") else None

        first_pick = ask(a_summary, b_summary)
        second_pick = ask(b_summary, a_summary)
        if first_pick is None or second_pick is None:
            return {"winner": None, "reason": "unparseable_response"}
        candidate_from_round_one = "A" if first_pick == "first" else "B"
        candidate_from_round_two = "B" if second_pick == "first" else "A"
        if candidate_from_round_one == candidate_from_round_two:
            return {"winner": candidate_from_round_one}
        return {"winner": None, "reason": "position_inconsistency"}
