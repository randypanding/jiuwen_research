"""Delivery pipeline orchestrator (WP10): the swarm state machine.

Drives: wave.begin -> fanout N builders (seeds platform-injected) ->
verifier hard gates (+ H5 differential across instances) -> judge soft gates
(advisory only) -> admission algebra -> admit/rollback -> measurement ->
moderator routing -> health recording.

Depends ONLY on ports (fakes in tests, OpenJiuwenAdapter in production).
Constitution enforcements here:
  #5  builders never see holdout; verifier/judge isolated
  #6  orchestrator config frozen for the session (no self-evolution)
  #14 judge tier >= builder tier checked at wiring time
  #17 seeds injected by orchestrator, recorded in receipt
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Optional

from ..gates.base import GateResult, decide_admission
from ..metrics.health import HealthTracker, WaveMetrics
from ..wave.manager import WaveManager
from .fanout import EarlyStopPolicy, plan_from_delta
from .ports import (
    BuilderPort,
    GateRunOrder,
    MessengerPort,
    ModeratorPort,
    SpawnOrder,
    SwarmEvent,
    VerifierPort,
)


class WiringError(RuntimeError):
    pass


def assert_wiring(builder_tier: str, judge_tier: Optional[str]) -> None:
    if judge_tier is None:
        return
    order = {"RU-L": 0, "RU-M": 1, "RU-H": 2}
    if order.get(judge_tier, -1) < order.get(builder_tier, 99):
        raise WiringError(
            f"constitution #14: judge tier {judge_tier} < builder tier {builder_tier}")


@dataclass
class OrchestratorConfig:
    world_ref: str = "main"
    rework_rate: float = 0.0
    early_stop: EarlyStopPolicy = field(default_factory=EarlyStopPolicy)
    cost_budget_usd: float = 50.0
    seed_base: int = 20260815
    judge_tier: Optional[str] = None       # None => no soft gates
    session_frozen: bool = True            # constitution #6


class DeliveryOrchestrator:
    def __init__(
        self,
        wave_manager: WaveManager,
        builder: BuilderPort,
        verifier: VerifierPort,
        moderator: ModeratorPort,
        messenger: Optional[MessengerPort] = None,
        config: Optional[OrchestratorConfig] = None,
        health: Optional[HealthTracker] = None,
    ):
        self.waves = wave_manager
        self.builder = builder
        self.verifier = verifier
        self.moderator = moderator
        self.messenger = messenger
        self.cfg = config or OrchestratorConfig()
        self.health = health or HealthTracker()
        assert_wiring(self.builder.tier, self.cfg.judge_tier)

    def _emit(self, kind: str, payload: dict[str, Any]) -> None:
        if self.messenger:
            import time

            self.messenger.publish(SwarmEvent(kind=kind, payload=payload, at=time.time()))

    def run_pipeline(self, spec_unit: dict[str, Any], spec_delta: dict[str, Any]) -> dict[str, Any]:
        """One delivery wave. Returns the wave outcome dict (receipt included)."""
        n, u = plan_from_delta(spec_delta, rework_rate=self.cfg.rework_rate)
        wave = self.waves.begin(spec_delta, pipeline="A")
        self._emit("wave-begin", {"wave_id": wave.wave_id, "N": n, "U": u})

        # ---- fan-out builders (seeds platform-injected) ------------------------
        rng = random.Random(self.cfg.seed_base ^ int(wave.wave_id.rsplit("-", 1)[-1], 16))
        instances: list[dict[str, Any]] = []
        identical_passes = 0
        for i in range(n):
            iid = f"{wave.wave_id}-b{i+1}"
            order = SpawnOrder(
                spec_delta=spec_delta, seed=rng.getrandbits(32), instance_id=iid,
                builder_tier=self.builder.tier,
                tools_allowlist=["read", "write", "test", "git"],
                context_id=f"builder::{iid}",
            )
            out = self.builder.spawn(order)
            self.waves.register_instance(wave.wave_id, out.source, instance_id=iid)
            instances.append({"instance_id": iid, "source": out.source,
                              "oracle_passed": out.oracle_passed, "cost_usd": out.cost_usd})
            self._emit("spawn", {"instance_id": iid, "oracle_passed": out.oracle_passed})
            if out.oracle_passed:
                identical_passes += 1
            if self.cfg.early_stop.should_stop(i + 1, identical_passes,
                                               spec_delta.get("r_level", "R0")):
                self._emit("spawn", {"early_stop": True, "after": i + 1})
                break

        if not instances:
            return {"wave_id": wave.wave_id, "outcome": "no-instances"}

        # ---- hard gates on each surviving instance, pick first fully-passing ---
        candidates: list[tuple[str, list[GateResult]]] = []
        for inst in instances:
            if not inst["oracle_passed"]:
                continue
            suite = self.verifier.run_hard_gates(GateRunOrder(
                instance_source=inst["source"], spec_unit=spec_unit, spec_delta=spec_delta))
            grs = [GateResult(**g) for g in suite.get("results", [])]
            decision = decide_admission(grs, [])
            self._emit("gates", {"instance_id": inst["instance_id"],
                                 "decision": decision.decision})
            if decision.admitted:
                candidates.append((inst["instance_id"], grs))
        if not candidates:
            # record measurement of failure and abort wave (no instance entered world)
            self._record(wave.wave_id, spec_delta, instances, None, "AMBIGUOUS_OR_FAIL")
            return {"wave_id": wave.wave_id, "outcome": "rejected", "instances": instances}

        # ---- H5 differential across candidate instances -------------------------
        measurement: dict[str, Any] = {}
        if len(candidates) >= 2:
            sources = [inst["source"] for inst in instances if inst["oracle_passed"]]
            measurement = self.verifier.run_differential(sources, spec_unit)
            self._emit("measurement", measurement)
            if measurement.get("verdict") in ("DIFF_IN_UNDEFINED",):
                self._record(wave.wave_id, spec_delta, instances, measurement, "DEFECT")
                return {"wave_id": wave.wave_id, "outcome": "differential-defect",
                        "measurement": measurement}
            if measurement.get("verdict") in ("SILENCE", "AMBIGUOUS", "CONFLICT", "INSUFFICIENT"):
                decision_route = self.moderator.route(measurement)
                self._emit("moderation", {"route": decision_route.route,
                                          "rationale": decision_route.rationale})
                if decision_route.route not in ("admit-best-instance", "more-instances"):
                    self._record(wave.wave_id, spec_delta, instances, measurement, "NEEDS_SPEC")
                    return {"wave_id": wave.wave_id, "outcome": f"moderated:{decision_route.route}",
                            "measurement": measurement, "moderation": decision_route.route}

        # ---- admit ---------------------------------------------------------------
        best_id, grs = candidates[0]
        decision, receipt = self.waves.admit(
            wave.wave_id, best_id, grs, soft_results=[],
            measurement=measurement or None,
            cost_usd=sum(i["cost_usd"] for i in instances),
            wall_s=0.0,
        )
        self._emit("admit", {"instance_id": best_id, "receipt": receipt.receipt_id if receipt else None})
        self._record(wave.wave_id, spec_delta, instances, measurement or {"verdict": "CLOSED"},
                     "ADMITTED", admitted=True)
        return {"wave_id": wave.wave_id, "outcome": "admitted", "instance_id": best_id,
                "receipt": receipt.to_dict() if receipt else None, "measurement": measurement}

    # ---- helpers ---------------------------------------------------------------

    def _record(self, wave_id: str, delta: dict, instances: list[dict],
                measurement: Optional[dict], outcome: str, admitted: bool = False) -> None:
        self.health.record_wave(WaveMetrics(
            wave_id=wave_id,
            spec_id=delta.get("spec_id", ""),
            n_instances=len(instances),
            measurement_verdict=(measurement or {}).get("verdict", "UNKNOWN"),
            divergences=len((measurement or {}).get("divergences", [])),
            admitted=admitted,
            cost_usd=sum(i.get("cost_usd", 0.0) for i in instances),
        ))
