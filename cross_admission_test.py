#!/usr/bin/env python
"""Cross-implementation admission-algebra differential test.

Runs the SAME abstract scenario matrix through all 7 branch implementations
and reports a normalized decision per (scenario, impl), so divergences in
gate semantics (missing/skip/inconclusive/abstain handling) become visible.

Usage:
    python cross_admission_test.py --impl PR3|GLM1|GLM2|K3|QW1|QW2|QW3
    python cross_admission_test.py --matrix   # runs all impls, prints matrix

Abstract input space:
    hard gate status in {PASS, FAIL, INCONCLUSIVE, SKIP, MISSING}
    soft status          in {NO_VETO, VETO, ABSTAIN, MISSING}
Normalized output:
    ADMIT | REJECT | BLOCK | ESCALATE | NA | CRASH
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile

GATES = ["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"]

SCENARIOS = [
    {"id": "S1",  "desc": "all PASS + no_veto (baseline)",                "bad": {},                   "soft": "NO_VETO"},
    {"id": "S2",  "desc": "H3 FAIL + no_veto (hard dominance)",           "bad": {"H3": "FAIL"},       "soft": "NO_VETO"},
    {"id": "S3",  "desc": "all PASS + VETO (soft veto power)",            "bad": {},                   "soft": "VETO"},
    {"id": "S4",  "desc": "H3 FAIL + VETO (both fail)",                   "bad": {"H3": "FAIL"},       "soft": "VETO"},
    {"id": "S5",  "desc": "ALL gates MISSING + soft MISSING (fail-open?)","bad": "ALL_MISSING",        "soft": "MISSING"},
    {"id": "S6",  "desc": "H5 MISSING, rest PASS + no_veto",              "bad": {"H5": "MISSING"},    "soft": "NO_VETO"},
    {"id": "S7",  "desc": "H5 SKIP (not applicable), rest PASS",          "bad": {"H5": "SKIP"},       "soft": "NO_VETO"},
    {"id": "S8",  "desc": "H5 INCONCLUSIVE, rest PASS (block vs reject)", "bad": {"H5": "INCONCLUSIVE"},"soft": "NO_VETO"},
    {"id": "S9",  "desc": "all PASS + ABSTAIN (soft evidence insufficient)","bad": {},                  "soft": "ABSTAIN"},
    {"id": "S10", "desc": "all PASS + soft MISSING (soft never ran)",     "bad": {},                   "soft": "MISSING"},
    {"id": "S11", "desc": "H3 FAIL + ABSTAIN (hard dominates abstain)",   "bad": {"H3": "FAIL"},       "soft": "ABSTAIN"},
]


def scenario_input(sc):
    """Return {gate: status} for the 8 hard gates."""
    if sc["bad"] == "ALL_MISSING":
        return {g: "MISSING" for g in GATES}
    return {g: sc["bad"].get(g, "PASS") for g in GATES}


# ---------------------------------------------------------------- PR3
def run_pr3():
    from swarmkernel.contracts.gate import (
        Finding, GateId, GateResult, GateStatus, SoftGateResult, SoftVerdict,
    )
    from swarmkernel.gates.algebra import admit, build_hard_report

    gid = {"H1": GateId.H1_BUILD, "H2": GateId.H2_UNIT_PROPERTY, "H3": GateId.H3_HOLDOUT,
           "H4": GateId.H4_SURFACE, "H5": GateId.H5_DIFFERENTIAL, "H6": GateId.H6_INVARIANT,
           "H7": GateId.H7_DRIFT, "H8": GateId.H8_BUDGET}
    smap = {"PASS": GateStatus.PASS, "FAIL": GateStatus.FAIL,
            "INCONCLUSIVE": GateStatus.ERROR, "SKIP": GateStatus.NOT_APPLICABLE}
    vmap = {"NO_VETO": SoftVerdict.NO_VETO, "VETO": SoftVerdict.VETO, "ABSTAIN": SoftVerdict.ABSTAIN}

    out = {}
    for sc in SCENARIOS:
        try:
            results = []
            for g, st in scenario_input(sc).items():
                if st == "MISSING":
                    continue
                findings = [Finding(code="TEST.FORCED", message="forced failure")] if st in ("FAIL", "INCONCLUSIVE") else []
                results.append(GateResult(gate=gid[g], status=smap[st], findings=findings))
            soft = None if sc["soft"] == "MISSING" else SoftGateResult(verdict=vmap[sc["soft"]])
            ok = admit(build_hard_report("u1", "i1", results), soft)
            out[sc["id"]] = "ADMIT" if ok else "REJECT"
        except Exception as e:
            out[sc["id"]] = f"CRASH:{type(e).__name__}"
    return out


# ---------------------------------------------------------------- GLM1
def run_glm1():
    from specforge.gates.base import GateResult, GateVerdict, decide_admission

    smap = {"PASS": GateVerdict.PASS, "FAIL": GateVerdict.FAIL,
            "INCONCLUSIVE": GateVerdict.INCONCLUSIVE, "SKIP": GateVerdict.SKIP}
    vmap = {"NO_VETO": GateVerdict.PASS, "VETO": GateVerdict.FAIL, "ABSTAIN": GateVerdict.INCONCLUSIVE}

    out = {}
    for sc in SCENARIOS:
        try:
            hard = [GateResult(gate_id=g, verdict=smap[st], hard=True)
                    for g, st in scenario_input(sc).items() if st != "MISSING"]
            soft = ([] if sc["soft"] == "MISSING"
                    else [GateResult(gate_id="S", verdict=vmap[sc["soft"]], hard=False)])
            d = decide_admission(hard, soft)
            out[sc["id"]] = d.decision if d.decision != "BLOCK" else "BLOCK"
        except Exception as e:
            out[sc["id"]] = f"CRASH:{type(e).__name__}"
    return out


# ---------------------------------------------------------------- GLM2
def run_glm2():
    from swarmforge.gates.algebra import GateResult, Verdict, adjudicate

    smap = {"PASS": Verdict.PASS, "FAIL": Verdict.FAIL,
            "INCONCLUSIVE": Verdict.INCONCLUSIVE, "SKIP": Verdict.SKIP}

    out = {}
    for sc in SCENARIOS:
        try:
            hard = []
            for g, st in scenario_input(sc).items():
                if st == "MISSING":
                    continue
                blocking = st != "SKIP"
                hard.append(GateResult(gate_id=g, verdict=smap[st], blocking=blocking))
            vetoes = 1 if sc["soft"] == "VETO" else 0
            abstains = 1 if sc["soft"] == "ABSTAIN" else 0
            k = adjudicate(hard, soft_vetoes=vetoes, soft_abstains=abstains)
            out[sc["id"]] = k.value.upper()
        except Exception as e:
            out[sc["id"]] = f"CRASH:{type(e).__name__}"
    return out


# ---------------------------------------------------------------- K3 (orchestrator level)
def run_k3():
    from swarmdev.admission.orchestrator import AdmissionOrchestrator, BuiltInstance
    from swarmdev.contracts import RLevel, SpecDoc, Wave, WaveTask
    from swarmdev.contracts.oracle import JudgeVerdict
    from swarmdev.contracts.receipt import GateOutcome, GateStatus, SoftVerdict
    from swarmdev.contracts.wave import FanoutPolicy

    smap = {"PASS": GateStatus.PASS, "FAIL": GateStatus.FAIL,
            "INCONCLUSIVE": GateStatus.INCONCLUSIVE, "SKIP": GateStatus.SKIPPED}
    jmap = {"NO_VETO": "no_veto", "VETO": "veto", "ABSTAIN": "abstain"}

    out = {}
    for sc in SCENARIOS:
        try:
            gate_plan = scenario_input(sc)

            def builder(task, i):
                return BuiltInstance(instance_id=f"i{i}", instance_dir="/tmp/na", tier="L", cost_tokens=10)

            def gate_executor(built, task):
                outs = []
                for g, st in gate_plan.items():
                    if st == "MISSING":
                        continue
                    outs.append(GateOutcome(gate_id=g, status=smap[st],
                                            details="forced" if st != "PASS" else ""))
                return outs

            soft_judge = None
            if sc["soft"] != "MISSING":
                v = jmap[sc["soft"]]
                def soft_judge(built, task, _v=v):
                    jv = JudgeVerdict(verdict=_v, reasons=["forced"] if _v == "veto" else [])
                    return [SoftVerdict(rubric_id="r1", judge=jv)]

            orch = AdmissionOrchestrator(builder, gate_executor, soft_judge=soft_judge)
            wave = Wave(wave_id="w1", spec_delta_ids=["sd1"], tasks=[
                WaveTask(ru_id="ru1", spec_delta_ref="sd1", r_level=RLevel.R0,
                         fanout=FanoutPolicy(n_target=1))])
            spec = SpecDoc(spec_id="sp1", domain="d", version="1.0.0", l1_intent="intent")
            result = orch.execute_wave(wave, spec)
            out[sc["id"]] = "ADMIT" if result.admitted else "REJECT"
        except Exception as e:
            out[sc["id"]] = f"CRASH:{type(e).__name__}: {str(e)[:80]}"
    return out


# ---------------------------------------------------------------- QW1
def run_qw1():
    from swarm_kernel.contracts.admission import EvidenceReceipt
    from swarm_kernel.contracts.base import RLevel, Verdict
    from swarm_kernel.contracts.gates import GateId, GateResult, GateSuiteResult
    from swarm_kernel.contracts.oracle import EvidenceCitation, JudgeVerdict, JudgeVerdictKind
    from swarm_kernel.admission.transaction import AdmissionTransaction

    gid = {g.value: g for g in GateId}
    vmap = {"NO_VETO": JudgeVerdictKind.NO_VETO, "VETO": JudgeVerdictKind.VETO,
            "ABSTAIN": JudgeVerdictKind.ABSTAIN}

    out = {}
    with tempfile.TemporaryDirectory() as td:
        tx = AdmissionTransaction(td)
        for sc in SCENARIOS:
            try:
                if "SKIP" in scenario_input(sc).values():
                    out[sc["id"]] = "NA:no SKIP verdict in QW1 contract"
                    continue
                smap = {"PASS": Verdict.PASS, "FAIL": Verdict.FAIL,
                        "INCONCLUSIVE": Verdict.INCONCLUSIVE, "ERROR": Verdict.ERROR}
                results = [GateResult(gate_id=gid[g], verdict=smap[st])
                           for g, st in scenario_input(sc).items() if st != "MISSING"]
                suite = GateSuiteResult(instance_id="i1", results=results)
                jv = None
                if sc["soft"] != "MISSING":
                    jv = JudgeVerdict(rubric_id="r1", instance_id="i1", kind=vmap[sc["soft"]],
                                      reasons=["forced"] if sc["soft"] == "VETO" else [],
                                      citations=[EvidenceCitation(locator="spec#L2-001")] if sc["soft"] == "VETO" else [])
                receipt = EvidenceReceipt(wave_id="w1", delta_id="d1", r_level=RLevel.R0,
                                          chosen_instance_id="i1", gate_suite=suite, judge_verdict=jv)
                problems = tx.verify_receipt(receipt)
                out[sc["id"]] = "ADMIT" if not problems else ("REJECT" if any("not all passed" in p or "vetoed" in p for p in problems) else "BLOCK")
            except Exception as e:
                out[sc["id"]] = f"CRASH:{type(e).__name__}"
    return out


# ---------------------------------------------------------------- QW2
def run_qw2():
    from swarmfoundry.schema.gates import GateResult, admit

    smap = {"PASS": "pass", "FAIL": "fail", "INCONCLUSIVE": "error", "SKIP": "skip"}
    vmap = {"NO_VETO": "pass", "VETO": "fail"}

    out = {}
    for sc in SCENARIOS:
        try:
            hard = [GateResult(gate_id=g, status=smap[st])
                    for g, st in scenario_input(sc).items() if st != "MISSING"]
            if sc["soft"] == "ABSTAIN":
                out[sc["id"]] = "NA:no abstain status in QW2 gate contract"
                continue
            soft = [] if sc["soft"] == "MISSING" else [GateResult(gate_id="S", status=vmap[sc["soft"]])]
            d = admit(hard, soft, "i1")
            out[sc["id"]] = "ADMIT" if d.admitted else "REJECT"
        except Exception as e:
            out[sc["id"]] = f"CRASH:{type(e).__name__}"
    return out


# ---------------------------------------------------------------- QW3
def run_qw3():
    from opc.schemas.common import Verdict
    from opc.schemas.gates import AdmissionVerdict, GateReport

    smap = {"PASS": Verdict.PASS, "FAIL": Verdict.FAIL, "INCONCLUSIVE": Verdict.INCONCLUSIVE}
    vmap = {"NO_VETO": Verdict.PASS, "VETO": Verdict.FAIL, "ABSTAIN": Verdict.INCONCLUSIVE}

    out = {}
    for sc in SCENARIOS:
        try:
            if "SKIP" in scenario_input(sc).values():
                out[sc["id"]] = "NA:no SKIP verdict in QW3 contract"
                continue
            hard = {g: GateReport(gate=g, verdict=smap[st], instance_id="i1", wave_id="w1")
                    for g, st in scenario_input(sc).items() if st != "MISSING"}
            soft = None if sc["soft"] == "MISSING" else GateReport(gate="S", verdict=vmap[sc["soft"]])
            v = AdmissionVerdict.decide(hard, soft)
            out[sc["id"]] = "ADMIT" if v.admitted else "REJECT"
        except Exception as e:
            out[sc["id"]] = f"CRASH:{type(e).__name__}"
    return out


IMPLS = {
    "PR3":  (run_pr3,  "/workspace/wt-PR3/kernel/src"),
    "GLM1": (run_glm1, "/workspace/wt-GLM1/specforge"),
    "GLM2": (run_glm2, "/workspace/wt-GLM2/swarmforge"),
    "K3":   (run_k3,   "/workspace/wt-K3/swarmdev"),
    "QW1":  (run_qw1,  "/workspace/wt-QW1/swarm-kernel"),
    "QW2":  (run_qw2,  "/workspace/wt-QW2/swarmfoundry/src"),
    "QW3":  (run_qw3,  "/workspace/wt-QW3/opc/src"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impl", choices=list(IMPLS))
    ap.add_argument("--matrix", action="store_true")
    args = ap.parse_args()

    if args.matrix:
        results = {}
        for name, (fn, path) in IMPLS.items():
            p = subprocess.run(
                [sys.executable, __file__, "--impl", name],
                capture_output=True, text=True, cwd="/workspace")
            if p.returncode == 0:
                results[name] = json.loads(p.stdout.strip().splitlines()[-1])
            else:
                results[name] = {sc["id"]: f"CRASH:subprocess:{p.stderr.strip().splitlines()[-1][:100]}" for sc in SCENARIOS}
        impls = list(IMPLS)
        w = 10
        header = f"{'scenario':<38}" + "".join(f"{i:>{w}}" for i in impls)
        print(header)
        print("-" * len(header))
        for sc in SCENARIOS:
            row = f"{sc['id'] + ' ' + sc['desc'][:32]:<38}"
            for i in impls:
                v = results[i].get(sc["id"], "?")
                row += f"{v[:w - 1]:>{w}}"
            print(row)
        print()
        # divergence detection on ADMIT vs NOT-ADMIT
        for sc in SCENARIOS:
            vals = []
            for i in impls:
                v = results[i].get(sc["id"], "?")
                vals.append("ADMIT" if v == "ADMIT" else ("NA" if v.startswith("NA") else "NOT"))
            adm = vals.count("ADMIT"); nots = vals.count("NOT"); nas = vals.count("NA")
            if adm > 0 and nots > 0:
                who_admit = [impls[k] for k, v in enumerate(vals) if v == "ADMIT"]
                who_not = [impls[k] for k, v in enumerate(vals) if v == "NOT"]
                print(f"DIVERGENCE {sc['id']}: ADMIT={who_admit} NOT_ADMIT={who_not}")
        return

    fn, path = IMPLS[args.impl]
    sys.path.insert(0, path)
    print(json.dumps(fn()))


if __name__ == "__main__":
    main()
