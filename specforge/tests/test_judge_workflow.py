"""WP7 tests: judge workflow (votes, swap, abstain, tier, independence)."""
import pytest

from specforge.judge import (
    EchoJudge,
    Rubric,
    RubricLevel,
    assert_independence,
    assert_tier_ok,
    pairwise,
    parse_verdict_json,
    run_judge,
)

RUBRIC = Rubric(
    rubric_id="r1", dimension="correctness", task="judge the snippet",
    levels=[RubricLevel(1.0, "correct"), RubricLevel(0.0, "incorrect")])


def test_majority_pass():
    judge = EchoJudge({"good": ("pass", 1.0)})
    res = run_judge(judge, RUBRIC, {"content": "good stuff"}, k=3)
    assert res.verdict == "PASS"
    assert res.votes == ["pass", "pass", "pass"]


def test_majority_fail():
    judge = EchoJudge({"bad": ("fail", 0.0)})
    res = run_judge(judge, RUBRIC, {"content": "bad stuff"}, k=3)
    assert res.verdict == "FAIL"


def test_abstain_limit_blocks():
    judge = EchoJudge({})  # always abstains
    res = run_judge(judge, RUBRIC, {"content": "anything"}, k=3)
    assert res.verdict == "INCONCLUSIVE"


def test_split_vote_inconclusive():
    class FlipJudge:
        model_id, tier = "flip", "RU-H"
        calls = 0

        def score(self, rubric, item):
            FlipJudge.calls += 1
            from specforge.judge import JudgeVerdict
            v = "pass" if FlipJudge.calls % 2 else "fail"
            return JudgeVerdict(v, 1.0 if v == "pass" else 0.0)

    res = run_judge(FlipJudge(), RUBRIC, {"content": "x"}, k=4)
    assert res.verdict == "INCONCLUSIVE"
    assert "split" in res.reason


def test_pairwise_swap_disagreement_is_tie():
    class PositionBiased:
        model_id, tier = "pb", "RU-H"

        def score(self, rubric, item):
            from specforge.judge import JudgeVerdict
            content = item["content"]
            a_pos = content.index("OPTION-A")
            b_pos = content.index("OPTION-B")
            # whichever OPTION label comes FIRST in the text always wins
            prefers_a = a_pos < b_pos
            return JudgeVerdict("pass", 1.0) if prefers_a else JudgeVerdict("fail", 0.0)

    # _pair_call keeps labels in fixed order (OPTION-A then OPTION-B), so a
    # label-position-biased judge is actually consistent; instead simulate a
    # value-position bias: prefer the option whose VALUE slot holds "AAA".
    class ValuePositionBiased:
        model_id, tier = "vpb", "RU-H"

        def score(self, rubric, item):
            from specforge.judge import JudgeVerdict
            content = item["content"]
            a_block = content[content.index("OPTION-A:"):content.index("OPTION-B:")]
            return JudgeVerdict("pass", 1.0) if "AAA" in a_block else JudgeVerdict("fail", 0.0)

    r = pairwise(ValuePositionBiased(), RUBRIC, {"content": "AAA"}, {"content": "BBB"})
    # run1: OPTION-A holds AAA -> pass -> "a>b"; run2 (swapped): OPTION-A holds BBB -> fail -> "b>a"
    assert r == "tie"  # swapped runs disagree -> neutralized


def test_pairwise_consistent():
    class PrefersA:
        model_id, tier = "pa", "RU-H"

        def score(self, rubric, item):
            from specforge.judge import JudgeVerdict
            return JudgeVerdict("pass", 1.0) if "AAA" in item["content"] else JudgeVerdict("fail", 0.0)

    r = pairwise(PrefersA(), RUBRIC, {"content": "AAA"}, {"content": "BBB"})
    assert r == "a>b"


def test_tier_enforcement():
    assert_tier_ok("RU-H", "RU-M")
    assert_tier_ok("RU-M", "RU-M")
    with pytest.raises(PermissionError):
        assert_tier_ok("RU-L", "RU-M")


def test_independence_checks():
    assert_independence("vendor-a/big", "vendor-b/small")
    with pytest.raises(PermissionError):
        assert_independence("m1", "m1")  # same model
    with pytest.raises(PermissionError):
        assert_independence("gpt-x", "gpt-y", {"gpt-x": "openai", "gpt-y": "openai"})


def test_parse_verdict_json_cot():
    raw = 'reasoning...\n{"verdict": "pass", "score": 0.9, "reasons": ["ok"], "evidence": ["line 3"]}'
    v = parse_verdict_json(raw)
    assert v.verdict == "pass" and v.score == 0.9 and v.evidence == ["line 3"]
    bad = parse_verdict_json("no json at all")
    assert bad.abstained
