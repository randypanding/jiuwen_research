from __future__ import annotations

import dataclasses

from swarmfoundry.schema import SCHEMA_VERSION
from swarmfoundry.schema.base import (
    SchemaError,
    check_schema_version,
    require,
    require_list,
)

EQUIVALENT = "equivalent"
DIVERGENT = "divergent"
INCONCLUSIVE = "inconclusive"
EQUIVALENCE_VALUES = (EQUIVALENT, DIVERGENT, INCONCLUSIVE)


@dataclasses.dataclass(frozen=True)
class Divergence:
    input_id: str
    path: str
    a_value: str
    b_value: str

    def to_dict(self) -> dict:
        return {"input_id": self.input_id, "path": self.path, "a_value": self.a_value, "b_value": self.b_value}

    @classmethod
    def from_dict(cls, data: dict) -> "Divergence":
        where = "Divergence"
        return cls(
            input_id=require(data, "input_id", str, where),
            path=require(data, "path", str, where),
            a_value=str(data.get("a_value", "")),
            b_value=str(data.get("b_value", "")),
        )


@dataclasses.dataclass(frozen=True)
class DiffReport:
    instance_a: str
    instance_b: str
    inputs_run: int
    equivalence: str
    divergences: tuple[Divergence, ...] = ()
    note: str = ""
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "instance_a": self.instance_a,
            "instance_b": self.instance_b,
            "inputs_run": self.inputs_run,
            "equivalence": self.equivalence,
            "divergences": [d.to_dict() for d in self.divergences],
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DiffReport":
        where = "DiffReport"
        check_schema_version(data, where)
        equivalence = require(data, "equivalence", str, where)
        if equivalence not in EQUIVALENCE_VALUES:
            raise SchemaError(f"{where}: equivalence must be one of {EQUIVALENCE_VALUES}")
        return cls(
            instance_a=require(data, "instance_a", str, where),
            instance_b=require(data, "instance_b", str, where),
            inputs_run=require(data, "inputs_run", int, where),
            equivalence=equivalence,
            divergences=tuple(Divergence.from_dict(d) for d in require_list(data, "divergences", where)),
            note=data.get("note", ""),
        )
