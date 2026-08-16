"""Message envelope for inter-contract communication.

The envelope carries everything a policy decision needs *without* looking at
the payload. That is deliberate: a routing decision that has to inspect content
is a routing decision that can be fooled by content.
"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field, field_validator, model_validator

from ..contracts.base import (
    ArtifactClass,
    Contract,
    Role,
    SemVer,
    digest_of,
    utcnow,
)

__all__ = ["Envelope", "EnvelopeHeader", "seal"]


class EnvelopeHeader(Contract):
    """Routing metadata. Immutable once sealed."""

    ARTIFACT_CLASS: ClassVar[ArtifactClass] = ArtifactClass.EVIDENCE_RECEIPT

    message_id: str
    contract_type: str
    """Registry name of the payload contract, e.g. ``SpecDelta``."""
    contract_version: str = "1.0.0"
    payload_class: ArtifactClass
    sender_role: Role
    sender_identity: str
    recipient_role: Role | None = None
    recipient_identity: str | None = None
    wave_id: str | None = None
    unit_id: str | None = None
    causation_id: str | None = None
    """Message this one is a reply to. Makes handoff chains auditable."""
    correlation_id: str | None = None
    sent_at: str = Field(default_factory=lambda: utcnow().isoformat())

    @field_validator("contract_version")
    @classmethod
    def _valid_version(cls, v: str) -> str:
        SemVer.parse(v)
        return v

    def major(self) -> int:
        return SemVer.parse(self.contract_version).major


class Envelope(Contract):
    """A sealed message. ``payload_digest`` is computed at construction and
    re-checked on delivery, so an intermediary cannot rewrite a payload without
    the receiver noticing."""

    ARTIFACT_CLASS: ClassVar[ArtifactClass] = ArtifactClass.EVIDENCE_RECEIPT

    header: EnvelopeHeader
    payload: dict[str, Any]
    payload_digest: str = ""

    @model_validator(mode="after")
    def _seal(self) -> "Envelope":
        computed = digest_of(self.payload)
        if not self.payload_digest:
            object.__setattr__(self, "payload_digest", computed)
        elif self.payload_digest != computed:
            raise ValueError(
                "payload_digest does not match payload; the envelope was tampered with"
            )
        return self

    def verify(self) -> bool:
        return self.payload_digest == digest_of(self.payload)


def seal(
    *,
    message_id: str,
    contract: Contract,
    sender_role: Role,
    sender_identity: str,
    recipient_role: Role | None = None,
    recipient_identity: str | None = None,
    wave_id: str | None = None,
    unit_id: str | None = None,
    causation_id: str | None = None,
    correlation_id: str | None = None,
) -> Envelope:
    """Build an envelope from a contract instance.

    The artefact class is read off the contract *class*, never supplied by the
    caller. A sender therefore cannot relabel a holdout oracle as a public one.
    """

    return Envelope(
        header=EnvelopeHeader(
            message_id=message_id,
            contract_type=type(contract).__name__,
            contract_version=type(contract).CONTRACT_VERSION,
            payload_class=type(contract).ARTIFACT_CLASS,
            sender_role=sender_role,
            sender_identity=sender_identity,
            recipient_role=recipient_role,
            recipient_identity=recipient_identity,
            wave_id=wave_id,
            unit_id=unit_id,
            causation_id=causation_id,
            correlation_id=correlation_id,
        ),
        payload=contract.model_dump(mode="json"),
    )
