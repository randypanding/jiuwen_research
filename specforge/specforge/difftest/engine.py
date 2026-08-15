"""N-instance differential measurement engine (H5 core, PDR-001 section 6).

Produces the spec-entropy measurement table:
  all pass + no diff                    -> CLOSED
  all pass + diff only in free regions  -> SILENCE_DC (register freedom)
  all pass + diff elsewhere             -> SILENCE (spec silence: moderator must route)
  partial pass                          -> AMBIGUOUS (spec divergence)
  all fail, N>=3                        -> CONFLICT (escalate to spec steward)
  N<3 with failures                     -> INSUFFICIENT (regenerate to >=3)
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Optional

from .comparator import (
    DIFF_IN_DONT_CARE,
    DIFF_IN_UNDEFINED,
    EQUAL,
    compare_outputs,
)
from .normalizer import NormalizeRules, normalize
from .runner import ExecRecord

VERDICTS = ("CLOSED", "SILENCE_DC", "SILENCE", "DIFF_IN_UNDEFINED", "AMBIGUOUS", "CONFLICT", "INSUFFICIENT")


@dataclass
class InstanceRecords:
    instance_id: str
    records: list[ExecRecord]
    oracle_passed: bool = True   # did the instance pass oracle-side checks (H1-H3)

    def to_dict(self) -> dict[str, Any]:
        return {"instance_id": self.instance_id, "oracle_passed": self.oracle_passed,
                "records": [r.to_dict() for r in self.records]}


@dataclass
class Divergence:
    input_index: int
    input: dict[str, Any]
    paths: list[str]
    outcome: str

    def to_dict(self) -> dict:
        return {"input_index": self.input_index, "input": self.input,
                "paths": self.paths, "outcome": self.outcome}


@dataclass
class Measurement:
    verdict: str
    n_instances: int
    n_inputs: int
    pass_fail: list[bool]
    divergences: list[Divergence] = field(default_factory=list)
    fingerprints: dict[str, str] = field(default_factory=dict)
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "n_instances": self.n_instances,
            "n_inputs": self.n_inputs,
            "pass_fail": self.pass_fail,
            "divergences": [d.to_dict() for d in self.divergences],
            "fingerprints": self.fingerprints,
            "detail": self.detail,
        }


def fingerprint(records: list[ExecRecord], rules: NormalizeRules) -> str:
    """Behaviour fingerprint: cluster instances before pairwise comparison."""
    payload = [normalize(r.output, rules) for r in records]
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str,
                                     ensure_ascii=False).encode()).hexdigest()


def run_measurement(
    instances: list[InstanceRecords],
    rules: Optional[NormalizeRules] = None,
    dc_regions: Optional[dict[str, str]] = None,
) -> Measurement:
    rules = rules or NormalizeRules()
    dc_regions = dc_regions or {}
    n = len(instances)
    pass_fail = [inst.oracle_passed for inst in instances]
    m = Measurement(verdict="INSUFFICIENT", n_instances=n,
                    n_inputs=len(instances[0].records) if instances else 0,
                    pass_fail=pass_fail)
    if n == 0:
        m.detail = "no instances"
        return m

    m.fingerprints = {inst.instance_id: fingerprint(inst.records, rules) for inst in instances}

    if not all(pass_fail):
        if n < 3:
            m.verdict = "INSUFFICIENT"
            m.detail = f"failures with N={n} < 3: regenerate to >=3 before judging"
            return m
        if not any(pass_fail):
            m.verdict = "CONFLICT"
            m.detail = "all instances failed oracle; spec-vs-oracle conflict, escalate to steward"
            return m
        m.verdict = "AMBIGUOUS"
        m.detail = "partial pass: spec ambiguity, moderator must converge spec (oracle untouched)"
        return m

    # all passed oracle: behaviour differential across instances
    divergences: list[Divergence] = []
    unique_fps = set(m.fingerprints.values())
    if len(unique_fps) == 1:
        m.verdict = "CLOSED"
        m.detail = "all instances pass oracle and behaviour is identical (spec closed for this oracle)"
        return m

    n_inputs = min(len(i.records) for i in instances)
    for idx in range(n_inputs):
        base = instances[0].records[idx]
        for other in instances[1:]:
            rec = other.records[idx]
            outcome = compare_outputs(base.output, rec.output, rules, dc_regions)
            if outcome.verdict != EQUAL:
                divergences.append(Divergence(
                    input_index=idx, input=base.input,
                    paths=[d.path for d in outcome.diffs], outcome=outcome.verdict))
                break

    m.divergences = divergences
    outcomes = {d.outcome for d in divergences}
    if DIFF_IN_UNDEFINED in outcomes:
        m.verdict = "DIFF_IN_UNDEFINED"
        m.detail = "divergence in `undefined` region: defect, block"
    elif outcomes == {DIFF_IN_DONT_CARE} or not (outcomes - {DIFF_IN_DONT_CARE}):
        m.verdict = "SILENCE_DC"
        m.detail = "divergences confined to registered don't-care regions"
    else:
        m.verdict = "SILENCE"
        m.detail = "spec silence: unregistered freedom filled differently; moderator routes"
    return m


def verdict_from_records(records: list[InstanceRecords],
                         dc_regions: Optional[dict[str, str]] = None) -> Measurement:
    """Bridge used by H5 gate: verdict from pre-collected records."""
    return run_measurement(records, rules=NormalizeRules(), dc_regions=dc_regions)


def moderation_route(m: Measurement) -> str:
    """PDR-001 section 6 disposition table -> routing target."""
    routing = {
        "CLOSED": "admit-best-instance",
        "SILENCE_DC": "register-freedom",
        "SILENCE": "spec-moderator: classify region (don't-care vs new clause)",
        "DIFF_IN_UNDEFINED": "defect: reject and fix",
        "AMBIGUOUS": "spec-moderator: converge spec, oracle untouched",
        "CONFLICT": "spec-steward + architect joint session (spec-vs-oracle conflict)",
        "INSUFFICIENT": "fan-out more instances (>=3)",
    }
    return routing[m.verdict]
