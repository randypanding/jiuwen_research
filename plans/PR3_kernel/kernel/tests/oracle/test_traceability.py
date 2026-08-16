"""H7: spec <-> code drift.

The funnel is hash -> structural -> semantic, and the ordering is the whole
design: cheap checks run on every commit, expensive ones only on candidates,
and the semantic layer is advisory because a false "drifted" verdict from a
model would train everyone to ignore the gate.

The other load-bearing decision under test here: the drift baseline is *not*
stored on the anchor. If it were, one commit could edit both the code and the
record of what the code used to be, and drift would be undetectable by
construction.
"""

from __future__ import annotations

import pytest

from swarmkernel.contracts.spec import Anchor, ClauseStatus, SpecDocument
from swarmkernel.oracle.traceability import (
    AnchorResolver,
    DriftKind,
    Exemption,
    TraceabilityEngine,
    anchors_from_source,
    build_baseline,
)

TODAY = "2026-08-15"


def kinds(findings) -> set[DriftKind]:
    return {f.kind for f in findings}


def blocking(findings):
    return [f for f in findings if f.blocking]


# ------------------------------------------------------------------ clean


def test_a_consistent_spec_and_codebase_is_clean(spec, resolver, baseline):
    engine = TraceabilityEngine(resolver=resolver, baseline=baseline, today=TODAY)
    assert blocking(engine.check(spec)) == []


def test_coverage_is_one_when_every_anchor_resolves(spec, resolver, baseline):
    engine = TraceabilityEngine(resolver=resolver, baseline=baseline, today=TODAY)
    assert engine.coverage(spec) == 1.0


# --------------------------------------------------------------- orphaned


def test_a_clause_with_no_anchor_is_reported(spec, resolver, baseline):
    orphan = spec.clauses[0].model_copy(update={"id": "L2-CART.ORPHAN-009", "anchors": []})
    doc = spec.model_copy(update={"clauses": [*spec.clauses, orphan]})
    engine = TraceabilityEngine(resolver=resolver, baseline=baseline, today=TODAY)
    findings = engine.check(doc)
    assert DriftKind.ORPHAN_CLAUSE in kinds(findings)


def test_an_orphan_clause_warns_but_does_not_block(spec, resolver, baseline):
    """A contract written before the code exists is normal during a wave; it
    becomes a problem only if it is still unanchored at admission, which is a
    separate H7 policy on the unit, not on every intermediate commit."""

    orphan = spec.clauses[0].model_copy(update={"id": "L2-CART.ORPHAN-009", "anchors": []})
    doc = spec.model_copy(update={"clauses": [orphan]})
    engine = TraceabilityEngine(resolver=resolver, baseline=baseline, today=TODAY)
    assert blocking(engine.check(doc)) == []


# --------------------------------------------------------------- dangling


def test_an_anchor_to_a_deleted_file_blocks(spec, baseline):
    engine = TraceabilityEngine(
        resolver=AnchorResolver(sources={}), baseline=baseline, today=TODAY
    )
    findings = engine.check(spec)
    assert DriftKind.DANGLING_ANCHOR in kinds(findings)
    assert blocking(findings)


def test_an_anchor_to_a_renamed_symbol_blocks(spec, baseline):
    resolver = AnchorResolver(
        sources={"cart/total.py": "def grand_total(lines): ..."},
        symbols={"cart/total.py::grand_total": "def grand_total(lines) -> Decimal"},
    )
    engine = TraceabilityEngine(resolver=resolver, baseline=baseline, today=TODAY)
    findings = engine.check(spec)
    assert DriftKind.DANGLING_ANCHOR in kinds(findings)


# ------------------------------------------------------- stale / structural


def test_changed_code_behind_an_unchanged_clause_blocks(spec, baseline):
    """The core H7 event: the implementation moved, the contract did not."""

    drifted = AnchorResolver(
        sources={"cart/total.py": "# @spec: L2-CART.TOTAL-001\ndef total(lines, discount): ...\n"},
        symbols={"cart/total.py::total": "def total(lines, discount) -> Decimal"},
    )
    engine = TraceabilityEngine(resolver=drifted, baseline=baseline, today=TODAY)
    findings = engine.check(spec)
    assert DriftKind.STRUCTURAL_DRIFT in kinds(findings)
    assert blocking(findings)


def test_a_module_level_anchor_reports_stale_rather_than_structural(spec, baseline):
    drifted = AnchorResolver(
        sources={"cart/total.py": "# changed\ndef total(lines): ...\n"},
        symbols={"cart/total.py::total": "def total(lines) -> Decimal"},
    )
    engine = TraceabilityEngine(resolver=drifted, baseline=baseline, today=TODAY)
    findings = engine.check(spec)
    assert DriftKind.STALE_ANCHOR in kinds(findings)


def test_the_baseline_is_not_owned_by_the_anchor():
    """Structural guarantee, not a convention: ``Anchor`` has no digest field,
    so a builder cannot update the expectation in the same commit as the code.
    """

    assert "digest" not in Anchor.model_fields
    assert "baseline" not in Anchor.model_fields


def test_a_never_snapshotted_anchor_is_not_silently_clean(spec, resolver):
    """No baseline entry means "we have never checked", which must not read as
    "we checked and it was fine". It is reported as un-checkable."""

    engine = TraceabilityEngine(resolver=resolver, baseline={}, today=TODAY)
    findings = engine.check(spec)
    assert DriftKind.STALE_ANCHOR not in kinds(findings)
    assert DriftKind.STRUCTURAL_DRIFT not in kinds(findings)


def test_revising_the_clause_clears_the_drift(spec, resolver):
    """Rebaselining is legal and explicit: the new baseline is computed from the
    new code *and* recorded against the new clause revision."""

    drifted = AnchorResolver(
        sources={"cart/total.py": "def total(lines, discount): ...\n"},
        symbols={"cart/total.py::total": "def total(lines, discount) -> Decimal"},
    )
    fresh = build_baseline(spec, drifted)
    engine = TraceabilityEngine(resolver=drifted, baseline=fresh, today=TODAY)
    assert blocking(engine.check(spec)) == []


# ------------------------------------------------------- unanchored code


def test_contract_bearing_code_with_no_clause_is_reported(spec, resolver, baseline):
    engine = TraceabilityEngine(
        resolver=resolver,
        baseline=baseline,
        today=TODAY,
        contract_bearing_symbols={"cart/api.py::checkout"},
    )
    findings = engine.check(spec)
    assert DriftKind.UNANCHORED_CODE in kinds(findings)


def test_unanchored_code_warns_but_does_not_block(spec, resolver, baseline):
    """Blocking here would stop every commit that adds a public helper before
    its clause lands, so this warns and is measured as a trend instead."""

    engine = TraceabilityEngine(
        resolver=resolver,
        baseline=baseline,
        today=TODAY,
        contract_bearing_symbols={"cart/api.py::checkout"},
    )
    assert blocking(engine.check(spec)) == []


# ------------------------------------------------------------- semantic


def test_semantic_drift_is_advisory_only(spec, resolver, baseline):
    engine = TraceabilityEngine(
        resolver=resolver,
        baseline=baseline,
        today=TODAY,
        semantic_check=lambda clause, digest: False,
    )
    findings = engine.check(spec)
    assert DriftKind.SEMANTIC_DRIFT in kinds(findings)
    assert blocking(findings) == []


def test_no_semantic_checker_means_no_semantic_findings(spec, resolver, baseline):
    engine = TraceabilityEngine(resolver=resolver, baseline=baseline, today=TODAY)
    assert DriftKind.SEMANTIC_DRIFT not in kinds(engine.check(spec))


# ------------------------------------------------------------ exemptions


def test_an_active_exemption_downgrades_a_blocking_finding(spec, baseline):
    key = f"L2-CART.TOTAL-001@{Anchor(path='cart/total.py', symbol='total').key()}"
    engine = TraceabilityEngine(
        resolver=AnchorResolver(sources={}),
        baseline=baseline,
        today=TODAY,
        exemptions=[
            Exemption(
                target=key,
                kind=DriftKind.DANGLING_ANCHOR,
                owner="alice",
                expires_on="2026-12-31",
                reason="module being split; anchor lands next wave",
            )
        ],
    )
    findings = [f for f in engine.check(spec) if f.target == key]
    assert findings and all(f.exempted for f in findings)
    assert not any(f.blocking for f in findings)


def test_an_expired_exemption_stops_protecting(spec, baseline):
    key = f"L2-CART.TOTAL-001@{Anchor(path='cart/total.py', symbol='total').key()}"
    engine = TraceabilityEngine(
        resolver=AnchorResolver(sources={}),
        baseline=baseline,
        today=TODAY,
        exemptions=[
            Exemption(
                target=key,
                kind=DriftKind.DANGLING_ANCHOR,
                owner="alice",
                expires_on="2026-01-01",
                reason="forgotten",
            )
        ],
    )
    assert blocking(engine.check(spec))
    assert engine.expired_exemptions()


def test_an_exemption_only_covers_its_own_kind(spec, baseline):
    key = f"L2-CART.TOTAL-001@{Anchor(path='cart/total.py', symbol='total').key()}"
    engine = TraceabilityEngine(
        resolver=AnchorResolver(sources={}),
        baseline=baseline,
        today=TODAY,
        exemptions=[
            Exemption(
                target=key,
                kind=DriftKind.STRUCTURAL_DRIFT,
                owner="alice",
                expires_on="2026-12-31",
                reason="wrong kind",
            )
        ],
    )
    assert blocking(engine.check(spec))


def test_an_exemption_needs_an_owner_and_an_expiry():
    """Enforced by the type: a permanent, unowned exemption is how gates die."""

    with pytest.raises(TypeError):
        Exemption(target="x", kind=DriftKind.ORPHAN_CLAUSE)  # type: ignore[call-arg]


# ------------------------------------------------------- deprecated clauses


def test_deprecated_clauses_are_not_checked(spec, resolver, baseline):
    dead = spec.clauses[0].model_copy(
        update={
            "status": ClauseStatus.DEPRECATED,
            "anchors": [],
            "deprecated_in": "1.3.0",
        }
    )
    doc = SpecDocument(
        spec_id=spec.spec_id,
        version=spec.version,
        domain=spec.domain,
        clauses=[dead],
        dont_care=spec.dont_care,
    )
    engine = TraceabilityEngine(resolver=resolver, baseline=baseline, today=TODAY)
    assert engine.check(doc) == []


# ---------------------------------------------------- source-side anchors


def test_source_markers_are_discoverable(resolver):
    assert resolver.declared_clause_ids() == {"L2-CART.TOTAL-001"}


def test_anchors_from_source_reports_path_and_clause():
    found = anchors_from_source(
        [("cart/total.py", "# @spec: L2-CART.TOTAL-001\ndef total(): ...")]
    )
    assert found == [("L2-CART.TOTAL-001", "cart/total.py")]


def test_drift_can_point_in_either_direction(spec, resolver, baseline):
    """The code claims a clause the spec does not have: also drift, and the
    direction humans usually forget to check."""

    lying = AnchorResolver(
        sources={"cart/total.py": "# @spec: L2-CART.GHOST-999\ndef total(lines): ...\n"},
        symbols={"cart/total.py::total": "def total(lines) -> Decimal"},
    )
    declared = lying.declared_clause_ids()
    spec_ids = {c.id for c in spec.clauses}
    assert declared - spec_ids == {"L2-CART.GHOST-999"}
