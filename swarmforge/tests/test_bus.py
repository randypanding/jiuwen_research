"""总线与契约间通信测试：权限矩阵、连线完整性、跨契约事件流。"""
import pytest

from swarmforge.bus import (
    BusPermissionError,
    ContractDecl,
    Envelope,
    InProcessBus,
    validate_wiring,
)


class TestPermissionMatrix:
    def test_builder_cannot_publish_gate_results(self):
        bus = InProcessBus()
        with pytest.raises(BusPermissionError) as ei:
            bus.publish(Envelope(topic="gate.W1.completed", type="gate.completed",
                                 sender_role="builder", payload={"admit": True}))
        assert ei.value.inv_id == "INV5"

    def test_builder_cannot_subscribe_holdout(self):
        bus = InProcessBus()
        with pytest.raises(BusPermissionError):
            bus.subscribe("builder", "holdout.*", lambda e: None)

    def test_builder_cannot_subscribe_measurement(self):
        bus = InProcessBus()
        with pytest.raises(BusPermissionError):
            bus.subscribe("builder", "measurement.*", lambda e: None)

    def test_verifier_can_publish_gate(self):
        bus = InProcessBus()
        n = bus.publish(Envelope(topic="gate.W1.completed", type="gate.completed",
                                 sender_role="verifier", payload={}))
        assert n >= 0  # 无订阅者=0 投递，但发布合法

    def test_unknown_role_denied(self):
        bus = InProcessBus()
        with pytest.raises(BusPermissionError):
            bus.publish(Envelope(topic="wave.sealed", type="wave.sealed",
                                 sender_role="intruder", payload={}))

    def test_wildcard_topic_within_grant(self):
        bus = InProcessBus()
        bus.publish(Envelope(topic="build.instance.I7.completed", type="build.completed",
                             sender_role="builder", payload={}))

    def test_payload_must_be_json_serializable(self):
        bus = InProcessBus()
        with pytest.raises(TypeError):
            bus.publish(Envelope(topic="build.x", type="build.completed",
                                 sender_role="builder", payload={"bad": {1, 2}}))


class TestWiringCompleteness:
    def test_dangling_subscription_detected(self):
        decls = [
            ContractDecl("admission", "leader", provides=["admit.committed"],
                         consumes=["measurement.classified"]),
            ContractDecl("gates", "verifier", provides=["gate.completed"], consumes=[]),
        ]
        issues = validate_wiring(decls)
        assert any(i.kind == "dangling_subscription" for i in issues)

    def test_closed_wiring_clean(self):
        decls = [
            ContractDecl("admission", "leader", provides=["admit.committed"],
                         consumes=["gate.completed", "measurement.classified"]),
            ContractDecl("gates", "verifier", provides=["gate.completed"], consumes=[]),
            ContractDecl("builder-pool", "builder",
                         provides=["build.completed"], consumes=["wave.assign.*"]),
            ContractDecl("measurement", "verifier",
                         provides=["measurement.classified"], consumes=["build.completed"]),
            ContractDecl("wave-mgr", "leader", provides=["wave.sealed", "wave.assign.dev1"],
                         consumes=["admit.committed"]),
        ]
        assert validate_wiring(decls) == []

    def test_role_grant_mismatch_detected(self):
        decls = [ContractDecl("sneaky", "builder", provides=["gate.completed"],
                              consumes=[])]
        issues = validate_wiring(decls)
        assert any(i.kind == "permission_mismatch" for i in issues)


class TestContractToContractFlow:
    """跨契约事件流：wave.sealed → build.completed → gate.completed →
    measurement.classified → admit.committed 全链路按权限矩阵流转。"""

    def test_full_wave_event_flow(self, tmp_path):
        bus = InProcessBus(audit_path=str(tmp_path / "bus.jsonl"))
        received: dict[str, list[Envelope]] = {
            "verifier": [], "leader": [], "spec_moderator": [], "reconciler": [],
        }

        bus.subscribe("verifier", "wave.sealed", lambda e: received["verifier"].append(e))
        bus.subscribe("verifier", "build.instance.*", lambda e: received["verifier"].append(e))
        bus.subscribe("leader", "gate.completed", lambda e: received["leader"].append(e))
        bus.subscribe("leader", "measurement.classified",
                      lambda e: received["leader"].append(e))
        bus.subscribe("spec_moderator", "measurement.classified",
                      lambda e: received["spec_moderator"].append(e))
        bus.subscribe("reconciler", "admit.committed",
                      lambda e: received["reconciler"].append(e))

        # leader 封波
        bus.publish(Envelope(topic="wave.sealed", type="wave.sealed",
                             sender_role="leader", wave_id="W1"))
        # builder 交付
        bus.publish(Envelope(topic="build.instance.I1.completed", type="build.completed",
                             sender_role="builder", wave_id="W1"))
        # verifier 出门禁结果（wave_id 在信封，topic 不嵌 id）
        bus.publish(Envelope(topic="gate.completed", type="gate.completed",
                             sender_role="verifier", wave_id="W1",
                             payload={"decision": "admit"}))
        # verifier 出测量结论（wave_id 在信封，不嵌 topic）
        bus.publish(Envelope(topic="measurement.classified", type="measurement.classified",
                             sender_role="verifier", wave_id="W1",
                             payload={"class": "closed"}))
        # leader 提交准入
        bus.publish(Envelope(topic="admit.committed", type="admit.committed",
                             sender_role="leader", wave_id="W1"))

        assert len(received["verifier"]) == 2      # wave.sealed + build.completed
        assert len(received["leader"]) == 2        # gate.completed + measurement.classified
        assert len(received["spec_moderator"]) == 1
        assert len(received["reconciler"]) == 1
        # 审计日志完整
        with open(tmp_path / "bus.jsonl") as f:
            assert sum(1 for _ in f) == 5

    def test_history_query(self):
        bus = InProcessBus()
        bus.publish(Envelope(topic="gate.W1.completed", type="gate.completed",
                             sender_role="verifier"))
        bus.publish(Envelope(topic="wave.sealed", type="wave.sealed",
                             sender_role="leader"))
        assert len(bus.history("gate.*")) == 1
        assert len(bus.history("*")) == 2

    def test_unsubscribe_stops_delivery(self):
        bus = InProcessBus()
        seen = []
        sub = bus.subscribe("leader", "gate.*", lambda e: seen.append(e))
        bus.publish(Envelope(topic="gate.W1.completed", type="gate.completed",
                             sender_role="verifier"))
        bus.unsubscribe(sub)
        bus.publish(Envelope(topic="gate.W2.completed", type="gate.completed",
                             sender_role="verifier"))
        assert len(seen) == 1
