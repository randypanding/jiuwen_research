"""Gate framework.

A gate is a *pure function* from evidence to a verdict. It never fetches, never
retries, never repairs. That restriction is what makes gates testable, and
testable gates are the only kind worth having.

Three invariants hold for every hard gate in this package:

* **Silence is not consent.** Missing evidence yields ``ERROR``, never ``PASS``.
* **A failure always carries a finding.** A red gate with no reason cannot be
  acted on, and unactionable gates get disabled.
* **A gate never mutates its inputs.** Re-running a gate on the same evidence
  yields the same result, forever.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Protocol, Sequence

from ..contracts.base import digest_of
from ..contracts.gate import Finding, GateId, GateResult, GateStatus
from ..contracts.governance import MigrationStage
from ..contracts.oracle import HoldoutOracle, PublicOracle
from ..contracts.spec import RLevel, SpecDelta, SpecDocument
from ..contracts.wave import FanoutPlan
from ..oracle.golden import GoldenStore
from ..oracle.traceability import AnchorResolver, Exemption

__all__ = [
    "GateContext",
    "Gate",
    "GateRegistry",
    "missing_evidence",
    "not_applicable",
    "ok",
    "fail",
]


@dataclass
class GateContext:
    """All evidence a gate may look at. A gate that needs something not in here
    is a gate with a side effect, and must be split."""

    unit_id: str
    instance_id: str
    r_level: RLevel = RLevel.R1
    spec: SpecDocument | None = None
    spec_delta: SpecDelta | None = None
    #: The wave's fan-out plan for this unit, when declared. Deliberately the
    #: FanoutPlan contract — not a bare int — so the single-instance n/a
    #: carve-out in H5 can only be licensed by a plan that FanoutPlan.decide()
    #: could actually have produced (its signal carries the R level, which the
    #: gate cross-checks against ctx.r_level). None means undeclared; H5 then
    #: stays fail-closed about missing differential evidence (D9/D18).
    fanout_plan: FanoutPlan | None = None

    # H1 / H2 / H8: raw tool output, supplied by the harness adapter.
    build: Mapping[str, Any] = field(default_factory=dict)
    static: Mapping[str, Any] = field(default_factory=dict)
    unit_tests: Mapping[str, Any] = field(default_factory=dict)
    property_tests: Mapping[str, Any] = field(default_factory=dict)
    budget: Mapping[str, Any] = field(default_factory=dict)
    budget_limits: Mapping[str, Any] = field(default_factory=dict)
    runtime_guard: Mapping[str, Any] = field(default_factory=dict)

    # H3 / H5
    public_oracle: PublicOracle | None = None
    holdout_oracle: HoldoutOracle | None = None
    holdout_results: Mapping[str, bool] = field(default_factory=dict)
    holdout_inconclusive: frozenset[str] = frozenset()
    differential_report: Any | None = None
    golden_store: GoldenStore | None = None
    golden_comparisons: Sequence[Any] = ()

    # H4
    old_surface: Mapping[str, Any] | None = None
    new_surface: Mapping[str, Any] | None = None

    # H6
    invariant_results: Mapping[str, bool] = field(default_factory=dict)

    # H7
    anchor_resolver: AnchorResolver | None = None
    drift_baseline: Mapping[str, str] = field(default_factory=dict)
    exemptions: Sequence[Exemption] = ()
    today: str = "1970-01-01"
    contract_bearing_symbols: set[str] = field(default_factory=set)

    def evidence_digest(self) -> str:
        return digest_of(
            {
                "unit": self.unit_id,
                "instance": self.instance_id,
                "r_level": self.r_level.value,
                "build": dict(self.build),
                "static": dict(self.static),
                "unit_tests": dict(self.unit_tests),
                "property_tests": dict(self.property_tests),
                "budget": dict(self.budget),
                "holdout": dict(self.holdout_results),
                "invariants": dict(self.invariant_results),
            }
        )


class Gate(Protocol):
    gate_id: GateId
    name: str
    #: Relative execution cost, ascending (1 = table lookup / static check,
    #: 5 = multi-instance differential). Used only to order fail-fast runs;
    #: defaults to 3 when a gate does not declare one.
    relative_cost: int

    def run(self, ctx: GateContext) -> GateResult: ...


def ok(gate_id: GateId, summary: str, **detail: Any) -> GateResult:
    return GateResult(
        gate=gate_id,
        status=GateStatus.PASS,
        detail={"summary": summary, **detail},
    )


def fail(
    gate_id: GateId,
    summary: str,
    findings: Sequence[Finding],
    **detail: Any,
) -> GateResult:
    return GateResult(
        gate=gate_id,
        status=GateStatus.FAIL,
        findings=list(findings),
        detail={"summary": summary, **detail},
    )


def missing_evidence(gate_id: GateId, what: str) -> GateResult:
    """Uniform 'evidence absent' result. Always ERROR, never PASS."""

    return GateResult(
        gate=gate_id,
        status=GateStatus.ERROR,
        findings=[
            Finding(
                code=f"{gate_id.value}.NO_EVIDENCE",
                message=(
                    f"{gate_id.value} requires {what}, which was not supplied. "
                    "Absence of evidence is never evidence of absence."
                ),
            )
        ],
        detail={"summary": f"missing evidence: {what}"},
    )


def not_applicable(gate_id: GateId, summary: str, **detail: Any) -> GateResult:
    """Uniform 'declared not applicable' result.

    NOT_APPLICABLE admits (like PASS) but is a different status on purpose:
    the report must distinguish "measured and fine" from "declared out of
    scope for this unit" — an n/a recorded as a pass quietly erases the
    decision to skip. The declaration comes from the R level / wave plan,
    never from the instance.
    """

    return GateResult(
        gate=gate_id,
        status=GateStatus.NOT_APPLICABLE,
        detail={"summary": summary, **detail},
    )


class GateRegistry:
    """Ordered registry. Order matters only for reporting, not for the verdict:
    the admission algebra is a conjunction, so it is order-independent."""

    #: Default cost for gates that do not declare :attr:`Gate.relative_cost`.
    DEFAULT_COST = 3

    def __init__(self, gates: Iterable[Gate] = ()) -> None:
        self._gates: dict[GateId, Gate] = {}
        for g in gates:
            self.register(g)

    def register(self, gate: Gate) -> None:
        if gate.gate_id in self._gates:
            raise ValueError(f"gate {gate.gate_id} already registered")
        self._gates[gate.gate_id] = gate

    def get(self, gate_id: GateId) -> Gate | None:
        return self._gates.get(gate_id)

    def ids(self) -> list[GateId]:
        return sorted(self._gates, key=lambda g: g.value)

    def _cost(self, gate: Gate) -> int:
        return getattr(gate, "relative_cost", self.DEFAULT_COST)

    def run_all(self, ctx: GateContext, *, fail_fast: bool = False) -> list[GateResult]:
        """Run the gates and collect their results.

        Default behaviour is *run everything, record everything*: a red build
        must carry the full measurement so the diagnosis names every defect,
        not just the first. With ``fail_fast=True`` (D17: M2+ maturity stages),
        gates run in ascending cost order and the run stops at the first
        non-admitting result — the un-run gates then surface as missing in the
        hard report, which the fail-closed algebra already treats as a block.
        """

        if not fail_fast:
            return [self._gates[gid].run(ctx) for gid in self.ids()]
        results: list[GateResult] = []
        order = sorted(self._gates.values(), key=lambda g: (self._cost(g), g.gate_id.value))
        for gate in order:
            result = gate.run(ctx)
            results.append(result)
            if not result.status.admits:
                break
        return sorted(results, key=lambda r: r.gate.value)

    def run_for_stage(self, ctx: GateContext, stage: MigrationStage) -> list[GateResult]:
        """D17 consensus policy by migration stage.

        M0/M1 run every gate and record every measurement — the org is still
        calibrating its instruments, and early fail-fast would starve it of the
        very data it needs. From M2 on, fail-fast in ascending cost order:
        pay the cheap gates first, stop at the first blocker.
        """

        return self.run_all(ctx, fail_fast=stage is not MigrationStage.M0_HARVEST
                            and stage is not MigrationStage.M1_ANCHOR)
