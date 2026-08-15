"""Strict parser for spec.md files.

Format (PLAN.md WP1):

    ---
    spec_id: units.demo.adder
    version: 0.1.0
    r_level: R0
    depends: []
    artifacts: ["demo/adder.py"]
    ---

    ## L1 意图            <- free prose

    ```clause
    id: REQ-demo-adder-L1-1
    level: L1
    text: 计算器必须对两个整数求和并返回精确结果。
    witness: h3:adder-basic        # gate:<id> or holdout:<set>
    ```

    ## L2 契约
    ```contract
    {...json...}
    ```
    ```invariant
    expr: add(a,b) == add(b,a)
    scope: h2
    ```

    ## DONT-CARE
    ```dontcare
    - id: DC-1
      kind: unspecified
      region: 日志格式
    ```
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

import yaml

from .schema import DC_KINDS, Clause, DontCare, Invariant, SpecUnit, Witness

_FRONT = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_BLOCK = re.compile(r"```([a-zA-Z0-9_-]+)(?:[^\n`]*)\n(.*?)```", re.DOTALL)
_SECTION = re.compile(r"^##\s+(L1|L2|L3|DONT-CARE)[^\n]*$", re.MULTILINE)

VALID_RLEVELS = ("R0", "R1", "R2", "R3")


class SpecParseError(ValueError):
    pass


def parse_spec(source: str | None = None, *, path: str | None = None) -> SpecUnit:
    if source is None:
        if path is None:
            raise SpecParseError("either source text or path is required")
        with open(path, encoding="utf-8") as f:
            source = f.read()

    m = _FRONT.match(source)
    if not m:
        raise SpecParseError("missing YAML frontmatter")
    try:
        meta: dict[str, Any] = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:  # pragma: no cover - defensive
        raise SpecParseError(f"frontmatter YAML error: {e}") from e

    for key in ("spec_id", "version", "r_level"):
        if key not in meta:
            raise SpecParseError(f"frontmatter missing required key: {key}")
    if meta["r_level"] not in VALID_RLEVELS:
        raise SpecParseError(f"invalid r_level {meta['r_level']!r}, expected one of {VALID_RLEVELS}")

    body = source[m.end():]

    # split body into sections by `## <LEVEL>` headings
    heads = list(_SECTION.finditer(body))
    sections: dict[str, str] = {}
    if heads:
        for i, h in enumerate(heads):
            start = h.end()
            end = heads[i + 1].start() if i + 1 < len(heads) else len(body)
            sections[h.group(1)] = body[start:end]
        prelude = body[: heads[0].start()]
    else:
        prelude = body
    sections.setdefault("L1", "")
    sections.setdefault("L2", "")
    sections.setdefault("L3", "")

    clauses: list[Clause] = []
    contract: dict[str, Any] = {}
    invariants: list[Invariant] = []
    dont_cares: list[DontCare] = []

    def scan(text: str, level: str) -> None:
        nonlocal contract
        for tag, payload in _BLOCK.findall(text):
            if tag == "clause":
                clauses.append(_parse_clause(payload, level))
            elif tag == "contract":
                try:
                    contract = json.loads(payload)
                except json.JSONDecodeError as e:
                    raise SpecParseError(f"contract block is not valid JSON: {e}") from e
                if not isinstance(contract, dict):
                    raise SpecParseError("contract block must be a JSON object")
            elif tag == "invariant":
                invariants.append(_parse_invariant(payload))
            elif tag == "dontcare":
                dont_cares.extend(_parse_dontcare(payload))
            # unknown tags are ignored (forward compat)

    scan(prelude, "L1")
    for lvl in ("L1", "L2", "L3"):
        scan(sections.get(lvl, ""), lvl)
    if "DONT-CARE" in sections:
        scan(sections["DONT-CARE"], "L3")  # blocks there carry own ids

    unit = SpecUnit(
        spec_id=str(meta["spec_id"]),
        version=str(meta["version"]),
        r_level=meta["r_level"],
        depends=[str(d) for d in meta.get("depends") or []],
        artifacts=[str(a) for a in meta.get("artifacts") or []],
        prose={lvl: sections.get(lvl, "").strip() for lvl in ("L1", "L2", "L3")},
        clauses=clauses,
        contract=contract,
        invariants=invariants,
        dont_cares=dont_cares,
        source_path=path,
    )
    return unit


def _parse_clause(payload: str, default_level: str) -> Clause:
    try:
        data = yaml.safe_load(payload) or {}
    except yaml.YAMLError as e:
        raise SpecParseError(f"clause block YAML error: {e}") from e
    if not isinstance(data, dict) or "text" not in data:
        raise SpecParseError(f"clause block requires at least `text`, got: {payload[:80]!r}")
    level = str(data.get("level", default_level))
    if level not in ("L1", "L2", "L3"):
        raise SpecParseError(f"clause level {level!r} invalid")
    witness: Optional[Witness] = None
    holdout_set: Optional[str] = None
    w = data.get("witness")
    if w:
        w = str(w)
        if ":" not in w:
            raise SpecParseError(f"witness {w!r} must be `gate:<id>` or `holdout:<set>`")
        kind, _, ref = w.partition(":")
        if kind not in ("gate", "holdout"):
            raise SpecParseError(f"witness kind {kind!r} must be gate|holdout")
        witness = Witness(kind=kind, ref=ref)
        if kind == "holdout":
            holdout_set = ref
    return Clause(
        clause_id=str(data.get("id") or ""),
        level=level,
        text=str(data["text"]),
        witness=witness,
        holdout_set=holdout_set,
    )


def _parse_invariant(payload: str) -> Invariant:
    try:
        data = yaml.safe_load(payload) or {}
    except yaml.YAMLError as e:
        raise SpecParseError(f"invariant block YAML error: {e}") from e
    if "expr" not in data:
        raise SpecParseError("invariant block requires `expr`")
    return Invariant(
        inv_id=str(data.get("id") or ""),
        expr=str(data["expr"]),
        scope=str(data.get("scope", "h2")),
    )


def _parse_dontcare(payload: str) -> list[DontCare]:
    try:
        data = yaml.safe_load(payload)
    except yaml.YAMLError as e:
        raise SpecParseError(f"dontcare block YAML error: {e}") from e
    if data is None:
        return []
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise SpecParseError("dontcare block must be a list of mappings")
    out: list[DontCare] = []
    for item in data:
        if not isinstance(item, dict) or "region" not in item:
            raise SpecParseError("each dontcare entry requires `region`")
        kind = str(item.get("kind", "unspecified"))
        if kind not in DC_KINDS:
            raise SpecParseError(f"dontcare kind {kind!r} invalid, expected one of {DC_KINDS}")
        out.append(DontCare(dc_id=str(item.get("id") or ""), kind=kind, region=str(item["region"])))
    return out
