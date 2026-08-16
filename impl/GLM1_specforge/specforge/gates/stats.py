"""Statistical gates for nondeterministic outcomes (D6).

Wilson lower bound, k-of-n consistency, and a lightweight SPRT (Wald)
between p0 (unacceptable pass rate) and p1 (acceptable pass rate).
INCONCLUSIVE is a blocking verdict by admission algebra.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


def wilson_lower(passes: int, n: int, z: float = 1.96) -> float:
    """Wilson score interval lower bound for pass rate."""
    if n <= 0:
        return 0.0
    p = passes / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - margin) / denom


@dataclass
class StatVerdict:
    verdict: str  # PASS | FAIL | INCONCLUSIVE
    statistic: float
    detail: str


def threshold_gate(passes: int, n: int, theta: float, z: float = 1.96) -> StatVerdict:
    """Pass only if the Wilson lower bound of pass rate >= theta."""
    if n <= 0:
        return StatVerdict("INCONCLUSIVE", 0.0, "no samples")
    lb = wilson_lower(passes, n, z)
    if lb >= theta:
        return StatVerdict("PASS", lb, f"wilson lower {lb:.4f} >= {theta} ({passes}/{n})")
    # distinguish "clearly below" from "not enough samples yet"
    p = passes / n
    if p < theta:
        return StatVerdict("FAIL", lb, f"point estimate {p:.3f} < {theta} ({passes}/{n})")
    return StatVerdict("INCONCLUSIVE", lb, f"insufficient samples: wilson lower {lb:.4f} < {theta} ({passes}/{n})")


def k_of_n_gate(results: Sequence[bool], k: int) -> StatVerdict:
    """All of the last k runs must pass (pass^k consistency)."""
    if len(results) < k:
        return StatVerdict("INCONCLUSIVE", len(results) / max(k, 1),
                           f"{len(results)}/{k} runs recorded")
    tail = results[-k:]
    if all(tail):
        return StatVerdict("PASS", 1.0, f"last {k} runs all passed")
    fails = tail.count(False)
    return StatVerdict("FAIL", 1 - fails / k, f"{fails} failure(s) in last {k} runs")


def sprt_gate(results: Sequence[bool], p0: float, p1: float,
              alpha: float = 0.05, beta: float = 0.10) -> StatVerdict:
    """Wald SPRT on Bernoulli pass rate. H0: p<=p0 (reject quality) vs H1: p>=p1."""
    if not (0 < p0 < p1 < 1):
        raise ValueError("require 0 < p0 < p1 < 1")
    if not results:
        return StatVerdict("INCONCLUSIVE", 0.0, "no samples")
    a = math.log(beta / (1 - alpha))    # lower boundary (accept H1 above this... see sign)
    b = math.log((1 - beta) / alpha)    # upper boundary
    llr = 0.0
    q0, q1 = 1 - p0, 1 - p1
    for r in results:
        llr += math.log(p1 / p0) if r else math.log(q1 / q0)
        if llr >= b:
            return StatVerdict("PASS", llr, f"SPRT accepted H1 (p>={p1}) after {results.count(True)+results.count(False)} obs, llr={llr:.3f}")
        if llr <= a:
            return StatVerdict("FAIL", llr, f"SPRT accepted H0 (p<={p0}), llr={llr:.3f}")
    return StatVerdict("INCONCLUSIVE", llr, f"SPRT undecided llr={llr:.3f} in ({a:.3f},{b:.3f})")


def required_reruns(p_hat: float, confidence: float = 0.95) -> int:
    """n >= ln(alpha)/ln(1-p_hat) — reruns needed to see one failure with confidence."""
    if p_hat <= 0 or p_hat >= 1:
        raise ValueError("p_hat in (0,1)")
    alpha = 1 - confidence
    return math.ceil(math.log(alpha) / math.log(1 - p_hat))


def zero_failure_upper_bound(n: int, confidence: float = 0.95) -> float:
    """n zero-failure runs => failure rate upper bound ~ 3/n (rule of three)."""
    if n <= 0:
        return 1.0
    return -math.log(1 - confidence) / n
