from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from pydantic import BaseModel, Field

from swarmdev.contracts.ids import new_id
from swarmdev.contracts.roles import CapabilityToken, Role


class EnvelopeKind(str, Enum):
    SPEC_ASSIGNMENT = "spec_assignment"          # spec-delta -> builder
    INSTANCE_SUBMISSION = "instance_submission"  # builder -> verifier
    GATE_RESULTS = "gate_results"                # verifier -> leader
    JUDGE_REQUEST = "judge_request"              # verifier -> judge
    JUDGE_VERDICT = "judge_verdict"              # judge -> verifier
    HOLDOUT_RESULTS = "holdout_results"          # verifier 内部（含 holdout 内容）
    MEASUREMENT_REPORT = "measurement_report"    # verifier -> spec moderator
    SPEC_CONVERGENCE = "spec_convergence"        # spec moderator -> spec steward
    DRIFT_ALERT = "drift_alert"                  # reconciler -> leader
    ADMISSION_RECEIPT = "admission_receipt"      # leader -> all persistent roles
    MEMORY_WRITE_REQUEST = "memory_write_request"  # any -> spec moderator 裁定
    RULE_PROPOSAL = "rule_proposal"              # deep agent -> human
    WAVE_PLAN = "wave_plan"                      # architect -> leader

# 每类信封的可见接收角色（信息不对称是硬约束）。
# 关键不变量：builder 永不出现在任何含判据/测量/holdout 内容的信封接收方。
RECEIVER_MATRIX: dict[EnvelopeKind, frozenset[Role]] = {
    EnvelopeKind.SPEC_ASSIGNMENT: frozenset({Role.BUILDER, Role.LEADER}),
    EnvelopeKind.INSTANCE_SUBMISSION: frozenset({Role.VERIFIER, Role.LEADER}),
    EnvelopeKind.GATE_RESULTS: frozenset({Role.LEADER, Role.ARCHITECT}),
    EnvelopeKind.JUDGE_REQUEST: frozenset({Role.JUDGE}),
    EnvelopeKind.JUDGE_VERDICT: frozenset({Role.VERIFIER, Role.LEADER}),
    EnvelopeKind.HOLDOUT_RESULTS: frozenset({Role.VERIFIER, Role.ARCHITECT}),
    EnvelopeKind.MEASUREMENT_REPORT: frozenset({Role.SPEC_MODERATOR, Role.ARCHITECT}),
    EnvelopeKind.SPEC_CONVERGENCE: frozenset({Role.SPEC_STEWARD, Role.HUMAN}),
    EnvelopeKind.DRIFT_ALERT: frozenset({Role.LEADER, Role.HUMAN}),
    EnvelopeKind.ADMISSION_RECEIPT: frozenset(
        {Role.LEADER, Role.ARCHITECT, Role.SPEC_STEWARD, Role.MODERATOR, Role.HUMAN}
    ),
    EnvelopeKind.MEMORY_WRITE_REQUEST: frozenset({Role.SPEC_MODERATOR}),
    EnvelopeKind.RULE_PROPOSAL: frozenset({Role.HUMAN}),
    EnvelopeKind.WAVE_PLAN: frozenset({Role.LEADER}),
}

# 信封 kind -> 发送方必须持有的能力
SEND_REQUIREMENTS: dict[EnvelopeKind, str] = {
    EnvelopeKind.SPEC_ASSIGNMENT: "wave.plan",
    EnvelopeKind.INSTANCE_SUBMISSION: "instance.build",
    EnvelopeKind.GATE_RESULTS: "gate.execute",
    EnvelopeKind.JUDGE_REQUEST: "gate.execute",
    EnvelopeKind.JUDGE_VERDICT: "judge.verdict.write",
    EnvelopeKind.HOLDOUT_RESULTS: "holdout.read",
    EnvelopeKind.MEASUREMENT_REPORT: "gate.execute",
    EnvelopeKind.SPEC_CONVERGENCE: "spec.l2.write",
    EnvelopeKind.DRIFT_ALERT: "drift.report",
    EnvelopeKind.ADMISSION_RECEIPT: "admission.decide",
    EnvelopeKind.MEMORY_WRITE_REQUEST: "spec.read",
    EnvelopeKind.RULE_PROPOSAL: "rule.proposal",
    EnvelopeKind.WAVE_PLAN: "wave.plan",
}


class VisibilityError(PermissionError):
    pass


class Envelope(BaseModel):
    env_id: str
    kind: EnvelopeKind
    sender: str = Field(description="发送者 subject_id")
    sender_role: Role
    recipients: list[Role]
    payload: dict[str, Any] = Field(default_factory=dict)
    trace_id: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ContractBus:
    """契约间通信总线：按 RECEIVER_MATRIX 与能力令牌强制信息不对称。"""

    def __init__(self) -> None:
        self._log: list[Envelope] = []
        self._subscribers: dict[Role, list[Callable[[Envelope], None]]] = defaultdict(list)

    def subscribe(self, role: Role, handler: Callable[[Envelope], None]) -> None:
        self._subscribers[role].append(handler)

    def publish(self, token: CapabilityToken, kind: EnvelopeKind,
                payload: dict[str, Any], recipients: list[Role],
                trace_id: str = "") -> Envelope:
        required = SEND_REQUIREMENTS.get(kind)
        if required:
            token.require(required)
        allowed = RECEIVER_MATRIX[kind]
        for r in recipients:
            if r not in allowed:
                raise VisibilityError(
                    f"envelope {kind.value} must not be visible to role {r.value}"
                )
        env = Envelope(
            env_id=new_id("env"), kind=kind, sender=token.subject_id,
            sender_role=token.role, recipients=list(recipients),
            payload=payload, trace_id=trace_id,
        )
        self._log.append(env)
        for r in recipients:
            for h in self._subscribers.get(r, []):
                h(env)
        return env

    def query(self, token: CapabilityToken, kind: EnvelopeKind) -> list[Envelope]:
        """按角色能力读取历史信封；builder 永远查不到判据/holdout 类信封。"""
        allowed = RECEIVER_MATRIX.get(kind, frozenset())
        if token.role not in allowed and token.role != Role.HUMAN:
            raise VisibilityError(
                f"role {token.role.value} may not read envelopes of kind {kind.value}"
            )
        return [e for e in self._log if e.kind == kind]

    def audit_stream(self) -> list[Envelope]:
        return list(self._log)
