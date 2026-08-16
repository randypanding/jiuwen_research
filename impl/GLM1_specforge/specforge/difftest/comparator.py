"""Pairwise output comparison with don't-care region classification."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import Any, Optional

from .normalizer import NormalizeRules, normalize

EQUAL = "EQUAL"
DIFF = "DIFF"
DIFF_IN_DONT_CARE = "DIFF_IN_DONT_CARE"   # divergence matches registered unspecified region
DIFF_IN_UNDEFINED = "DIFF_IN_UNDEFINED"   # divergence crosses an `undefined` boundary -> defect


@dataclass
class FieldDiff:
    path: str
    a: Any
    b: Any

    def to_dict(self) -> dict:
        return {"path": self.path, "a": self.a, "b": self.b}


@dataclass
class CompareOutcome:
    verdict: str
    diffs: list[FieldDiff] = field(default_factory=list)
    dc_hits: list[str] = field(default_factory=list)

    @property
    def equal(self) -> bool:
        return self.verdict == EQUAL


def _flatten(obj: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    else:
        out[prefix or "<root>"] = obj
    return out


# Only these kinds mark a region as don't-care. Any other registered kind
# (e.g. a type constraint like "int") is a spec annotation, not a DC region.
VALID_DC_KINDS = frozenset({"unspecified", "undefined", "unreachable"})


def match_dc_region(path: str, dc_regions: dict[str, str]) -> Optional[str]:
    """dc_regions: region-pattern -> kind. Patterns are fnmatch on dotted paths;
    a trailing `.*` also covers the bare prefix (field + its children)."""
    for pattern, kind in dc_regions.items():
        if kind not in VALID_DC_KINDS:
            continue
        if fnmatch.fnmatch(path, pattern):
            return kind
        if pattern.endswith(".*") and fnmatch.fnmatch(path, pattern[:-2]):
            return kind
    return None


def compare_outputs(a: Any, b: Any, rules: NormalizeRules,
                    dc_regions: Optional[dict[str, str]] = None) -> CompareOutcome:
    dc_regions = dc_regions or {}
    na, nb = normalize(a, rules), normalize(b, rules)
    if na == nb:
        return CompareOutcome(EQUAL)
    fa, fb = _flatten(na), _flatten(nb)
    paths = sorted(set(fa) | set(fb))
    diffs: list[FieldDiff] = []
    dc_hits: list[str] = []
    in_undefined = False
    for p in paths:
        va, vb = fa.get(p, "<ABSENT>"), fb.get(p, "<ABSENT>")
        if va != vb:
            diffs.append(FieldDiff(p, va, vb))
            kind = match_dc_region(p, dc_regions)
            if kind == "undefined":
                in_undefined = True
            elif kind is not None:
                dc_hits.append(p)
    if in_undefined:
        return CompareOutcome(DIFF_IN_UNDEFINED, diffs, dc_hits)
    if dc_hits and len(dc_hits) == len(diffs):
        return CompareOutcome(DIFF_IN_DONT_CARE, diffs, dc_hits)
    return CompareOutcome(DIFF, diffs, dc_hits)
