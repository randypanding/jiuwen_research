"""Golden records for R3 units.

The load-bearing claim, and the one most often got wrong in practice: a golden
file is a *regression guard*, not a correctness proof. It says "this behaves
like it did yesterday", which is worthless if yesterday was wrong. So the store
enforces two things the plan depends on — CI can never write a golden, and an R3
unit must carry an independent oracle alongside its goldens.
"""

from __future__ import annotations

import pytest

from swarmkernel.contracts.base import digest_of
from swarmkernel.contracts.oracle import GoldenRecord, MetamorphicRelation
from swarmkernel.oracle.golden import (
    GoldenMode,
    GoldenStore,
    GoldenStoreWriteError,
    GoldenSuite,
    R3Info,
    capture_r3info,
)

ENV_A = R3Info(
    python_version="3.12.3",
    platform_machine="x86_64",
    platform_system="Linux",
    timezone="UTC",
    locale="C",
    source_date_epoch="0",
    dependency_digest="sha256:deps-a",
)
ENV_B = R3Info(
    python_version="3.13.1",
    platform_machine="x86_64",
    platform_system="Linux",
    timezone="UTC",
    locale="C",
    source_date_epoch="0",
    dependency_digest="sha256:deps-a",
)


def record(gid: str, value) -> GoldenRecord:
    return GoldenRecord(
        id=gid,
        unit_id="UNIT-CART",
        entrypoint="cart.total",
        input_digest=digest_of({"lines": [{"price": "5.00", "qty": 2}]}),
        observation_digest=digest_of(value),
        frozen_at_version="1.2.0",
    )


# --------------------------------------------------------------- mode lock


def test_compare_mode_cannot_write():
    """The single most important property: a green CI run must never be
    achievable by rewriting the expectation."""

    store = GoldenStore([record("G1", "10.00")])
    with pytest.raises(GoldenStoreWriteError, match="compare mode"):
        store.put(record("G2", "20.00"))


def test_compare_mode_cannot_supersede():
    store = GoldenStore([record("G1", "10.00")])
    with pytest.raises(GoldenStoreWriteError, match="compare mode"):
        store.supersede("G1", record("G1b", "20.00"), reason="drift")


def test_regenerate_mode_requires_human_authorisation():
    with pytest.raises(GoldenStoreWriteError, match="authorisation"):
        GoldenStore([], mode=GoldenMode.REGENERATE)


def test_authorised_regeneration_is_allowed():
    store = GoldenStore([], mode=GoldenMode.REGENERATE, authorisation="approved-by:alice#PR-42")
    store.put(record("G1", "10.00"))
    assert store.get("G1") is not None


def test_goldens_are_append_only():
    store = GoldenStore(
        [record("G1", "10.00")], mode=GoldenMode.REGENERATE, authorisation="ok"
    )
    with pytest.raises(GoldenStoreWriteError, match="append-only"):
        store.put(record("G1", "99.00"))


def test_supersede_keeps_the_history_and_redirects():
    store = GoldenStore(
        [record("G1", "10.00")], mode=GoldenMode.REGENERATE, authorisation="ok"
    )
    store.supersede("G1", record("G1b", "11.00"), reason="rounding rule changed in L2")
    assert store.get("G1").id == "G1b"


# --------------------------------------------------------------- comparison


def test_matching_observation_passes():
    store = GoldenStore([record("G1", "10.00")])
    assert store.compare("G1", "10.00").matched


def test_differing_observation_fails():
    store = GoldenStore([record("G1", "10.00")])
    result = store.compare("G1", "10.01")
    assert not result.matched
    assert result.expected_digest != result.actual_digest


def test_missing_golden_fails_rather_than_passes():
    """Deleting a golden must not be the cheapest way to green the build."""

    store = GoldenStore([])
    result = store.compare("G-NOPE", "anything")
    assert not result.matched
    assert "no golden" in result.message.lower() or "missing" in result.message.lower()


def test_environment_drift_is_reported_but_never_auto_passes():
    """"The world changed" is a hypothesis for a human, not an excuse the gate
    may grant itself."""

    store = GoldenStore([record("G1", "10.00")], environments={"G1": ENV_A})
    result = store.compare("G1", "10.01", actual_env=ENV_B)
    assert not result.matched
    assert result.is_environment_suspect
    assert any("python_version" in d for d in result.environment_drift)


def test_environment_drift_alone_does_not_fail_a_matching_golden():
    store = GoldenStore([record("G1", "10.00")], environments={"G1": ENV_A})
    result = store.compare("G1", "10.00", actual_env=ENV_B)
    assert result.matched
    assert not result.is_environment_suspect


def test_r3info_diff_lists_every_changed_axis():
    assert ENV_A.diff(ENV_A) == []
    assert len(ENV_B.diff(ENV_A)) == 1


def test_r3info_digest_is_stable():
    assert ENV_A.digest() == ENV_A.digest()
    assert ENV_A.digest() != ENV_B.digest()


def test_capture_r3info_records_the_live_environment():
    info = capture_r3info(dependency_digest="sha256:x", build_id="42")
    assert info.python_version
    assert info.dependency_digest == "sha256:x"
    assert info.extra["build_id"] == "42"


# ------------------------------------------------------- the dual-track rule


def test_goldens_without_an_independent_oracle_are_rejected():
    """Research conclusion adopted verbatim: goldens freeze behaviour, they do
    not justify it. An R3 unit whose only evidence is "same as last time" can
    never discover that last time was wrong."""

    suite = GoldenSuite(unit_id="UNIT-CART", goldens=[record("G1", "10.00")])
    problems = suite.validate()
    assert problems
    assert any("regression guards" in p for p in problems)


def test_a_metamorphic_relation_satisfies_the_independence_requirement():
    suite = GoldenSuite(
        unit_id="UNIT-CART",
        goldens=[record("G1", "10.00")],
        independent_relations=[
            MetamorphicRelation(
                id="MR-PERMUTE",
                clause_ids=["L2-CART.TOTAL-001"],
                entrypoint="cart.total",
                transform="permute(lines)",
                relation="output_equal",
            )
        ],
    )
    assert suite.validate() == []


def test_a_reference_implementation_also_satisfies_it():
    suite = GoldenSuite(
        unit_id="UNIT-CART",
        goldens=[record("G1", "10.00")],
        reference_impl_ref="legacy.cart:total",
    )
    assert suite.validate() == []


def test_a_round_trip_property_also_satisfies_it():
    suite = GoldenSuite(
        unit_id="UNIT-CART",
        goldens=[record("G1", "10.00")],
        round_trip_property="parse(render(x)) == x",
    )
    assert suite.validate() == []


def test_an_r3_unit_with_no_goldens_is_rejected():
    suite = GoldenSuite(unit_id="UNIT-CART", round_trip_property="p")
    assert any("no frozen goldens" in p for p in suite.validate())


def test_duplicate_golden_ids_are_rejected():
    suite = GoldenSuite(
        unit_id="UNIT-CART",
        goldens=[record("G1", "10.00"), record("G1", "11.00")],
        round_trip_property="p",
    )
    assert any("duplicate golden id" in p for p in suite.validate())
