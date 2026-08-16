from __future__ import annotations

from collections import defaultdict
from typing import Callable

from opc.schemas.events import Envelope, Topic

ROUTING_TABLE: frozenset[tuple[str, str, Topic]] = frozenset(
    {
        ("architect", "leader", Topic.TASK_ASSIGN),
        ("leader", "builder", Topic.TASK_ASSIGN),
        ("builder", "verifier", Topic.INSTANCE_SUBMIT),
        ("verifier", "leader", Topic.GATE_REPORT),
        ("verifier", "spec_moderator", Topic.MEASUREMENT_REPORT),
        ("critic", "architect", Topic.MEASUREMENT_REPORT),
        ("spec_moderator", "spec_steward", Topic.SPEC_CONVERGE),
        ("reconciler", "leader", Topic.DRIFT_ALARM),
        ("deep_agent", "human_gateway", Topic.PROPOSAL_SUBMIT),
        ("leader", "human_gateway", Topic.WAIVER_REQUEST),
        ("world", "leader", Topic.ADMIT_COMMIT),
    }
)

FORBIDDEN_TO_BUILDER_KEYS: frozenset[str] = frozenset(
    {
        "scenarios",
        "holdout",
        "rubric",
        "rubric_text",
        "judge_verdict",
        "expected_outputs",
        "golden_outputs",
        "holdout_hashes",
    }
)

JUDGE_SIDE_ROLES: frozenset[str] = frozenset({"verifier", "spec_moderator", "architect"})


class RoutingViolation(Exception):
    """Raised when an envelope breaks the routing law or the information
    asymmetry discipline. Violations are recorded and blocked, never
    silently delivered."""


class EventBus:
    """The only legal carrier of inter-contract messages.

    Enforced invariants:
      1. (src, dst, topic) must be in ROUTING_TABLE - there is no ad-hoc
         channel between roles;
      2. builders receive nothing but TASK_ASSIGN, and their payloads are
         scanned for oracle-side keys (holdout / rubric / verdicts);
      3. INSTANCE_SUBMIT may never be addressed to judge-side roles by a
         generator;
      4. every envelope is journaled with its content hash for audit.
    """

    def __init__(self, extra_routes: set[tuple[str, str, Topic]] | None = None):
        self.routes: frozenset[tuple[str, str, Topic]] = ROUTING_TABLE | frozenset(extra_routes or set())
        self.journal: list[Envelope] = []
        self.violations: list[dict] = []
        self._subscribers: dict[tuple[str, Topic], list[Callable[[Envelope], None]]] = defaultdict(list)

    def subscribe(self, role: str, topic: Topic, handler: Callable[[Envelope], None]) -> None:
        self._subscribers[(role, topic)].append(handler)

    def publish(self, envelope: Envelope) -> None:
        route = (envelope.src_role, envelope.dst_role, envelope.topic)
        if route not in self.routes:
            self._record_violation(envelope, f"illegal route {route}")
            raise RoutingViolation(f"illegal route {route}")

        if envelope.dst_role == "builder":
            if envelope.topic is not Topic.TASK_ASSIGN:
                self._record_violation(envelope, f"builder received non-task topic {envelope.topic}")
                raise RoutingViolation("builders may only receive TASK_ASSIGN")
            leaked = FORBIDDEN_TO_BUILDER_KEYS & set(envelope.payload.keys())
            if leaked:
                self._record_violation(envelope, f"oracle-side keys in builder payload: {sorted(leaked)}")
                raise RoutingViolation(f"oracle-side keys in builder payload: {sorted(leaked)}")

        if envelope.topic is Topic.INSTANCE_SUBMIT and envelope.src_role != "builder":
            self._record_violation(envelope, "INSTANCE_SUBMIT must originate from the builder")
            raise RoutingViolation("INSTANCE_SUBMIT must originate from the builder")

        self.journal.append(envelope)
        for handler in self._subscribers.get((envelope.dst_role, envelope.topic), []):
            handler(envelope)

    def _record_violation(self, envelope: Envelope, reason: str) -> None:
        self.violations.append(
            {
                "envelope_id": envelope.envelope_id,
                "topic": envelope.topic.value,
                "src": envelope.src_role,
                "dst": envelope.dst_role,
                "reason": reason,
                "digest": envelope.digest(),
            }
        )

    def audit(self) -> list[dict]:
        return [
            {"seq": i, "envelope_id": e.envelope_id, "topic": e.topic.value, "src": e.src_role, "dst": e.dst_role, "digest": e.digest()}
            for i, e in enumerate(self.journal)
        ]
