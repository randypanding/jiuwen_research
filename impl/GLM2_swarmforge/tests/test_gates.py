"""门禁代数与 H 门测试：代数真值表、逐门拦截性、证据来源链、fail-fast。"""
import pytest

from swarmforge.gates import (
    AdmissionDecisionKind,
    EvidenceItem,
    EvidenceRejected,
    GateContext,
    GateResult,
    GateRunner,
    Verdict,
    adjudicate,
    gates_for_r_level,
)
from swarmforge.specrepo import RLevel


def r(verdict, blocking=True):
    return GateResult(gate_id=f"H{verdict}", verdict=verdict, blocking=blocking)


class TestAdmissionAlgebra:
    """INV4 真值表：H FAIL → REJECT（S 无法救场）；H 过 + S veto → REJECT。"""

    def test_all_pass_admits(self):
        assert adjudicate([r(Verdict.PASS)]) == AdmissionDecisionKind.ADMIT

    def test_hard_fail_rejects_even_with_soft_ok(self):
        assert adjudicate([r(Verdict.PASS), r(Verdict.FAIL)],
                          soft_vetoes=0, soft_abstains=0) == AdmissionDecisionKind.REJECT

    def test_hard_pass_soft_veto_rejects(self):
        assert adjudicate([r(Verdict.PASS)], soft_vetoes=1) == AdmissionDecisionKind.REJECT

    def test_soft_abstain_escalates_never_admits(self):
        assert adjudicate([r(Verdict.PASS)], soft_abstains=1) == AdmissionDecisionKind.ESCALATE

    def test_hard_inconclusive_escalates(self):
        assert adjudicate([r(Verdict.INCONCLUSIVE)]) == AdmissionDecisionKind.ESCALATE

    def test_non_blocking_fail_does_not_reject(self):
        assert adjudicate([r(Verdict.FAIL, blocking=False)]) == AdmissionDecisionKind.ADMIT


def ctx(evidence: dict, config=None) -> GateContext:
    return GateContext(
        wave_id="W1", instance_id="I1",
        evidence={k: EvidenceItem(kind=k, producer_role=v, payload=p)
                  for k, (v, p) in evidence.items()},
        config=config or {},
    )


GREEN = {
    "build_report": ("ci", {"compile_ok": True, "type_errors": [], "lint_errors": []}),
    "test_report": ("ci", {"total": 10, "passed": 10, "failed": 0, "errors": 0}),
    "scenario_results": ("verifier", {
        "results": [{"scenario_id": "SC-1", "instance_id": "I1", "outcome": "pass"}],
        "fail_to_pass": ["SC-1"], "pass_to_pass": []}),
    "contract_diff": ("verifier", {"breaking": [], "removed_symbols": []}),
    "guard_report": ("sandbox", {"path_violations": [], "declared_deps": ["requests"]}),
    "drift_report": ("verifier", {"orphans": [], "missing_anchors": [],
                                  "bypasses": [], "stale_clauses": []}),
    "budget_report": ("ci", {"tokens_used": 1000, "token_cap": 100000,
                             "wallclock_used_s": 10.0, "wallclock_cap_s": 3600}),
}


class TestGateInterception:
    """每个门的拦截性：构造坏证据，门必须 FAIL。"""

    def test_h1_build_failure_blocks(self):
        out = GateRunner().run(ctx({"build_report": ("ci", {"compile_ok": False})}),
                               RLevel.R0, gate_ids=["H1"])
        assert not out.admitted and "H1:fail" in out.blocking_failures

    def test_h2_test_failure_blocks(self):
        out = GateRunner().run(ctx({"test_report": ("ci", {"total": 5, "passed": 3,
                                                           "failed": 2, "errors": 0})}),
                               RLevel.R0, gate_ids=["H2"])
        assert not out.admitted

    def test_h2_property_failure_blocks(self):
        out = GateRunner().run(ctx({"test_report": ("ci", {"total": 5, "passed": 5,
                                                           "failed": 0, "errors": 0,
                                                           "property_failures": ["prop-refund-nonneg"]})}),
                               RLevel.R0, gate_ids=["H2"])
        assert not out.admitted

    def test_h3_fail_to_pass_unmet_blocks(self):
        out = GateRunner().run(ctx({"scenario_results": ("verifier", {
            "results": [{"scenario_id": "SC-1", "instance_id": "I1", "outcome": "fail"}],
            "fail_to_pass": ["SC-1"], "pass_to_pass": []})}),
            RLevel.R0, gate_ids=["H3"])
        assert not out.admitted

    def test_h3_regression_blocks(self):
        out = GateRunner().run(ctx({"scenario_results": ("verifier", {
            "results": [{"scenario_id": "SC-1", "instance_id": "I1", "outcome": "pass"},
                        {"scenario_id": "SC-old", "instance_id": "I1", "outcome": "fail"}],
            "fail_to_pass": ["SC-1"], "pass_to_pass": ["SC-old"]})}),
            RLevel.R0, gate_ids=["H3"])
        assert not out.admitted

    def test_h4_breaking_without_bump_blocks(self):
        out = GateRunner().run(ctx({"contract_diff": ("verifier", {
            "breaking": ["removed POST /refunds"], "major_bump_declared": False})}),
            RLevel.R2, gate_ids=["H4"])
        assert not out.admitted

    def test_h4_breaking_with_declared_major_bump_passes(self):
        out = GateRunner().run(ctx({"contract_diff": ("verifier", {
            "breaking": ["removed POST /refunds"], "major_bump_declared": True})}),
            RLevel.R2, gate_ids=["H4"])
        assert out.hard_results[0].verdict == Verdict.PASS

    def test_h5_spec_silence_blocks(self):
        out = GateRunner().run(ctx({"diff_report": ("verifier", {
            "conclusion": "difference_found", "divergent_inputs": ["in-1"]})}),
            RLevel.R0, gate_ids=["H5"])
        assert not out.admitted

    def test_h5_nondet_inconclusive_blocks(self):
        out = GateRunner().run(ctx({"diff_report": ("verifier", {
            "conclusion": "inconclusive"})}),
            RLevel.R0, gate_ids=["H5"])
        assert not out.admitted
        assert out.decision == AdmissionDecisionKind.REJECT

    def test_h5_golden_mismatch_blocks(self):
        out = GateRunner().run(ctx({"golden_result": ("verifier", {
            "verdict": "fail", "detail": "byte mismatch"})}),
            RLevel.R3, gate_ids=["H5"])
        assert not out.admitted

    def test_h5_golden_manifest_invalid_escalates_not_rejects(self):
        """manifest 不一致 = 比对无效 = INCONCLUSIVE（升级），不是 FAIL。"""
        out = GateRunner().run(ctx({"golden_result": ("verifier", {
            "verdict": "inconclusive", "detail": "seed mismatch"})}),
            RLevel.R3, gate_ids=["H5"])
        assert out.decision == AdmissionDecisionKind.ESCALATE

    def test_h5_single_instance_r0_skips(self):
        out = GateRunner().run(ctx({}), RLevel.R0, gate_ids=["H5"])
        assert out.hard_results[0].verdict == Verdict.SKIP
        assert out.admitted  # SKIP 不阻断

    def test_h6_path_violation_blocks(self):
        out = GateRunner().run(ctx({"guard_report": ("sandbox", {
            "path_violations": ["/etc/passwd"], "declared_deps": []})}),
            RLevel.R0, gate_ids=["H6"])
        assert not out.admitted

    def test_h6_forbidden_dep_pattern_scan(self):
        out = GateRunner().run(ctx({"guard_report": ("sandbox", {
            "declared_deps": ["telnetlib", "requests"]})}),
            RLevel.R0, gate_ids=["H6"])
        assert not out.admitted

    def test_h7_drift_blocks(self):
        out = GateRunner().run(ctx({"drift_report": ("verifier", {
            "orphans": ["CON-404@a.py"], "missing_anchors": [], "bypasses": [],
            "stale_clauses": []})}),
            RLevel.R1, gate_ids=["H7"])
        assert not out.admitted

    def test_h8_budget_blocks(self):
        out = GateRunner().run(ctx({"budget_report": ("ci", {
            "tokens_used": 999999, "token_cap": 1000})}),
            RLevel.R0, gate_ids=["H8"])
        assert not out.admitted


class TestEvidenceProvenance:
    """证据来源链：builder 自报的验证性证据必须被拒绝并升级（防伪造）。"""

    def test_builder_forged_build_report_rejected(self):
        forged = ctx({"build_report": ("builder", {"compile_ok": True})})
        out = GateRunner().run(forged, RLevel.R0, gate_ids=["H1"])
        assert out.decision == AdmissionDecisionKind.ESCALATE  # 不是静默放行

    def test_builder_forged_test_report_rejected(self):
        forged = ctx({"test_report": ("builder", {"total": 9, "passed": 9,
                                                  "failed": 0, "errors": 0})})
        out = GateRunner().run(forged, RLevel.R0, gate_ids=["H2"])
        assert out.decision == AdmissionDecisionKind.ESCALATE

    def test_missing_evidence_escalates(self):
        out = GateRunner().run(ctx({}), RLevel.R0, gate_ids=["H1"])
        assert out.decision == AdmissionDecisionKind.ESCALATE


class TestGateRunner:
    def test_fail_fast_stops_at_first_blocking(self):
        """H1 FAIL 后不再跑昂贵的 H3/H5（省成本）。"""
        evidence = dict(GREEN)
        evidence["build_report"] = ("ci", {"compile_ok": False})
        evidence["scenario_results"] = ("verifier", {
            "results": [], "fail_to_pass": ["SC-1"], "pass_to_pass": []})
        out = GateRunner().run(ctx(evidence), RLevel.R0, collect_all=False,
                               gate_ids=["H1", "H2", "H3", "H5", "H6", "H8"])
        assert [res.gate_id for res in out.hard_results] == ["H1"]

    def test_collect_all_mode_gathers_everything(self):
        evidence = dict(GREEN)
        evidence["build_report"] = ("ci", {"compile_ok": False})
        out = GateRunner().run(ctx(evidence), RLevel.R0, collect_all=True,
                               gate_ids=["H1", "H2", "H6", "H8"])
        assert len(out.hard_results) == 4  # 全部收集（证据收据用）

    def test_full_green_r0_admits(self):
        out = GateRunner().run(ctx(GREEN), RLevel.R0)
        assert out.admitted, out.to_dict()

    def test_r_level_gate_selection(self):
        r3_ids = {g.gate_id for g in gates_for_r_level(RLevel.R3)}
        assert "H5" in r3_ids and "H3" not in r3_ids  # R3 要 H5 不要 H3
        r0_ids = {g.gate_id for g in gates_for_r_level(RLevel.R0)}
        assert "H5" not in r0_ids and "H3" in r0_ids

    def test_soft_judge_veto_blocks_after_hard_green(self):
        evidence = dict(GREEN)
        evidence["judge_outputs"] = ("verifier", [
            {"verdict": "veto", "reasons": ["违反契约"], "evidence_citations": ["CON-1"]},
            {"verdict": "veto", "reasons": ["x"], "evidence_citations": []},
            {"verdict": "no_veto", "reasons": [], "evidence_citations": []},
        ])
        out = GateRunner().run(ctx(evidence), RLevel.R0,
                               gate_ids=["H1", "H2", "H3", "H6"])
        assert out.decision == AdmissionDecisionKind.REJECT  # 2/3 veto 多数

    def test_soft_judge_abstain_escalates(self):
        evidence = dict(GREEN)
        evidence["judge_outputs"] = ("verifier", [
            {"verdict": "no_veto", "reasons": [], "evidence_citations": []},
            {"verdict": "abstain", "reasons": ["证据不足"], "evidence_citations": []},
            {"verdict": "no_veto", "reasons": [], "evidence_citations": []},
        ])
        out = GateRunner().run(ctx(evidence), RLevel.R0,
                               gate_ids=["H1", "H2", "H3", "H6"])
        assert out.decision == AdmissionDecisionKind.ESCALATE
