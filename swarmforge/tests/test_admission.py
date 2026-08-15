"""准入事务测试：波次状态机、2PC 原子性、崩溃恢复、收据哈希链、INV2。"""
import pytest

from swarmforge.admission import (
    AdmissionTransaction,
    EvidenceReceipt,
    IllegalTransition,
    MeasurementLedger,
    MeasurementRecord,
    ReceiptLedger,
    SpecStore,
    SpecDelta,
    WaveState,
    WaveTracker,
)
from swarmforge.gates import AdmissionDecisionKind, GateRunner, GateContext, EvidenceItem
from swarmforge.specrepo import ClauseLayer, SpecClause, SpecDocument, WitnessKind, WitnessRef, RLevel


def doc():
    return SpecDocument(domain="pay", clauses=[
        SpecClause(clause_id="CON-1", layer=ClauseLayer.L2, text="退款精确",
                   witnesses=[WitnessRef(WitnessKind.GATE, "H2")]),
    ])


class TestWaveStateMachine:
    def test_legal_lifecycle(self):
        tracker = WaveTracker()
        tracker.create("W1", "pay")
        for to in [WaveState.SEALED, WaveState.FANOUT, WaveState.VERIFY,
                   WaveState.CLASSIFY, WaveState.ADMITTING, WaveState.COMMITTED]:
            tracker.transition("W1", to)
        assert tracker.get("W1").state == WaveState.COMMITTED

    def test_illegal_skip_rejected(self):
        tracker = WaveTracker()
        tracker.create("W1", "pay")
        with pytest.raises(IllegalTransition):
            tracker.transition("W1", WaveState.COMMITTED)  # draft → committed 非法

    def test_converging_loops_back_to_sealed(self):
        tracker = WaveTracker()
        tracker.create("W1", "pay")
        for to in [WaveState.SEALED, WaveState.FANOUT, WaveState.VERIFY,
                   WaveState.CLASSIFY, WaveState.CONVERGING, WaveState.SEALED]:
            tracker.transition("W1", to)
        assert tracker.get("W1").state == WaveState.SEALED

    def test_terminal_states_absorbing(self):
        tracker = WaveTracker()
        tracker.create("W1", "pay")
        tracker.transition("W1", WaveState.ABORTED)
        with pytest.raises(IllegalTransition):
            tracker.transition("W1", WaveState.SEALED)

    def test_transition_emits_event(self):
        events = []
        tracker = WaveTracker(on_transition=lambda rec, ev: events.append(ev))
        tracker.create("W1", "pay")
        tracker.transition("W1", WaveState.SEALED)
        assert events == ["wave.sealed"]


def green_outcome():
    ctx = GateContext(wave_id="W1", instance_id="I1", evidence={
        "build_report": EvidenceItem("build_report", "ci", {"compile_ok": True}),
        "test_report": EvidenceItem("test_report", "ci",
                                    {"total": 3, "passed": 3, "failed": 0, "errors": 0}),
    })
    return GateRunner().run(ctx, RLevel.R0, gate_ids=["H1", "H2"])


class TestAdmissionTransaction:
    @pytest.fixture(autouse=True)
    def _dirs(self, tmp_path):
        self.root = tmp_path
        self.store = SpecStore(str(tmp_path / "specs"))
        self.v0 = self.store.init_domain(doc())
        self.ledger = ReceiptLedger(str(tmp_path / "receipts.jsonl"))
        self.mledger = MeasurementLedger(str(tmp_path / "measurements.jsonl"))

    def txn(self):
        return AdmissionTransaction(str(self.root / "txn"), self.store,
                                     self.ledger, self.mledger)

    def test_commit_applies_delta_and_receipt(self):
        t = self.txn()
        delta = SpecDelta(delta_id="D1", wave_id="W1", base_version=self.v0,
                          clauses_added=[])
        t.begin("W1", "pay", "I1", green_outcome(), delta,
                differential={"conclusion": "equivalent"},
                measurement_class="closed", discarded_instances=["I2", "I3"])
        receipt_hash = t.commit()
        assert receipt_hash
        # spec 版本链有 D1
        assert any(v.delta_id == "D1" for v in self.store.version_chain())
        # 收据在账本，链完整
        assert self.ledger.verify_chain() is None
        r = self.ledger.all()[0]
        assert r.instance_id == "I1" and set(r.discarded_instances) == {"I2", "I3"}

    def test_inv2_rollback_keeps_measurements(self):
        t = self.txn()
        delta = SpecDelta(delta_id="D1", wave_id="W1", base_version=self.v0)
        t.begin("W1", "pay", "I1", green_outcome(), delta,
                differential={"conclusion": "difference_found"},
                measurement_class="silence", discarded_instances=["I2"])
        t.rollback("spec silence unresolved")
        # 实例被弃，但测量结论保留
        recs = self.mledger.for_wave("W1")
        assert len(recs) == 2  # I1 + I2
        assert recs[0].passed is False
        assert recs[0].classification == "silence"
        # spec 未被改动
        assert self.store.load_domain("pay").contract_hash() == self.v0
        # 无收据（未准入）
        assert self.ledger.all() == []

    def test_commit_failure_auto_rollback(self):
        t = self.txn()
        stale = SpecDelta(delta_id="D-bad", wave_id="W1", base_version="wrong")
        t.begin("W1", "pay", "I1", green_outcome(), stale,
                differential={}, measurement_class="closed")
        with pytest.raises(Exception):
            t.commit()  # base_version 不符 → SpecConflictError
        assert self.mledger.for_wave("W1")  # 测量仍保留
        assert self.ledger.all() == []

    def test_crash_recovery_rolls_back_open_txn(self):
        t = self.txn()
        delta = SpecDelta(delta_id="D1", wave_id="W1", base_version=self.v0)
        t.begin("W1", "pay", "I1", green_outcome(), delta,
                differential={}, measurement_class="closed")
        # 模拟崩溃：不调 commit，直接新开一个恢复流程
        recovered = AdmissionTransaction.recover(
            str(self.root / "txn"), self.store, self.ledger, self.mledger)
        assert recovered == [t.txn_id]
        # 恢复后：测量保留、spec 未动、再 commit 该事务对象应报状态错
        assert self.mledger.for_wave("W1")
        assert self.store.load_domain("pay").contract_hash() == self.v0

    def test_finished_txn_rejects_operations(self):
        t = self.txn()
        delta = SpecDelta(delta_id="D1", wave_id="W1", base_version=self.v0)
        t.begin("W1", "pay", "I1", green_outcome(), delta,
                differential={}, measurement_class="closed")
        t.commit()
        from swarmforge.admission import TransactionStateError
        with pytest.raises(TransactionStateError):
            t.commit()
        with pytest.raises(TransactionStateError):
            t.rollback("late")


class TestReceiptHashChain:
    def test_chain_tamper_detection(self, tmp_path):
        ledger = ReceiptLedger(str(tmp_path / "r.jsonl"))
        for i in range(3):
            r = EvidenceReceipt(receipt_id=f"R{i}", wave_id="W1", domain="pay",
                                spec_delta_id=f"D{i}")
            ledger.append(r)
        assert ledger.verify_chain() is None
        # 篡改第二张收据的内容
        path = tmp_path / "r.jsonl"
        lines = path.read_text().splitlines()
        import json
        rec = json.loads(lines[1])
        rec["instance_id"] = "tampered"
        lines[1] = json.dumps(rec, ensure_ascii=False)
        path.write_text("\n".join(lines) + "\n")
        break_at = ledger.verify_chain()
        assert break_at == 1  # 断点定位在篡改处

    def test_empty_chain(self, tmp_path):
        ledger = ReceiptLedger(str(tmp_path / "r.jsonl"))
        assert ledger.verify_chain() is None
        assert ledger.tail_hash() == "0" * 64
