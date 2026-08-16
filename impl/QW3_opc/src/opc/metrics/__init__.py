from __future__ import annotations

from dataclasses import dataclass, field

from opc.schemas.common import Verdict


@dataclass
class WaveMeasurement:
    wave_id: str
    contract_id: str
    fanout_n: int
    all_pass: bool
    diff_empty: bool
    silence_events: int = 0
    divergence_events: int = 0
    failures: int = 0
    tokens_prompt: int = 0
    tokens_completion: int = 0
    rework_count: int = 0
    judge_verdict: Verdict = Verdict.PASS
    drift_alarms: int = 0


@dataclass
class HealthSnapshot:
    spec_closure_rate: float = 0.0
    spec_entropy_per_delta: float = 0.0
    judge_abstention_rate: float = 0.0
    drift_rate: float = 0.0
    rework_rate: float = 0.0
    admission_cost_tokens: int = 0
    waves: int = 0
    escapes: int = 0
    notes: list[str] = field(default_factory=list)


def compute_health(measurements: list[WaveMeasurement], escapes: int = 0) -> HealthSnapshot:
    """Health metrics of PDR-001 section 13.

    * spec closure rate : fraction of fan-outs fully green with empty diff;
    * spec entropy      : (silence + divergence events) per spec-delta;
    * judge abstention  : INCONCLUSIVE judge verdicts / judged waves;
    * drift rate        : drift alarms per wave;
    * rework rate       : rework cycles per wave;
    * admission cost    : total tokens spent.

    Demotion triggers are evaluated against thresholds by the leader rail,
    not here; this module only computes the observables.
    """

    snapshot = HealthSnapshot(waves=len(measurements), escapes=escapes)
    if not measurements:
        snapshot.notes.append("no waves measured yet")
        return snapshot

    closed = sum(1 for m in measurements if m.all_pass and m.diff_empty and m.failures == 0)
    snapshot.spec_closure_rate = round(closed / len(measurements), 4)

    entropy_events = sum(m.silence_events + m.divergence_events for m in measurements)
    snapshot.spec_entropy_per_delta = round(entropy_events / len(measurements), 4)

    judged = [m for m in measurements if m.judge_verdict is not None]
    abstained = sum(1 for m in judged if m.judge_verdict is Verdict.INCONCLUSIVE)
    snapshot.judge_abstention_rate = round(abstained / len(judged), 4) if judged else 0.0

    snapshot.drift_rate = round(sum(m.drift_alarms for m in measurements) / len(measurements), 4)
    snapshot.rework_rate = round(sum(m.rework_count for m in measurements) / len(measurements), 4)
    snapshot.admission_cost_tokens = sum(m.tokens_prompt + m.tokens_completion for m in measurements)
    return snapshot
