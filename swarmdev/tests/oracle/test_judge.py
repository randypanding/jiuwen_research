import json

from swarmdev.contracts import JudgeRubric
from swarmdev.contracts.oracle import RubricDimension, RubricLevel
from swarmdev.oracle import JudgeWorkflow


def _rubric(evidence_required=True) -> JudgeRubric:
    return JudgeRubric(
        rubric_id="RUB-1",
        target_description="demo artifact",
        dimensions=[
            RubricDimension(
                dimension_id="D1",
                description="correctness",
                levels=[
                    RubricLevel(level=0, label="bad", observable_criteria="broken behavior"),
                    RubricLevel(level=1, label="good", observable_criteria="works as specified"),
                ],
            )
        ],
        evidence_required=evidence_required,
    )


def _veto_json() -> str:
    return json.dumps(
        {"verdict": "veto", "reasons": ["broken behavior"], "evidence_refs": ["ev-1"]}
    )


_NO_VETO_JSON = json.dumps({"verdict": "no_veto", "reasons": [], "evidence_refs": []})
_ABSTAIN_JSON = json.dumps({"verdict": "abstain", "reasons": [], "evidence_refs": []})


def test_majority_veto():
    workflow = JudgeWorkflow(lambda prompt: _veto_json(), samples=3)
    verdict = workflow.evaluate(_rubric(), "artifact summary", ["ev-1"])
    assert verdict.verdict == "veto"
    assert verdict.reasons == ["broken behavior"]
    assert verdict.evidence_refs == ["ev-1"]
    assert verdict.agreement_ratio == 1.0
    assert verdict.samples == 3


def test_majority_no_veto():
    workflow = JudgeWorkflow(lambda prompt: _NO_VETO_JSON, samples=3)
    verdict = workflow.evaluate(_rubric(), "artifact summary", [])
    assert verdict.verdict == "no_veto"
    assert verdict.agreement_ratio == 1.0


def test_majority_vote_two_of_three():
    responses = iter([_veto_json(), _veto_json(), _NO_VETO_JSON])
    workflow = JudgeWorkflow(lambda prompt: next(responses), samples=3)
    verdict = workflow.evaluate(_rubric(), "s", [])
    assert verdict.verdict == "veto"
    assert verdict.agreement_ratio == 2 / 3


def test_no_majority_falls_to_abstain():
    responses = iter([_veto_json(), _NO_VETO_JSON, _ABSTAIN_JSON])
    workflow = JudgeWorkflow(lambda prompt: next(responses), samples=3)
    verdict = workflow.evaluate(_rubric(), "s", [])
    assert verdict.verdict == "abstain"
    assert verdict.agreement_ratio == 1 / 3


def test_bad_json_votes_abstain():
    workflow = JudgeWorkflow(lambda prompt: "this is not json", samples=3)
    verdict = workflow.evaluate(_rubric(), "s", [])
    assert verdict.verdict == "abstain"


def test_veto_without_evidence_downgraded_to_abstain():
    payload = json.dumps({"verdict": "veto", "reasons": ["bad"], "evidence_refs": []})
    strict = JudgeWorkflow(lambda prompt: payload, samples=3)
    assert strict.evaluate(_rubric(evidence_required=True), "s", []).verdict == "abstain"
    lax = JudgeWorkflow(lambda prompt: payload, samples=3)
    assert lax.evaluate(_rubric(evidence_required=False), "s", []).verdict == "veto"


def test_prompt_contains_rubric_and_json_contract():
    seen = []

    def model(prompt):
        seen.append(prompt)
        return _NO_VETO_JSON

    JudgeWorkflow(model, samples=1).evaluate(_rubric(), "SUMMARY-MARKER", ["ev-x"])
    prompt = seen[0]
    assert "D1" in prompt
    assert "SUMMARY-MARKER" in prompt
    assert "ev-x" in prompt
    assert '"verdict"' in prompt


def _fair_model(prompt: str) -> str:
    try:
        first = prompt.split("FIRST: ", 1)[1].split("\n", 1)[0]
        second = prompt.split("SECOND: ", 1)[1].split("\n", 1)[0]
    except IndexError:
        return "{}"
    if "GOOD" in first:
        return json.dumps({"winner": "first"})
    if "GOOD" in second:
        return json.dumps({"winner": "second"})
    return json.dumps({"winner": "first"})


def test_pairwise_consistent_winner():
    workflow = JudgeWorkflow(_fair_model, samples=1)
    assert workflow.compare_pairwise("ALPHA GOOD artifact", "BETA artifact") == {"winner": "A"}


def test_pairwise_position_bias_detected():
    biased = JudgeWorkflow(lambda prompt: json.dumps({"winner": "first"}), samples=1)
    result = biased.compare_pairwise("A1", "B1")
    assert result == {"winner": None, "reason": "position_inconsistency"}


def test_pairwise_unparseable_response():
    workflow = JudgeWorkflow(lambda prompt: "???", samples=1)
    result = workflow.compare_pairwise("A", "B")
    assert result["winner"] is None
    assert result["reason"] == "unparseable_response"
