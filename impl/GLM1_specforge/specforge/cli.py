"""SpecForge CLI (WP11).

Commands:
  validate-spec <spec.md>       parse + lint (gate/holdout registries optional)
  extract-contract <path>       dump SurfaceSnapshot JSON
  contract-diff <old.json> <new.json>
  gates run <instance_dir> --spec <spec.md> [--json]
  difftest run --mode calibration ...
  golden compare|approve
  judge calibrate
  wave status <root>
  metrics report
  demo                          run the dogfood example end to end
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _cmd_validate_spec(args: argparse.Namespace) -> int:
    from .spec import load_and_lint

    unit, rep = load_and_lint(args.spec)
    print(json.dumps({
        "spec_id": unit.spec_id, "version": unit.version, "r_level": unit.r_level,
        "clauses": len(unit.clauses), "dont_cares": len(unit.dont_cares),
        "lint_ok": rep.ok, "errors": [str(e) for e in rep.errors],
    }, ensure_ascii=False, indent=1))
    return 0 if rep.ok else 1


def _cmd_extract_contract(args: argparse.Namespace) -> int:
    from .contracts import extract

    snap = extract(args.path)
    print(snap.to_json())
    return 0


def _cmd_contract_diff(args: argparse.Namespace) -> int:
    from .contracts import SurfaceSnapshot, diff_surfaces, explain

    old = SurfaceSnapshot.from_json(Path(args.old).read_text(encoding="utf-8"))
    new = SurfaceSnapshot.from_json(Path(args.new).read_text(encoding="utf-8"))
    delta = diff_surfaces(old, new)
    print(json.dumps(delta.to_dict(), ensure_ascii=False, indent=1))
    print(explain(delta), file=sys.stderr)
    return 1 if delta.has_breaking else 0


def _cmd_gates(args: argparse.Namespace) -> int:
    from .gates import GateContext, decide_admission, run_hard_suite
    from .spec import parse_spec

    unit = parse_spec(path=args.spec) if args.spec else None
    ctx = GateContext(instance_path=args.instance_dir, world_path=args.world,
                      spec_unit=unit, config={"artifacts": unit.artifacts if unit else []})
    suite = run_hard_suite(ctx, fail_fast=not args.no_fail_fast)
    decision = decide_admission(suite.results, [])
    print(json.dumps({"suite": suite.to_dict(), "admission": {
        "decision": decision.decision, "reasons": decision.reasons,
        "constitution_refs": decision.constitution_refs}}, ensure_ascii=False, indent=1))
    return 0 if decision.admitted else 1


def _cmd_wave_status(args: argparse.Namespace) -> int:
    from .wave import FakeInstancePort, WaveManager

    wm = WaveManager(args.root, FakeInstancePort(args.root + "/instances"))
    print(json.dumps(wm.frontier_status(), ensure_ascii=False, indent=1))
    return 0


def _cmd_metrics(args: argparse.Namespace) -> int:
    from .metrics import HealthReport, render_human_report

    rep = HealthReport()
    if args.data:
        d = json.loads(Path(args.data).read_text(encoding="utf-8"))
        for k, v in d.items():
            if hasattr(rep, k):
                setattr(rep, k, v)
    print(render_human_report(rep))
    return 0


def _cmd_demo(args: argparse.Namespace) -> int:
    try:
        from tests.test_e2e_demo import run_demo
    except ImportError as e:
        print(f"demo requires running from the specforge repo root (tests/ present): {e}")
        return 2
    result = run_demo()
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0 if result.get("ok") else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="specforge")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("validate-spec")
    sp.add_argument("spec")
    sp.set_defaults(func=_cmd_validate_spec)

    sp = sub.add_parser("extract-contract")
    sp.add_argument("path")
    sp.set_defaults(func=_cmd_extract_contract)

    sp = sub.add_parser("contract-diff")
    sp.add_argument("old")
    sp.add_argument("new")
    sp.set_defaults(func=_cmd_contract_diff)

    sp = sub.add_parser("gates")
    sub2 = sp.add_subparsers(dest="gates_cmd", required=True)
    spr = sub2.add_parser("run")
    spr.add_argument("instance_dir")
    spr.add_argument("--spec")
    spr.add_argument("--world", default=".")
    spr.add_argument("--json", action="store_true")
    spr.add_argument("--no-fail-fast", action="store_true")
    spr.set_defaults(func=_cmd_gates)

    sp = sub.add_parser("wave")
    sub2 = sp.add_subparsers(dest="wave_cmd", required=True)
    spr = sub2.add_parser("status")
    spr.add_argument("root")
    spr.set_defaults(func=_cmd_wave_status)

    sp = sub.add_parser("metrics")
    sp.add_argument("--data")
    sp.set_defaults(func=_cmd_metrics)

    sp = sub.add_parser("demo")
    sp.set_defaults(func=_cmd_demo)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
