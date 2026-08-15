"""H6: invariants & runtime guardrails — dangerous patterns, dependency policy, licenses."""
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any, Iterable, Optional

from .base import GateContext, GateResult, GateVerdict

DANGEROUS_CALLS = {"eval", "exec", "compile", "__import__"}
DANGEROUS_ATTRS = {"system", "popen", "run_in_terminal"}
SECRET_PATTERNS = [
    re.compile(r"(?i)api[_-]?key\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]"),
    re.compile(r"(?i)token\s*=\s*['\"][A-Za-z0-9_\-]{20,}['\"]"),
    re.compile(r"(?i)-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
LICENSE_ALLOWLIST = {"MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "ISC", "MPL-2.0", "Python-2.0", "Unlicense"}


def scan_source(source: str, relpath: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        findings.append({"file": relpath, "line": e.lineno or 0, "kind": "syntax_error",
                         "detail": str(e), "severity": "CRITICAL"})
        return findings
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id in DANGEROUS_CALLS:
                findings.append({"file": relpath, "line": getattr(node, "lineno", 0),
                                 "kind": "dangerous_call", "detail": fn.id, "severity": "CRITICAL"})
            if isinstance(fn, ast.Attribute) and fn.attr in DANGEROUS_ATTRS:
                sev = "CRITICAL"
                if isinstance(fn.value, ast.Name) and fn.value.id == "sh":
                    sev = "WARNING"  # sh module usage flagged but shell= is the killer below
                findings.append({"file": relpath, "line": getattr(node, "lineno", 0),
                                 "kind": "subprocess_attr", "detail": fn.attr, "severity": sev})
            if isinstance(fn, ast.Attribute) and fn.attr == "run" and isinstance(fn.value, ast.Name) \
                    and fn.value.id == "subprocess":
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value:
                        findings.append({"file": relpath, "line": getattr(node, "lineno", 0),
                                         "kind": "shell_true", "detail": "subprocess.run(shell=True)",
                                         "severity": "CRITICAL"})
    for pat in SECRET_PATTERNS:
        for m in pat.finditer(source):
            line = source.count("\n", 0, m.start()) + 1
            findings.append({"file": relpath, "line": line, "kind": "hardcoded_secret",
                             "detail": m.group(0)[:40] + "...", "severity": "CRITICAL"})
    return findings


class H6GuardrailGate:
    gate_id = "h6"
    description = "dangerous patterns / dependency policy / license compatibility"
    hard = True

    def __init__(self, dependency_allowlist: Optional[Iterable[str]] = None,
                 license_allowlist: Optional[set[str]] = None,
                 fail_on_warning: bool = False, max_files: int = 400):
        self.dependency_allowlist = set(dependency_allowlist) if dependency_allowlist is not None else None
        self.license_allowlist = license_allowlist or LICENSE_ALLOWLIST
        self.fail_on_warning = fail_on_warning
        self.max_files = max_files

    def applicable(self, ctx: GateContext) -> bool:
        return True

    def run(self, ctx: GateContext) -> GateResult:
        root = Path(ctx.instance_path)
        findings: list[dict[str, Any]] = []
        scanned = 0
        for py in sorted(root.rglob("*.py")):
            if scanned >= self.max_files:
                break
            rel = str(py.relative_to(root))
            if any(part in (".git", ".venv", "node_modules", "__pycache__") for part in py.parts):
                continue
            scanned += 1
            try:
                findings.extend(scan_source(py.read_text(encoding="utf-8"), rel))
            except OSError:
                pass

        evidence: dict[str, Any] = {"files_scanned": scanned, "findings": findings}

        # dependency policy (pyproject.toml or requirements.txt if present)
        dep_violations: list[str] = []
        req = root / "requirements.txt"
        if self.dependency_allowlist is not None and req.exists():
            for line in req.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                pkg = re.split(r"[<>=!\[ ]", line)[0]
                if pkg and pkg not in self.dependency_allowlist:
                    dep_violations.append(pkg)
        evidence["dependency_violations"] = dep_violations

        license_findings: list[str] = []
        license_file = root / "LICENSE"
        if license_file.exists():
            head = license_file.read_text(encoding="utf-8", errors="ignore")[:400].lower()
            matched = next((L for L in self.license_allowlist if L.lower().split("-")[0] in head), None)
            if matched is None:
                license_findings.append("LICENSE present but not in allowlist")
        evidence["license_findings"] = license_findings

        critical = [f for f in findings if f["severity"] == "CRITICAL"]
        warnings = [f for f in findings if f["severity"] == "WARNING"]
        if critical:
            return GateResult(self.gate_id, GateVerdict.FAIL,
                              reason=f"{len(critical)} CRITICAL guardrail finding(s): "
                                     + "; ".join(f"{f['file']}:{f['line']} {f['kind']}" for f in critical[:5]),
                              evidence=evidence,
                              constitution_ref="#3/#11 危险操作与不可再生物必须被机械拦截")
        if dep_violations:
            return GateResult(self.gate_id, GateVerdict.FAIL,
                              reason=f"dependencies not in allowlist: {dep_violations}", evidence=evidence)
        if self.fail_on_warning and warnings:
            return GateResult(self.gate_id, GateVerdict.FAIL,
                              reason=f"{len(warnings)} guardrail warning(s)", evidence=evidence)
        return GateResult(self.gate_id, GateVerdict.PASS,
                          reason=f"clean ({scanned} files scanned, {len(warnings)} warnings)",
                          evidence=evidence)
