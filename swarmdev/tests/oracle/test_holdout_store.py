import pytest

from swarmdev.contracts import CapabilityError, HoldoutScenario, OracleBundle, Role, make_token
from swarmdev.oracle import HoldoutStore


def _bundle() -> OracleBundle:
    return OracleBundle(
        bundle_id="BND-1",
        spec_id="SPEC-1",
        spec_version="1.0.0",
        scenarios=[
            HoldoutScenario(
                scenario_id="SCN-1", spec_clause_ids=["CL-A1"], title="a", run_command="true"
            ),
            HoldoutScenario(
                scenario_id="SCN-2", spec_clause_ids=["CL-B1"], title="b", run_command="true"
            ),
        ],
    )


def test_builder_cannot_read_holdout():
    store = HoldoutStore(_bundle())
    with pytest.raises(CapabilityError):
        store.get(make_token(Role.BUILDER, "b-1", "s1"))


def test_leader_cannot_read_holdout():
    store = HoldoutStore(_bundle())
    with pytest.raises(CapabilityError):
        store.get(make_token(Role.LEADER, "l-1", "s1"))


def test_architect_and_verifier_can_read():
    store = HoldoutStore(_bundle())
    assert [s.scenario_id for s in store.get(make_token(Role.ARCHITECT, "a-1", "s1"))] == [
        "SCN-1",
        "SCN-2",
    ]
    assert len(store.get(make_token(Role.VERIFIER, "v-1", "s1"))) == 2


def test_get_filters_by_scenario_ids():
    store = HoldoutStore(_bundle())
    token = make_token(Role.VERIFIER, "v-1", "s1")
    picked = store.get(token, scenario_ids=["SCN-2"])
    assert [s.scenario_id for s in picked] == ["SCN-2"]


def test_rotate_requires_write_capability():
    store = HoldoutStore(_bundle())
    new = [
        HoldoutScenario(
            scenario_id="SCN-9", spec_clause_ids=[], title="n", run_command="true"
        )
    ]
    with pytest.raises(CapabilityError):
        store.rotate(make_token(Role.BUILDER, "b-1", "s1"), new, epoch=1)
    with pytest.raises(CapabilityError):
        store.rotate(make_token(Role.VERIFIER, "v-1", "s1"), new, epoch=1)


def test_rotate_epoch_must_increase():
    store = HoldoutStore(_bundle())
    token = make_token(Role.ARCHITECT, "a-1", "s1")
    new = [
        HoldoutScenario(
            scenario_id="SCN-9", spec_clause_ids=[], title="n", run_command="true"
        )
    ]
    store.rotate(token, new, epoch=1)
    rotated = store.get(token)
    assert [s.scenario_id for s in rotated] == ["SCN-9"]
    assert rotated[0].rotation_epoch == 1
    with pytest.raises(ValueError):
        store.rotate(token, new, epoch=1)
    with pytest.raises(ValueError):
        store.rotate(token, new, epoch=0)
    store.rotate(token, new, epoch=2)
    assert store.get(token)[0].rotation_epoch == 2
