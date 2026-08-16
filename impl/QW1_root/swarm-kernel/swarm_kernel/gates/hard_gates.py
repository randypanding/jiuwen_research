from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Optional

from swarm_kernel.contracts.base import Verdict
from swarm_kernel.contracts.gates import GateId, GateResult, WitnessRef
from swarm_kernel.diff.engine import run_differential
from swarm_kernel.golden.store import GoldenPolicyError, GoldenStore
from swarm_kernel.oracle.grader import ScenarioGrader, load_scenarios
from swarm_kernel.spec_repo.registry import check_drift

from .base import GateConfig, GateContext


def _hash_file(p: Path) -> str:
    import hashlib

    return hashlib.sha256(p.read_bytes()).hexdigest()


def _witness(p: Path, kind: str) -> WitnessRef:
    return WitnessRef(kind=kind, locator=str(p), content_sha256=_hash_file(p) if p.exists() else "")


def run_command_gate(gate_id: GateId, commands: list[list[str]], cwd: Path, max_attempts: int = 1, timeout: int = 300) -> GateResult:
    from .base import wilson_verdict

    start = time.time()
    if not commands:
        return GateResult(gate_id=gate_id, verdict=Verdict.INCONCLUSIVE, details={"reason": "no commands configured"})
    successes = 0
    attempts = 0
    logs: list[str] = []
    for attempt in range(1, max_attempts + 1):
        attempts = attempt
        ok = True
        for cmd in commands:
            try:
                proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
                if proc.returncode != 0:
                    ok = False
                    logs.append(f"attempt{attempt}:{' '.join(cmd)} rc={proc.returncode} {(proc.stderr or proc.stdout)[-400:]}")
                    break
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                ok = False
                logs.append(f"attempt{attempt}:{' '.join(cmd)} error={e}")
                break
        if ok:
            successes += 1
            break
    verdict_str = wilson_verdict(successes, attempts)
    verdict = {"pass": Verdict.PASS, "fail": Verdict.FAIL}.get(verdict_str, Verdict.INCONCLUSIVE)
    return GateResult(
        gate_id=gate_id,
        verdict=verdict,
        attempts=attempts,
        duration_ms=int((time.time() - start) * 1000),
        details={"successes": successes, "logs": logs[-5:]},
    )


def h1_build(ctx: GateContext) -> GateResult:
    commands = ctx.config.h1_commands or [["python3", "-m", "compileall", "-q", "."]]
    return run_command_gate(GateId.H1_BUILD, commands, ctx.instance_dir)


def h2_unit(ctx: GateContext) -> GateResult:
    commands = ctx.config.h2_commands
    if not commands and (ctx.instance_dir / "tests").exists():
        commands = [["python3", "-m", "pytest", "-q", "tests"]]
    if not commands:
        return GateResult(gate_id=GateId.H2_UNIT, verdict=Verdict.INCONCLUSIVE, details={"reason": "no unit tests present"})
    return run_command_gate(GateId.H2_UNIT, commands, ctx.instance_dir)


def h3_holdout(ctx: GateContext) -> GateResult:
    start = time.time()
    try:
        scenarios = load_scenarios(ctx.oracle_dir)
    except Exception as e:
        return GateResult(gate_id=GateId.H3_HOLDOUT, verdict=Verdict.ERROR, details={"error": str(e)})
    if not scenarios:
        return GateResult(gate_id=GateId.H3_HOLDOUT, verdict=Verdict.INCONCLUSIVE, details={"reason": "holdout suite empty"})
    grader = ScenarioGrader(scenarios)
    try:
        outcomes, suite_pass = grader.grade(ctx.instance_dir)
    except Exception as e:
        return GateResult(gate_id=GateId.H3_HOLDOUT, verdict=Verdict.ERROR, details={"error": str(e)})
    out_dir = ctx.out_dir / "h3"
    out_dir.mkdir(parents=True, exist_ok=True)
    report = out_dir / f"{ctx.instance_dir.name}.scenarios.json"
    report.write_text(json.dumps([o.model_dump(mode="json") for o in outcomes], indent=2, ensure_ascii=False), encoding="utf-8")
    failed = [o.scenario_id for o in outcomes if not o.passed]
    return GateResult(
        gate_id=GateId.H3_HOLDOUT,
        verdict=Verdict.PASS if suite_pass else Verdict.FAIL,
        duration_ms=int((time.time() - start) * 1000),
        witness_refs=[_witness(report, "scenario_report")],
        details={"total": len(outcomes), "failed": failed},
    )


def _load_contract_surface(instance_dir: Path) -> Optional[dict]:
    fp = instance_dir / "contract.json"
    if not fp.exists():
        return None
    return json.loads(fp.read_text(encoding="utf-8"))


def h4_contract_surface(ctx: GateContext) -> GateResult:
    baseline_path = ctx.oracle_dir / "baseline_contract.json"
    surface = _load_contract_surface(ctx.instance_dir)
    if surface is None:
        return GateResult(gate_id=GateId.H4_CONTRACT_SURFACE, verdict=Verdict.FAIL, details={"error": "contract.json missing"})
    if ctx.wave and ctx.wave.frozen_interfaces:
        import hashlib

        canon = json.dumps(surface, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canon.encode()).hexdigest()
        expected = {fi.interface_id: fi.contract_digest for fi in ctx.wave.frozen_interfaces}
        for iid, exp in expected.items():
            if exp and digest != exp and not digest.startswith(exp):
                return GateResult(gate_id=GateId.H4_CONTRACT_SURFACE, verdict=Verdict.FAIL, details={"frozen_interface": iid, "digest": digest, "expected": exp})
    if not baseline_path.exists():
        return GateResult(gate_id=GateId.H4_CONTRACT_SURFACE, verdict=Verdict.PASS, details={"note": "no baseline; surface recorded"}, witness_refs=[])
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    old_exports = set(baseline.get("exports", []))
    new_exports = set(surface.get("exports", []))
    removed = sorted(old_exports - new_exports)
    old_sigs = baseline.get("signatures", {})
    new_sigs = surface.get("signatures", {})
    changed = sorted(k for k in old_sigs if k in new_sigs and old_sigs[k] != new_sigs[k])
    if removed or changed:
        return GateResult(gate_id=GateId.H4_CONTRACT_SURFACE, verdict=Verdict.FAIL, details={"removed_exports": removed, "changed_signatures": changed})
    return GateResult(gate_id=GateId.H4_CONTRACT_SURFACE, verdict=Verdict.PASS, details={"added_exports": sorted(new_exports - old_exports)})


def h5_differential(ctx: GateContext) -> GateResult:
    start = time.time()
    golden_dir = ctx.oracle_dir / "golden"
    group = [p for p in ctx.peer_instances if p.exists()] or [ctx.instance_dir]
    out_dir = ctx.out_dir / "h5"
    out_dir.mkdir(parents=True, exist_ok=True)
    if len(group) >= 2:
        try:
            report = run_differential(group, ctx.oracle_dir, seed=ctx.diff_seed, corpus_size=ctx.corpus_size)
        except Exception as e:
            return GateResult(gate_id=GateId.H5_DIFFERENTIAL, verdict=Verdict.ERROR, details={"error": str(e)})
        rp = out_dir / f"diff-{ctx.instance_dir.name}.json"
        rp.write_text(json.dumps({"divergent": report.divergent, "pairwise": report.pairwise, "divergent_inputs": report.divergent_inputs[:5]}, indent=2, ensure_ascii=False), encoding="utf-8")
        verdict = Verdict.FAIL if report.divergent else Verdict.PASS
        return GateResult(
            gate_id=GateId.H5_DIFFERENTIAL,
            verdict=verdict,
            duration_ms=int((time.time() - start) * 1000),
            witness_refs=[_witness(rp, "diff_report")],
            details={"n_instances": len(group), "divergent": report.divergent, "corpus_size": report.corpus_size},
        )
    if golden_dir.exists():
        store = GoldenStore(golden_dir)
        mismatches_all: list[str] = []
        ok = True
        for gp in sorted(golden_dir.glob("*.golden")):
            artifact_id = gp.stem
            try:
                from swarm_kernel.oracle.grader import load_instance_adapter

                run = load_instance_adapter(ctx.instance_dir)
                meta = json.loads((golden_dir / f"{artifact_id}.input.json").read_text(encoding="utf-8")) if (golden_dir / f"{artifact_id}.input.json").exists() else {}
                actual = json.dumps(run(meta.get("inputs", {})), sort_keys=True, ensure_ascii=False, default=str, indent=2)
            except Exception as e:
                return GateResult(gate_id=GateId.H5_DIFFERENTIAL, verdict=Verdict.ERROR, details={"error": str(e)})
            match, mismatches, manifest = store.compare(artifact_id, actual)
            if manifest is None or not manifest.approved:
                ok = False
                mismatches_all.append(f"{artifact_id}: manifest missing approval")
            if not match:
                ok = False
                mismatches_all.extend(f"{artifact_id}:{m}" for m in mismatches[:5])
        return GateResult(
            gate_id=GateId.H5_DIFFERENTIAL,
            verdict=Verdict.PASS if ok else Verdict.FAIL,
            duration_ms=int((time.time() - start) * 1000),
            details={"golden_mismatches": mismatches_all[:10]},
        )
    return GateResult(gate_id=GateId.H5_DIFFERENTIAL, verdict=Verdict.INCONCLUSIVE, details={"reason": "single instance without golden baseline"})


def h6_invariants(ctx: GateContext) -> GateResult:
    cfg = ctx.config
    problems: list[str] = []
    total_bytes = 0
    secret_res = [re.compile(p) for p in cfg.secret_patterns]
    forbidden_res = [re.compile(p) for p in cfg.forbidden_patterns]
    for fp in sorted(ctx.instance_dir.rglob("*")):
        if not fp.is_file():
            continue
        size = fp.stat().st_size
        total_bytes += size
        if fp.suffix not in (".py", ".ts", ".js", ".java", ".go", ".rs", ".json", ".yaml", ".yml", ".md", ".txt"):
            continue
        try:
            text = fp.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for rx in secret_res:
            if rx.search(text):
                problems.append(f"secret pattern at {fp.relative_to(ctx.instance_dir)}")
        for rx in forbidden_res:
            if rx.search(text):
                problems.append(f"forbidden pattern {rx.pattern!r} at {fp.relative_to(ctx.instance_dir)}")
        for imp in cfg.forbidden_imports:
            if re.search(rf"\b{re.escape(imp)}\b", text):
                problems.append(f"forbidden import {imp} at {fp.relative_to(ctx.instance_dir)}")
    if total_bytes > cfg.max_total_bytes:
        problems.append(f"instance too large: {total_bytes} > {cfg.max_total_bytes}")
    surface = _load_contract_surface(ctx.instance_dir)
    if surface:
        for dep in surface.get("dependencies", []):
            lic = dep.get("license", "")
            if lic in cfg.license_denylist:
                problems.append(f"license denylist: {dep.get('name')} {lic}")
    verdict = Verdict.PASS if not problems else Verdict.FAIL
    return GateResult(gate_id=GateId.H6_INVARIANTS, verdict=verdict, details={"problems": problems[:20], "total_bytes": total_bytes})


def h7_drift(ctx: GateContext) -> GateResult:
    if ctx.registry is None:
        return GateResult(gate_id=GateId.H7_DRIFT, verdict=Verdict.INCONCLUSIVE, details={"reason": "no spec registry provided"})
    records = check_drift(ctx.registry, ctx.instance_dir)
    stale = [r for r in records if r.state.value == "stale"]
    orphan = [r for r in records if r.state.value == "orphan"]
    unimpl = [r for r in records if r.state.value == "unimplemented"]
    ok_n = len([r for r in records if r.state.value == "ok"])
    out_dir = ctx.out_dir / "h7"
    out_dir.mkdir(parents=True, exist_ok=True)
    rp = out_dir / f"drift-{ctx.instance_dir.name}.json"
    rp.write_text(json.dumps([r.model_dump(mode="json") for r in records], indent=2, ensure_ascii=False), encoding="utf-8")
    verdict = Verdict.PASS if not (stale or orphan or unimpl) else Verdict.FAIL
    return GateResult(
        gate_id=GateId.H7_DRIFT,
        verdict=verdict,
        witness_refs=[_witness(rp, "drift_report")],
        details={"stale": len(stale), "orphan": len(orphan), "unimplemented": len(unimpl), "ok": ok_n},
    )


def h8_budget(ctx: GateContext) -> GateResult:
    report_fp = ctx.instance_dir / "report.json"
    if not report_fp.exists():
        return GateResult(gate_id=GateId.H8_BUDGET, verdict=Verdict.INCONCLUSIVE, details={"reason": "no resource report"})
    try:
        report = json.loads(report_fp.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return GateResult(gate_id=GateId.H8_BUDGET, verdict=Verdict.ERROR, details={"error": str(e)})
    cfg = ctx.config
    over = []
    if float(report.get("tokens", 0)) > cfg.budget_tokens:
        over.append("tokens")
    if float(report.get("seconds", 0)) > cfg.budget_seconds:
        over.append("seconds")
    if float(report.get("bytes", 0)) > cfg.budget_bytes:
        over.append("bytes")
    return GateResult(gate_id=GateId.H8_BUDGET, verdict=Verdict.PASS if not over else Verdict.FAIL, details={"report": report, "over_budget": over})


GATE_IMPLS = {
    GateId.H1_BUILD: h1_build,
    GateId.H2_UNIT: h2_unit,
    GateId.H3_HOLDOUT: h3_holdout,
    GateId.H4_CONTRACT_SURFACE: h4_contract_surface,
    GateId.H5_DIFFERENTIAL: h5_differential,
    GateId.H6_INVARIANTS: h6_invariants,
    GateId.H7_DRIFT: h7_drift,
    GateId.H8_BUDGET: h8_budget,
}
