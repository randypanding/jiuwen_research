"""门禁代数：Admit = H ∧ S（合取、否决型、缺一不可）。

Admit(instance) = H(instance) ∧ S(instance)
- H：硬门禁合取，机械见证；任何 H FAIL → 拒绝，软门禁无法救场（INV4）
- S：软门禁（LLM-as-judge），单调否决器：只能 否决 或 不否决，永不豁免硬门禁
- 证据来源链：验证性证据必须由判别侧角色产出；builder 自报的证据被拒绝
  （reward-hacking 的信息前提消除，INV5 的机械投影）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Protocol


class Verdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"                # 阻断（blocking 门）
    SKIP = "skip"                # 本 R 级/本波次不适用
    NOT_CONFIGURED = "not_configured"
    INCONCLUSIVE = "inconclusive"  # 无法判定 → 不得放行，升级处置


class AdmissionDecisionKind(str, Enum):
    ADMIT = "admit"
    REJECT = "reject"
    ESCALATE = "escalate"        # 判据不可信/弃权 → 降自治级别，人类介入（INV15）


VERIFIER_ROLES = frozenset({"verifier", "architect", "human", "ci", "sandbox"})


class EvidenceRejected(Exception):
    """证据来源非法：验证性证据由生成侧（builder）产出。"""

    def __init__(self, kind: str, producer: str):
        self.kind = kind
        self.producer = producer
        super().__init__(
            f"evidence '{kind}' produced by '{producer}' is not admissible "
            f"(verifier-side roles only: {sorted(VERIFIER_ROLES)})"
        )


@dataclass
class EvidenceItem:
    """带来源的证据。gate 只信任判别侧角色产出的证据。"""
    kind: str
    producer_role: str
    payload: dict = field(default_factory=dict)


@dataclass
class GateContext:
    wave_id: str
    instance_id: str
    touched_paths: list[str] = field(default_factory=list)   # 实例改动的制品
    evidence: dict[str, EvidenceItem] = field(default_factory=dict)
    config: dict = field(default_factory=dict)               # 门禁参数（预算阈值等）

    def verified_evidence(self, kind: str) -> dict:
        item = self.evidence.get(kind)
        if item is None:
            raise KeyError(f"missing evidence '{kind}'")
        if item.producer_role not in VERIFIER_ROLES:
            raise EvidenceRejected(kind, item.producer_role)
        return item.payload


class Gate(Protocol):
    gate_id: str
    description: str

    def evaluate(self, ctx: GateContext) -> "GateResult": ...


@dataclass
class GateResult:
    gate_id: str
    verdict: Verdict
    blocking: bool = True
    reason: str = ""
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "gate_id": self.gate_id,
            "verdict": self.verdict.value,
            "blocking": self.blocking,
            "reason": self.reason,
            "details": self.details,
        }


def adjudicate(hard_results: list[GateResult],
               soft_vetoes: int = 0,
               soft_abstains: int = 0) -> AdmissionDecisionKind:
    """门禁代数的判定函数（纯函数，可独立测试）。

    规则（INV4/INV15）：
    1. 任一 blocking H FAIL → REJECT（S 无法救场）
    2. 任一 blocking H INCONCLUSIVE → ESCALATE（不得放行）
    3. S veto（H 全过后）→ REJECT
    4. S abstain 未被人类处置 → ESCALATE
    5. 否则 ADMIT
    """
    for r in hard_results:
        if not r.blocking:
            continue
        if r.verdict == Verdict.FAIL:
            return AdmissionDecisionKind.REJECT
    for r in hard_results:
        if not r.blocking:
            continue
        if r.verdict == Verdict.INCONCLUSIVE:
            return AdmissionDecisionKind.ESCALATE
    if soft_vetoes > 0:
        return AdmissionDecisionKind.REJECT
    if soft_abstains > 0:
        return AdmissionDecisionKind.ESCALATE
    return AdmissionDecisionKind.ADMIT
