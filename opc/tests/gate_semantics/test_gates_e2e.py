from __future__ import annotations

import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from opc.fixtures_gen import CONTRACT_YAML
from opc.gates.base import GateContext
from opc.gates.h1_build import H1BuildGate
from opc.gates.h2_tests import H2TestsGate
from opc.gates.h3_holdout import H3HoldoutGate
from opc.gates.h4_surface import H4ContractSurfaceGate
from opc.gates.h5_diff import H5DiffGate
from opc.gates.h6_constitution import H6ConstitutionGate
from opc.gates.h7_drift import H7DriftGate
from opc.gates.h8_budget import H8BudgetGate
from opc.gates.runner import GateRunner
from opc.gates.waivers import WaiverEntry
from opc.schemas.common import Verdict
from opc.schemas.gates import GateReport
from opc.specrepo.lint import lint_spec_repo, load_repo

PAYMENTS_BAD_ROUNDING = '''\
def compute_fee(amount: float, rate: float) -> dict:
    fee = int(amount * rate * 100) / 100.0
    return {"fee": fee, "currency": "CNY", "elapsed_ms": 0.0}
'''


@pytest.fixture()
def ctx_factory(spec_dir, holdout_dir, instances_dir, corpus_file):
    def make(instance: str, **overrides) -> GateContext:
        manifest = load_repo(spec_dir)
        kwargs = dict(
            instance_id=instance,
            instance_dir=instances_dir / instance,
            spec_dir=spec_dir,
            manifest=manifest,
            contract_id="CTR-payments-core",
            holdout_dir=holdout_dir,
            corpus_file=corpus_file,
            policy_file=spec_dir / "policy.yaml",
            wave_id="WAVE-T1",
        )
        kwargs.update(overrides)
        return GateContext(**kwargs)

    return make


class TestGateSemantics:
    def test_h1_passes_clean_instance(self, ctx_factory):
        report = H1BuildGate().run(ctx_factory("inst-a"))
        assert report.verdict is Verdict.PASS

    def test_h1_fails_syntax_error(self, ctx_factory, instances_dir):
        broken = instances_dir / "inst-broken"
        broken.mkdir(exist_ok=True)
        (broken / "payments.py").write_text("def compute_fee(:\n", encoding="utf-8")
        report = H1BuildGate().run(ctx_factory("inst-broken"))
        assert report.verdict is Verdict.FAIL

    def test_h2_passes_with_assertions(self, ctx_factory):
        report = H2TestsGate().run(ctx_factory("inst-a"))
        assert report.verdict is Verdict.PASS

    def test_h2_fails_smoke_without_alarm(self, ctx_factory):
        report = H2TestsGate().run(ctx_factory("inst-evil"))
        assert report.verdict is Verdict.FAIL
        signal = next(c for c in report.checks if c.id == "h2.oracle_signal")
        assert "lack effective assertions" in signal.detail

    def test_h3_passes_correct_instance(self, ctx_factory):
        report = H3HoldoutGate().run(ctx_factory("inst-a"))
        assert report.verdict is Verdict.PASS

    def test_h3_fails_wrong_behaviour(self, ctx_factory, instances_dir):
        bad = instances_dir / "inst-badround"
        bad.mkdir(exist_ok=True)
        (bad / "payments.py").write_text(PAYMENTS_BAD_ROUNDING, encoding="utf-8")
        report = H3HoldoutGate().run(ctx_factory("inst-badround"))
        assert report.verdict is Verdict.FAIL
        scn = next(c for c in report.checks if c.id == "h3.SCN-pay-001")
        assert scn.status is Verdict.FAIL

    def test_h3_fails_without_holdout_store(self, ctx_factory):
        ctx = ctx_factory("inst-a", holdout_dir=None)
        report = H3HoldoutGate().run(ctx)
        assert report.verdict is Verdict.FAIL

    def test_h4_detects_removed_contract_symbol(self, ctx_factory, instances_dir):
        stripped = instances_dir / "inst-stripped"
        if stripped.exists():
            shutil.rmtree(stripped)
        shutil.copytree(instances_dir / "inst-a", stripped)
        (stripped / "payments.py").write_text(
            "def fee(amount: float, rate: float) -> dict:\n    return {}\n", encoding="utf-8"
        )
        report = H4ContractSurfaceGate().run(
            ctx_factory("inst-stripped", baseline_dir=instances_dir / "inst-a")
        )
        assert report.verdict is Verdict.FAIL

    def test_h4_passes_compatible_reimplementation(self, ctx_factory, instances_dir):
        report = H4ContractSurfaceGate().run(
            ctx_factory("inst-b", baseline_dir=instances_dir / "inst-a")
        )
        assert report.verdict is Verdict.PASS

    def test_h5_diff_detects_silence(self, ctx_factory, instances_dir):
        ctx = ctx_factory(
            "inst-a",
            sibling_instances={
                "inst-a": instances_dir / "inst-a",
                "inst-b": instances_dir / "inst-b",
                "inst-c": instances_dir / "inst-c",
            },
        )
        ctx.extra["entrypoint"] = "payments:compute_fee"
        ctx.extra["redactions"] = ["elapsed_ms"]
        report = H5DiffGate().run(ctx)
        assert report.verdict is Verdict.FAIL
        assert "silence" in report.checks[-1].detail or "divergence" in report.checks[-1].detail.lower()

    def test_h5_diff_passes_equivalent_instances(self, ctx_factory, instances_dir):
        ctx = ctx_factory(
            "inst-a",
            sibling_instances={
                "inst-a": instances_dir / "inst-a",
                "inst-b": instances_dir / "inst-b",
            },
        )
        ctx.extra["entrypoint"] = "payments:compute_fee"
        ctx.extra["redactions"] = ["elapsed_ms"]
        ctx.extra["min_instances"] = 2
        report = H5DiffGate().run(ctx)
        assert report.verdict is Verdict.PASS

    def test_h5_inconclusive_at_n1_without_golden(self, ctx_factory):
        report = H5DiffGate().run(ctx_factory("inst-a"))
        assert report.verdict is Verdict.INCONCLUSIVE

    def test_h5_golden_mode_r3(self, ctx_factory, instances_dir, tmp_path):
        golden = tmp_path / "golden"
        golden.mkdir()
        (golden / "fee_basic.golden.json").write_text(
            json.dumps(
                {
                    "entrypoint": "payments:compute_fee",
                    "inputs": {"amount": 100.0, "rate": 0.05},
                    "expected": {"fee": 5.0, "currency": "CNY"},
                    "redact": ["elapsed_ms"],
                }
            ),
            encoding="utf-8",
        )
        spec_dir = tmp_path / "spec"
        (spec_dir / "L2").mkdir(parents=True)
        contract = yaml.safe_load(CONTRACT_YAML)
        contract["r_level"] = "R3"
        contract["frozen_outputs"] = ["golden/fee_basic.golden.json"]
        (spec_dir / "L2" / "CTR-payments-core.contract.yaml").write_text(
            yaml.safe_dump(contract, allow_unicode=True), encoding="utf-8"
        )
        (spec_dir / "registry.yaml").write_text("spec_version: 1.0.0\nmigration_stage: M2\n", encoding="utf-8")
        (spec_dir / "L1").mkdir()
        (spec_dir / "L1" / "payments.md").write_text(
            "# Payments Intent (L1)\n\n## PAY-INTENT-001\nexact cents\n\n## PAY-INTENT-002\nmonotone\n", encoding="utf-8"
        )
        manifest = load_repo(spec_dir)
        ctx = ctx_factory("inst-a", spec_dir=spec_dir, manifest=manifest, golden_dir=golden)
        report = H5DiffGate().run(ctx)
        assert report.verdict is Verdict.PASS

        (golden / "fee_wrong.golden.json").write_text(
            json.dumps(
                {
                    "entrypoint": "payments:compute_fee",
                    "inputs": {"amount": 100.0, "rate": 0.05},
                    "expected": {"fee": 5.01, "currency": "CNY"},
                    "redact": ["elapsed_ms"],
                }
            ),
            encoding="utf-8",
        )
        report = H5DiffGate().run(ctx)
        assert report.verdict is Verdict.FAIL

    def test_h6_blocks_evil_instance(self, ctx_factory):
        report = H6ConstitutionGate().run(ctx_factory("inst-evil"))
        assert report.verdict is Verdict.FAIL
        ids = {c.id for c in report.checks if c.status is Verdict.FAIL}
        assert "h6.secrets" in ids and "h6.dangerous_calls" in ids

    def test_h7_passes_clean_provenance(self, ctx_factory):
        report = H7DriftGate().run(ctx_factory("inst-a"))
        assert report.verdict is Verdict.PASS

    def test_h7_fails_after_contract_drift(self, ctx_factory, spec_dir, instances_dir):
        drifted = spec_dir / "L2" / "CTR-payments-core.contract.yaml"
        original = drifted.read_text(encoding="utf-8")
        try:
            data = yaml.safe_load(original)
            data["clauses"][0]["text"] = "fee rounded half-up (silently changed)"
            drifted.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
            manifest = load_repo(spec_dir)
            ctx = ctx_factory("inst-a", manifest=manifest)
            report = H7DriftGate().run(ctx)
            assert report.verdict is Verdict.FAIL
            provenance = next(c for c in report.checks if c.id == "h7.provenance")
            assert "drifted" in provenance.detail
        finally:
            drifted.write_text(original, encoding="utf-8")

    def test_h8_budget_bounds(self, ctx_factory, instances_dir):
        report = H8BudgetGate().run(ctx_factory("inst-a"))
        assert report.verdict is Verdict.PASS

        over = instances_dir / "inst-overbudget"
        over.mkdir(exist_ok=True)
        (over / "usage.json").write_text(
            json.dumps({"prompt_tokens": 999999, "completion_tokens": 10}), encoding="utf-8"
        )
        report = H8BudgetGate().run(ctx_factory("inst-overbudget"))
        assert report.verdict is Verdict.FAIL

        noevidence = instances_dir / "inst-noevidence"
        noevidence.mkdir(exist_ok=True)
        report = H8BudgetGate().run(ctx_factory("inst-noevidence"))
        assert report.verdict is Verdict.INCONCLUSIVE


class TestRunnerAdmission:
    def _waiver_file(self, tmp_path: Path, gate: str = "H5") -> Path:
        waivers = tmp_path / "waivers.yaml"
        entry = WaiverEntry(
            waiver_id="WVR-001",
            gate=gate,
            scope="CTR-payments-core",
            reason="N=1 calibration wave; closure re-check scheduled at next wave",
            approver="human-owner",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        waivers.write_text(
            yaml.safe_dump({"waivers": [entry.model_dump(mode="json")]}, allow_unicode=True),
            encoding="utf-8",
        )
        return waivers

    def test_full_admission_with_waiver(self, ctx_factory, tmp_path):
        ctx = ctx_factory("inst-a")
        soft = GateReport(gate="S", verdict=Verdict.PASS, instance_id="inst-a", wave_id="WAVE-T1")
        runner = GateRunner()
        verdict, hard = runner.run_reports(ctx, soft, waivers_file=self._waiver_file(tmp_path))
        assert verdict.admitted, verdict.blocking_gates
        assert hard["H5"].artifacts.get("waiver_id") == "WVR-001"

    def test_admission_blocked_without_waiver(self, ctx_factory):
        ctx = ctx_factory("inst-a")
        soft = GateReport(gate="S", verdict=Verdict.PASS, instance_id="inst-a", wave_id="WAVE-T1")
        runner = GateRunner()
        verdict, hard = runner.run_reports(ctx, soft)
        assert not verdict.admitted
        assert "H5" in verdict.blocking_gates

    def test_evil_instance_never_admitted(self, ctx_factory, tmp_path):
        ctx = ctx_factory("inst-evil")
        soft = GateReport(gate="S", verdict=Verdict.PASS, instance_id="inst-evil", wave_id="WAVE-T1")
        runner = GateRunner()
        verdict, _ = runner.run_reports(ctx, soft, waivers_file=self._waiver_file(tmp_path))
        assert not verdict.admitted
        assert {"H2", "H3", "H6"} & set(verdict.blocking_gates)

    def test_soft_gate_can_veto_only(self, ctx_factory, tmp_path):
        ctx = ctx_factory("inst-a")
        veto = GateReport(gate="S", verdict=Verdict.FAIL, instance_id="inst-a", wave_id="WAVE-T1")
        runner = GateRunner()
        verdict, _ = runner.run_reports(ctx, veto, waivers_file=self._waiver_file(tmp_path))
        assert not verdict.admitted
        assert "S" in verdict.blocking_gates

    def test_expired_waiver_is_inert(self, ctx_factory, tmp_path):
        waivers = tmp_path / "waivers.yaml"
        entry = WaiverEntry(
            waiver_id="WVR-002",
            gate="H5",
            scope="*",
            reason="expired",
            approver="human-owner",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        waivers.write_text(
            yaml.safe_dump({"waivers": [entry.model_dump(mode="json")]}, allow_unicode=True),
            encoding="utf-8",
        )
        ctx = ctx_factory("inst-a")
        soft = GateReport(gate="S", verdict=Verdict.PASS, instance_id="inst-a", wave_id="WAVE-T1")
        verdict, _ = GateRunner().run_reports(ctx, soft, waivers_file=waivers)
        assert not verdict.admitted


class TestSpecLintSemantics:
    def test_lint_flags_unwitnessed_clause(self, tmp_path, spec_dir):
        bad_spec = tmp_path / "spec"
        shutil.copytree(spec_dir, bad_spec)
        contract_path = bad_spec / "L2" / "CTR-payments-core.contract.yaml"
        data = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        data["clauses"].append({"id": "REQ-payments-004", "layer": "L2", "text": "no witness", "witnesses": []})
        contract_path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
        results = lint_spec_repo(bad_spec)
        clause_rules = next(r for r in results if r.id == "spec.clause_rules")
        assert clause_rules.status is Verdict.FAIL
        assert "REQ-payments-004" in clause_rules.detail

    def test_lint_flags_r3_without_frozen_outputs(self, tmp_path, spec_dir):
        bad_spec = tmp_path / "spec"
        shutil.copytree(spec_dir, bad_spec)
        contract_path = bad_spec / "L2" / "CTR-payments-core.contract.yaml"
        data = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        data["r_level"] = "R3"
        data["frozen_outputs"] = []
        contract_path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
        results = lint_spec_repo(bad_spec)
        clause_rules = next(r for r in results if r.id == "spec.clause_rules")
        assert clause_rules.status is Verdict.FAIL
        assert "frozen_outputs" in clause_rules.detail
