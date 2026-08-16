from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


def _annotation_str(node: ast.expr | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:  # noqa: BLE001
        return ""


def extract_surface(root: Path) -> dict[str, dict[str, Any]]:
    """Extract a deterministic public-surface map from a Python tree.

    Returns {qualified_symbol: {kind, signature}} where signature captures
    parameter names + annotations for functions/methods and method names for
    classes. This is the mechanical witness for L2 interface contracts (H4)
    and the drift detector's structural anchor (H7).
    """

    surface: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root)
        if any(part.startswith(".") or part in {"__pycache__", ".venv", "node_modules"} for part in rel.parts):
            continue
        module = ".".join(rel.with_suffix("").parts)
        if module.endswith(".__init__"):
            module = module[: -len(".__init__")]
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue
                params = [
                    f"{a.arg}:{_annotation_str(a.annotation)}" for a in node.args.args
                ]
                surface[f"{module}.{node.name}"] = {
                    "kind": "function",
                    "signature": f"({', '.join(params)}) -> {_annotation_str(node.returns)}",
                }
            elif isinstance(node, ast.ClassDef):
                if node.name.startswith("_"):
                    continue
                methods = sorted(
                    m.name
                    for m in node.body
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and not m.name.startswith("_")
                )
                surface[f"{module}.{node.name}"] = {
                    "kind": "class",
                    "signature": "{" + ",".join(methods) + "}",
                }
    return surface


def surface_breaking(baseline: dict[str, dict[str, Any]], candidate: dict[str, dict[str, Any]]) -> list[str]:
    problems: list[str] = []
    for symbol, info in baseline.items():
        if symbol not in candidate:
            problems.append(f"removed: {symbol}")
        elif candidate[symbol]["signature"] != info["signature"]:
            problems.append(
                f"signature changed: {symbol} {info['signature']} -> {candidate[symbol]['signature']}"
            )
    return problems
