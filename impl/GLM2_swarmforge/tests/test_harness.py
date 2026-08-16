"""角色装配与档位测试：宪法投影（INV5/6/13/14）、提案通道（INV6/8）。"""
import pytest

from swarmforge.constitution import ConstitutionViolation
from swarmforge.harness import (
    MEMORY_WRITE_RAILS,
    ModelTier,
    ProposalBook,
    RoleSpec,
    RuleChangeProposal,
    TierAssignment,
    builder_role,
    build_team_spec_fragment,
    validate_role,
    validate_tier_assignment,
    verifier_role,
)


class TestRoleValidation:
    def test_builder_role_valid(self):
        validate_role(builder_role())  # 不抛即通过

    def test_inv13_builder_memory_write_rejected(self):
        bad = RoleSpec(role="builder", bus_role="builder", memory_writable=True)
        with pytest.raises(ConstitutionViolation) as ei:
            validate_role(bad)
        assert ei.value.inv_id == "INV13"

    def test_inv13_builder_evolution_rail_rejected(self):
        bad = RoleSpec(role="builder", bus_role="builder",
                       rails=MEMORY_WRITE_RAILS)
        with pytest.raises(ConstitutionViolation) as ei:
            validate_role(bad)
        assert ei.value.inv_id == "INV13"

    def test_inv5_builder_judge_tool_leak_rejected(self):
        bad = RoleSpec(role="builder", bus_role="builder",
                       tools={"holdout.read", "write_file"})
        with pytest.raises(ConstitutionViolation) as ei:
            validate_role(bad)
        assert ei.value.inv_id == "INV5"

    def test_inv6_adjudicator_evolution_rail_rejected(self):
        bad = RoleSpec(role="verifier", bus_role="verifier", lifecycle="persistent",
                       rails={"swarm.member_skill_evolution"})
        with pytest.raises(ConstitutionViolation) as ei:
            validate_role(bad)
        assert ei.value.inv_id == "INV6"

    def test_inv6_adjudicator_must_be_persistent(self):
        bad = RoleSpec(role="verifier", bus_role="verifier", lifecycle="temporary")
        with pytest.raises(ConstitutionViolation) as ei:
            validate_role(bad)
        assert ei.value.inv_id == "INV6"

    def test_verifier_role_valid(self):
        validate_role(verifier_role())


class TestTierPolicy:
    def test_inv14_judge_below_builder_rejected(self):
        with pytest.raises(ConstitutionViolation) as ei:
            validate_tier_assignment(TierAssignment(
                role="verifier", builder_tier=ModelTier.RU_H, judge_tier=ModelTier.RU_M))
        assert ei.value.inv_id == "INV14"

    def test_equal_tiers_allowed(self):
        validate_tier_assignment(TierAssignment(
            role="verifier", builder_tier=ModelTier.RU_M, judge_tier=ModelTier.RU_M))

    def test_role_floors(self):
        from swarmforge.harness import role_floor
        assert role_floor("cartographer", "generation") == ModelTier.RU_L
        assert role_floor("architect", "generation") == ModelTier.RU_H


class TestTeamSpecFragment:
    MODELS = {
        "RU-L": [{"name": "qwen3-30b", "provider": "openai"}],
        "RU-M": [{"name": "qwen3-max", "provider": "openai"}],
        "RU-H": [{"name": "glm-5", "provider": "openai"}],
    }

    def test_fragment_contains_role_constraints(self):
        frag = build_team_spec_fragment(
            [builder_role(), verifier_role()], models_by_tier=self.MODELS)
        members = {m["member_name"]: m for m in frag["predefined_members"]}
        assert members["builder"]["options"]["lifecycle"] == "temporary"
        assert members["builder"]["options"]["memory_writable"] is False
        assert members["builder"]["options"]["worktree_isolation"] == "worktree"
        assert "holdout.read" not in members["builder"]["options"]["tools_allowlist"]

    def test_invalid_member_rejected_at_build(self):
        bad = RoleSpec(role="builder", bus_role="builder", memory_writable=True)
        with pytest.raises(ConstitutionViolation):
            build_team_spec_fragment([bad], models_by_tier=self.MODELS)


class TestProposalChannel:
    def test_same_session_effective_rejected(self, tmp_path):
        book = ProposalBook(str(tmp_path / "p.jsonl"))
        p = RuleChangeProposal(proposal_id="P1", kind="tier_policy",
                               summary="cartographer 升 RU-M",
                               effective_from_session="S1")
        with pytest.raises(ConstitutionViolation) as ei:
            book.submit(p, current_session="S1")
        assert ei.value.inv_id == "INV6"

    def test_later_session_effective_ok(self, tmp_path):
        book = ProposalBook(str(tmp_path / "p.jsonl"))
        p = RuleChangeProposal(proposal_id="P1", kind="tier_policy",
                               summary="x", effective_from_session="S2")
        book.submit(p, current_session="S1")
        book.decide("P1", approved=True)
        assert book.effective_for("S2") and not book.effective_for("S1")
        # 提交 session 内绝不生效
        assert all(p.status == "approved" for p in book.all())

    def test_pending_not_effective(self, tmp_path):
        book = ProposalBook(str(tmp_path / "p.jsonl"))
        book.submit(RuleChangeProposal(proposal_id="P2", kind="gate_threshold",
                                       summary="y", effective_from_session="S9"),
                    current_session="S1")
        assert book.effective_for("S9") == []  # 未批准不装载

    def test_rejected_proposal_stays_rejected(self, tmp_path):
        book = ProposalBook(str(tmp_path / "p.jsonl"))
        book.submit(RuleChangeProposal(proposal_id="P3", kind="rubric", summary="z",
                                       effective_from_session="S2"),
                    current_session="S1")
        book.decide("P3", approved=False)
        assert book.effective_for("S5") == []
