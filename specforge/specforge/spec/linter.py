"""Spec linter: constitution-grade structural checks (WP1).

Enforced rules:
  SPEC001 clause ids unique and non-empty (auto-assigned if absent)
  SPEC002 L1/L2 clauses must bind a mechanical witness; otherwise marked
          `unverifiable` -> advisory_only (may veto, never clear)
  SPEC003 witness must reference a registered gate id or holdout set id
  SPEC004 r_level valid; artifacts non-empty for L2-bearing units
  SPEC005 version parses as SemVer
  SPEC006 dontcare ids unique, kinds valid (parser checks kind)
  SPEC007 depends reference known unit ids (when unit index provided)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from .parser import parse_spec
from .schema import Clause, LintError, SpecUnit


@dataclass
class LintReport:
    errors: list[LintError] = field(default_factory=list)
    auto_ids: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors


def _auto_id(unit: SpecUnit, level: str, seq: int) -> str:
    short = unit.spec_id.rsplit(".", 1)[-1].replace("-", "_").upper()
    return f"REQ-{short}-{level}-{seq}"


def lint_spec(
    unit: SpecUnit,
    gate_ids: Optional[Iterable[str]] = None,
    holdout_ids: Optional[Iterable[str]] = None,
    known_unit_ids: Optional[Iterable[str]] = None,
) -> LintReport:
    rep = LintReport()
    gate_ids = set(gate_ids or ())
    holdout_ids = set(holdout_ids or ())
    seen_ids: set[str] = set()
    counters: dict[str, int] = {}

    for cl in unit.clauses:
        level = cl.level
        counters[level] = counters.get(level, 0) + 1
        if not cl.clause_id:
            cl.clause_id = _auto_id(unit, level, counters[level])
            rep.auto_ids += 1
        if cl.clause_id in seen_ids:
            rep.errors.append(LintError("SPEC001", f"duplicate clause id {cl.clause_id}", unit.spec_id))
        seen_ids.add(cl.clause_id)

        if level in ("L1", "L2"):
            if cl.witness is None:
                cl.advisory_only = True
                rep.errors.append(
                    LintError(
                        "SPEC002",
                        f"clause {cl.clause_id} has no mechanical witness; "
                        "marked unverifiable/advisory (constitution #3: cannot clear)",
                        unit.spec_id,
                    )
                )
            else:
                valid = (
                    cl.witness.kind == "gate" and cl.witness.ref in gate_ids
                ) or (cl.witness.kind == "holdout" and cl.witness.ref in holdout_ids)
                if gate_ids or holdout_ids:  # only check when a registry was provided
                    if not valid:
                        rep.errors.append(
                            LintError(
                                "SPEC003",
                                f"clause {cl.clause_id} witness {cl.witness.as_ref()} "
                                "not found in gate/holdout registry",
                                unit.spec_id,
                            )
                        )

    if unit.clauses_by_level("L2") and not unit.artifacts:
        rep.errors.append(LintError("SPEC004", "L2 contract clauses require `artifacts`", unit.spec_id))

    try:
        from .semver import SemVer

        SemVer.parse(unit.version)
    except ValueError as e:
        rep.errors.append(LintError("SPEC005", str(e), unit.spec_id))

    dc_ids: set[str] = set()
    for dc in unit.dont_cares:
        if dc.dc_id and dc.dc_id in dc_ids:
            rep.errors.append(LintError("SPEC006", f"duplicate dontcare id {dc.dc_id}", unit.spec_id))
        dc_ids.add(dc.dc_id)

    if known_unit_ids is not None:
        known = set(known_unit_ids)
        for dep in unit.depends:
            if dep not in known and dep != unit.spec_id:
                rep.errors.append(LintError("SPEC007", f"unknown dependency {dep!r}", unit.spec_id))

    return rep


def load_and_lint(path: str, **kw) -> tuple[SpecUnit, LintReport]:
    unit = parse_spec(path=path)
    rep = lint_spec(unit, **kw)
    return unit, rep


def machine_clause_coverage(unit: SpecUnit) -> float:
    """Fraction of L1/L2 clauses with a mechanical witness (metrics: 判据覆盖率)."""
    mach = unit.machine_clauses()
    if not mach:
        return 1.0
    bound = sum(1 for c in mach if c.witness is not None)
    return bound / len(mach)


def advisory_clauses(unit: SpecUnit) -> list[Clause]:
    return [c for c in unit.machine_clauses() if c.advisory_only]
