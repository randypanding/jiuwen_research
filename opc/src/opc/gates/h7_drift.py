from __future__ import annotations

import ast
import json
import time
from pathlib import Path

import yaml

from opc.gates.base import Gate, GateContext, check, worst
from opc.gates.surface import extract_surface
from opc.oracle.scenarios import load_scenarios
from opc.schemas.common import Verdict, content_hash
from opc.schemas.gates import CheckResult, GateReport

SUBMISSION_MANIFEST = "opc_submission.json"


def _instance_test_names(instance_dir: Path) -> set[str]:
    names: set[str] = set()
    for path in sorted(instance_dir.rglob("test_*.py")):
        rel = str(path.relative_to(instance_dir))
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                names.add(node.name)
                names.add(f"{rel}::{node.name}")
    return names


class H7DriftGate(Gate):
    """H7: spec<->code drift detection (the reconciler's mechanical half).

    Four deterministic channels, cheapest first:
      1. hash channel: the instance's submission manifest must commit to the
         exact contract content hash it was generated from (SpecSeal-style);
      2. witness existence: every H2/H3 witness bound in the spec resolves
         to a real test / scenario;
      3. structural channel: every contract interface symbol exists;
      4. coverage channel: no clause silently lost its mechanical witness.

    A drift hit defaults to 'defect, block' - the world's existing behaviour
    is never truth; only the spec is.
    """

    gate_id = "H7"

    def run(self, ctx: GateContext) -> GateReport:
        started = time.monotonic()
        checks: list[CheckResult] = []
        contract = ctx.contract()
        if contract is None:
            checks.append(check("h7.contract", False, "no contract bound"))
            return self.report(ctx, Verdict.FAIL, checks, started)

        manifest_path = ctx.instance_dir / SUBMISSION_MANIFEST
        if not manifest_path.exists():
            checks.append(
                check("h7.provenance", False, f"instance lacks {SUBMISSION_MANIFEST}; origin unprovable")
            )
        else:
            submission = json.loads(manifest_path.read_text(encoding="utf-8"))
            contract_file = ctx.spec_dir / "L2" / f"{ctx.contract_id}.contract.yaml"
            if contract_file.exists():
                current_hash = content_hash_from_file(contract_file)
            else:
                current_hash = content_hash(contract)
            recorded = submission.get("contract_hash", "")
            checks.append(
                check(
                    "h7.provenance",
                    recorded == current_hash,
                    "contract hash matches submission" if recorded == current_hash else f"contract drifted: recorded {recorded[:19]}… current {current_hash[:19]}…",
                )
            )
            checks.append(
                check(
                    "h7.spec_version",
                    submission.get("spec_version", "") == ctx.manifest.spec_version,
                    f"submission spec_version={submission.get('spec_version')!r} repo={ctx.manifest.spec_version!r}",
                )
            )

        test_names = _instance_test_names(ctx.instance_dir)
        missing_h2 = []
        for clause in contract.clauses:
            for witness in clause.witnesses:
                if witness.gate == "H2" and witness.target not in test_names:
                    missing_h2.append(f"{clause.id}->{witness.target}")
        checks.append(
            check("h7.h2_witnesses", not missing_h2, f"unresolvable H2 witnesses: {missing_h2[:8]}")
        )

        if ctx.holdout_dir is not None:
            scenario_ids = {s.scenario_id for s in load_scenarios(ctx.holdout_dir)}
            missing_h3 = []
            for clause in contract.clauses:
                for witness in clause.witnesses:
                    if witness.gate == "H3" and witness.target not in scenario_ids:
                        missing_h3.append(f"{clause.id}->{witness.target}")
            checks.append(
                check("h7.h3_witnesses", not missing_h3, f"unresolvable H3 witnesses: {missing_h3[:8]}")
            )

        surface = extract_surface(ctx.instance_dir)
        suffixes = {symbol.rsplit(".", 1)[-1] for symbol in surface}
        missing_symbols = [i.symbol for i in contract.interface_surface if i.symbol not in suffixes]
        checks.append(
            check("h7.interface_symbols", not missing_symbols, f"interface symbols vanished: {missing_symbols}")
        )

        naked = [c.id for c in contract.clauses if not c.is_verifiable and not c.advisory]
        checks.append(
            check(
                "h7.witness_coverage",
                not naked,
                f"clauses lost mechanical witnesses without advisory flag: {naked}",
            )
        )

        return self.report(ctx, worst([c.status for c in checks]), checks, started)


def content_hash_from_file(path: Path) -> str:
    from opc.schemas.spec import ContractSpec

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return content_hash(ContractSpec.model_validate(data))
