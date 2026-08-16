"""SemVer + machine-checked BC/NBC consistency (decision D4, rec_03).

oasdiff-inspired: version bump must match change severity. A breaking
contract change without a major bump is a gate failure (H4).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

_SEMVER = re.compile(r"^\s*(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?\s*$")


@dataclass(frozen=True, order=True)
class SemVer:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, s: str) -> "SemVer":
        m = _SEMVER.match(s)
        if not m:
            raise ValueError(f"invalid SemVer: {s!r}")
        return cls(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def bumped(self, kind: str) -> "SemVer":
        if kind == "major":
            return SemVer(self.major + 1, 0, 0)
        if kind == "minor":
            return SemVer(self.major, self.minor + 1, 0)
        if kind == "patch":
            return SemVer(self.major, self.minor, self.patch + 1)
        raise ValueError(f"unknown bump kind {kind!r}")


def required_bump(has_breaking: bool, has_feature: bool) -> str:
    """YANG-Semver style: breaking -> major, additive -> minor, else patch."""
    if has_breaking:
        return "major"
    if has_feature:
        return "minor"
    return "patch"


@dataclass
class BumpCheck:
    old: SemVer
    new: SemVer
    required: str
    ok: bool
    reason: str


def check_bump(old: str | SemVer, new: str | SemVer, has_breaking: bool, has_feature: bool) -> BumpCheck:
    o = old if isinstance(old, SemVer) else SemVer.parse(old)
    n = new if isinstance(new, SemVer) else SemVer.parse(new)
    req = required_bump(has_breaking, has_feature)
    if n <= o:
        return BumpCheck(o, n, req, False, f"version must increase ({o} -> {n})")
    if req == "major" and (n.major, 0, 0) != (o.major + 1, 0, 0):
        return BumpCheck(o, n, req, False, f"breaking change requires major bump {o.major + 1}.x.x, got {n}")
    if req == "minor" and n.major == o.major and n.minor <= o.minor:
        return BumpCheck(o, n, req, False, f"additive change requires minor bump > {o.minor} on same major, got {n}")
    return BumpCheck(o, n, req, True, f"bump {o} -> {n} satisfies required '{req}'")


def classify_deprecation(old_present: set[str], new_present: set[str],
                         deprecated_state: Optional[dict[str, str]] = None) -> list[str]:
    """Deprecated -> removed must pass through a `deprecated` state with a
    one-minor-version buffer (rec_03 advice 5). Returns violations."""
    deprecated_state = deprecated_state or {}
    violations = []
    for name in sorted(old_present - new_present):
        state = deprecated_state.get(name)
        if state == "deprecated":
            continue  # allowed removal after buffer period
        violations.append(
            f"export {name!r} removed without deprecation buffer (state={state!r})"
        )
    return violations
