from __future__ import annotations

import dataclasses

from swarmfoundry.schema import SCHEMA_VERSION
from swarmfoundry.schema.base import (
    SchemaError,
    check_schema_version,
    require,
    require_list,
)

SYMBOL_FUNCTION = "function"
SYMBOL_CLASS = "class"
SYMBOL_METHOD = "method"
SYMBOL_CONSTANT = "constant"
SYMBOL_SCHEMA_FILE = "schema_file"
SYMBOL_KINDS = (SYMBOL_FUNCTION, SYMBOL_CLASS, SYMBOL_METHOD, SYMBOL_CONSTANT, SYMBOL_SCHEMA_FILE)


@dataclasses.dataclass(frozen=True)
class SymbolSurface:
    name: str
    kind: str
    signature: str = ""
    detail: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "kind": self.kind, "signature": self.signature, "detail": self.detail}

    @classmethod
    def from_dict(cls, data: dict) -> "SymbolSurface":
        where = "SymbolSurface"
        kind = require(data, "kind", str, where)
        if kind not in SYMBOL_KINDS:
            raise SchemaError(f"{where}: kind must be one of {SYMBOL_KINDS}")
        return cls(
            name=require(data, "name", str, where),
            kind=kind,
            signature=data.get("signature", ""),
            detail=data.get("detail", ""),
        )


@dataclasses.dataclass(frozen=True)
class ContractSurface:
    module: str
    symbols: tuple[SymbolSurface, ...]
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "module": self.module,
            "symbols": [s.to_dict() for s in self.symbols],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ContractSurface":
        where = "ContractSurface"
        check_schema_version(data, where)
        symbols = tuple(SymbolSurface.from_dict(s) for s in require_list(data, "symbols", where))
        return cls(module=require(data, "module", str, where), symbols=symbols)

    def by_key(self) -> dict[tuple[str, str], SymbolSurface]:
        return {(s.kind, s.name): s for s in self.symbols}


CHANGE_ADDED = "added"
CHANGE_REMOVED = "removed"
CHANGE_MODIFIED = "modified"
SEVERITY_BREAKING = "breaking"
SEVERITY_NON_BREAKING = "non_breaking"


@dataclasses.dataclass(frozen=True)
class SurfaceChange:
    name: str
    kind: str
    change: str
    severity: str
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "change": self.change,
            "severity": self.severity,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SurfaceChange":
        where = "SurfaceChange"
        change = require(data, "change", str, where)
        if change not in (CHANGE_ADDED, CHANGE_REMOVED, CHANGE_MODIFIED):
            raise SchemaError(f"{where}: change must be added/removed/modified")
        severity = require(data, "severity", str, where)
        if severity not in (SEVERITY_BREAKING, SEVERITY_NON_BREAKING):
            raise SchemaError(f"{where}: severity must be breaking/non_breaking")
        return cls(
            name=require(data, "name", str, where),
            kind=require(data, "kind", str, where),
            change=change,
            severity=severity,
            detail=data.get("detail", ""),
        )


@dataclasses.dataclass(frozen=True)
class SurfaceDiff:
    module: str
    changes: tuple[SurfaceChange, ...]
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "module": self.module,
            "changes": [c.to_dict() for c in self.changes],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SurfaceDiff":
        where = "SurfaceDiff"
        check_schema_version(data, where)
        return cls(
            module=require(data, "module", str, where),
            changes=tuple(SurfaceChange.from_dict(c) for c in require_list(data, "changes", where)),
        )

    def breaking(self) -> list[SurfaceChange]:
        return [c for c in self.changes if c.severity == SEVERITY_BREAKING]
