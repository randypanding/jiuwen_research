"""Gate framework + admission algebra (WP3, constitution #3/#4).

Admission: admit = AND(H results) AND (S results).
  - any FAIL (hard or soft)          -> REJECT
  - any INCONCLUSIVE                 -> BLOCK (never silently clear)
  - SKIP is neutral (gate not applicable)
Judge (soft) can veto but can never waive a hard failure.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

CONSTITUTION_PATHS = {
    "no_witness": "#3 无机械见证的条款只能否决，不能放行",
    "hard_fail": "#4 硬门禁不通过，任何软性判断不得放行",
    "inconclusive": "#3/#12 证据不足即未验证；准入必须附带完整证据收据",
    "soft_veto": "#4 硬门禁通过，软性判断有权否决",
}


class GateVerdict(str):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    SKIP = "SKIP"


@dataclass
class GateResult:
    gate_id: str
    verdict: str
    evidence: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    reason: str = ""
    constitution_ref: str = ""
    duration_s: float = 0.0
    hard: bool = True

    @property
    def passed(self) -> bool:
        return self.verdict == GateVerdict.PASS

    @property
    def blocked(self) -> bool:
        return self.verdict in (GateVerdict.FAIL, GateVerdict.INCONCLUSIVE)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "verdict": self.verdict,
            "hard": self.hard,
            "reason": self.reason,
            "constitution_ref": self.constitution_ref,
            "evidence": self.evidence,
            "artifacts": self.artifacts,
            "duration_s": self.duration_s,
        }


class GateContext:
    """Everything a gate may see. Assembled by the wave manager / orchestrator."""

    def __init__(
        self,
        *,
        instance_path: str,
        world_path: str,
        spec_unit: Any = None,          # SpecUnit
        spec_delta: Any = None,         # SpecDelta
        surface_old: Any = None,        # SurfaceSnapshot (world version)
        surface_new: Any = None,        # SurfaceSnapshot (instance version)
        config: Optional[dict[str, Any]] = None,
        holdout_store: Any = None,
        golden_store: Any = None,
        difftest_records: Any = None,   # list[ExecRecord] per instance (pre-run)
        budget: Optional[dict[str, float]] = None,
        extra: Optional[dict[str, Any]] = None,
    ):
        self.instance_path = instance_path
        self.world_path = world_path
        self.spec_unit = spec_unit
        self.spec_delta = spec_delta
        self.surface_old = surface_old
        self.surface_new = surface_new
        self.config = config or {}
        self.holdout_store = holdout_store
        self.golden_store = golden_store
        self.difftest_records = difftest_records
        self.budget = budget or {}
        self.extra = extra or {}


class Gate(Protocol):
    gate_id: str
    description: str
    hard: bool

    def applicable(self, ctx: GateContext) -> bool: ...
    def run(self, ctx: GateContext) -> GateResult: ...


@dataclass
class AdmissionDecision:
    decision: str                 # ADMIT | REJECT | BLOCK
    reasons: list[str] = field(default_factory=list)
    constitution_refs: list[str] = field(default_factory=list)
    blocking_gates: list[str] = field(default_factory=list)
    vetoing_gates: list[str] = field(default_factory=list)

    @property
    def admitted(self) -> bool:
        return self.decision == "ADMIT"


def _eval_results(results: list[GateResult], label: str) -> tuple[list[str], list[str], list[str]]:
    fails, inconclusive, refs = [], [], []
    for r in results:
        if r.verdict == GateVerdict.FAIL:
            fails.append(f"{label}:{r.gate_id}: {r.reason}")
            if r.constitution_ref:
                refs.append(r.constitution_ref)
        elif r.verdict == GateVerdict.INCONCLUSIVE:
            inconclusive.append(f"{label}:{r.gate_id}: {r.reason or 'evidence incomplete'}")
            if r.constitution_ref:
                refs.append(r.constitution_ref or CONSTITUTION_PATHS["inconclusive"])
    return fails, inconclusive, refs


def decide_admission(hard_results: list[GateResult], soft_results: Optional[list[GateResult]] = None) -> AdmissionDecision:
    soft_results = soft_results or []
    d = AdmissionDecision(decision="ADMIT")

    h_fail, h_inc, refs = _eval_results(hard_results, "H")
    s_fail, s_inc, srefs = _eval_results(soft_results, "S")

    if h_fail:
        d.decision = "REJECT"
        d.reasons.extend(h_fail)
        d.blocking_gates.extend(r.split(":")[1] for r in h_fail)
        d.constitution_refs.append(CONSTITUTION_PATHS["hard_fail"])
        d.constitution_refs.extend(refs)
        # soft results still recorded but hard failure dominates
        d.reasons.extend(s_fail + s_inc)
        return d

    if s_fail:
        d.decision = "REJECT"
        d.reasons.extend(s_fail)
        d.vetoing_gates.extend(r.split(":")[1] for r in s_fail)
        d.constitution_refs.append(CONSTITUTION_PATHS["soft_veto"])
        return d

    if h_inc or s_inc:
        d.decision = "BLOCK"
        d.reasons.extend(h_inc + s_inc)
        d.blocking_gates.extend(r.split(":")[1] for r in h_inc)
        d.constitution_refs.append(CONSTITUTION_PATHS["inconclusive"])
        return d

    return d


@dataclass
class SuiteResult:
    gate_id: str
    results: list[GateResult] = field(default_factory=list)
    started: float = 0.0
    finished: float = 0.0

    @property
    def duration_s(self) -> float:
        return self.finished - self.started

    def to_dict(self) -> dict[str, Any]:
        return {
            "results": [r.to_dict() for r in self.results],
            "duration_s": self.duration_s,
        }


def run_suite(ctx: GateContext, gates: list[Gate], fail_fast: bool = False) -> SuiteResult:
    suite = SuiteResult(gate_id="suite", started=time.time())
    for gate in gates:
        if not gate.applicable(ctx):
            suite.results.append(GateResult(gate.gate_id, GateVerdict.SKIP,
                                            reason="not applicable", hard=getattr(gate, "hard", True)))
            continue
        t0 = time.time()
        try:
            result = gate.run(ctx)
        except Exception as e:  # gate crash = inconclusive, never silent pass
            result = GateResult(gate.gate_id, GateVerdict.INCONCLUSIVE,
                                reason=f"gate crashed: {e}",
                                constitution_ref=CONSTITUTION_PATHS["inconclusive"])
        result.duration_s = time.time() - t0
        result.hard = getattr(gate, "hard", True)
        if not result.gate_id:
            result.gate_id = gate.gate_id
        suite.results.append(result)
        if fail_fast and result.blocked:
            break
    suite.finished = time.time()
    return suite
