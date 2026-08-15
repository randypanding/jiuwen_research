"""Contract surface extraction — the mechanical witness for L2 (H4).

Extracts a *language-level* API surface from Python source with ``ast`` only
(no import, no execution — a gate must never run builder code to decide whether
builder code is admissible), and a *data-level* surface from JSON Schema.

The surface is a plain, sorted, JSON-serialisable structure so that it can be
digested, stored in an evidence receipt, frozen as a wave's interface horizon,
and diffed by :mod:`swarmkernel.oracle.compat`.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

__all__ = ["ParamInfo", "FunctionSurface", "ClassSurface", "ModuleSurface", "extract_surface", "surface_to_dict"]


def _is_public(name: str) -> bool:
    return not name.startswith("_") or (name.startswith("__") and name.endswith("__"))


def _ann(node: ast.expr | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - defensive
        return "<unparseable>"


@dataclass(frozen=True)
class ParamInfo:
    name: str
    kind: str
    """positional_only | positional_or_keyword | var_positional | keyword_only | var_keyword"""
    annotation: str | None = None
    has_default: bool = False
    default_repr: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "annotation": self.annotation,
            "has_default": self.has_default,
            "default_repr": self.default_repr,
        }


@dataclass(frozen=True)
class FunctionSurface:
    qualname: str
    params: tuple[ParamInfo, ...]
    returns: str | None
    is_async: bool
    decorators: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "qualname": self.qualname,
            "params": [p.to_dict() for p in self.params],
            "returns": self.returns,
            "is_async": self.is_async,
            "decorators": sorted(self.decorators),
        }


@dataclass(frozen=True)
class ClassSurface:
    qualname: str
    bases: tuple[str, ...]
    methods: tuple[FunctionSurface, ...]
    attributes: tuple[tuple[str, str | None], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "qualname": self.qualname,
            "bases": sorted(self.bases),
            "methods": [m.to_dict() for m in self.methods],
            "attributes": [{"name": n, "annotation": a} for n, a in self.attributes],
        }


@dataclass
class ModuleSurface:
    module: str
    functions: list[FunctionSurface] = field(default_factory=list)
    classes: list[ClassSurface] = field(default_factory=list)
    constants: list[tuple[str, str | None]] = field(default_factory=list)
    dunder_all: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "functions": [f.to_dict() for f in sorted(self.functions, key=lambda f: f.qualname)],
            "classes": [c.to_dict() for c in sorted(self.classes, key=lambda c: c.qualname)],
            "constants": [
                {"name": n, "annotation": a} for n, a in sorted(self.constants)
            ],
            "__all__": sorted(self.dunder_all) if self.dunder_all is not None else None,
        }


def _params(args: ast.arguments) -> tuple[ParamInfo, ...]:
    out: list[ParamInfo] = []

    def default_reprs(arglist: list[ast.arg], defaults: list[ast.expr]) -> list[str | None]:
        pad: list[str | None] = [None] * (len(arglist) - len(defaults))
        return pad + [_ann(d) for d in defaults]

    posonly_and_regular = list(args.posonlyargs) + list(args.args)
    defaults = default_reprs(posonly_and_regular, list(args.defaults))
    for idx, a in enumerate(posonly_and_regular):
        kind = "positional_only" if idx < len(args.posonlyargs) else "positional_or_keyword"
        d = defaults[idx]
        out.append(
            ParamInfo(a.arg, kind, _ann(a.annotation), has_default=d is not None, default_repr=d)
        )
    if args.vararg:
        out.append(ParamInfo(args.vararg.arg, "var_positional", _ann(args.vararg.annotation)))
    for a, d in zip(args.kwonlyargs, args.kw_defaults):
        out.append(
            ParamInfo(
                a.arg,
                "keyword_only",
                _ann(a.annotation),
                has_default=d is not None,
                default_repr=_ann(d),
            )
        )
    if args.kwarg:
        out.append(ParamInfo(args.kwarg.arg, "var_keyword", _ann(args.kwarg.annotation)))
    return tuple(out)


def _function(node: ast.FunctionDef | ast.AsyncFunctionDef, prefix: str) -> FunctionSurface:
    return FunctionSurface(
        qualname=f"{prefix}{node.name}",
        params=_params(node.args),
        returns=_ann(node.returns),
        is_async=isinstance(node, ast.AsyncFunctionDef),
        decorators=tuple(sorted(filter(None, (_ann(d) for d in node.decorator_list)))),
    )


def _class(node: ast.ClassDef) -> ClassSurface:
    methods: list[FunctionSurface] = []
    attributes: list[tuple[str, str | None]] = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_public(item.name):
            methods.append(_function(item, f"{node.name}."))
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            if _is_public(item.target.id):
                attributes.append((item.target.id, _ann(item.annotation)))
        elif isinstance(item, ast.Assign):
            for tgt in item.targets:
                if isinstance(tgt, ast.Name) and _is_public(tgt.id):
                    attributes.append((tgt.id, None))
    return ClassSurface(
        qualname=node.name,
        bases=tuple(sorted(filter(None, (_ann(b) for b in node.bases)))),
        methods=tuple(sorted(methods, key=lambda m: m.qualname)),
        attributes=tuple(sorted(attributes)),
    )


def extract_module_surface(source: str, module: str) -> ModuleSurface:
    """Parse-only extraction. Never imports or executes ``source``."""

    tree = ast.parse(source)
    surface = ModuleSurface(module=module)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _is_public(node.name):
                surface.functions.append(_function(node, ""))
        elif isinstance(node, ast.ClassDef):
            if _is_public(node.name):
                surface.classes.append(_class(node))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if _is_public(node.target.id):
                surface.constants.append((node.target.id, _ann(node.annotation)))
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "__all__":
                    try:
                        surface.dunder_all = [
                            str(v) for v in ast.literal_eval(node.value)
                        ]
                    except Exception:  # pragma: no cover - malformed __all__
                        surface.dunder_all = []
                elif isinstance(tgt, ast.Name) and _is_public(tgt.id):
                    surface.constants.append((tgt.id, None))
    # An explicit __all__ *is* the declared surface; honour it.
    if surface.dunder_all is not None:
        allowed = set(surface.dunder_all)
        surface.functions = [f for f in surface.functions if f.qualname in allowed]
        surface.classes = [c for c in surface.classes if c.qualname in allowed]
        surface.constants = [c for c in surface.constants if c[0] in allowed]
    return surface


def extract_surface(paths: Iterable[str | Path], root: str | Path = ".") -> dict[str, Any]:
    """Extract the contract surface for a set of files/directories.

    Returns a canonical dict: ``{"modules": {module_name: {...}}, "schemas": {}}``.
    """

    root_path = Path(root)
    modules: dict[str, Any] = {}
    files: list[Path] = []
    for p in paths:
        pp = root_path / p
        if pp.is_dir():
            files.extend(sorted(pp.rglob("*.py")))
        elif pp.suffix == ".py":
            files.append(pp)
    for f in sorted(set(files)):
        rel = f.relative_to(root_path)
        module = ".".join(rel.with_suffix("").parts)
        try:
            surface = extract_module_surface(f.read_text(encoding="utf-8"), module)
        except SyntaxError as exc:
            modules[module] = {"module": module, "error": f"syntax error: {exc}"}
            continue
        modules[module] = surface.to_dict()
    return {"modules": modules, "schemas": {}}


def surface_to_dict(surface: dict[str, Any]) -> dict[str, Any]:
    """Identity today; a seam for adding non-Python surfaces (OpenAPI, proto)."""

    return surface


def attach_schema_surface(
    surface: dict[str, Any], name: str, json_schema: dict[str, Any]
) -> dict[str, Any]:
    """Attach a JSON Schema (data contract) to the surface under ``schemas``."""

    surface.setdefault("schemas", {})[name] = json_schema
    return surface
