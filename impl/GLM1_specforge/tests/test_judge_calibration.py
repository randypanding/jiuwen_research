"""WP7 tests: calibration (kappa hand-check, readiness, monitoring signals)."""
from specforge.judge import (
    CalibrationItem,
    EchoJudge,
    Rubric,
    RubricLevel,
    calibrate,
    cohens_kappa,
)

RUBRIC = Rubric(
    rubric_id="rc", dimension="correctness", task="t",
    levels=[RubricLevel(1.0, "good"), RubricLevel(0.0, "bad")])


def test_kappa_hand_computed():
    a = ["pass", "pass", "fail", "fail"]
    b = ["pass", "fail", "fail", "fail"]
    # po = 3/4; pe = (0.5*0.5)+(0.5*0.5) = 0.5 -> kappa = (0.75-0.5)/0.5 = 0.5
    assert abs(cohens_kappa(a, b) - 0.5) < 1e-9


def test_kappa_perfect_agreement():
    assert cohens_kappa(["pass"] * 5, ["pass"] * 5) == 1.0


def test_kappa_length_mismatch_raises():
    import pytest

    with pytest.raises(ValueError):
        cohens_kappa(["pass"], ["pass", "fail"])


def test_calibrate_good_judge_ready():
    items = [CalibrationItem({"content": f"good-{i}"}, "pass") for i in range(20)] + \
            [CalibrationItem({"content": f"bad-{i}"}, "fail") for i in range(20)]
    judge = EchoJudge({"good-": ("pass", 1.0), "bad-": ("fail", 0.0)})
    rep = calibrate(judge, RUBRIC, items)
    assert rep.kappa == 1.0
    assert rep.ready
    assert rep.signals == []


def test_calibrate_random_judge_not_ready():
    class RandomJudge:
        import random as _r

        model_id, tier = "rand", "RU-H"

        def score(self, rubric, item):
            from specforge.judge import JudgeVerdict
            r = RandomJudge._r.Random(item["content"]).random()
            return JudgeVerdict("pass" if r > 0.5 else "fail", 1.0)

    items = [CalibrationItem({"content": f"x{i}"}, "pass" if i % 2 else "fail")
             for i in range(40)]
    rep = calibrate(RandomJudge(), RUBRIC, items)
    assert not rep.ready
    assert any("kappa" in s for s in rep.signals)


def test_calibrate_small_set_flagged():
    items = [CalibrationItem({"content": "good-1"}, "pass")]
    judge = EchoJudge({"good-": ("pass", 1.0)})
    rep = calibrate(judge, RUBRIC, items)
    assert any("too small" in s for s in rep.signals)


def test_confusion_matrix_populated():
    items = [CalibrationItem({"content": "good-1"}, "pass"),
             CalibrationItem({"content": "bad-1"}, "fail")]
    judge = EchoJudge({"good-": ("pass", 1.0), "bad-": ("fail", 0.0)})
    rep = calibrate(judge, RUBRIC, items)
    assert rep.confusion["pass"]["pass"] == 1
    assert rep.confusion["fail"]["fail"] == 1
