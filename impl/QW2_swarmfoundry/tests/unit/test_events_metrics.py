from swarmfoundry.schema.events import (
    OBS_CLOSED,
    OBS_DIVERGENCE,
    OBS_INSUFFICIENT_INSTANCES,
    OBS_SILENCE,
    OBS_SPEC_ORACLE_CONFLICT,
    OBS_TIER_INSUFFICIENT,
    classify_measurement,
)
from swarmfoundry.schema.metrics import (
    DOWNGRADE_ESCAPE_DEFECT,
    DOWNGRADE_JUDGE_KAPPA,
    HealthMetrics,
    Thresholds,
    evaluate_downgrades,
)


def test_classification_table():
    assert classify_measurement(3, 3, True) == OBS_CLOSED
    assert classify_measurement(3, 3, False) == OBS_SILENCE
    assert classify_measurement(3, 2, True) == OBS_DIVERGENCE
    assert classify_measurement(3, 0, True) == OBS_TIER_INSUFFICIENT
    assert classify_measurement(3, 0, True, upgraded_tier_failed=True) == OBS_SPEC_ORACLE_CONFLICT
    assert classify_measurement(2, 1, True) == OBS_INSUFFICIENT_INSTANCES


def test_downgrade_triggers():
    m = HealthMetrics(
        window="w",
        closure_rate=0.2,
        spec_entropy=1.0,
        witness_coverage=0.5,
        unverifiable_clauses=4,
        escape_defect_rate=0.1,
        drift_alerts=1,
        drift_fix_latency_h=1.0,
        judge_kappa=0.3,
        judge_abstain_rate=0.4,
        rework_rate=0.5,
        unit_admission_cost=2000.0,
    )
    triggers = evaluate_downgrades(m, Thresholds())
    assert DOWNGRADE_ESCAPE_DEFECT in triggers
    assert DOWNGRADE_JUDGE_KAPPA in triggers
