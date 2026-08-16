"""R3 golden-output management.

Three rules, each of which exists because violating it has burned a real
project (research 04 / rec_04):

1. **CI never writes goldens.** :class:`GoldenStore` opened in ``compare`` mode
   physically cannot mutate. Regeneration is a separate, human-authorised mode.
2. **Baseline and snapshot are physically separated.** Expected values come from
   the frozen store; produced values come from the run. There is no code path
   where a run result becomes the baseline it is compared against.
3. **Goldens are regression guards, not correctness proofs.** Every R3 unit must
   *also* bind an independent correctness oracle (metamorphic relation,
   reference implementation, or round-trip). :meth:`GoldenSuite.validate`
   refuses a suite that has only goldens.
"""

from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping

from ..contracts.base import canonical_json, digest_of
from ..contracts.oracle import GoldenRecord, MetamorphicRelation

__all__ = [
    "GoldenMode",
    "R3Info",
    "GoldenStore",
    "GoldenSuite",
    "GoldenComparison",
    "capture_r3info",
]


class GoldenMode(str, Enum):
    COMPARE = "compare"
    """Read-only. The only mode CI may use."""

    REGENERATE = "regenerate"
    """Writes. Requires an explicit human authorisation token."""


@dataclass(frozen=True)
class R3Info:
    """Reproducibility manifest, modelled on Debian ``.buildinfo``.

    A golden that was produced in an unrecorded environment cannot be
    invalidated when that environment changes, so it silently rots. Recording
    the environment lets the gate distinguish "the code changed" from "the
    world changed" — which is the difference between a real regression and a
    false alarm.
    """

    python_version: str
    platform_machine: str
    platform_system: str
    timezone: str
    locale: str
    source_date_epoch: str | None
    dependency_digest: str
    extra: Mapping[str, str] = field(default_factory=dict)

    def digest(self) -> str:
        return digest_of(
            {
                "python_version": self.python_version,
                "platform_machine": self.platform_machine,
                "platform_system": self.platform_system,
                "timezone": self.timezone,
                "locale": self.locale,
                "source_date_epoch": self.source_date_epoch,
                "dependency_digest": self.dependency_digest,
                "extra": dict(self.extra),
            }
        )

    def diff(self, other: "R3Info") -> list[str]:
        out = []
        for fieldname in (
            "python_version",
            "platform_machine",
            "platform_system",
            "timezone",
            "locale",
            "source_date_epoch",
            "dependency_digest",
        ):
            a, b = getattr(self, fieldname), getattr(other, fieldname)
            if a != b:
                out.append(f"{fieldname}: {a!r} -> {b!r}")
        return out


def capture_r3info(dependency_digest: str = "", **extra: str) -> R3Info:
    return R3Info(
        python_version=".".join(map(str, sys.version_info[:3])),
        platform_machine=platform.machine(),
        platform_system=platform.system(),
        timezone=os.environ.get("TZ", ""),
        locale=os.environ.get("LC_ALL", os.environ.get("LANG", "")),
        source_date_epoch=os.environ.get("SOURCE_DATE_EPOCH"),
        dependency_digest=dependency_digest,
        extra=dict(extra),
    )


@dataclass(frozen=True)
class GoldenComparison:
    golden_id: str
    matched: bool
    expected_digest: str
    actual_digest: str
    environment_drift: tuple[str, ...] = ()
    message: str = ""

    @property
    def is_environment_suspect(self) -> bool:
        """A mismatch with recorded environment drift is not automatically a
        regression — but it is never automatically *not* one either. It is
        reported so a human decides, and it never auto-passes."""

        return bool(self.environment_drift) and not self.matched


class GoldenStoreWriteError(RuntimeError):
    pass


class GoldenStore:
    """In-memory store with a mode lock. Persistence is an adapter concern."""

    def __init__(
        self,
        records: Iterable[GoldenRecord] = (),
        mode: GoldenMode = GoldenMode.COMPARE,
        authorisation: str | None = None,
        environments: Mapping[str, R3Info] | None = None,
    ) -> None:
        if mode is GoldenMode.REGENERATE and not authorisation:
            raise GoldenStoreWriteError(
                "regenerate mode requires an explicit human authorisation token"
            )
        self._mode = mode
        self._auth = authorisation
        self._records: dict[str, GoldenRecord] = {}
        self._environments: dict[str, R3Info] = dict(environments or {})
        self._supersede_reasons: dict[str, str] = {}
        for r in records:
            self._records[r.id] = r

    @property
    def mode(self) -> GoldenMode:
        return self._mode

    def get(self, golden_id: str) -> GoldenRecord | None:
        record = self._records.get(golden_id)
        if record is not None and record.superseded_by:
            return self._records.get(record.superseded_by, record)
        return record

    def put(self, record: GoldenRecord) -> None:
        if self._mode is not GoldenMode.REGENERATE:
            raise GoldenStoreWriteError(
                "golden store is in compare mode; CI may never write goldens"
            )
        existing = self._records.get(record.id)
        if existing is not None and not existing.superseded_by:
            raise GoldenStoreWriteError(
                f"golden {record.id!r} already exists and was not superseded; "
                "goldens are append-only"
            )
        self._records[record.id] = record

    def supersede(self, golden_id: str, new_record: GoldenRecord, reason: str) -> None:
        if self._mode is not GoldenMode.REGENERATE:
            raise GoldenStoreWriteError("cannot supersede in compare mode")
        old = self._records[golden_id]
        self._records[golden_id] = old.model_copy(
            update={"superseded_by": new_record.id}
        )
        self._records[new_record.id] = new_record
        self._supersede_reasons[golden_id] = reason

    def compare(
        self, golden_id: str, actual: Any, actual_env: R3Info | None = None
    ) -> GoldenComparison:
        record = self.get(golden_id)
        if record is None:
            # Missing golden is a failure, never a pass. Otherwise deleting a
            # golden becomes the cheapest way to make the gate green.
            return GoldenComparison(
                golden_id=golden_id,
                matched=False,
                expected_digest="",
                actual_digest=digest_of(actual),
                message="no golden record found; a missing baseline is a failure",
            )
        actual_digest = digest_of(actual)
        matched = actual_digest == record.observation_digest
        drift: tuple[str, ...] = ()
        recorded_env = self._environments.get(record.id)
        if actual_env is not None and recorded_env is not None:
            drift = tuple(recorded_env.diff(actual_env))
        return GoldenComparison(
            golden_id=golden_id,
            matched=matched,
            expected_digest=record.observation_digest,
            actual_digest=actual_digest,
            environment_drift=drift,
            message="" if matched else "golden mismatch",
        )


@dataclass
class GoldenSuite:
    """A unit's R3 evidence: goldens plus at least one independent oracle."""

    unit_id: str
    goldens: list[GoldenRecord] = field(default_factory=list)
    independent_relations: list[MetamorphicRelation] = field(default_factory=list)
    reference_impl_ref: str | None = None
    round_trip_property: str | None = None

    def has_independent_oracle(self) -> bool:
        return bool(
            self.independent_relations
            or self.reference_impl_ref
            or self.round_trip_property
        )

    def validate(self) -> list[str]:
        problems: list[str] = []
        if not self.goldens:
            problems.append(f"{self.unit_id}: R3 unit has no frozen goldens")
        if not self.has_independent_oracle():
            problems.append(
                f"{self.unit_id}: goldens are regression guards, not correctness "
                "proofs; bind a metamorphic relation, a reference implementation, "
                "or a round-trip property"
            )
        seen: set[str] = set()
        for g in self.goldens:
            if g.id in seen:
                problems.append(f"{self.unit_id}: duplicate golden id {g.id!r}")
            seen.add(g.id)
        return problems


def dependency_digest_of(requirements: Mapping[str, str]) -> str:
    return digest_of(canonical_json(dict(sorted(requirements.items()))))
