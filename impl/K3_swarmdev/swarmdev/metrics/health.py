from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from swarmdev.admission.measurement import Outcome
from swarmdev.contracts import EvidenceReceipt


class HealthSnapshot(BaseModel):
    closure_rate: float
    silence_or_divergence_events: int
    witness_coverage: float
    drift_hard_events: int
    judge_kappa: Optional[float] = None
    avg_cost_per_admission: float
    degradation_triggers: list[str] = Field(default_factory=list)


class HealthMetrics:
    def __init__(self) -> None:
        self._judged = 0
        self._closed = 0
        self._silence_or_divergence = 0
        self._drift_hard_events = 0
        self._kappa: Optional[float] = None
        self._witness_coverage = 0.0
        self._admitted_count = 0
        self._admitted_cost = 0.0

    def record_fanout(self, outcome: Outcome) -> None:
        self._judged += 1
        if outcome == Outcome.CLOSED:
            self._closed += 1
        if outcome in (Outcome.SILENCE, Outcome.DIVERGENCE):
            self._silence_or_divergence += 1

    def record_receipt(self, receipt: EvidenceReceipt, cost_tokens: float = 0.0) -> None:
        if receipt.admitted:
            self._admitted_count += 1
            self._admitted_cost += cost_tokens

    def record_drift(self, clean: bool, hard_events: int) -> None:
        self._drift_hard_events += hard_events

    def record_calibration(self, kappa: Optional[float]) -> None:
        self._kappa = kappa

    def set_witness_coverage(self, x: float) -> None:
        self._witness_coverage = x

    def snapshot(self, closure_threshold: float = 0.6, drift_spike: int = 5) -> HealthSnapshot:
        closure_rate = self._closed / self._judged if self._judged else 0.0
        avg_cost = self._admitted_cost / self._admitted_count if self._admitted_count else 0.0
        triggers: list[str] = []
        # PDR-001 §13/§15：判据不可信时降低自治级别，而非放宽判据
        if self._kappa is not None and self._kappa < 0.6:
            triggers.append("soft_gate_suspended")
        if self._judged >= 3 and closure_rate < closure_threshold:
            triggers.append("reduce_autonomy")
        if self._drift_hard_events >= drift_spike:
            triggers.append("freeze_fanout")
        return HealthSnapshot(
            closure_rate=closure_rate,
            silence_or_divergence_events=self._silence_or_divergence,
            witness_coverage=self._witness_coverage,
            drift_hard_events=self._drift_hard_events,
            judge_kappa=self._kappa,
            avg_cost_per_admission=avg_cost,
            degradation_triggers=triggers,
        )
