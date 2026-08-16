from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from opc.diff.engine import DiffEngine


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="opc-diff")
    parser.add_argument("--instance", action="append", required=True, help="id=dir, repeatable")
    parser.add_argument("--corpus-file", required=True)
    parser.add_argument("--entrypoint", default="main:run")
    parser.add_argument("--redact", action="append", default=[])
    parser.add_argument("--dont-care", action="append", default=[])
    parser.add_argument("--min-instances", type=int, default=3)
    args = parser.parse_args(argv)

    instances = {}
    for item in args.instance:
        instance_id, _, directory = item.partition("=")
        instances[instance_id] = Path(directory)
    corpus = json.loads(Path(args.corpus_file).read_text(encoding="utf-8"))
    report = DiffEngine().run(
        instances=instances,
        entrypoint=args.entrypoint,
        corpus=corpus,
        redactions=args.redact,
        dont_care_scopes=args.dont_care,
        min_instances=args.min_instances,
    )
    print(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return 0 if report.verdict.value == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
