"""Adaptive fan-out N (WP13 core, decision D13).

Three layers (tco research):
  L1 fuzzy sizing: U = 0.4*rework + 0.3*novelty + 0.3*risk -> N in {1,3,6}, cap 8
  L2 early stop:  if the first k instances all pass oracle identically, stop
  L3 (future):    bandit / Bayesian optimal stopping
R3 units: no early stop, no fan-out (frozen artifacts).
"""
from __future__ import annotations

from dataclasses import dataclass

HARD_CAP = 8


def uncertainty(rework: float, novelty: float, risk: float) -> float:
    u = 0.4 * _clamp(rework) + 0.3 * _clamp(novelty) + 0.3 * _clamp(risk)
    return round(_clamp(u), 3)


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def fanout_plan(u: float, r_level: str = "R0") -> int:
    if r_level == "R3":
        return 1  # frozen: regeneration forbidden
    u = _clamp(u)
    if u < 0.3:
        n = 1
    elif u < 0.7:
        n = 3
    else:
        n = 6
    return min(n, HARD_CAP)


@dataclass
class EarlyStopPolicy:
    k: int = 2                 # stop after k identical oracle-passing instances
    enabled: bool = True

    def should_stop(self, completed: int, identical_oracle_passes: int, r_level: str = "R0") -> bool:
        if not self.enabled or r_level == "R3":
            return False       # R3 forbids early stop (frozen artifacts)
        return identical_oracle_passes >= self.k and completed >= self.k


def plan_from_delta(delta: dict, rework_rate: float = 0.0) -> tuple[int, float]:
    """Convenience: compute (N, U) from a SpecDelta dict."""
    u = uncertainty(
        rework=rework_rate,
        novelty=float(delta.get("novelty", 0.5)),
        risk=float(delta.get("risk", 0.5)),
    )
    return fanout_plan(u, delta.get("r_level", "R0")), u
