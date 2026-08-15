"""Differential engine — the instrument of PDR-001 §6.

Pipeline (each stage is cheaper than the next, per research 4.5 / 4.7)::

    normalise (don't-care)  ->  fingerprint  ->  cluster  ->  pairwise diff
                                                       (representatives only)

Clustering first is what makes this affordable: N instances need
``K*(K-1)/2`` comparisons over K cluster representatives instead of
``N*(N-1)/2`` over instances, and K is usually 1-3.

The verdict table implements §6 literally, including the ``INSUFFICIENT`` rule
("fewer than 3 instances and a failure occurred -> sample more before judging").
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from ..contracts.instance import (
    Divergence,
    DifferentialReport,
    DivergenceVerdict,
    EquivalenceClass,
    InstanceReport,
    ProbeResult,
)
from ..contracts.oracle import ObservationChannel
from ..contracts.spec import DontCareRegion
from .dontcare import DontCareMask

__all__ = ["DifferentialEngine", "DifferentialInput", "EquivalenceLevel"]


class EquivalenceLevel:
    """Three-level equivalence ladder (research 4.1). Cost grows, precision grows.

    ``IO`` and ``BEHAVIOURAL`` are implemented here (deterministic, offline).
    ``SEMANTIC`` (product programs / SMT) is a declared escalation hook: the
    engine marks candidates for it but never claims to have proved equivalence.
    Differential testing can only ever prove *in*equivalence.
    """

    IO = "io"
    BEHAVIOURAL = "behavioural"
    SEMANTIC = "semantic"

    #: Channels compared at each level.
    CHANNELS: dict[str, tuple[ObservationChannel, ...]] = {
        IO: (ObservationChannel.RETURN, ObservationChannel.EXCEPTION),
        BEHAVIOURAL: (
            ObservationChannel.RETURN,
            ObservationChannel.EXCEPTION,
            ObservationChannel.STDOUT,
            ObservationChannel.STDERR,
            ObservationChannel.EXIT_CODE,
            ObservationChannel.SIDE_EFFECT,
        ),
        SEMANTIC: (
            ObservationChannel.RETURN,
            ObservationChannel.EXCEPTION,
            ObservationChannel.STDOUT,
            ObservationChannel.STDERR,
            ObservationChannel.EXIT_CODE,
            ObservationChannel.SIDE_EFFECT,
        ),
    }


@dataclass
class DifferentialInput:
    """Everything the engine needs. Deliberately a plain dataclass: the engine
    must be callable from a unit test with no bus, no spec repo, no LLM."""

    unit_id: str
    delta_id: str
    spec_version: str
    reports: Sequence[InstanceReport]
    passing_instance_ids: set[str] = field(default_factory=set)
    dont_care: Sequence[DontCareRegion] = ()
    level: str = EquivalenceLevel.BEHAVIOURAL
    tier_escalated: bool = False
    min_instances_for_verdict: int = 3


class DifferentialEngine:
    """Deterministic. Same inputs always yield the same report."""

    def __init__(self, dont_care: Iterable[DontCareRegion] = ()) -> None:
        self.mask = DontCareMask(dont_care)

    # ---------------------------------------------------------------- helpers

    def _channels(self, level: str) -> tuple[ObservationChannel, ...]:
        return EquivalenceLevel.CHANNELS[level]

    def _normalised(self, probe: ProbeResult, level: str) -> dict[str, object]:
        """Normalise one probe result into a comparable mapping."""

        out: dict[str, object] = {}
        for channel in self._channels(level):
            obs = probe.observation(channel)
            if obs is None:
                continue
            normalised, _ = self.mask.apply(channel.value, obs.value)
            out[channel.value] = normalised
        return out

    def _fingerprint(self, report: InstanceReport, level: str) -> str:
        from ..contracts.base import digest_of

        rows = []
        for probe in sorted(report.probe_results, key=lambda p: p.probe_id):
            rows.append((probe.probe_id, self._normalised(probe, level)))
        return digest_of(rows)

    # ------------------------------------------------------------------- API

    def cluster(self, data: DifferentialInput) -> list[EquivalenceClass]:
        """Group instances by behavioural fingerprint (LDB-style)."""

        buckets: dict[str, list[str]] = {}
        for report in data.reports:
            fp = self._fingerprint(report, data.level)
            buckets.setdefault(fp, []).append(report.manifest.instance_id)
        return [
            EquivalenceClass(
                fingerprint=fp,
                instance_ids=sorted(ids),
                representative=sorted(ids)[0],
            )
            for fp, ids in sorted(buckets.items())
        ]

    def diff_pair(
        self, left: InstanceReport, right: InstanceReport, level: str
    ) -> list[Divergence]:
        """Compare two instances probe by probe, channel by channel."""

        out: list[Divergence] = []
        right_by_probe = {p.probe_id: p for p in right.probe_results}
        for lp in sorted(left.probe_results, key=lambda p: p.probe_id):
            rp = right_by_probe.get(lp.probe_id)
            if rp is None:
                continue
            for channel in self._channels(level):
                lo, ro = lp.observation(channel), rp.observation(channel)
                if lo is None and ro is None:
                    continue
                lv = lo.value if lo else None
                rv = ro.value if ro else None
                nlv, _ = self.mask.apply(channel.value, lv)
                nrv, _ = self.mask.apply(channel.value, rv)
                if nlv == nrv:
                    continue
                # Raw values differ *and* survived normalisation. Ask whether any
                # single registered freedom explains it; if so the divergence is
                # licensed, otherwise it is a defect and must be resolved.
                region = self.mask.covering_region(channel.value, lv, rv)
                out.append(
                    Divergence(
                        probe_id=lp.probe_id,
                        channel=channel,
                        left_instance=left.manifest.instance_id,
                        right_instance=right.manifest.instance_id,
                        left_value=lv,
                        right_value=rv,
                        covered_by_dont_care=region,
                    )
                )
        return out

    def delta_diversity(self, data: DifferentialInput) -> float:
        """NEZHA-style delta diversity: how *informative* the probe set is.

        Fraction of probes that produced more than one distinct normalised
        observation tuple. A probe set with diversity 0 tells you nothing about
        spec silence no matter how many instances you sample, so this number is
        the scheduling signal for probe budget.
        """

        if not data.reports:
            return 0.0
        from ..contracts.base import canonical_json

        per_probe: dict[str, set[str]] = {}
        for report in data.reports:
            for probe in report.probe_results:
                key = canonical_json(self._normalised(probe, data.level))
                per_probe.setdefault(probe.probe_id, set()).add(key)
        if not per_probe:
            return 0.0
        discriminating = sum(1 for v in per_probe.values() if len(v) > 1)
        return discriminating / len(per_probe)

    def verdict(
        self,
        data: DifferentialInput,
        classes: Sequence[EquivalenceClass],
        divergences: Sequence[Divergence],
    ) -> DivergenceVerdict:
        """PDR-001 §6 decision table, implemented exactly."""

        total = len(data.reports)
        passing = len(data.passing_instance_ids)
        failing = total - passing
        unresolved = [d for d in divergences if d.is_defect]

        if total == 0:
            return DivergenceVerdict.INSUFFICIENT
        if failing and total < data.min_instances_for_verdict:
            return DivergenceVerdict.INSUFFICIENT
        if passing == total:
            return (
                DivergenceVerdict.CLOSED if not unresolved else DivergenceVerdict.SILENCE
            )
        if passing > 0:
            return DivergenceVerdict.AMBIGUITY
        # passing == 0
        return (
            DivergenceVerdict.INFEASIBLE
            if data.tier_escalated
            else DivergenceVerdict.UNSOLVED_AT_TIER
        )

    def run(self, data: DifferentialInput, report_id: str) -> DifferentialReport:
        classes = self.cluster(data)
        by_id = {r.manifest.instance_id: r for r in data.reports}

        divergences: list[Divergence] = []
        # Compare cluster representatives only: instances inside a class are
        # fingerprint-identical, so any intra-class pair is provably empty.
        reps = [c.representative for c in classes]
        for a, b in itertools.combinations(sorted(reps), 2):
            divergences.extend(self.diff_pair(by_id[a], by_id[b], data.level))

        probes = {p.probe_id for r in data.reports for p in r.probe_results}
        return DifferentialReport(
            report_id=report_id,
            unit_id=data.unit_id,
            delta_id=data.delta_id,
            spec_version=data.spec_version,
            instance_ids=sorted(by_id),
            passing_instance_ids=sorted(data.passing_instance_ids),
            classes=classes,
            divergences=divergences,
            verdict=self.verdict(data, classes, divergences),
            probes_executed=len(probes),
            delta_diversity=self.delta_diversity(data),
            tier_escalated=data.tier_escalated,
        )
