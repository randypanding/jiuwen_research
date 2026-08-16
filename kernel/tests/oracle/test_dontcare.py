"""Don't-care semantics.

The central claim of PDR-001 §4 is that "unspecified" and "undefined" are
different things and that conflating them poisons every downstream verdict. A
mask that silently treats an unnormalised channel as identity would re-introduce
exactly that conflation, so these tests pin the closed normalizer set.
"""

from __future__ import annotations

import pytest

from swarmkernel.contracts.spec import DontCareCategory, DontCareRegion, FreedomTrack
from swarmkernel.oracle.dontcare import (
    NORMALIZERS,
    DontCareMask,
    Selector,
    normalize_observation,
)


def region(
    rid: str,
    selectors: list[str],
    normalizer: str | None = "sort_list",
    track: FreedomTrack = FreedomTrack.UNSPECIFIED,
    category: DontCareCategory = DontCareCategory.OUTPUT_FREEDOM,
) -> DontCareRegion:
    return DontCareRegion(
        id=rid,
        category=category,
        track=track,
        description=rid,
        selectors=selectors,
        normalizer=normalizer,
        justification_clause_ids=["L2-CART.TOTAL-001"],
    )


# ------------------------------------------------------------------ selectors


def test_selector_matches_its_own_channel():
    sel = Selector("return.breakdown")
    assert sel.matches_channel("return")
    assert not sel.matches_channel("stdout")


def test_selector_matches_nested_paths():
    sel = Selector("return.breakdown")
    assert sel.matches_path(["breakdown"])
    assert not sel.matches_path(["total"])


def test_wildcard_selector_matches_any_leaf():
    sel = Selector("log.*")
    assert sel.matches_path(["anything"])
    assert sel.matches_path(["a", "b"])


# ------------------------------------------------------------------ masking


def test_ordering_freedom_makes_two_orders_equal(dont_care_order):
    mask = DontCareMask([dont_care_order])
    a, hit_a = mask.apply("return", {"total": "10.00", "breakdown": ["x", "y"]})
    b, hit_b = mask.apply("return", {"total": "10.00", "breakdown": ["y", "x"]})
    assert a == b
    assert hit_a == hit_b == {"DC-LINE-ORDER"}


def test_masking_does_not_hide_a_real_difference(dont_care_order):
    mask = DontCareMask([dont_care_order])
    a, _ = mask.apply("return", {"total": "10.00", "breakdown": ["x"]})
    b, _ = mask.apply("return", {"total": "11.00", "breakdown": ["x"]})
    assert a != b


def test_covering_region_names_the_region_that_forgave_the_difference(dont_care_order):
    mask = DontCareMask([dont_care_order])
    covered = mask.covering_region(
        "return",
        {"total": "10.00", "breakdown": ["x", "y"]},
        {"total": "10.00", "breakdown": ["y", "x"]},
    )
    assert covered == "DC-LINE-ORDER"


def test_covering_region_is_none_for_a_real_divergence(dont_care_order):
    mask = DontCareMask([dont_care_order])
    assert (
        mask.covering_region(
            "return",
            {"total": "10.00", "breakdown": ["x"]},
            {"total": "11.00", "breakdown": ["x"]},
        )
        is None
    )


def test_unmasked_channel_passes_through_untouched(dont_care_order):
    mask = DontCareMask([dont_care_order])
    value = {"total": "10.00"}
    out, hits = mask.apply("stdout", value)
    assert out == value
    assert hits == set()


def test_normalize_observation_without_mask_is_identity():
    assert normalize_observation("return", {"a": 1}, None) == {"a": 1}


# -------------------------------------------------------- the closed set


def test_normalizer_set_is_closed():
    """An open normalizer set would let a team define ``identity`` for a region
    that actually varies, quietly turning a defect into a don't-care."""

    with pytest.raises(ValueError, match="unknown normalizer"):
        DontCareMask([region("DC-X", ["return.x"], normalizer="eval:whatever")])


def test_every_declared_normalizer_is_implemented():
    for name in (
        "identity",
        "sort_list",
        "drop",
        "round:3",
        "round:6",
        "round:9",
        "mask_uuid",
        "mask_timestamp",
        "mask_address",
        "strip_whitespace",
        "exception_type_only",
    ):
        assert name in NORMALIZERS


def test_drop_replaces_the_value_with_a_visible_placeholder():
    """Erasing the key would change the shape of the observation; replacing it
    keeps diffs readable and makes the freedom visible in the report."""

    mask = DontCareMask([region("DC-TS", ["return.timestamp"], normalizer="drop")])
    out, hits = mask.apply("return", {"total": "1", "timestamp": "2026-01-01"})
    assert out == {"total": "1", "timestamp": "<don't-care>"}
    assert hits == {"DC-TS"}


def test_rounding_absorbs_float_noise():
    mask = DontCareMask([region("DC-F", ["return.score"], normalizer="round:3")])
    a, _ = mask.apply("return", {"score": 0.1234567})
    b, _ = mask.apply("return", {"score": 0.1234891})
    assert a == b


def test_identity_normalizer_masks_nothing():
    """``identity`` is legal but must be inert: declaring a region and getting
    silent equality for free is the failure mode this guards."""

    mask = DontCareMask([region("DC-ID", ["return.x"], normalizer="identity")])
    assert mask.covering_region("return", {"x": 1}, {"x": 2}) is None


# ------------------------------------------------------------------- tracks


def test_undefined_and_unspecified_are_not_interchangeable():
    """§4: ``undefined`` means the spec is stuck (a bug in the spec), whereas
    ``unspecified`` is deliberate freedom. Only the latter may forgive a diff."""

    stuck = region("DC-STUCK", ["return.x"], normalizer=None, track=FreedomTrack.UNDEFINED)
    mask = DontCareMask([stuck])
    assert mask.covering_region("return", {"x": 1}, {"x": 2}) is None


def test_unspecified_track_does_forgive():
    free = region("DC-FREE", ["return.x"], normalizer="drop", track=FreedomTrack.UNSPECIFIED)
    mask = DontCareMask([free])
    assert mask.covering_region("return", {"x": 1}, {"x": 2}) == "DC-FREE"


def test_region_must_select_something():
    """A freedom that selects nothing is a freedom that is declared and not
    honoured -- the worst of both worlds, so it cannot be constructed."""

    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="covers nothing"):
        region("DC-Z", [])


def test_an_undefined_region_may_not_carry_a_normalizer():
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="silently legalise"):
        region("DC-W", ["return.x"], normalizer="drop", track=FreedomTrack.UNDEFINED)


@pytest.mark.parametrize("category", list(DontCareCategory))
def test_all_three_categories_are_usable(category):
    mask = DontCareMask([region("DC-C", ["return.x"], normalizer="drop", category=category)])
    out, hits = mask.apply("return", {"x": 1})
    assert out == {"x": "<don't-care>"}
    assert hits == {"DC-C"}
