"""In-process contract bus.

Small on purpose. Its whole job is to make three failure modes *impossible*
rather than *discouraged*:

1. Delivering an artefact to a role that must not see it.
2. Delivering a payload whose contract version the receiver cannot understand.
3. Losing the record of who saw what.

Everything else — transport, persistence, retries — belongs to an adapter. The
kernel bus is synchronous and deterministic so that inter-contract handoffs can
be unit-tested end to end without a runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence

from ..contracts.base import ArtifactClass, Contract, Role, SemVer
from ..contracts import CONTRACT_REGISTRY
from .envelope import Envelope
from .policy import AsymmetryPolicy, Capability, PolicyDecision

__all__ = ["Subscription", "DeliveryRecord", "DeliveryError", "ContractBus"]

Handler = Callable[[Envelope, Contract], None]


class DeliveryError(RuntimeError):
    """Raised on a *policy* refusal. Never swallowed: a refused delivery that
    looks like a successful one is how asymmetry leaks."""


@dataclass(frozen=True)
class Subscription:
    subscriber_id: str
    role: Role
    artifact_classes: frozenset[ArtifactClass]
    handler: Handler
    accepts_major: int = 1

    def accepts(self, envelope: Envelope) -> bool:
        return (
            envelope.header.payload_class in self.artifact_classes
            and envelope.header.major() == self.accepts_major
        )


@dataclass
class DeliveryRecord:
    """Audit row. The bus keeps one for *every* attempt, including refusals —
    a refusal is the most interesting event in the log."""

    message_id: str
    contract_type: str
    payload_class: ArtifactClass
    sender_role: Role
    sender_identity: str
    recipient_id: str | None
    recipient_role: Role | None
    delivered: bool
    reason: str = ""
    payload_digest: str = ""


@dataclass
class ContractBus:
    policy: AsymmetryPolicy = field(default_factory=AsymmetryPolicy)
    strict: bool = True
    """If True, a policy refusal on an explicitly addressed message raises."""

    _subs: list[Subscription] = field(default_factory=list)
    _log: list[DeliveryRecord] = field(default_factory=list)

    # ------------------------------------------------------------ management

    def subscribe(
        self,
        subscriber_id: str,
        role: Role,
        artifact_classes: Iterable[ArtifactClass],
        handler: Handler,
        accepts_major: int = 1,
    ) -> Subscription:
        requested = frozenset(artifact_classes)
        # Refuse the subscription itself if the role cannot read the class.
        # Failing at subscribe time turns a runtime leak into a wiring error,
        # which is discovered by the first test run instead of in production.
        for ac in sorted(requested, key=lambda a: a.value):
            decision = self.policy.can_read(role, ac)
            if not decision.allowed:
                raise DeliveryError(
                    f"{subscriber_id!r} cannot subscribe to {ac.value!r}: {decision.reason}"
                )
        sub = Subscription(subscriber_id, role, requested, handler, accepts_major)
        self._subs.append(sub)
        return sub

    def unsubscribe(self, subscriber_id: str) -> None:
        self._subs = [s for s in self._subs if s.subscriber_id != subscriber_id]

    @property
    def audit_log(self) -> Sequence[DeliveryRecord]:
        return tuple(self._log)

    # ------------------------------------------------------------- delivery

    def _decode(self, envelope: Envelope) -> Contract:
        cls = CONTRACT_REGISTRY.get(envelope.header.contract_type)
        if cls is None:
            raise DeliveryError(
                f"unknown contract type {envelope.header.contract_type!r}; "
                "the registry is closed by design"
            )
        expected_major = SemVer.parse(cls.CONTRACT_VERSION).major
        if envelope.header.major() != expected_major:
            raise DeliveryError(
                f"contract-major mismatch for {envelope.header.contract_type}: "
                f"envelope v{envelope.header.contract_version}, "
                f"local v{cls.CONTRACT_VERSION}"
            )
        if cls.ARTIFACT_CLASS is not envelope.header.payload_class:
            raise DeliveryError(
                f"artefact class {envelope.header.payload_class.value!r} does not "
                f"match the declared class of {cls.__name__} "
                f"({cls.ARTIFACT_CLASS.value!r}); relabelling is refused"
            )
        return cls.model_validate(envelope.payload)

    def _record(self, envelope: Envelope, sub_id: str | None, role: Role | None,
                delivered: bool, reason: str = "") -> None:
        self._log.append(
            DeliveryRecord(
                message_id=envelope.header.message_id,
                contract_type=envelope.header.contract_type,
                payload_class=envelope.header.payload_class,
                sender_role=envelope.header.sender_role,
                sender_identity=envelope.header.sender_identity,
                recipient_id=sub_id,
                recipient_role=role,
                delivered=delivered,
                reason=reason,
                payload_digest=envelope.payload_digest,
            )
        )

    def _authorise_send(self, envelope: Envelope) -> PolicyDecision:
        h = envelope.header
        write = self.policy.can_write(h.sender_role, h.payload_class)
        if not write.allowed:
            return write
        return self.policy.check_separation(
            sender_role=h.sender_role,
            sender_identity=h.sender_identity,
            recipient_role=h.recipient_role,
            recipient_identity=h.recipient_identity,
            artifact=h.payload_class,
            subject_identity=h.recipient_identity,
        )

    def publish(self, envelope: Envelope) -> list[str]:
        """Fan out to every eligible subscriber. Returns delivered subscriber ids."""

        if not envelope.verify():
            raise DeliveryError("payload digest mismatch: envelope was tampered with")

        allowed = self._authorise_send(envelope)
        if not allowed.allowed:
            self._record(envelope, None, None, False, allowed.reason)
            raise DeliveryError(allowed.reason)

        contract = self._decode(envelope)
        delivered: list[str] = []
        for sub in list(self._subs):
            if not sub.accepts(envelope):
                continue
            if (
                envelope.header.recipient_identity is not None
                and envelope.header.recipient_identity != sub.subscriber_id
            ):
                continue
            if (
                envelope.header.recipient_role is not None
                and envelope.header.recipient_role is not sub.role
            ):
                continue
            read = self.policy.can_read(sub.role, envelope.header.payload_class)
            if not read.allowed:
                self._record(envelope, sub.subscriber_id, sub.role, False, read.reason)
                if self.strict and envelope.header.recipient_identity == sub.subscriber_id:
                    raise DeliveryError(read.reason)
                continue
            sep = self.policy.check_separation(
                sender_role=envelope.header.sender_role,
                sender_identity=envelope.header.sender_identity,
                recipient_role=sub.role,
                recipient_identity=sub.subscriber_id,
                artifact=envelope.header.payload_class,
                subject_identity=envelope.header.recipient_identity,
            )
            if not sep.allowed:
                self._record(envelope, sub.subscriber_id, sub.role, False, sep.reason)
                if self.strict and envelope.header.recipient_identity == sub.subscriber_id:
                    raise DeliveryError(sep.reason)
                continue
            sub.handler(envelope, contract)
            self._record(envelope, sub.subscriber_id, sub.role, True)
            delivered.append(sub.subscriber_id)

        if not delivered:
            self._record(envelope, None, None, False, "no eligible subscriber")
        return delivered

    def send(self, envelope: Envelope) -> str:
        """Point-to-point. Fails loudly if the single recipient did not receive."""

        if envelope.header.recipient_identity is None:
            raise DeliveryError("send() requires an explicit recipient_identity")
        delivered = self.publish(envelope)
        if envelope.header.recipient_identity not in delivered:
            raise DeliveryError(
                f"recipient {envelope.header.recipient_identity!r} did not receive "
                f"message {envelope.header.message_id!r}"
            )
        return envelope.header.recipient_identity

    # ------------------------------------------------------------- forensics

    def who_saw(self, payload_class: ArtifactClass) -> set[str]:
        return {
            r.recipient_id
            for r in self._log
            if r.payload_class is payload_class and r.delivered and r.recipient_id
        }

    def refusals(self) -> list[DeliveryRecord]:
        return [r for r in self._log if not r.delivered and r.reason]

    def view_of(self, subscriber_id: str) -> set[str]:
        """Digests this subscriber has actually seen. Used to assert
        ``View(builder) ∩ View(verifier) ⊆ public`` in tests."""

        return {
            r.payload_digest
            for r in self._log
            if r.recipient_id == subscriber_id and r.delivered
        }
