from __future__ import annotations


import pytest

from opc.fixtures_gen import CONTRACT_YAML, REGISTRY_YAML
from opc.oracle.judge import (
    JudgeContext,
    JudgeWorkflow,
    ModelLineageRegistry,
    RelayPackage,
    RubricConfig,
    RubricDimension,
    build_relay,
)
from opc.schemas.common import RLevel, Verdict
from opc.schemas.events import Envelope, Topic
from opc.schemas.gates import GateReport
from opc.schemas.oracle import JudgeSample
from opc.schemas.spec import ContractSpec
from opc.schemas.wave import InstanceRecord, WaveManifest
from opc.world.admission import AdmissionController, AdmissionError
from opc.world.bus import EventBus, RoutingViolation
from opc.world.ledger import AdmissionLedger
from opc.world.sanitizer import HoldoutLeak, package_builder_workspace


class TestContractRoundTrips:
    """Every inter-contract artifact must survive producer->consumer serialization."""

    def test_contract_spec_round_trip(self):
        import yaml

        contract = ContractSpec.model_validate(yaml.safe_load(CONTRACT_YAML))
        wire = contract.model_dump_json()
        restored = ContractSpec.model_validate_json(wire)
        assert restored == contract
        assert restored.r_level is RLevel.R1

    def test_gate_report_round_trip(self):
        report = GateReport(gate="H3", verdict=Verdict.PASS, instance_id="inst-a", wave_id="WAVE-1")
        restored = GateReport.model_validate_json(report.model_dump_json())
        assert restored.verdict is Verdict.PASS
        assert restored.gate == "H3"

    def test_envelope_round_trip(self):
        envelope = Envelope(
            topic=Topic.TASK_ASSIGN,
            src_role="leader",
            dst_role="builder",
            wave_id="WAVE-1",
            payload={"spec_delta_ref": "abc", "contract_id": "CTR-payments-core"},
        )
        restored = Envelope.model_validate_json(envelope.model_dump_json())
        assert restored.digest() == envelope.digest()

    def test_wave_manifest_rejects_bad_ids(self):
        with pytest.raises(ValueError):
            WaveManifest(wave_id="wave-1", spec_version="1.0.0")


class TestBusRoutingContract:
    def test_all_legal_routes_deliver(self):
        from opc.world.bus import ROUTING_TABLE

        bus = EventBus()
        received: list[Envelope] = []
        for src, dst, topic in sorted(ROUTING_TABLE, key=lambda r: (r[2].value, r[0], r[1])):
            bus.subscribe(dst, topic, received.append)
        for src, dst, topic in sorted(ROUTING_TABLE, key=lambda r: (r[2].value, r[0], r[1])):
            bus.publish(Envelope(topic=topic, src_role=src, dst_role=dst, payload={}))
        assert len(received) == len(ROUTING_TABLE)
        assert bus.violations == []

    def test_illegal_route_blocked_and_journaled(self):
        bus = EventBus()
        with pytest.raises(RoutingViolation):
            bus.publish(Envelope(topic=Topic.GATE_REPORT, src_role="builder", dst_role="leader"))
        assert len(bus.violations) == 1
        assert bus.journal == []

    def test_builder_only_receives_task_assign(self):
        bus = EventBus()
        with pytest.raises(RoutingViolation):
            bus.publish(
                Envelope(
                    topic=Topic.MEASUREMENT_REPORT,
                    src_role="verifier",
                    dst_role="builder",
                ),
                )
        assert "legal route" in bus.violations[-1]["reason"] or "route" in bus.violations[-1]["reason"]

    def test_oracle_side_keys_never_reach_builder(self):
        bus = EventBus()
        for forbidden_key in ("scenarios", "rubric", "judge_verdict", "golden_outputs"):
            with pytest.raises(RoutingViolation):
                bus.publish(
                    Envelope(
                        topic=Topic.TASK_ASSIGN,
                        src_role="leader",
                        dst_role="builder",
                        payload={forbidden_key: "leak"},
                    )
                )
        assert len(bus.violations) == 4

    def test_instance_submit_must_come_from_builder(self):
        bus = EventBus(extra_routes={("verifier", "verifier", Topic.INSTANCE_SUBMIT)})
        with pytest.raises(RoutingViolation):
            bus.publish(
                Envelope(topic=Topic.INSTANCE_SUBMIT, src_role="verifier", dst_role="verifier")
            )

    def test_audit_trail_is_complete(self):
        bus = EventBus()
        bus.publish(Envelope(topic=Topic.TASK_ASSIGN, src_role="leader", dst_role="builder"))
        bus.publish(Envelope(topic=Topic.INSTANCE_SUBMIT, src_role="builder", dst_role="verifier"))
        audit = bus.audit()
        assert [a["topic"] for a in audit] == ["task.assign", "instance.submit"]
        assert all(a["digest"].startswith("sha256:") for a in audit)


class TestJudgeWorkflowContract:
    def _rubric(self, **overrides) -> RubricConfig:
        defaults = dict(
            rubric_id="RUB-readability",
            dimensions=[RubricDimension(name="clarity", criteria="claims are specific and evidenced")],
            judge_model="judge-strong",
        )
        defaults.update(overrides)
        return RubricConfig(**defaults)

    def _relay(self) -> RelayPackage:
        return build_relay(
            {
                "instance_id": "inst-a",
                "claims": ["fee rounded half-even"],
                "evidence": ["H3 SCN-pay-001 passed"],
                "scenario_ids": ["SCN-pay-001"],
            }
        )

    def test_judge_rejects_without_evidence_samples(self):
        class NoEvidenceJudge:
            model_id = "judge-strong"

            def sample(self, context: JudgeContext) -> JudgeSample:
                return JudgeSample(sample_index=context.sample_index, verdict="no_reject", reasons=[], evidence=[])

        workflow = JudgeWorkflow(NoEvidenceJudge())
        verdict = workflow.judge(self._relay(), self._rubric(samples_k=3, require_pairwise_swap=False))
        assert verdict.verdict is Verdict.INCONCLUSIVE
        assert verdict.abstained

    def test_judge_majority_reject_with_evidence(self):
        calls = {"n": 0}

        class MajorityJudge:
            model_id = "judge-strong"

            def sample(self, context: JudgeContext) -> JudgeSample:
                calls["n"] += 1
                reject = context.sample_index < 2
                return JudgeSample(
                    sample_index=context.sample_index,
                    verdict="reject" if reject else "no_reject",
                    reasons=["violates clarity"] if reject else [],
                    evidence=["claim lacks citation"],
                )

        workflow = JudgeWorkflow(MajorityJudge())
        verdict = workflow.judge(self._relay(), self._rubric(samples_k=3, require_pairwise_swap=False))
        assert verdict.verdict is Verdict.FAIL
        assert calls["n"] == 3

    def test_judge_same_family_refused(self):
        class FineJudge:
            model_id = "builder-family-large"

            def sample(self, context: JudgeContext) -> JudgeSample:
                return JudgeSample(sample_index=0, verdict="no_reject", evidence=["e"])

        lineage = ModelLineageRegistry(families={"builder-family-large": "fam-x", "judge-strong": "fam-x"})
        workflow = JudgeWorkflow(FineJudge(), lineage=lineage)
        verdict = workflow.judge(self._relay(), self._rubric(), generator_model="builder-family-large")
        assert verdict.verdict is Verdict.INCONCLUSIVE
        assert any("family" in r for r in verdict.reasons)

    def test_judge_weaker_tier_refused(self):
        class WeakJudge:
            model_id = "judge-small"

            def sample(self, context: JudgeContext) -> JudgeSample:
                return JudgeSample(sample_index=0, verdict="no_reject", evidence=["e"])

        workflow = JudgeWorkflow(WeakJudge(), tier_table={"judge-small": 1, "builder-large": 3})
        verdict = workflow.judge(
            self._relay(), self._rubric(judge_model="judge-small"), builder_tier="builder-large"
        )
        assert verdict.verdict is Verdict.INCONCLUSIVE
        assert verdict.abstained

    def test_relay_never_carries_raw_reasoning(self):
        relay = build_relay(
            {
                "instance_id": "inst-a",
                "claims": ["c"],
                "evidence": ["e"],
                "reasoning_chain": ["step1", "step2"],
                "rubric_text": "secret rubric",
            }
        )
        dumped = relay.model_dump()
        assert "reasoning_chain" not in dumped
        assert "rubric_text" not in dumped


class TestSanitizerContract:
    def test_builder_bundle_excludes_oracle_dirs(self, tmp_path, fixtures_root):
        spec_dir = fixtures_root / "spec_repo"
        holdout_dir = fixtures_root / "holdout"
        dest = tmp_path / "builder_ws"
        bundle_hash = package_builder_workspace(spec_dir, dest, holdout_dir)
        assert bundle_hash.startswith("sha256:")
        assert not (dest / "oracle").exists()
        bundled = "\n".join(p.read_text(encoding="utf-8") for p in dest.rglob("*") if p.is_file())
        assert "CANARY-8f2e1d-pay-001-77aa" not in bundled
        assert "CANARY-3b9c4e-pay-002-19df" not in bundled
        assert "123.455" not in bundled

    def test_builder_bundle_raises_on_holdout_leak(self, tmp_path, fixtures_root):
        spec_dir = tmp_path / "leaky_spec"
        (spec_dir / "L2").mkdir(parents=True)
        (spec_dir / "registry.yaml").write_text(REGISTRY_YAML, encoding="utf-8")
        (spec_dir / "L2" / "notes.md").write_text(
            "builder notes: CANARY-8f2e1d-pay-001-77aa", encoding="utf-8"
        )
        with pytest.raises(HoldoutLeak):
            package_builder_workspace(spec_dir, tmp_path / "out", fixtures_root / "holdout")


class TestWaveLifecycleContract:
    """End-to-end contract communication of one wave across all roles."""

    def test_full_wave_flow_preserves_information_asymmetry(self, tmp_path, fixtures_root):
        bus = EventBus()
        ledger = AdmissionLedger(tmp_path / "ledger.jsonl")
        controller = AdmissionController(ledger)

        seen_by_builder: list[Envelope] = []
        seen_by_moderator: list[Envelope] = []
        seen_by_leader: list[Envelope] = []
        bus.subscribe("builder", Topic.TASK_ASSIGN, seen_by_builder.append)
        bus.subscribe("spec_moderator", Topic.MEASUREMENT_REPORT, seen_by_moderator.append)
        bus.subscribe("leader", Topic.GATE_REPORT, seen_by_leader.append)

        wave = WaveManifest(
            wave_id="WAVE-001",
            spec_version="1.0.0",
            contract_ids=["CTR-payments-core"],
            spec_delta_refs=["delta-1"],
            fanout_n=3,
            r_levels={"CTR-payments-core": RLevel.R1},
        )
        controller.begin_wave(wave)

        bus.publish(
            Envelope(
                topic=Topic.TASK_ASSIGN,
                src_role="architect",
                dst_role="leader",
                wave_id=wave.wave_id,
                payload={"contract_id": "CTR-payments-core", "fanout_n": 3},
            )
        )
        bus.publish(
            Envelope(
                topic=Topic.TASK_ASSIGN,
                src_role="leader",
                dst_role="builder",
                wave_id=wave.wave_id,
                payload={"contract_id": "CTR-payments-core", "workspace_hash": "sha256:abc"},
            )
        )

        for name in ("inst-a", "inst-b", "inst-c"):
            controller.stage_instance(
                wave.wave_id, InstanceRecord(instance_id=name, builder_id="builder-1", status="submitted")
            )
            bus.publish(
                Envelope(
                    topic=Topic.INSTANCE_SUBMIT,
                    src_role="builder",
                    dst_role="verifier",
                    wave_id=wave.wave_id,
                    payload={"instance_id": name},
                )
            )

        bus.publish(
            Envelope(
                topic=Topic.GATE_REPORT,
                src_role="verifier",
                dst_role="leader",
                wave_id=wave.wave_id,
                payload={"instance_id": "inst-a", "gates": {"H1": "pass", "H2": "pass"}},
            )
        )
        bus.publish(
            Envelope(
                topic=Topic.MEASUREMENT_REPORT,
                src_role="verifier",
                dst_role="spec_moderator",
                wave_id=wave.wave_id,
                payload={"kind": "silence", "divergence_inputs": ["IN-003"]},
            )
        )
        bus.publish(
            Envelope(
                topic=Topic.SPEC_CONVERGE,
                src_role="spec_moderator",
                dst_role="spec_steward",
                wave_id=wave.wave_id,
                payload={"clause": "REQ-payments-001", "action": "clarify rounding tie-break"},
            )
        )

        soft = GateReport(gate="S", verdict=Verdict.PASS, instance_id="inst-a", wave_id=wave.wave_id)
        from opc.schemas.gates import AdmissionVerdict

        hard = {f"H{i}": GateReport(gate=f"H{i}", verdict=Verdict.PASS, instance_id="inst-a", wave_id=wave.wave_id) for i in range(1, 9)}
        verdict = AdmissionVerdict.decide(hard, soft)
        receipt = controller.admit(
            wave.wave_id,
            verdict,
            selected="inst-a",
            discarded={"inst-b": "equivalent to inst-a under corpus; no new spec information", "inst-c": "diverged at IN-003: silence candidate, routed to moderator"},
            gate_hashes={g: r.model_dump_json()[:20] for g, r in hard.items()},
            spec_delta_ref="delta-1",
            r_level=RLevel.R1,
        )
        bus.publish(
            Envelope(
                topic=Topic.ADMIT_COMMIT,
                src_role="world",
                dst_role="leader",
                wave_id=wave.wave_id,
                payload={"receipt_id": receipt.receipt_id},
            )
        )
        controller.commit(wave.wave_id, commit_hash="sha256:" + "1" * 64)

        assert len(seen_by_builder) == 1
        builder_payload = seen_by_builder[0].payload
        assert not ({"scenarios", "rubric", "judge_verdict"} & set(builder_payload))
        assert len(seen_by_moderator) == 1
        assert seen_by_moderator[0].payload["kind"] == "silence"
        ok, problems = ledger.verify()
        assert ok, problems
        assert controller.transactions[wave.wave_id].committed
        assert controller.waves[wave.wave_id].status == "committed"

    def test_admit_refuses_blocking_verdict(self, tmp_path):
        controller = AdmissionController(AdmissionLedger(tmp_path / "l.jsonl"))
        wave = WaveManifest(wave_id="WAVE-002", spec_version="1.0.0")
        controller.begin_wave(wave)
        from opc.schemas.gates import AdmissionVerdict

        blocked = AdmissionVerdict(
            admitted=False,
            hard_verdicts={"H3": Verdict.FAIL},
            soft_verdict=Verdict.PASS,
            blocking_gates=["H3"],
        )
        with pytest.raises(AdmissionError):
            controller.admit(wave.wave_id, blocked, "inst-x", {}, {}, "delta", RLevel.R0)

    def test_discard_without_measurement_note_refused(self, tmp_path):
        controller = AdmissionController(AdmissionLedger(tmp_path / "l.jsonl"))
        wave = WaveManifest(wave_id="WAVE-003", spec_version="1.0.0")
        controller.begin_wave(wave)
        controller.stage_instance(wave.wave_id, InstanceRecord(instance_id="inst-a", builder_id="b"))
        controller.stage_instance(wave.wave_id, InstanceRecord(instance_id="inst-b", builder_id="b"))
        from opc.schemas.gates import AdmissionVerdict

        verdict = AdmissionVerdict(admitted=True, hard_verdicts={}, soft_verdict=Verdict.PASS)
        with pytest.raises(AdmissionError):
            controller.admit(wave.wave_id, verdict, "inst-a", {"inst-b": "   "}, {}, "delta", RLevel.R0)

    def test_fanout_forbidden_for_r3(self, tmp_path):
        controller = AdmissionController(AdmissionLedger(tmp_path / "l.jsonl"))
        wave = WaveManifest(wave_id="WAVE-004", spec_version="1.0.0")
        controller.begin_wave(wave)
        violation = controller.fanout_policy_violation(wave.wave_id, "CTR-x", fanout_n=3)
        assert violation is None
        wave.r_levels["CTR-x"] = RLevel.R3
        violation = controller.fanout_policy_violation(wave.wave_id, "CTR-x", fanout_n=3)
        assert violation is not None and "R3" in violation
