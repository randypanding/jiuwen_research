"""Contract base types.

Every artefact that crosses a team boundary is a :class:`Contract`.  Three
properties are non-negotiable and are enforced here rather than by convention:

1. **Versioned.**  Every payload carries ``contract_version`` (SemVer).  A
   consumer declares the range it accepts; the bus refuses anything else.
   Research ``03_Spec版本化与增量演化.md`` reports that at worst **25 % of
   3075 public Web APIs actually follow SemVer** — compatibility can never be
   left to discipline, it must be machine-checked.
2. **Classified.**  Every payload carries an :class:`ArtifactClass`.  The
   information-asymmetry policy (PDR-001 §7) is expressed as
   ``role x ArtifactClass -> permission`` and is enforced by the bus.
3. **Content-addressed.**  Every payload can emit a stable ``digest`` used for
   drift detection (H7), golden freezing (R3) and evidence receipts.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>[0-9A-Za-z.-]+))?$"
)


class SemVer(BaseModel):
    """Minimal SemVer with the only three comparisons the gates need."""

    model_config = ConfigDict(frozen=True)

    major: int = 0
    minor: int = 1
    patch: int = 0
    pre: str | None = None

    @classmethod
    def parse(cls, text: str) -> "SemVer":
        m = SEMVER_RE.match(text.strip())
        if not m:
            raise ValueError(f"not a semver: {text!r}")
        return cls(
            major=int(m["major"]),
            minor=int(m["minor"]),
            patch=int(m["patch"]),
            pre=m["pre"],
        )

    def __str__(self) -> str:  # pragma: no cover - trivial
        base = f"{self.major}.{self.minor}.{self.patch}"
        return f"{base}-{self.pre}" if self.pre else base

    @property
    def tuple(self) -> tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    def compatible_with(self, other: "SemVer") -> bool:
        """Consumer-side compatibility: same major, consumer minor <= producer."""
        if self.major != other.major:
            return False
        return other.tuple[1:] >= self.tuple[1:] or other.minor > self.minor

    def bump(self, level: "ChangeSeverity") -> "SemVer":
        if level is ChangeSeverity.BREAKING:
            return SemVer(major=self.major + 1, minor=0, patch=0)
        if level is ChangeSeverity.ADDITIVE:
            return SemVer(major=self.major, minor=self.minor + 1, patch=0)
        return SemVer(major=self.major, minor=self.minor, patch=self.patch + 1)


class ChangeSeverity(str, Enum):
    """Structural change severity. Maps 1:1 onto the SemVer bump obligation.

    Adopted from YANG Semver's ``BC``/``NBC`` annotation and oasdiff's change
    classification (research ``03_Spec版本化与增量演化.md``): the version number
    must *carry* machine-readable compatibility information, and CI must reject
    ``api-version-not-bumped``.
    """

    NONE = "none"
    """No observable change."""
    PATCH = "patch"
    """Documentation / internal only. BC."""
    ADDITIVE = "additive"
    """New optional capability. BC. (YANG: BC)"""
    BREAKING = "breaking"
    """Removes or narrows a guarantee consumers may rely on. (YANG: NBC)"""

    @property
    def is_breaking(self) -> bool:
        return self is ChangeSeverity.BREAKING

    @property
    def rank(self) -> int:
        return {"none": 0, "patch": 1, "additive": 2, "breaking": 3}[self.value]

    @staticmethod
    def max_of(items: "list[ChangeSeverity]") -> "ChangeSeverity":
        return max(items, key=lambda s: s.rank, default=ChangeSeverity.NONE)


class ArtifactClass(str, Enum):
    """What kind of thing a payload is.

    This enum *is* the information-asymmetry axis (PDR-001 §7.1). Any new
    artefact type must be classified here or the bus will refuse to route it.
    """

    CONSTITUTION = "constitution"
    SPEC_L1 = "spec.l1"
    SPEC_L2 = "spec.l2"
    SPEC_L3 = "spec.l3"
    SPEC_DELTA = "spec.delta"
    RLEVEL_REGISTRY = "rlevel.registry"
    INTERFACE_SURFACE = "interface.surface"
    ORACLE_PUBLIC = "oracle.public"
    """Self-check subset a builder is *allowed* to run locally."""
    ORACLE_HOLDOUT = "oracle.holdout"
    """Scenario holdout + rubric. NEVER visible to a generator. PDR-001 §7.1."""
    INSTANCE = "instance"
    INSTANCE_REPORT = "instance.report"
    GATE_REPORT = "gate.report"
    JUDGE_VERDICT = "judge.verdict"
    DIFFERENTIAL_REPORT = "differential.report"
    EVIDENCE_RECEIPT = "evidence.receipt"
    TEAM_MEMORY = "team.memory"
    HEALTH_METRICS = "health.metrics"
    RULE_PROPOSAL = "rule.proposal"
    WAVE_MANIFEST = "wave.manifest"


class Role(str, Enum):
    """The role set fixed by PDR-001 §10. Closed set: no ad-hoc roles."""

    HUMAN = "human"
    LEADER = "leader"
    ARCHITECT = "architect"
    BUILDER = "builder"
    VERIFIER = "verifier"
    SPEC_MODERATOR = "spec_moderator"
    SPEC_STEWARD = "spec_steward"
    RECONCILER = "reconciler"
    CARTOGRAPHER = "cartographer"
    CRITIC = "critic"
    REFACTOR = "refactor"
    MODERATOR = "moderator"
    DEEP_AGENT = "deep_agent"
    JUDGE = "judge"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def canonical_json(value: Any) -> str:
    """Deterministic JSON used for every digest in the system.

    Determinism matters: digests feed H7 drift detection and R3 golden freezing.
    ``sort_keys`` + fixed separators + ``ensure_ascii=False`` is the single
    serialization rule for the whole platform.
    """

    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    )


def digest_of(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class Contract(BaseModel):
    """Base class for every cross-team artefact."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    ARTIFACT_CLASS: ClassVar[ArtifactClass]
    CONTRACT_VERSION: ClassVar[str] = "1.0.0"

    contract_version: str = Field(default="1.0.0")

    @field_validator("contract_version")
    @classmethod
    def _check_semver(cls, v: str) -> str:
        SemVer.parse(v)
        return v

    def model_post_init(self, __context: Any) -> None:  # noqa: D105
        # Subclasses declare their own CONTRACT_VERSION; honour it unless the
        # caller explicitly supplied a different one.
        if "contract_version" not in self.model_fields_set:
            object.__setattr__(self, "contract_version", type(self).CONTRACT_VERSION)

    @property
    def artifact_class(self) -> ArtifactClass:
        return type(self).ARTIFACT_CLASS

    def digest(self) -> str:
        """Content digest, excluding volatile fields."""

        payload = self.model_dump(mode="json", exclude=self._volatile_fields())
        return digest_of(payload)

    def _volatile_fields(self) -> set[str]:
        return {"created_at", "produced_at", "observed_at"}

    @classmethod
    def json_schema(cls) -> dict[str, Any]:
        schema = cls.model_json_schema()
        schema["$id"] = f"https://openjiuwen.dev/swarm/contracts/{cls.__name__}.json"
        schema["x-artifact-class"] = cls.ARTIFACT_CLASS.value
        schema["x-contract-version"] = cls.CONTRACT_VERSION
        return schema
