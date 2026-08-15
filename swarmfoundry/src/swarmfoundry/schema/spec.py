from __future__ import annotations

import dataclasses
from typing import Any

from swarmfoundry.schema import SCHEMA_VERSION
from swarmfoundry.schema.base import (
    SchemaError,
    check_clause_id,
    check_id,
    check_schema_version,
    optional,
    require,
    require_list,
)

LEVEL_L1 = "L1"
LEVEL_L2 = "L2"
LEVEL_L3 = "L3"
CLAUSE_LEVELS = (LEVEL_L1, LEVEL_L2, LEVEL_L3)

R0 = "R0"
R1 = "R1"
R2 = "R2"
R3 = "R3"
R_LEVELS = (R0, R1, R2, R3)

WITNESS_HARD_GATE = "hard_gate"
WITNESS_HOLDOUT = "holdout_scenario"
WITNESS_JUDGE_RUBRIC = "judge_rubric"
WITNESS_KINDS = (WITNESS_HARD_GATE, WITNESS_HOLDOUT, WITNESS_JUDGE_RUBRIC)
MECHANICAL_WITNESSES = (WITNESS_HARD_GATE, WITNESS_HOLDOUT)

CLAUSE_ACTIVE = "active"
CLAUSE_ADVISORY = "advisory"
CLAUSE_UNVERIFIABLE = "unverifiable"
CLAUSE_STATUSES = (CLAUSE_ACTIVE, CLAUSE_ADVISORY, CLAUSE_UNVERIFIABLE)

DC_OUTPUT_FREEDOM = "output_freedom"
DC_UNREACHABLE_STATE = "unreachable_state"
DC_IGNORABLE_OUTPUT = "ignorable_output"
DONT_CARE_KINDS = (DC_OUTPUT_FREEDOM, DC_UNREACHABLE_STATE, DC_IGNORABLE_OUTPUT)


@dataclasses.dataclass(frozen=True)
class WitnessBinding:
    kind: str
    ref: str
    note: str = ""

    def to_dict(self) -> dict:
        return {"kind": self.kind, "ref": self.ref, "note": self.note}

    @classmethod
    def from_dict(cls, data: dict, where: str) -> "WitnessBinding":
        kind = require(data, "kind", str, where)
        if kind not in WITNESS_KINDS:
            raise SchemaError(f"{where}: witness kind must be one of {WITNESS_KINDS}, got {kind!r}")
        return cls(kind=kind, ref=check_id(require(data, "ref", str, where), where), note=data.get("note", ""))


@dataclasses.dataclass(frozen=True)
class Clause:
    id: str
    level: str
    statement: str
    r_level: str = R0
    witnesses: tuple[WitnessBinding, ...] = ()
    status: str = CLAUSE_ACTIVE

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "level": self.level,
            "statement": self.statement,
            "r_level": self.r_level,
            "witnesses": [w.to_dict() for w in self.witnesses],
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict, where: str) -> "Clause":
        cid = check_clause_id(require(data, "id", str, where), where)
        level = require(data, "level", str, where)
        if level not in CLAUSE_LEVELS:
            raise SchemaError(f"{where}: level must be one of {CLAUSE_LEVELS}")
        statement = require(data, "statement", str, where).strip()
        if not statement:
            raise SchemaError(f"{where}: clause {cid} has empty statement")
        r_level = data.get("r_level", R0)
        if r_level not in R_LEVELS:
            raise SchemaError(f"{where}: r_level must be one of {R_LEVELS}")
        witnesses = tuple(
            WitnessBinding.from_dict(w, f"{where}.{cid}.witnesses[{i}]")
            for i, w in enumerate(require_list(data, "witnesses", where))
        )
        status = data.get("status", CLAUSE_ACTIVE)
        if status not in CLAUSE_STATUSES:
            raise SchemaError(f"{where}: status must be one of {CLAUSE_STATUSES}")
        return cls(id=cid, level=level, statement=statement, r_level=r_level, witnesses=witnesses, status=status)

    def has_mechanical_witness(self) -> bool:
        return any(w.kind in MECHANICAL_WITNESSES for w in self.witnesses)

    def effective_status(self) -> str:
        if self.level == LEVEL_L3:
            return self.status
        if self.has_mechanical_witness():
            return self.status if self.status != CLAUSE_UNVERIFIABLE else CLAUSE_UNVERIFIABLE
        return CLAUSE_UNVERIFIABLE


@dataclasses.dataclass(frozen=True)
class DontCareEntry:
    id: str
    clause_id: str
    kind: str
    description: str
    registered_by: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "clause_id": self.clause_id,
            "kind": self.kind,
            "description": self.description,
            "registered_by": self.registered_by,
        }

    @classmethod
    def from_dict(cls, data: dict, where: str) -> "DontCareEntry":
        kind = require(data, "kind", str, where)
        if kind not in DONT_CARE_KINDS:
            raise SchemaError(f"{where}: dont-care kind must be one of {DONT_CARE_KINDS}")
        return cls(
            id=check_id(require(data, "id", str, where), where),
            clause_id=check_clause_id(require(data, "clause_id", str, where), where),
            kind=kind,
            description=require(data, "description", str, where),
            registered_by=data.get("registered_by", ""),
        )


@dataclasses.dataclass(frozen=True)
class SpecDomain:
    domain: str
    version: int
    intent: str
    clauses: tuple[Clause, ...]
    dontcares: tuple[DontCareEntry, ...] = ()
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "domain": self.domain,
            "version": self.version,
            "intent": self.intent,
            "clauses": [c.to_dict() for c in self.clauses],
            "dontcares": [d.to_dict() for d in self.dontcares],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SpecDomain":
        where = "SpecDomain"
        check_schema_version(data, where)
        domain = check_id(require(data, "domain", str, where), where)
        clauses = tuple(
            Clause.from_dict(c, f"{where}.{domain}.clauses[{i}]")
            for i, c in enumerate(require_list(data, "clauses", where))
        )
        dontcares = tuple(
            DontCareEntry.from_dict(d, f"{where}.{domain}.dontcares[{i}]")
            for i, d in enumerate(require_list(data, "dontcares", where))
        )
        return cls(
            domain=domain,
            version=require(data, "version", int, where),
            intent=require(data, "intent", str, where).strip(),
            clauses=clauses,
            dontcares=dontcares,
        )

    def clause(self, clause_id: str) -> Clause:
        for c in self.clauses:
            if c.id == clause_id:
                return c
        raise SchemaError(f"clause {clause_id} not found in domain {self.domain}")

    def validate(self) -> list[str]:
        problems: list[str] = []
        seen: set[str] = set()
        for c in self.clauses:
            if c.id in seen:
                problems.append(f"duplicate clause id {c.id}")
            seen.add(c.id)
        clause_ids = set(seen)
        for d in self.dontcares:
            if d.clause_id not in clause_ids:
                problems.append(f"dont-care {d.id} references unknown clause {d.clause_id}")
        for c in self.clauses:
            if c.level in (LEVEL_L1, LEVEL_L2) and not c.has_mechanical_witness():
                if not any(w.kind == WITNESS_JUDGE_RUBRIC for w in c.witnesses):
                    problems.append(
                        f"clause {c.id} has no witness at all; it cannot even serve as advisory"
                    )
        return problems


@dataclasses.dataclass(frozen=True)
class ArtifactEntry:
    path: str
    r_level: str
    clauses: tuple[str, ...]
    golden_ref: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "r_level": self.r_level,
            "clauses": list(self.clauses),
            "golden_ref": self.golden_ref,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict, where: str) -> "ArtifactEntry":
        r_level = require(data, "r_level", str, where)
        if r_level not in R_LEVELS:
            raise SchemaError(f"{where}: r_level must be one of {R_LEVELS}")
        golden_ref = data.get("golden_ref", "")
        if r_level == R3 and not golden_ref:
            raise SchemaError(f"{where}: R3 artifact must declare golden_ref (frozen golden output)")
        clauses = tuple(check_clause_id(c, where) for c in require_list(data, "clauses", where))
        return cls(
            path=require(data, "path", str, where),
            r_level=r_level,
            clauses=clauses,
            golden_ref=golden_ref,
            notes=data.get("notes", ""),
        )


@dataclasses.dataclass(frozen=True)
class RRegistry:
    artifacts: tuple[ArtifactEntry, ...]
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "artifacts": [a.to_dict() for a in self.artifacts],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RRegistry":
        where = "RRegistry"
        check_schema_version(data, where)
        artifacts = tuple(
            ArtifactEntry.from_dict(a, f"{where}.artifacts[{i}]")
            for i, a in enumerate(require_list(data, "artifacts", where))
        )
        paths = [a.path for a in artifacts]
        if len(paths) != len(set(paths)):
            raise SchemaError(f"{where}: duplicate artifact paths")
        return cls(artifacts=artifacts)

    def r_level_of(self, relpath: str) -> str | None:
        best: ArtifactEntry | None = None
        for a in self.artifacts:
            if relpath.startswith(a.path) and (best is None or len(a.path) > len(best.path)):
                best = a
        return best.r_level if best else None


def load_json_dict(path_or_text: str | dict, *, loader) -> dict[str, Any]:
    if isinstance(path_or_text, dict):
        return path_or_text
    return loader(path_or_text)
