"""Output normalization before comparison (R3 research: matcher/redaction layers)."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class NormalizeRules:
    float_rel_tol: float = 1e-9
    sort_dict_keys: bool = True
    sort_lists: bool = False          # order-insensitive collections (declare per-unit!)
    strip_fields: list[str] = field(default_factory=list)   # e.g. ["duration", "timestamp"]
    redact_patterns: list[str] = field(default_factory=list)  # regex -> "<REDACTED>"
    trim_strings: bool = True
    drop_keys_matching: list[str] = field(default_factory=list)  # fnmatch patterns

    def to_dict(self) -> dict[str, Any]:
        return {
            "float_rel_tol": self.float_rel_tol,
            "sort_dict_keys": self.sort_dict_keys,
            "sort_lists": self.sort_lists,
            "strip_fields": self.strip_fields,
            "redact_patterns": self.redact_patterns,
            "trim_strings": self.trim_strings,
            "drop_keys_matching": self.drop_keys_matching,
        }


def normalize(value: Any, rules: NormalizeRules) -> Any:
    redactors = [re.compile(p) for p in rules.redact_patterns]
    import fnmatch

    def walk(v: Any, key: Optional[str] = None) -> Any:
        if key is not None:
            if key in rules.strip_fields:
                return "<DROPPED>"
            for pat in rules.drop_keys_matching:
                if fnmatch.fnmatch(key, pat):
                    return "<DROPPED>"
        if isinstance(v, bool) or v is None:
            return v
        if isinstance(v, float):
            if math.isnan(v):
                return "<NaN>"
            if math.isinf(v):
                return "<Inf+>" if v > 0 else "<Inf->"
            if v == 0:
                return 0.0  # unify -0.0
            # relative-tolerance quantization: 9 significant digits
            return float(f"{v:.8e}")
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            s = v.strip() if rules.trim_strings else v
            for rx in redactors:
                s = rx.sub("<REDACTED>", s)
            return s
        if isinstance(v, dict):
            items = ((k, walk(x, k)) for k, x in v.items())
            return dict(sorted(items) if rules.sort_dict_keys else items)
        if isinstance(v, (list, tuple)):
            walked = [walk(x) for x in v]
            return sorted(walked, key=repr) if rules.sort_lists else walked
        return f"<{type(v).__name__}:{v!r}>"

    return walk(value)


def floats_close(a: float, b: float, rel_tol: float) -> bool:
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=1e-12)
