from __future__ import annotations

import hashlib
import json
from pathlib import Path

from swarmdev.contracts import L2Clause, SpecDoc


def hash_clause(clause: L2Clause) -> str:
    payload = {
        "title": clause.title,
        "assumes": sorted(clause.assumes),
        "guarantees": sorted(clause.guarantees),
        "invariants": sorted(clause.invariants),
    }
    blob = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


class ContractHashStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> dict:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def record(self, spec: SpecDoc) -> None:
        data = self.load()
        data[spec.spec_id] = {c.clause_id: hash_clause(c) for c in spec.l2_clauses}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, sort_keys=True, indent=2)

    def diff(self, spec: SpecDoc) -> list[tuple[str, str]]:
        stored = self.load().get(spec.spec_id)
        if stored is None:
            return []
        current = {c.clause_id: hash_clause(c) for c in spec.l2_clauses}
        changes: list[tuple[str, str]] = []
        for clause_id in sorted(set(stored) | set(current)):
            if clause_id not in stored:
                changes.append((clause_id, "added"))
            elif clause_id not in current:
                changes.append((clause_id, "removed"))
            elif stored[clause_id] != current[clause_id]:
                changes.append((clause_id, "changed"))
        return changes
