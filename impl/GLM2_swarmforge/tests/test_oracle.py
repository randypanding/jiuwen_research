"""Oracle 契约测试：holdout 访问控制（信息不对称物理层）、差分引擎、黄金门。"""
import pytest

from swarmforge.oracle import (
    DiffConclusion,
    DifferentialEngine,
    DiffInputGenerator,
    GoldenGate,
    GoldenManifest,
    HoldoutAccessDenied,
    HoldoutScenario,
    HoldoutStore,
    JudgeOutput,
    JudgeRubric,
    JudgeVerdict,
    OutputNormalizer,
    ScenarioVisibility,
)
from swarmforge.specrepo import DontCareEntry


def scenario(sid="SC-pay-0001", visibility=ScenarioVisibility.HOLDOUT):
    return HoldoutScenario(
        scenario_id=sid, domain="pay", visibility=visibility,
        clause_ids=["CON-1"], stimulus={"amount": 100},
        expected={"refunded": 10000},
    )


class TestHoldoutIsolation:
    def test_builder_cannot_read_holdout(self, tmp_path):
        store = HoldoutStore(str(tmp_path))
        store.put(scenario())
        with pytest.raises(HoldoutAccessDenied):
            store.get("SC-pay-0001", reader_role="builder")

    def test_builder_cannot_list_holdout(self, tmp_path):
        store = HoldoutStore(str(tmp_path))
        store.put(scenario())
        with pytest.raises(HoldoutAccessDenied):
            store.list_ids(ScenarioVisibility.HOLDOUT, reader_role="builder")

    def test_verifier_reads_and_audited(self, tmp_path):
        store = HoldoutStore(str(tmp_path))
        store.put(scenario())
        sc = store.get("SC-pay-0001", reader_role="verifier")
        assert sc.expected == {"refunded": 10000}
        audit = store.audit_tail()
        assert audit[-1]["allowed"] is True and audit[-1]["role"] == "verifier"

    def test_denied_attempt_is_audited(self, tmp_path):
        store = HoldoutStore(str(tmp_path))
        store.put(scenario())
        with pytest.raises(HoldoutAccessDenied):
            store.get("SC-pay-0001", reader_role="builder")
        audit = store.audit_tail()
        assert audit[-1]["allowed"] is False  # 取证面：失败尝试留痕

    def test_open_scenario_visible_to_builder(self, tmp_path):
        store = HoldoutStore(str(tmp_path))
        store.put(scenario("SC-pay-0002", ScenarioVisibility.OPEN))
        sc = store.get("SC-pay-0002", reader_role="builder")
        assert sc.visibility == ScenarioVisibility.OPEN


class TestNormalizer:
    def test_strips_nondeterminism(self):
        n = OutputNormalizer(drop_keys={"timestamp", "session_id"})
        a = n.normalize({"ok": True, "timestamp": 111, "session_id": "aaa"})
        b = n.normalize({"session_id": "bbb", "timestamp": 222, "ok": True})
        assert a == b

    def test_redaction(self):
        n = OutputNormalizer(redact_patterns=[r"req-[0-9a-f]+"])
        assert "req-" not in n.normalize({"trace": "req-abc123 started"})

    def test_float_noise(self):
        n = OutputNormalizer()
        assert n.normalize(0.1 + 0.2) == n.normalize(0.3)

    def test_real_difference_survives(self):
        n = OutputNormalizer(drop_keys={"timestamp"})
        assert n.normalize({"amount": 100}) != n.normalize({"amount": 101})


class TestDifferentialEngine:
    def test_equivalent_instances(self):
        eng = DifferentialEngine(OutputNormalizer(drop_keys={"timestamp"}))
        traces = {
            "I1": {"in-1": {"refunded": 1000}, "in-2": {"refunded": 2000}},
            "I2": {"in-1": {"refunded": 1000, "timestamp": 1}, "in-2": {"refunded": 2000}},
        }
        rep = eng.compare("W1", "D1", traces, ["in-1", "in-2"], dont_cares=[])
        assert rep.conclusion == DiffConclusion.EQUIVALENT

    def test_difference_found_is_spec_silence(self):
        eng = DifferentialEngine()
        traces = {
            "I1": {"in-1": {"refunded": 1000}},
            "I2": {"in-1": {"refunded": 1000, "receipt_no": "R-1"}},  # I2 多了未定义行为
        }
        rep = eng.compare("W1", "D1", traces, ["in-1"], dont_cares=[])
        assert rep.conclusion == DiffConclusion.DIFFERENCE_FOUND
        assert rep.divergent_inputs == ["in-1"]

    def test_difference_within_dontcare_zone_is_legal(self):
        eng = DifferentialEngine()
        dcs = [DontCareEntry(entry_id="DC-1", clause_id="CON-1",
                             dimension="*.receipt_no")]
        traces = {
            "I1": {"in-1": {"refunded": 1000}},
            "I2": {"in-1": {"refunded": 1000, "receipt_no": "R-1"}},
        }
        rep = eng.compare("W1", "D1", traces, ["in-1"], dont_cares=dcs)
        assert rep.conclusion == DiffConclusion.EQUIVALENT
        assert "within registered don't-care" in rep.detail

    def test_perturbation_instability_is_inconclusive(self):
        """换 seed 复跑差异移位 → 非确定性嫌疑 → 统计通道。"""
        eng = DifferentialEngine()
        main = {
            "I1": {"in-1": {"v": 1}, "in-2": {"v": 1}},
            "I2": {"in-1": {"v": 2}, "in-2": {"v": 1}},
        }
        probe = {  # 扰动后差异消失
            "I1": {"in-1": {"v": 1}, "in-2": {"v": 1}},
            "I2": {"in-1": {"v": 1}, "in-2": {"v": 1}},
        }
        rep = eng.compare("W1", "D1", main, ["in-1", "in-2"], dont_cares=[],
                          probe_traces=probe)
        assert rep.conclusion == DiffConclusion.INCONCLUSIVE
        assert rep.nondet_suspects

    def test_fingerprint_order_sensitive(self):
        eng = DifferentialEngine()
        t1 = {"a": {"v": 1}, "b": {"v": 2}}
        t2 = {"a": {"v": 1}, "b": {"v": 3}}
        assert eng.fingerprint(t1) != eng.fingerprint(t2)


class TestDiffInputGenerator:
    def test_deterministic(self):
        g1 = DiffInputGenerator(seed=42)
        g2 = DiffInputGenerator(seed=42)
        s = {"amount": 100, "note": "x", "tags": ["a", "b"]}
        assert g1.perturb(s, 5) == g2.perturb(s, 5)

    def test_different_seed_differs(self):
        assert (DiffInputGenerator(seed=1).perturb({"n": 0}, 8)
                != DiffInputGenerator(seed=2).perturb({"n": 0}, 8))


class TestGoldenGate:
    def test_manifest_consistency(self):
        m = GoldenManifest(artifact_path="migrations/x", code_hash="c1", deps_hash="d1",
                           seed=7, normalizer_config_hash="n1", golden_hash="g1")
        ok, msg = GoldenGate.verify_manifest(m, "c1", "d1", 7, "n1")
        assert ok, msg
        ok, msg = GoldenGate.verify_manifest(m, "c1", "d1", 8, "n1")
        assert not ok and "seed" in msg

    def test_byte_compare(self):
        verdict, _ = GoldenGate.compare(b"abc", b"abc")
        assert verdict == "pass"
        verdict, detail = GoldenGate.compare(b"abc", b"abd")
        assert verdict == "fail" and "byte mismatch" in detail


class TestJudgeProtocol:
    def test_output_enum_roundtrip(self):
        jo = JudgeOutput(verdict=JudgeVerdict.ABSTAIN, reasons=["证据不足"],
                         evidence_citations=["receipt#1"])
        d = jo.to_dict()
        jo2 = JudgeOutput.from_dict(d)
        assert jo2.verdict == JudgeVerdict.ABSTAIN

    def test_rubric_shape(self):
        r = JudgeRubric(rubric_id="R1", dimension="契约符合度",
                        levels={"veto": "违反 L2 条款", "pass": "符合"},
                        sample_count=3)
        assert r.abstain_allowed and r.version == "1"
