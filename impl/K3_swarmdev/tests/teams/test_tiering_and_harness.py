import pytest
from pydantic import ValidationError

from swarmdev.contracts import Role
from swarmdev.teams.harness_map import HARNESS_BINDINGS
from swarmdev.teams.tiering import ModelTier, TierAssignment, TierPolicyError


def test_judge_tier_must_not_be_weaker_than_builder():
    with pytest.raises((TierPolicyError, ValidationError)):
        TierAssignment(builder=ModelTier.M, judge=ModelTier.L)
    ok = TierAssignment(builder=ModelTier.M, judge=ModelTier.H)
    assert ok.judge.rank >= ok.builder.rank


def test_verifier_tier_must_not_be_weaker_than_builder():
    with pytest.raises((TierPolicyError, ValidationError)):
        TierAssignment(builder=ModelTier.H, verifier=ModelTier.M, judge=ModelTier.H)


def test_harness_bindings_cover_all_agent_roles():
    missing = {r for r in Role if r != Role.HUMAN} - set(HARNESS_BINDINGS)
    assert not missing
    builder = HARNESS_BINDINGS[Role.BUILDER]
    assert builder["lifecycle"] == "temporary"
    for role, binding in HARNESS_BINDINGS.items():
        assert binding["carrier"], role
        assert "notes" in binding, role
