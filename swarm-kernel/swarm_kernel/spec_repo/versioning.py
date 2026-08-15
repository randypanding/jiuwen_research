from __future__ import annotations

import re

from swarm_kernel.contracts.spec import BCClass, ClauseChange, SpecDelta

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def parse_semver(v: str) -> tuple[int, int, int]:
    m = SEMVER_RE.match(v.strip())
    if not m:
        raise ValueError(f"invalid semver: {v}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def next_version(current: str, delta: SpecDelta) -> str:
    major, minor, patch = parse_semver(current)
    classes = {c.bc_class for c in delta.changes}
    ops = {c.op.value for c in delta.changes}
    if BCClass.NBC in classes:
        return f"{major + 1}.0.0"
    if "add" in ops or "modify" in ops:
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def validate_version_policy(current: str, declared_next: str, delta: SpecDelta) -> tuple[bool, str]:
    expected = next_version(current, delta)
    if declared_next == expected:
        return True, ""
    has_nbc = any(c.bc_class == BCClass.NBC for c in delta.changes)
    e_major, _, _ = parse_semver(expected)
    d_major, _, _ = parse_semver(declared_next)
    if has_nbc and d_major <= parse_semver(current)[0]:
        return False, f"NBC changes require major bump: expected {expected}, got {declared_next}"
    return False, f"version policy mismatch: expected {expected}, got {declared_next}"


def classify_change(old_exports: set[str], new_exports: set[str]) -> BCClass:
    removed = old_exports - new_exports
    return BCClass.NBC if removed else BCClass.BC
