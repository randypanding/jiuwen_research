from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class Role(str, Enum):
    LEADER = "leader"
    ARCHITECT = "architect"
    BUILDER = "builder"
    VERIFIER = "verifier"
    SPEC_MODERATOR = "spec_moderator"
    SPEC_STEWARD = "spec_steward"
    RECONCILER = "reconciler"
    CARTOGRAPHER = "cartographer"
    CRITIC = "critic"
    REFACTOR = "refactor"
    MODERATOR = "moderator"
    DEEP_AGENT = "deep_agent"
    HUMAN = "human"
    SYSTEM = "system"


GENERATOR_ROLES = frozenset({Role.BUILDER})
JUDGE_ROLES = frozenset({Role.VERIFIER, Role.ARCHITECT})
SPEC_ROLES = frozenset({Role.SPEC_MODERATOR, Role.SPEC_STEWARD})


class RLevel(str, Enum):
    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"


class SpecLevel(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class Verdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"
    ERROR = "error"


class Confidentiality(str, Enum):
    PUBLIC = "public"
    HOLDOUT = "holdout"
    JUDGE_INTERNAL = "judge_internal"
    MEMORY_RESTRICTED = "memory_restricted"


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)
    contract_name: str = ""
    contract_version: int = 1

    def canonical_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


class ContractEnvelope(ContractModel):
    contract_name: str = "ContractEnvelope"
    envelope_id: str = Field(default_factory=lambda: new_id("env"))
    schema_name: str
    schema_version: int = 1
    producer_role: Role
    consumer_role: Optional[Role] = None
    topic: str = "default"
    session_scope: str = "default_context_id"
    confidentiality: Confidentiality = Confidentiality.PUBLIC
    ts: str = Field(default_factory=utc_now_iso)
    payload: dict[str, Any] = Field(default_factory=dict)
    payload_sha256: str = ""

    def seal(self) -> "ContractEnvelope":
        body = json.dumps(self.payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        self.payload_sha256 = hashlib.sha256(body.encode("utf-8")).hexdigest()
        return self

    def verify_seal(self) -> bool:
        body = json.dumps(self.payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(body.encode("utf-8")).hexdigest() == self.payload_sha256
