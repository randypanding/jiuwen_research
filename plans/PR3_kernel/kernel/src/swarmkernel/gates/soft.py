"""The soft gate: a monotone veto device.

Everything here exists to enforce one sentence from PDR-001 §5: *the soft gate
can only subtract, never add.* The type system already forbids a PASS verdict
(:class:`SoftVerdict` has no such member). This module adds the operational
rules that make the veto trustworthy:

* **Judge tier >= builder tier.** A weaker model may not overrule a stronger one.
  Enforced by ``SoftGateResult`` itself, which refuses to be constructed.
* **A veto must cite.** An uncited veto is an opinion; opinions do not block.
  Enforced by ``JudgeSample``.
* **No self-review.** A judge may not evaluate an instance it authored.
* **Position swap.** Comparative judging runs both orders; disagreement between
  the two orders is evidence of noise, not a verdict.
* **Abstention is legal.** Forcing a judge to choose manufactures signal that
  does not exist.
* **Agreement is measured, not assumed.** Cohen's kappa over repeated rounds,
  with a floor. Below the floor the judge is *unfit* and the soft gate is
  disabled — which weakens nothing, because it could only ever veto.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Sequence

from ..contracts.gate import Finding, JudgeSample, SoftGateResult, SoftVerdict

__all__ = [
    "AGGREGATION_MODES",
    "cohens_kappa",
    "SoftGateEngine",
    "JudgeFitness",
    "aggregate",
    "ScreenedSample",
]

#: The closed set of aggregation modes. Closed because "the config said so" is
#: not a reason to invent a new admission rule at runtime.
AGGREGATION_MODES: frozenset[str] = frozenset(
    {"any_veto", "majority_veto", "unanimous_veto"}
)


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
    expected = sum((ca[c] / n) * (cb[c] / n) for c in set(ca) | set(cb))
    if expected >= 1.0:
        # Both raters were constant and identical: agreement carries no
        # information, so kappa is undefined. Report 0, never 1.
        return 0.0
    return (observed - expected) / (1.0 - expected)


@dataclass(frozen=True)
class JudgeFitness:
    kappa: float
    threshold: float
    round_count: int

    @property
    def fit(self) -> bool:
        return self.round_count >= 2 and self.kappa >= self.threshold

    @property
    def reason(self) -> str:
        if self.round_count < 2:
            return "fewer than two independent rating rounds; agreement unmeasurable"
        if self.kappa < self.threshold:
            return f"kappa {self.kappa:.3f} < required {self.threshold:.2f}"
        return ""


@dataclass(frozen=True)
class ScreenedSample:
    """A sample plus the identity metadata the contract deliberately omits.

    ``JudgeSample`` carries no author identity — an identity field would be one
    more thing a prompt could lie about. Identity lives here, outside the
    payload, and is supplied by the runtime that dispatched the judge call.
    """

    sample: JudgeSample
    judge_identity: str
    judge_tier: int


def aggregate(samples: Sequence[JudgeSample], mode: str) -> SoftVerdict:
    """Aggregate judge samples into a verdict.

    ``any_veto`` is the default and the only mode safe for a single-sample
    configuration: one credible, cited veto blocks.
    """

    if mode not in AGGREGATION_MODES:
        # Checked before the sample count, so a misconfigured mode is loud even
        # on an empty sample set. A config typo must never degrade to a silent
        # default.
        raise ValueError(f"unknown aggregation mode {mode!r}")
    considered = [s for s in samples if s.verdict is not SoftVerdict.ABSTAIN]
    vetoes = [s for s in considered if s.verdict is SoftVerdict.VETO]
    if not considered:
        return SoftVerdict.ABSTAIN
    if mode == "any_veto":
        return SoftVerdict.VETO if vetoes else SoftVerdict.NO_VETO
    if mode == "majority_veto":
        return (
            SoftVerdict.VETO if len(vetoes) * 2 > len(considered) else SoftVerdict.NO_VETO
        )
    if mode == "unanimous_veto":
        return (
            SoftVerdict.VETO
            if vetoes and len(vetoes) == len(considered)
            else SoftVerdict.NO_VETO
        )
    raise AssertionError(f"unreachable: mode {mode!r}")  # pragma: no cover


class SoftGateEngine:
    """Turns raw judge samples into a :class:`SoftGateResult`.

    Rejected samples are *dropped*, not converted into vetoes: a malformed veto
    is not evidence of a defect, it is evidence of a broken judge.
    """

    def screen(
        self,
        samples: Sequence[ScreenedSample],
        *,
        builder_tier: int,
        builder_identity: str,
        forbid_self_review: bool = True,
    ) -> tuple[list[JudgeSample], list[str]]:
        kept: list[JudgeSample] = []
        rejected: list[str] = []
        for s in samples:
            label = f"{s.sample.criterion_id}#{s.sample.presentation_order}"
            if forbid_self_review and s.judge_identity == builder_identity:
                rejected.append(f"{label}: self-review by {s.judge_identity!r}")
                continue
            if s.judge_tier < builder_tier:
                rejected.append(
                    f"{label}: judge tier {s.judge_tier} below builder tier {builder_tier}"
                )
                continue
            kept.append(s.sample)
        return kept, rejected

    def evaluate(
        self,
        samples: Sequence[ScreenedSample],
        *,
        builder_tier: int,
        builder_identity: str,
        judge_tier: int,
        aggregation: str = "any_veto",
        forbid_self_review: bool = True,
        kappa_threshold: float = 0.6,
        rating_rounds: Sequence[Sequence[str]] = (),
        position_swap_agreement: bool | None = None,
    ) -> tuple[SoftGateResult, JudgeFitness]:
        kept, rejected = self.screen(
            samples,
            builder_tier=builder_tier,
            builder_identity=builder_identity,
            forbid_self_review=forbid_self_review,
        )

        rounds = [list(r) for r in rating_rounds]
        kappa = 0.0
        if len(rounds) >= 2:
            pairs = [
                cohens_kappa(rounds[i], rounds[j])
                for i in range(len(rounds))
                for j in range(i + 1, len(rounds))
            ]
            kappa = min(pairs) if pairs else 0.0
        fitness = JudgeFitness(
            kappa=kappa, threshold=kappa_threshold, round_count=len(rounds)
        )

        verdict = aggregate(kept, aggregation)
        disabled_reason: str | None = None

        if verdict is SoftVerdict.VETO and not fitness.fit:
            # An unfit judge may not block either. Blocking on noise trains the
            # organisation to bypass the gate, which is strictly worse than not
            # having one.
            verdict = SoftVerdict.ABSTAIN
            disabled_reason = f"judge unfit: {fitness.reason}"
            rejected.append(f"veto discarded: {fitness.reason}")
        if position_swap_agreement is False and verdict is SoftVerdict.VETO:
            verdict = SoftVerdict.ABSTAIN
            disabled_reason = "position-swap disagreement"
            rejected.append("veto discarded: position-swap disagreement")

        considered = [s for s in kept if s.verdict is not SoftVerdict.ABSTAIN]
        abstention_rate = (
            0.0 if not kept else (len(kept) - len(considered)) / len(kept)
        )

        result = SoftGateResult(
            verdict=verdict,
            samples=kept,
            judge_model_tier=judge_tier,
            builder_model_tier=builder_tier,
            calibration_agreement=kappa if rounds else None,
            abstention_rate=abstention_rate,
            findings=[
                Finding(
                    code="S.SAMPLE_REJECTED",
                    message=reason,
                    severity="warning",
                )
                for reason in rejected
            ],
            disabled_reason=disabled_reason,
        )
        return result, fitness
