"""Don't-care selector language and normalisers.

The differential engine is only usable if the spec can say *"this difference is
allowed"*. Research 02/05 is emphatic: without a first-class don't-care
construct every differential run reports defects, the spec inflates to
pseudo-code, and the paradigm collapses (PDR-001 §6).

Selector grammar (deliberately tiny — a big DSL is a new source of ambiguity)::

    selector   := channel [ "." path ]
    channel    := "return" | "stdout" | "stderr" | "exception" | "exit_code"
                | "side_effect" | "resource" | "*"
    path       := segment { "." segment }
    segment    := NAME | "*" | "[" INDEX "]" | "[*]"

Examples::

    return.items[*].id          any element's id under return.items
    return.*                    any top-level field of the return value
    side_effect.cache.*         any cache effect
    stdout                      the whole stdout channel
    *                           everything (use only for R0 scratch units)

Normalisers are a **closed set**. An open set would let a builder-authored
normaliser define away a real difference, which is exactly the reward hacking
the information-asymmetry rules exist to prevent.
"""

from __future__ import annotations

import math
import re
from typing import Any, Callable, Iterable

__all__ = [
    "Selector",
    "NORMALIZERS",
    "apply_normalizer",
    "normalize_observation",
    "DontCareMask",
]

_SEG_RE = re.compile(r"\[(\*|\d+)\]|([^.\[\]]+)")

UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
ISO_TS_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b")
HEXADDR_RE = re.compile(r"0x[0-9a-fA-F]{4,}")


def _segments(path: str) -> list[str]:
    out: list[str] = []
    for m in _SEG_RE.finditer(path):
        idx, name = m.group(1), m.group(2)
        out.append(f"[{idx}]" if idx is not None else name)
    return out


class Selector:
    """A compiled don't-care selector. Matching is pure structure, no eval."""

    __slots__ = ("raw", "channel", "segments")

    def __init__(self, raw: str) -> None:
        self.raw = raw.strip()
        if not self.raw:
            raise ValueError("empty selector")
        head, _, rest = self.raw.partition(".")
        self.channel = head
        self.segments = _segments(rest) if rest else []

    def matches_channel(self, channel: str) -> bool:
        return self.channel in ("*", channel)

    def matches_path(self, path: Iterable[str]) -> bool:
        """Match a concrete path. A selector with no path matches the whole channel."""

        target = list(path)
        if not self.segments:
            return True
        if len(self.segments) != len(target):
            # trailing '*' absorbs the remainder, e.g. 'cache.*'
            if self.segments and self.segments[-1] == "*" and len(target) >= len(self.segments):
                return all(
                    s in ("*", t) for s, t in zip(self.segments[:-1], target[: len(self.segments) - 1])
                )
            return False
        for seg, tgt in zip(self.segments, target):
            if seg == "*" or seg == "[*]":
                continue
            if seg != tgt:
                return False
        return True

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"Selector({self.raw!r})"


def _round(value: Any, digits: int) -> Any:
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        if math.isinf(value):
            return "inf" if value > 0 else "-inf"
        return round(value, digits)
    if isinstance(value, list):
        return [_round(v, digits) for v in value]
    if isinstance(value, dict):
        return {k: _round(v, digits) for k, v in value.items()}
    return value


def _sortable_key(item: Any) -> str:
    from ..contracts.base import canonical_json

    return canonical_json(item)


def _sort_list(value: Any) -> Any:
    if isinstance(value, list):
        return sorted((_sort_list(v) for v in value), key=_sortable_key)
    if isinstance(value, dict):
        return {k: _sort_list(v) for k, v in value.items()}
    return value


def _mask(pattern: re.Pattern[str], token: str) -> Callable[[Any], Any]:
    def run(value: Any) -> Any:
        if isinstance(value, str):
            return pattern.sub(token, value)
        if isinstance(value, list):
            return [run(v) for v in value]
        if isinstance(value, dict):
            return {k: run(v) for k, v in value.items()}
        return value

    return run


def _strip_ws(value: Any) -> Any:
    if isinstance(value, str):
        return re.sub(r"[ \t]+", " ", value).strip()
    if isinstance(value, list):
        return [_strip_ws(v) for v in value]
    if isinstance(value, dict):
        return {k: _strip_ws(v) for k, v in value.items()}
    return value


def _drop(_: Any) -> Any:
    """Total erasure. Used for ``ignorable_output`` don't-care."""

    return "<don't-care>"


def _exception_type_only(value: Any) -> Any:
    """Compare exception *type* but not message.

    Research 4.1: "crash vs graceful error" must be distinguishable, but message
    wording is usually a legitimate freedom. Type is kept, message is dropped.
    """

    if isinstance(value, dict) and "type" in value:
        return {"type": value["type"]}
    if isinstance(value, str):
        return value.split(":", 1)[0].strip()
    return value


#: Closed normaliser set. Extending it is a rule change, not a config tweak.
NORMALIZERS: dict[str, Callable[[Any], Any]] = {
    "identity": lambda v: v,
    "sort_list": _sort_list,
    "round:3": lambda v: _round(v, 3),
    "round:6": lambda v: _round(v, 6),
    "round:9": lambda v: _round(v, 9),
    "mask_uuid": _mask(UUID_RE, "<uuid>"),
    "mask_timestamp": _mask(ISO_TS_RE, "<ts>"),
    "mask_address": _mask(HEXADDR_RE, "<addr>"),
    "strip_whitespace": _strip_ws,
    "exception_type_only": _exception_type_only,
    "drop": _drop,
}


def apply_normalizer(name: str, value: Any) -> Any:
    try:
        fn = NORMALIZERS[name]
    except KeyError as exc:
        raise ValueError(
            f"unknown normalizer {name!r}; the normaliser set is closed "
            f"(available: {sorted(NORMALIZERS)})"
        ) from exc
    return fn(value)


def _walk_apply(
    value: Any,
    selector: Selector,
    fn: Callable[[Any], Any],
    path: list[str] | None = None,
    seen: list[bool] | None = None,
) -> Any:
    """Apply ``fn`` at every location inside ``value`` matched by ``selector``.

    ``seen`` is an out-parameter recording whether the selector matched *any*
    location. Matching and changing are different questions: a region that
    matched but happened to leave the value untouched still governs the
    comparison, and reporting only the changes would understate which freedoms
    a verdict relied on.
    """

    path = path or []
    if selector.matches_path(path):
        if seen is not None:
            seen.append(True)
        return fn(value)
    if isinstance(value, dict):
        return {
            k: _walk_apply(v, selector, fn, path + [str(k)], seen) for k, v in value.items()
        }
    if isinstance(value, list):
        return [
            _walk_apply(v, selector, fn, path + [f"[{i}]"], seen)
            for i, v in enumerate(value)
        ]
    return value


class DontCareMask:
    """Compiled set of don't-care regions, applied before every comparison."""

    def __init__(self, regions: Iterable[Any]) -> None:
        self._compiled: list[tuple[str, Selector, str]] = []
        for region in regions:
            normalizer = getattr(region, "normalizer", None) or self._default_normalizer(
                region
            )
            if normalizer not in NORMALIZERS:
                # Fail at compile time, not at the first comparison: an unknown
                # normaliser discovered mid-run would abort a wave halfway
                # through instead of failing the spec that introduced it.
                raise ValueError(
                    f"unknown normalizer {normalizer!r} in region {region.id!r}; "
                    f"the normaliser set is closed (available: {sorted(NORMALIZERS)})"
                )
            if getattr(region, "track", None) is not None and (
                getattr(region.track, "value", "") == "undefined"
            ):
                # An 'undefined' region marks territory that is out of contract.
                # It must never normalise anything, or reaching forbidden
                # behaviour would be forgiven instead of reported.
                continue
            for raw in getattr(region, "selectors", []) or []:
                self._compiled.append((region.id, Selector(raw), normalizer))

    @staticmethod
    def _default_normalizer(region: Any) -> str:
        """A registered freedom with no explicit normaliser erases the value.

        Rationale: ``output_freedom`` and ``ignorable_output`` both mean "we do
        not constrain this". Defaulting to ``identity`` would silently make the
        region a no-op, i.e. a freedom that is declared but not honoured — the
        worst of both worlds.
        """

        category = getattr(getattr(region, "category", None), "value", "")
        return "sort_list" if category == "output_freedom" else "drop"

    def apply(self, channel: str, value: Any) -> tuple[Any, set[str]]:
        """Return the normalised value plus the region ids that touched it."""

        touched: set[str] = set()
        out = value
        for region_id, selector, normalizer in self._compiled:
            if not selector.matches_channel(channel):
                continue
            fn = NORMALIZERS[normalizer]
            seen: list[bool] = []
            out = _walk_apply(out, selector, fn, None, seen)
            if seen:
                touched.add(region_id)
        return out, touched

    def covering_region(self, channel: str, value_a: Any, value_b: Any) -> str | None:
        """Which single region, if any, makes ``a`` and ``b`` indistinguishable."""

        for region_id, selector, normalizer in self._compiled:
            if not selector.matches_channel(channel):
                continue
            fn = NORMALIZERS[normalizer]
            if _walk_apply(value_a, selector, fn) == _walk_apply(value_b, selector, fn):
                return region_id
        return None

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._compiled)


def normalize_observation(channel: str, value: Any, mask: DontCareMask | None) -> Any:
    """The single normalisation entry point used by every comparison in H5."""

    if mask is None:
        return value
    normalised, _ = mask.apply(channel, value)
    return normalised
