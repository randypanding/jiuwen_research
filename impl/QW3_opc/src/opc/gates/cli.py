from __future__ import annotations

import argparse
import json
import sys

from opc.gates.runner import ALL_GATES, build_context


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="opc-gate")
    parser.add_argument("--gate", required=True, choices=sorted(ALL_GATES))
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
    args = parser.parse_args(argv)

    ctx = build_context(args)
    report = ALL_GATES[args.gate]().run(ctx)
    print(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return 0 if report.verdict.value == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
