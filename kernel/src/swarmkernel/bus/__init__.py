"""Contract bus: envelopes, information-asymmetry policy, and routing."""

from .bus import ContractBus, DeliveryError, DeliveryRecord, Subscription
from .envelope import Envelope, EnvelopeHeader, seal
from .policy import DEFAULT_MATRIX, AsymmetryPolicy, Capability, PolicyDecision

__all__ = [
    "ContractBus",
    "DeliveryError",
    "DeliveryRecord",
    "Subscription",
    "Envelope",
    "EnvelopeHeader",
    "seal",
    "DEFAULT_MATRIX",
    "AsymmetryPolicy",
    "Capability",
    "PolicyDecision",
]
