from __future__ import annotations

import ast
import re
import time
from pathlib import Path

from opc.gates.base import Gate, GateContext, check, worst
from opc.schemas.gates import CheckResult, GateReport

SECRET_PATTERNS = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}")),
    ("private_key_block", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("generic_bearer", re.compile(r"""(api[_-]?key|secret|token)\s*[:=]\s*['"][A-Za-z0-9_\-]{24,}['"]""", re.I)),
]

DANGEROUS_CALLS = {
    "eval",
    "exec",
    "compile",
    "pickle.loads",
    "marshal.loads",
    "os.system",
    "subprocess.call",
    "subprocess.run",
    "subprocess.Popen",
    "__import__",
}

TEXT_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".cfg", ".ini", ".sh"}


def scan_secrets(instance_dir: Path) -> list[str]:
    hits: list[str] = []
    for path in sorted(instance_dir.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                hits.append(f"{path.relative_to(instance_dir)}: {name}")
    return hits


def scan_dangerous_calls(instance_dir: Path, extra_deny: set[str]) -> list[str]:
    deny = DANGEROUS_CALLS | extra_deny
    hits: list[str] = []
    for path in sorted(instance_dir.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            hits.append(f"{path.relative_to(instance_dir)}: unparseable")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = ""
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    value = node.func.value
                    parts = []
                    while isinstance(value, ast.Attribute):
                        parts.append(value.attr)
                        value = value.value
                    if isinstance(value, ast.Name):
                        parts.append(value.id)
                    name = ".".join(reversed(parts)) + "." + node.func.attr
                if name in deny:
                    if name in ("subprocess.call", "subprocess.run", "subprocess.Popen"):
                        shell_true = any(
                            kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True
                            for kw in node.keywords
                        )
                        if not shell_true:
                            continue
                    hits.append(f"{path.relative_to(instance_dir)}:{node.lineno} {name}")
    return hits


def declared_dependencies(instance_dir: Path) -> set[str]:
    deps: set[str] = set()
    req = instance_dir / "requirements.txt"
    if req.exists():
        for line in req.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                deps.add(re.split(r"[<>=!~;\[ ]", line, 1)[0].lower())
    pyproject = instance_dir / "pyproject.toml"
    if pyproject.exists():
        try:
            import tomllib

            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            for dep in data.get("project", {}).get("dependencies", []):
                deps.add(re.split(r"[<>=!~;\[ ]", dep, 1)[0].lower())
        except Exception:  # noqa: BLE001
            pass
    return deps


class H6ConstitutionGate(Gate):
    """H6: the mechanizable projection of the constitution.

    Scans for leaked secrets, denied dangerous calls, and banned
    dependencies. Runtime sandbox boundaries are enforced by jiuwenbox +
    permission rails on the harness side; this gate is the static witness.
    """

    gate_id = "H6"

    def run(self, ctx: GateContext) -> GateReport:
        started = time.monotonic()
        checks: list[CheckResult] = []
        policy = ctx.policy().get("constitution", {})

        secrets = scan_secrets(ctx.instance_dir)
        checks.append(check("h6.secrets", not secrets, f"secret material detected: {secrets[:5]}"))

        dangerous = scan_dangerous_calls(ctx.instance_dir, set(policy.get("dangerous_calls_deny", [])))
        checks.append(
            check("h6.dangerous_calls", not dangerous, f"denied calls present: {dangerous[:8]}")
        )

        denylist = {d.lower() for d in policy.get("dependency_denylist", [])}
        bad_deps = sorted(declared_dependencies(ctx.instance_dir) & denylist)
        checks.append(check("h6.dependency_policy", not bad_deps, f"banned dependencies: {bad_deps}"))

        return self.report(ctx, worst([c.status for c in checks]), checks, started)
