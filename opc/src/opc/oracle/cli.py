from __future__ import annotations

import argparse
import json
import sys

from opc.oracle.scenarios import ScenarioRunner, load_scenarios


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="opc-oracle")
    parser.add_argument("--holdout-dir", required=True)
    parser.add_argument("--instance-dir", required=True)
    parser.add_argument("--scenario", default=None, help="run a single scenario id")
    args = parser.parse_args(argv)

    runner = ScenarioRunner()
    results = []
    for scenario in load_scenarios(args.holdout_dir):
        if args.scenario and scenario.scenario_id != args.scenario:
            continue
        results.append(runner.run(scenario, args.instance_dir))
    output = [r.model_dump(mode="json") for r in results]
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if all(r.status.value == "pass" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
