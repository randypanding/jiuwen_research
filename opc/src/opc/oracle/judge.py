from __future__ import annotations

from typing import Any, Protocol

from pydantic import Field

from opc.schemas.common import BaseSchema, Verdict
from opc.schemas.oracle import JudgeSample, JudgeVerdict


class RubricDimension(BaseSchema):
    name: str
    criteria: str
    weight: float = Field(default=1.0, gt=0)


class RubricConfig(BaseSchema):
    rubric_id: str
    dimensions: list[RubricDimension]
    judge_model: str
    samples_k: int = Field(default=3, ge=1, le=7)
    require_pairwise_swap: bool = True

    def render(self) -> str:
        lines = [f"rubric {self.rubric_id}:"]
        for d in self.dimensions:
            lines.append(f"- [{d.name}] (weight {d.weight}) {d.criteria}")
        lines.append("output ONLY: verdict in {reject, no_reject}; reasons; evidence quotes")
        return "\n".join(lines)


class RelayPackage(BaseSchema):
    """Minimal sufficient relay: the ONLY shape the judge ever sees.

    Per the information-asymmetry discipline, the judge receives atomic
    claims plus public evidence - never the builder's raw reasoning chain,
    hidden scenario bodies, or rubric-adjacent hints smuggled in artifacts.
    """

    instance_id: str
    claims: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    scenario_ids: list[str] = Field(default_factory=list)


class JudgeContext(BaseSchema):
    relay: RelayPackage
    rubric_text: str
    sample_index: int
    swapped: bool = False


class JudgeClient(Protocol):
    model_id: str

    def sample(self, context: JudgeContext) -> JudgeSample: ...


class ModelLineageRegistry:
    """Encodes the three model-relation checks (same model / descendant / same family)."""

    def __init__(self, families: dict[str, str], descendants: dict[str, str] | None = None):
        self.families = families
        self.descendants = descendants or {}

    def conflicts(self, generator_model: str, judge_model: str) -> list[str]:
        problems: list[str] = []
        if generator_model == judge_model:
            problems.append("judge is the same model as the generator")
        if self.descendants.get(judge_model) == generator_model or self.descendants.get(generator_model) == judge_model:
            problems.append("judge and generator are in a distillation/finetune lineage")
        fam_g = self.families.get(generator_model)
        fam_j = self.families.get(judge_model)
        if fam_g is not None and fam_g == fam_j:
            problems.append("judge and generator are from the same model family")
        return problems


class JudgeWorkflow:
    """Deterministic soft-gate orchestration around a pluggable judge client.

    Rules implemented (all veto-monotone):
      * k samples, majority reject wins; a split panel abstains (INCONCLUSIVE);
      * samples without evidence citations are discarded before voting;
      * pairwise presentation requires swap-order consistency, else abstain;
      * the judge model must clear the three model-relation checks;
      * the judge never emits 'exempt hard gates' - it only rejects or not.
    """

    def __init__(
        self,
        client: JudgeClient,
        lineage: ModelLineageRegistry | None = None,
        tier_table: dict[str, int] | None = None,
    ):
        self.client = client
        self.lineage = lineage or ModelLineageRegistry({}, {})
        self.tier_table = tier_table or {}

    def judge(
        self,
        relay: RelayPackage,
        rubric: RubricConfig,
        generator_model: str = "",
        builder_tier: str = "",
    ) -> JudgeVerdict:
        relation_problems = self.lineage.conflicts(generator_model, self.client.model_id)
        if relation_problems:
            return JudgeVerdict(
                verdict=Verdict.INCONCLUSIVE,
                abstained=True,
                rubric_id=rubric.rubric_id,
                judge_model=self.client.model_id,
                reasons=relation_problems,
            )
        judge_rank = self.tier_table.get(self.client.model_id, 0)
        builder_rank = self.tier_table.get(builder_tier or generator_model, 0)
        if judge_rank < builder_rank:
            return JudgeVerdict(
                verdict=Verdict.INCONCLUSIVE,
                abstained=True,
                rubric_id=rubric.rubric_id,
                judge_model=self.client.model_id,
                reasons=[f"judge tier {self.client.model_id} is weaker than builder tier; refusing to judge"],
            )

        context = JudgeContext(relay=relay, rubric_text=rubric.render(), sample_index=0)
        samples: list[JudgeSample] = []
        for i in range(rubric.samples_k):
            context.sample_index = i
            sample = self.client.sample(context)
            if not sample.evidence:
                continue
            samples.append(sample)

        swapped_consistent: bool | None = None
        if rubric.require_pairwise_swap:
            swapped_context = JudgeContext(
                relay=relay, rubric_text=rubric.render(), sample_index=0, swapped=True
            )
            swap_verdicts: list[str] = []
            for i in range(rubric.samples_k):
                swapped_context.sample_index = i
                swap_verdicts.append(self.client.sample(swapped_context).verdict)
            original_verdicts = [s.verdict for s in samples]
            swapped_consistent = sorted(swap_verdicts) == sorted(original_verdicts)

        return JudgeVerdict.from_samples(
            samples,
            rubric_id=rubric.rubric_id,
            judge_model=self.client.model_id,
            position_swapped_consistent=swapped_consistent,
        )


def build_relay(instance_report: dict[str, Any]) -> RelayPackage:
    return RelayPackage(
        instance_id=str(instance_report.get("instance_id", "")),
        claims=[str(c) for c in instance_report.get("claims", [])],
        evidence=[str(e) for e in instance_report.get("evidence", [])],
        scenario_ids=[str(s) for s in instance_report.get("scenario_ids", [])],
    )
