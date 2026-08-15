"""Spec contracts — the single source of truth (PDR-001 §4, layer 1).

Design decisions taken here (and *closed* for implementation teams):

* **Clause is the atomic unit of truth**, not the document. Clauses have stable
  IDs that are never reused, a content ``revision`` digest, and a mandatory
  witness binding. This makes §8's rule — *"every L1/L2 clause must bind >=1
  mechanical witness or >=1 holdout scenario, otherwise it is ``unverifiable``
  and may only veto, never admit"* — mechanically checkable.
* **Contract semantics = Design-by-Contract + assume/guarantee.** ``requires`` /
  ``ensures`` / ``invariant`` (Meyer 1992) plus ``assumes`` / ``guarantees``
  (Pacti / interface automata) so that environment freedom is *delegated* rather
  than specified. Research 01/05 marks both as A-grade foundations.
* **Don't-care is a first-class construct with three categories and two tracks.**
  Categories map onto Damiani & De Micheli's SDC/ODC taxonomy; the two tracks
  (``undefined`` = stuck/forbidden vs ``unspecified`` = any choice is legal) come
  from CH2O/Krebbers. Research 02/05 is explicit that conflating them poisons the
  semantics, so they are separate enum members and separate gate behaviour.
* **Only safety and liveness may be asserted.** Alpern-Schneider says every
  temporal property decomposes into safety ∩ liveness; anything not asserted is
  don't-care *by construction*. This is the spec-bloat upper bound from §6.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from .base import (
    ArtifactClass,
    ChangeSeverity,
    Contract,
    SemVer,
    digest_of,
    utcnow,
)


class SpecLayer(str, Enum):
    L1 = "L1"
    """Business intent. Human-owned, human-approved."""
    L2 = "L2"
    """Development contract. Human reads the diff and may veto."""
    L3 = "L3"
    """Implementation notes. Machine-owned; humans neither read nor approve."""


class PropertyKind(str, Enum):
    """Alpern-Schneider decomposition. The *only* two assertable kinds."""

    SAFETY = "safety"
    LIVENESS = "liveness"


class FreedomTrack(str, Enum):
    """The two tracks of "not specified"; conflating them is a defect."""

    UNSPECIFIED = "unspecified"
    """Any of the allowed choices is legal. Differential divergence here is OK."""
    UNDEFINED = "undefined"
    """Out of contract. Behaviour is stuck/forbidden; reaching it is a defect."""


class DontCareCategory(str, Enum):
    """SDC/ODC taxonomy (Damiani & De Micheli), lifted to program behaviour."""

    OUTPUT_FREEDOM = "output_freedom"
    """Several outputs are equally correct (e.g. any valid topological order)."""
    UNREACHABLE_STATE = "unreachable_state"
    """Satisfiability don't-care: the input cannot occur under ``requires``."""
    IGNORABLE_OUTPUT = "ignorable_output"
    """Observability don't-care: nobody downstream observes this channel."""


class ClauseStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    REMOVED = "removed"


class WitnessKind(str, Enum):
    """How a clause is mechanically witnessed. Ordered weakest -> strongest."""

    NONE = "none"
    ADVISORY = "advisory"
    """Judge rubric only — cannot admit, may veto."""
    STATIC = "static"
    """H1: type / lint / structural check."""
    UNIT = "unit"
    """H2: unit test."""
    PROPERTY = "property"
    """H2: property-based test (Hypothesis/QuickCheck family)."""
    HOLDOUT = "holdout"
    """H3: end-to-end scenario held by the architect."""
    SURFACE = "surface"
    """H4: contract-surface extraction + breaking change detection."""
    DIFFERENTIAL = "differential"
    """H5: cross-instance behavioural differential."""
    GOLDEN = "golden"
    """H5: frozen golden output (R3)."""
    INVARIANT = "invariant"
    """H6: runtime guardrail / constitutional invariant."""
    BUDGET = "budget"
    """H8: cost / latency / resource budget."""

    @property
    def is_mechanical(self) -> bool:
        return self not in (WitnessKind.NONE, WitnessKind.ADVISORY)


class WitnessBinding(Contract):
    """Binds a clause to the concrete mechanical evidence that guards it."""

    ARTIFACT_CLASS = ArtifactClass.SPEC_L2

    kind: WitnessKind
    gate_id: str = Field(description="H1..H8, or 'S' for the soft gate.")
    selector: str = Field(
        description="Stable pointer to the concrete check: test node id, "
        "scenario id, surface symbol, golden record id, budget key."
    )
    note: str | None = None


class DontCareRegion(Contract):
    """An explicitly licensed freedom. Differential divergence inside a
    registered region is *not* a defect (PDR-001 §6)."""

    ARTIFACT_CLASS = ArtifactClass.SPEC_L2

    id: str
    category: DontCareCategory
    track: FreedomTrack = FreedomTrack.UNSPECIFIED
    description: str
    selectors: list[str] = Field(
        default_factory=list,
        description="Observation selectors this freedom covers, in the "
        "swarmkernel.oracle.dontcare selector language (e.g. "
        "'return.items[*].order', 'stdout', 'sideeffect:cache.*').",
    )
    normalizer: str | None = Field(
        default=None,
        description="Named normalizer applied before comparison, e.g. "
        "'sort_list', 'round:6', 'mask_uuid', 'mask_timestamp'.",
    )
    justification_clause_ids: list[str] = Field(
        default_factory=list,
        description="Which clause(s) license this freedom. Empty means the "
        "freedom was registered by the spec moderator from a measurement.",
    )

    @model_validator(mode="after")
    def _undefined_has_no_normalizer(self) -> "DontCareRegion":
        if self.track is FreedomTrack.UNDEFINED and self.normalizer:
            raise ValueError(
                "an 'undefined' region is stuck/forbidden territory; it must not "
                "carry a normalizer (that would silently legalise reaching it)"
            )
        return self


class Clause(Contract):
    """One atomic, individually addressable statement of truth."""

    ARTIFACT_CLASS = ArtifactClass.SPEC_L2

    id: str = Field(
        pattern=r"^L[123]-[A-Z0-9]+(?:\.[A-Z0-9]+)*-\d{3,}$",
        description="Stable, never reused. e.g. 'L2-ORDER.PRICING-014'.",
    )
    layer: SpecLayer
    title: str
    text: str = Field(description="Normative natural language. Human-authored for L1/L2.")
    kind: PropertyKind = PropertyKind.SAFETY

    requires: list[str] = Field(default_factory=list, description="Preconditions.")
    ensures: list[str] = Field(default_factory=list, description="Postconditions.")
    invariant: list[str] = Field(default_factory=list)
    assumes: list[str] = Field(
        default_factory=list, description="Environment assumptions (A of A/G)."
    )
    guarantees: list[str] = Field(
        default_factory=list, description="Guarantees given the assumptions (G of A/G)."
    )

    witnesses: list[WitnessBinding] = Field(default_factory=list)
    dont_care_ids: list[str] = Field(default_factory=list)
    anchors: list["Anchor"] = Field(
        default_factory=list,
        description="Artefacts this clause governs. The spec declares anchors; "
        "code carries back-references. Mismatch is drift (H7).",
    )
    derives_from: list[str] = Field(
        default_factory=list, description="Parent clause ids (L2 -> L1 traceability)."
    )
    status: ClauseStatus = ClauseStatus.ACTIVE
    deprecated_in: str | None = None
    removable_from: str | None = Field(
        default=None,
        description="Earliest version at which removal is legal. Enforced to be "
        ">= one minor after `deprecated_in` (research 03/rec_03).",
    )

    @property
    def revision(self) -> str:
        """Content digest of the normative part only."""

        return digest_of(
            {
                "id": self.id,
                "text": self.text,
                "kind": self.kind.value,
                "requires": self.requires,
                "ensures": self.ensures,
                "invariant": self.invariant,
                "assumes": self.assumes,
                "guarantees": self.guarantees,
            }
        )

    @property
    def is_verifiable(self) -> bool:
        """§8: a clause may only *admit* if it has a mechanical witness."""

        return any(w.kind.is_mechanical for w in self.witnesses)

    @property
    def is_advisory_only(self) -> bool:
        return not self.is_verifiable

    @model_validator(mode="after")
    def _layer_matches_id(self) -> "Clause":
        if not self.id.startswith(self.layer.value + "-"):
            raise ValueError(f"clause id {self.id!r} does not match layer {self.layer}")
        if self.status is ClauseStatus.DEPRECATED and not self.deprecated_in:
            raise ValueError("deprecated clause must record `deprecated_in`")
        if self.deprecated_in and self.removable_from:
            dep, rem = SemVer.parse(self.deprecated_in), SemVer.parse(self.removable_from)
            if (rem.major, rem.minor) <= (dep.major, dep.minor):
                raise ValueError(
                    "deprecation needs at least one minor of buffer before removal"
                )
        return self


class Anchor(Contract):
    """A pointer from spec to a governed artefact. The basis of H7."""

    ARTIFACT_CLASS = ArtifactClass.SPEC_L2

    path: str = Field(description="Repo-relative path.")
    symbol: str | None = Field(default=None, description="Qualified symbol name.")
    kind: str = Field(default="module", description="module|function|class|schema|file")

    def key(self) -> str:
        return f"{self.path}::{self.symbol or '*'}"


Clause.model_rebuild()


class RLevel(str, Enum):
    """Regenerability grade (PDR-001 §5). Declared by spec, never inferred."""

    R0 = "R0"
    """Disposable instance. fan-out / discard / rewrite freely."""
    R1 = "R1"
    """Anchored artefact, internal consumers. Regenerable via spec-delta + H4."""
    R2 = "R2"
    """Contract artefact, external consumers. Evolve only; breaking needs a version."""
    R3 = "R3"
    """Frozen. State-bearing or line-by-line semantics. Forward-append only."""

    @property
    def allows_fanout(self) -> bool:
        return self in (RLevel.R0, RLevel.R1)

    @property
    def allows_discard(self) -> bool:
        return self is RLevel.R0

    @property
    def requires_golden(self) -> bool:
        return self is RLevel.R3

    @property
    def requires_human_approval(self) -> bool:
        return self in (RLevel.R2, RLevel.R3)


class RegenerationUnit(Contract):
    """The unit of change (PDR-001 axis C). Carries the R level."""

    ARTIFACT_CLASS = ArtifactClass.RLEVEL_REGISTRY

    id: str
    title: str
    r_level: RLevel
    paths: list[str] = Field(default_factory=list)
    surface_paths: list[str] = Field(
        default_factory=list,
        description="Subset of `paths` that forms the externally visible "
        "contract surface for H4.",
    )
    clause_ids: list[str] = Field(default_factory=list)
    external_consumers: list[str] = Field(default_factory=list)
    interface_version: str = "0.1.0"
    frozen_golden_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _consistency(self) -> "RegenerationUnit":
        if self.r_level is RLevel.R2 and not self.external_consumers:
            raise ValueError("R2 means 'has external consumers' — list at least one")
        if self.r_level is RLevel.R3 and not self.frozen_golden_ids:
            raise ValueError("R3 requires frozen golden output ids (PDR-001 §5 G3)")
        if self.r_level is RLevel.R0 and self.external_consumers:
            raise ValueError("R0 must have no consumers; promote it to R1/R2")
        return self


class RLevelRegistry(Contract):
    """The authoritative R-level table. Owned by spec, read by every gate."""

    ARTIFACT_CLASS = ArtifactClass.RLEVEL_REGISTRY
    CONTRACT_VERSION = "1.0.0"

    units: list[RegenerationUnit] = Field(default_factory=list)

    def by_id(self, unit_id: str) -> RegenerationUnit | None:
        return next((u for u in self.units if u.id == unit_id), None)

    def level_for_path(self, path: str) -> RLevel | None:
        """Most restrictive level among units that claim this path."""

        hits = [u.r_level for u in self.units if any(path.startswith(p) for p in u.paths)]
        if not hits:
            return None
        return max(hits, key=lambda r: ["R0", "R1", "R2", "R3"].index(r.value))


class SpecDocument(Contract):
    """A versioned bundle of clauses + registered freedoms."""

    ARTIFACT_CLASS = ArtifactClass.SPEC_L2
    CONTRACT_VERSION = "1.0.0"

    spec_id: str
    version: str = "0.1.0"
    domain: str
    clauses: list[Clause] = Field(default_factory=list)
    dont_care: list[DontCareRegion] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)

    def clause(self, clause_id: str) -> Clause | None:
        return next((c for c in self.clauses if c.id == clause_id), None)

    def active_clauses(self) -> list[Clause]:
        return [c for c in self.clauses if c.status is not ClauseStatus.REMOVED]

    def unverifiable_clauses(self) -> list[Clause]:
        """§8: these may only participate as advisory input to the soft gate."""

        return [
            c
            for c in self.active_clauses()
            if c.layer in (SpecLayer.L1, SpecLayer.L2) and not c.is_verifiable
        ]

    def witness_coverage(self) -> float:
        governed = [
            c for c in self.active_clauses() if c.layer in (SpecLayer.L1, SpecLayer.L2)
        ]
        if not governed:
            return 1.0
        return sum(1 for c in governed if c.is_verifiable) / len(governed)

    def dont_care_region(self, region_id: str) -> DontCareRegion | None:
        return next((r for r in self.dont_care if r.id == region_id), None)

    @model_validator(mode="after")
    def _unique_ids_and_resolvable_refs(self) -> "SpecDocument":
        ids = [c.id for c in self.clauses]
        if len(ids) != len(set(ids)):
            dupes = {i for i in ids if ids.count(i) > 1}
            raise ValueError(f"duplicate clause ids: {sorted(dupes)}")
        region_ids = {r.id for r in self.dont_care}
        for c in self.clauses:
            missing = set(c.dont_care_ids) - region_ids
            if missing:
                raise ValueError(f"{c.id} references unknown don't-care {sorted(missing)}")
        return self


class DeltaOp(str, Enum):
    ADD_CLAUSE = "add_clause"
    AMEND_CLAUSE = "amend_clause"
    DEPRECATE_CLAUSE = "deprecate_clause"
    REMOVE_CLAUSE = "remove_clause"
    ADD_DONT_CARE = "add_dont_care"
    REMOVE_DONT_CARE = "remove_dont_care"
    RETARGET_ANCHOR = "retarget_anchor"


class SpecDeltaItem(Contract):
    ARTIFACT_CLASS = ArtifactClass.SPEC_DELTA

    op: DeltaOp
    clause_id: str | None = None
    region_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    severity: ChangeSeverity = ChangeSeverity.PATCH
    rationale: str = ""


class SpecDelta(Contract):
    """The unit of spec change and the trigger of a wave (PDR-001 §9)."""

    ARTIFACT_CLASS = ArtifactClass.SPEC_DELTA
    CONTRACT_VERSION = "1.0.0"

    delta_id: str
    spec_id: str
    from_version: str
    to_version: str
    items: list[SpecDeltaItem] = Field(default_factory=list)
    origin: str = Field(
        default="human",
        description="human | spec_moderator | critic | reconciler | deep_agent",
    )
    measurement_ref: str | None = Field(
        default=None,
        description="Differential report id when this delta was produced by a "
        "measurement (silence/divergence), per PDR-001 §6.",
    )
    human_approved: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    @property
    def severity(self) -> ChangeSeverity:
        return ChangeSeverity.max_of([i.severity for i in self.items])

    @model_validator(mode="after")
    def _version_bump_matches_severity(self) -> "SpecDelta":
        """Machine enforcement of "the version number must carry the severity".

        oasdiff v1.27.0 added exactly this check (``api-version-not-bumped``)
        because 75 % of real APIs get it wrong. We refuse to construct an
        inconsistent delta at all.
        """

        old, new = SemVer.parse(self.from_version), SemVer.parse(self.to_version)
        expected = old.bump(self.severity)
        if self.severity is ChangeSeverity.NONE:
            return self
        if self.severity is ChangeSeverity.BREAKING and new.major <= old.major:
            raise ValueError(
                f"breaking spec-delta must bump major: {old} -> {new} "
                f"(expected >= {expected})"
            )
        if self.severity is ChangeSeverity.ADDITIVE and new.tuple <= old.tuple:
            raise ValueError(f"additive spec-delta must bump minor: {old} -> {new}")
        if self.severity is ChangeSeverity.PATCH and new.tuple <= old.tuple:
            raise ValueError(f"patch spec-delta must bump patch: {old} -> {new}")
        return self
