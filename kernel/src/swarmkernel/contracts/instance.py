"""Instance & differential contracts — layer 3 of PDR-001.

An instance is a *sample* of the spec, not an asset. What survives an instance
is its measurement, which is why :class:`InstanceReport` and
:class:`DifferentialReport` are contracts while the code itself is only
referenced by digest.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from .base import ArtifactClass, Contract, digest_of
from .oracle import ObservationChannel


class Observation(Contract):
    """One normalised observation of one execution. The comparison unit of H5."""

    ARTIFACT_CLASS = ArtifactClass.INSTANCE_REPORT

    channel: ObservationChannel
    value: Any = None
    truncated: bool = False

    def digest(self) -> str:
        return digest_of({"channel": self.channel.value, "value": self.value})


class ProbeResult(Contract):
    """The result of running one probe input against one instance."""

    ARTIFACT_CLASS = ArtifactClass.INSTANCE_REPORT

    probe_id: str
    entrypoint: str
    observations: list[Observation] = Field(default_factory=list)
    duration_ms: float = 0.0
    crashed: bool = False
    timed_out: bool = False

    def observation(self, channel: ObservationChannel) -> Observation | None:
        return next((o for o in self.observations if o.channel is channel), None)

    def fingerprint(self, channels: list[ObservationChannel] | None = None) -> str:
        """Behavioural fingerprint used for clustering.

        Research 4.5 (LDB) recommends clustering instances by behavioural
        fingerprint *before* pairwise differencing, turning an O(N^2) comparison
        into O(K^2) over cluster representatives. That is the single biggest
        cost lever in the differential engine.
        """

        wanted = channels or [o.channel for o in self.observations]
        items = sorted(
            (o.channel.value, o.digest())
            for o in self.observations
            if o.channel in wanted
        )
        return digest_of({"probe": self.probe_id, "obs": items})


class InstanceManifest(Contract):
    """Identity of one sampled instance. Deliberately thin."""

    ARTIFACT_CLASS = ArtifactClass.INSTANCE

    instance_id: str
    unit_id: str
    spec_version: str
    delta_id: str
    builder_id: str
    model_tier: int = Field(default=1, ge=0)
    seed: int | None = None
    tree_digest: str = Field(description="Digest of the produced source tree.")
    surface_digest: str | None = None


class InstanceReport(Contract):
    """What a builder hands to the verifier. Contains no oracle knowledge."""

    ARTIFACT_CLASS = ArtifactClass.INSTANCE_REPORT
    CONTRACT_VERSION = "1.0.0"

    manifest: InstanceManifest
    self_check_passed: bool = False
    probe_results: list[ProbeResult] = Field(default_factory=list)
    token_cost: int = 0
    wall_time_s: float = 0.0
    notes: str = ""

    @model_validator(mode="after")
    def _no_holdout_leakage(self) -> "InstanceReport":
        """Structural tripwire: builders must not echo holdout identifiers.

        Best-effort by design: it scans ``notes`` only — probe payloads and
        manifests can still carry echoes. The primary defence is structural
        and lives elsewhere: the bus routing policy never delivers
        ORACLE_HOLDOUT artefacts to a builder in the first place
        (bus/policy.py §7.1). This validator is the cheap second line.
        """

        forbidden = ("holdout", "rubric", "scenario:")
        blob = (self.notes or "").lower()
        hit = next((f for f in forbidden if f in blob), None)
        if hit:
            raise ValueError(
                f"instance report mentions {hit!r}; a builder that knows about the "
                "holdout invalidates the measurement (PDR-001 §7.1)"
            )
        return self


class DivergenceVerdict(str, Enum):
    """The measurement taxonomy of PDR-001 §6 — this table *is* the paradigm."""

    CLOSED = "closed"
    """All pass, no divergence. Spec is closed w.r.t. this oracle."""
    SILENCE = "silence"
    """All pass, but instances differ. The spec did not say. -> don't-care or new clause."""
    AMBIGUITY = "ambiguity"
    """Some pass, some fail. The spec was unclear. -> spec moderator converges."""
    UNSOLVED_AT_TIER = "unsolved_at_tier"
    """All fail at this model tier. -> clarify + record tier requirement."""
    INFEASIBLE = "infeasible"
    """All fail even after tier escalation. -> spec/oracle conflict, escalate."""
    INSUFFICIENT = "insufficient"
    """Fewer than min_instances_for_verdict instances, pass or fail (D9): the
    sample is too small for any differential conclusion. Sample more before
    judging."""


class Divergence(Contract):
    """One concrete behavioural difference between two instances."""

    ARTIFACT_CLASS = ArtifactClass.DIFFERENTIAL_REPORT

    probe_id: str
    channel: ObservationChannel
    left_instance: str
    right_instance: str
    left_value: Any = None
    right_value: Any = None
    covered_by_dont_care: str | None = Field(
        default=None, description="Don't-care region id, when the freedom is licensed."
    )
    minimised_input: Any = Field(
        default=None,
        description="Shrunk counterexample (PBT shrink / delta debugging).",
    )

    @property
    def is_defect(self) -> bool:
        return self.covered_by_dont_care is None


class EquivalenceClass(Contract):
    """Instances that share a behavioural fingerprint."""

    ARTIFACT_CLASS = ArtifactClass.DIFFERENTIAL_REPORT

    fingerprint: str
    instance_ids: list[str] = Field(default_factory=list)
    representative: str


class DifferentialReport(Contract):
    """The instrument reading of PDR-001 §6. Survives the instances it measured."""

    ARTIFACT_CLASS = ArtifactClass.DIFFERENTIAL_REPORT
    CONTRACT_VERSION = "1.0.0"

    report_id: str
    unit_id: str
    delta_id: str
    spec_version: str
    instance_ids: list[str] = Field(default_factory=list)
    passing_instance_ids: list[str] = Field(default_factory=list)
    classes: list[EquivalenceClass] = Field(default_factory=list)
    divergences: list[Divergence] = Field(default_factory=list)
    verdict: DivergenceVerdict = DivergenceVerdict.CLOSED
    probes_executed: int = 0
    delta_diversity: float = Field(
        default=0.0,
        description="NEZHA-style delta-diversity of the probe set: fraction of "
        "distinct observation tuples per probe. Used to schedule probe budget "
        "towards difference-revealing inputs rather than raw coverage.",
    )
    dont_care_touched: list[str] = Field(
        default_factory=list,
        description="Every don't-care region this verdict relied upon — "
        "including regions that matched but happened to leave the value "
        "unchanged (D8: reporting only value-changing regions understates "
        "which freedoms a CLOSED verdict depends on).",
    )
    tier_escalated: bool = False

    @property
    def undecided_divergences(self) -> list[Divergence]:
        return [d for d in self.divergences if d.is_defect]

    @property
    def closure(self) -> float:
        """Spec closure: share of instances in the single largest class."""

        if not self.instance_ids:
            return 0.0
        if not self.classes:
            return 0.0
        return max(len(c.instance_ids) for c in self.classes) / len(self.instance_ids)

    @model_validator(mode="after")
    def _passing_is_subset(self) -> "DifferentialReport":
        extra = set(self.passing_instance_ids) - set(self.instance_ids)
        if extra:
            raise ValueError(f"passing instances not in instance set: {sorted(extra)}")
        return self
