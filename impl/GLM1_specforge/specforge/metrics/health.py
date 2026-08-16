"""Health metrics + human-facing report (WP9, D17).

Human interface contains ONLY: L1/L2 matters, improvement proposals, health
score. It must NOT contain code diffs, instance choices, tier changes, or
per-case exceptions (PDR-001 section 9).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class WaveMetrics:
    wave_id: str
    spec_id: str
    n_instances: int
    measurement_verdict: str
    divergences: int = 0
    gates_failed: list[str] = field(default_factory=list)
    escape_suspected: bool = False
    judge_kappa: Optional[float] = None
    mutation_score: Optional[float] = None
    cost_usd: float = 0.0
    wall_s: float = 0.0
    admitted: bool = False
    at: float = field(default_factory=time.time)


DEFAULT_THRESHOLDS = {
    "closure_min": 0.5,          # M1 entry
    "entropy_max": 0.4,          # divergence events per delta
    "coverage_min": 0.9,         # witness-bound clause ratio (M1 entry)
    "escape_rate_max": 0.02,
    "kappa_min": 0.6,
    "cost_per_admission_max": 25.0,
    "drift_alarm_max": 0.2,
}


@dataclass
class HealthReport:
    waves: int = 0
    admissions: int = 0
    closures: int = 0                     # CLOSED verdicts
    silence_events: int = 0               # SILENCE + SILENCE_DC
    ambiguity_events: int = 0             # AMBIGUOUS + CONFLICT
    clause_coverage: float = 1.0
    unverifiable_clauses: int = 0
    mutation_score_avg: Optional[float] = None
    judge_kappa: Optional[float] = None
    escape_rate: float = 0.0
    drift_alarm_rate: float = 0.0
    total_cost_usd: float = 0.0
    degradations: list[str] = field(default_factory=list)

    @property
    def closure(self) -> float:
        return self.closures / self.waves if self.waves else 1.0

    @property
    def spec_entropy(self) -> float:
        """Divergence events per wave (lower is better)."""
        return (self.silence_events + self.ambiguity_events) / self.waves if self.waves else 0.0

    @property
    def cost_per_admission(self) -> float:
        return self.total_cost_usd / self.admissions if self.admissions else 0.0

    @property
    def health_score(self) -> float:
        """Weighted 0..1 score; degradation triggers reduce it."""
        score = (
            0.3 * self.closure
            + 0.2 * min(1.0, self.clause_coverage / DEFAULT_THRESHOLDS["coverage_min"])
            + 0.2 * max(0.0, 1.0 - self.spec_entropy)
            + 0.1 * (self.judge_kappa if self.judge_kappa is not None else 1.0)
            + 0.1 * (1.0 if self.mutation_score_avg is None else self.mutation_score_avg)
            + 0.1 * max(0.0, 1.0 - self.escape_rate / DEFAULT_THRESHOLDS["escape_rate_max"])
        )
        return round(max(0.0, min(1.0, score - 0.1 * len(self.degradations))), 3)

    def to_dict(self) -> dict[str, Any]:
        return {
            "waves": self.waves, "admissions": self.admissions, "closure": self.closure,
            "spec_entropy": self.spec_entropy, "clause_coverage": self.clause_coverage,
            "unverifiable_clauses": self.unverifiable_clauses,
            "silence_events": self.silence_events, "ambiguity_events": self.ambiguity_events,
            "mutation_score_avg": self.mutation_score_avg, "judge_kappa": self.judge_kappa,
            "escape_rate": self.escape_rate, "drift_alarm_rate": self.drift_alarm_rate,
            "total_cost_usd": self.total_cost_usd,
            "cost_per_admission": self.cost_per_admission,
            "health_score": self.health_score, "degradations": self.degradations,
        }


class HealthTracker:
    def __init__(self):
        self.records: list[WaveMetrics] = []

    def record_wave(self, m: WaveMetrics) -> WaveMetrics:
        self.records.append(m)
        return m

    def snapshot(self, clause_coverage: float = 1.0, unverifiable: int = 0,
                 drift_alarm_rate: float = 0.0) -> HealthReport:
        rep = HealthReport(clause_coverage=clause_coverage, unverifiable_clauses=unverifiable,
                           drift_alarm_rate=drift_alarm_rate)
        rep.waves = len(self.records)
        kappas: list[float] = []
        muts: list[float] = []
        escapes = 0
        for m in self.records:
            if m.admitted:
                rep.admissions += 1
            rep.total_cost_usd += m.cost_usd
            if m.measurement_verdict == "CLOSED":
                rep.closures += 1
            elif m.measurement_verdict in ("SILENCE", "SILENCE_DC"):
                rep.silence_events += 1
            elif m.measurement_verdict in ("AMBIGUOUS", "CONFLICT"):
                rep.ambiguity_events += 1
            if m.judge_kappa is not None:
                kappas.append(m.judge_kappa)
            if m.mutation_score is not None:
                muts.append(m.mutation_score)
            if m.escape_suspected:
                escapes += 1
        rep.judge_kappa = min(kappas) if kappas else None
        rep.mutation_score_avg = sum(muts) / len(muts) if muts else None
        rep.escape_rate = escapes / rep.waves if rep.waves else 0.0
        rep.degradations = evaluate_degradation(rep)
        return rep


def evaluate_degradation(rep: HealthReport,
                         thresholds: Optional[dict[str, float]] = None) -> list[str]:
    th = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    triggers: list[str] = []
    if rep.escape_rate > th["escape_rate_max"]:
        triggers.append(f"escape rate {rep.escape_rate:.3f} > {th['escape_rate_max']}: "
                        "oracle untrusted -> fall back one stage, require extra L2 confirmation")
    if rep.judge_kappa is not None and rep.judge_kappa < th["kappa_min"]:
        triggers.append(f"judge kappa {rep.judge_kappa:.2f} < {th['kappa_min']}: "
                        "disable soft gates, pause auto admission in this domain")
    if rep.drift_alarm_rate > th["drift_alarm_max"]:
        triggers.append("drift storm: freeze fan-out, switch to calibration pipeline B")
    if rep.cost_per_admission > th["cost_per_admission_max"] and rep.closure < th["closure_min"]:
        triggers.append("cost over budget without closure gain: reduce N, shrink unit, raise tier floor")
    if rep.waves >= 3 and rep.ambiguity_events >= rep.waves:
        triggers.append("oracle-vs-spec repeated conflict: escalate to human spec-level issue")
    return triggers


def render_human_report(rep: HealthReport, l1_l2_matters: Optional[list[str]] = None,
                        proposals: Optional[list[str]] = None) -> str:
    """Human-facing surface: L1/L2 matters + proposals + health score ONLY."""
    lines = ["# SpecForge Health Report (human interface)", ""]
    lines.append(f"- health score: {rep.health_score}")
    lines.append(f"- waves: {rep.waves} | admissions: {rep.admissions} | "
                 f"closure: {rep.closure:.2f} | spec entropy: {rep.spec_entropy:.2f}")
    lines.append(f"- clause coverage: {rep.clause_coverage:.2f} "
                 f"(unverifiable: {rep.unverifiable_clauses})")
    if rep.judge_kappa is not None:
        lines.append(f"- judge kappa: {rep.judge_kappa:.2f}")
    if rep.mutation_score_avg is not None:
        lines.append(f"- mutation score avg: {rep.mutation_score_avg:.2f}")
    lines.append(f"- cost/admission: ${rep.cost_per_admission:.2f}")
    if l1_l2_matters:
        lines += ["", "## L1/L2 matters needing human attention"]
        lines += [f"- {m}" for m in l1_l2_matters]
    if proposals:
        lines += ["", "## Improvement proposals (deep agent; effective next session only)"]
        lines += [f"- {p}" for p in proposals]
    if rep.degradations:
        lines += ["", "## Degradation triggers"]
        lines += [f"- {d}" for d in rep.degradations]
    lines += ["", "(code diffs, instance selection and tier changes are intentionally omitted)"]
    return "\n".join(lines)


def collect_proposals(rep: HealthReport) -> list[str]:
    """Deep-agent proposal channel stub: rules changes require human approval
    and only take effect in a NEW session (constitution #6)."""
    props: list[str] = []
    if rep.spec_entropy > DEFAULT_THRESHOLDS["entropy_max"]:
        props.append("proposal: add don't-care registrations or tighten clauses in top-divergence units")
    if rep.unverifiable_clauses > 0:
        props.append(f"proposal: bind {rep.unverifiable_clauses} unverifiable clauses to mechanical witnesses")
    if rep.cost_per_admission > DEFAULT_THRESHOLDS["cost_per_admission_max"]:
        props.append("proposal: lower default fanout N, raise builder tier floor")
    return props
