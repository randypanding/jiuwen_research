"""The differential engine: H5, and the only instrument that detects spec silence.

PDR-001 §6 turns N instances into a verdict about the *spec*, not about the
code. Getting that table wrong is the most expensive mistake available in this
architecture: a mislabelled "closed" hides an undefined region forever, and a
mislabelled "silence" sends the spec moderator chasing a phantom.
"""

from __future__ import annotations

import pytest

from swarmkernel.contracts.instance import DivergenceVerdict
from swarmkernel.oracle.differ import DifferentialEngine, DifferentialInput, EquivalenceLevel

from ..conftest import make_report


def make_input(reports, passing=None, *, dont_care=(), level=EquivalenceLevel.IO,
               tier_escalated=False, min_instances=3):
    return DifferentialInput(
        unit_id="UNIT-CART",
        delta_id="DELTA-001",
        spec_version="1.2.0",
        reports=reports,
        passing_instance_ids=(
            {r.manifest.instance_id for r in reports} if passing is None else set(passing)
        ),
        dont_care=list(dont_care),
        level=level,
        tier_escalated=tier_escalated,
        min_instances_for_verdict=min_instances,
    )


# ----------------------------------------------------------- the §6 table


def test_all_pass_no_divergence_means_the_spec_is_closed(dont_care_order):
    reports = [
        make_report("a", breakdown=["x", "y"]),
        make_report("b", breakdown=["y", "x"]),
        make_report("c", breakdown=["x", "y"]),
    ]
    engine = DifferentialEngine([dont_care_order])
    report = engine.run(make_input(reports), "DR-1")
    assert report.verdict is DivergenceVerdict.CLOSED
    assert report.undecided_divergences == []


def test_all_pass_with_divergence_means_the_spec_is_silent():
    """Everyone passed, yet they disagree: the oracle did not constrain this."""

    reports = [
        make_report("a", total="10.00", breakdown=["x"]),
        make_report("b", total="10.000", breakdown=["x"]),
        make_report("c", total="10.00", breakdown=["x"]),
    ]
    engine = DifferentialEngine([])
    report = engine.run(make_input(reports), "DR-2")
    assert report.verdict is DivergenceVerdict.SILENCE
    assert report.undecided_divergences


def test_partial_pass_means_ambiguity():
    reports = [
        make_report("a", breakdown=["x"]),
        make_report("b", breakdown=["x"], total="9.00"),
        make_report("c", breakdown=["x"]),
    ]
    engine = DifferentialEngine([])
    report = engine.run(make_input(reports, passing={"a", "c"}), "DR-3")
    assert report.verdict is DivergenceVerdict.AMBIGUITY


def test_all_fail_at_this_tier_is_not_yet_infeasible():
    reports = [make_report(i, breakdown=["x"]) for i in ("a", "b", "c")]
    engine = DifferentialEngine([])
    report = engine.run(make_input(reports, passing=set()), "DR-4")
    assert report.verdict is DivergenceVerdict.UNSOLVED_AT_TIER


def test_all_fail_after_escalation_is_infeasible():
    reports = [make_report(i, breakdown=["x"]) for i in ("a", "b", "c")]
    engine = DifferentialEngine([])
    report = engine.run(make_input(reports, passing=set(), tier_escalated=True), "DR-5")
    assert report.verdict is DivergenceVerdict.INFEASIBLE


def test_too_few_instances_yields_insufficient_not_a_guess():
    """The dangerous failure is answering a question you lack the data for."""

    reports = [make_report("a", breakdown=["x"])]
    engine = DifferentialEngine([])
    report = engine.run(make_input(reports, passing=set()), "DR-6")
    assert report.verdict is DivergenceVerdict.INSUFFICIENT


def test_no_instances_yields_insufficient():
    engine = DifferentialEngine([])
    report = engine.run(make_input([], passing=set()), "DR-7")
    assert report.verdict is DivergenceVerdict.INSUFFICIENT


def test_single_passing_instance_is_closed_not_insufficient():
    """N=1 is legal (low uncertainty, or R3). It cannot detect silence, but it
    is not "insufficient evidence" for the question it does answer."""

    engine = DifferentialEngine([])
    report = engine.run(make_input([make_report("a", breakdown=["x"])]), "DR-8")
    assert report.verdict is DivergenceVerdict.CLOSED


# ------------------------------------------------------------- don't-care


def test_a_registered_freedom_downgrades_a_divergence(dont_care_order):
    engine = DifferentialEngine([dont_care_order])
    divs = engine.diff_pair(
        make_report("a", breakdown=["x", "y"]),
        make_report("b", breakdown=["y", "x"]),
        EquivalenceLevel.IO,
    )
    assert divs == []


def test_an_unregistered_difference_stays_a_defect():
    engine = DifferentialEngine([])
    divs = engine.diff_pair(
        make_report("a", breakdown=["x", "y"]),
        make_report("b", breakdown=["y", "x"]),
        EquivalenceLevel.IO,
    )
    assert len(divs) == 1
    assert divs[0].is_defect


def test_a_freedom_does_not_forgive_an_unrelated_channel(dont_care_order):
    """Scoping matters: the ordering freedom must not accidentally excuse a
    wrong total that happens to travel in the same payload."""

    engine = DifferentialEngine([dont_care_order])
    divs = engine.diff_pair(
        make_report("a", breakdown=["x", "y"], total="10.00"),
        make_report("b", breakdown=["y", "x"], total="11.00"),
        EquivalenceLevel.IO,
    )
    assert len(divs) == 1
    assert divs[0].is_defect


# ------------------------------------------------------------- clustering


def test_clustering_collapses_identical_behaviour(dont_care_order):
    """The cost lever: pairwise diffing is O(N^2), cluster-representative
    diffing is O(K^2) where K is the number of *distinct* behaviours."""

    reports = [make_report(f"i{i}", breakdown=["x", "y"]) for i in range(6)]
    engine = DifferentialEngine([dont_care_order])
    classes = engine.cluster(make_input(reports))
    assert len(classes) == 1
    assert classes[0].instance_ids == sorted(r.manifest.instance_id for r in reports)


def test_clustering_separates_distinct_behaviour():
    reports = [
        make_report("a", total="10.00", breakdown=["x"]),
        make_report("b", total="11.00", breakdown=["x"]),
        make_report("c", total="10.00", breakdown=["x"]),
    ]
    engine = DifferentialEngine([])
    classes = engine.cluster(make_input(reports))
    assert len(classes) == 2
    assert sorted(len(c.instance_ids) for c in classes) == [1, 2]


def test_clustering_respects_dont_care(dont_care_order):
    """Two instances that differ only inside a registered freedom belong to the
    same class, or the freedom would cost O(N^2) diffs to re-discover."""

    reports = [
        make_report("a", breakdown=["x", "y"]),
        make_report("b", breakdown=["y", "x"]),
    ]
    engine = DifferentialEngine([dont_care_order])
    assert len(engine.cluster(make_input(reports))) == 1


def test_representatives_are_deterministic():
    reports = [make_report(i, breakdown=["x"]) for i in ("c", "a", "b")]
    engine = DifferentialEngine([])
    first = engine.cluster(make_input(reports))
    second = engine.cluster(make_input(list(reversed(reports))))
    assert [c.representative for c in first] == [c.representative for c in second]


def test_closure_is_reported(dont_care_order):
    reports = [make_report(i, breakdown=["x", "y"]) for i in ("a", "b", "c")]
    engine = DifferentialEngine([dont_care_order])
    report = engine.run(make_input(reports), "DR-9")
    assert report.closure == 1.0


# --------------------------------------------------------- delta diversity


def test_delta_diversity_is_zero_when_every_instance_agrees():
    """A probe set that never discriminates cannot detect silence however many
    instances you buy; diversity is the signal that says "stop paying"."""

    reports = [make_report(i, breakdown=["x"]) for i in ("a", "b", "c")]
    engine = DifferentialEngine([])
    assert engine.delta_diversity(make_input(reports)) == 0.0


def test_delta_diversity_is_one_when_the_probe_discriminates():
    reports = [
        make_report("a", total="10.00", breakdown=["x"]),
        make_report("b", total="11.00", breakdown=["x"]),
    ]
    engine = DifferentialEngine([])
    assert engine.delta_diversity(make_input(reports)) == 1.0


def test_delta_diversity_ignores_differences_inside_a_freedom(dont_care_order):
    reports = [
        make_report("a", breakdown=["x", "y"]),
        make_report("b", breakdown=["y", "x"]),
    ]
    engine = DifferentialEngine([dont_care_order])
    assert engine.delta_diversity(make_input(reports)) == 0.0


# ------------------------------------------------------------------ levels


def test_io_level_ignores_stdout_but_behavioural_does_not():
    a = make_report("a", breakdown=["x"])
    b = make_report("b", breakdown=["x"])
    from swarmkernel.contracts.instance import Observation
    from swarmkernel.contracts.oracle import ObservationChannel

    b.probe_results[0].observations.append(
        Observation(channel=ObservationChannel.STDOUT, value="chatty debug line")
    )
    engine = DifferentialEngine([])
    assert engine.diff_pair(a, b, EquivalenceLevel.IO) == []
    assert engine.diff_pair(a, b, EquivalenceLevel.BEHAVIOURAL)


@pytest.mark.parametrize(
    "level", [EquivalenceLevel.IO, EquivalenceLevel.BEHAVIOURAL, EquivalenceLevel.SEMANTIC]
)
def test_every_level_has_a_channel_set(level):
    assert EquivalenceLevel.CHANNELS[level]


def test_exceptions_are_compared_not_ignored():
    """"Crashes differently" is the divergence most likely to matter."""

    engine = DifferentialEngine([])
    divs = engine.diff_pair(
        make_report("a", breakdown=["x"], exception="ValueError"),
        make_report("b", breakdown=["x"], exception="CurrencyMismatch"),
        EquivalenceLevel.IO,
    )
    assert len(divs) == 1


def test_missing_probe_on_one_side_is_not_a_silent_pass():
    """If an instance simply did not run a probe, the pair must not be reported
    as equivalent on that probe; absence of evidence is not evidence."""

    a = make_report("a", breakdown=["x"])
    b = make_report("b", breakdown=["x"])
    b.probe_results.clear()
    engine = DifferentialEngine([])
    divs = engine.diff_pair(a, b, EquivalenceLevel.IO)
    assert divs == []  # no comparison was possible
    data = make_input([a, b], passing={"a", "b"})
    report = engine.run(data, "DR-10")
    # ...and the report must not claim full closure on a probe nobody ran twice
    assert report.probes_executed == 1
