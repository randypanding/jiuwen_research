from __future__ import annotations

import ast
import json
import time
from pathlib import Path

from swarmdev.contracts import GateOutcome
from swarmdev.contracts.receipt import GateStatus

from swarmdev.gates.protocol import GateContext


def extract_surface(directory: Path) -> dict[str, list[str]]:
    surface: dict[str, list[str]] = {}
    for path in sorted(Path(directory).rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        names: list[str] = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue
                names.append(node.name)
                args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
                for arg in args:
                    if not arg.arg.startswith("_"):
                        names.append(arg.arg)
                if node.args.vararg and not node.args.vararg.arg.startswith("_"):
                    names.append(node.args.vararg.arg)
                if node.args.kwarg and not node.args.kwarg.arg.startswith("_"):
                    names.append(node.args.kwarg.arg)
            elif isinstance(node, ast.ClassDef):
                if node.name.startswith("_"):
                    continue
                names.append(node.name)
        if names:
            surface[str(path.relative_to(directory))] = names
    return surface


class ContractGate:
    gate_id = "H4"

    def run(self, ctx: GateContext) -> GateOutcome:
        started = time.monotonic()
        current = extract_surface(ctx.instance_dir)
        if ctx.surface_snapshot is None:
            return GateOutcome(
                gate_id=self.gate_id,
                status=GateStatus.PASS,
                evidence_refs=["surface:baseline-recorded"],
                details=json.dumps(current, sort_keys=True),
                duration_s=time.monotonic() - started,
            )
        removed = []
        for module, names in ctx.surface_snapshot.items():
            current_names = set(current.get(module, []))
            for name in names:
                if name not in current_names:
                    removed.append(f"{module}:{name}")
        if removed:
            return GateOutcome(
                gate_id=self.gate_id,
                status=GateStatus.FAIL,
                details="breaking surface removals: " + ", ".join(sorted(removed)),
                duration_s=time.monotonic() - started,
            )
        return GateOutcome(
            gate_id=self.gate_id,
            status=GateStatus.PASS,
            details="contract surface preserved",
            duration_s=time.monotonic() - started,
        )
