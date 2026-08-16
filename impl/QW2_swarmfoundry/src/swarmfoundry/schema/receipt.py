from __future__ import annotations

import dataclasses
import hashlib

from swarmfoundry.schema import SCHEMA_VERSION
from swarmfoundry.schema.base import (
    SchemaError,
    check_id,
    check_schema_version,
    optional,
    require,
    require_list,
)
from swarmfoundry.schema.gates import AdmissionDecision, GateResult
from swarmfoundry.schema.spec import R_LEVELS


@dataclasses.dataclass(frozen=True)
class CostRecord:
    tokens_in: int = 0
    tokens_out: int = 0
    spend_units: float = 0.0

    def to_dict(self) -> dict:
        return {"tokens_in": self.tokens_in, "tokens_out": self.tokens_out, "spend_units": self.spend_units}

    @classmethod
    def from_dict(cls, data: dict) -> "CostRecord":
        return cls(
            tokens_in=int(data.get("tokens_in", 0)),
            tokens_out=int(data.get("tokens_out", 0)),
            spend_units=float(data.get("spend_units", 0.0)),
        )


@dataclasses.dataclass(frozen=True)
class DiscardedMeasurement:
    instance_id: str
    conclusion: str

    def to_dict(self) -> dict:
        return {"instance_id": self.instance_id, "conclusion": self.conclusion}

    @classmethod
    def from_dict(cls, data: dict) -> "DiscardedMeasurement":
        return cls(
            instance_id=require(data, "instance_id", str, "DiscardedMeasurement"),
            conclusion=require(data, "conclusion", str, "DiscardedMeasurement"),
        )


@dataclasses.dataclass(frozen=True)
class EvidenceReceipt:
    receipt_id: str
    wave_id: str
    spec_delta_id: str
    instance_id: str
    r_level: str
    admission: AdmissionDecision
    diff_conclusion: str
    drift_clean: bool
    cost: CostRecord
    discarded: tuple[DiscardedMeasurement, ...] = ()
    notes: str = ""
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "wave_id": self.wave_id,
            "spec_delta_id": self.spec_delta_id,
            "instance_id": self.instance_id,
            "r_level": self.r_level,
            "admission": self.admission.to_dict(),
            "diff_conclusion": self.diff_conclusion,
            "drift_clean": self.drift_clean,
            "cost": self.cost.to_dict(),
            "discarded": [d.to_dict() for d in self.discarded],
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EvidenceReceipt":
        where = "EvidenceReceipt"
        check_schema_version(data, where)
        r_level = require(data, "r_level", str, where)
        if r_level not in R_LEVELS:
            raise SchemaError(f"{where}: r_level must be one of {R_LEVELS}")
        return cls(
            receipt_id=require(data, "receipt_id", str, where),
            wave_id=require(data, "wave_id", str, where),
            spec_delta_id=require(data, "spec_delta_id", str, where),
            instance_id=require(data, "instance_id", str, where),
            r_level=r_level,
            admission=AdmissionDecision.from_dict(require(data, "admission", dict, where)),
            diff_conclusion=require(data, "diff_conclusion", str, where),
            drift_clean=require(data, "drift_clean", bool, where),
            cost=CostRecord.from_dict(data.get("cost", {})),
            discarded=tuple(DiscardedMeasurement.from_dict(d) for d in require_list(data, "discarded", where)),
            notes=data.get("notes", ""),
        )

    def content_hash(self) -> str:
        d = self.to_dict()
        d.pop("receipt_id", None)
        import json

        return hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
