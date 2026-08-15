from __future__ import annotations

import re
from pathlib import Path

from swarmfoundry.schema.gates import GATE_H6, GateResult, STATUS_FAIL, STATUS_PASS
from swarmfoundry.gates.base import Gate
from swarmfoundry.gates.context import GateContext

DEFAULT_FORBIDDEN_PATTERNS = [
    ("secret.aws_access_key", r"AKIA[0-9A-Z]{16}"),
    ("secret.private_key_block", r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ("dangerous.rm_rf_root", r"\brm\s+-[a-z]*r[a-z]*f?\s+/(?:\s|$)"),
    ("dangerous.curl_pipe_shell", r"curl[^\n|]*\|\s*(ba)?sh"),
]

DEFAULT_FORBIDDEN_IMPORTS = [
    ("module.os_system_shell", r"^\s*(?:import\s+pty|from\s+socket\s+import)"),
]

_SCAN_SUFFIXES = (".py", ".sh", ".json", ".toml", ".yaml", ".yml", ".md", ".txt", ".js", ".ts")


class H6GuardGate(Gate):
    """H6: invariants & runtime guardrails — the mechanizable projection of the
    constitution: forbidden content patterns, forbidden imports/dependencies,
    file-size bomb defense. Config can extend the default rule set."""

    gate_id = GATE_H6

    def run(self, ctx: GateContext) -> GateResult:
        cfg = ctx.gate_config(self.gate_id)
        patterns = DEFAULT_FORBIDDEN_PATTERNS + [(p["name"], p["regex"]) for p in cfg.get("forbidden_patterns", [])]
        imports = DEFAULT_FORBIDDEN_IMPORTS + [(p["name"], p["regex"]) for p in cfg.get("forbidden_imports", [])]
        max_file_kb = int(cfg.get("max_file_kb", 2048))
        evidence: list[str] = []
        failed = False
        compiled_p = [(n, re.compile(rx)) for n, rx in patterns]
        compiled_i = [(n, re.compile(rx, re.MULTILINE)) for n, rx in imports]
        scanned = 0
        for p in Path(ctx.instance_dir).rglob("*"):
            if not p.is_file() or p.suffix not in _SCAN_SUFFIXES:
                continue
            scanned += 1
            if p.stat().st_size > max_file_kb * 1024:
                failed = True
                evidence.append(f"file exceeds {max_file_kb}KB: {p.relative_to(ctx.instance_dir)}")
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            for name, rx in compiled_p:
                if rx.search(text):
                    failed = True
                    evidence.append(f"forbidden pattern '{name}' in {p.relative_to(ctx.instance_dir)}")
            if p.suffix == ".py":
                for name, rx in compiled_i:
                    if rx.search(text):
                        failed = True
                        evidence.append(f"forbidden import rule '{name}' in {p.relative_to(ctx.instance_dir)}")
        if not failed:
            evidence.append(f"scanned {scanned} files, no constitution violations")
        return GateResult(
            gate_id=self.gate_id,
            status=STATUS_FAIL if failed else STATUS_PASS,
            evidence=tuple(evidence[:50]),
            details={"scanned": scanned},
        )
