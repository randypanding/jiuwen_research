"""Spec 仓契约测试：schema、原子写、delta 应用、接口锁、R 级注册表。"""
import pytest

from swarmforge.specrepo import (
    ClauseLayer,
    DontCareEntry,
    InterfaceLock,
    OperationError,
    RLevel,
    RRegistry,
    ArtifactRule,
    SpecClause,
    SpecConflictError,
    SpecDelta,
    SpecDocument,
    SpecStore,
    WitnessKind,
    WitnessRef,
    validate_delta_solvency,
)


def clause(cid="CON-1", layer=ClauseLayer.L2, text="契约条款", witnesses=True, anchors=None):
    return SpecClause(
        clause_id=cid, layer=layer, text=text,
        witnesses=[WitnessRef(WitnessKind.GATE, "H2")] if witnesses else [],
        anchors=anchors or [],
    )


def make_doc():
    return SpecDocument(
        domain="pay",
        intent="支付域",
        clauses=[
            SpecClause(clause_id="REQ-1", layer=ClauseLayer.L1, text="支持退款"),  # 无见证
            clause("CON-1", ClauseLayer.L2, "退款金额精确到分", anchors=["pay/refund.py*"]),
            clause("IMP-1", ClauseLayer.L3, "用 decimal 实现"),
        ],
    )


class TestSchema:
    def test_roundtrip(self):
        doc = make_doc()
        d = doc.to_dict()
        doc2 = SpecDocument.from_dict(d)
        assert doc2.contract_hash() == doc.contract_hash()

    def test_unverifiable_clause_status(self):
        c = clause("CON-9", witnesses=False)
        assert c.status.value == "unverifiable"

    def test_contract_hash_ignores_l1_l3_and_text_rationale(self):
        """J1 行为契约哈希：L1/L3 变化与文案润色不触发。"""
        doc = make_doc()
        h1 = doc.contract_hash()
        doc.intent = "新的意图描述"
        doc.clauses[2].text = "改用浮点"
        assert doc.contract_hash() == h1
        doc.clauses[1].text = "退款金额精确到厘"  # L2 变了
        assert doc.contract_hash() != h1

    def test_bound_ratio(self):
        doc = make_doc()
        # REQ-1 (无见证, L1) + CON-1 (有见证, L2) → 1/2
        assert doc.bound_clause_ratio() == pytest.approx(0.5)


class TestStore:
    def test_delta_apply_and_version_chain(self, tmp_path):
        store = SpecStore(str(tmp_path))
        doc = make_doc()
        v0 = store.init_domain(doc)
        delta = SpecDelta(
            delta_id="D1", wave_id="W1", base_version=v0,
            clauses_added=[clause("CON-2", text="支持部分退款")],
        )
        v1 = store.apply_delta("pay", delta)
        assert v1 != v0
        assert store.load_domain("pay").clause("CON-2") is not None
        chain = store.version_chain()
        assert len(chain) == 1 and chain[0].delta_id == "D1"

    def test_stale_delta_rejected(self, tmp_path):
        store = SpecStore(str(tmp_path))
        v0 = store.init_domain(make_doc())
        delta = SpecDelta(delta_id="D1", wave_id="W1", base_version="deadbeef")
        with pytest.raises(SpecConflictError):
            store.apply_delta("pay", delta)

    def test_dontcare_dedup(self, tmp_path):
        store = SpecStore(str(tmp_path))
        v0 = store.init_domain(make_doc())
        dc = DontCareEntry(entry_id="DC-1", clause_id="CON-1", dimension="log.*")
        d1 = SpecDelta(delta_id="D1", wave_id="W1", base_version=v0, dont_cares_added=[dc])
        v1 = store.apply_delta("pay", d1)
        d2 = SpecDelta(delta_id="D2", wave_id="W2", base_version=v1, dont_cares_added=[dc])
        store.apply_delta("pay", d2)
        assert len(store.load_domain("pay").dont_cares) == 1


class TestInterfaceLock:
    def test_overlapping_lock_rejected(self, tmp_path):
        store = SpecStore(str(tmp_path))
        store.acquire_lock(InterfaceLock("W1", ["CON-1", "CON-2"]))
        with pytest.raises(SpecConflictError):
            store.acquire_lock(InterfaceLock("W2", ["CON-2", "CON-3"]))

    def test_disjoint_lock_ok(self, tmp_path):
        store = SpecStore(str(tmp_path))
        store.acquire_lock(InterfaceLock("W1", ["CON-1"]))
        store.acquire_lock(InterfaceLock("W2", ["CON-9"]))  # 不相交
        store.release_lock("W1")
        store.acquire_lock(InterfaceLock("W3", ["CON-1"]))  # 释放后可锁

    def test_expired_lock_no_conflict(self, tmp_path):
        store = SpecStore(str(tmp_path))
        lock = InterfaceLock("W1", ["CON-1"], ttl_seconds=-1)
        store.acquire_lock(lock)
        assert store.active_locks()[0].expired()
        store.acquire_lock(InterfaceLock("W2", ["CON-1"]))  # 过期锁不阻塞


class TestRRegistry:
    def test_first_match_and_default_r0(self):
        reg = RRegistry(rules=[
            ArtifactRule("migrations/**", RLevel.R3, golden_locked=True),
            ArtifactRule("api/**", RLevel.R2),
            ArtifactRule("internal/**", RLevel.R1),
        ])
        assert reg.classify("migrations/0001.sql") == RLevel.R3
        assert reg.classify("api/v2/handler.py") == RLevel.R2
        assert reg.classify("anything/else.py") == RLevel.R0

    def test_operation_guard_inv11(self):
        reg = RRegistry(rules=[ArtifactRule("migrations/**", RLevel.R3)])
        with pytest.raises(OperationError):
            reg.check_operation("migrations/0001.sql", "fanout")
        with pytest.raises(OperationError):
            reg.check_operation("migrations/0001.sql", "discard")
        reg.check_operation("migrations/0001.sql", "append_only")  # OK

    def test_required_gates_union(self):
        reg = RRegistry(rules=[ArtifactRule("migrations/**", RLevel.R3)])
        gates = reg.required_gates(["migrations/x.sql", "src/a.py"])
        assert "H5" in gates and "H4" in gates  # R3 需要 H5；R0 不需要
        assert gates >= {"H1", "H2", "H3", "H6"}


class TestDeltaSolvency:
    def test_removing_bound_l2_flagged(self):
        doc = make_doc()
        delta = SpecDelta(delta_id="D", wave_id="W", base_version="x",
                          clauses_removed=["CON-1"])
        problems = validate_delta_solvency(delta, doc)
        assert any("bound L2" in p for p in problems)

    def test_witnessless_clause_advisory_only(self):
        doc = make_doc()
        delta = SpecDelta(delta_id="D", wave_id="W", base_version="x",
                          clauses_added=[clause("CON-7", witnesses=False)])
        problems = validate_delta_solvency(delta, doc)
        assert any("advisory only" in p for p in problems)
