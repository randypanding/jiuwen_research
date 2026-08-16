"""SpecDelta: the input contract of a wave (WP1).

A wave consumes the diff between two spec unit versions. Builders see the
delta (plus full spec), verifier sees the delta's witness bindings.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .schema import SpecUnit


@dataclass
class SpecDelta:
    spec_id: str
    old_version: str
    new_version: str
    added_clauses: list[str] = field(default_factory=list)      # clause ids
    removed_clauses: list[str] = field(default_factory=list)
    changed_clauses: list[str] = field(default_factory=list)
    contract_changed: bool = False
    dontcare_added: list[str] = field(default_factory=list)     # dc ids
    dontcare_removed: list[str] = field(default_factory=list)
    r_level: str = "R0"
    artifacts: list[str] = field(default_factory=list)
    witnesses: list[str] = field(default_factory=list)          # as_ref list for verifier
    risk: float = 0.5      # 0..1 uncertainty signal (fanout input)
    novelty: float = 0.5   # 0..1 new-domain signal (fanout input)

    def to_dict(self) -> dict[str, Any]:
        return {
            "spec_id": self.spec_id,
            "old_version": self.old_version,
            "new_version": self.new_version,
            "added_clauses": self.added_clauses,
            "removed_clauses": self.removed_clauses,
            "changed_clauses": self.changed_clauses,
            "contract_changed": self.contract_changed,
            "dontcare_added": self.dontcare_added,
            "dontcare_removed": self.dontcare_removed,
            "r_level": self.r_level,
            "artifacts": self.artifacts,
            "witnesses": self.witnesses,
            "risk": self.risk,
            "novelty": self.novelty,
        }


def compute_delta(old: Optional[SpecUnit], new: SpecUnit, risk: float = 0.5, novelty: float = 0.5) -> SpecDelta:
    old_ids = {c.clause_id: c for c in old.clauses} if old else {}
    new_ids = {c.clause_id: c for c in new.clauses}
    added = [i for i in new_ids if i not in old_ids]
    removed = [i for i in old_ids if i not in new_ids]
    changed = [i for i in new_ids if i in old_ids and old_ids[i].text != new_ids[i].text]
    old_dc = {d.dc_id for d in (old.dont_cares if old else [])}
    new_dc = {d.dc_id for d in new.dont_cares}
    return SpecDelta(
        spec_id=new.spec_id,
        old_version=old.version if old else "0.0.0",
        new_version=new.version,
        added_clauses=sorted(added),
        removed_clauses=sorted(removed),
        changed_clauses=sorted(changed),
        contract_changed=bool(old and old.contract != new.contract) or bool(not old and new.contract),
        dontcare_added=sorted(new_dc - old_dc),
        dontcare_removed=sorted(old_dc - new_dc),
        r_level=new.r_level,
        artifacts=list(new.artifacts),
        witnesses=[c.witness.as_ref() for c in new.machine_clauses() if c.witness],
        risk=min(1.0, max(0.0, risk)),
        novelty=min(1.0, max(0.0, novelty)),
    )
