from __future__ import annotations

import argparse
import json
import sys

from opc.world.ledger import AdmissionLedger
from opc.world.sanitizer import package_builder_workspace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="opc-admit")
    sub = parser.add_subparsers(dest="command", required=True)

    verify = sub.add_parser("ledger-verify")
    verify.add_argument("--ledger", required=True)

    package = sub.add_parser("package-workspace")
    package.add_argument("--spec-dir", required=True)
    package.add_argument("--dest-dir", required=True)
    package.add_argument("--holdout-dir", default=None)

    args = parser.parse_args(argv)
    if args.command == "ledger-verify":
        ok, problems = AdmissionLedger(args.ledger).verify()
        print(json.dumps({"ok": ok, "problems": problems}, ensure_ascii=False, indent=2))
        return 0 if ok else 1

    bundle_hash = package_builder_workspace(args.spec_dir, args.dest_dir, args.holdout_dir)
    print(bundle_hash)
    return 0


if __name__ == "__main__":
    sys.exit(main())
