"""Breaking-change classification — the machine half of "compatibility".

Two-layer verification, as recommended by research 03 / rec_03:

* **Structural layer (implemented here).** Enumerated change rules that decide
  ``ChangeSeverity`` mechanically, in the spirit of oasdiff's change catalogue.
  Fast, total, no false negatives on the categories it covers.
* **Semantic layer (declared, not faked).** Refinement-as-implication needs a
  model checker; :func:`classify` never claims semantic compatibility. Callers
  that need it register a :class:`SemanticRefinementCheck`. If none is
  registered, semantic compatibility is reported as ``UNKNOWN`` and — per the
  rule "no mechanical witness means advisory only" — it may veto but not admit.

Every rule has a stable code (``H4.*``) so a finding can be cited in an evidence
receipt and traced to a spec clause.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from ..contracts.base import ChangeSeverity

__all__ = ["Change", "classify", "classify_json_schema", "SemanticRefinementCheck", "SemanticResult"]


@dataclass(frozen=True)
class Change:
    code: str
    severity: ChangeSeverity
    location: str
    message: str
    detail: dict[str, Any] | None = None


class SemanticResult:
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"


class SemanticRefinementCheck(Protocol):
    """Hook for a real refinement checker (TLC/Apalache/SMT).

    Deliberately narrow: it may only *strengthen* the verdict to INCOMPATIBLE or
    report UNKNOWN. It can never downgrade a structural BREAKING to compatible —
    a structural break is observable to consumers regardless of semantics.
    """

    def __call__(self, old: dict[str, Any], new: dict[str, Any]) -> str: ...


# --------------------------------------------------------------------- python


def _param_index(params: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {p["name"]: p for p in params}


def _positional(params: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [p for p in params if p["kind"] in ("positional_only", "positional_or_keyword")]


def _accepts_var_keyword(params: list[dict[str, Any]]) -> bool:
    return any(p["kind"] == "var_keyword" for p in params)


def _accepts_var_positional(params: list[dict[str, Any]]) -> bool:
    return any(p["kind"] == "var_positional" for p in params)


def _compare_function(old: dict[str, Any], new: dict[str, Any], loc: str) -> list[Change]:
    out: list[Change] = []
    o_params, n_params = old["params"], new["params"]
    o_idx, n_idx = _param_index(o_params), _param_index(n_params)

    for name, op in o_idx.items():
        np_ = n_idx.get(name)
        if np_ is None:
            if op["kind"] == "var_keyword" or _accepts_var_keyword(n_params):
                out.append(
                    Change(
                        "H4.PARAM_ABSORBED_BY_KWARGS",
                        ChangeSeverity.PATCH,
                        f"{loc}({name})",
                        f"parameter {name!r} removed but **kwargs absorbs it",
                    )
                )
            else:
                out.append(
                    Change(
                        "H4.PARAM_REMOVED",
                        ChangeSeverity.BREAKING,
                        f"{loc}({name})",
                        f"parameter {name!r} was removed",
                    )
                )
            continue
        if op["kind"] != np_["kind"]:
            tightening = (op["kind"], np_["kind"]) in {
                ("positional_or_keyword", "positional_only"),
                ("positional_or_keyword", "keyword_only"),
            }
            out.append(
                Change(
                    "H4.PARAM_KIND_CHANGED",
                    ChangeSeverity.BREAKING if tightening else ChangeSeverity.ADDITIVE,
                    f"{loc}({name})",
                    f"parameter {name!r} kind {op['kind']} -> {np_['kind']}",
                )
            )
        if op["has_default"] and not np_["has_default"]:
            out.append(
                Change(
                    "H4.PARAM_DEFAULT_REMOVED",
                    ChangeSeverity.BREAKING,
                    f"{loc}({name})",
                    f"parameter {name!r} lost its default; existing callers break",
                )
            )
        elif not op["has_default"] and np_["has_default"]:
            out.append(
                Change(
                    "H4.PARAM_DEFAULT_ADDED",
                    ChangeSeverity.ADDITIVE,
                    f"{loc}({name})",
                    f"parameter {name!r} gained a default",
                )
            )
        elif (
            op["has_default"]
            and np_["has_default"]
            and op["default_repr"] != np_["default_repr"]
        ):
            # A silently changed default is an "Assignment Override" conflict in
            # ConflictLens terms — observable behaviour change without a signature
            # change, which is precisely the class of drift humans never notice.
            out.append(
                Change(
                    "H4.PARAM_DEFAULT_CHANGED",
                    ChangeSeverity.BREAKING,
                    f"{loc}({name})",
                    f"default of {name!r} changed "
                    f"{op['default_repr']!r} -> {np_['default_repr']!r}",
                )
            )
        if op["annotation"] != np_["annotation"]:
            out.append(
                Change(
                    "H4.PARAM_TYPE_CHANGED",
                    ChangeSeverity.BREAKING,
                    f"{loc}({name})",
                    f"type of {name!r} changed {op['annotation']} -> {np_['annotation']}",
                )
            )

    for name, np_ in n_idx.items():
        if name in o_idx:
            continue
        if np_["has_default"] or np_["kind"] in ("var_positional", "var_keyword"):
            out.append(
                Change(
                    "H4.PARAM_ADDED_OPTIONAL",
                    ChangeSeverity.ADDITIVE,
                    f"{loc}({name})",
                    f"optional parameter {name!r} added",
                )
            )
        else:
            out.append(
                Change(
                    "H4.PARAM_ADDED_REQUIRED",
                    ChangeSeverity.BREAKING,
                    f"{loc}({name})",
                    f"required parameter {name!r} added",
                )
            )

    o_pos, n_pos = _positional(o_params), _positional(n_params)
    common = min(len(o_pos), len(n_pos))
    if [p["name"] for p in o_pos[:common]] != [p["name"] for p in n_pos[:common]]:
        out.append(
            Change(
                "H4.POSITIONAL_ORDER_CHANGED",
                ChangeSeverity.BREAKING,
                loc,
                "positional parameter order changed",
                {
                    "old": [p["name"] for p in o_pos],
                    "new": [p["name"] for p in n_pos],
                },
            )
        )

    if old["returns"] != new["returns"]:
        out.append(
            Change(
                "H4.RETURN_TYPE_CHANGED",
                ChangeSeverity.BREAKING,
                loc,
                f"return type changed {old['returns']} -> {new['returns']}",
            )
        )
    if old["is_async"] != new["is_async"]:
        out.append(
            Change(
                "H4.ASYNCNESS_CHANGED",
                ChangeSeverity.BREAKING,
                loc,
                f"async-ness changed {old['is_async']} -> {new['is_async']}",
            )
        )
    return out


def _compare_class(old: dict[str, Any], new: dict[str, Any], loc: str) -> list[Change]:
    out: list[Change] = []
    o_methods = {m["qualname"]: m for m in old["methods"]}
    n_methods = {m["qualname"]: m for m in new["methods"]}
    for name, om in o_methods.items():
        nm = n_methods.get(name)
        if nm is None:
            out.append(
                Change("H4.METHOD_REMOVED", ChangeSeverity.BREAKING, f"{loc}.{name}", f"method {name!r} removed")
            )
        else:
            out.extend(_compare_function(om, nm, f"{loc}.{name}"))
    for name in n_methods.keys() - o_methods.keys():
        out.append(
            Change("H4.METHOD_ADDED", ChangeSeverity.ADDITIVE, f"{loc}.{name}", f"method {name!r} added")
        )
    o_attrs = dict(
        (a["name"], a["annotation"]) for a in old.get("attributes", [])
    )
    n_attrs = dict((a["name"], a["annotation"]) for a in new.get("attributes", []))
    for name in o_attrs.keys() - n_attrs.keys():
        out.append(
            Change("H4.ATTRIBUTE_REMOVED", ChangeSeverity.BREAKING, f"{loc}.{name}", f"attribute {name!r} removed")
        )
    for name in n_attrs.keys() - o_attrs.keys():
        out.append(
            Change("H4.ATTRIBUTE_ADDED", ChangeSeverity.ADDITIVE, f"{loc}.{name}", f"attribute {name!r} added")
        )
    removed_bases = set(old.get("bases", [])) - set(new.get("bases", []))
    if removed_bases:
        out.append(
            Change(
                "H4.BASE_REMOVED",
                ChangeSeverity.BREAKING,
                loc,
                f"base class(es) removed: {sorted(removed_bases)}",
            )
        )
    return out


# ---------------------------------------------------------------- json schema

_TYPE_WIDTH = {"integer": 1, "number": 2, "string": 1, "boolean": 1, "array": 1, "object": 1}


def classify_json_schema(old: dict[str, Any], new: dict[str, Any], loc: str = "") -> list[Change]:
    """Data-contract compatibility. Producer-side (response) semantics.

    Rules follow the same intuition as oasdiff: anything that can invalidate a
    consumer's existing, valid usage is BREAKING.
    """

    out: list[Change] = []
    o_req = set(old.get("required", []) or [])
    n_req = set(new.get("required", []) or [])
    o_props = old.get("properties", {}) or {}
    n_props = new.get("properties", {}) or {}

    for name in sorted(n_req - o_req):
        out.append(
            Change(
                "H4.SCHEMA_REQUIRED_ADDED",
                ChangeSeverity.BREAKING,
                f"{loc}.{name}",
                f"property {name!r} became required",
            )
        )
    for name in sorted(o_req - n_req):
        out.append(
            Change(
                "H4.SCHEMA_REQUIRED_REMOVED",
                ChangeSeverity.ADDITIVE,
                f"{loc}.{name}",
                f"property {name!r} is no longer required",
            )
        )
    for name in sorted(o_props.keys() - n_props.keys()):
        out.append(
            Change(
                "H4.SCHEMA_PROPERTY_REMOVED",
                ChangeSeverity.BREAKING,
                f"{loc}.{name}",
                f"property {name!r} removed",
            )
        )
    for name in sorted(n_props.keys() - o_props.keys()):
        severity = (
            ChangeSeverity.BREAKING if name in n_req else ChangeSeverity.ADDITIVE
        )
        out.append(
            Change(
                "H4.SCHEMA_PROPERTY_ADDED",
                severity,
                f"{loc}.{name}",
                f"property {name!r} added",
            )
        )
    for name in sorted(o_props.keys() & n_props.keys()):
        op, np_ = o_props[name], n_props[name]
        where = f"{loc}.{name}"
        if op.get("type") != np_.get("type"):
            out.append(
                Change(
                    "H4.SCHEMA_TYPE_CHANGED",
                    ChangeSeverity.BREAKING,
                    where,
                    f"type {op.get('type')} -> {np_.get('type')}",
                )
            )
        o_enum, n_enum = op.get("enum"), np_.get("enum")
        if o_enum is not None and n_enum is not None:
            removed = set(map(str, o_enum)) - set(map(str, n_enum))
            added = set(map(str, n_enum)) - set(map(str, o_enum))
            if removed:
                out.append(
                    Change(
                        "H4.SCHEMA_ENUM_SHRUNK",
                        ChangeSeverity.BREAKING,
                        where,
                        f"enum values removed: {sorted(removed)}",
                    )
                )
            if added:
                out.append(
                    Change(
                        "H4.SCHEMA_ENUM_GROWN",
                        ChangeSeverity.ADDITIVE,
                        where,
                        f"enum values added: {sorted(added)}",
                    )
                )
        elif o_enum is None and n_enum is not None:
            out.append(
                Change(
                    "H4.SCHEMA_ENUM_INTRODUCED",
                    ChangeSeverity.BREAKING,
                    where,
                    "an unconstrained field became an enum",
                )
            )
        for key, direction in (("maxLength", "shrink"), ("maximum", "shrink"), ("minimum", "grow"), ("minLength", "grow")):
            ov, nv = op.get(key), np_.get(key)
            if ov is None or nv is None:
                continue
            tighter = nv < ov if direction == "shrink" else nv > ov
            if tighter:
                out.append(
                    Change(
                        "H4.SCHEMA_CONSTRAINT_TIGHTENED",
                        ChangeSeverity.BREAKING,
                        where,
                        f"{key} tightened {ov} -> {nv}",
                    )
                )
        if op.get("type") == "object" and np_.get("type") == "object":
            out.extend(classify_json_schema(op, np_, where))
    return out


# ------------------------------------------------------------------ top level


def classify(
    old_surface: dict[str, Any],
    new_surface: dict[str, Any],
    *,
    semantic_check: SemanticRefinementCheck | Callable[..., str] | None = None,
) -> tuple[list[Change], ChangeSeverity, str]:
    """Diff two surfaces. Returns ``(changes, overall_severity, semantic_result)``."""

    changes: list[Change] = []
    o_mods = old_surface.get("modules", {})
    n_mods = new_surface.get("modules", {})

    for module in sorted(o_mods.keys() - n_mods.keys()):
        changes.append(
            Change("H4.MODULE_REMOVED", ChangeSeverity.BREAKING, module, f"module {module!r} removed")
        )
    for module in sorted(n_mods.keys() - o_mods.keys()):
        changes.append(
            Change("H4.MODULE_ADDED", ChangeSeverity.ADDITIVE, module, f"module {module!r} added")
        )
    for module in sorted(o_mods.keys() & n_mods.keys()):
        om, nm = o_mods[module], n_mods[module]
        if "error" in om or "error" in nm:
            changes.append(
                Change(
                    "H4.SURFACE_UNPARSEABLE",
                    ChangeSeverity.BREAKING,
                    module,
                    "surface could not be extracted; an unverifiable surface is "
                    "treated as breaking, never as unchanged",
                )
            )
            continue
        o_fn = {f["qualname"]: f for f in om.get("functions", [])}
        n_fn = {f["qualname"]: f for f in nm.get("functions", [])}
        for name in sorted(o_fn.keys() - n_fn.keys()):
            changes.append(
                Change("H4.SYMBOL_REMOVED", ChangeSeverity.BREAKING, f"{module}.{name}", f"function {name!r} removed")
            )
        for name in sorted(n_fn.keys() - o_fn.keys()):
            changes.append(
                Change("H4.SYMBOL_ADDED", ChangeSeverity.ADDITIVE, f"{module}.{name}", f"function {name!r} added")
            )
        for name in sorted(o_fn.keys() & n_fn.keys()):
            changes.extend(_compare_function(o_fn[name], n_fn[name], f"{module}.{name}"))

        o_cls = {c["qualname"]: c for c in om.get("classes", [])}
        n_cls = {c["qualname"]: c for c in nm.get("classes", [])}
        for name in sorted(o_cls.keys() - n_cls.keys()):
            changes.append(
                Change("H4.SYMBOL_REMOVED", ChangeSeverity.BREAKING, f"{module}.{name}", f"class {name!r} removed")
            )
        for name in sorted(n_cls.keys() - o_cls.keys()):
            changes.append(
                Change("H4.SYMBOL_ADDED", ChangeSeverity.ADDITIVE, f"{module}.{name}", f"class {name!r} added")
            )
        for name in sorted(o_cls.keys() & n_cls.keys()):
            changes.extend(_compare_class(o_cls[name], n_cls[name], f"{module}.{name}"))

        o_const = {c["name"] for c in om.get("constants", [])}
        n_const = {c["name"] for c in nm.get("constants", [])}
        for name in sorted(o_const - n_const):
            changes.append(
                Change("H4.CONSTANT_REMOVED", ChangeSeverity.BREAKING, f"{module}.{name}", f"constant {name!r} removed")
            )

    o_schemas = old_surface.get("schemas", {}) or {}
    n_schemas = new_surface.get("schemas", {}) or {}
    for name in sorted(o_schemas.keys() - n_schemas.keys()):
        changes.append(
            Change("H4.SCHEMA_REMOVED", ChangeSeverity.BREAKING, name, f"schema {name!r} removed")
        )
    for name in sorted(o_schemas.keys() & n_schemas.keys()):
        changes.extend(classify_json_schema(o_schemas[name], n_schemas[name], name))

    overall = ChangeSeverity.max_of([c.severity for c in changes])

    semantic = SemanticResult.UNKNOWN
    if semantic_check is not None:
        semantic = semantic_check(old_surface, new_surface)
        if semantic == SemanticResult.INCOMPATIBLE:
            overall = ChangeSeverity.BREAKING
            changes.append(
                Change(
                    "H4.SEMANTIC_REFINEMENT_FAILED",
                    ChangeSeverity.BREAKING,
                    "<semantic>",
                    "new spec does not refine the old one",
                )
            )
    return changes, overall, semantic
