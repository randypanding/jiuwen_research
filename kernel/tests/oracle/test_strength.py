"""Oracle strength: who tests the tests.

The finding that motivates this whole module: roughly four in five
agent-written tests contain no valid assertion. A swarm that grades itself with
such tests is a machine for producing confident nonsense, so the oracle is
audited before it is trusted, and the audit is a hard prerequisite of H3.

The grade ladder is deliberately monotone and gap-free: you cannot buy Gold with
mutation probes if your scenarios assert nothing.
"""

from __future__ import annotations

import pytest

from swarmkernel.contracts.oracle import (
    HoldoutOracle,
    OracleBundle,
    OracleGrade,
    Scenario,
    ScenarioKind,
)
from swarmkernel.oracle.strength import (
    MutationOutcome,
    OracleAuditor,
    run_mutation_probes,
)

CLAUSES = ["L2-CART.TOTAL-001", "L2-CART.CURRENCY-002"]


def killed_all(bundle) -> list[MutationOutcome]:
    return [
        MutationOutcome(probe_id=p.id, killed=True, killed_by=("H2",))
        for p in bundle.holdout.mutation_probes
    ]


def regression_all_green(bundle) -> dict[str, bool]:
    return {s.id: True for s in bundle.holdout.scenarios}


# ------------------------------------------------------------- the ladder


def test_a_full_bundle_reaches_diamond(bundle):
    report = OracleAuditor().audit(
        bundle,
        clause_ids=CLAUSES,
        mutation_outcomes=killed_all(bundle),
        regression_scenarios=regression_all_green(bundle),
    )
    assert report.grade is OracleGrade.DIAMOND
    assert report.at_least(OracleGrade.GOLD)


def test_a_surviving_mutation_probe_caps_the_grade_at_gold(bundle):
    """The probe is the whole point: a scenario set that cannot detect a
    deliberately broken implementation has not earned the top grade."""

    outcomes = killed_all(bundle)
    outcomes[0] = MutationOutcome(probe_id=outcomes[0].probe_id, killed=False)
    report = OracleAuditor().audit(
        bundle,
        clause_ids=CLAUSES,
        mutation_outcomes=outcomes,
        regression_scenarios=regression_all_green(bundle),
    )
    assert report.grade is OracleGrade.GOLD
    assert report.surviving_probes == [outcomes[0].probe_id]


def test_no_mutation_probes_means_diamond_is_unattainable(bundle):
    report = OracleAuditor().audit(
        bundle, clause_ids=CLAUSES, regression_scenarios=regression_all_green(bundle)
    )
    assert report.grade is OracleGrade.GOLD
    assert any("Diamond is unattainable" in r for r in report.reasons)


def test_an_unbound_clause_caps_the_grade_at_silver(bundle):
    report = OracleAuditor().audit(
        bundle,
        clause_ids=[*CLAUSES, "L2-CART.DISCOUNT-004"],
        mutation_outcomes=killed_all(bundle),
        regression_scenarios=regression_all_green(bundle),
    )
    assert report.grade is OracleGrade.SILVER
    assert any("L2-CART.DISCOUNT-004" in r for r in report.reasons)


def test_a_missing_regression_set_caps_the_grade_at_bronze(bundle):
    """SWE-bench's dual criterion: making the new scenarios pass proves nothing
    if you were allowed to break everything else on the way."""

    report = OracleAuditor().audit(
        bundle, clause_ids=CLAUSES, mutation_outcomes=killed_all(bundle)
    )
    assert report.grade is OracleGrade.BRONZE
    assert any("PASS_TO_PASS" in r for r in report.reasons)


def test_a_failing_regression_scenario_caps_the_grade_at_bronze(bundle):
    regression = regression_all_green(bundle)
    regression["SC-EMPTY"] = False
    report = OracleAuditor().audit(
        bundle,
        clause_ids=CLAUSES,
        mutation_outcomes=killed_all(bundle),
        regression_scenarios=regression,
    )
    assert report.grade is OracleGrade.BRONZE
    assert not report.dual_criterion


def test_an_empty_bundle_is_bronze_not_an_error(bundle):
    empty = bundle.model_copy(
        update={
            "holdout": bundle.holdout.model_copy(update={"scenarios": []}),
        }
    )
    report = OracleAuditor().audit(empty, clause_ids=CLAUSES)
    assert report.grade is OracleGrade.BRONZE
    assert "bundle contains no scenarios" in report.reasons


def test_the_ladder_is_monotone(bundle):
    """Every rung strictly implies the ones below it, so ``at_least`` is a
    usable gate predicate."""

    report = OracleAuditor().audit(
        bundle,
        clause_ids=CLAUSES,
        mutation_outcomes=killed_all(bundle),
        regression_scenarios=regression_all_green(bundle),
    )
    for grade in (OracleGrade.BRONZE, OracleGrade.SILVER, OracleGrade.GOLD, OracleGrade.DIAMOND):
        assert report.at_least(grade)


def test_bronze_is_not_gold(bundle):
    report = OracleAuditor().audit(bundle, clause_ids=CLAUSES)
    assert not report.at_least(OracleGrade.GOLD)


# ----------------------------------------------------------- anti-vacuity


def test_a_scenario_that_asserts_nothing_cannot_be_constructed():
    """First line of defence: the vacuous scenario never enters the bundle."""

    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="asserts nothing"):
        Scenario(
            id="SC-VACUOUS",
            kind=ScenarioKind.EXAMPLE,
            clause_ids=["L2-CART.TOTAL-001"],
            entrypoint="cart.total",
            inputs={"lines": []},
            expect={},
        )


def test_the_auditor_still_measures_assertion_rate(bundle):
    """Second line of defence: even if a scenario arrives from an older schema
    version, the audit reports the rate rather than assuming it is 1.0."""

    report = OracleAuditor().audit(
        bundle,
        clause_ids=CLAUSES,
        mutation_outcomes=killed_all(bundle),
        regression_scenarios=regression_all_green(bundle),
    )
    assert report.assertion_rate == 1.0


def test_clause_coverage_is_measured_not_assumed(bundle):
    report = OracleAuditor().audit(bundle, clause_ids=CLAUSES)
    assert report.clause_coverage == 1.0

    partial = OracleAuditor().audit(bundle, clause_ids=[*CLAUSES, "L2-X-999"])
    assert partial.clause_coverage == pytest.approx(2 / 3)


def test_properties_and_relations_count_towards_coverage(bundle):
    """A clause witnessed by a property is covered even with no scenario:
    otherwise teams write redundant scenarios purely to satisfy the metric."""

    holdout: HoldoutOracle = bundle.holdout.model_copy(
        update={"scenarios": [bundle.holdout.scenarios[1]]}
    )
    trimmed = OracleBundle(
        bundle_id=bundle.bundle_id,
        unit_id=bundle.unit_id,
        spec_version=bundle.spec_version,
        public=bundle.public,
        holdout=holdout,
    )
    report = OracleAuditor().audit(trimmed, clause_ids=CLAUSES)
    assert report.clause_coverage == 1.0


# ----------------------------------------------------------- probe running


def test_run_mutation_probes_records_who_killed_each_probe(bundle):
    def runner(probe):
        return ["H2"] if probe.id == "MP-ROUND" else []

    outcomes = run_mutation_probes(bundle.holdout.mutation_probes, runner)
    by_id = {o.probe_id: o for o in outcomes}
    assert by_id["MP-ROUND"].killed
    assert by_id["MP-ROUND"].killed_by == ("H2",)
    assert not by_id["MP-CURRENCY"].killed


def test_a_probe_killed_by_the_wrong_gate_does_not_count(bundle):
    """``must_be_caught_by`` is part of the contract: if the currency probe is
    only caught by a linter, the holdout scenarios still do not cover it."""

    def runner(probe):
        return ["H1"]

    outcomes = run_mutation_probes(bundle.holdout.mutation_probes, runner)
    assert all(not o.killed for o in outcomes)


def test_a_probe_caught_by_a_superset_of_gates_counts(bundle):
    def runner(probe):
        return ["H1", "H2", "H3"]

    outcomes = run_mutation_probes(bundle.holdout.mutation_probes, runner)
    assert all(o.killed for o in outcomes)


def test_mutation_score_is_a_fraction(bundle):
    outcomes = killed_all(bundle)
    outcomes[0] = MutationOutcome(probe_id=outcomes[0].probe_id, killed=False)
    report = OracleAuditor().audit(
        bundle,
        clause_ids=CLAUSES,
        mutation_outcomes=outcomes,
        regression_scenarios=regression_all_green(bundle),
    )
    assert report.mutation_score == pytest.approx(0.5)


# ------------------------------------------------------------- thresholds


def test_thresholds_are_configurable_but_default_to_strict():
    strict = OracleAuditor()
    assert strict.min_clause_coverage == 1.0
    assert strict.min_mutation_score == 1.0


def test_a_relaxed_auditor_can_be_used_during_migration(bundle):
    """M1/M2 need a documented way to run below full strength; the point is that
    it is a named threshold in the report, not an undocumented tolerance."""

    outcomes = killed_all(bundle)
    outcomes[0] = MutationOutcome(probe_id=outcomes[0].probe_id, killed=False)
    lenient = OracleAuditor(min_mutation_score=0.5)
    report = lenient.audit(
        bundle,
        clause_ids=CLAUSES,
        mutation_outcomes=outcomes,
        regression_scenarios=regression_all_green(bundle),
    )
    assert report.grade is OracleGrade.DIAMOND
    assert report.surviving_probes
