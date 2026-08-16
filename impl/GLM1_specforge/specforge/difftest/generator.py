"""Deterministic schema-driven input generation (D10).

Seeds are ALWAYS provided by the platform (orchestrator), never chosen by
builders (information asymmetry: PRNG seed is a zero-modification channel).
Schema: recursive type descriptors, e.g.
    {"a": {"type": "int", "min": -100, "max": 100},
     "b": {"type": "int", "min": -100, "max": 100},
     "name": {"type": "str", "max_len": 8},
     "items": {"type": "list", "item": {"type": "int"}, "max_len": 3}}
"""
from __future__ import annotations

import random
import string
from typing import Any

BOUNDARY_INTS = [0, 1, -1, 2, -2, 100, -100, 10**9, -(10**9)]


class InputSchemaError(ValueError):
    pass


def generate_inputs(schema: dict[str, Any], seed: int, n: int) -> list[dict[str, Any]]:
    """Generate n input objects.

    Schema forms:
      - field record:  {"a": {"type": "int"}, "b": {"type": "str"}}  (most common)
      - single descriptor: {"type": "dict", "properties": {...}}
    """
    if seed is None:
        raise InputSchemaError("seed must be provided by the platform (constitution #17)")
    if not isinstance(schema, dict):
        raise InputSchemaError(f"schema must be a dict, got {type(schema)!r}")
    if "type" not in schema:
        schema = {"type": "dict", "properties": schema}
    rng = random.Random(seed)
    out: list[dict[str, Any]] = []
    for _ in range(n):
        out.append(_gen(schema, rng, boundary=bool(rng.random() < 0.3)))
    return out


def _gen(desc: Any, rng: random.Random, boundary: bool) -> Any:
    if isinstance(desc, list) and desc and isinstance(desc[0], dict):
        return _gen(rng.choice(desc), rng, boundary)  # union: pick one variant
    if not isinstance(desc, dict) or "type" not in desc:
        raise InputSchemaError(f"invalid type descriptor: {desc!r}")
    t = desc["type"]
    if t == "int":
        lo, hi = int(desc.get("min", -100)), int(desc.get("max", 100))
        if boundary and rng.random() < 0.6:
            return rng.choice([v for v in BOUNDARY_INTS if lo <= v <= hi] or [lo, hi])
        return rng.randint(lo, hi)
    if t == "float":
        lo, hi = float(desc.get("min", -1e3)), float(desc.get("max", 1e3))
        if boundary:
            return rng.choice([0.0, lo, hi, -0.0])
        return round(rng.uniform(lo, hi), 6)
    if t == "str":
        max_len = int(desc.get("max_len", 8))
        if boundary and rng.random() < 0.5:
            return rng.choice(["", " ", "0", "Ø", "日本語", "a" * max_len])
        alphabet = string.ascii_letters + string.digits + " _-"
        length = rng.randint(0, max_len)
        return "".join(rng.choice(alphabet) for _ in range(length))
    if t == "bool":
        return rng.random() < 0.5
    if t == "none":
        return None
    if t == "list":
        item = desc.get("item", {"type": "int"})
        max_len = int(desc.get("max_len", 3))
        if boundary and rng.random() < 0.4:
            return []
        length = rng.randint(0, max_len)
        return [_gen(item, rng, boundary) for _ in range(length)]
    if t == "dict":
        props = desc.get("properties", {})
        return {k: _gen(v, rng, boundary) for k, v in props.items()}
    if t == "enum":
        values = desc.get("values", [])
        if not values:
            raise InputSchemaError("enum requires values")
        return rng.choice(values)
    raise InputSchemaError(f"unknown type {t!r}")
