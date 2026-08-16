from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from swarmfoundry.contracts.compat import diff_surfaces
from swarmfoundry.contracts.extract import dump_surface, extract_surface, load_surface
from swarmfoundry.gates.context import GateContext, load_config
from swarmfoundry.gates.runner import GateRunner, build_receipt, register_receipt
from swarmfoundry.oracle.runner import load_suite, run_suite
from swarmfoundry.specrepo.coverage import witness_coverage
from swarmfoundry.specrepo.loader import SpecRepo
from swarmfoundry.specrepo.seal import reseal


def _cmd_spec_validate(args) -> int:
    repo = SpecRepo(Path(args.repo))
    problems = repo.validate_all()
    for p in problems:
        print(f"PROBLEM {p}")
    for dom in repo.list_domains():
        report = witness_coverage(repo.load_domain(dom))
        print(
            f"coverage {dom}: {report.covered}/{report.total_normative} "
            f"(advisory_only={report.advisory_only} unverifiable={report.unverifiable})"
        )
    return 1 if problems else 0


def _cmd_spec_seal(args) -> int:
    repo = SpecRepo(Path(args.repo))
    seals = reseal(repo)
    total = sum(len(v) for v in seals.values())
    print(f"sealed {total} clauses across {len(seals)} domains -> {repo.root}/registry/seals.json")
    return 0


def _cmd_surface_extract(args) -> int:
    surface = extract_surface(Path(args.dir), module=args.module)
    dump_surface(surface, Path(args.out))
    print(f"extracted {len(surface.symbols)} symbols -> {args.out}")
    return 0


def _cmd_surface_diff(args) -> int:
    diff = diff_surfaces(load_surface(Path(args.old)), load_surface(Path(args.new)))
    print(json.dumps(diff.to_dict(), ensure_ascii=False, indent=2))
    return 1 if diff.breaking() else 0


def _cmd_oracle_run(args) -> int:
    suite_dir = Path(args.suite)
    suite = load_suite(suite_dir)
    results = run_suite(suite, Path(args.instance), suite_dir)
    for r in results:
        print(f"{'PASS' if r.passed else 'FAIL'} {r.scenario_id}: {r.detail}")
    return 0 if all(r.passed for r in results) else 1


def _cmd_gates_run(args) -> int:
    repo = SpecRepo(Path(args.spec_repo)) if args.spec_repo else None
    config = load_config(Path(args.config)) if args.config else {}
    ctx = GateContext(
        instance_dir=Path(args.instance),
        instance_id=args.instance_id,
        spec_repo=repo,
        config=config,
        r_level=args.r_level,
        baseline_surface_path=Path(args.baseline) if args.baseline else None,
        holdout_dirs=tuple(Path(p) for p in args.holdout),
        diff_suite_dir=Path(args.diff_suite) if args.diff_suite else None,
        sibling_instances=tuple(Path(p) for p in args.sibling),
    )
    decision = GateRunner().decide(ctx)
    print(json.dumps(decision.to_dict(), ensure_ascii=False, indent=2))
    if args.receipt_dir:
        receipt = build_receipt(
            wave_id=args.wave_id or "wave-local",
            spec_delta_id=args.spec_delta or "delta-local",
            ctx=ctx,
            decision=decision,
            diff_conclusion=args.diff_conclusion or "not_run",
        )
        path = register_receipt(receipt, Path(args.receipt_dir))
        print(f"receipt -> {path}")
    return 0 if decision.admitted else 1


def _cmd_selftest(args) -> int:
    from swarmfoundry.selftest import run_selftest

    return run_selftest(verbose=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="swarmfoundry")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("spec-validate")
    p.add_argument("--repo", required=True)
    p.set_defaults(func=_cmd_spec_validate)

    p = sub.add_parser("spec-seal")
    p.add_argument("--repo", required=True)
    p.set_defaults(func=_cmd_spec_seal)

    p = sub.add_parser("surface-extract")
    p.add_argument("--dir", required=True)
    p.add_argument("--module", default="instance")
    p.add_argument("--out", required=True)
    p.set_defaults(func=_cmd_surface_extract)

    p = sub.add_parser("surface-diff")
    p.add_argument("--old", required=True)
    p.add_argument("--new", required=True)
    p.set_defaults(func=_cmd_surface_diff)

    p = sub.add_parser("oracle-run")
    p.add_argument("--suite", required=True)
    p.add_argument("--instance", required=True)
    p.set_defaults(func=_cmd_oracle_run)

    p = sub.add_parser("gates-run")
    p.add_argument("--instance", required=True)
    p.add_argument("--instance-id", required=True)
    p.add_argument("--spec-repo")
    p.add_argument("--config")
    p.add_argument("--r-level", default="R0")
    p.add_argument("--baseline")
    p.add_argument("--holdout", action="append", default=[])
    p.add_argument("--diff-suite")
    p.add_argument("--sibling", action="append", default=[])
    p.add_argument("--receipt-dir")
    p.add_argument("--wave-id")
    p.add_argument("--spec-delta")
    p.add_argument("--diff-conclusion")
    p.set_defaults(func=_cmd_gates_run)

    p = sub.add_parser("selftest")
    p.set_defaults(func=_cmd_selftest)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
