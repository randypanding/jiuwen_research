from __future__ import annotations

import ast
import re
import time

from swarmdev.contracts import GateOutcome
from swarmdev.contracts.receipt import GateStatus

from swarmdev.gates.protocol import GateContext


class InvariantGate:
    gate_id = "H6"

    def __init__(self, dangerous_patterns: list[str], import_allowlist: list[str] | None = None):
        self.dangerous_patterns = list(dangerous_patterns)
        self.import_allowlist = list(import_allowlist) if import_allowlist is not None else None

    def run(self, ctx: GateContext) -> GateOutcome:
        started = time.monotonic()
        hits: set[str] = set()
        for path in sorted(ctx.instance_dir.rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            rel = str(path.relative_to(ctx.instance_dir))
            for pattern in self.dangerous_patterns:
                if re.search(pattern, source):
                    hits.add(f"{rel}: pattern {pattern}")
            if self.import_allowlist is None:
                continue
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            allowed = set(self.import_allowlist)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0]
                        if top not in allowed:
                            hits.add(f"{rel}: import {top}")
                elif isinstance(node, ast.ImportFrom):
                    if node.level == 0 and node.module:
                        top = node.module.split(".")[0]
                        if top not in allowed:
                            hits.add(f"{rel}: import {top}")
        if hits:
            return GateOutcome(
                gate_id=self.gate_id,
                status=GateStatus.FAIL,
                details="invariant violations: " + "; ".join(sorted(hits)),
                duration_s=time.monotonic() - started,
            )
        return GateOutcome(
            gate_id=self.gate_id,
            status=GateStatus.PASS,
            details="no dangerous patterns or disallowed imports",
            duration_s=time.monotonic() - started,
        )
