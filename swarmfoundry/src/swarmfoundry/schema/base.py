from __future__ import annotations

import dataclasses
import json
import re
from typing import Any, Type, TypeVar

from swarmfoundry.schema import SCHEMA_VERSION

T = TypeVar("T")

_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_\-\.]{0,127}$")
_CLAUSE_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+-\d{3,}$")


class SchemaError(ValueError):
    pass


def is_dataclass_instance(obj: Any) -> bool:
    return dataclasses.is_dataclass(obj) and not isinstance(obj, type)


def to_jsonable(obj: Any) -> Any:
    if is_dataclass_instance(obj):
        return {f.name: to_jsonable(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    raise SchemaError(f"not json-serializable: {type(obj)!r}")


def dumps(obj: Any, indent: int | None = None) -> str:
    return json.dumps(to_jsonable(obj), ensure_ascii=False, sort_keys=True, indent=indent)


def require(data: dict, key: str, typ: Type[T], where: str) -> T:
    if key not in data or data[key] is None:
        raise SchemaError(f"{where}: missing required field '{key}'")
    val = data[key]
    if typ is float and isinstance(val, int) and not isinstance(val, bool):
        val = float(val)
    if not isinstance(val, typ):
        raise SchemaError(f"{where}: field '{key}' must be {typ.__name__}, got {type(val).__name__}")
    return val


def optional(data: dict, key: str, typ: Type[T], default: T | None) -> T | None:
    val = data.get(key)
    if val is None:
        return default
    if typ is float and isinstance(val, int) and not isinstance(val, bool):
        val = float(val)
    if not isinstance(val, typ):
        raise SchemaError(f"field '{key}' must be {typ.__name__}, got {type(val).__name__}")
    return val


def require_list(data: dict, key: str, where: str) -> list:
    val = data.get(key)
    if val is None:
        return []
    if not isinstance(val, list):
        raise SchemaError(f"{where}: field '{key}' must be a list")
    return val


def check_id(value: str, where: str) -> str:
    if not isinstance(value, str) or not _ID_RE.match(value):
        raise SchemaError(f"{where}: invalid identifier {value!r}")
    return value


def check_clause_id(value: str, where: str) -> str:
    if not isinstance(value, str) or not _CLAUSE_RE.match(value):
        raise SchemaError(
            f"{where}: clause id {value!r} must match DOMAIN-SECTION-NNN (e.g. AUTH-SESSION-001)"
        )
    return value


def check_schema_version(data: dict, where: str) -> str:
    ver = data.get("schema_version")
    if ver != SCHEMA_VERSION:
        raise SchemaError(f"{where}: unsupported schema_version {ver!r}, expected {SCHEMA_VERSION}")
    return ver
