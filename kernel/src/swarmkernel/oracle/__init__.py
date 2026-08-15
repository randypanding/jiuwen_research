"""Oracle engines: don't-care masking, differential comparison, contract
surface extraction and compatibility, golden management, traceability, and
oracle strength auditing.

Every engine in this package is deterministic and offline. No engine calls a
model. Where a model would be needed (semantic refinement, semantic drift) the
engine exposes a hook and reports ``UNKNOWN`` rather than guessing — an oracle
that guesses is worse than no oracle, because it is trusted.
"""

from .compat import Change, SemanticResult, classify, classify_json_schema
from .differ import DifferentialEngine, DifferentialInput, EquivalenceLevel
from .dontcare import DontCareMask, NORMALIZERS, Selector, normalize_observation
from .golden import (
    GoldenComparison,
    GoldenMode,
    GoldenStore,
    GoldenStoreWriteError,
    GoldenSuite,
    R3Info,
    capture_r3info,
)
from .strength import MutationOutcome, OracleAuditor, StrengthReport, run_mutation_probes
from .surface import (
    ClassSurface,
    FunctionSurface,
    ModuleSurface,
    attach_schema_surface,
    extract_module_surface,
    extract_surface,
)
from .traceability import (
    AnchorResolver,
    DriftFinding,
    DriftKind,
    Exemption,
    TraceabilityEngine,
    build_anchor,
)

__all__ = [
    "Change",
    "SemanticResult",
    "classify",
    "classify_json_schema",
    "DifferentialEngine",
    "DifferentialInput",
    "EquivalenceLevel",
    "DontCareMask",
    "NORMALIZERS",
    "Selector",
    "normalize_observation",
    "GoldenComparison",
    "GoldenMode",
    "GoldenStore",
    "GoldenStoreWriteError",
    "GoldenSuite",
    "R3Info",
    "capture_r3info",
    "MutationOutcome",
    "OracleAuditor",
    "StrengthReport",
    "run_mutation_probes",
    "ClassSurface",
    "FunctionSurface",
    "ModuleSurface",
    "attach_schema_surface",
    "extract_module_surface",
    "extract_surface",
    "AnchorResolver",
    "DriftFinding",
    "DriftKind",
    "Exemption",
    "TraceabilityEngine",
    "build_anchor",
]
