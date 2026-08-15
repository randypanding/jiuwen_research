from __future__ import annotations

import dataclasses

from swarmfoundry.schema.envelope import SwarmEnvelope, assert_information_asymmetry, next_envelope_id


class BusError(RuntimeError):
    pass


@dataclasses.dataclass
class Subscription:
    role: str
    method_prefix: str
    handler: object


class SwarmBus:
    """In-process deterministic message bus implementing contract C10 transport
    semantics. Production binding maps 1:1 onto agent-core TeamRuntime
    (send -> P2P by recipient role, publish -> PubSub topic) and jiuwenswarm
    E2AEnvelope WS methods; this object is the reference implementation used by
    contract-communication tests."""

    def __init__(self):
        self._subs: list[Subscription] = []
        self.ledger: list[SwarmEnvelope] = []
        self.delivered: list[tuple[str, SwarmEnvelope]] = []

    def subscribe(self, role: str, method_prefix: str, handler) -> None:
        self._subs.append(Subscription(role=role, method_prefix=method_prefix, handler=handler))

    def send(
        self,
        *,
        sender_role: str,
        recipient_role: str,
        method: str,
        payload: dict,
        correlation_id: str = "",
        envelope_id: str | None = None,
    ) -> SwarmEnvelope:
        env = SwarmEnvelope(
            envelope_id=envelope_id or next_envelope_id(),
            sender_role=sender_role,
            recipient_role=recipient_role,
            method=method,
            payload=payload,
            correlation_id=correlation_id,
        )
        assert_information_asymmetry(env)
        self.ledger.append(env)
        matched = False
        for sub in self._subs:
            if sub.role == env.recipient_role and env.method.startswith(sub.method_prefix):
                sub.handler(env)
                self.delivered.append((sub.role, env))
                matched = True
        if not matched:
            raise BusError(f"no subscriber for role={env.recipient_role} method={env.method}")
        return env
