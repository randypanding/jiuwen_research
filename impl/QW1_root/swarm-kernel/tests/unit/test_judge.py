from __future__ import annotations

from swarm_kernel.contracts.oracle import BiasControls, JudgeVerdictKind, Rubric, RubricItem
from swarm_kernel.judge.workflow import JudgeWorkflow, ScriptedJudgeBackend


def make_rubric(samples: int = 3) -> Rubric:
    return Rubric(
        rubric_id="rub-toy",
        items=[RubricItem(item_id="i1", criterion="submission honors L1 intent")],
        bias=BiasControls(samples=samples, position_swap=False),
    )


def test_no_veto_majority() -> None:
    backend = ScriptedJudgeBackend([{"kind": "no_veto", "reasons": [], "citations": []}])
    verdict = JudgeWorkflow(backend).run(make_rubric(), {"summary": "s"}, "inst-1")
    assert verdict.kind == JudgeVerdictKind.NO_VETO


def test_veto_requires_citations() -> None:
    backend = ScriptedJudgeBackend([{"kind": "veto", "reasons": ["breaks boundary"], "citations": []}])
    verdict = JudgeWorkflow(backend).run(make_rubric(), {"summary": "s"}, "inst-1")
    assert verdict.kind == JudgeVerdictKind.ABSTAIN
    assert any("downgraded" in r for r in verdict.reasons)


def test_veto_with_evidence_holds() -> None:
    backend = ScriptedJudgeBackend(
        [{"kind": "veto", "reasons": ["boundary broken"], "citations": [{"locator": "clamp_impl.py:7", "quote": "hi - 1"}]}]
    )
    verdict = JudgeWorkflow(backend).run(make_rubric(), {"summary": "s"}, "inst-1")
    assert verdict.kind == JudgeVerdictKind.VETO
    assert verdict.citations


def test_disagreement_abstains() -> None:
    backend = ScriptedJudgeBackend(
        [
            {"kind": "veto", "reasons": ["x"], "citations": [{"locator": "a", "quote": "q"}]},
            {"kind": "no_veto", "reasons": [], "citations": []},
            {"kind": "no_veto", "reasons": [], "citations": []},
        ]
    )
    verdict = JudgeWorkflow(backend).run(make_rubric(samples=3), {"summary": "s"}, "inst-1")
    assert verdict.kind == JudgeVerdictKind.ABSTAIN


def test_position_swap_inconsistency_abstains() -> None:
    rubric = make_rubric(samples=2)
    rubric.bias.position_swap = True
    backend = ScriptedJudgeBackend(
        [
            {"kind": "no_veto", "reasons": [], "citations": []},
            {"kind": "veto", "reasons": ["swap-flip"], "citations": [{"locator": "x", "quote": "y"}]},
        ]
    )
    verdict = JudgeWorkflow(backend).run(rubric, {"summary": "s"}, "inst-1")
    assert verdict.kind == JudgeVerdictKind.ABSTAIN


def test_sanitization_strips_builder_identity() -> None:
    seen: list[dict] = []

    class Spy:
        def sample(self, rubric, sanitized_submission, sample_index):
            seen.append(dict(sanitized_submission))
            return {"kind": "no_veto", "reasons": [], "citations": []}

    JudgeWorkflow(Spy()).run(make_rubric(samples=1), {"summary": "s", "builder_identity": "agent-77", "chain_of_thought": "..."}, "inst-1")
    assert seen
    assert "builder_identity" not in seen[0]
    assert "chain_of_thought" not in seen[0]


def test_judge_never_exempts_hard_gates() -> None:
    backend = ScriptedJudgeBackend([{"kind": "no_veto", "reasons": [], "citations": []}])
    verdict = JudgeWorkflow(backend).run(make_rubric(), {"summary": "s"}, "inst-1")
    dumped = verdict.model_dump()
    assert not any("exempt" in k for k in dumped.keys())
