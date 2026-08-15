from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from opc.schemas.common import (
    BaseSchema,
    RLevel,
    validate_clause_id,
)


class WitnessBinding(BaseSchema):
    clause_id: str
    gate: Literal["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "S"]
    target: str = Field(description="gate-specific witness target, e.g. test node id or scenario id")

    @field_validator("clause_id")
    @classmethod
    def _clause_id(cls, v: str) -> str:
        return validate_clause_id(v)

    @field_validator("target")
    @classmethod
    def _target(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("witness target must be non-empty")
        return v


class DontCareEntry(BaseSchema):
    id: str
    scope: str = Field(description="dotted path the freedom applies to, e.g. receipt.latency")
    kind: Literal["unspecified", "undefined"] = "unspecified"
    note: str = ""

    @field_validator("id")
    @classmethod
    def _id(cls, v: str) -> str:
        if not v.startswith("DC-"):
            raise ValueError("don't-care id must start with 'DC-'")
        return v


class InterfaceItem(BaseSchema):
    symbol: str
    kind: Literal["function", "class", "method", "cli", "event", "schema"]
    signature: str = ""
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    invariants: list[str] = Field(default_factory=list)


class Clause(BaseSchema):
    id: str
    layer: Literal["L1", "L2"]
    text: str
    witnesses: list[WitnessBinding] = Field(default_factory=list)
    advisory: bool = Field(
        default=False,
        description="true when no mechanical witness exists; advisory clauses may only veto via S, never admit",
    )

    @field_validator("id")
    @classmethod
    def _id(cls, v: str) -> str:
        return validate_clause_id(v)

    @property
    def is_verifiable(self) -> bool:
        return any(w.gate != "S" for w in self.witnesses)


class ContractSpec(BaseSchema):
    """L2 development contract: the machine-owned truth layer humans only diff-review."""

    contract_id: str
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    r_level: RLevel
    domain: str
    l1_refs: list[str] = Field(default_factory=list)
    interface_surface: list[InterfaceItem] = Field(default_factory=list)
    clauses: list[Clause] = Field(default_factory=list)
    dont_care: list[DontCareEntry] = Field(default_factory=list)
    frozen_outputs: list[str] = Field(
        default_factory=list,
        description="R3 golden-output artifact paths locked against regeneration",
    )

    @field_validator("contract_id")
    @classmethod
    def _contract_id(cls, v: str) -> str:
        if not v.startswith("CTR-"):
            raise ValueError("contract_id must start with 'CTR-'")
        return v

    def clause_ids(self) -> set[str]:
        return {c.id for c in self.clauses}

    def unverifiable_clauses(self) -> list[Clause]:
        return [c for c in self.clauses if not c.is_verifiable]


class SpecRepoManifest(BaseSchema):
    """registry.yaml at the spec repo root: R-level registry + global witness index."""

    spec_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    contracts: list[ContractSpec]
    migration_stage: Literal["M0", "M1", "M2", "M3"] = "M0"

    def contract_by_id(self, contract_id: str) -> ContractSpec | None:
        for c in self.contracts:
            if c.contract_id == contract_id:
                return c
        return None

    def r_level_of(self, contract_id: str) -> RLevel | None:
        c = self.contract_by_id(contract_id)
        return c.r_level if c else None
