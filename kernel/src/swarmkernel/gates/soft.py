"""The soft gate: a monotone veto device.

Everything about this module exists to enforce one sentence from PDR-001 §5:
*the soft gate can only subtract, never add.* The type system already forbids a
PASS verdict (:class:`SoftVerdict` has no such member). This module adds the
operational rules that make the veto trustworthy:

* **Judge tier >= builder tier.** A weaker model may not overrule a stronger one.
* **A veto must cite.** An uncited veto is an opinion; opinions do not block.
* **No self-review.** A judge may not evaluate an instance it authored.
* **Position swap.** Comparative judging runs both orders; disagreement between
  the two orders is itself evidence of noise, not a verdict.
* **Abstention is legal.** Forcing a judge to choose manufactures signal that
  does not exist.
* **Agreement is measured, not assumed.** Cohen's kappa over repeated samples,
  with a floor; below the floor the judge is *unfit* and its output is discarded
  rather than trusted.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Mapping, Sequence

from ..contracts.gate import JudgeSample, SoftGateResult, SoftVerdict

__all__ = ["cohens_kappa", "SoftGateEngine", "JudgeFitness", "aggregate"]


def cohens_kappa(a: Sequence[str], b: Sequence[str]) -> float:
    """Cohen's kappa between two raters over the same items.

    Exact-match agreement rewards a judge that always answers the same thing;
    kappa corrects for chance and therefore punishes it.
    """

    if len(a) != len(b):
        raise ValueError("rating vectors must be the same length")
    n = len(a)
    if n == 0:
        return 0.0
    observed = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    categories = set(ca) | set(cb)
    expected = sum((ca[c] / n) * (cb[c] / n) for c in categories)
    if expected >= 1.0:
        # Both raters were constant and identical: agreement carries no
        # information, so kappa is undefined. Report 0, never 1.
        return 0.0
    return (observed - expected) / (1.0 - expected)


@dataclass(frozen=True)
class JudgeFitness:
    kappa: float
    threshold: float
    sample_count: int

    @property
    def fit(self) -> bool:
        return self.kappa >= self.threshold and self.sample_count >= 2

    @property
    def reason(self) -> str:
        if self.sample_count < 2:
            return "fewer than two independent sample rounds; agreement unmeasurable"
        if self.kappa < self.threshold:
            return f"kappa {self.kappa:.3f} < required {self.threshold:.2f}"
        return ""


def aggregate(samples: Sequence[JudgeSample], mode: str) -> SoftVerdict:
    """Aggregate judge samples into a verdict.

    ``any_veto`` is the default and the only mode that is safe for a
    single-sample configuration: one credible, cited veto blocks.
    ``majority_veto`` requires more than half the non-abstaining samples to veto.
    """

    considered = [s for s in samples if s.verdict is not SoftVerdict.ABSTAIN]
    vetoes = [s for s in considered if s.verdict is SoftVerdict.VETO]
    if not considered:
        return SoftVerdict.ABSTAIN
    if mode == "any_veto":
        return SoftVerdict.VETO if vetoes else SoftVerdict.NO_VETO
    if mode == "majority_veto":
        return (
            SoftVerdict.VETO
            if len(vetoes) * 2 > len(considered)
            else SoftVerdict.NO_VETO
        )
    if mode == "unanimous_veto":
        return (
            SoftVerdict.VETO
            if vetoes and len(vetoes) == len(considered)
            else SoftVerdict.NO_VETO
        )
    raise ValueError(f"unknown aggregation mode {mode!r}")


class SoftGateEngine:
    """Turns raw judge samples into a :class:`SoftGateResult`.

    Rejected samples are *dropped*, not converted into vetoes: a malformed veto
    is not evidence of a defect, it is evidence of a broken judge.
    """

    def __init__(self, tier_order: Mapping[str, int]) -> None:
        self.tier_order = dict(tier_order)

    def _tier(self, name: str) -> int:
        return self.tier_order.get(name, -1)

    def screen(
        self,
        samples: Sequence[JudgeSample],
        *,
        builder_tier: str,
        builder_identity: str,
        require_citation: bool,
        forbid_self_review: bool,
    ) -> tuple[list[JudgeSample], list[str]]:
        kept: list[JudgeSample] = []
        rejected: list[str] = []
        for s in samples:
            if forbid_self_review and s.judge_identity == builder_identity:
                rejected.append(f"{s.sample_id}: self-review by {s.judge_identity!r}")
                continue
            if self._tier(s.judge_tier) < self._tier(builder_tier):
                rejected.append(
                    f"{s.sample_id}: judge tier {s.judge_tier!r} below builder tier "
                    f"{builder_tier!r}"
                )
                continue
            if (
                require_citation
                and s.verdict is SoftVerdict.VETO
                and not s.citations
            ):
                rejected.append(f"{s.sample_id}: veto without citation")
                continue
            kept.append(s)
        return kept, rejected

    def evaluate(
        self,
        *,
        unit_id: str,
        instance_id: str,
        samples: Sequence[JudgeSample],
        builder_tier: str,
        builder_identity: str,
        aggregation: str = "any_veto",
        require_citation: bool = True,
        forbid_self_review: bool = True,
        kappa_threshold: float = 0.6,
        round_labels: Sequence[Sequence[str]] = (),
        position_swap_agreement: bool | None = None,
    ) -> tuple[SoftGateResult, JudgeFitness]:
        kept, rejected = self.screen(
            samples,
            builder_tier=builder_tier,
            builder_identity=builder_identity,
            require_citation=require_citation,
            forbid_self_review=forbid_self_review,
        )

        kappa = 0.0
        rounds = [list(r) for r in round_labels]
        if len(rounds) >= 2:
            pairs = [
                cohens_kappa(rounds[i], rounds[j])
                for i in range(len(rounds))
                for j in range(i + 1, len(rounds))
            ]
            kappa = min(pairs) if pairs else 0.0
        fitness = JudgeFitness(
            kappa=kappa, threshold=kappa_threshold, sample_count=len(rounds)
        )

        verdict = aggregate(kept, aggregation)
        if verdict is SoftVerdict.VETO and not fitness.fit:
            # An unfit judge may not block either. Blocking on noise trains the
            # organisation to bypass the gate, which is strictly worse than not
            # having it.
            verdict = SoftVerdict.ABSTAIN
            rejected.append(f"veto discarded: judge unfit ({fitness.reason})")
        if position_swap_agreement is False and verdict is SoftVerdict.VETO:
            verdict = SoftVerdict.ABSTAIN
            rejected.append("veto discarded: position-swap disagreement")

        result = SoftGateResult(
            unit_id=unit_id,
            instance_id=instance_id,
            verdict=verdict,
            samples=list(kept),
            aggregation=aggregation,
            builder_tier=builder_tier,
            rejected_samples=rejected,
            kappa=kappa if rounds else None,
            position_swap_agreement=position_swap_agreement,
        )
        return result, fitness
