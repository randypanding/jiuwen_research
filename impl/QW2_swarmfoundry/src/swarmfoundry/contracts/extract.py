from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from swarmfoundry.schema.surface import (
    SYMBOL_CLASS,
    SYMBOL_CONSTANT,
    SYMBOL_FUNCTION,
    SYMBOL_METHOD,
    SYMBOL_SCHEMA_FILE,
    ContractSurface,
    SymbolSurface,
)

_SCHEMA_SUFFIXES = (".schema.json", ".contract.json")


def _annotation_text(node: ast.expr | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def _signature(func: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = func.args
    parts: list[str] = []
    n = len(args.args)
    defaults = list(args.defaults)
    pad = n - len(defaults)
    for i, a in enumerate(args.args):
        if a.arg in ("self", "cls"):
            continue
        txt = a.arg
        ann = _annotation_text(a.annotation)
        if ann:
            txt += f": {ann}"
        di = i - pad
        if di >= 0:
            txt += f"={ast.unparse(defaults[di])}"
        parts.append(txt)
    if args.vararg:
        parts.append("*" + args.vararg.arg)
    for a, d in zip(args.kwonlyargs, args.kw_defaults):
        txt = a.arg
        ann = _annotation_text(a.annotation)
        if ann:
            txt += f": {ann}"
        if d is not None:
            txt += f"={ast.unparse(d)}"
        parts.append(txt)
    if args.kwarg:
        parts.append("**" + args.kwarg.arg)
    ret = _annotation_text(func.returns)
    return f"({', '.join(parts)})" + (f" -> {ret}" if ret else "")


def _is_public(name: str) -> bool:
    return not name.startswith("_")


def extract_module_surface(path: Path, module_prefix: str) -> list[SymbolSurface]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    rel = path.name
    qual = f"{module_prefix}.{rel.removesuffix('.py')}" if module_prefix else rel.removesuffix(".py")
    out: list[SymbolSurface] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_public(node.name):
            out.append(
                SymbolSurface(
                    name=f"{qual}.{node.name}",
                    kind=SYMBOL_FUNCTION,
                    signature=_signature(node),
                    detail=(ast.get_docstring(node) or "").splitlines()[0][:200] if ast.get_docstring(node) else "",
                )
            )
        elif isinstance(node, ast.ClassDef) and _is_public(node.name):
            out.append(SymbolSurface(name=f"{qual}.{node.name}", kind=SYMBOL_CLASS, signature="", detail=""))
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_public(sub.name):
                    out.append(
                        SymbolSurface(
                            name=f"{qual}.{node.name}.{sub.name}",
                            kind=SYMBOL_METHOD,
                            signature=_signature(sub),
                            detail="",
                        )
                    )
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
            if isinstance(tgt, ast.Name) and tgt.id.isupper() and _is_public(tgt.id):
                try:
                    val = ast.unparse(node.value)[:120]
                except Exception:
                    val = ""
                out.append(SymbolSurface(name=f"{qual}.{tgt.id}", kind=SYMBOL_CONSTANT, signature="", detail=val))
    return out


def extract_surface(root: Path, module: str = "instance") -> ContractSurface:
    """Extract the contract surface of an instance directory: public Python API
    plus data-contract files (*.schema.json / *.contract.json) by content hash."""
    root = Path(root)
    symbols: list[SymbolSurface] = []
    py_files = sorted(p for p in root.rglob("*.py") if ".venv" not in p.parts and "site-packages" not in p.parts)
    for p in py_files:
        rel = p.relative_to(root)
        prefix = ".".join(rel.parts[:-1])
        symbols.extend(extract_module_surface(p, prefix))
    for suffix in _SCHEMA_SUFFIXES:
        for p in sorted(root.rglob(f"*{suffix}")):
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            symbols.append(
                SymbolSurface(
                    name=str(p.relative_to(root)),
                    kind=SYMBOL_SCHEMA_FILE,
                    signature=f"sha256:{digest}",
                    detail="",
                )
            )
    symbols.sort(key=lambda s: (s.kind, s.name))
    return ContractSurface(module=module, symbols=tuple(symbols))


def dump_surface(surface: ContractSurface, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(surface.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def load_surface(path: Path) -> ContractSurface:
    return ContractSurface.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
