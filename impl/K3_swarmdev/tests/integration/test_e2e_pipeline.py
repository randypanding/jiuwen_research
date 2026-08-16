import sys
from pathlib import Path

import pytest

from swarmdev.admission.orchestrator import AdmissionOrchestrator, BuiltInstance
from swarmdev.contracts import (
    CapabilityError, ContractBus, EnvelopeKind, JudgeVerdict, OracleBundle,
    RLevel, Role, SoftVerdict, SpecDoc, VisibilityError, Wave, WaveTask,
    WitnessRef, make_token,
)
from swarmdev.contracts.oracle import Expectation, HoldoutScenario
from swarmdev.contracts.receipt import GateStatus
from swarmdev.contracts.spec_doc import WitnessKind
from swarmdev.contracts.wave import FanoutPolicy, WaveState
from swarmdev.drift.detector import DriftDetector
from swarmdev.gates.h7_drift import DriftGate
from swarmdev.gates.protocol import GateContext
from swarmdev.integration.wiring import build_gate_runner, drift_detector_callable
from swarmdev.oracle.diff_engine import DifferentialEngine, RunOutput
from swarmdev.oracle.golden import GoldenManifest, GoldenStore

GOOD_IMPL = '''def compute(x):
    """# @REQ-CL-C1@"""
    return x * 2
'''
BAD_IMPL = '''def compute(x):
    """# @REQ-CL-C1@"""
    return x * 3
'''
DRIFT_IMPL = '''def compute(x):
    """# @REQ-CL-C1@ # @REQ-CL-ZZ@"""
    return x * 2
'''
CHECKS = '''from impl import compute
assert compute(3) == 6
print("ok")
'''
PY = sys.executable


def make_spec() -> SpecDoc:
    return SpecDoc(
        spec_id="SPEC-e2e-0001", domain="demo", version="1.0.0",
        l1_intent="compute(x) doubles its input",
        l2_clauses=[{
            "clause_id": "CL-C1", "title": "doubling contract",
            "guarantees": ["compute(x) == 2*x for all int x"],
            "witnesses": [
                {"kind": WitnessKind.HOLDOUT_SCENARIO, "ref_id": "SCN-1"},
                {"kind": WitnessKind.DIFFERENTIAL, "ref_id": "DIFF-1"},
            ],
        }],
    )


def make_bundle() -> OracleBundle:
    return OracleBundle(
        bundle_id="ORC-e2e", spec_id="SPEC-e2e-0001", spec_version="1.0.0",
        scenarios=[HoldoutScenario(
            scenario_id="SCN-1", spec_clause_ids=["CL-C1"], title="double 21",
            run_command=f'{PY} -c "from impl import compute; print(compute(21))"',
            timeout_s=30.0,
            expectation=Expectation(exit_code=0, stdout_regex=r"^42\s*$"),
        )],
    )


def write_instance(root: Path, name: str, impl_src: str) -> Path:
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "impl.py").write_text(impl_src, encoding="utf-8")
    (d / "run_checks.py").write_text(CHECKS, encoding="utf-8")
    return d


def diff_runner(instance_dir: Path, inp: str) -> RunOutput:
    import subprocess
    proc = subprocess.run(
        [PY, "-c", f"from impl import compute; print(repr(compute({inp})))"],
        cwd=instance_dir, capture_output=True, text=True, timeout=30,
    )
    return RunOutput(exit_code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


class Harness:
    def __init__(self, tmp_path: Path, impls: list[str], r_level: RLevel = RLevel.R0,
                 golden_artifact: str | None = None, bundle: OracleBundle | None = None):
        self.tmp_path = tmp_path
        self.impls = impls
        self.spec = make_spec()
        self.bundle = bundle or make_bundle()
        self.registry: dict[str, Path] = {}
        self.cursor = 0
        self.bus = ContractBus()
        engine = DifferentialEngine(diff_runner)
        golden_store = None
        if golden_artifact is not None:
            golden_store = GoldenStore(tmp_path / "golden")
        self.golden_store = golden_store
        self.golden_artifact = golden_artifact
        self.runner = build_gate_runner(
            build_commands=[[PY, "-m", "py_compile", "impl.py"]],
            test_command=[PY, "run_checks.py"],
            bundle=self.bundle,
            diff_engine=engine,
            diff_inputs=["1", "2", "7"],
            golden_store=golden_store,
            golden_artifact_id=golden_artifact,
            dangerous_patterns=[r"eval\(", r"os\.system\("],
            drift_detector=DriftDetector(None),
            fail_fast=False,
        )
        self.engine = engine
        self.r_level = r_level

    def builder_factory(self, task: WaveTask, index: int) -> BuiltInstance:
        impl = self.impls[self.cursor % len(self.impls)]
        self.cursor += 1
        d = write_instance(self.tmp_path / "instances", f"{task.ru_id}-{index}", impl)
        instance_id = f"INST-{task.ru_id}-{index}"
        self.registry[instance_id] = d
        return BuiltInstance(instance_id=instance_id, instance_dir=str(d),
                             tier="M", cost_tokens=100)

    def gate_executor(self, built: BuiltInstance, task: WaveTask):
        ctx = GateContext(
            workspace=Path(built.instance_dir), spec=self.spec,
            instance_id=built.instance_id, instance_dir=Path(built.instance_dir),
            r_level=task.r_level, bundle=self.bundle, surface_snapshot=None,
            cost_record={"tokens": built.cost_tokens, "duration_s": 1.0},
            extra={"token": make_token(Role.VERIFIER, "verifier", "wave"),
                   "instance_dirs": {iid: p for iid, p in self.registry.items()}},
        )
        return self.runner.run(ctx)

    def orchestrator(self, soft_judge=None) -> AdmissionOrchestrator:
        return AdmissionOrchestrator(
            builder_factory=self.builder_factory,
            gate_executor=self.gate_executor,
            soft_judge=soft_judge,
            bus=self.bus,
        )

    def wave(self, n: int, r_level: RLevel | None = None) -> Wave:
        return Wave(
            wave_id="WAVE-e2e-1", spec_delta_ids=["DLT-e2e"],
            tasks=[WaveTask(ru_id="RU-compute", spec_delta_ref="DLT-e2e",
                            r_level=r_level or self.r_level,
                            fanout=FanoutPolicy(n_target=n))],
        )


def test_wave_admits_when_closed(tmp_path):
    h = Harness(tmp_path, impls=[GOOD_IMPL])
    out = h.orchestrator().execute_wave(h.wave(3), h.spec, h.bundle)
    assert out.admitted
    assert out.final_state == WaveState.COMMITTED
    assert out.outcomes["RU-compute"] == "CLOSED"
    receipt = out.receipts[0]
    assert receipt.admitted and receipt.commit_ref
    assert {o.gate_id for o in receipt.hard_gate_outcomes} >= {"H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"}
    assert all(o.status == GateStatus.PASS for o in receipt.hard_gate_outcomes)

    audit = h.bus.audit_stream()
    assert audit
    for env in audit:
        if env.kind in (EnvelopeKind.JUDGE_REQUEST, EnvelopeKind.HOLDOUT_RESULTS,
                        EnvelopeKind.MEASUREMENT_REPORT):
            assert Role.BUILDER not in env.recipients
    assignments = [e for e in audit if e.kind == EnvelopeKind.SPEC_ASSIGNMENT]
    assert assignments
    for env in assignments:
        assert set(env.payload.keys()) == {"spec_id", "version", "ru_id", "l1_intent"}
    builder = make_token(Role.BUILDER, "any", "wave")
    with pytest.raises(VisibilityError):
        h.bus.query(builder, EnvelopeKind.JUDGE_REQUEST)
    with pytest.raises(CapabilityError):
        h.bus.publish(builder, EnvelopeKind.GATE_RESULTS, {}, [Role.LEADER])


def test_wave_detects_spec_silence_when_passing_instances_diverge(tmp_path):
    silence_impl = '''def compute(x):
    """# @REQ-CL-C1@"""
    if x == 7:
        return 15
    return x * 2
'''
    h = Harness(tmp_path, impls=[GOOD_IMPL, GOOD_IMPL, silence_impl])
    out = h.orchestrator().execute_wave(h.wave(3), h.spec, h.bundle)
    assert not out.admitted
    assert out.outcomes["RU-compute"] == "SILENCE"
    assert out.final_state == WaveState.ROLLED_BACK
    report = [e for e in h.bus.audit_stream()
              if e.kind == EnvelopeKind.MEASUREMENT_REPORT]
    assert report and report[0].payload["outcome"] == "SILENCE"


def test_wave_rejects_on_behavior_divergence(tmp_path):
    h = Harness(tmp_path, impls=[GOOD_IMPL, GOOD_IMPL, BAD_IMPL])
    out = h.orchestrator().execute_wave(h.wave(3), h.spec, h.bundle)
    assert not out.admitted
    assert out.final_state == WaveState.ROLLED_BACK
    assert out.outcomes["RU-compute"] == "DIVERGENCE"
    receipt = out.receipts[0]
    assert receipt.admitted is False
    assert receipt.rollback_ref == "rollback:WAVE-e2e-1"
    assert receipt.discarded_instances
    assert all(d.measurement_conclusion for d in receipt.discarded_instances)


def test_wave_rejects_on_judge_veto(tmp_path):
    h = Harness(tmp_path, impls=[GOOD_IMPL])

    def veto_judge(built, task):
        return [SoftVerdict(rubric_id="RUB-1",
                            judge=JudgeVerdict(verdict="veto",
                                               reasons=["contract clarity insufficient"],
                                               evidence_refs=["rubric:RUB-1"]))]

    out = h.orchestrator(soft_judge=veto_judge).execute_wave(h.wave(3), h.spec, h.bundle)
    assert not out.admitted
    assert out.final_state == WaveState.ROLLED_BACK
    verdicts = [e for e in h.bus.audit_stream() if e.kind == EnvelopeKind.JUDGE_VERDICT]
    assert verdicts and all(e.sender_role == Role.JUDGE for e in verdicts)


def test_wave_rejects_on_spec_code_drift(tmp_path):
    h = Harness(tmp_path, impls=[GOOD_IMPL, GOOD_IMPL, DRIFT_IMPL])
    out = h.orchestrator().execute_wave(h.wave(3), h.spec, h.bundle)
    assert not out.admitted
    assert out.outcomes["RU-compute"] == "DIVERGENCE"


def test_r3_requires_golden_witness(tmp_path):
    h = Harness(tmp_path, impls=[GOOD_IMPL], r_level=RLevel.R3,
                golden_artifact="ART-compute")
    out = h.orchestrator().execute_wave(h.wave(1, r_level=RLevel.R3), h.spec, h.bundle)
    assert not out.admitted
    assert out.final_state == WaveState.ROLLED_BACK


def test_r3_golden_path_admits_with_human_approved_snapshot(tmp_path):
    h = Harness(tmp_path, impls=[GOOD_IMPL], r_level=RLevel.R3,
                golden_artifact="ART-compute")
    ref = write_instance(tmp_path / "ref", "ref", GOOD_IMPL)
    diff_gate = next(g for g in h.runner.gates if g.gate_id == "H5")
    content = diff_gate.golden_content({"INST-RU-compute-0": ref}, ["1", "2", "7"])
    h.golden_store.save("ART-compute", content, GoldenManifest(
        spec_hash="sha:spec", seed="fixed", lock_hash="sha:lock",
        approved_by="human:alice"))
    out = h.orchestrator().execute_wave(h.wave(1, r_level=RLevel.R3), h.spec, h.bundle)
    assert out.admitted
    assert out.final_state == WaveState.COMMITTED
    h5 = [o for o in out.receipts[0].hard_gate_outcomes if o.gate_id == "H5"][0]
    assert h5.status == GateStatus.PASS


def test_h7_wiring_direct(tmp_path):
    spec = make_spec()
    clean_dir = write_instance(tmp_path, "clean", GOOD_IMPL)
    dirty_dir = write_instance(tmp_path, "dirty", DRIFT_IMPL)
    gate = DriftGate(drift_detector_callable(DriftDetector(None)))
    ctx_clean = GateContext(workspace=clean_dir, spec=spec, instance_id="i1",
                            instance_dir=clean_dir, r_level=RLevel.R0)
    ctx_dirty = GateContext(workspace=dirty_dir, spec=spec, instance_id="i2",
                            instance_dir=dirty_dir, r_level=RLevel.R0)
    assert gate.run(ctx_clean).status == GateStatus.PASS
    dirty_outcome = gate.run(ctx_dirty)
    assert dirty_outcome.status == GateStatus.FAIL
    assert "unknown_tag_reference" in dirty_outcome.details
