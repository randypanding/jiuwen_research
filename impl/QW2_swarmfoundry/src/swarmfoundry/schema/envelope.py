from __future__ import annotations

import dataclasses
import itertools

from swarmfoundry.schema import ALL_ROLES, SCHEMA_VERSION
from swarmfoundry.schema.base import (
    SchemaError,
    check_schema_version,
    require,
)

METHOD_TASK_ASSIGN = "task.assign"
METHOD_TASK_INSTANCES_READY = "task.instances_ready"
METHOD_VERIFY_REQUEST = "verify.request"
METHOD_GATE_RESULT = "gate.result"
METHOD_JUDGE_VERDICT = "judge.verdict"
METHOD_ADMISSION_DECISION = "admission.decision"
METHOD_MEASUREMENT_EVENT = "measurement.event"
METHOD_SPEC_DELTA_PROPOSAL = "spec_delta.proposal"
METHOD_RULE_PROPOSAL = "rule.proposal"
METHOD_HEALTH_METRICS = "health.metrics"
METHOD_RECEIPT_REGISTERED = "receipt.registered"

KNOWN_METHODS = (
    METHOD_TASK_ASSIGN,
    METHOD_TASK_INSTANCES_READY,
    METHOD_VERIFY_REQUEST,
    METHOD_GATE_RESULT,
    METHOD_JUDGE_VERDICT,
    METHOD_ADMISSION_DECISION,
    METHOD_MEASUREMENT_EVENT,
    METHOD_SPEC_DELTA_PROPOSAL,
    METHOD_RULE_PROPOSAL,
    METHOD_HEALTH_METRICS,
    METHOD_RECEIPT_REGISTERED,
)

_seq = itertools.count(1)


def next_envelope_id() -> str:
    return f"env-{next(_seq):08d}"


@dataclasses.dataclass(frozen=True)
class SwarmEnvelope:
    """Contract C10. Mirrors agent-core MessageEnvelope / jiuwenswarm E2AEnvelope
    semantics (sender/recipient/method/payload/correlation) so the swarm-side
    transport can wrap it 1:1."""

    envelope_id: str
    sender_role: str
    recipient_role: str
    method: str
    payload: dict
    correlation_id: str = ""
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "envelope_id": self.envelope_id,
            "sender_role": self.sender_role,
            "recipient_role": self.recipient_role,
            "method": self.method,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SwarmEnvelope":
        where = "SwarmEnvelope"
        check_schema_version(data, where)
        sender = require(data, "sender_role", str, where)
        recipient = require(data, "recipient_role", str, where)
        if sender not in ALL_ROLES:
            raise SchemaError(f"{where}: unknown sender_role {sender!r}")
        if recipient not in ALL_ROLES:
            raise SchemaError(f"{where}: unknown recipient_role {recipient!r}")
        method = require(data, "method", str, where)
        if method not in KNOWN_METHODS:
            raise SchemaError(f"{where}: unknown method {method!r}")
        payload = data.get("payload")
        if not isinstance(payload, dict):
            raise SchemaError(f"{where}: payload must be a dict")
        return cls(
            envelope_id=require(data, "envelope_id", str, where),
            sender_role=sender,
            recipient_role=recipient,
            method=method,
            payload=payload,
            correlation_id=data.get("correlation_id", ""),
        )


class ProtocolViolation(SchemaError):
    pass


def assert_information_asymmetry(env: SwarmEnvelope) -> None:
    """Enforce structure.md §7 information-asymmetry discipline at message level:
    builders never receive holdout content, verdicts, or judge rubrics; generators
    never send judge/verdict/admission messages."""
    holdout_markers = ("holdout", "rubric", "verdict", "gate.result", "admission")
    if env.recipient_role == "builder":
        if env.method in (METHOD_GATE_RESULT, METHOD_JUDGE_VERDICT, METHOD_ADMISSION_DECISION):
            raise ProtocolViolation(f"builder must not receive {env.method}")
        blob = (str(env.payload)).lower()
        if any(m in blob for m in ("holdout_scenarios", "judge_rubric")):
            raise ProtocolViolation("builder-bound envelope leaks holdout/judge material")
    if env.sender_role == "builder" and env.method in (
        METHOD_GATE_RESULT,
        METHOD_JUDGE_VERDICT,
        METHOD_ADMISSION_DECISION,
    ):
        raise ProtocolViolation("generator must not participate in discrimination")
