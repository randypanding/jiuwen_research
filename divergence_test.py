"""Objective divergence tests across all 7 plan implementations.

Verifies three hypotheses empirically:

H1 - R3 fan-out enforcement:
    PR3/GLM1/GLM2/K3/QW1 forbid fan-out for R3 (N must be 1);
    QW2 (and possibly QW3) allow R3 fan-out > 1.

H2 - Soft gate abstention semantics:
    PR3/QW1 treat ABSTAIN as non-blocking (no veto -> admit if hard passes);
    GLM2 treats ABSTAIN as ESCALATE; QW2/QW3/GLM1 treat abstain as blocking
    (fail-closed / inconclusive).

H3 - No-rescue property (consensus expectation):
    If hard gates fail, no soft verdict (including PASS/NO_VETO) may admit.
"""
import sys

def section(title):
    print("\n" + "=" * 70)
    print("## " + title)
    print("=" * 70)

def test_qw2_r3_fanout():
    section("QW2 (swarmfoundry) - R3 fan-out enforcement in wave schema")
    sys.path.insert(0, "/tmp/checkouts/QW2/swarmfoundry/src")
    try:
        from swarmfoundry.schema.wave import WaveTask
        try:
            task = WaveTask.from_dict({
                "task_id": "T-1", "spec_delta_id": "D-1", "r_level": "R3",
                "n_fanout": 3,
            }, "test")
            print(f"  R3 n_fanout=3 -> ACCEPTED (task created, n_fanout={task.n_fanout})")
        except Exception as e:
            print(f"  R3 n_fanout=3 -> REJECTED: {type(e).__name__}: {e}")
        try:
            task = WaveTask.from_dict({
                "task_id": "T-2", "spec_delta_id": "D-1", "r_level": "R0",
                "n_fanout": 3,
            }, "test")
            print(f"  R0 n_fanout=3 -> ACCEPTED (n_fanout={task.n_fanout})")
        except Exception as e:
            print(f"  R0 n_fanout=3 -> REJECTED: {type(e).__name__}: {e}")
    except Exception as e:
        print(f"  IMPORT FAILED: {e}")
    sys.path.pop(0)

def test_k3_r3_fanout():
    section("K3 (swarmdev) - R3 fan-out enforcement")
    sys.path.insert(0, "/tmp/checkouts/K3/swarmdev")
    try:
        from swarmdev.contracts.r_level import RLevel, RRegistry
        print(f"  fanout_allowed(R0)={RRegistry.fanout_allowed(RLevel.R0)}")
        print(f"  fanout_allowed(R1)={RRegistry.fanout_allowed(RLevel.R1)}")
        print(f"  fanout_allowed(R2)={RRegistry.fanout_allowed(RLevel.R2)}")
        print(f"  fanout_allowed(R3)={RRegistry.fanout_allowed(RLevel.R3)}")
        print(f"  discard_allowed(R3)={RRegistry.discard_allowed(RLevel.R3)}")
    except Exception as e:
        print(f"  IMPORT FAILED: {e}")
    sys.path.pop(0)

def test_glm1_r3_fanout():
    section("GLM1 (specforge) - R3 fan-out enforcement")
    sys.path.insert(0, "/tmp/checkouts/GLM1/specforge")
    try:
        from specforge.spec.rlevels import RRegistry
        from specforge.swarm.fanout import fanout_plan
        reg = RRegistry()
        print(f"  fanout_allowed(R0)={reg.fanout_allowed('R0')}")
        print(f"  fanout_allowed(R1)={reg.fanout_allowed('R1')}")
        print(f"  fanout_allowed(R2)={reg.fanout_allowed('R2')}")
        print(f"  fanout_allowed(R3)={reg.fanout_allowed('R3')}")
        for u in (0.1, 0.5, 0.9):
            print(f"  fanout_plan(u={u}, R3)={fanout_plan(u, 'R3')} ; R0={fanout_plan(u, 'R0')}")
    except Exception as e:
        print(f"  IMPORT FAILED: {e}")
    sys.path.pop(0)

def test_glm2_r3_fanout():
    section("GLM2 (swarmforge) - R3 fan-out enforcement")
    sys.path.insert(0, "/tmp/checkouts/GLM2/swarmforge")
    try:
        from swarmforge.measurement.fanout import compute_fanout
        for r in ("R0", "R1", "R2", "R3"):
            d = compute_fanout(0.9, 0.9, r)
            print(f"  compute_fanout(rework=0.9, novelty=0.9, {r}) -> n={d.n}, early_stop={d.early_stop_enabled}")
    except Exception as e:
        print(f"  IMPORT FAILED: {e}")
    sys.path.pop(0)

def test_qw1_r3_fanout():
    section("QW1 (swarm-kernel) - R3 fan-out enforcement")
    sys.path.insert(0, "/tmp/checkouts/QW1/swarm-kernel")
    try:
        from swarm_kernel.contracts.fanout import FanoutRequest
        from swarm_kernel.contracts.base import RLevel
        try:
            fr = FanoutRequest(wave_id="W-1", delta_id="D-1", r_level=RLevel.R3, n_instances=2)
            print(f"  R3 n_instances=2 -> ACCEPTED ({fr.n_instances})")
        except Exception as e:
            print(f"  R3 n_instances=2 -> REJECTED: {type(e).__name__}: {e}")
        try:
            fr = FanoutRequest(wave_id="W-1", delta_id="D-1", r_level=RLevel.R3, n_instances=1)
            print(f"  R3 n_instances=1 -> ACCEPTED ({fr.n_instances})")
        except Exception as e:
            print(f"  R3 n_instances=1 -> REJECTED: {type(e).__name__}: {e}")
    except Exception as e:
        print(f"  IMPORT FAILED: {e}")
    sys.path.pop(0)

def test_qw3_r3_fanout():
    section("QW3 (opc) - R3 fan-out enforcement in WaveManifest")
    sys.path.insert(0, "/tmp/checkouts/QW3/opc/src")
    try:
        from opc.schemas.wave import WaveManifest
        from opc.schemas.common import RLevel
        try:
            m = WaveManifest(wave_id="WAVE-1", spec_version="1", fanout_n=3, r_levels={"A": RLevel.R3})
            print(f"  WaveManifest R3 with fanout_n=3 -> ACCEPTED (fanout_n={m.fanout_n})")
        except Exception as e:
            print(f"  WaveManifest R3 with fanout_n=3 -> REJECTED: {type(e).__name__}: {e}")
        try:
            m = WaveManifest(wave_id="WAVE-2", spec_version="1", fanout_n=3, r_levels={"A": RLevel.R0})
            print(f"  WaveManifest R0 with fanout_n=3 -> ACCEPTED (fanout_n={m.fanout_n})")
        except Exception as e:
            print(f"  WaveManifest R0 with fanout_n=3 -> REJECTED: {type(e).__name__}: {e}")
    except Exception as e:
        print(f"  IMPORT FAILED: {e}")
    sys.path.pop(0)

def test_pr3_r3_fanout():
    section("PR3 (copilot kernel) - R3 fan-out enforcement")
    sys.path.insert(0, "/tmp/checkouts/copilot/create-engineering-plan/kernel/src")
    try:
        from swarmkernel.contracts.spec import RLevel
        print(f"  RLevel values: {[r.value for r in RLevel]}")
        for r in RLevel:
            print(f"  RLevel.allows_fanout({r.value})={r.allows_fanout}")
        from swarmkernel.contracts.wave import UncertaintySignal, FanoutPlan
        for r in RLevel:
            sig = UncertaintySignal(r_level=r, novel_domain=True, new_clause_count=5, historical_rework_rate=0.9, blast_radius=3)
            plan = FanoutPlan.decide("u", sig)
            print(f"  FanoutPlan.decide({r.value}, high-uncertainty) -> n={plan.n}, reason={plan.reason}")
        # Violation attempt: R3 with n>1 should raise
        sig_r3 = UncertaintySignal(r_level=RLevel.R3)
        try:
            plan = FanoutPlan(unit_id="u", n=3, signal=sig_r3)
            print(f"  R3 n=3 direct -> ACCEPTED (BUG)")
        except Exception as e:
            print(f"  R3 n=3 direct -> REJECTED: {type(e).__name__}: {e}")
    except Exception as e:
        print(f"  IMPORT FAILED: {e}")
    sys.path.pop(0)

def test_soft_abstention():
    section("Soft gate abstention semantics")

    print("-- PR3 (copilot kernel): admit(H_pass, soft) --")
    sys.path.insert(0, "/tmp/checkouts/copilot/create-engineering-plan/kernel/src")
    try:
        from swarmkernel.contracts.gate import SoftVerdict, SoftGateResult
        from swarmkernel.contracts.gate import HardGateReport, GateResult, GateStatus, GateId, Finding
        from swarmkernel.gates.algebra import admit

        def mk_hard(passed=True):
            if passed:
                results = [GateResult(gate=g, status=GateStatus.PASS) for g in GateId if g.is_hard]
            else:
                results = [GateResult(gate=g, status=GateStatus.FAIL, findings=[Finding(code="X", message="boom")]) for g in GateId if g.is_hard]
            return HardGateReport(instance_id="i", unit_id="u", results=results)

        soft_none = None
        soft_noveto = SoftGateResult(verdict=SoftVerdict.NO_VETO)
        soft_abstain = SoftGateResult(verdict=SoftVerdict.ABSTAIN)
        for lbl, s in [("soft=None", soft_none), ("NO_VETO", soft_noveto), ("ABSTAIN", soft_abstain)]:
            print(f"  admit(H_pass, {lbl}) = {admit(mk_hard(True), s)}")
        for lbl, s in [("soft=None", soft_none), ("NO_VETO", soft_noveto), ("ABSTAIN", soft_abstain)]:
            print(f"  admit(H_FAIL, {lbl}) = {admit(mk_hard(False), s)}")
    except Exception as e:
        print(f"  IMPORT FAILED: {e}")
    sys.path.pop(0)

    print("-- QW1 (swarm-kernel): judge verdict -> admission --")
    sys.path.insert(0, "/tmp/checkouts/QW1/swarm-kernel")
    try:
        from swarm_kernel.contracts.oracle import JudgeVerdict, JudgeVerdictKind
        from swarm_kernel.contracts.gates import HARD_GATES, GateId, GateResult, GateSuiteResult
        from swarm_kernel.contracts.base import Verdict, RLevel
        from swarm_kernel.contracts.admission import EvidenceReceipt, DriftCheckSummary
        from swarm_kernel.admission.transaction import AdmissionTransaction

        tx = AdmissionTransaction("/tmp/divergence_tests/qw1_tmp")
        results = [GateResult(gate_id=g, verdict=Verdict.PASS) for g in HARD_GATES]
        suite = GateSuiteResult(instance_id="i", results=results)
        rec = EvidenceReceipt(
            wave_id="W", delta_id="D", r_level=RLevel.R3, chosen_instance_id="i",
            gate_suite=suite, judge_verdict=JudgeVerdict(rubric_id="R", instance_id="i", kind=JudgeVerdictKind.ABSTAIN),
            drift_check=DriftCheckSummary(),
        )
        probs = tx.verify_receipt(rec)
        print(f"  ABSTAIN judge -> verify_receipt problems = {probs}")
        rec2 = EvidenceReceipt(
            wave_id="W", delta_id="D", r_level=RLevel.R3, chosen_instance_id="i",
            gate_suite=suite, judge_verdict=JudgeVerdict(rubric_id="R", instance_id="i", kind=JudgeVerdictKind.VETO),
            drift_check=DriftCheckSummary(),
        )
        probs2 = tx.verify_receipt(rec2)
        print(f"  VETO judge   -> verify_receipt problems = {probs2}")
    except Exception as e:
        print(f"  IMPORT FAILED: {e}")
    sys.path.pop(0)

    print("-- GLM2 (swarmforge): adjudicate() --")
    sys.path.insert(0, "/tmp/checkouts/GLM2/swarmforge")
    try:
        from swarmforge.gates.algebra import adjudicate, GateResult, Verdict
        ok = [GateResult(gate_id="H1", verdict=Verdict.PASS, blocking=True)]
        print(f"  H pass, S abstain=1 -> {adjudicate(ok, soft_vetoes=0, soft_abstains=1).value}")
        print(f"  H pass, S veto=1    -> {adjudicate(ok, soft_vetoes=1, soft_abstains=0).value}")
        print(f"  H pass, S no veto   -> {adjudicate(ok, soft_vetoes=0, soft_abstains=0).value}")
        fail = [GateResult(gate_id="H1", verdict=Verdict.FAIL, blocking=True)]
        print(f"  H FAIL, S no veto    -> {adjudicate(fail, soft_vetoes=0, soft_abstains=0).value}")
        inc = [GateResult(gate_id="H1", verdict=Verdict.INCONCLUSIVE, blocking=True)]
        print(f"  H INCONCLUSIVE, S ok -> {adjudicate(inc, soft_vetoes=0, soft_abstains=0).value}")
    except Exception as e:
        print(f"  IMPORT FAILED: {e}")
    sys.path.pop(0)

    print("-- QW2 (swarmfoundry): aggregate_panel --")
    sys.path.insert(0, "/tmp/checkouts/QW2/swarmfoundry/src")
    try:
        from swarmfoundry.schema.judge import JudgeVerdict, aggregate_panel, VERDICT_ABSTAIN, VERDICT_NO_VETO, VERDICT_VETO
        p = aggregate_panel([
            JudgeVerdict(judge_id="j1", model_family="fam-a", verdict=VERDICT_ABSTAIN, reasons="r"),
            JudgeVerdict(judge_id="j2", model_family="fam-b", verdict=VERDICT_ABSTAIN, reasons="r"),
        ], builder_model_family="fam-x", min_valid=2)
        print(f"  all-abstain panel -> vetoed={p.vetoed}, counted={p.counted}, abstained={p.abstained}")
        p2 = aggregate_panel([
            JudgeVerdict(judge_id="j1", model_family="fam-a", verdict=VERDICT_NO_VETO, reasons="r"),
            JudgeVerdict(judge_id="j2", model_family="fam-b", verdict=VERDICT_ABSTAIN, reasons="r"),
        ], builder_model_family="fam-x", min_valid=2)
        print(f"  1 no_veto + 1 abstain -> vetoed={p2.vetoed}, counted={p2.counted}")
    except Exception as e:
        print(f"  IMPORT FAILED: {e}")
    sys.path.pop(0)

    print("-- QW3 (opc): AdmissionVerdict.decide --")
    sys.path.insert(0, "/tmp/checkouts/QW3/opc/src")
    try:
        from opc.schemas.gates import GateReport, AdmissionVerdict
        from opc.schemas.common import Verdict
        hard_all_pass = {g: GateReport(gate=g, verdict=Verdict.PASS) for g in ("H1","H2","H3","H4","H5","H6","H7","H8")}
        soft_inconclusive = GateReport(gate="S", verdict=Verdict.INCONCLUSIVE)
        v = AdmissionVerdict.decide(hard_all_pass, soft_inconclusive)
        print(f"  hard pass + S=INCONCLUSIVE -> admitted={v.admitted}, blocking={v.blocking_gates}")
        v2 = AdmissionVerdict.decide(hard_all_pass, None)
        print(f"  hard pass + S=None    -> admitted={v2.admitted}, blocking={v2.blocking_gates}")
    except Exception as e:
        print(f"  IMPORT FAILED: {e}")
    sys.path.pop(0)

    print("-- GLM1 (specforge): run_judge / decide_admission --")
    sys.path.insert(0, "/tmp/checkouts/GLM1/specforge")
    try:
        from specforge.judge.workflow import run_judge
        from specforge.judge.model import JudgeModel, ABSTAIN, PASS
        from specforge.judge.rubric import Rubric

        class AllAbstain(JudgeModel):
            model_id = "abstainer"
            def score(self, rubric, item):
                return type("V", (), {"verdict": ABSTAIN})()

        class AllPass(JudgeModel):
            model_id = "passer"
            def score(self, rubric, item):
                return type("V", (), {"verdict": PASS})()

        rubric = Rubric(rubric_id="R1", dimension="correctness", task="judge", levels=[])
        r = run_judge(AllAbstain(), rubric, {"content": "x"}, k=3)
        print(f"  all-abstain -> verdict={r.verdict}, reason={r.reason}")
        r2 = run_judge(AllPass(), rubric, {"content": "x"}, k=3)
        print(f"  all-pass    -> verdict={r2.verdict}, reason={r2.reason}")

        from specforge.gates.base import decide_admission, GateResult, GateVerdict
        hard_pass = [GateResult("H1", GateVerdict.PASS)]
        soft_inc = [GateResult("S", GateVerdict.INCONCLUSIVE, hard=False)]
        d = decide_admission(hard_pass, soft_inc)
        print(f"  H pass + S=INCONCLUSIVE -> decision={d.decision}")
        hard_fail = [GateResult("H1", GateVerdict.FAIL)]
        soft_pass = [GateResult("S", GateVerdict.PASS, hard=False)]
        d2 = decide_admission(hard_fail, soft_pass)
        print(f"  H FAIL + S=PASS -> decision={d2.decision}")
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"  IMPORT FAILED: {e}")
    sys.path.pop(0)


if __name__ == "__main__":
    test_qw2_r3_fanout()
    test_k3_r3_fanout()
    test_glm1_r3_fanout()
    test_glm2_r3_fanout()
    test_qw1_r3_fanout()
    test_qw3_r3_fanout()
    test_pr3_r3_fanout()
    test_soft_abstention()
    print("\nALL TESTS DONE")
