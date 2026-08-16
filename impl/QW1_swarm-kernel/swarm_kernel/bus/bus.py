from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from swarm_kernel.contracts.base import (
    Confidentiality,
    ContractEnvelope,
    GENERATOR_ROLES,
    JUDGE_ROLES,
    Role,
)


@dataclass
class Subscription:
    subscriber: str
    role: Role
    topic: str
    handler: Callable[[ContractEnvelope], None]
    session_scope: str = "default_context_id"


@dataclass
class AuditRecord:
    envelope_id: str
    schema: str
    producer_role: str
    subscriber: str
    action: str
    reason: str = ""


class IsolationViolation(Exception):
    pass


def default_acl(envelope: ContractEnvelope, role: Role) -> tuple[bool, str]:
    conf = envelope.confidentiality
    if conf == Confidentiality.HOLDOUT and role in GENERATOR_ROLES:
        return False, "holdout invisible to builders"
    if conf == Confidentiality.HOLDOUT and role not in (Role.VERIFIER, Role.ARCHITECT, Role.SYSTEM, Role.HUMAN):
        return False, "holdout restricted to verifier/architect"
    if conf == Confidentiality.JUDGE_INTERNAL and role in GENERATOR_ROLES:
        return False, "judge internals invisible to builders"
    if conf == Confidentiality.JUDGE_INTERNAL and role not in JUDGE_ROLES | {Role.SYSTEM}:
        return False, "judge internals restricted to judge side"
    if conf == Confidentiality.MEMORY_RESTRICTED and role == Role.BUILDER:
        return False, "temporary builders write no memory"
    if envelope.schema_name == "JudgeVerdict" and envelope.producer_role in GENERATOR_ROLES:
        return False, "generators must not participate in judging"
    if envelope.schema_name == "HoldoutScenario" and role in GENERATOR_ROLES:
        return False, "holdout scenarios invisible to builders"
    if envelope.schema_name == "MemoryWrite" and envelope.producer_role == Role.BUILDER:
        return False, "builder memory writes must go through adjudication"
    return True, ""


class ContractBus:
    def __init__(self, acl: Optional[Callable[[ContractEnvelope, Role], tuple[bool, str]]] = None) -> None:
        self._subs: dict[str, list[Subscription]] = {}
        self._audit: list[AuditRecord] = []
        self._acl = acl or default_acl

    def subscribe(self, topic: str, subscriber: str, role: Role, handler: Callable[[ContractEnvelope], None], session_scope: str = "default_context_id") -> None:
        self._subs.setdefault(topic, []).append(Subscription(subscriber, role, topic, handler, session_scope))

    def publish(self, envelope: ContractEnvelope, strict: bool = True) -> list[str]:
        delivered: list[str] = []
        if not envelope.payload_sha256:
            envelope.seal()
        for sub in self._subs.get(envelope.topic, []):
            allowed, reason = self._acl(envelope, sub.role)
            scope_ok = sub.session_scope == envelope.session_scope or sub.session_scope == "*"
            if allowed and scope_ok:
                sub.handler(envelope)
                delivered.append(sub.subscriber)
                self._audit.append(AuditRecord(envelope.envelope_id, envelope.schema_name, envelope.producer_role.value, sub.subscriber, "deliver"))
            else:
                why = reason if allowed else "session_scope mismatch"
                if not allowed:
                    why = reason
                self._audit.append(AuditRecord(envelope.envelope_id, envelope.schema_name, envelope.producer_role.value, sub.subscriber, "deny", why))
                if strict and not allowed and reason != "":
                    continue
        return delivered

    def audit_log(self) -> list[AuditRecord]:
        return list(self._audit)

    def denials(self) -> list[AuditRecord]:
        return [r for r in self._audit if r.action == "deny"]


def envelope_to_ndjson(envelope: ContractEnvelope) -> str:
    return json.dumps(envelope.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)


def envelope_from_ndjson(line: str) -> ContractEnvelope:
    return ContractEnvelope.model_validate(json.loads(line))


class FileRelay:
    def __init__(self, root: str | Path, bus: Optional[ContractBus] = None) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.bus = bus or ContractBus()

    def send(self, envelope: ContractEnvelope) -> Path:
        if not envelope.payload_sha256:
            envelope.seal()
        target = self.root / f"{envelope.topic}.ndjson"
        with target.open("a", encoding="utf-8") as f:
            f.write(envelope_to_ndjson(envelope) + "\n")
        return target

    def receive(self, role: Role, topic: Optional[str] = None, strict: bool = True) -> tuple[list[ContractEnvelope], list[AuditRecord]]:
        accepted: list[ContractEnvelope] = []
        denials: list[AuditRecord] = []
        files = [self.root / f"{topic}.ndjson"] if topic else sorted(self.root.glob("*.ndjson"))
        for fp in files:
            if not fp.exists():
                continue
            for line in fp.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                env = envelope_from_ndjson(line)
                if not env.verify_seal():
                    denials.append(AuditRecord(env.envelope_id, env.schema_name, env.producer_role.value, role.value, "deny", "seal broken"))
                    if strict:
                        raise IsolationViolation(f"broken seal on {env.envelope_id}")
                    continue
                allowed, reason = self.bus._acl(env, role)
                if allowed:
                    accepted.append(env)
                else:
                    denials.append(AuditRecord(env.envelope_id, env.schema_name, env.producer_role.value, role.value, "deny", reason))
        return accepted, denials
