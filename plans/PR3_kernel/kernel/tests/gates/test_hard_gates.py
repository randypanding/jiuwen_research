"""H1-H8, one gate at a time.

The structure of every test in this file is deliberate: start from a context in
which *all* evidence is good, break exactly one thing, and assert that exactly
the gate responsible fails. A gate that fires on someone else's defect is as
useless as one that never fires, because both destroy the diagnostic value of a
red build.
"""

from __future__ import annotations

import pytest

from swarmkernel.contracts.base import ChangeSeverity, digest_of
from swarmkernel.contracts.gate import GateId, GateStatus
from swarmkernel.contracts.instance import DivergenceVerdict
from swarmkernel.contracts.spec import RLevel, SpecDelta, SpecDeltaItem, WitnessKind
from swarmkernel.gates.base import GateContext, GateRegistry
from swarmkernel.gates.hard import (
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
from swarmkernel.oracle.differ import DifferentialEngine, DifferentialInput
from swarmkernel.oracle.golden import GoldenComparison, GoldenStore
from swarmkernel.oracle.surface import extract_module_surface

from ..conftest import make_report

SRC = "def total(lines):\n    return 0\n"


def surface(src: str = SRC) -> dict:
    return {"modules": {"cart.total": extract_module_surface(src, "cart.total").to_dict()},
            "schemas": {}}


@pytest.fixture
def good_report(dont_care_order):
    reports = [make_report(i, breakdown=["x", "y"]) for i in ("a", "b", "c")]
    engine = DifferentialEngine([dont_care_order])
    return engine.run(
        DifferentialInput(
            unit_id="UNIT-CART",
            delta_id="DELTA-001",
            spec_version="1.2.0",
            reports=reports,
            passing_instance_ids={r.manifest.instance_id for r in reports},
            dont_care=[dont_care_order],
        ),
        "DR-OK",
    )


@pytest.fixture
def ctx(spec, holdout_oracle, public_oracle, resolver, baseline, good_report) -> GateContext:
    """Every gate passes on this context. Tests break one field at a time."""

    return GateContext(
        unit_id="UNIT-CART",
        instance_id="inst-a",
        r_level=RLevel.R1,
        spec=spec,
        spec_delta=None,
        build={"compiled": True},
        static={"type_errors": 0, "lint_errors": 0},
        unit_tests={"total": 12, "failed": 0, "errors": 0, "assertion_rate": 1.0},
        property_tests={"falsified": []},
        budget={"usd": 0.8, "wall_time_s": 45},
        budget_limits={"usd": 2.0, "wall_time_s": 120},
        runtime_guard={"violations": []},
        public_oracle=public_oracle,
        holdout_oracle=holdout_oracle,
        holdout_results={s.id: True for s in holdout_oracle.scenarios},
        differential_report=good_report,
        old_surface=surface(),
        new_surface=surface(),
        invariant_results={"L2-CART.CURRENCY-002": True},
        anchor_resolver=resolver,
        drift_baseline=baseline,
        today="2026-08-15",
    )


def run(gate, ctx):
    return gate.run(ctx)


def replace(ctx: GateContext, **kw) -> GateContext:
    import dataclasses

    return dataclasses.replace(ctx, **kw)


# ------------------------------------------------------- everything passes


def test_the_reference_context_passes_every_gate(ctx):
    """If this ever fails, every negative test below is meaningless."""

    for gate_cls in ALL_HARD_GATES:
        result = gate_cls().run(ctx)
        assert result.status is GateStatus.PASS, (gate_cls.__name__, result.findings)


# ------------------------------------------------------------------- H1


def test_h1_fails_on_a_broken_build(ctx):
    result = H1Build().run(replace(ctx, build={"compiled": False, "error": "boom"}))
    assert result.status is GateStatus.FAIL
    assert {f.code for f in result.findings} == {"H1.BUILD_FAILED"}


def test_h1_fails_on_type_errors(ctx):
    result = H1Build().run(replace(ctx, static={"type_errors": 3, "lint_errors": 0}))
    assert result.status is GateStatus.FAIL
    assert "H1.TYPE_ERRORS" in {f.code for f in result.findings}


def test_h1_fails_on_lint_errors(ctx):
    result = H1Build().run(replace(ctx, static={"type_errors": 0, "lint_errors": 1}))
    assert result.status is GateStatus.FAIL


def test_h1_errors_when_the_build_never_ran(ctx):
    result = H1Build().run(replace(ctx, build={}))
    assert result.status is GateStatus.ERROR


# ------------------------------------------------------------------- H2


def test_h2_fails_on_failing_tests(ctx):
    result = H2UnitProperty().run(
        replace(ctx, unit_tests={"total": 12, "failed": 1, "errors": 0, "assertion_rate": 1.0})
    )
    assert result.status is GateStatus.FAIL
    assert "H2.TESTS_FAILED" in {f.code for f in result.findings}


def test_h2_fails_on_an_empty_suite(ctx):
    """"0 failed" is not "passed"."""

    result = H2UnitProperty().run(
        replace(ctx, unit_tests={"total": 0, "failed": 0, "errors": 0, "assertion_rate": 1.0})
    )
    assert result.status is GateStatus.FAIL
    assert "H2.NO_TESTS" in {f.code for f in result.findings}


def test_h2_fails_on_tests_that_assert_nothing(ctx):
    """The 80%-of-agent-tests problem, made mechanical."""

    result = H2UnitProperty().run(
        replace(ctx, unit_tests={"total": 12, "failed": 0, "errors": 0, "assertion_rate": 0.5})
    )
    assert result.status is GateStatus.FAIL
    assert "H2.VACUOUS_TESTS" in {f.code for f in result.findings}


def test_h2_fails_on_a_falsified_property(ctx):
    result = H2UnitProperty().run(
        replace(ctx, property_tests={"falsified": ["P-TOTAL-SUM"], "counterexample": {"lines": []}})
    )
    assert result.status is GateStatus.FAIL
    finding = next(f for f in result.findings if f.code == "H2.PROPERTY_FALSIFIED")
    assert finding.evidence["counterexample"] == {"lines": []}


# ------------------------------------------------------------------- H3


def test_h3_fails_on_a_failing_holdout_scenario(ctx, holdout_oracle):
    results = {s.id: True for s in holdout_oracle.scenarios}
    results["SC-CURRENCY-MIX"] = False
    result = H3Holdout().run(replace(ctx, holdout_results=results))
    assert result.status is GateStatus.FAIL
    finding = next(f for f in result.findings if f.code == "H3.SCENARIO_FAILED")
    assert "L2-CART.CURRENCY-002" in finding.clause_ids


def test_h3_fails_when_a_scenario_was_never_run(ctx, holdout_oracle):
    """Silently skipping the hard scenario is the cheapest way to fake a pass."""

    results = {holdout_oracle.scenarios[0].id: True}
    result = H3Holdout().run(replace(ctx, holdout_results=results))
    assert result.status is GateStatus.FAIL
    assert "H3.SCENARIOS_NOT_RUN" in {f.code for f in result.findings}


def test_h3_fails_on_inconclusive_never_defaults_to_pass(ctx, holdout_oracle):
    result = H3Holdout().run(
        replace(ctx, holdout_inconclusive=frozenset({"SC-EMPTY"}))
    )
    assert result.status is GateStatus.FAIL
    assert "H3.INCONCLUSIVE" in {f.code for f in result.findings}


def test_h3_errors_without_a_holdout_oracle(ctx):
    assert H3Holdout().run(replace(ctx, holdout_oracle=None)).status is GateStatus.ERROR


# ------------------------------------------------------------------- H4


def test_h4_fails_on_an_undeclared_breaking_change(ctx):
    result = H4ContractSurface().run(
        replace(ctx, new_surface=surface("def total(lines, tax):\n    return 0\n"))
    )
    assert result.status is GateStatus.FAIL
    assert "H4.UNDECLARED_BREAKING_CHANGE" in {f.code for f in result.findings}


def test_h4_fails_when_the_delta_understates_the_change(ctx):
    """The SemVer-compliance problem: the author says "additive", the surface
    says "breaking". The surface wins."""

    delta = SpecDelta(
        delta_id="D",
        spec_id="SPEC-CART",
        from_version="1.2.0",
        to_version="1.3.0",
        items=[
            SpecDeltaItem(
                op="amend_clause",
                clause_id="L2-CART.TOTAL-001",
                severity=ChangeSeverity.ADDITIVE,
                rationale="small tweak",
            )
        ],
    )
    result = H4ContractSurface().run(
        replace(
            ctx,
            spec_delta=delta,
            new_surface=surface("def total(lines, tax):\n    return 0\n"),
        )
    )
    assert result.status is GateStatus.FAIL
    assert "H4.SEVERITY_UNDERSTATED" in {f.code for f in result.findings}


def test_h4_accepts_a_correctly_declared_breaking_change(ctx):
    """A declared, version-bumped breaking change is legal. H4 catches
    *undeclared* breakage; it does not forbid breakage."""

    delta = SpecDelta(
        delta_id="D",
        spec_id="SPEC-CART",
        from_version="1.2.0",
        to_version="2.0.0",
        items=[
            SpecDeltaItem(
                op="amend_clause",
                clause_id="L2-CART.TOTAL-001",
                severity=ChangeSeverity.BREAKING,
                rationale="tax is now mandatory",
            )
        ],
    )
    result = H4ContractSurface().run(
        replace(
            ctx,
            spec_delta=delta,
            new_surface=surface("def total(lines, tax):\n    return 0\n"),
        )
    )
    assert result.status is GateStatus.PASS


def test_h4_ignores_internal_refactoring(ctx):
    result = H4ContractSurface().run(
        replace(ctx, new_surface=surface("def total(lines):\n    x = 0\n    return x\n"))
    )
    assert result.status is GateStatus.PASS


# ------------------------------------------------------------------- H5


@pytest.mark.parametrize(
    "verdict",
    [
        DivergenceVerdict.SILENCE,
        DivergenceVerdict.AMBIGUITY,
        DivergenceVerdict.UNSOLVED_AT_TIER,
        DivergenceVerdict.INFEASIBLE,
        DivergenceVerdict.INSUFFICIENT,
    ],
)
def test_h5_blocks_every_non_closed_verdict(ctx, good_report, verdict):
    """Only CLOSED admits. In particular INSUFFICIENT must block: "we could not
    tell" is the one answer that must never be rounded up to "fine"."""

    report = good_report.model_copy(update={"verdict": verdict})
    result = H5Differential().run(replace(ctx, differential_report=report))
    assert result.status is GateStatus.FAIL


def test_h5_passes_on_closed(ctx):
    assert H5Differential().run(ctx).status is GateStatus.PASS


def test_h5_is_not_applicable_at_r0(ctx):
    """R0 has no fan-out, so the gate reports "n/a" rather than being skipped:
    a skipped gate leaves a hole in the report, an n/a one does not."""

    result = H5Differential().run(
        replace(ctx, r_level=RLevel.R0, differential_report=None)
    )
    assert result.status is GateStatus.PASS
    assert result.detail["verdict"] == "n/a"


def test_h5_errors_at_r1_without_a_differential_report(ctx):
    result = H5Differential().run(replace(ctx, differential_report=None))
    assert result.status is GateStatus.ERROR


def test_h5_requires_goldens_at_r3(ctx):
    result = H5Differential().run(replace(ctx, r_level=RLevel.R3))
    assert result.status is GateStatus.ERROR


def test_h5_fails_on_a_golden_mismatch_at_r3(ctx):
    comparison = GoldenComparison(
        golden_id="G1",
        matched=False,
        expected_digest=digest_of("a"),
        actual_digest=digest_of("b"),
    )
    result = H5Differential().run(
        replace(
            ctx,
            r_level=RLevel.R3,
            golden_store=GoldenStore([]),
            golden_comparisons=[comparison],
        )
    )
    assert result.status is GateStatus.FAIL
    assert "H5.GOLDEN_MISMATCH" in {f.code for f in result.findings}


def test_h5_reports_environment_drift_alongside_the_mismatch(ctx):
    comparison = GoldenComparison(
        golden_id="G1",
        matched=False,
        expected_digest=digest_of("a"),
        actual_digest=digest_of("b"),
        environment_drift=("python_version: '3.12' -> '3.13'",),
    )
    result = H5Differential().run(
        replace(
            ctx,
            r_level=RLevel.R3,
            golden_store=GoldenStore([]),
            golden_comparisons=[comparison],
        )
    )
    assert result.status is GateStatus.FAIL
    assert any("environment drift" in f.message for f in result.findings)


# ------------------------------------------------------------------- H6


def test_h6_fails_on_a_violated_invariant(ctx):
    result = H6Invariant().run(
        replace(ctx, invariant_results={"L2-CART.CURRENCY-002": False})
    )
    assert result.status is GateStatus.FAIL
    assert "H6.INVARIANT_VIOLATED" in {f.code for f in result.findings}


def test_h6_fails_when_an_invariant_was_never_evaluated(ctx):
    result = H6Invariant().run(replace(ctx, invariant_results={"L2-OTHER-001": True}))
    assert result.status is GateStatus.FAIL
    assert "H6.INVARIANT_UNCHECKED" in {f.code for f in result.findings}


def test_h6_fails_on_a_runtime_guardrail_trip(ctx):
    result = H6Invariant().run(
        replace(ctx, runtime_guard={"violations": ["egress to unapproved host"]})
    )
    assert result.status is GateStatus.FAIL
    assert "H6.GUARDRAIL_TRIPPED" in {f.code for f in result.findings}


# ------------------------------------------------------------------- H7


def test_h7_fails_on_structural_drift(ctx):
    from swarmkernel.oracle.traceability import AnchorResolver

    drifted = AnchorResolver(
        sources={"cart/total.py": "def total(lines, discount): ...\n"},
        symbols={"cart/total.py::total": "def total(lines, discount) -> Decimal"},
    )
    result = H7Drift().run(replace(ctx, anchor_resolver=drifted))
    assert result.status is GateStatus.FAIL
    assert "H7.STRUCTURAL_DRIFT" in {f.code for f in result.findings}


def test_h7_fails_on_an_expired_exemption(ctx):
    from swarmkernel.oracle.traceability import DriftKind, Exemption

    result = H7Drift().run(
        replace(
            ctx,
            exemptions=[
                Exemption(
                    target="anything",
                    kind=DriftKind.ORPHAN_CLAUSE,
                    owner="alice",
                    expires_on="2020-01-01",
                    reason="stale",
                )
            ],
        )
    )
    assert result.status is GateStatus.FAIL
    assert "H7.EXEMPTION_EXPIRED" in {f.code for f in result.findings}


def test_h7_reports_unverifiable_clauses_as_a_warning_not_a_block(ctx):
    """The advisory clause in the fixture spec must not block admission, but it
    must be visible on every single run so the debt cannot be forgotten."""

    result = H7Drift().run(ctx)
    assert result.status is GateStatus.PASS
    warning = next(f for f in result.findings if f.code == "H7.UNVERIFIABLE_CLAUSE")
    assert warning.severity == "warning"
    assert "L1-CART.UX-003" in warning.clause_ids


# ------------------------------------------------------------------- H8


def test_h8_fails_when_a_budget_is_exceeded(ctx):
    result = H8Budget().run(replace(ctx, budget={"usd": 5.0, "wall_time_s": 45}))
    assert result.status is GateStatus.FAIL
    finding = next(f for f in result.findings if f.code == "H8.BUDGET_EXCEEDED")
    assert finding.evidence == {"limit": 2.0, "actual": 5.0}


def test_h8_fails_when_a_limited_resource_was_never_measured(ctx):
    """An unmeasured budget is an unbounded one."""

    result = H8Budget().run(replace(ctx, budget={"usd": 0.8}))
    assert result.status is GateStatus.FAIL
    assert "H8.UNMEASURED" in {f.code for f in result.findings}


def test_h8_errors_without_declared_limits(ctx):
    assert H8Budget().run(replace(ctx, budget_limits={})).status is GateStatus.ERROR


# --------------------------------------------------------------- registry


def test_the_registry_covers_every_hard_gate():
    registry = default_registry()
    assert set(registry.ids()) == {g for g in GateId if g.is_hard}


def test_the_registry_refuses_duplicate_gates():
    with pytest.raises(ValueError, match="already registered"):
        GateRegistry([H1Build(), H1Build()])


def test_running_the_registry_produces_one_result_per_gate(ctx):
    results = default_registry().run_all(ctx)
    assert len(results) == 8
    assert all(r.status is GateStatus.PASS for r in results)


# ----------------------------------------------------------- witness kinds


def test_witness_kinds_reflect_the_evidence_actually_present(ctx):
    kinds = witness_kinds_satisfied(ctx)
    assert WitnessKind.UNIT in kinds
    assert WitnessKind.HOLDOUT in kinds
    assert WitnessKind.DIFFERENTIAL in kinds
    assert WitnessKind.GOLDEN not in kinds


def test_a_declared_witness_with_no_gate_behind_it_is_detectable(ctx):
    """The check that stops "we bound a witness" from meaning "we ran one"."""

    kinds = witness_kinds_satisfied(replace(ctx, unit_tests={}, property_tests={}))
    assert WitnessKind.UNIT not in kinds
    assert WitnessKind.PROPERTY not in kinds
