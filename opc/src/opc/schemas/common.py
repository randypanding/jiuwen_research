from __future__ import annotations

import hashlib
import json
import re
from enum import Enum

from pydantic import BaseModel, ConfigDict


class Verdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"

    @property
    def admits(self) -> bool:
        return self is Verdict.PASS


class RLevel(str, Enum):
    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"

    @property
    def fanout_allowed(self) -> bool:
        return self in (RLevel.R0, RLevel.R1)

    @property
    def regeneration_allowed(self) -> bool:
        return self is RLevel.R0

    @property
    def requires_human_diff(self) -> bool:
        return self in (RLevel.R2, RLevel.R3)


CLAUSE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*-\d{3,}$")
CONTENT_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False, str_strip_whitespace=True)


def canonical_json_bytes(obj: BaseModel) -> bytes:
    return json.dumps(
        obj.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def content_hash(obj: BaseModel) -> str:
    return sha256_hex(canonical_json_bytes(obj))


def validate_clause_id(value: str) -> str:
    if not CLAUSE_ID_RE.match(value):
        raise ValueError(f"invalid clause id: {value!r} (must match {CLAUSE_ID_RE.pattern})")
    return value
