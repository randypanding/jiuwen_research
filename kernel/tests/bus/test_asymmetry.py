"""Information asymmetry, tested as an attack surface.

PDR-001 §7 claims that the builder cannot see the holdout, that generators never
judge, and that temporary workers leave no trace. Those are security claims, and
security claims are only worth what their negative tests are worth. Every test
below is an attempted violation that must fail.

The framing matters: these are not "the policy table says X" tests (which would
merely restate the table), they are "the attack does not work" tests.
"""

from __future__ import annotations

import pytest

from swarmkernel.bus import ContractBus, DeliveryError, seal
from swarmkernel.bus.policy import AsymmetryPolicy, Capability
from swarmkernel.contracts.base import ArtifactClass, Role
from swarmkernel.contracts.gate import JudgeSample, SoftGateResult, SoftVerdict


def _sink(_env, _contract) -> None:  # pragma: no cover - trivial
    pass


# --------------------------------------------------- the holdout is invisible


def test_builder_cannot_even_subscribe_to_the_holdout():
    """The leak is refused at wiring time, not at delivery time.

    Catching it at delivery would mean a mis-wired swarm looks healthy until the
    first holdout is published; catching it at subscribe makes it a startup
    crash that no test run can miss.
    """

    bus = ContractBus()
    with pytest.raises(DeliveryError, match="cannot subscribe"):
        bus.subscribe("builder", Role.BUILDER, [ArtifactClass.ORACLE_HOLDOUT], _sink)


@pytest.mark.parametrize(
    "role",
    [Role.BUILDER, Role.REFACTOR, Role.RECONCILER, Role.CRITIC],
)
def test_no_generating_role_can_read_the_holdout(role):
    policy = AsymmetryPolicy()
    assert not policy.can_read(role, ArtifactClass.ORACLE_HOLDOUT).allowed


def test_builder_cannot_publish_a_holdout_it_forged(holdout_oracle):
    bus = ContractBus()
    with pytest.raises(DeliveryError, match="no write capability"):
        bus.publish(
            seal(
                message_id="m1",
                contract=holdout_oracle,
                sender_role=Role.BUILDER,
                sender_identity="builder",
            )
        )


def test_holdout_never_appears_in_the_builder_view(holdout_oracle, public_oracle):
    """``View(builder) ∩ View(verifier) ⊆ public`` — the actual §7 predicate,
    asserted over what was really delivered rather than over intentions."""

    bus = ContractBus()
    seen_b: list = []
    seen_v: list = []
    bus.subscribe(
        "builder",
        Role.BUILDER,
        [ArtifactClass.ORACLE_PUBLIC],
        lambda e, c: seen_b.append(c),
    )
    bus.subscribe(
        "verifier",
        Role.VERIFIER,
        [ArtifactClass.ORACLE_PUBLIC, ArtifactClass.ORACLE_HOLDOUT],
        lambda e, c: seen_v.append(c),
    )
    env_public, env_holdout = (
        seal(
            message_id=f"m{i}",
            contract=art,
            sender_role=Role.VERIFIER,
            sender_identity="verifier",
        )
        for i, art in enumerate((public_oracle, holdout_oracle))
    )
    bus.publish(env_public)
    bus.publish(env_holdout)

    shared = bus.view_of("builder") & bus.view_of("verifier")
    assert shared == {env_public.payload_digest}
    assert env_holdout.payload_digest not in bus.view_of("builder")
    assert "builder" not in bus.who_saw(ArtifactClass.ORACLE_HOLDOUT)
    assert seen_b == [public_oracle]
    assert seen_v == [public_oracle, holdout_oracle]


def test_the_refusal_is_recorded_not_silent(holdout_oracle):
    """A leak attempt that leaves no trace is indistinguishable from a leak."""

    bus = ContractBus()
    bus.subscribe("verifier", Role.VERIFIER, [ArtifactClass.ORACLE_HOLDOUT], _sink)
    try:
        bus.publish(
            seal(
                message_id="m1",
                contract=holdout_oracle,
                sender_role=Role.BUILDER,
                sender_identity="builder",
            )
        )
    except DeliveryError:
        pass
    assert any("no write capability" in r.reason for r in bus.refusals())


# ------------------------------------------------ generators never judge


def test_a_builder_cannot_wear_the_judge_hat():
    policy = AsymmetryPolicy()
    assert not policy.can_write(Role.BUILDER, ArtifactClass.JUDGE_VERDICT).allowed
    assert not policy.can_read(Role.BUILDER, ArtifactClass.JUDGE_VERDICT).allowed


def test_judge_cannot_review_its_own_output():
    """Same *identity* on both ends of a verdict is self-review even when the
    roles differ, so separation is checked on identity, not only on role."""

    policy = AsymmetryPolicy()
    decision = policy.check_separation(
        sender_role=Role.JUDGE,
        sender_identity="agent-7",
        recipient_role=Role.JUDGE,
        recipient_identity="agent-7",
        artifact=ArtifactClass.JUDGE_VERDICT,
        subject_identity="agent-7",
    )
    assert not decision.allowed
    assert "self" in decision.reason.lower()


def test_a_judge_verdict_about_oneself_is_refused_at_send():
    """Refused before fan-out, so the verdict never exists on the bus at all."""

    bus = ContractBus()
    got: list = []
    bus.subscribe("agent-7", Role.JUDGE, [ArtifactClass.JUDGE_VERDICT], lambda e, c: got.append(c))
    verdict = SoftGateResult(
        verdict=SoftVerdict.NO_VETO,
        samples=[JudgeSample(criterion_id="RC", verdict=SoftVerdict.NO_VETO)],
        judge_model_tier=3,
        builder_model_tier=3,
    )
    with pytest.raises(DeliveryError, match="self-review"):
        bus.publish(
            seal(
                message_id="m1",
                contract=verdict,
                sender_role=Role.JUDGE,
                sender_identity="agent-7",
                recipient_identity="agent-7",
            )
        )
    assert got == []


def test_an_oracle_author_may_not_grade_itself(holdout_oracle):
    bus = ContractBus()
    with pytest.raises(DeliveryError, match="may not also be its subject"):
        bus.publish(
            seal(
                message_id="m1",
                contract=holdout_oracle,
                sender_role=Role.VERIFIER,
                sender_identity="verifier-1",
                recipient_identity="verifier-1",
            )
        )


# --------------------------------------------- temporary workers leave no trace


@pytest.mark.parametrize("role", [Role.BUILDER, Role.REFACTOR, Role.CRITIC, Role.RECONCILER])
def test_temporary_roles_cannot_write_team_memory(role):
    """PDR-001 §7 and JiuwenSwarm agree: a single writer for shared memory.

    If short-lived workers could write memory, a wave that was discarded would
    still have changed the next wave's beliefs — the exact contamination the
    calibration pipeline exists to prevent.
    """

    policy = AsymmetryPolicy()
    assert not policy.can_write(role, ArtifactClass.TEAM_MEMORY).allowed


def test_only_the_designated_writers_hold_the_memory_pen():
    policy = AsymmetryPolicy()
    writers = {
        role
        for role in Role
        if policy.can_write(role, ArtifactClass.TEAM_MEMORY).allowed
    }
    assert writers == {Role.LEADER, Role.SPEC_STEWARD, Role.HUMAN}


def test_builder_cannot_write_the_l2_contract_it_implements():
    policy = AsymmetryPolicy()
    assert not policy.can_write(Role.BUILDER, ArtifactClass.SPEC_L2).allowed
    assert policy.can_write(Role.BUILDER, ArtifactClass.SPEC_L3).allowed


def test_verifier_cannot_rewrite_the_spec_it_verifies_against():
    """Otherwise every failing test can be "fixed" by weakening the contract."""

    policy = AsymmetryPolicy()
    assert not policy.can_write(Role.VERIFIER, ArtifactClass.SPEC_L2).allowed
    assert not policy.can_write(Role.VERIFIER, ArtifactClass.SPEC_L1).allowed


def test_architect_cannot_author_the_holdout():
    """Whoever writes the contract must not also write the hidden exam, or the
    exam degenerates into a restatement of the author's own reading."""

    policy = AsymmetryPolicy()
    assert not policy.can_write(Role.ARCHITECT, ArtifactClass.ORACLE_HOLDOUT).allowed
    assert not policy.can_read(Role.ARCHITECT, ArtifactClass.ORACLE_HOLDOUT).allowed


def test_no_machine_role_may_write_the_constitution():
    """Layer 0 is amended by humans out of band, never by a running swarm."""

    policy = AsymmetryPolicy()
    machine_roles = [r for r in Role if r is not Role.HUMAN]
    assert not any(
        policy.can_write(role, ArtifactClass.CONSTITUTION).allowed for role in machine_roles
    )
    assert policy.can_write(Role.HUMAN, ArtifactClass.CONSTITUTION).allowed


def test_default_is_denial_not_permission():
    """An artefact class nobody thought about must be unreachable, not public."""

    policy = AsymmetryPolicy()
    unknown_pairs = [
        (Role.CRITIC, ArtifactClass.RLEVEL_REGISTRY),
        (Role.REFACTOR, ArtifactClass.EVIDENCE_RECEIPT),
        (Role.CARTOGRAPHER, ArtifactClass.SPEC_L3),
    ]
    for role, art in unknown_pairs:
        assert not policy.can_write(role, art).allowed


def test_capability_grants_are_explicit_and_enumerable():
    """The matrix must be inspectable, because a policy nobody can print is a
    policy nobody can review."""

    policy = AsymmetryPolicy()
    assert policy.capabilities(Role.BUILDER, ArtifactClass.INSTANCE) == frozenset(
        {Capability.READ, Capability.WRITE}
    )
    assert policy.capabilities(Role.BUILDER, ArtifactClass.ORACLE_HOLDOUT) == frozenset()


# ------------------------------------------------------------ tier discipline


def test_judge_tier_must_not_be_below_builder_tier():
    """A weaker judge grading a stronger builder produces noise that looks like
    signal; the contract refuses to represent that situation at all."""

    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        SoftGateResult(judge_model_tier=2, builder_model_tier=3)
    SoftGateResult(judge_model_tier=3, builder_model_tier=3)
