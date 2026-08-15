"""GateRunner：门禁编排器。

职责：
- 按 R 级要求选择硬门禁集合（H1-H8），S 恒可选配
- fail-fast（默认）：首个 blocking FAIL 即停（省成本）；collect_all 模式为证据收据收集全量
- 证据来源链校验：EvidenceRejected → 该门 INCONCLUSIVE + 升级（不能静默放行）
- 产出 AdmissionDecision（adjudicate 纯函数）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..specrepo.rregistry import RLevel
from .algebra import (
    AdmissionDecisionKind,
    EvidenceRejected,
    GateContext,
    GateResult,
    Verdict,
    adjudicate,
)
from .h_gates import ALL_GATES, GATE_BY_ID, gates_for_r_level


@dataclass
class GateRunOutcome:
    decision: AdmissionDecisionKind
    hard_results: list[GateResult] = field(default_factory=list)
    soft_results: list[GateResult] = field(default_factory=list)
    blocking_failures: list[str] = field(default_factory=list)

    @property
    def admitted(self) -> bool:
        return self.decision == AdmissionDecisionKind.ADMIT

    def to_dict(self) -> dict:
        return {
            "decision": self.decision.value,
            "hard": [r.to_dict() for r in self.hard_results],
            "soft": [r.to_dict() for r in self.soft_results],
            "blocking_failures": self.blocking_failures,
        }


class GateRunner:
    def __init__(self, extra_gates: Optional[list] = None):
        self.gates = list(ALL_GATES)
        for g in extra_gates or []:
            self.gates.append(g)
            GATE_BY_ID[g.gate_id] = g

    def run(self, ctx: GateContext, r_level: RLevel,
            gate_ids: Optional[list[str]] = None,
            collect_all: bool = False) -> GateRunOutcome:
        """执行门禁集。

        gate_ids 显式指定（准入事务按 touched paths 的 R 级并集计算后传入）；
        缺省用 gates_for_r_level(r_level)。
        """
        if gate_ids is None:
            gate_ids = [g.gate_id for g in gates_for_r_level(r_level)]

        hard: list[GateResult] = []
        soft: list[GateResult] = []
        blocking_failures: list[str] = []

        for g in self.gates:
            is_soft = g.gate_id == "S"
            if not is_soft and g.gate_id not in gate_ids:
                continue
            if is_soft and "S" not in (gate_ids or []) and not ctx.evidence.get("judge_outputs"):
                continue  # S 未配置且无判词 → 不参与
            try:
                result = g.evaluate(ctx)
            except EvidenceRejected as exc:
                # 证据来源非法：绝不放行，升级处置（不是简单 FAIL——需要人看是谁伪造）
                result = GateResult(
                    g.gate_id, Verdict.INCONCLUSIVE, True,
                    f"evidence rejected: {exc}", {"evidence_kind": exc.kind,
                                                  "producer": exc.producer})
            except KeyError as exc:
                result = GateResult(
                    g.gate_id, Verdict.INCONCLUSIVE, True,
                    f"missing evidence {exc}")
            (soft if is_soft else hard).append(result)
            if result.blocking and result.verdict in (Verdict.FAIL, Verdict.INCONCLUSIVE):
                blocking_failures.append(f"{g.gate_id}:{result.verdict.value}")
                if not collect_all:
                    break

        soft_vetoes = sum(
            1 for r in soft if r.verdict == Verdict.FAIL)
        soft_abstains = sum(
            1 for r in soft if r.verdict == Verdict.INCONCLUSIVE)
        decision = adjudicate(hard, soft_vetoes, soft_abstains)
        return GateRunOutcome(decision, hard, soft, blocking_failures)
