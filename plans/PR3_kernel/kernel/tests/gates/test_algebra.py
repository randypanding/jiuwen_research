"""The admission algebra: ``Admit = H ∧ S``.

This is the smallest and most important module in the kernel, so it gets the
heaviest tests: the two safety properties are proved by *exhaustion* over the
whole reachable state space rather than by example.
"""

from __future__ import annotations

import itertools

import pytest

from swarmkernel.contracts.base import Role
from swarmkernel.contracts.gate import (
    Finding,
    GateId,
    GateResult,
    GateStatus,
    JudgeSample,
    SoftGateResult,
    SoftVerdict,
)
from swarmkernel.contracts.spec import RLevel
from swarmkernel.gates.algebra import REQUIRED_GATES, admit, build_hard_report, decide

HARD = [g for g in GateId if g.is_hard]


def result(gate: GateId, status: GateStatus) -> GateResult:
    findings = (
        []
        if status is GateStatus.PASS
        else [Finding(code=f"{gate.value}.X", message="broken")]
    )
    return GateResult(gate=gate, status=status, findings=findings)


def all_pass() -> list[GateResult]:
    return [result(g, GateStatus.PASS) for g in HARD]


def soft(verdict: SoftVerdict, *, judge_tier: int = 2, builder_tier: int = 2):
    samples = []
    if verdict is SoftVerdict.VETO:
        samples = [
            JudgeSample(
                criterion_id="C-READABILITY",
                verdict=SoftVerdict.VETO,
                citation="cart/total.py:12",
            )
        ]
    return SoftGateResult(
        verdict=verdict,
        samples=samples,
        judge_model_tier=judge_tier,
        builder_model_tier=builder_tier,
    )


# ------------------------------------------------------- required gate set


def test_every_hard_gate_is_required_at_every_level():
    """There is no per-level opt-out. A gate that is optional is a gate that is
    off, and an off gate is indistinguishable from a passing one in the report."""

    assert set(REQUIRED_GATES) == set(HARD)
    assert len(REQUIRED_GATES) == 8


def test_a_missing_gate_is_not_a_pass():
    for omitted in HARD:
        results = [r for r in all_pass() if r.gate is not omitted]
        report = build_hard_report("U", "i", results)
        assert not report.passed, omitted
        assert report.missing_gates == [omitted]


def test_an_errored_gate_is_not_a_pass():
    """ERROR means the gate could not run. An unrunnable gate is not a gate."""

    for broken in HARD:
        results = [
            result(g, GateStatus.ERROR if g is broken else GateStatus.PASS) for g in HARD
        ]
        assert not build_hard_report("U", "i", results).passed, broken


# ---------------------------------------------------------- the two proofs


@pytest.mark.parametrize("n_failures", range(0, 9))
def test_no_rescue_property(n_failures):
    """**No rescue.** For any soft verdict, if the hard report is not fully
    passed, admission is False. Proven over every subset of failing gates and
    every soft verdict, which is the entire reachable space."""

    for failing in itertools.combinations(HARD, n_failures):
        results = [
            result(g, GateStatus.FAIL if g in failing else GateStatus.PASS) for g in HARD
        ]
        report = build_hard_report("U", "i", results)
        for verdict in SoftVerdict:
            got = admit(report, soft(verdict))
            assert got is (n_failures == 0 and verdict is not SoftVerdict.VETO)


def test_veto_monotonicity_property():
    """**Monotone veto.** A VETO makes admission False regardless of H, and
    removing the veto never turns an admitted decision into a rejected one."""

    for n in range(0, 9):
        for failing in itertools.combinations(HARD, n):
            results = [
                result(g, GateStatus.FAIL if g in failing else GateStatus.PASS)
                for g in HARD
            ]
            report = build_hard_report("U", "i", results)
            assert admit(report, soft(SoftVerdict.VETO)) is False
            without = admit(report, None)
            with_no_veto = admit(report, soft(SoftVerdict.NO_VETO))
            assert without == with_no_veto
            assert without >= admit(report, soft(SoftVerdict.VETO))


def test_the_soft_gate_cannot_express_a_pass():
    """Structural, not behavioural: the enum has no PASS member, so no future
    edit to the aggregation logic can accidentally invent one."""

    assert {v.value for v in SoftVerdict} == {"veto", "no_veto", "abstain"}
    assert not any("pass" in v.value for v in SoftVerdict)


def test_an_absent_soft_gate_is_neither_veto_nor_rescue():
    assert admit(build_hard_report("U", "i", all_pass()), None) is True
    failing = [result(g, GateStatus.FAIL if g is GateId.H2_UNIT_PROPERTY else GateStatus.PASS) for g in HARD]
    assert admit(build_hard_report("U", "i", failing), None) is False


def test_abstention_does_not_block():
    report = build_hard_report("U", "i", all_pass())
    assert admit(report, soft(SoftVerdict.ABSTAIN)) is True


# ------------------------------------------------------------- decide()


def test_decide_records_a_clean_admission():
    d = decide(
        unit_id="UNIT-CART",
        instance_id="inst-a",
        r_level=RLevel.R1,
        results=all_pass(),
        soft=soft(SoftVerdict.NO_VETO),
    )
    assert d.admitted and d.hard_passed and not d.soft_vetoed
    assert d.reasons == []


def test_decide_explains_every_rejection():
    """A rejection without a reason is unappealable, and an unappealable gate
    gets disabled by the first team it inconveniences."""

    results = [
        result(g, GateStatus.FAIL if g is GateId.H3_HOLDOUT else GateStatus.PASS)
        for g in HARD
    ]
    d = decide(
        unit_id="U",
        instance_id="i",
        r_level=RLevel.R1,
        results=results,
        soft=soft(SoftVerdict.VETO),
    )
    assert not d.admitted
    codes = {f.code for f in d.reasons}
    assert codes == {"ADMIT.GATE_FAILED", "ADMIT.SOFT_VETO"}
    assert "cart/total.py:12" in next(
        f.message for f in d.reasons if f.code == "ADMIT.SOFT_VETO"
    )


def test_decide_names_the_gates_that_never_ran():
    d = decide(
        unit_id="U",
        instance_id="i",
        r_level=RLevel.R1,
        results=all_pass()[:5],
        soft=None,
    )
    assert not d.admitted
    reason = next(f for f in d.reasons if f.code == "ADMIT.GATE_MISSING")
    assert "H6" in reason.message and "H8" in reason.message


@pytest.mark.parametrize("level", [RLevel.R2, RLevel.R3])
def test_high_reversibility_levels_require_recorded_human_approval(level):
    d = decide(
        unit_id="U",
        instance_id="i",
        r_level=level,
        results=all_pass(),
        soft=None,
        human_approved=False,
    )
    assert not d.admitted
    assert "ADMIT.HUMAN_APPROVAL_REQUIRED" in {f.code for f in d.reasons}

    approved = decide(
        unit_id="U",
        instance_id="i",
        r_level=level,
        results=all_pass(),
        soft=None,
        human_approved=True,
    )
    assert approved.admitted


@pytest.mark.parametrize("level", [RLevel.R0, RLevel.R1])
def test_low_reversibility_levels_do_not_need_a_human(level):
    d = decide(
        unit_id="U",
        instance_id="i",
        r_level=level,
        results=all_pass(),
        soft=None,
    )
    assert d.admitted


def test_human_approval_cannot_rescue_a_failing_unit():
    """Approval is a precondition, not an override. This is the property that
    stops "the human signed off" from becoming a bypass of the gates."""

    results = [
        result(g, GateStatus.FAIL if g is GateId.H1_BUILD else GateStatus.PASS)
        for g in HARD
    ]
    d = decide(
        unit_id="U",
        instance_id="i",
        r_level=RLevel.R3,
        results=results,
        soft=None,
        human_approved=True,
    )
    assert not d.admitted


def test_the_decision_record_cannot_be_forged():
    """The contract re-derives ``admitted`` from its own inputs, so a runtime
    that lies in one field is rejected at construction rather than believed."""

    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="algebra violated"):
        from swarmkernel.contracts.gate import AdmissionDecision

        AdmissionDecision(
            unit_id="U",
            instance_id="i",
            admitted=True,
            hard_passed=False,
            soft_vetoed=False,
            decided_by=Role.LEADER,
        )

    with pytest.raises(ValidationError, match="algebra violated"):
        from swarmkernel.contracts.gate import AdmissionDecision

        AdmissionDecision(
            unit_id="U",
            instance_id="i",
            admitted=True,
            hard_passed=True,
            soft_vetoed=True,
            decided_by=Role.LEADER,
        )


def test_decide_is_deterministic_given_the_same_evidence():
    kw = dict(
        unit_id="U",
        instance_id="i",
        r_level=RLevel.R1,
        results=all_pass(),
        soft=soft(SoftVerdict.NO_VETO),
    )
    a, b = decide(**kw), decide(**kw)
    assert a.model_dump(exclude={"decided_at"}) == b.model_dump(exclude={"decided_at"})
