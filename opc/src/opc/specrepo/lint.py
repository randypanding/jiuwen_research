from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

from opc.schemas.common import Verdict
from opc.schemas.gates import CheckResult
from opc.schemas.spec import ContractSpec, SpecRepoManifest

METADATA_FILE = "registry.yaml"


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level YAML must be a mapping")
    return data


def load_repo(spec_dir: str | Path) -> SpecRepoManifest:
    spec_dir = Path(spec_dir)
    meta = _load_yaml(spec_dir / METADATA_FILE)
    contracts: list[ContractSpec] = []
    for path in sorted((spec_dir / "L2").rglob("*.contract.yaml")):
        contracts.append(ContractSpec.model_validate(_load_yaml(path)))
    return SpecRepoManifest(
        spec_version=str(meta.get("spec_version", "0.0.0")),
        migration_stage=meta.get("migration_stage", "M0"),
        contracts=contracts,
    )


def lint_spec_repo(spec_dir: str | Path) -> list[CheckResult]:
    spec_dir = Path(spec_dir)
    results: list[CheckResult] = []

    def add(check_id: str, ok: bool, detail: str = "") -> None:
        results.append(
            CheckResult(id=check_id, status=Verdict.PASS if ok else Verdict.FAIL, detail=detail)
        )

    if not (spec_dir / METADATA_FILE).exists():
        add("spec.metadata", False, f"missing {METADATA_FILE}")
        return results
    try:
        manifest = load_repo(spec_dir)
        add("spec.metadata", True)
    except (ValidationError, ValueError, yaml.YAMLError) as e:
        add("spec.metadata", False, str(e))
        return results

    contract_ids = [c.contract_id for c in manifest.contracts]
    dup = sorted({c for c in contract_ids if contract_ids.count(c) > 1})
    add("spec.contract_id_unique", not dup, f"duplicates: {dup}")

    all_clause_ids: list[str] = []
    problems: list[str] = []
    for c in manifest.contracts:
        for clause in c.clauses:
            all_clause_ids.append(clause.id)
            if not clause.is_verifiable and not clause.advisory:
                problems.append(
                    f"{clause.id}: no mechanical witness but not marked advisory "
                    "(unverifiable clauses may only veto, never admit)"
                )
            if clause.advisory and clause.is_verifiable:
                problems.append(f"{clause.id}: marked advisory but has mechanical witness")
        if c.r_level.value == "R3" and not c.frozen_outputs:
            problems.append(f"{c.contract_id}: R3 contract must declare frozen_outputs (golden outputs)")
        dc_ids = [d.id for d in c.dont_care]
        dc_dup = sorted({d for d in dc_ids if dc_ids.count(d) > 1})
        if dc_dup:
            problems.append(f"{c.contract_id}: duplicate don't-care ids {dc_dup}")
    clause_dup = sorted({c for c in all_clause_ids if all_clause_ids.count(c) > 1})
    if clause_dup:
        problems.append(f"duplicate clause ids across contracts: {clause_dup}")
    add("spec.clause_rules", not problems, "; ".join(problems))

    l1_dir = spec_dir / "L1"
    l1_text = ""
    if l1_dir.exists():
        l1_text = "\n".join(
            p.read_text(encoding="utf-8") for p in l1_dir.rglob("*.md")
        )
    missing_refs: list[str] = []
    for c in manifest.contracts:
        for ref in c.l1_refs:
            if ref and ref not in l1_text:
                missing_refs.append(f"{c.contract_id}:{ref}")
    add("spec.l1_refs_resolvable", not missing_refs, f"unresolvable L1 refs: {missing_refs}")

    witness_count = sum(len(cl.witnesses) for c in manifest.contracts for cl in c.clauses)
    advisory_count = sum(1 for c in manifest.contracts for cl in c.clauses if cl.advisory)
    total = len(all_clause_ids)
    add(
        "spec.witness_coverage",
        total > 0 and advisory_count < total,
        f"clauses={total} advisory={advisory_count} witness_bindings={witness_count}",
    )
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="opc-spec-lint")
    parser.add_argument("--spec-dir", required=True)
    parser.add_argument("--json", action="store_true", help="emit JSON report to stdout")
    args = parser.parse_args(argv)

    results = lint_spec_repo(args.spec_dir)
    failed = [r for r in results if r.status is not Verdict.PASS]
    if args.json:
        print(json.dumps([r.model_dump(mode="json") for r in results], ensure_ascii=False, indent=2))
    else:
        for r in results:
            print(f"[{r.status.value.upper():<12}] {r.id} {r.detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
