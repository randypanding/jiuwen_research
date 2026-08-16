"""Every contract must survive the wire.

A contract that cannot round-trip is a contract that silently loses fields at a
team boundary, which is the single most common way a "well-defined interface"
turns out not to be one.
"""

from __future__ import annotations

import json

import pytest

from swarmkernel.contracts import CONTRACT_REGISTRY
from swarmkernel.contracts.base import ArtifactClass, SemVer

# Registered in pyproject [tool.pytest.ini_options] markers.
pytestmark = pytest.mark.contract

ALL_NAMES = sorted(CONTRACT_REGISTRY)


def test_registry_is_not_empty():
    assert len(ALL_NAMES) >= 30


@pytest.mark.parametrize("name", ALL_NAMES)
def test_every_contract_declares_an_artifact_class(name):
    cls = CONTRACT_REGISTRY[name]
    assert isinstance(cls.ARTIFACT_CLASS, ArtifactClass), (
        f"{name} has no artefact class; the bus would refuse to route it"
    )


@pytest.mark.parametrize("name", ALL_NAMES)
def test_every_contract_declares_a_semver(name):
    cls = CONTRACT_REGISTRY[name]
    SemVer.parse(cls.CONTRACT_VERSION)


@pytest.mark.parametrize("name", ALL_NAMES)
def test_every_contract_emits_json_schema(name):
    cls = CONTRACT_REGISTRY[name]
    schema = cls.json_schema()
    assert schema["x-artifact-class"] == cls.ARTIFACT_CLASS.value
    json.dumps(schema)


@pytest.mark.parametrize("name", ALL_NAMES)
def test_every_contract_forbids_unknown_fields(name):
    """``extra="forbid"`` everywhere.

    Silent field-dropping is how two teams end up "agreeing" on a contract while
    exchanging different data.
    """

    cls = CONTRACT_REGISTRY[name]
    assert cls.model_config.get("extra") == "forbid", name


def _roundtrip(obj):
    cls = type(obj)
    dumped = obj.model_dump(mode="json")
    text = json.dumps(dumped)
    restored = cls.model_validate(json.loads(text))
    assert restored.digest() == obj.digest()
    return restored


def test_roundtrip_spec(spec):
    restored = _roundtrip(spec)
    assert [c.id for c in restored.clauses] == [c.id for c in spec.clauses]


def test_roundtrip_bundle(bundle):
    restored = _roundtrip(bundle)
    assert restored.holdout.bundle_id == bundle.holdout.bundle_id


def test_roundtrip_instance_report(three_agreeing_reports):
    for report in three_agreeing_reports:
        _roundtrip(report)


def test_roundtrip_delta(additive_delta):
    _roundtrip(additive_delta)


def test_roundtrip_unit(unit_r1):
    _roundtrip(unit_r1)


def test_digest_is_order_independent(spec):
    """Canonical JSON: key order must not change identity, or every diff lies."""

    a = spec.model_dump(mode="json")
    b = {k: a[k] for k in reversed(list(a))}
    assert type(spec).model_validate(b).digest() == spec.digest()


def test_digest_changes_when_content_changes(clause_total):
    other = clause_total.model_copy(update={"title": clause_total.title + "!"})
    assert other.digest() != clause_total.digest()
