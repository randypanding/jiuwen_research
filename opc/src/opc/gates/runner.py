from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from opc.gates.base import GateContext
from opc.gates.h1_build import H1BuildGate
from opc.gates.h2_tests import H2TestsGate
from opc.gates.h3_holdout import H3HoldoutGate
from opc.gates.h4_surface import H4ContractSurfaceGate
from opc.gates.h5_diff import H5DiffGate
from opc.gates.h6_constitution import H6ConstitutionGate
from opc.gates.h7_drift import H7DriftGate
from opc.gates.h8_budget import H8BudgetGate
from opc.gates.waivers import find_valid_waiver, load_waivers
from opc.schemas.common import Verdict
from opc.schemas.gates import AdmissionVerdict, CheckResult, GateReport
from opc.specrepo.lint import load_repo

ALL_GATES = {
    "H1": H1BuildGate,
    "H2": H2TestsGate,
    "H3": H3HoldoutGate,
    "H4": H4ContractSurfaceGate,
    "H5": H5DiffGate,
    "H6": H6ConstitutionGate,
    "H7": H7DriftGate,
    "H8": H8BudgetGate,
}


class GateRunner:
    """Runs the full hard-gate conjunction plus the soft gate.

    Admission algebra: Admit = (H1 ^ ... ^ H8) ^ S. Every gate is veto-only.
    A gate that cannot run yields INCONCLUSIVE, which blocks admission unless
    a valid human-approved waiver covers it; the waiver is recorded in the
    verdict so it lands in the evidence receipt.
    """

    def __init__(self, gate_ids: tuple[str, ...] = ("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8")):
        self.gate_ids = gate_ids

    def run_reports(
        self,
        ctx: GateContext,
        soft: GateReport | None = None,
        waivers_file: str | Path | None = None,
    ) -> tuple[AdmissionVerdict, dict[str, GateReport]]:
        waivers = load_waivers(waivers_file) if waivers_file else []
        hard: dict[str, GateReport] = {}
        for gate_id in self.gate_ids:
            report = ALL_GATES[gate_id]().run(ctx)
            if report.verdict is not Verdict.PASS:
                waiver = find_valid_waiver(
                    waivers, gate_id, ctx.contract_id, (ctx.r_level().value if ctx.r_level() else "")
                )
                if waiver is not None:
                    report.verdict = Verdict.PASS
                    report.artifacts["waiver_id"] = waiver.waiver_id
                    report.artifacts["waiver_reason"] = waiver.reason
                    report.checks.append(
                        CheckResult(
                            id=f"{gate_id.lower()}.waiver",
                            status=Verdict.PASS,
                            detail=f"waived by {waiver.waiver_id} (approver={waiver.approver}, expires={waiver.expires_at.isoformat()})",
                        )
                    )
            hard[gate_id] = report
        return AdmissionVerdict.decide(hard, soft, required_hard=self.gate_ids), hard

    def run(
        self,
        ctx: GateContext,
        soft: GateReport | None = None,
        waivers_file: str | Path | None = None,
    ) -> AdmissionVerdict:
        verdict, _ = self.run_reports(ctx, soft, waivers_file)
        return verdict


def build_context(args: argparse.Namespace) -> GateContext:
    manifest = load_repo(args.spec_dir)
    return GateContext(
        instance_id=args.instance_id,
        instance_dir=Path(args.instance_dir),
        spec_dir=Path(args.spec_dir),
        manifest=manifest,
        wave_id=getattr(args, "wave_id", "") or "",
        contract_id=args.contract_id,
        holdout_dir=Path(args.holdout_dir) if getattr(args, "holdout_dir", None) else None,
        baseline_dir=Path(args.baseline_dir) if getattr(args, "baseline_dir", None) else None,
        corpus_file=Path(args.corpus_file) if getattr(args, "corpus_file", None) else None,
        golden_dir=Path(args.golden_dir) if getattr(args, "golden_dir", None) else None,
        policy_file=Path(args.policy_file) if getattr(args, "policy_file", None) else None,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="opc-gate-runner")
    parser.add_argument("--instance-id", required=True)
    parser.add_argument("--instance-dir", required=True)
    parser.add_argument("--spec-dir", required=True)
    parser.add_argument("--contract-id", required=True)
    parser.add_argument("--wave-id", default="")
    parser.add_argument("--holdout-dir", default=None)
    parser.add_argument("--baseline-dir", default=None)
    parser.add_argument("--corpus-file", default=None)
    parser.add_argument("--golden-dir", default=None)
    parser.add_argument("--policy-file", default=None)
    parser.add_argument("--waivers-file", default=None)
    parser.add_argument("--gates", default="H1,H2,H3,H4,H5,H6,H7,H8")
    args = parser.parse_args(argv)

    ctx = build_context(args)
    runner = GateRunner(tuple(g.strip() for g in args.gates.split(",") if g.strip()))
    verdict, hard = runner.run_reports(ctx, waivers_file=args.waivers_file)
    output = {
        "admitted": verdict.admitted,
        "blocking_gates": verdict.blocking_gates,
        "soft_verdict": verdict.soft_verdict.value,
        "hard": {g: {"verdict": r.verdict.value, "waiver": r.artifacts.get("waiver_id")} for g, r in hard.items()},
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if verdict.admitted else 1


if __name__ == "__main__":
    sys.exit(main())
