from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field

from swarmdev.contracts import SpecDoc
from swarmdev.drift.contract_hash import ContractHashStore
from swarmdev.drift.trace_tags import scan_dir


class DriftEvent(BaseModel):
    kind: str
    severity: Literal["hard", "advisory"]
    detail: str


class DriftReport(BaseModel):
    events: list[DriftEvent] = Field(default_factory=list)
    clean: bool = True


class DriftDetector:
    def __init__(self, hash_store: Optional[ContractHashStore] = None):
        self.hash_store = hash_store

    def detect(self, spec: SpecDoc, code_root: Path) -> DriftReport:
        events: list[DriftEvent] = []
        tag_files = scan_dir(Path(code_root))
        tags: dict[str, set[str]] = {}
        for rel, ids in tag_files.items():
            for tag in ids:
                tags.setdefault(tag, set()).add(rel)

        known = {c.clause_id for c in spec.l2_clauses}
        for tag in sorted(tags):
            if tag not in known:
                files = ", ".join(sorted(tags[tag]))
                events.append(DriftEvent(
                    kind="unknown_tag_reference", severity="hard",
                    detail=f"@REQ-{tag}@ in {files} references clause missing from {spec.spec_id}",
                ))

        if self.hash_store is not None:
            for clause_id, op in self.hash_store.diff(spec):
                events.append(DriftEvent(
                    kind="clause_hash_changed", severity="hard",
                    detail=f"clause {clause_id} {op} relative to recorded contract hash",
                ))

        for clause in spec.l2_clauses:
            if clause.witnesses and clause.clause_id not in tags:
                events.append(DriftEvent(
                    kind="missing_implementation_tag", severity="advisory",
                    detail=(f"clause {clause.clause_id} has witness bindings but no "
                            f"@REQ-{clause.clause_id}@ tag under code root"),
                ))

        clean = not any(e.severity == "hard" for e in events)
        return DriftReport(events=events, clean=clean)
