"""Spec unit schema: the single source of truth (PDR-001 layer 1).

A spec unit is a `spec.md` file with:
  - YAML frontmatter: spec_id, version, r_level, depends, artifacts
  - Sections `## L1`, `## L2`, `## L3`, `## DONT-CARE`
  - Fenced blocks tagged `clause`, `contract`, `invariant`, `dontcare`

Machine model below is the authority; the parser produces it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

LEVELS = ("L1", "L2", "L3")


@dataclass
class Witness:
    """Mechanical witness binding for a clause (gate id or holdout set id).

    Constitution #3: a clause without a mechanical witness may only veto
    (advisory), never clear. The linter marks such clauses unverifiable.
    """

    kind: str  # "gate" | "holdout"
    ref: str   # e.g. "h2:unit-tests-demo" or "holdout:adder-basic"

    def as_ref(self) -> str:
        return f"{self.kind}:{self.ref}"


@dataclass
class Clause:
    clause_id: str
    level: str                      # L1 | L2 | L3
    text: str
    witness: Optional[Witness] = None
    holdout_set: Optional[str] = None  # convenience: holdout scenario set id
    advisory_only: bool = field(default=False)  # set by linter when no witness

    def to_dict(self) -> dict[str, Any]:
        return {
            "clause_id": self.clause_id,
            "level": self.level,
            "text": self.text,
            "witness": self.witness.as_ref() if self.witness else None,
            "holdout_set": self.holdout_set,
            "advisory_only": self.advisory_only,
        }


@dataclass
class Invariant:
    inv_id: str
    expr: str          # python expression over scenario params, e.g. "add(a,b)==add(b,a)"
    scope: str         # gate id that executes it (typically h2)

    def to_dict(self) -> dict[str, Any]:
        return {"inv_id": self.inv_id, "expr": self.expr, "scope": self.scope}


@dataclass
class DontCare:
    dc_id: str
    kind: str          # unspecified | undefined | unreachable | ignorable_output
    region: str        # human description of the freedom region

    def to_dict(self) -> dict[str, Any]:
        return {"dc_id": self.dc_id, "kind": self.kind, "region": self.region}


DC_KINDS = ("unspecified", "undefined", "unreachable", "ignorable_output")


@dataclass
class SpecUnit:
    spec_id: str
    version: str                   # SemVer string
    r_level: str                   # R0..R3
    depends: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)  # path patterns owned by unit
    prose: dict[str, str] = field(default_factory=dict)  # level -> free text
    clauses: list[Clause] = field(default_factory=list)
    contract: dict[str, Any] = field(default_factory=dict)  # machine contract block
    invariants: list[Invariant] = field(default_factory=list)
    dont_cares: list[DontCare] = field(default_factory=list)
    source_path: Optional[str] = None

    def clauses_by_level(self, level: str) -> list[Clause]:
        return [c for c in self.clauses if c.level == level]

    def machine_clauses(self) -> list[Clause]:
        """L1/L2 clauses only (L3 is machine-owned prose)."""
        return [c for c in self.clauses if c.level in ("L1", "L2")]

    def clause(self, clause_id: str) -> Optional[Clause]:
        for c in self.clauses:
            if c.clause_id == clause_id:
                return c
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "spec_id": self.spec_id,
            "version": self.version,
            "r_level": self.r_level,
            "depends": list(self.depends),
            "artifacts": list(self.artifacts),
            "clauses": [c.to_dict() for c in self.clauses],
            "contract": self.contract,
            "invariants": [i.to_dict() for i in self.invariants],
            "dont_cares": [d.to_dict() for d in self.dont_cares],
        }


@dataclass
class LintError:
    code: str
    message: str
    location: str = ""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"[{self.code}] {self.location}: {self.message}"
