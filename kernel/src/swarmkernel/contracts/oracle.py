"""Oracle contracts — layer 2 of PDR-001, produced by the architect.

Two hard separations are encoded in the types themselves:

* :class:`OracleBundle` splits into a **public** half (what a builder may run
  locally) and a **holdout** half (scenarios + rubric, architect-held). They are
  distinct classes with distinct :class:`ArtifactClass` values so the bus can
  refuse to deliver the holdout to a generator. Information asymmetry stops
  being a rule people follow and becomes a routing failure (PDR-001 §7.1).
* :class:`OracleGrade` records how strong an oracle is, using the four-tier
  execution-level scale recommended by research 05 (Bronze/Silver/Gold/Diamond).
  ``DIAMOND`` requires that the oracle passed **mutation probing**: small
  mutations of the artefact under test must be *detected*. An oracle that cannot
  fail is a vacuous oracle and is rejected — this is the anti-vacuity rule that
  makes "任何门必须有硬门禁" real rather than decorative.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from .base import ArtifactClass, Contract


class OracleGrade(str, Enum):
    """Execution-level oracle strength. Never string-matching (research 05 ⑫)."""

    BRONZE = "bronze"
    """Parses / loads. Nothing more."""
    SILVER = "silver"
    """Runs clean on a known-good reference with no warnings."""
    GOLD = "gold"
    """Actually discriminates: passes good, and the suite is non-empty."""
    DIAMOND = "diamond"
    """Survives mutation probing: injected defects are detected. Anti-vacuity."""

    @property
    def rank(self) -> int:
        return ["bronze", "silver", "gold", "diamond"].index(self.value)


class ObservationChannel(str, Enum):
    """The closed set of observable channels. The differential engine compares
    exactly these and nothing else — "output serialization rules" must be fixed
    up front or differential testing is not reproducible (research 4.1)."""

    RETURN = "return"
    EXCEPTION = "exception"
    STDOUT = "stdout"
    STDERR = "stderr"
    EXIT_CODE = "exit_code"
    SIDE_EFFECT = "side_effect"
    """Ordered log of declared effects (writes, calls, emitted events)."""
    RESOURCE = "resource"
    """Wall time / memory / token buckets. Compared only against H8 budgets."""


class ScenarioKind(str, Enum):
    EXAMPLE = "example"
    PROPERTY = "property"
    METAMORPHIC = "metamorphic"
    ADVERSARIAL = "adversarial"
    REGRESSION = "regression"


class Scenario(Contract):
    """One end-to-end holdout case. Architect-owned, builder-invisible."""

    ARTIFACT_CLASS = ArtifactClass.ORACLE_HOLDOUT

    id: str
    kind: ScenarioKind = ScenarioKind.EXAMPLE
    clause_ids: list[str] = Field(
        default_factory=list, description="Clauses this scenario witnesses."
    )
    entrypoint: str = Field(description="Callable/CLI/HTTP route under test.")
    setup: dict[str, Any] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    expect: dict[str, Any] = Field(
        default_factory=dict,
        description="Expected observation per channel; channels absent here are "
        "not asserted by this scenario.",
    )
    observed_channels: list[ObservationChannel] = Field(
        default_factory=lambda: [ObservationChannel.RETURN, ObservationChannel.EXCEPTION]
    )
    timeout_s: float = 30.0
    weight: float = 1.0

    @model_validator(mode="after")
    def _must_assert_something(self) -> "Scenario":
        if not self.expect:
            raise ValueError(
                f"scenario {self.id} asserts nothing — a vacuous scenario is worse "
                "than no scenario because it inflates coverage"
            )
        if not self.clause_ids:
            raise ValueError(
                f"scenario {self.id} witnesses no clause; unbound scenarios cannot "
                "be counted towards witness coverage"
            )
        return self


class PropertySpec(Contract):
    """A property-based test declaration (H2). Builder-visible."""

    ARTIFACT_CLASS = ArtifactClass.ORACLE_PUBLIC

    id: str
    clause_ids: list[str] = Field(default_factory=list)
    entrypoint: str
    strategy: str = Field(
        description="Input strategy expression in the host PBT library "
        "(Hypothesis by default)."
    )
    predicate: str = Field(description="Property assertion source.")
    max_examples: int = 200
    shrink: bool = True
    """Shrinking is the cheap substitute for delta-debugging (research 4.4 ⑥)."""


class MetamorphicRelation(Contract):
    """Fallback oracle when no reference implementation exists (research 4.2 ⑤)."""

    ARTIFACT_CLASS = ArtifactClass.ORACLE_PUBLIC

    id: str
    clause_ids: list[str] = Field(default_factory=list)
    entrypoint: str
    transform: str = Field(description="Input transformation, e.g. 'permute_items'.")
    relation: str = Field(description="Expected output relation, e.g. 'equal', 'monotone'.")


class GoldenRecord(Contract):
    """Frozen observation for an R3 artefact. Forward-append only."""

    ARTIFACT_CLASS = ArtifactClass.ORACLE_HOLDOUT

    id: str
    unit_id: str
    entrypoint: str
    input_digest: str
    observation_digest: str
    frozen_at_version: str
    superseded_by: str | None = Field(
        default=None,
        description="Golden records are never edited. A change appends a new "
        "record and points the old one at it (research 03: multi-version "
        "coexistence beats forced migration).",
    )


class RubricCriterion(Contract):
    """One soft-gate criterion. Veto-only by construction."""

    ARTIFACT_CLASS = ArtifactClass.ORACLE_HOLDOUT

    id: str
    clause_ids: list[str] = Field(default_factory=list)
    question: str
    veto_when: str = Field(
        description="Condition under which the judge MUST veto. Phrased "
        "negatively on purpose: a rubric can only ever remove an instance."
    )
    evidence_required: bool = True
    """Judges must cite evidence; unsupported vetoes are discarded (§8)."""


class JudgeProtocol(Contract):
    """Fixed workflow for LLM-as-judge. Frozen for the duration of a session."""

    ARTIFACT_CLASS = ArtifactClass.ORACLE_HOLDOUT

    samples: int = Field(default=3, ge=1, description="Independent samples per item.")
    aggregation: str = Field(
        default="majority_veto",
        description="majority_veto | unanimous_veto | any_veto",
    )
    position_swap: bool = Field(
        default=True, description="Counter position/order bias by swapping presentations."
    )
    allow_abstain: bool = True
    require_citation: bool = True
    forbid_self_review: bool = True
    min_model_tier: int = Field(
        default=2,
        description="Judge tier must be >= builder tier (constitution §14). "
        "Enforced in swarmkernel.gates.algebra.",
    )
    calibration_set_id: str | None = None
    min_calibration_agreement: float = Field(default=0.8, ge=0.0, le=1.0)


class MutationProbe(Contract):
    """A deliberately broken variant used to test the oracle itself.

    This is the anti-vacuity instrument. Research 05 ⑩ ("对性质做小幅变异，验证
    器必须能检出违例，否则判契约恒真作废") and TLA-Prover's Diamond tier both
    require it. Without this, an oracle that always passes looks identical to an
    oracle that is correct.
    """

    ARTIFACT_CLASS = ArtifactClass.ORACLE_HOLDOUT

    id: str
    description: str
    target_clause_ids: list[str] = Field(default_factory=list)
    mutation: str = Field(
        description="How the artefact is broken, e.g. 'off_by_one:boundary', "
        "'drop_validation:input.email', 'swap_branches'."
    )
    must_be_caught_by: list[str] = Field(
        default_factory=list,
        description="Gate ids expected to fail. Empty means 'any hard gate'.",
    )


class PublicOracle(Contract):
    """The half a builder may hold locally. No end-to-end scenarios, no rubric."""

    ARTIFACT_CLASS = ArtifactClass.ORACLE_PUBLIC
    CONTRACT_VERSION = "1.0.0"

    bundle_id: str
    unit_id: str
    properties: list[PropertySpec] = Field(default_factory=list)
    metamorphic: list[MetamorphicRelation] = Field(default_factory=list)
    smoke_entrypoints: list[str] = Field(default_factory=list)
    interface_surface_digest: str | None = Field(
        default=None,
        description="Frozen interface horizon for the wave. Builders may read the "
        "surface — that is the point of a wave — but not the scenarios.",
    )


class HoldoutOracle(Contract):
    """The architect-held half. NEVER routed to a generator."""

    ARTIFACT_CLASS = ArtifactClass.ORACLE_HOLDOUT
    CONTRACT_VERSION = "1.0.0"

    bundle_id: str
    unit_id: str
    scenarios: list[Scenario] = Field(default_factory=list)
    golden: list[GoldenRecord] = Field(default_factory=list)
    rubric: list[RubricCriterion] = Field(default_factory=list)
    judge_protocol: JudgeProtocol = Field(default_factory=JudgeProtocol)
    mutation_probes: list[MutationProbe] = Field(default_factory=list)
    grade: OracleGrade = OracleGrade.BRONZE

    def clause_coverage(self) -> set[str]:
        covered: set[str] = set()
        for s in self.scenarios:
            covered.update(s.clause_ids)
        for r in self.rubric:
            covered.update(r.clause_ids)
        return covered


class OracleBundle(Contract):
    """Pairs the two halves. Only the architect and the verifier ever hold this."""

    ARTIFACT_CLASS = ArtifactClass.ORACLE_HOLDOUT
    CONTRACT_VERSION = "1.0.0"

    bundle_id: str
    unit_id: str
    spec_version: str
    public: PublicOracle
    holdout: HoldoutOracle

    @model_validator(mode="after")
    def _halves_agree(self) -> "OracleBundle":
        if self.public.bundle_id != self.bundle_id or self.holdout.bundle_id != self.bundle_id:
            raise ValueError("oracle halves must share the bundle id")
        if self.public.unit_id != self.unit_id or self.holdout.unit_id != self.unit_id:
            raise ValueError("oracle halves must share the unit id")
        return self
