from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from swarm_kernel.contracts.gates import GateId
from swarm_kernel.contracts.wave import WavePlan
from swarm_kernel.spec_repo.registry import ClauseRegistry


@dataclass
class GateConfig:
    h1_commands: list[list[str]] = field(default_factory=list)
    h2_commands: list[list[str]] = field(default_factory=list)
    forbidden_imports: list[str] = field(default_factory=lambda: ["os.system"])
    secret_patterns: list[str] = field(
        default_factory=lambda: [
            r"AKIA[0-9A-Z]{16}",
            r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
            r"sk-[A-Za-z0-9]{20,}",
        ]
    )
    forbidden_patterns: list[str] = field(default_factory=lambda: [r"eval\s*\(", r"subprocess\.call\(.+shell\s*=\s*True"])
    license_denylist: list[str] = field(default_factory=lambda: ["AGPL-3.0"])
    max_total_bytes: int = 2_000_000
    budget_tokens: float = 500_000
    budget_seconds: float = 3600
    budget_bytes: float = 2_000_000


@dataclass
class GateContext:
    instance_dir: Path
    oracle_dir: Path
    registry: Optional[ClauseRegistry]
    out_dir: Path
    wave: Optional[WavePlan] = None
    config: GateConfig = field(default_factory=GateConfig)
    peer_instances: list[Path] = field(default_factory=list)
    diff_seed: int = 42
    corpus_size: int = 50


GATE_ORDER = [
    GateId.H1_BUILD,
    GateId.H2_UNIT,
    GateId.H3_HOLDOUT,
    GateId.H4_CONTRACT_SURFACE,
    GateId.H5_DIFFERENTIAL,
    GateId.H6_INVARIANTS,
    GateId.H7_DRIFT,
    GateId.H8_BUDGET,
]

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_INCONCLUSIVE = 2


def wilson_bounds(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = successes / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    lower = (centre - spread) / denom
    upper = (centre + spread) / denom
    return max(0.0, lower), min(1.0, upper)


def wilson_verdict(successes: int, n: int, pass_threshold: float = 0.4, fail_threshold: float = 0.6) -> str:
    if n == 0:
        return "inconclusive"
    if n == 1:
        return "pass" if successes == 1 else "fail"
    lower, upper = wilson_bounds(successes, n)
    if lower >= pass_threshold:
        return "pass"
    if upper <= fail_threshold:
        return "fail"
    return "inconclusive"
