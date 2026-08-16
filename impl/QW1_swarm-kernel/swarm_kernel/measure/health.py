from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from swarm_kernel.contracts.fanout import MeasurementClassification, MeasurementEvent
from swarm_kernel.contracts.health import HealthSnapshot, MigrationStage
from swarm_kernel.contracts.oracle import JudgeVerdict, JudgeVerdictKind
from swarm_kernel.contracts.spec import SpecDoc


class EventLog:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, kind: str, payload: dict) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"kind": kind, "payload": payload}, ensure_ascii=False) + "\n")

    def read(self, kind: Optional[str] = None) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if kind is None or rec.get("kind") == kind:
                out.append(rec["payload"])
        return out


def compute_health(
    log: EventLog,
    spec: Optional[SpecDoc] = None,
    stage: MigrationStage = MigrationStage.M0_HARVEST,
    period: str = "",
) -> HealthSnapshot:
    measurements = [MeasurementEvent.model_validate(p) for p in log.read("measurement")]
    drift_events = log.read("drift")
    verdicts = [JudgeVerdict.model_validate(p) for p in log.read("judge_verdict")]
    admitted = log.read("admitted")
    escaped = log.read("escaped_defect")
    reworks = log.read("rework")
    tokens = [float(p.get("tokens", 0.0)) for p in log.read("cost")]

    closure = 0.0
    entropy = 0.0
    if measurements:
        closed = sum(1 for m in measurements if m.classification == MeasurementClassification.CLOSED)
        closure = closed / len(measurements)
        entropy_events = sum(1 for m in measurements if m.classification in (MeasurementClassification.SILENCE, MeasurementClassification.DIVERGENCE))
        deltas = len({m.delta_id for m in measurements}) or 1
        entropy = entropy_events / deltas

    coverage = 0.0
    unverifiable = 0
    if spec is not None and spec.clauses:
        verified = [c for c in spec.clauses if c.is_verifiable()]
        coverage = len(verified) / len(spec.clauses)
        unverifiable = len(spec.unverifiable_clauses())

    kappa = 0.0
    abstention = 0.0
    if verdicts:
        abstain = sum(1 for v in verdicts if v.kind == JudgeVerdictKind.ABSTAIN)
        abstention = abstain / len(verdicts)
        kappas = [float(p.get("kappa", 0.0)) for p in log.read("judge_calibration")]
        if kappas:
            kappa = sum(kappas) / len(kappas)

    escape_rate = len(escaped) / len(admitted) if admitted else 0.0
    rework_rate = len(reworks) / len(admitted) if admitted else 0.0

    return HealthSnapshot(
        period=period,
        stage=stage,
        closure_rate=round(closure, 4),
        spec_entropy_events_per_delta=round(entropy, 4),
        witness_coverage=round(coverage, 4),
        unverifiable_clauses=unverifiable,
        escape_defect_rate=round(escape_rate, 4),
        drift_alert_rate=float(len(drift_events)),
        judge_calibration_kappa=round(kappa, 4),
        judge_abstention_rate=round(abstention, 4),
        rework_rate=round(rework_rate, 4),
        admission_cost_tokens=sum(tokens),
    )
