from __future__ import annotations

from typing import Protocol

from swarm_kernel.contracts.oracle import (
    BiasControls,
    EvidenceCitation,
    JudgeVerdict,
    JudgeVerdictKind,
    Rubric,
)


class JudgeBackend(Protocol):
    def sample(self, rubric: Rubric, sanitized_submission: dict, sample_index: int) -> dict:
        ...


class JudgeWorkflow:
    def __init__(self, backend: JudgeBackend) -> None:
        self.backend = backend

    def _sanitize(self, submission: dict, anonymize: bool) -> dict:
        if not anonymize:
            return dict(submission)
        clean = dict(submission)
        clean.pop("builder_identity", None)
        clean.pop("chain_of_thought", None)
        clean.pop("timestamps", None)
        return clean

    def run(self, rubric: Rubric, submission: dict, instance_id: str) -> JudgeVerdict:
        bias: BiasControls = rubric.bias
        payload = self._sanitize(submission, bias.anonymize)
        samples: list[dict] = []
        k = max(1, bias.samples)
        for i in range(k):
            out = self.backend.sample(rubric, payload, i)
            if bias.position_swap:
                out_swap = self.backend.sample(rubric, payload, i + 1000)
                if out.get("kind") != out_swap.get("kind"):
                    out = {"kind": "abstain", "reasons": ["position-swap inconsistency"], "citations": []}
            samples.append(out)
        kinds = [s.get("kind", "abstain") for s in samples]
        veto_votes = sum(1 for x in kinds if x == "veto")
        no_veto_votes = sum(1 for x in kinds if x == "no_veto")
        if bias.abstain_on_disagreement and veto_votes > 0 and no_veto_votes > 0:
            kind = JudgeVerdictKind.ABSTAIN
        elif veto_votes > no_veto_votes:
            kind = JudgeVerdictKind.VETO
        elif no_veto_votes > veto_votes:
            kind = JudgeVerdictKind.NO_VETO
        else:
            kind = JudgeVerdictKind.ABSTAIN
        reasons: list[str] = []
        citations: list[EvidenceCitation] = []
        for s in samples:
            if s.get("kind") == "veto":
                reasons.extend(str(r) for r in s.get("reasons", []))
                citations.extend(EvidenceCitation(locator=c.get("locator", ""), quote=c.get("quote", "")) for c in s.get("citations", []))
        if kind == JudgeVerdictKind.VETO and not citations:
            kind = JudgeVerdictKind.ABSTAIN
            reasons.append("veto without evidence citations downgraded to abstain")
        return JudgeVerdict(
            rubric_id=rubric.rubric_id,
            instance_id=instance_id,
            kind=kind,
            reasons=sorted(set(reasons)),
            citations=citations,
            samples_used=k,
        )


class ScriptedJudgeBackend:
    def __init__(self, scripted: list[dict]) -> None:
        self.scripted = scripted

    def sample(self, rubric: Rubric, sanitized_submission: dict, sample_index: int) -> dict:
        if not self.scripted:
            return {"kind": "no_veto", "reasons": [], "citations": []}
        return self.scripted[sample_index % len(self.scripted)]
