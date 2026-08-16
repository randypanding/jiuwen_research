"""端到端契约协作测试：波次全流程经总线流转（契约间通信的最终验证）。

覆盖：
- Pipeline A（交付）：spec → seal(lock) → fanout(N) → build → verify(gates)
  → classify(CLOSED) → admission commit → receipt/health
- Pipeline B（标定）：SILENCE → spec moderator 收敛（don't-care 或 spec-delta）
  → reseal 下一波次；代码全部丢弃但测量保留（INV2）
- 事务原子性 + 收据哈希链 + 健康度反馈到下一波次的 fan-out N
"""
import pytest

from swarmforge.admission import (
    AdmissionTransaction,
    MeasurementLedger,
    MeasurementRecord,
    ReceiptLedger,
    WaveState,
    WaveTracker,
)
from swarmforge.bus import BusPermissionError, ContractDecl, Envelope, InProcessBus, validate_wiring
from swarmforge.gates import (
    AdmissionDecisionKind, EvidenceItem, GateContext, GateRunner,
)
from swarmforge.measurement import (
    ClassifyInput, MeasurementClass, classify, compute_fanout, compute_health,
)
from swarmforge.oracle import (
    DiffConclusion, DifferentialEngine, HoldoutScenario, HoldoutStore,
    OutputNormalizer, ScenarioVisibility,
)
from swarmforge.specrepo import (
    ClauseLayer, DontCareEntry, InterfaceLock, RLevel, SpecClause, SpecDelta,
    SpecDocument, SpecStore, WitnessKind, WitnessRef,
)

# ---- 契约的连线声明（装配期校验，运行前完成） ----
CONTRACT_DECLS = [
    ContractDecl("wave-mgr", "leader", provides=["wave.sealed", "wave.assign.pool"],
                 consumes=["gate.completed", "measurement.classified", "admit.committed"]),
    ContractDecl("builder-pool", "builder", provides=["build.completed"],
                 consumes=["wave.assign.pool"]),
    ContractDecl("verifier", "verifier",
                 provides=["gate.completed", "measurement.classified"],
                 consumes=["build.completed", "wave.sealed"]),
    ContractDecl("spec-moderation", "spec_moderator", provides=["spec.delta.proposed"],
                 consumes=["measurement.classified"]),
    ContractDecl("admission", "leader", provides=["admit.committed"],
                 consumes=["measurement.classified", "gate.completed"]),
    ContractDecl("reconciler", "reconciler", provides=["drift.detected"],
                 consumes=["admit.committed"]),
]


@pytest.fixture
def world(tmp_path):
    store = SpecStore(str(tmp_path / "specs"))
    # 域规范：一条 bound L2 契约 + 一条 don't-care
    doc = SpecDocument(domain="pay", intent="支付", clauses=[
        SpecClause(clause_id="CON-1", layer=ClauseLayer.L2,
                   text="退款金额=本金*比例，精确到分",
                   witnesses=[WitnessRef(WitnessKind.HOLDOUT, "SC-pay-0001")],
                   anchors=["pay/refund.py*"]),
    ])
    v0 = store.init_domain(doc)
    # R 级注册：迁移冻结，其余默认 R0
    from swarmforge.specrepo import ArtifactRule, RRegistry
    store.write_registry(RRegistry(rules=[
        ArtifactRule("migrations/**", RLevel.R3, golden_locked=True),
    ]))
    holdout = HoldoutStore(str(tmp_path / "scenarios"))
    holdout.put(HoldoutScenario(
        scenario_id="SC-pay-0001", domain="pay",
        visibility=ScenarioVisibility.HOLDOUT, clause_ids=["CON-1"],
        stimulus={"principal": 10000, "ratio": 7}, expected={"refund_cents": 70000},
    ))
    return {
        "root": tmp_path, "store": store, "v0": v0, "holdout": holdout,
        "ledger": ReceiptLedger(str(tmp_path / "receipts.jsonl")),
        "mledger": MeasurementLedger(str(tmp_path / "measurements.jsonl")),
    }


def run_gate_for_instance(instance_id, scenario_pass, build_ok=True,
                          traces=None, delta_id="D1"):
    """verifier 契约的核心动作：执行 oracle + 出门禁证据。"""
    evid = {
        "build_report": EvidenceItem("build_report", "ci",
                                     {"compile_ok": build_ok}),
        "test_report": EvidenceItem("test_report", "ci",
                                    {"total": 1, "passed": 1, "failed": 0, "errors": 0}),
        "scenario_results": EvidenceItem("scenario_results", "verifier", {
            "results": [{"scenario_id": "SC-pay-0001", "instance_id": instance_id,
                         "outcome": "pass" if scenario_pass else "fail"}],
            "fail_to_pass": ["SC-pay-0001"], "pass_to_pass": [],
        }),
        "guard_report": EvidenceItem("guard_report", "sandbox",
                                     {"path_violations": [], "declared_deps": []}),
        "drift_report": EvidenceItem("drift_report", "verifier",
                                     {"orphans": [], "missing_anchors": [],
                                      "bypasses": [], "stale_clauses": []}),
    }
    if traces is not None:
        evid["diff_report"] = EvidenceItem(
            "diff_report", "verifier",
            DifferentialEngine(OutputNormalizer(drop_keys={"timestamp"}))
            .compare("W1", delta_id, traces, ["in-1"], dont_cares=[]).to_dict())
    ctx = GateContext(wave_id="W1", instance_id=instance_id, evidence=evid)
    return GateRunner().run(ctx, RLevel.R0,
                            gate_ids=["H1", "H2", "H3", "H6", "H7"])


class TestPipelineA_Delivery:
    def test_full_delivery_flow(self, world):
        # 0. 装配期：连线检查通过
        assert validate_wiring(CONTRACT_DECLS) == []

        events = []
        bus = InProcessBus()
        bus.subscribe("verifier", "wave.sealed", lambda e: events.append(e))
        bus.subscribe("leader", "gate.completed", lambda e: events.append(e))
        bus.subscribe("leader", "measurement.classified", lambda e: events.append(e))
        tracker = WaveTracker(on_transition=lambda rec, ev: events.append(ev))
        tracker.create("W1", "pay")

        # 1. SEAL：接口冻结（锁 CON-1）
        world["store"].acquire_lock(InterfaceLock("W1", ["CON-1"]))
        tracker.transition("W1", WaveState.SEALED)
        bus.publish(Envelope(topic="wave.sealed", type="wave.sealed",
                             sender_role="leader", wave_id="W1"))

        # 2. FANOUT：健康度反馈的 N（首波次，无历史 → U 低 → N=1）
        fan = compute_fanout(rework_rate=0.0, novelty=0.1, r_level="R0")
        assert fan.n == 1
        tracker.transition("W1", WaveState.FANOUT)

        # 3. builder 交付实例 I1（行为=退款正确，无额外行为）
        bus.publish(Envelope(topic="build.instance.I1.completed",
                             type="build.completed", sender_role="builder",
                             wave_id="W1"))
        tracker.transition("W1", WaveState.VERIFY)

        # 4. verifier：单实例无差分（N=1），跑门禁全绿
        outcome = run_gate_for_instance("I1", scenario_pass=True)
        assert outcome.admitted
        bus.publish(Envelope(topic="gate.completed", type="gate.completed",
                             sender_role="verifier", wave_id="W1",
                             payload={"decision": outcome.decision.value}))

        # 5. CLASSIFY：N=1 全过 + 无差分 → CLOSED
        cls = classify(ClassifyInput(instance_passed=[True],
                                     diff_conclusion="na", n=1))
        assert cls == MeasurementClass.CLOSED
        tracker.transition("W1", WaveState.CLASSIFY)
        bus.publish(Envelope(topic="measurement.classified",
                             type="measurement.classified", sender_role="verifier",
                             wave_id="W1", payload={"class": cls.value}))

        # 6. ADMIT：准入事务提交
        tracker.transition("W1", WaveState.ADMITTING)
        txn = AdmissionTransaction(str(world["root"] / "txn"), world["store"],
                                   world["ledger"], world["mledger"])
        delta = SpecDelta(delta_id="D1", wave_id="W1", base_version=world["v0"],
                          motivation="首个交付")
        txn.begin("W1", "pay", "I1", outcome, delta,
                  differential={"conclusion": "equivalent"},
                  measurement_class=cls.value)
        receipt_hash = txn.commit()
        assert receipt_hash and world["ledger"].verify_chain() is None
        tracker.transition("W1", WaveState.COMMITTED)
        world["store"].release_lock("W1")
        bus.publish(Envelope(topic="admit.committed", type="admit.committed",
                             sender_role="leader", wave_id="W1"))

        # 事件流完整：wave.sealed → gate/measurement → admit
        types = [e.type for e in events if isinstance(e, Envelope)]
        assert types == ["wave.sealed", "gate.completed", "measurement.classified"]

        # 8. 健康度：闭合 100%，反馈下一波次 fan-out N
        health = compute_health(world["mledger"].all(), bound_ratio=1.0)
        assert health.spec_closure == 1.0
        next_fan = compute_fanout(rework_rate=health.rework_rate, novelty=0.1,
                                  r_level="R0")
        assert next_fan.n == 1


class TestPipelineB_Calibration:
    def test_silence_flow_discards_code_but_keeps_measurements(self, world):
        bus = InProcessBus()
        tracker = WaveTracker()
        tracker.create("W2", "pay")
        world["store"].acquire_lock(InterfaceLock("W2", ["CON-1"]))
        tracker.transition("W2", WaveState.SEALED)
        tracker.transition("W2", WaveState.FANOUT)

        # N=3 fan-out（标定流水线强制多实例）
        traces = {
            "I1": {"in-1": {"refund_cents": 70000}},
            "I2": {"in-1": {"refund_cents": 70000, "receipt_no": "R-001"}},
            "I3": {"in-1": {"refund_cents": 70000, "receipt_no": "R-002"}},
        }
        outcomes = [run_gate_for_instance(iid, True, traces=traces)
                    for iid in ("I1", "I2", "I3")]
        assert all(o.admitted for o in outcomes)
        tracker.transition("W2", WaveState.VERIFY)

        diff = DifferentialEngine(OutputNormalizer(drop_keys={"timestamp"})) \
            .compare("W2", "D2", traces, ["in-1"], dont_cares=[])
        assert diff.conclusion == DiffConclusion.DIFFERENCE_FOUND

        cls = classify(ClassifyInput(instance_passed=[True, True, True],
                                     diff_conclusion=diff.conclusion.value, n=3))
        assert cls == MeasurementClass.SILENCE
        tracker.transition("W2", WaveState.CLASSIFY)
        bus.publish(Envelope(topic="measurement.classified",
                             type="measurement.classified", sender_role="verifier",
                             wave_id="W2", payload={"class": cls.value}))

        # SILENCE → CONVERGING（全部代码丢弃；spec moderator 收敛）
        tracker.transition("W2", WaveState.CONVERGING)
        for iid in ("I1", "I2", "I3"):
            world["mledger"].append(MeasurementRecord(
                wave_id="W2", spec_delta_id="D2", instance_id=iid,
                passed=False, diff_conclusion=diff.conclusion.value,
                classification=cls.value))
        # spec moderator 裁定：差异维度（回单号格式）登记为 don't-care
        dc = DontCareEntry(entry_id="DC-1", clause_id="CON-1",
                           dimension="*.receipt_no", origin="measured")
        v1 = world["store"].apply_delta("pay", SpecDelta(
            delta_id="D2", wave_id="W2", base_version=world["v0"],
            dont_cares_added=[dc], motivation="SILENCE: receipt_no 格式未定义"))

        # RESEAL 下一波次（收敛后的新接口窗口）
        world["store"].release_lock("W2")
        tracker.transition("W2", WaveState.SEALED)
        assert world["store"].load_domain("pay").dont_cares[0].entry_id == "DC-1"

        # 重跑差分：现在差异落在登记的自由度内 → EQUIVALENT → 可准入
        dcs = world["store"].load_domain("pay").dont_cares
        diff2 = DifferentialEngine(OutputNormalizer(drop_keys={"timestamp"})) \
            .compare("W2b", "D2b", traces, ["in-1"], dont_cares=dcs)
        assert diff2.conclusion == DiffConclusion.EQUIVALENT

        # 健康度：本波次 spec 熵 = 1 次沉默事件
        health = compute_health(world["mledger"].all(), bound_ratio=1.0)
        assert health.spec_entropy == pytest.approx(1.0)


class TestInformationAsymmetryE2E:
    def test_builder_never_sees_holdout_through_any_channel(self, world):
        """契约级红队：builder 通过总线/场景库均拿不到 holdout。"""
        bus = InProcessBus()
        with pytest.raises(BusPermissionError):
            bus.subscribe("builder", "holdout.*", lambda e: None)
        with pytest.raises(BusPermissionError):
            bus.subscribe("builder", "gate.*", lambda e: None)
        with pytest.raises(Exception):
            world["holdout"].get("SC-pay-0001", reader_role="builder")
        # 判别侧正常
        sc = world["holdout"].get("SC-pay-0001", reader_role="verifier")
        assert sc.clause_ids == ["CON-1"]
