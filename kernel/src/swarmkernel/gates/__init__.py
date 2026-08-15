"""Gate layer: the eight hard gates, the soft veto gate, and the algebra that
combines them."""

from .algebra import REQUIRED_GATES_BY_RLEVEL, admit, build_hard_report, decide
from .base import Gate, GateContext, GateRegistry, missing_evidence
from .hard import (
    ALL_HARD_GATES,
    H1Build,
    H2UnitProperty,
    H3Holdout,
    H4ContractSurface,
    H5Differential,
    H6Invariant,
    H7Drift,
    H8Budget,
    default_registry,
    witness_kinds_satisfied,
)
from .soft import JudgeFitness, SoftGateEngine, aggregate, cohens_kappa

__all__ = [
    "REQUIRED_GATES_BY_RLEVEL",
    "admit",
    "build_hard_report",
    "decide",
    "Gate",
    "GateContext",
    "GateRegistry",
    "missing_evidence",
    "ALL_HARD_GATES",
    "H1Build",
    "H2UnitProperty",
    "H3Holdout",
    "H4ContractSurface",
    "H5Differential",
    "H6Invariant",
    "H7Drift",
    "H8Budget",
    "default_registry",
    "witness_kinds_satisfied",
    "JudgeFitness",
    "SoftGateEngine",
    "aggregate",
    "cohens_kappa",
]
