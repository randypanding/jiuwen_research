from __future__ import annotations

import pytest

from swarm_kernel.contracts.base import Verdict
from swarm_kernel.contracts.gates import GateId
from swarm_kernel.contracts.spec import SpecDoc
from swarm_kernel.gates.base import GateConfig, GateContext
from swarm_kernel.gates.hard_gates import (
    h1_build,
    h2_unit,
    h3_holdout,
    h4_contract_surface,
    h5_differential,
    h6_invariants,
    h7_drift,
    h8_budget,
)
from swarm_kernel.gates.runner import run_suite, suite_exit_code
from swarm_kernel.spec_repo.registry import ClauseRegistry


@pytest.fixture()
def registry(spec_path) -> ClauseRegistry:
    return ClauseRegistry(SpecDoc.model_validate_json(spec_path.read_text(encoding="utf-8")))


def make_ctx(instance, oracle_dir, registry, tmp_path, peers=None) -> GateContext:
    return GateContext(
        instance_dir=instance,
        oracle_dir=oracle_dir,
        registry=registry,
        out_dir=tmp_path / "out",
        config=GateConfig(),
        peer_instances=peers or [],
    )


def test_h1_build_passes_on_valid_python(instance, oracle_dir, registry, tmp_path) -> None:
    ctx = make_ctx(instance("good"), oracle_dir, registry, tmp_path)
    assert h1_build(ctx).verdict == Verdict.PASS


def test_h2_unit_passes(instance, oracle_dir, registry, tmp_path) -> None:
    ctx = make_ctx(instance("good"), oracle_dir, registry, tmp_path)
    result = h2_unit(ctx)
    assert result.verdict == Verdict.PASS, result.details


def test_h3_holdout_pass_good_fail_bad(instance, oracle_dir, registry, tmp_path) -> None:
    ok = h3_holdout(make_ctx(instance("good"), oracle_dir, registry, tmp_path))
    bad = h3_holdout(make_ctx(instance("bad"), oracle_dir, registry, tmp_path))
    assert ok.verdict == Verdict.PASS
    assert bad.verdict == Verdict.FAIL
    assert "S-CLAMP-003" in bad.details["failed"]


def test_h4_contract_surface_detects_removed_export(instance, oracle_dir, registry, tmp_path) -> None:
    ok = h4_contract_surface(make_ctx(instance("good"), oracle_dir, registry, tmp_path))
    bad = h4_contract_surface(make_ctx(instance("surface_bad"), oracle_dir, registry, tmp_path))
    assert ok.verdict == Verdict.PASS
    assert bad.verdict == Verdict.FAIL
    assert "clamp" in bad.details["removed_exports"]


def test_h5_differential_silence_detection(instance, oracle_dir, registry, tmp_path) -> None:
    ctx = make_ctx(instance("divergent_a"), oracle_dir, registry, tmp_path, peers=[instance("divergent_a"), instance("divergent_b")])
    result = h5_differential(ctx)
    assert result.verdict == Verdict.FAIL
    assert result.details["divergent"] is True


def test_h5_differential_closed_pair(instance, oracle_dir, registry, tmp_path) -> None:
    ctx = make_ctx(instance("good"), oracle_dir, registry, tmp_path, peers=[instance("good"), instance("good2")])
    result = h5_differential(ctx)
    assert result.verdict == Verdict.PASS


def test_h6_detects_secret(instance, oracle_dir, registry, tmp_path) -> None:
    bad = h6_invariants(make_ctx(instance("secret_bad"), oracle_dir, registry, tmp_path))
    ok = h6_invariants(make_ctx(instance("good"), oracle_dir, registry, tmp_path))
    assert bad.verdict == Verdict.FAIL
    assert any("secret" in p for p in bad.details["problems"])
    assert ok.verdict == Verdict.PASS


def test_h7_drift_detects_stale_anchor(instance, oracle_dir, registry, tmp_path) -> None:
    bad = h7_drift(make_ctx(instance("drift_bad"), oracle_dir, registry, tmp_path))
    ok = h7_drift(make_ctx(instance("good"), oracle_dir, registry, tmp_path))
    assert bad.verdict == Verdict.FAIL
    assert bad.details["stale"] >= 1
    assert ok.verdict == Verdict.PASS


def test_h8_budget_overrun(instance, oracle_dir, registry, tmp_path) -> None:
    bad = h8_budget(make_ctx(instance("budget_bad"), oracle_dir, registry, tmp_path))
    ok = h8_budget(make_ctx(instance("good"), oracle_dir, registry, tmp_path))
    assert bad.verdict == Verdict.FAIL
    assert "tokens" in bad.details["over_budget"]
    assert ok.verdict == Verdict.PASS


def test_full_suite_good_passes(instance, oracle_dir, registry, tmp_path) -> None:
    ctx = make_ctx(instance("good"), oracle_dir, registry, tmp_path, peers=[instance("good"), instance("good2")])
    suite = run_suite(ctx)
    assert suite.hard_pass, [(r.gate_id.value, r.verdict, r.details) for r in suite.results if r.verdict != Verdict.PASS]
    assert suite_exit_code(suite) == 0


def test_full_suite_bad_fails_with_exit_1(instance, oracle_dir, registry, tmp_path) -> None:
    ctx = make_ctx(instance("bad"), oracle_dir, registry, tmp_path, peers=[instance("bad")])
    suite = run_suite(ctx)
    assert not suite.hard_pass
    assert GateId.H3_HOLDOUT in suite.blocking_gates()
    assert suite_exit_code(suite) == 1
