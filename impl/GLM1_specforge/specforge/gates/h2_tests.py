"""H2: unit/property tests + oracle signal strength audit (mutation).

Constitution-relevant: an agent-written test suite with weak assertions is
worthless ("All Smoke No Alarm"). We run pytest, then run a small deterministic
mutation audit over the unit's artifacts: each mutant MUST be killed by the
suite or the mutation score drops below threshold -> FAIL.
"""
from __future__ import annotations

import ast
import random
from pathlib import Path
from typing import Any, Optional

from .base import GateContext, GateResult, GateVerdict
from .shell import run_command

# --- deterministic source mutation -----------------------------------------

_MUTATIONS = [
    ("Add", "Sub"), ("Sub", "Add"), ("Mult", "Add"), ("Div", "Mult"),
    ("Lt", "LtE"), ("LtE", "Lt"), ("Gt", "GtE"), ("GtE", "Gt"),
    ("Eq", "NotEq"), ("NotEq", "Eq"), ("And", "Or"), ("Or", "And"),
]


def _code_only(line: str) -> str:
    """Strip comments and string literal contents so operator tokens inside
    strings/comments are never mutated (avoids trivially-equivalent mutants)."""
    if "#" in line:
        # naive: only strip comment when # is not inside quotes
        code = line
        in_s = in_d = False
        for i, ch in enumerate(code):
            if ch == '"' and not in_s:
                in_d = not in_d
            elif ch == "'" and not in_d:
                in_s = not in_s
            elif ch == "#" and not in_s and not in_d:
                code = code[:i]
                break
        line = code
    import re

    line = re.sub(r'"[^"]*"', '""', line)
    line = re.sub(r"'[^']*'", "''", line)
    return line


def generate_mutants(source: str, max_mutants: int = 8, seed: int = 0,
                     only_anchored: bool = False) -> list[tuple[int, str, str, str]]:
    """Return [(lineno, op_old, op_new, mutated_source)] deterministic under seed.

    Textual single-token operator replacement per candidate line, validated by
    re-parsing the mutated source. Deterministic: candidates shuffled by seeded
    RNG, first per line wins. Lines whose operator tokens only appear inside
    strings/comments are skipped.

    only_anchored=True restricts mutations to lines carrying `spec:` trace
    anchors: we audit oracle strength exactly where spec claims coverage.
    Falls back to all lines when the file has no anchors.
    """
    lines = source.splitlines(keepends=True)
    anchored = [i for i, ln in enumerate(lines, start=1) if "spec:" in ln]
    if only_anchored and anchored:
        allowed = set(anchored)
    else:
        allowed = set(range(1, len(lines) + 1))
    candidates: list[tuple[int, str, str]] = []
    for i, line in enumerate(lines, start=1):
        if i not in allowed:
            continue
        code = _code_only(line)
        for o, n in _MUTATIONS:
            to, tn = _op_token(o), _op_token(n)
            if to and to in code:
                candidates.append((i, o, n))
                break
    if not candidates:
        return []
    rng = random.Random(seed)
    rng.shuffle(candidates)
    picked: list[tuple[int, str, str]] = []
    seen: set[int] = set()
    for lineno, o, n in candidates:
        if lineno in seen:
            continue
        picked.append((lineno, o, n))
        seen.add(lineno)
        if len(picked) >= max_mutants:
            break
    out: list[tuple[int, str, str, str]] = []
    for lineno, o, n in picked:
        mutated_lines = list(lines)
        to, tn = _op_token(o), _op_token(n)
        mutated_lines[lineno - 1] = lines[lineno - 1].replace(to, tn, 1)
        mutated_src = "".join(mutated_lines)
        try:
            ast.parse(mutated_src)
        except SyntaxError:
            continue
        out.append((lineno, o, n, mutated_src))
    return out


_TOKENS = {
    "Add": "+", "Sub": "-", "Mult": "*", "Div": "/", "Lt": "<", "LtE": "<=",
    "Gt": ">", "GtE": ">=", "Eq": "==", "NotEq": "!=", "And": "and", "Or": "or",
}


def _op_token(opname: str) -> Optional[str]:
    return _TOKENS.get(opname)


class H2TestsGate:
    gate_id = "h2"
    description = "unit/property tests + mutation-based oracle strength audit"
    hard = True

    def __init__(self, test_args: Optional[list[str]] = None, timeout: float = 600.0,
                 mutation_score_threshold: float = 0.7, max_mutants: int = 6,
                 mutation_seed: int = 0, enable_mutation: bool = True):
        self.test_args = test_args
        self.timeout = timeout
        self.threshold = mutation_score_threshold
        self.max_mutants = max_mutants
        self.mutation_seed = mutation_seed
        self.enable_mutation = enable_mutation

    def applicable(self, ctx: GateContext) -> bool:
        return True

    def run(self, ctx: GateContext) -> GateResult:
        argv = ["pytest", "-q", "--no-header", "-x"]
        if self.test_args:
            argv = ["pytest", *self.test_args]
        try:
            res = run_command(argv, cwd=ctx.instance_path, timeout=self.timeout,
                              env={"PYTHONDONTWRITEBYTECODE": "1"})
        except PermissionError as e:
            return GateResult(self.gate_id, GateVerdict.INCONCLUSIVE, reason=str(e))
        ev: dict[str, Any] = {
            "pytest": {"returncode": res.returncode, "timed_out": res.timed_out,
                       "stdout_tail": res.stdout[-3000:]}
        }
        if res.timed_out:
            return GateResult(self.gate_id, GateVerdict.FAIL, reason="pytest timed out", evidence=ev)
        if res.returncode != 0:
            return GateResult(self.gate_id, GateVerdict.FAIL,
                              reason=f"pytest exited {res.returncode}", evidence=ev)

        if not self.enable_mutation:
            return GateResult(self.gate_id, GateVerdict.PASS, evidence=ev)

        # ---- mutation audit -------------------------------------------------
        artifacts = (ctx.spec_unit.artifacts if ctx.spec_unit else None) or ctx.config.get("artifacts") or []
        score, detail = self._mutation_audit(ctx, artifacts)
        ev["mutation"] = detail
        if score is None:
            return GateResult(self.gate_id, GateVerdict.INCONCLUSIVE,
                              reason="mutation audit produced no valid mutants (cannot certify oracle strength)",
                              evidence=ev,
                              constitution_ref="#3 无机械见证的条款只能否决，不能放行")
        if score < self.threshold:
            return GateResult(self.gate_id, GateVerdict.FAIL,
                              reason=(f"mutation score {score:.2f} < {self.threshold}: "
                                      "tests do not kill injected defects (weak oracle)"),
                              evidence=ev)
        return GateResult(self.gate_id, GateVerdict.PASS, evidence=ev)

    def _mutation_audit(self, ctx: GateContext, artifacts: list[str]) -> tuple[Optional[float], dict]:
        detail: dict[str, Any] = {"mutants": []}
        total = killed = 0
        root = Path(ctx.instance_path)
        py_files: list[Path] = []
        for pattern in artifacts:
            if pattern.endswith(".py"):
                p = root / pattern
                if p.exists():
                    py_files.append(p)
            else:
                py_files.extend(root.glob(pattern if pattern.endswith(".py") else pattern + "/*.py"))
        if not py_files:
            py_files = sorted(root.rglob("*.py"))
        py_files = [p for p in py_files if "test" not in p.name][:4]

        for py in py_files:
            try:
                source = py.read_text(encoding="utf-8")
            except OSError:
                continue
            mutants = generate_mutants(source, max_mutants=self.max_mutants,
                                       seed=self.mutation_seed, only_anchored=True)
            backup = source
            for lineno, old, new, mutated_src in mutants:
                total += 1
                py.write_text(mutated_src, encoding="utf-8")
                try:
                    res = run_command(["pytest", "-q", "--no-header", "-x"], cwd=ctx.instance_path,
                                      timeout=self.timeout, env={"PYTHONDONTWRITEBYTECODE": "1"})
                    survived = (res.returncode == 0 and not res.timed_out)
                finally:
                    py.write_text(backup, encoding="utf-8")
                if not survived:
                    killed += 1
                detail["mutants"].append({"file": str(py.relative_to(root)), "line": lineno,
                                          "old": old, "new": new, "killed": not survived})
        score = (killed / total) if total else None
        detail["score"] = score
        detail["killed"] = killed
        detail["total"] = total
        return score, detail
