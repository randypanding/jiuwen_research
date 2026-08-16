import pytest

from swarmdev.admission import Outcome
from swarmdev.contracts import EvidenceReceipt, GateOutcome, RLevel
from swarmdev.contracts.receipt import GateStatus
from swarmdev.metrics import HealthMetrics


def _receipt(admitted=True):
    outs = [GateOutcome(gate_id=f"H{i}", status=GateStatus.PASS) for i in range(1, 9)]
    return EvidenceReceipt(receipt_id="RCPT-1", wave_id="W-1", spec_id="s",
                           spec_delta_ref="d", r_level=RLevel.R0,
                           chosen_instance_id="INST-1", hard_gate_outcomes=outs,
                           admitted=admitted,
                           commit_ref="sha:abc" if admitted else None)


def test_soft_gate_suspended_on_low_kappa():
    m = HealthMetrics()
    for _ in range(3):
        m.record_fanout(Outcome.CLOSED)
    m.record_calibration(0.4)
    snap = m.snapshot()
    assert snap.degradation_triggers == ["soft_gate_suspended"]
    assert snap.judge_kappa == 0.4


def test_reduce_autonomy_on_low_closure():
    m = HealthMetrics()
    m.record_fanout(Outcome.CLOSED)
    m.record_fanout(Outcome.SILENCE)
    m.record_fanout(Outcome.DIVERGENCE)
    snap = m.snapshot()
    assert snap.closure_rate == pytest.approx(1 / 3)
    assert snap.silence_or_divergence_events == 2
    assert snap.degradation_triggers == ["reduce_autonomy"]


def test_freeze_fanout_on_drift_spike():
    m = HealthMetrics()
    for _ in range(3):
        m.record_fanout(Outcome.CLOSED)
    m.record_drift(clean=False, hard_events=5)
    snap = m.snapshot()
    assert snap.drift_hard_events == 5
    assert snap.degradation_triggers == ["freeze_fanout"]


def test_all_green_no_triggers():
    m = HealthMetrics()
    for _ in range(3):
        m.record_fanout(Outcome.CLOSED)
    m.record_receipt(_receipt(True), cost_tokens=1000)
    m.record_receipt(_receipt(True), cost_tokens=3000)
    m.record_drift(clean=True, hard_events=0)
    m.record_calibration(0.9)
    m.set_witness_coverage(1.0)
    snap = m.snapshot()
    assert snap.degradation_triggers == []
    assert snap.closure_rate == 1.0
    assert snap.silence_or_divergence_events == 0
    assert snap.witness_coverage == 1.0
    assert snap.avg_cost_per_admission == 2000.0
    assert snap.judge_kappa == 0.9


def test_empty_metrics_snapshot():
    snap = HealthMetrics().snapshot()
    assert snap.closure_rate == 0.0
    assert snap.avg_cost_per_admission == 0.0
    assert snap.degradation_triggers == []
