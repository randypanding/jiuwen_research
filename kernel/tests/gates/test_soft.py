"""The soft gate: everything that stops an LLM judge from becoming a bottleneck
that blocks correct work for stylistic reasons it cannot defend.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from swarmkernel.contracts.gate import JudgeSample, SoftGateResult, SoftVerdict
from swarmkernel.gates.soft import (
    ScreenedSample,
    SoftGateEngine,
    aggregate,
    cohens_kappa,
)


def sample(
    verdict: SoftVerdict,
    *,
    identity: str = "judge-1",
    tier: int = 3,
    criterion: str = "C-READABILITY",
    order: int = 0,
    citation: str | None = "cart/total.py:12",
) -> ScreenedSample:
    return ScreenedSample(
        sample=JudgeSample(
            criterion_id=criterion,
            verdict=verdict,
            citation=citation if verdict is SoftVerdict.VETO else None,
            presentation_order=order,
        ),
        judge_identity=identity,
        judge_tier=tier,
    )


FIT_ROUNDS = (
    ["veto", "no_veto", "veto", "no_veto", "veto", "no_veto"],
    ["veto", "no_veto", "veto", "no_veto", "veto", "veto"],
)


# ----------------------------------------------------------------- kappa


def test_kappa_of_perfect_agreement_on_a_varied_task_is_one():
    a = ["a", "b", "a", "c", "b", "c"]
    assert cohens_kappa(a, a) == pytest.approx(1.0)


def test_kappa_of_a_constant_rater_is_zero_not_one():
    """A judge that always says the same thing agrees with itself perfectly and
    tells us nothing. Raw agreement would score it 1.0; kappa must not."""

    a = ["no_veto"] * 20
    assert cohens_kappa(a, a) == 0.0


def test_kappa_of_independent_noise_is_near_zero():
    a = ["a", "b"] * 10
    b = ["a", "a", "b", "b"] * 5
    assert cohens_kappa(a, b) < 0.3


def test_kappa_rejects_mismatched_vectors():
    with pytest.raises(ValueError):
        cohens_kappa(["a"], ["a", "b"])


def test_kappa_of_empty_input_is_zero():
    assert cohens_kappa([], []) == 0.0


# ----------------------------------------------------------- aggregation


@pytest.mark.parametrize(
    "mode,verdicts,expected",
    [
        ("any_veto", ["veto", "no_veto", "no_veto"], SoftVerdict.VETO),
        ("any_veto", ["no_veto", "no_veto"], SoftVerdict.NO_VETO),
        ("majority_veto", ["veto", "no_veto", "no_veto"], SoftVerdict.NO_VETO),
        ("majority_veto", ["veto", "veto", "no_veto"], SoftVerdict.VETO),
        ("unanimous_veto", ["veto", "veto"], SoftVerdict.VETO),
        ("unanimous_veto", ["veto", "no_veto"], SoftVerdict.NO_VETO),
    ],
)
def test_aggregation_modes(mode, verdicts, expected):
    samples = [
        sample(SoftVerdict(v), criterion=f"C-{i}").sample for i, v in enumerate(verdicts)
    ]
    assert aggregate(samples, mode) is expected


def test_abstentions_are_excluded_from_the_denominator():
    """Otherwise a judge could dilute a real veto into a minority by abstaining
    on everything else."""

    samples = [
        sample(SoftVerdict.VETO, criterion="C-1").sample,
        sample(SoftVerdict.ABSTAIN, criterion="C-2").sample,
        sample(SoftVerdict.ABSTAIN, criterion="C-3").sample,
    ]
    assert aggregate(samples, "majority_veto") is SoftVerdict.VETO


def test_all_abstain_is_abstain_not_no_veto():
    samples = [sample(SoftVerdict.ABSTAIN, criterion=f"C-{i}").sample for i in range(3)]
    assert aggregate(samples, "any_veto") is SoftVerdict.ABSTAIN


def test_unknown_aggregation_mode_is_refused():
    with pytest.raises(ValueError, match="unknown aggregation"):
        aggregate([], "whatever_the_prompt_said")


# ------------------------------------------------------------- screening


def test_a_veto_without_a_citation_cannot_even_be_constructed():
    with pytest.raises(ValidationError, match="citation"):
        JudgeSample(criterion_id="C", verdict=SoftVerdict.VETO)


def test_a_judge_may_not_review_its_own_work():
    engine = SoftGateEngine()
    kept, rejected = engine.screen(
        [sample(SoftVerdict.VETO, identity="builder-7")],
        builder_tier=3,
        builder_identity="builder-7",
    )
    assert kept == []
    assert "self-review" in rejected[0]


def test_a_weaker_judge_may_not_overrule_a_stronger_builder():
    engine = SoftGateEngine()
    kept, rejected = engine.screen(
        [sample(SoftVerdict.VETO, tier=1)],
        builder_tier=3,
        builder_identity="builder-7",
    )
    assert kept == []
    assert "below required floor" in rejected[0]


def test_a_judge_below_the_protocol_floor_is_dropped_even_above_the_builder():
    """D31: the absolute ``min_model_tier`` floor (JudgeProtocol default 2) is
    enforced at screening — a tier-1 judge is rejected even when the builder
    is also tier 1, closing the gap between the documented rule and the code."""

    engine = SoftGateEngine()
    kept, rejected = engine.screen(
        [sample(SoftVerdict.NO_VETO, tier=1)],
        builder_tier=1,
        builder_identity="builder-7",
        min_judge_tier=2,
    )
    assert kept == []
    assert "protocol minimum 2" in rejected[0]


def test_the_default_aggregation_is_any_veto_everywhere():
    """D15: engine default and contract default must agree, and must be
    ``any_veto`` — with k=3, ``majority_veto`` lets one credible cited veto be
    outvoted, which turns the soft gate into a rubber stamp."""

    from swarmkernel.contracts.oracle import JudgeProtocol

    assert JudgeProtocol().aggregation == "any_veto"


def test_the_tier_rule_is_also_enforced_by_the_contract_itself():
    """Belt and braces: even a runtime that skips ``screen`` cannot persist an
    inverted-tier result."""

    with pytest.raises(ValidationError):
        SoftGateResult(judge_model_tier=1, builder_model_tier=3)


# -------------------------------------------------------------- evaluate


def test_a_fit_judge_with_a_cited_veto_blocks():
    result, fitness = SoftGateEngine().evaluate(
        [sample(SoftVerdict.VETO)],
        builder_tier=2,
        builder_identity="builder-7",
        judge_tier=3,
        rating_rounds=FIT_ROUNDS,
    )
    assert fitness.fit
    assert result.verdict is SoftVerdict.VETO
    assert result.disabled_reason is None


def test_an_unfit_judge_is_disabled_rather_than_trusted():
    """Below the kappa floor the veto is discarded. Weakening the soft gate
    weakens nothing: it could only ever subtract."""

    noisy = (["a", "b"] * 6, ["a", "a", "b", "b"] * 3)
    result, fitness = SoftGateEngine().evaluate(
        [sample(SoftVerdict.VETO)],
        builder_tier=2,
        builder_identity="builder-7",
        judge_tier=3,
        rating_rounds=noisy,
    )
    assert not fitness.fit
    assert result.verdict is SoftVerdict.ABSTAIN
    assert "judge unfit" in result.disabled_reason


def test_a_judge_with_fewer_than_two_rounds_is_unmeasured_and_therefore_unfit():
    result, fitness = SoftGateEngine().evaluate(
        [sample(SoftVerdict.VETO)],
        builder_tier=2,
        builder_identity="builder-7",
        judge_tier=3,
        rating_rounds=(),
    )
    assert not fitness.fit
    assert "unmeasurable" in fitness.reason
    assert result.verdict is SoftVerdict.ABSTAIN


def test_position_swap_disagreement_discards_the_veto():
    """If flipping the order of the two candidates flips the answer, the answer
    was about the order, not the code."""

    result, _ = SoftGateEngine().evaluate(
        [sample(SoftVerdict.VETO, order=0), sample(SoftVerdict.VETO, order=1)],
        builder_tier=2,
        builder_identity="builder-7",
        judge_tier=3,
        rating_rounds=FIT_ROUNDS,
        position_swap_agreement=False,
    )
    assert result.verdict is SoftVerdict.ABSTAIN
    assert result.disabled_reason == "position-swap disagreement"


def test_position_swap_agreement_keeps_the_veto():
    result, _ = SoftGateEngine().evaluate(
        [sample(SoftVerdict.VETO)],
        builder_tier=2,
        builder_identity="builder-7",
        judge_tier=3,
        rating_rounds=FIT_ROUNDS,
        position_swap_agreement=True,
    )
    assert result.verdict is SoftVerdict.VETO


def test_rejected_samples_become_warnings_not_vetoes():
    """A malformed veto is evidence of a broken judge, not of a defect."""

    result, _ = SoftGateEngine().evaluate(
        [sample(SoftVerdict.VETO, identity="builder-7")],
        builder_tier=2,
        builder_identity="builder-7",
        judge_tier=3,
        rating_rounds=FIT_ROUNDS,
    )
    assert result.verdict is SoftVerdict.ABSTAIN
    assert result.samples == []
    assert all(f.severity == "warning" for f in result.findings)
    assert any("self-review" in f.message for f in result.findings)


def test_abstention_rate_is_reported_so_a_silent_judge_is_visible():
    result, _ = SoftGateEngine().evaluate(
        [
            sample(SoftVerdict.ABSTAIN, criterion="C-1"),
            sample(SoftVerdict.ABSTAIN, criterion="C-2"),
            sample(SoftVerdict.NO_VETO, criterion="C-3"),
        ],
        builder_tier=2,
        builder_identity="builder-7",
        judge_tier=3,
        rating_rounds=FIT_ROUNDS,
    )
    assert result.abstention_rate == pytest.approx(2 / 3)


def test_kappa_uses_the_worst_pair_not_the_average():
    """Three rounds where two agree and one is noise must not average away the
    noise."""

    rounds = (
        ["a", "b", "a", "b", "a", "b"],
        ["a", "b", "a", "b", "a", "b"],
        ["b", "a", "b", "a", "b", "a"],
    )
    _, fitness = SoftGateEngine().evaluate(
        [],
        builder_tier=2,
        builder_identity="b",
        judge_tier=3,
        rating_rounds=rounds,
    )
    assert fitness.kappa < 0.0
    assert not fitness.fit
