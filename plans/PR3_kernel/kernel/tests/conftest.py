"""Shared fixtures.

Everything here is a *complete, valid* artefact set for one imaginary unit
(``UNIT-CART``) so that tests can mutate one thing at a time and observe exactly
one failure. Fixtures never reach the network, the filesystem, or a model.
"""

from __future__ import annotations

import pytest

from swarmkernel.contracts.base import ChangeSeverity, Role
from swarmkernel.contracts.gate import GateId
from swarmkernel.contracts.instance import (
    InstanceManifest,
    InstanceReport,
    Observation,
    ProbeResult,
)
from swarmkernel.contracts.oracle import (
    HoldoutOracle,
    JudgeProtocol,
    MetamorphicRelation,
    MutationProbe,
    ObservationChannel,
    OracleBundle,
    PropertySpec,
    PublicOracle,
    RubricCriterion,
    Scenario,
    ScenarioKind,
)
from swarmkernel.contracts.spec import (
    Anchor,
    Clause,
    DontCareCategory,
    DontCareRegion,
    FreedomTrack,
    PropertyKind,
    RLevel,
    RegenerationUnit,
    SpecDelta,
    SpecDeltaItem,
    SpecDocument,
    SpecLayer,
    WitnessBinding,
    WitnessKind,
)
from swarmkernel.oracle.traceability import AnchorResolver, build_baseline

UNIT = "UNIT-CART"


# --------------------------------------------------------------------- spec


@pytest.fixture
def clause_total() -> Clause:
    return Clause(
        id="L2-CART.TOTAL-001",
        layer=SpecLayer.L2,
        title="Cart total is the sum of line totals",
        text=(
            "total() returns the sum over lines of (unit_price * quantity), "
            "rounded half-up to 2 decimal places."
        ),
        kind=PropertyKind.SAFETY,
        requires=["every line has quantity >= 1"],
        ensures=["result >= 0", "result is rounded to 2dp"],
        witnesses=[
            WitnessBinding(
                kind=WitnessKind.UNIT,
                gate_id=GateId.H2_UNIT_PROPERTY,
                selector="tests/test_cart.py::test_total",
            ),
            WitnessBinding(
                kind=WitnessKind.PROPERTY,
                gate_id=GateId.H2_UNIT_PROPERTY,
                selector="prop:total_is_sum",
            ),
        ],
        anchors=[Anchor(path="cart/total.py", symbol="total", kind="function")],
    )


@pytest.fixture
def clause_currency() -> Clause:
    return Clause(
        id="L2-CART.CURRENCY-002",
        layer=SpecLayer.L2,
        title="Mixed currencies are rejected",
        text="total() raises CurrencyMismatch when lines use more than one currency.",
        kind=PropertyKind.SAFETY,
        invariant=["all lines share one currency"],
        ensures=["raises CurrencyMismatch on mixed input"],
        witnesses=[
            WitnessBinding(
                kind=WitnessKind.HOLDOUT,
                gate_id=GateId.H3_HOLDOUT,
                selector="SC-CURRENCY-MIX",
            )
        ],
        anchors=[Anchor(path="cart/total.py", symbol="total", kind="function")],
    )


@pytest.fixture
def clause_unverifiable() -> Clause:
    """A clause with no mechanical witness: advisory only, never admitting."""

    return Clause(
        id="L1-CART.UX-003",
        layer=SpecLayer.L1,
        title="Totals should feel instant to the shopper",
        text="The shopper should not perceive latency when the cart updates.",
        kind=PropertyKind.LIVENESS,
        witnesses=[],
        anchors=[Anchor(path="cart/total.py", kind="module")],
    )


@pytest.fixture
def dont_care_order() -> DontCareRegion:
    return DontCareRegion(
        id="DC-LINE-ORDER",
        category=DontCareCategory.OUTPUT_FREEDOM,
        track=FreedomTrack.UNSPECIFIED,
        description="The order of the returned breakdown lines is unspecified.",
        selectors=["return.breakdown"],
        normalizer="sort_list",
        justification_clause_ids=["L2-CART.TOTAL-001"],
    )


@pytest.fixture
def spec(clause_total, clause_currency, clause_unverifiable, dont_care_order) -> SpecDocument:
    return SpecDocument(
        spec_id="SPEC-CART",
        version="1.2.0",
        domain="checkout",
        clauses=[clause_total, clause_currency, clause_unverifiable],
        dont_care=[dont_care_order],
    )


@pytest.fixture
def unit_r1() -> RegenerationUnit:
    return RegenerationUnit(
        id=UNIT,
        title="Cart totalling",
        r_level=RLevel.R1,
        paths=["cart/"],
        surface_paths=["cart/total.py"],
        clause_ids=["L2-CART.TOTAL-001", "L2-CART.CURRENCY-002"],
    )


@pytest.fixture
def additive_delta() -> SpecDelta:
    return SpecDelta(
        delta_id="DELTA-001",
        spec_id="SPEC-CART",
        from_version="1.2.0",
        to_version="1.3.0",
        items=[
            SpecDeltaItem(
                op="add_clause",
                clause_id="L2-CART.DISCOUNT-004",
                severity=ChangeSeverity.ADDITIVE,
                rationale="new optional discount parameter",
            )
        ],
    )


# ------------------------------------------------------------------- oracle


@pytest.fixture
def public_oracle() -> PublicOracle:
    return PublicOracle(
        bundle_id="OB-CART-1",
        unit_id=UNIT,
        properties=[
            PropertySpec(
                id="P-TOTAL-SUM",
                clause_ids=["L2-CART.TOTAL-001"],
                entrypoint="cart.total",
                strategy="lists(line_strategy, min_size=1)",
                predicate="result == sum(l.price * l.qty for l in lines)",
            )
        ],
        metamorphic=[
            MetamorphicRelation(
                id="MR-PERMUTE",
                clause_ids=["L2-CART.TOTAL-001"],
                entrypoint="cart.total",
                transform="permute(lines)",
                relation="output_equal",
            )
        ],
        smoke_entrypoints=["cart.total"],
    )


@pytest.fixture
def holdout_oracle() -> HoldoutOracle:
    return HoldoutOracle(
        bundle_id="OB-CART-1",
        unit_id=UNIT,
        scenarios=[
            Scenario(
                id="SC-EMPTY",
                kind=ScenarioKind.EXAMPLE,
                clause_ids=["L2-CART.TOTAL-001"],
                entrypoint="cart.total",
                inputs={"lines": []},
                expect={"return": "0.00"},
            ),
            Scenario(
                id="SC-CURRENCY-MIX",
                kind=ScenarioKind.ADVERSARIAL,
                clause_ids=["L2-CART.CURRENCY-002"],
                entrypoint="cart.total",
                inputs={"lines": [{"ccy": "EUR"}, {"ccy": "USD"}]},
                expect={"exception": "CurrencyMismatch"},
                observed_channels=[ObservationChannel.EXCEPTION],
            ),
        ],
        rubric=[
            RubricCriterion(
                id="RC-READABILITY",
                question="Does the implementation hide a special case behind a magic constant?",
                veto_when="a magic constant encodes a scenario-specific answer",
            )
        ],
        judge_protocol=JudgeProtocol(samples=3, aggregation="any_veto"),
        mutation_probes=[
            MutationProbe(
                id="MP-ROUND",
                description="round half-down instead of half-up",
                target_clause_ids=["L2-CART.TOTAL-001"],
                mutation="rounding:half_down",
                must_be_caught_by=["H2"],
            ),
            MutationProbe(
                id="MP-CURRENCY",
                description="drop the currency check",
                target_clause_ids=["L2-CART.CURRENCY-002"],
                mutation="drop_validation:currency",
                must_be_caught_by=["H3"],
            ),
        ],
    )


@pytest.fixture
def bundle(public_oracle, holdout_oracle) -> OracleBundle:
    return OracleBundle(
        bundle_id="OB-CART-1",
        unit_id=UNIT,
        spec_version="1.2.0",
        public=public_oracle,
        holdout=holdout_oracle,
    )


# ----------------------------------------------------------------- instances


def make_report(
    instance_id: str,
    *,
    breakdown: list[str],
    total: str = "10.00",
    exception: str | None = None,
    builder_id: str = "builder-a",
) -> InstanceReport:
    observations = [
        Observation(channel=ObservationChannel.RETURN, value={"total": total, "breakdown": breakdown}),
    ]
    if exception is not None:
        observations.append(
            Observation(channel=ObservationChannel.EXCEPTION, value=exception)
        )
    return InstanceReport(
        manifest=InstanceManifest(
            instance_id=instance_id,
            unit_id=UNIT,
            spec_version="1.2.0",
            delta_id="DELTA-001",
            builder_id=builder_id,
            model_tier=2,
            tree_digest=f"tree-{instance_id}",
        ),
        self_check_passed=True,
        probe_results=[
            ProbeResult(
                probe_id="PR-TOTAL",
                entrypoint="cart.total",
                observations=observations,
            )
        ],
    )


@pytest.fixture
def three_agreeing_reports() -> list[InstanceReport]:
    return [
        make_report("inst-a", breakdown=["x", "y"]),
        make_report("inst-b", breakdown=["y", "x"], builder_id="builder-b"),
        make_report("inst-c", breakdown=["x", "y"], builder_id="builder-c"),
    ]


# ------------------------------------------------------------------- code


@pytest.fixture
def resolver() -> AnchorResolver:
    return AnchorResolver(
        sources={"cart/total.py": "# @spec: L2-CART.TOTAL-001\ndef total(lines): ...\n"},
        symbols={"cart/total.py::total": "def total(lines) -> Decimal"},
    )


@pytest.fixture
def baseline(spec, resolver) -> dict[str, str]:
    return build_baseline(spec, resolver)


@pytest.fixture
def roles() -> dict[str, Role]:
    return {
        "architect": Role.ARCHITECT,
        "builder": Role.BUILDER,
        "verifier": Role.VERIFIER,
        "judge": Role.JUDGE,
        "leader": Role.LEADER,
    }
