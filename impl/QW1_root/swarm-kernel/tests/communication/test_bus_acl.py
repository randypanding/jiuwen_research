from __future__ import annotations

import pytest

from swarm_kernel.bus.bus import ContractBus, FileRelay, IsolationViolation, envelope_from_ndjson, envelope_to_ndjson
from swarm_kernel.contracts.base import Confidentiality, ContractEnvelope, Role


def env(schema_name: str, producer: Role, conf: Confidentiality = Confidentiality.PUBLIC, topic: str = "default", scope: str = "ctx-1") -> ContractEnvelope:
    return ContractEnvelope(schema_name=schema_name, producer_role=producer, topic=topic, session_scope=scope, confidentiality=conf, payload={"k": schema_name})


def test_builder_cannot_receive_holdout_scenarios() -> None:
    bus = ContractBus()
    seen: list[ContractEnvelope] = []
    bus.subscribe("oracle", "builder-1", Role.BUILDER, seen.append, session_scope="ctx-1")
    bus.subscribe("oracle", "verifier-1", Role.VERIFIER, seen.append, session_scope="ctx-1")
    bus.publish(env("HoldoutScenario", Role.ARCHITECT, Confidentiality.HOLDOUT, topic="oracle"))
    assert len(seen) == 1
    denials = bus.denials()
    assert len(denials) == 1
    assert denials[0].subscriber == "builder-1"
    assert "holdout" in denials[0].reason


def test_builder_cannot_receive_judge_internals() -> None:
    bus = ContractBus()
    seen: list[ContractEnvelope] = []
    bus.subscribe("rubric", "builder-1", Role.BUILDER, seen.append, session_scope="ctx-1")
    bus.publish(env("Rubric", Role.ARCHITECT, Confidentiality.JUDGE_INTERNAL, topic="rubric"))
    assert seen == []
    assert bus.denials()


def test_verifier_receives_holdout() -> None:
    bus = ContractBus()
    seen: list[ContractEnvelope] = []
    bus.subscribe("oracle", "verifier-1", Role.VERIFIER, seen.append, session_scope="ctx-1")
    bus.publish(env("HoldoutScenario", Role.ARCHITECT, Confidentiality.HOLDOUT, topic="oracle"))
    assert len(seen) == 1


def test_builder_cannot_produce_judge_verdict() -> None:
    bus = ContractBus()
    seen: list[ContractEnvelope] = []
    bus.subscribe("verdicts", "verifier-1", Role.VERIFIER, seen.append, session_scope="ctx-1")
    bus.publish(env("JudgeVerdict", Role.BUILDER, topic="verdicts"))
    assert seen == []
    assert any("judging" in d.reason for d in bus.denials())


def test_verifier_can_produce_judge_verdict() -> None:
    bus = ContractBus()
    seen: list[ContractEnvelope] = []
    bus.subscribe("verdicts", "leader-1", Role.LEADER, seen.append, session_scope="ctx-1")
    bus.publish(env("JudgeVerdict", Role.VERIFIER, topic="verdicts"))
    assert len(seen) == 1


def test_builder_memory_write_is_blocked() -> None:
    bus = ContractBus()
    seen: list[ContractEnvelope] = []
    bus.subscribe("memory", "steward-1", Role.SPEC_STEWARD, seen.append, session_scope="ctx-1")
    bus.publish(env("MemoryWrite", Role.BUILDER, topic="memory"))
    assert seen == []
    assert bus.denials()


def test_temporary_builder_cannot_read_memory_restricted() -> None:
    bus = ContractBus()
    seen: list[ContractEnvelope] = []
    bus.subscribe("memory", "builder-1", Role.BUILDER, seen.append, session_scope="ctx-1")
    bus.publish(env("TeamMemoryDigest", Role.SPEC_MODERATOR, Confidentiality.MEMORY_RESTRICTED, topic="memory"))
    assert seen == []


def test_session_scope_isolation() -> None:
    bus = ContractBus()
    seen: list[ContractEnvelope] = []
    bus.subscribe("public", "leader-2", Role.LEADER, seen.append, session_scope="ctx-OTHER")
    delivered = bus.publish(env("WavePlan", Role.ARCHITECT, topic="public", scope="ctx-1"))
    assert delivered == []
    assert seen == []


def test_wildcard_scope_observes_all_sessions() -> None:
    bus = ContractBus()
    seen: list[ContractEnvelope] = []
    bus.subscribe("audit", "reconciler-1", Role.RECONCILER, seen.append, session_scope="*")
    bus.publish(env("DriftEvent", Role.RECONCILER, topic="audit", scope="ctx-9"))
    assert len(seen) == 1


def test_file_relay_roundtrip_and_acl(tmp_path) -> None:
    relay = FileRelay(tmp_path / "relay")
    relay.send(env("HoldoutScenario", Role.ARCHITECT, Confidentiality.HOLDOUT, topic="oracle"))
    relay.send(env("WavePlan", Role.ARCHITECT, topic="oracle"))
    builder_view, builder_denials = relay.receive(Role.BUILDER, topic="oracle")
    verifier_view, verifier_denials = relay.receive(Role.VERIFIER, topic="oracle")
    assert [e.schema_name for e in builder_view] == ["WavePlan"]
    assert len(builder_denials) == 1
    assert {e.schema_name for e in verifier_view} == {"HoldoutScenario", "WavePlan"}
    assert verifier_denials == []


def test_file_relay_detects_tampering(tmp_path) -> None:
    relay = FileRelay(tmp_path / "relay")
    relay.send(env("WavePlan", Role.ARCHITECT, topic="wave"))
    fp = tmp_path / "relay" / "wave.ndjson"
    line = fp.read_text(encoding="utf-8").strip()
    tampered = line.replace('"WavePlan"', '"WavePlanEVIL"')
    fp.write_text(tampered + "\n", encoding="utf-8")
    with pytest.raises(IsolationViolation):
        relay.receive(Role.BUILDER, topic="wave")
    accepted, denials = relay.receive(Role.BUILDER, topic="wave", strict=False)
    assert accepted == []
    assert any("seal broken" in d.reason for d in denials)


def test_envelope_ndjson_roundtrip() -> None:
    e = env("SpecDelta", Role.ARCHITECT)
    e.seal()
    restored = envelope_from_ndjson(envelope_to_ndjson(e))
    assert restored == e
    assert restored.verify_seal()
