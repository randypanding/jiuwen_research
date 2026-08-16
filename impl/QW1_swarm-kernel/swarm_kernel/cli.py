from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from swarm_kernel.contracts.admission import DriftCheckSummary, EvidenceReceipt
from swarm_kernel.contracts.base import Verdict
from swarm_kernel.contracts.gates import GateSuiteResult
from swarm_kernel.contracts.oracle import JudgeVerdictKind
from swarm_kernel.contracts.spec import SpecDoc
from swarm_kernel.gates.base import GateConfig, GateContext
from swarm_kernel.gates.runner import run_suite, suite_exit_code
from swarm_kernel.spec_repo.registry import ClauseRegistry, check_drift


def cmd_gates(args: argparse.Namespace) -> int:
    instance = Path(args.instance)
    oracle = Path(args.oracle)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    registry = None
    if args.spec:
        spec = SpecDoc.model_validate_json(Path(args.spec).read_text(encoding="utf-8"))
        registry = ClauseRegistry(spec)
    ctx = GateContext(
        instance_dir=instance,
        oracle_dir=oracle,
        registry=registry,
        out_dir=out,
        config=GateConfig(),
        peer_instances=[Path(p) for p in args.group or []],
        diff_seed=args.seed,
        corpus_size=args.corpus_size,
    )
    suite = run_suite(ctx)
    report = out / f"suite-{instance.name}.json"
    report.write_text(suite.model_dump_json(indent=2), encoding="utf-8")
    print(json.dumps({"instance": instance.name, "hard_pass": suite.hard_pass, "blocking": [g.value for g in suite.blocking_gates()], "report": str(report)}, ensure_ascii=False))
    return suite_exit_code(suite)


def cmd_drift(args: argparse.Namespace) -> int:
    spec = SpecDoc.model_validate_json(Path(args.spec).read_text(encoding="utf-8"))
    registry = ClauseRegistry(spec)
    records = check_drift(registry, Path(args.root))
    print(json.dumps([r.model_dump(mode="json") for r in records], ensure_ascii=False, indent=2))
    return 1 if any(r.state.value != "ok" for r in records) else 0


def cmd_admit(args: argparse.Namespace) -> int:
    from swarm_kernel.admission.transaction import AdmissionTransaction

    receipt = EvidenceReceipt.model_validate_json(Path(args.receipt).read_text(encoding="utf-8"))
    tx = AdmissionTransaction(Path(args.world_root))
    decision = tx.admit(receipt)
    print(decision.model_dump_json(indent=2))
    return 0 if decision.admit else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="swarm-kernel")
    sub = parser.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gates", help="run H1-H8 hard gate suite")
    g.add_argument("action", choices=["run"])
    g.add_argument("--instance", required=True)
    g.add_argument("--oracle", required=True)
    g.add_argument("--spec", default=None)
    g.add_argument("--out", required=True)
    g.add_argument("--group", nargs="*", default=None)
    g.add_argument("--seed", type=int, default=42)
    g.add_argument("--corpus-size", type=int, default=50)
    g.set_defaults(func=cmd_gates)

    d = sub.add_parser("drift", help="scan spec anchors")
    d.add_argument("action", choices=["scan"])
    d.add_argument("--spec", required=True)
    d.add_argument("--root", required=True)
    d.set_defaults(func=cmd_drift)

    a = sub.add_parser("admit", help="run admission transaction")
    a.add_argument("action", choices=["commit"])
    a.add_argument("--receipt", required=True)
    a.add_argument("--world-root", required=True)
    a.set_defaults(func=cmd_admit)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
