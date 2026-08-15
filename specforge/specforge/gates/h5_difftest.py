"""H5: differential testing / golden output gate."""
from __future__ import annotations

from typing import Any

from .base import GateContext, GateResult, GateVerdict


class H5DifftestGate:
    gate_id = "h5"
    description = "instance differential testing / golden replay"
    hard = True

    def __init__(self, min_instances: int = 2):
        self.min_instances = min_instances

    def applicable(self, ctx: GateContext) -> bool:
        return bool(ctx.difftest_records) or ctx.golden_store is not None

    def run(self, ctx: GateContext) -> GateResult:
        evidence: dict[str, Any] = {}
        unit = ctx.spec_unit
        dc_regions = {d.region: d.kind for d in (unit.dont_cares if unit else [])}

        if ctx.difftest_records:
            from ..difftest.engine import verdict_from_records

            v = verdict_from_records(ctx.difftest_records, dc_regions)
            evidence["differential"] = v.to_dict()
            if v.verdict == "DIFF_IN_UNDEFINED":
                return GateResult(self.gate_id, GateVerdict.FAIL,
                                  reason=f"behaviour diverges in undefined (non-free) region: {v.detail}",
                                  evidence=evidence, constitution_ref="#10 spec 与代码不一致默认判缺陷")
            if v.verdict in ("CLOSED", "SILENCE_DC"):
                # CLOSED: identical behaviour; SILENCE_DC: divergence confined to
                # explicitly registered don't-care regions (constitution #9 satisfied)
                return GateResult(self.gate_id, GateVerdict.PASS, reason=v.detail, evidence=evidence)
            # SILENCE / AMBIGUOUS / CONFLICT / INSUFFICIENT: must not admit silently
            return GateResult(self.gate_id, GateVerdict.INCONCLUSIVE,
                              reason=f"{v.verdict}: {v.detail} "
                                      "(route to spec moderator; do not admit silently)",
                              evidence=evidence,
                              constitution_ref="#9 多实例行为差异必须被解释")

        if ctx.golden_store is not None and unit is not None:
            res = ctx.golden_store.compare(unit.spec_id, ctx.extra.get("golden_records"))
            evidence["golden"] = res.to_dict()
            if res.verdict == "MISMATCH":
                return GateResult(self.gate_id, GateVerdict.FAIL,
                                  reason=f"golden mismatch: {res.detail}", evidence=evidence)
            if res.verdict == "INCONCLUSIVE":
                return GateResult(self.gate_id, GateVerdict.INCONCLUSIVE,
                                  reason=f"golden manifest gate: {res.detail}", evidence=evidence,
                                  constitution_ref="#12 准入必须附带完整证据收据")
            return GateResult(self.gate_id, GateVerdict.PASS, reason=res.detail, evidence=evidence)

        return GateResult(self.gate_id, GateVerdict.INCONCLUSIVE,
                          reason="neither differential records nor golden store available",
                          constitution_ref="#3 无机械见证的条款只能否决，不能放行")
