"""Oracle strength audit — grade the oracle before trusting the gate.

The single most load-bearing number in the whole platform is *"the gate
passed"*. That number is worthless if the oracle behind the gate asserts
nothing. Measured rates of assertion-free machine-written tests are high enough
(research 01) that an un-audited oracle must be assumed vacuous.

Grades (execution-level, PDR-001-aligned):

===========  ==========================================================
Bronze       runs without crashing; asserts *something*
Silver       + dual criterion: proves the fix AND proves nothing else broke
Gold         + bound to a spec clause, and covers the clause's stated cases
Diamond      + survives mutation probing: every probe is *killed*
===========  ==========================================================

A Diamond oracle is one that has demonstrated it can fail. Nothing below
Diamond may be the sole evidence for an R2/R3 admission.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Mapping, Sequence

from ..contracts.oracle import (
    MutationProbe,
    OracleBundle,
    OracleGrade,
    Scenario,
)

__all__ = ["StrengthReport", "OracleAuditor", "MutationOutcome", "run_mutation_probes"]


@dataclass(frozen=True)
class MutationOutcome:
    probe_id: str
    killed: bool
    killed_by: tuple[str, ...] = ()
    message: str = ""


@dataclass
class StrengthReport:
    bundle_id: str
    grade: OracleGrade
    reasons: list[str] = field(default_factory=list)
    assertion_rate: float = 0.0
    dual_criterion: bool = False
    clause_coverage: float = 0.0
    mutation_score: float = 0.0
    surviving_probes: list[str] = field(default_factory=list)

    @property
    def is_vacuous(self) -> bool:
        return self.assertion_rate < 1.0

    def at_least(self, grade: OracleGrade) -> bool:
        return self.grade.rank >= grade.rank


def _asserts_something(scenario: Scenario) -> bool:
    return bool(scenario.expect)


def run_mutation_probes(
    probes: Sequence[MutationProbe],
    runner: Callable[[MutationProbe], Iterable[str]],
) -> list[MutationOutcome]:
    """Run each probe; ``runner`` returns the ids of scenarios that failed.

    A probe injects a defect the oracle *claims* to catch. If no scenario fails,
    the oracle does not actually catch it — the probe survives, and the oracle's
    claim is false. This is the only mechanical anti-vacuity instrument that
    does not itself need to be trusted.
    """

    out: list[MutationOutcome] = []
    for probe in probes:
        failing = tuple(sorted(runner(probe)))
        expected = set(probe.must_be_caught_by)
        killed = bool(failing) and (not expected or bool(expected & set(failing)))
        out.append(
            MutationOutcome(
                probe_id=probe.id,
                killed=killed,
                killed_by=failing,
                message=""
                if killed
                else "probe survived: the oracle does not detect the defect it claims to",
            )
        )
    return out


class OracleAuditor:
    """Grades an :class:`OracleBundle`. Pure function of its inputs."""

    def __init__(self, min_clause_coverage: float = 1.0, min_mutation_score: float = 1.0):
        self.min_clause_coverage = min_clause_coverage
        self.min_mutation_score = min_mutation_score

    def audit(
        self,
        bundle: OracleBundle,
        *,
        clause_ids: Iterable[str] = (),
        mutation_outcomes: Sequence[MutationOutcome] = (),
        regression_scenarios: Mapping[str, bool] | None = None,
    ) -> StrengthReport:
        scenarios = list(bundle.holdout.scenarios)
        reasons: list[str] = []

        if not scenarios:
            return StrengthReport(
                bundle_id=bundle.bundle_id,
                grade=OracleGrade.BRONZE,
                reasons=["bundle contains no scenarios"],
            )

        asserting = [s for s in scenarios if _asserts_something(s)]
        assertion_rate = len(asserting) / len(scenarios)
        if assertion_rate < 1.0:
            silent = [s.id for s in scenarios if not _asserts_something(s)]
            reasons.append(f"scenarios that assert nothing: {sorted(silent)}")

        # Dual criterion (SWE-bench FAIL_TO_PASS + PASS_TO_PASS): the change must
        # make the target scenarios pass *and* leave the regression set passing.
        regression = regression_scenarios or {}
        dual = bool(regression) and all(regression.values())
        if regression and not dual:
            reasons.append(
                "regression scenarios (PASS_TO_PASS) are failing: "
                f"{sorted(k for k, v in regression.items() if not v)}"
            )
        elif not regression:
            reasons.append("no regression scenario set declared (PASS_TO_PASS missing)")

        wanted = set(clause_ids)
        bound: set[str] = set()
        for s in scenarios:
            bound.update(s.clause_ids)
        for prop in bundle.public.properties:
            bound.update(prop.clause_ids)
        for mr in bundle.public.metamorphic:
            bound.update(mr.clause_ids)
        clause_coverage = (len(wanted & bound) / len(wanted)) if wanted else 1.0
        if wanted and clause_coverage < self.min_clause_coverage:
            reasons.append(f"clauses with no oracle: {sorted(wanted - bound)}")

        if mutation_outcomes:
            killed = sum(1 for m in mutation_outcomes if m.killed)
            mutation_score = killed / len(mutation_outcomes)
        else:
            mutation_score = 0.0
        surviving = [m.probe_id for m in mutation_outcomes if not m.killed]
        if surviving:
            reasons.append(f"surviving mutation probes: {sorted(surviving)}")
        elif not mutation_outcomes:
            reasons.append("no mutation probes were run; Diamond is unattainable")

        grade = OracleGrade.BRONZE
        if assertion_rate >= 1.0:
            if dual:
                grade = OracleGrade.SILVER
                if clause_coverage >= self.min_clause_coverage:
                    grade = OracleGrade.GOLD
                    if mutation_outcomes and mutation_score >= self.min_mutation_score:
                        grade = OracleGrade.DIAMOND

        return StrengthReport(
            bundle_id=bundle.bundle_id,
            grade=grade,
            reasons=reasons,
            assertion_rate=assertion_rate,
            dual_criterion=dual,
            clause_coverage=clause_coverage,
            mutation_score=mutation_score,
            surviving_probes=sorted(surviving),
        )
