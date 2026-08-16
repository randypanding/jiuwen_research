"""Structural invariants: things the type system must make *impossible*.

Each test here corresponds to a rule that a real project would otherwise try to
enforce with a code-review checklist. Checklists decay; constructors do not.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from swarmkernel.contracts.base import ChangeSeverity
from swarmkernel.contracts.gate import (
    AdmissionDecision,
    Finding,
    GateId,
    GateResult,
    GateStatus,
    HardGateReport,
    JudgeSample,
    SoftGateResult,
    SoftVerdict,
)
from swarmkernel.contracts.instance import InstanceReport
from swarmkernel.contracts.oracle import Scenario, ScenarioKind
from swarmkernel.contracts.spec import (
    RLevel,
    RegenerationUnit,
    SpecDelta,
    SpecDeltaItem,
)
from swarmkernel.contracts.spec_md import (
    parse_frontmatter,
    render_spec_markdown,
    verify_spec_markdown,
)
from swarmkernel.contracts.wave import (
    FanoutPlan,
    PipelineKind,
    UncertaintySignal,
    WaveManifest,
    WaveStatus,
    wave_transition,
)


# --------------------------------------------------------------- soft gate


def test_soft_verdict_has_no_pass_member():
    """The soft gate cannot admit, because there is no word for it."""

    assert {v.value for v in SoftVerdict} == {"veto", "no_veto", "abstain"}
    assert not hasattr(SoftVerdict, "PASS")


def test_veto_without_citation_is_refused():
    with pytest.raises(ValidationError, match="citation"):
        JudgeSample(criterion_id="RC-1", verdict=SoftVerdict.VETO)


def test_no_veto_needs_no_citation():
    JudgeSample(criterion_id="RC-1", verdict=SoftVerdict.NO_VETO)


def test_judge_weaker_than_builder_is_refused():
    with pytest.raises(ValidationError, match="judge tier"):
        SoftGateResult(judge_model_tier=1, builder_model_tier=3)


# --------------------------------------------------------------- hard gate


def test_failed_gate_without_finding_is_refused():
    with pytest.raises(ValidationError, match="without a finding"):
        GateResult(gate=GateId.H1_BUILD, status=GateStatus.FAIL)


def test_error_status_also_needs_a_finding():
    with pytest.raises(ValidationError):
        GateResult(gate=GateId.H2_UNIT_PROPERTY, status=GateStatus.ERROR)


def test_soft_gate_cannot_masquerade_as_hard():
    with pytest.raises(ValidationError, match="hard gates only"):
        GateResult(gate=GateId.S_JUDGE, status=GateStatus.PASS)


def test_missing_gate_means_not_passed():
    """Silence is never consent."""

    report = HardGateReport(
        unit_id="U",
        instance_id="I",
        results=[GateResult(gate=GateId.H1_BUILD, status=GateStatus.PASS)],
    )
    assert not report.passed
    assert GateId.H5_DIFFERENTIAL in report.missing_gates


def test_all_gates_present_and_passing_passes():
    report = HardGateReport(
        unit_id="U",
        instance_id="I",
        results=[
            GateResult(gate=g, status=GateStatus.PASS)
            for g in GateId
            if g.is_hard
        ],
    )
    assert report.passed


# -------------------------------------------------------------- admission


def test_admission_record_cannot_be_forged():
    """Even bypassing the algebra function, the record refuses to exist."""

    with pytest.raises(ValidationError, match="algebra violated"):
        AdmissionDecision(
            unit_id="U",
            instance_id="I",
            admitted=True,
            hard_passed=False,
            soft_vetoed=False,
            reasons=[Finding(code="X", message="y")],
        )


def test_admission_cannot_survive_a_veto():
    with pytest.raises(ValidationError, match="algebra violated"):
        AdmissionDecision(
            unit_id="U",
            instance_id="I",
            admitted=True,
            hard_passed=True,
            soft_vetoed=True,
            reasons=[Finding(code="X", message="y")],
        )


def test_rejection_must_carry_a_reason():
    with pytest.raises(ValidationError, match="at least one reason"):
        AdmissionDecision(
            unit_id="U", instance_id="I", admitted=False, hard_passed=False, soft_vetoed=False
        )


# ------------------------------------------------------------------ oracle


def test_scenario_must_assert_something():
    with pytest.raises(ValidationError, match="asserts nothing"):
        Scenario(
            id="SC-X",
            kind=ScenarioKind.EXAMPLE,
            clause_ids=["L2-A-001"],
            entrypoint="f",
            expect={},
        )


def test_scenario_must_bind_a_clause():
    with pytest.raises(ValidationError, match="witnesses no clause"):
        Scenario(id="SC-X", entrypoint="f", expect={"return": 1}, clause_ids=[])


# -------------------------------------------------------------------- spec


def test_breaking_change_without_major_bump_is_refused():
    with pytest.raises(ValidationError):
        SpecDelta(
            delta_id="D",
            spec_id="S",
            from_version="1.2.0",
            to_version="1.2.1",
            items=[
                SpecDeltaItem(
                    op="remove_clause",
                    clause_id="L2-A-001",
                    severity=ChangeSeverity.BREAKING,
                    rationale="removed",
                )
            ],
        )


def test_breaking_change_with_major_bump_is_accepted():
    delta = SpecDelta(
        delta_id="D",
        spec_id="S",
        from_version="1.2.0",
        to_version="2.0.0",
        items=[
            SpecDeltaItem(
                op="remove_clause",
                clause_id="L2-A-001",
                severity=ChangeSeverity.BREAKING,
                rationale="removed",
            )
        ],
    )
    assert delta.severity is ChangeSeverity.BREAKING


def test_r3_unit_without_frozen_goldens_is_refused():
    with pytest.raises(ValidationError):
        RegenerationUnit(
            id="U", title="t", r_level=RLevel.R3, paths=["a/"], frozen_golden_ids=[]
        )


def test_r0_unit_with_external_consumers_is_refused():
    with pytest.raises(ValidationError):
        RegenerationUnit(
            id="U",
            title="t",
            r_level=RLevel.R0,
            paths=["a/"],
            external_consumers=["team-b"],
        )


def test_clause_verifiability(clause_total, clause_unverifiable):
    assert clause_total.is_verifiable
    assert not clause_unverifiable.is_verifiable
    assert clause_unverifiable.is_advisory_only


def test_unverifiable_clauses_are_reported(spec):
    ids = [c.id for c in spec.unverifiable_clauses()]
    assert ids == ["L1-CART.UX-003"]


def test_witness_coverage_is_a_real_fraction(spec):
    assert 0.0 < spec.witness_coverage() < 1.0


# -------------------------------------------------------------------- wave


def test_r3_never_fans_out():
    plan = FanoutPlan.decide(
        unit_id="U",
        signal=UncertaintySignal(novel_domain=True, blast_radius=1.0, r_level=RLevel.R3),
    )
    assert plan.n == 1


def test_fanout_is_bounded():
    plan = FanoutPlan.decide(
        unit_id="U",
        signal=UncertaintySignal(
            novel_domain=True,
            new_clause_count=99,
            historical_rework_rate=1.0,
            blast_radius=1.0,
        ),
    )
    assert 1 <= plan.n <= 8


def test_low_uncertainty_means_single_instance():
    plan = FanoutPlan.decide(
        unit_id="U",
        signal=UncertaintySignal(blast_radius=0.0, historical_rework_rate=0.0),
    )
    assert plan.n == 1


# ---------------------------------------------------- D2: R2 may fan out


def test_r2_may_fan_out_but_r3_may_not():
    """D2 consensus: R2 has external consumers, so parallel regeneration is
    the only way drift against them becomes visible — H4 stays the backstop.
    R3 remains frozen (PDR-001 §5)."""

    assert RLevel.R2.allows_fanout is True
    assert RLevel.R3.allows_fanout is False


def test_fanout_plan_allows_r2_above_the_single_sample():
    signal = UncertaintySignal(
        novel_domain=True, historical_rework_rate=0.6, r_level=RLevel.R2
    )
    plan = FanoutPlan.decide(unit_id="U", signal=signal)
    assert plan.n > 1  # R2 fans out; H4 gates every fanned-out instance


# ------------------------------------------------ D18: majority formula


def test_majority_formula_maps_to_the_consensus_ladder():
    """Default formula U = 0.4*rework + 0.3*novelty + 0.3*R-level, mapped to
    N in {1, 3, 6} (D18 consensus)."""

    low = UncertaintySignal(
        historical_rework_rate=0.0, new_clause_count=0, r_level=RLevel.R0
    )
    mid = UncertaintySignal(
        historical_rework_rate=0.5, new_clause_count=0, r_level=RLevel.R1
    )
    high = UncertaintySignal(
        novel_domain=True, historical_rework_rate=1.0, r_level=RLevel.R2
    )
    assert 0.0 <= low.score_majority() < 0.25
    assert 0.25 <= mid.score_majority() < 0.55
    assert high.score_majority() >= 0.55
    assert FanoutPlan.decide(unit_id="U", signal=low).n == 1
    assert FanoutPlan.decide(unit_id="U", signal=mid).n == 3
    assert FanoutPlan.decide(unit_id="U", signal=high).n == 6


def test_signal_formula_is_an_opt_in_refinement():
    from swarmkernel.contracts.instance import DivergenceVerdict

    signal = UncertaintySignal(
        novel_domain=True,
        new_clause_count=99,
        historical_rework_rate=1.0,
        blast_radius=1.0,
        prior_verdict=DivergenceVerdict.SILENCE,
    )
    plan = FanoutPlan.decide(unit_id="U", signal=signal, formula="signal")
    assert signal.score() >= 0.8
    assert plan.n == 7  # the wider ladder survives as a refinement input
    assert "formula=signal" in plan.reason


def test_unknown_fanout_formula_is_refused():
    signal = UncertaintySignal(r_level=RLevel.R1)
    with pytest.raises(ValueError, match="unknown fan-out formula"):
        FanoutPlan.decide(unit_id="U", signal=signal, formula="vibes")


# ------------------------------------------- D29: six-state wave machine


def test_wave_status_is_the_six_state_sequence_plus_rollback():
    assert [s.value for s in WaveStatus] == [
        "planned",
        "frozen",
        "building",
        "measuring",
        "admitting",
        "committed",
        "rolled_back",
    ]
    assert not hasattr(WaveStatus, "RUNNING")


def test_the_wave_lifecycle_walks_legally_to_committed():
    current = WaveStatus.PLANNED
    for nxt in (
        WaveStatus.FROZEN,
        WaveStatus.BUILDING,
        WaveStatus.MEASURING,
        WaveStatus.ADMITTING,
        WaveStatus.COMMITTED,
    ):
        current = wave_transition(current, nxt)
    assert current is WaveStatus.COMMITTED


def test_every_non_terminal_state_may_roll_back():
    for state in (
        WaveStatus.FROZEN,
        WaveStatus.BUILDING,
        WaveStatus.MEASURING,
        WaveStatus.ADMITTING,
    ):
        assert wave_transition(state, WaveStatus.ROLLED_BACK) is WaveStatus.ROLLED_BACK


def test_phase_skipping_is_refused():
    """A wave that could skip ADMITTING could commit unmeasured code."""

    with pytest.raises(ValueError, match="illegal wave transition"):
        wave_transition(WaveStatus.PLANNED, WaveStatus.MEASURING)
    with pytest.raises(ValueError, match="illegal wave transition"):
        wave_transition(WaveStatus.FROZEN, WaveStatus.COMMITTED)


def test_terminal_states_are_terminal():
    with pytest.raises(ValueError, match="illegal wave transition"):
        wave_transition(WaveStatus.COMMITTED, WaveStatus.PLANNED)
    with pytest.raises(ValueError, match="illegal wave transition"):
        wave_transition(WaveStatus.ROLLED_BACK, WaveStatus.PLANNED)


def test_calibration_pipeline_can_never_commit():
    with pytest.raises(ValidationError):
        WaveManifest(
            wave_id="W",
            pipeline=PipelineKind.CALIBRATION,
            spec_id="S",
            spec_version="1.0.0",
            frozen_surface_digest="d",
            status=WaveStatus.COMMITTED,
        )


# ------------------------------------------- D22: spec Markdown layer


def test_spec_renders_as_markdown_with_frontmatter(spec):
    text = render_spec_markdown(spec)
    assert text.startswith("---\n")
    front = parse_frontmatter(text)
    assert front["spec_id"] == spec.spec_id
    assert front["version"] == spec.version
    assert front["content_digest"].startswith("sha256:")
    assert "## Don't-care regions" in text or front["dont_care_count"] == 0


def test_markdown_rendering_is_deterministic(spec):
    assert render_spec_markdown(spec) == render_spec_markdown(spec)


def test_markdown_verification_pins_the_machine_contract(spec):
    """Frontmatter carries the machine-layer digest; any model change without
    a re-render breaks verification (D22 + D23)."""

    text = render_spec_markdown(spec)
    assert verify_spec_markdown(text, spec) is True
    tampered = text.replace("# ", "#! ", 1)
    assert verify_spec_markdown(tampered, spec) is False
    bumped = spec.model_copy(update={"version": "9.9.9"})
    assert verify_spec_markdown(text, bumped) is False


# ---------------------------------------------------------------- instance


def test_instance_report_may_not_leak_holdout(three_agreeing_reports):
    report: InstanceReport = three_agreeing_reports[0]
    with pytest.raises(ValidationError):
        report.model_copy(
            update={"notes": "I peeked at the holdout scenario list"}
        ).model_validate(
            report.model_copy(
                update={"notes": "I peeked at the holdout scenario list"}
            ).model_dump()
        )
