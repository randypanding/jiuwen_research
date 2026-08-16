from __future__ import annotations

import dataclasses

from swarmfoundry.schema import SCHEMA_VERSION
from swarmfoundry.schema.base import check_schema_version, require

DOWNGRADE_ESCAPE_DEFECT = "escape_defect_rate"
DOWNGRADE_JUDGE_KAPPA = "judge_calibration_kappa"
DOWNGRADE_DRIFT_STORM = "drift_storm"
DOWNGRADE_COST_OVERRUN = "cost_overrun"
DOWNGRADE_ORACLE_CONFLICT = "oracle_conflict"


@dataclasses.dataclass(frozen=True)
class HealthMetrics:
    """Contract C12. All seven core indicators of structure.md §13."""

    window: str
    closure_rate: float
    spec_entropy: float
    witness_coverage: float
    unverifiable_clauses: int
    escape_defect_rate: float
    drift_alerts: int
    drift_fix_latency_h: float
    judge_kappa: float
    judge_abstain_rate: float
    rework_rate: float
    unit_admission_cost: float
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "window": self.window,
            "closure_rate": self.closure_rate,
            "spec_entropy": self.spec_entropy,
            "witness_coverage": self.witness_coverage,
            "unverifiable_clauses": self.unverifiable_clauses,
            "escape_defect_rate": self.escape_defect_rate,
            "drift_alerts": self.drift_alerts,
            "drift_fix_latency_h": self.drift_fix_latency_h,
            "judge_kappa": self.judge_kappa,
            "judge_abstain_rate": self.judge_abstain_rate,
            "rework_rate": self.rework_rate,
            "unit_admission_cost": self.unit_admission_cost,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HealthMetrics":
        where = "HealthMetrics"
        check_schema_version(data, where)
        return cls(
            window=require(data, "window", str, where),
            closure_rate=float(require(data, "closure_rate", float, where)),
            spec_entropy=float(require(data, "spec_entropy", float, where)),
            witness_coverage=float(require(data, "witness_coverage", float, where)),
            unverifiable_clauses=require(data, "unverifiable_clauses", int, where),
            escape_defect_rate=float(require(data, "escape_defect_rate", float, where)),
            drift_alerts=require(data, "drift_alerts", int, where),
            drift_fix_latency_h=float(require(data, "drift_fix_latency_h", float, where)),
            judge_kappa=float(require(data, "judge_kappa", float, where)),
            judge_abstain_rate=float(require(data, "judge_abstain_rate", float, where)),
            rework_rate=float(require(data, "rework_rate", float, where)),
            unit_admission_cost=float(require(data, "unit_admission_cost", float, where)),
        )


@dataclasses.dataclass(frozen=True)
class Thresholds:
    escape_defect_rate_max: float = 0.02
    judge_kappa_min: float = 0.6
    drift_alerts_max_per_window: int = 5
    unit_admission_cost_max: float = 1000.0
    closure_rate_min: float = 0.5


def evaluate_downgrades(m: HealthMetrics, t: Thresholds) -> list[str]:
    out: list[str] = []
    if m.escape_defect_rate > t.escape_defect_rate_max:
        out.append(DOWNGRADE_ESCAPE_DEFECT)
    if m.judge_kappa < t.judge_kappa_min:
        out.append(DOWNGRADE_JUDGE_KAPPA)
    if m.drift_alerts > t.drift_alerts_max_per_window:
        out.append(DOWNGRADE_DRIFT_STORM)
    if m.unit_admission_cost > t.unit_admission_cost_max and m.closure_rate < t.closure_rate_min:
        out.append(DOWNGRADE_COST_OVERRUN)
    return out
