"""The eight hard gates of PDR-001 §5.

Each gate is a small class with one method. They are deliberately boring: the
interesting engineering lives in :mod:`swarmkernel.oracle`, and a gate's job is
only to turn engine output into a verdict with a citable finding.
"""

from __future__ import annotations

from typing import Any, Sequence

from ..contracts.base import ChangeSeverity
from ..contracts.gate import Finding, GateId, GateResult, GateStatus
from ..contracts.instance import DivergenceVerdict
from ..contracts.spec import RLevel, WitnessKind
from ..oracle.compat import classify
from ..oracle.traceability import TraceabilityEngine
from .base import GateContext, missing_evidence

__all__ = [
    "H1Build",
    "H2UnitProperty",
    "H3Holdout",
    "H4ContractSurface",
    "H5Differential",
    "H6Invariant",
    "H7Drift",
    "H8Budget",
    "ALL_HARD_GATES",
]


def _ok(gate_id: GateId, ctx: GateContext, summary: str, **metrics: Any) -> GateResult:
    return GateResult(
        gate_id=gate_id,
        status=GateStatus.PASS,
        instance_id=ctx.instance_id,
        unit_id=ctx.unit_id,
        summary=summary,
        metrics=metrics,
    )


def _fail(
    gate_id: GateId,
    ctx: GateContext,
    summary: str,
    findings: Sequence[Finding],
    **metrics: Any,
) -> GateResult:
    return GateResult(
        gate_id=gate_id,
        status=GateStatus.FAIL,
        instance_id=ctx.instance_id,
        unit_id=ctx.unit_id,
        summary=summary,
        findings=list(findings),
        metrics=metrics,
    )


class H1Build:
    """Build, type check, static analysis.

    The cheapest gate, and therefore the first: it must reject before any model
    is paid to look at anything.
    """

    gate_id = GateId.H1_BUILD
    name = "build/type/static"

    def run(self, ctx: GateContext) -> GateResult:
        if not ctx.build:
            return missing_evidence(self.gate_id, "build result", ctx)
        findings: list[Finding] = []
        if not ctx.build.get("compiled", False):
            findings.append(
                Finding(
                    code="H1.BUILD_FAILED",
                    message=str(ctx.build.get("error", "build failed")),
                    blocking=True,
                )
            )
        type_errors = int(ctx.static.get("type_errors", 0))
        lint_errors = int(ctx.static.get("lint_errors", 0))
        if type_errors:
            findings.append(
                Finding(
                    code="H1.TYPE_ERRORS",
                    message=f"{type_errors} type error(s)",
                    blocking=True,
                    evidence_ref=str(ctx.static.get("type_report", "")) or None,
                )
            )
        if lint_errors:
            findings.append(
                Finding(
                    code="H1.LINT_ERRORS",
                    message=f"{lint_errors} lint error(s)",
                    blocking=True,
                    evidence_ref=str(ctx.static.get("lint_report", "")) or None,
                )
            )
        if findings:
            return _fail(
                self.gate_id, ctx, "build/type/static failed", findings,
                type_errors=type_errors, lint_errors=lint_errors,
            )
        return _ok(self.gate_id, ctx, "build clean", type_errors=0, lint_errors=0)


class H2UnitProperty:
    """Unit + property tests, with an explicit anti-vacuity check.

    A green suite that asserts nothing is the most expensive kind of green,
    because it buys false confidence at full price.
    """

    gate_id = GateId.H2_UNIT_PROPERTY
    name = "unit+property"

    def __init__(self, min_assertion_rate: float = 1.0) -> None:
        self.min_assertion_rate = min_assertion_rate

    def run(self, ctx: GateContext) -> GateResult:
        if not ctx.unit_tests:
            return missing_evidence(self.gate_id, "unit test results", ctx)
        findings: list[Finding] = []
        total = int(ctx.unit_tests.get("total", 0))
        failed = int(ctx.unit_tests.get("failed", 0))
        errors = int(ctx.unit_tests.get("errors", 0))
        assertion_rate = float(ctx.unit_tests.get("assertion_rate", 0.0))

        if total == 0:
            findings.append(
                Finding(
                    code="H2.NO_TESTS",
                    message="no unit tests executed; an empty suite never passes",
                    blocking=True,
                )
            )
        if failed or errors:
            findings.append(
                Finding(
                    code="H2.TESTS_FAILED",
                    message=f"{failed} failed, {errors} errored",
                    blocking=True,
                )
            )
        if total and assertion_rate < self.min_assertion_rate:
            findings.append(
                Finding(
                    code="H2.VACUOUS_TESTS",
                    message=(
                        f"assertion rate {assertion_rate:.2%} < required "
                        f"{self.min_assertion_rate:.0%}: some tests assert nothing"
                    ),
                    blocking=True,
                )
            )
        prop_falsified = list(ctx.property_tests.get("falsified", []) or [])
        if prop_falsified:
            findings.append(
                Finding(
                    code="H2.PROPERTY_FALSIFIED",
                    message=f"falsified properties: {sorted(prop_falsified)}",
                    blocking=True,
                    evidence_ref=str(ctx.property_tests.get("counterexample_ref", "")) or None,
                )
            )
        metrics = {
            "total": total,
            "failed": failed,
            "assertion_rate": assertion_rate,
            "properties_falsified": len(prop_falsified),
        }
        if findings:
            return _fail(self.gate_id, ctx, "unit/property failed", findings, **metrics)
        return _ok(self.gate_id, ctx, "unit/property clean", **metrics)


class H3Holdout:
    """Holdout scenarios: the builder never saw these.

    Three-valued by construction. An ``inconclusive`` scenario is not a pass;
    it is a request for more samples, and it blocks.
    """

    gate_id = GateId.H3_HOLDOUT
    name = "holdout scenarios"

    def run(self, ctx: GateContext) -> GateResult:
        if ctx.holdout_oracle is None:
            return missing_evidence(self.gate_id, "holdout oracle", ctx)
        if not ctx.holdout_results:
            return missing_evidence(self.gate_id, "holdout results", ctx)
        expected = {s.scenario_id for s in ctx.holdout_oracle.scenarios}
        got = set(ctx.holdout_results)
        findings: list[Finding] = []
        if expected - got:
            findings.append(
                Finding(
                    code="H3.SCENARIOS_NOT_RUN",
                    message=f"holdout scenarios not executed: {sorted(expected - got)}",
                    blocking=True,
                )
            )
        failing = sorted(k for k, v in ctx.holdout_results.items() if not v)
        if failing:
            findings.append(
                Finding(
                    code="H3.SCENARIO_FAILED",
                    message=f"failing holdout scenarios: {failing}",
                    blocking=True,
                )
            )
        if ctx.holdout_inconclusive:
            findings.append(
                Finding(
                    code="H3.INCONCLUSIVE",
                    message=(
                        "inconclusive holdout scenarios: "
                        f"{sorted(ctx.holdout_inconclusive)}; inconclusive never "
                        "defaults to pass"
                    ),
                    blocking=True,
                )
            )
        metrics = {
            "executed": len(got),
            "failing": len(failing),
            "inconclusive": len(ctx.holdout_inconclusive),
        }
        if findings:
            return _fail(self.gate_id, ctx, "holdout failed", findings, **metrics)
        return _ok(self.gate_id, ctx, "holdout clean", **metrics)


class H4ContractSurface:
    """Contract surface + breaking-change detection + version-bump enforcement."""

    gate_id = GateId.H4_SURFACE
    name = "contract surface"

    def run(self, ctx: GateContext) -> GateResult:
        if ctx.old_surface is None or ctx.new_surface is None:
            return missing_evidence(self.gate_id, "old and new contract surfaces", ctx)
        changes, severity, _semantic = classify(dict(ctx.old_surface), dict(ctx.new_surface))
        findings: list[Finding] = []
        breaking = [c for c in changes if c.severity is ChangeSeverity.BREAKING]

        delta = ctx.spec_delta
        if breaking and delta is None:
            findings.append(
                Finding(
                    code="H4.UNDECLARED_BREAKING_CHANGE",
                    message=(
                        f"{len(breaking)} breaking change(s) with no spec delta: "
                        f"{[c.code for c in breaking][:5]}"
                    ),
                    blocking=True,
                )
            )
        elif delta is not None:
            if severity.rank > delta.severity.rank:
                findings.append(
                    Finding(
                        code="H4.SEVERITY_UNDERSTATED",
                        message=(
                            f"observed severity {severity.value} exceeds declared "
                            f"{delta.severity.value}"
                        ),
                        blocking=True,
                    )
                )
            if not delta.version_bump_is_consistent():
                findings.append(
                    Finding(
                        code="H4.VERSION_NOT_BUMPED",
                        message=(
                            f"version {delta.from_version} -> {delta.to_version} does "
                            f"not match severity {delta.severity.value}"
                        ),
                        blocking=True,
                    )
                )
        for c in breaking:
            findings.append(
                Finding(code=c.code, message=f"{c.location}: {c.message}", blocking=True)
            )
        metrics = {
            "changes": len(changes),
            "breaking": len(breaking),
            "severity": severity.value,
        }
        if findings:
            return _fail(self.gate_id, ctx, "contract surface violation", findings, **metrics)
        return _ok(self.gate_id, ctx, f"surface compatible ({severity.value})", **metrics)


class H5Differential:
    """Cross-instance differential + golden comparison."""

    gate_id = GateId.H5_DIFFERENTIAL
    name = "differential/golden"

    #: Verdicts that may not proceed to admission.
    BLOCKING_VERDICTS = {
        DivergenceVerdict.AMBIGUITY,
        DivergenceVerdict.SILENCE,
        DivergenceVerdict.UNSOLVED_AT_TIER,
        DivergenceVerdict.INFEASIBLE,
        DivergenceVerdict.INSUFFICIENT,
    }

    gate_id_for_r3 = RLevel.R3

    def run(self, ctx: GateContext) -> GateResult:
        report = ctx.differential_report
        if report is None:
            if ctx.r_level is RLevel.R0:
                return _ok(self.gate_id, ctx, "R0: no fan-out, differential not applicable")
            return missing_evidence(self.gate_id, "differential report", ctx)

        findings: list[Finding] = []
        verdict = report.verdict
        if verdict in self.BLOCKING_VERDICTS:
            findings.append(
                Finding(
                    code=f"H5.{verdict.value.upper()}",
                    message=(
                        f"differential verdict {verdict.value}: "
                        f"{len(report.classes)} equivalence class(es), "
                        f"{len(report.unresolved_divergences())} unresolved divergence(s)"
                    ),
                    blocking=True,
                    evidence_ref=report.report_id,
                )
            )
        for d in report.unresolved_divergences()[:10]:
            findings.append(
                Finding(
                    code="H5.DIVERGENCE",
                    message=(
                        f"probe {d.probe_id} channel {d.channel.value}: "
                        f"{d.left_instance} != {d.right_instance}"
                    ),
                    blocking=True,
                )
            )

        if ctx.r_level is RLevel.R3:
            if ctx.golden_store is None:
                return missing_evidence(self.gate_id, "golden store (R3)", ctx)
            if not ctx.golden_comparisons:
                return missing_evidence(self.gate_id, "golden comparisons (R3)", ctx)
            for comp in ctx.golden_comparisons:
                if not comp.matched:
                    findings.append(
                        Finding(
                            code="H5.GOLDEN_MISMATCH",
                            message=(
                                f"golden {comp.golden_id} mismatch"
                                + (
                                    f"; environment drift: {list(comp.environment_drift)}"
                                    if comp.environment_drift
                                    else ""
                                )
                            ),
                            blocking=True,
                            evidence_ref=comp.golden_id,
                        )
                    )
        metrics = {
            "verdict": verdict.value,
            "classes": len(report.classes),
            "delta_diversity": report.delta_diversity,
        }
        if findings:
            return _fail(self.gate_id, ctx, f"differential {verdict.value}", findings, **metrics)
        return _ok(self.gate_id, ctx, f"differential {verdict.value}", **metrics)


class H6Invariant:
    """Spec invariants + runtime guardrails."""

    gate_id = GateId.H6_INVARIANT
    name = "invariants/guardrails"

    def run(self, ctx: GateContext) -> GateResult:
        if ctx.spec is None:
            return missing_evidence(self.gate_id, "spec document", ctx)
        required = {
            c.id
            for c in ctx.spec.clauses
            if c.invariant and c.status.value == "active"
        }
        if required and not ctx.invariant_results:
            return missing_evidence(self.gate_id, "invariant check results", ctx)
        findings: list[Finding] = []
        unchecked = required - set(ctx.invariant_results)
        if unchecked:
            findings.append(
                Finding(
                    code="H6.INVARIANT_UNCHECKED",
                    message=f"invariants never evaluated: {sorted(unchecked)}",
                    blocking=True,
                )
            )
        violated = sorted(k for k, v in ctx.invariant_results.items() if not v)
        if violated:
            findings.append(
                Finding(
                    code="H6.INVARIANT_VIOLATED",
                    message=f"violated invariants: {violated}",
                    blocking=True,
                )
            )
        guard_trips = list(ctx.runtime_guard.get("violations", []) or [])
        if guard_trips:
            findings.append(
                Finding(
                    code="H6.GUARDRAIL_TRIPPED",
                    message=f"runtime guardrail violations: {guard_trips}",
                    blocking=True,
                )
            )
        metrics = {"required": len(required), "violated": len(violated), "guard_trips": len(guard_trips)}
        if findings:
            return _fail(self.gate_id, ctx, "invariant violation", findings, **metrics)
        return _ok(self.gate_id, ctx, "invariants hold", **metrics)


class H7Drift:
    """Spec<->code drift, plus the unverifiable-clause census."""

    gate_id = GateId.H7_DRIFT
    name = "spec/code drift"

    def __init__(self, min_coverage: float = 1.0) -> None:
        self.min_coverage = min_coverage

    def run(self, ctx: GateContext) -> GateResult:
        if ctx.spec is None:
            return missing_evidence(self.gate_id, "spec document", ctx)
        if ctx.anchor_resolver is None:
            return missing_evidence(self.gate_id, "code snapshot for anchor resolution", ctx)
        engine = TraceabilityEngine(
            resolver=ctx.anchor_resolver,
            exemptions=ctx.exemptions,
            today=ctx.today,
            contract_bearing_symbols=set(ctx.contract_bearing_symbols),
        )
        drift = engine.check(ctx.spec)
        coverage = engine.coverage(ctx.spec)
        findings = [
            Finding(
                code=f"H7.{d.kind.value.upper()}",
                message=d.message,
                blocking=d.blocking,
                clause_id=d.clause_id,
                evidence_ref=d.anchor_ref,
            )
            for d in drift
            if d.blocking
        ]
        for e in engine.expired_exemptions():
            findings.append(
                Finding(
                    code="H7.EXEMPTION_EXPIRED",
                    message=(
                        f"exemption for {e.target} ({e.kind.value}) owned by {e.owner} "
                        f"expired on {e.expires_on}"
                    ),
                    blocking=True,
                )
            )
        if coverage < self.min_coverage:
            findings.append(
                Finding(
                    code="H7.COVERAGE_BELOW_THRESHOLD",
                    message=f"anchor coverage {coverage:.2%} < {self.min_coverage:.0%}",
                    blocking=True,
                )
            )
        unverifiable = ctx.spec.unverifiable_clauses()
        metrics = {
            "coverage": coverage,
            "drift_findings": len(drift),
            "unverifiable_clauses": len(unverifiable),
        }
        if findings:
            return _fail(self.gate_id, ctx, "spec/code drift", findings, **metrics)
        result = _ok(self.gate_id, ctx, "spec and code agree", **metrics)
        if unverifiable:
            # Advisory, non-blocking: an unverifiable clause is a spec-quality
            # debt, not an implementation defect. It is surfaced every run so it
            # cannot quietly accumulate.
            return result.model_copy(
                update={
                    "findings": [
                        Finding(
                            code="H7.UNVERIFIABLE_CLAUSE",
                            message=(
                                f"{len(unverifiable)} clause(s) bind no mechanical "
                                "witness and no holdout scenario; advisory only"
                            ),
                            blocking=False,
                            clause_id=unverifiable[0].id,
                        )
                    ]
                }
            )
        return result


class H8Budget:
    """Cost, resource and performance budget."""

    gate_id = GateId.H8_BUDGET
    name = "budget"

    def run(self, ctx: GateContext) -> GateResult:
        if not ctx.budget_limits:
            return missing_evidence(self.gate_id, "budget limits", ctx)
        if not ctx.budget:
            return missing_evidence(self.gate_id, "budget measurements", ctx)
        findings: list[Finding] = []
        metrics: dict[str, Any] = {}
        for key, limit in sorted(ctx.budget_limits.items()):
            actual = ctx.budget.get(key)
            if actual is None:
                findings.append(
                    Finding(
                        code="H8.UNMEASURED",
                        message=f"budget {key!r} has a limit but was never measured",
                        blocking=True,
                    )
                )
                continue
            metrics[key] = actual
            if float(actual) > float(limit):
                findings.append(
                    Finding(
                        code="H8.BUDGET_EXCEEDED",
                        message=f"{key}: {actual} exceeds limit {limit}",
                        blocking=True,
                    )
                )
        if findings:
            return _fail(self.gate_id, ctx, "budget exceeded", findings, **metrics)
        return _ok(self.gate_id, ctx, "within budget", **metrics)


ALL_HARD_GATES = (
    H1Build,
    H2UnitProperty,
    H3Holdout,
    H4ContractSurface,
    H5Differential,
    H6Invariant,
    H7Drift,
    H8Budget,
)


def default_registry(**kwargs: Any):
    from .base import GateRegistry

    return GateRegistry([cls() for cls in ALL_HARD_GATES])


def witness_kinds_satisfied(ctx: GateContext) -> set[WitnessKind]:
    """Which mechanical witness kinds this context actually provides.

    Used by the spec tooling to decide whether a clause's declared witness is
    backed by a gate that really ran.
    """

    out: set[WitnessKind] = set()
    if ctx.unit_tests:
        out.add(WitnessKind.UNIT_TEST)
    if ctx.property_tests:
        out.add(WitnessKind.PROPERTY)
    if ctx.static:
        out.add(WitnessKind.STATIC_CHECK)
    if ctx.new_surface is not None:
        out.add(WitnessKind.CONTRACT_CHECK)
    if ctx.differential_report is not None:
        out.add(WitnessKind.DIFFERENTIAL)
    if ctx.golden_comparisons:
        out.add(WitnessKind.GOLDEN)
    if ctx.invariant_results:
        out.add(WitnessKind.RUNTIME_ASSERTION)
    return out
