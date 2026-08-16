from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Optional

from pydantic import Field

from .base import ContractModel, RLevel, SpecLevel, new_id


class DontCareKind(str, Enum):
    OUTPUT_FREEDOM = "output_freedom"
    UNREACHABLE_STATE = "unreachable_state"
    IGNORABLE_OUTPUT = "ignorable_output"


class DontCareDeclaration(ContractModel):
    contract_name: str = "DontCareDeclaration"
    dont_care_id: str = Field(default_factory=lambda: new_id("dc"))
    kind: DontCareKind
    scope: str
    description: str
    registered_by: str = "spec_moderator"
    ts: str = ""


class MachineContract(ContractModel):
    contract_name: str = "MachineContract"
    pre: list[str] = Field(default_factory=list)
    post: list[str] = Field(default_factory=list)
    invariants: list[str] = Field(default_factory=list)
    assume: list[str] = Field(default_factory=list)
    guarantee: list[str] = Field(default_factory=list)


class WitnessKind(str, Enum):
    MECHANICAL = "mechanical"
    HOLDOUT = "holdout"


class ClauseStatus(str, Enum):
    ACTIVE = "active"
    ADVISORY = "advisory"
    UNVERIFIABLE = "unverifiable"
    DEPRECATED = "deprecated"


def canonical_clause_digest(clause_id: str, level: SpecLevel, contract_body: Optional[MachineContract], dont_care: list[DontCareDeclaration]) -> str:
    body = contract_body.model_dump(mode="json") if contract_body else None
    dc = sorted([d.model_dump(mode="json") for d in dont_care], key=lambda x: json.dumps(x, sort_keys=True))
    canon = json.dumps({"clause_id": clause_id, "level": level.value, "contract": body, "dont_care": dc}, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


class SpecClause(ContractModel):
    contract_name: str = "SpecClause"
    clause_id: str
    level: SpecLevel
    r_level: RLevel = RLevel.R0
    title: str = ""
    text: str
    contract_body: Optional[MachineContract] = None
    dont_care: list[DontCareDeclaration] = Field(default_factory=list)
    witness_kind: WitnessKind = WitnessKind.MECHANICAL
    witness_refs: list[str] = Field(default_factory=list)
    status: ClauseStatus = ClauseStatus.ACTIVE
    version: int = 1

    def digest(self) -> str:
        return canonical_clause_digest(self.clause_id, self.level, self.contract_body, self.dont_care)

    def anchor(self) -> str:
        return f"@spec {self.clause_id} #{self.digest()[:16]}"

    def is_verifiable(self) -> bool:
        return bool(self.witness_refs) or self.witness_kind == WitnessKind.HOLDOUT


class SpecDoc(ContractModel):
    contract_name: str = "SpecDoc"
    spec_id: str
    spec_version: str = "0.1.0"
    clauses: list[SpecClause] = Field(default_factory=list)

    def clause_map(self) -> dict[str, SpecClause]:
        return {c.clause_id: c for c in self.clauses}

    def unverifiable_clauses(self) -> list[SpecClause]:
        return [c for c in self.clauses if not c.is_verifiable() and c.status == ClauseStatus.ACTIVE]


class ChangeOp(str, Enum):
    ADD = "add"
    MODIFY = "modify"
    REMOVE = "remove"


class BCClass(str, Enum):
    BC = "BC"
    NBC = "NBC"


class ClauseChange(ContractModel):
    contract_name: str = "ClauseChange"
    clause_id: str
    op: ChangeOp
    bc_class: BCClass = BCClass.BC
    old_digest: Optional[str] = None
    new_digest: Optional[str] = None
    rationale: str = ""


class SpecDelta(ContractModel):
    contract_name: str = "SpecDelta"
    delta_id: str = Field(default_factory=lambda: new_id("sd"))
    spec_id: str
    base_spec_version: str
    new_spec_version: str
    changes: list[ClauseChange] = Field(default_factory=list)
    author: str = "architect"

    @property
    def requires_human_approval(self) -> bool:
        return any(c.bc_class == BCClass.NBC for c in self.changes)

    @property
    def affected_clauses(self) -> list[str]:
        return [c.clause_id for c in self.changes]
