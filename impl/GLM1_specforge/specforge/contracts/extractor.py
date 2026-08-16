"""AST-based public surface extraction for Python packages (WP2)."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Optional

from .surface import ClassSig, FunctionSig, Param, SurfaceSnapshot


def _ann(node: Optional[ast.expr]) -> Optional[str]:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover
        return "<unparsable>"


def _default(node: Optional[ast.expr]) -> Optional[str]:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover
        return "<unparsable>"


def _func_sig(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionSig:
    params: list[Param] = []
    a = fn.args
    pos = list(a.posonlyargs) + list(a.args)
    defaults: list[Optional[ast.expr]] = [None] * (len(pos) - len(a.defaults)) + list(a.defaults)
    for arg, dflt in zip(pos, defaults):
        params.append(Param(name=arg.arg, annotation=_ann(arg.annotation), default=_default(dflt)))
    for arg, dflt in zip(a.kwonlyargs, a.kw_defaults):
        params.append(Param(name=arg.arg, annotation=_ann(arg.annotation), default=_default(dflt)))
    if a.vararg:
        params.append(Param(name=f"*{a.vararg.arg}", annotation=_ann(a.vararg.annotation), default="variadic"))
    if a.kwarg:
        params.append(Param(name=f"**{a.kwarg.arg}", annotation=_ann(a.kwarg.annotation), default="kw_variadic"))
    return FunctionSig(name=fn.name, params=params, returns=_ann(fn.returns))


class _Visitor(ast.NodeVisitor):
    def __init__(self, module_name: str):
        self.snap = SurfaceSnapshot(module=module_name)
        self._all_exports: Optional[list[str]] = None

    def visit_Module(self, node: ast.Module) -> None:
        for stmt in node.body:
            self.visit(stmt)

    def _public(self, name: str) -> bool:
        return not name.startswith("_")

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if self._public(node.name):
            self.snap.functions[node.name] = _func_sig(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if not self._public(node.name):
            return
        bases = [_ann(b) or "" for b in node.bases]
        methods: list[FunctionSig] = []
        attrs: list[str] = []
        for stmt in node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if self._public(stmt.name) or stmt.name in ("__init__", "__call__"):
                    methods.append(_func_sig(stmt))
            elif isinstance(stmt, ast.Assign):
                for t in stmt.targets:
                    if isinstance(t, ast.Name) and self._public(t.id):
                        attrs.append(t.id)
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                if self._public(stmt.target.id):
                    attrs.append(stmt.target.id)
        self.snap.classes[node.name] = ClassSig(node.name, bases, methods, attrs)

    def visit_Assign(self, node: ast.Assign) -> None:
        for t in node.targets:
            if isinstance(t, ast.Name):
                if t.id == "__all__":
                    try:
                        vals = ast.literal_eval(node.value)
                        if isinstance(vals, (list, tuple)):
                            self._all_exports = [str(v) for v in vals]
                            self.snap.dunder_exports = self._all_exports
                    except Exception:
                        pass
                elif self._public(t.id):
                    try:
                        self.snap.constants[t.id] = repr(ast.literal_eval(node.value))
                    except Exception:
                        self.snap.constants[t.id] = "<expr>"

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name) and self._public(node.target.id) and node.value is not None:
            try:
                self.snap.constants[node.target.id] = repr(ast.literal_eval(node.value))
            except Exception:
                self.snap.constants[node.target.id] = "<expr>"

    def restrict_to_all(self) -> None:
        """If __all__ is declared, surface contains only those names (plus classes/functions resolved)."""
        if self._all_exports is None:
            return
        keep = set(self._all_exports)
        self.snap.functions = {k: v for k, v in self.snap.functions.items() if k in keep}
        self.snap.classes = {k: v for k, v in self.snap.classes.items() if k in keep}
        self.snap.constants = {k: v for k, v in self.snap.constants.items() if k in keep}


def extract_module(source: str, module_name: str = "<module>") -> SurfaceSnapshot:
    tree = ast.parse(source)
    v = _Visitor(module_name)
    v.visit(tree)
    v.restrict_to_all()
    return v.snap


def extract_file(path: str | Path, module_name: Optional[str] = None) -> SurfaceSnapshot:
    p = Path(path)
    return extract_module(p.read_text(encoding="utf-8"), module_name or p.stem)


def extract_tree(root: str | Path, package_name: Optional[str] = None) -> SurfaceSnapshot:
    root = Path(root)
    merged = SurfaceSnapshot(module=package_name or root.name)
    all_decl: Optional[list[str]] = None
    for py in sorted(root.rglob("*.py")):
        snap = extract_file(py)
        if snap.dunder_exports:
            all_decl = snap.dunder_exports  # package-level __init__ wins (last sorted)
        for k, v in snap.functions.items():
            merged.functions[f"{py.stem}.{k}" if py.name != "__init__.py" else k] = v
        for k, v in snap.classes.items():
            merged.classes[f"{py.stem}.{k}" if py.name != "__init__.py" else k] = v
        for k, v in snap.constants.items():
            merged.constants[f"{py.stem}.{k}" if py.name != "__init__.py" else k] = v
    if all_decl:
        keep = set(all_decl)
        merged.functions = {k: v for k, v in merged.functions.items() if k in keep}
        merged.classes = {k: v for k, v in merged.classes.items() if k in keep}
        merged.constants = {k: v for k, v in merged.constants.items() if k in keep}
        merged.dunder_exports = all_decl
    return merged


def extract(path: str | Path, module_name: Optional[str] = None) -> SurfaceSnapshot:
    p = Path(path)
    if p.is_dir():
        return extract_tree(p, module_name)
    return extract_file(p, module_name)
