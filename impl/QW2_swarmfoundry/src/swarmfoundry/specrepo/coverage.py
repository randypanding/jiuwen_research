from __future__ import annotations

import dataclasses

from swarmfoundry.schema.spec import (
    CLAUSE_ADVISORY,
    CLAUSE_UNVERIFIABLE,
    LEVEL_L1,
    LEVEL_L2,
    SpecDomain,
    WITNESS_JUDGE_RUBRIC,
)


@dataclasses.dataclass(frozen=True)
class CoverageReport:
    domain: str
    total_normative: int
    covered: int
    advisory_only: int
    unverifiable: int
    coverage: float
    unverifiable_ids: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "total_normative": self.total_normative,
            "covered": self.covered,
            "advisory_only": self.advisory_only,
            "unverifiable": self.unverifiable,
            "coverage": self.coverage,
            "unverifiable_ids": list(self.unverifiable_ids),
        }


def witness_coverage(spec: SpecDomain) -> CoverageReport:
    """Gate-algebra obligation: every L1/L2 clause must bind >=1 mechanical
    witness (hard gate or holdout scenario); judge rubric alone demotes the
    clause to advisory; nothing at all marks it unverifiable and it may never
    be used as admission evidence."""
    normative = [c for c in spec.clauses if c.level in (LEVEL_L1, LEVEL_L2)]
    covered = [c for c in normative if c.has_mechanical_witness()]
    advisory = [
        c
        for c in normative
        if not c.has_mechanical_witness() and any(w.kind == WITNESS_JUDGE_RUBRIC for w in c.witnesses)
    ]
    unverifiable = [
        c for c in normative if not c.has_mechanical_witness() and c not in advisory
    ]
    total = len(normative)
    return CoverageReport(
        domain=spec.domain,
        total_normative=total,
        covered=len(covered),
        advisory_only=len(advisory),
        unverifiable=len(unverifiable),
        coverage=(len(covered) / total) if total else 1.0,
        unverifiable_ids=tuple(c.id for c in unverifiable),
    )
