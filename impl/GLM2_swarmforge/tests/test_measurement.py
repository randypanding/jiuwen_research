"""测量层测试：自适应 fan-out、早停、六格判定全覆盖、健康度、降级触发。"""
import pytest

from swarmforge.measurement import (
    ClassifyInput,
    FanoutConfig,
    MeasurementClass,
    classify,
    compute_fanout,
    compute_health,
    check_degradation,
    should_early_stop,
)
from swarmforge.admission import MeasurementRecord


class TestFanout:
    def test_low_uncertainty_n1(self):
        d = compute_fanout(rework_rate=0.0, novelty=0.0, r_level="R0")
        assert d.n == 1

    def test_mid_uncertainty_n3(self):
        d = compute_fanout(rework_rate=0.5, novelty=0.5, r_level="R1")
        # U = .4*.5 + .3*.5 + .3*.5 = 0.5 → mid
        assert d.n == 3

    def test_high_uncertainty_n6_capped(self):
        d = compute_fanout(rework_rate=1.0, novelty=1.0, r_level="R2")
        assert d.n == 6
        assert d.n <= FanoutConfig().n_cap

    def test_r3_forbids_fanout_n1_no_early_stop(self):
        d = compute_fanout(1.0, 1.0, "R3")
        assert d.n == 1 and not d.early_stop_enabled  # INV11：冻结制品禁重采样

    def test_early_stop_rule(self):
        assert should_early_stop([True, True]) is True
        assert should_early_stop([True, False]) is False
        assert should_early_stop([True]) is False  # 样本不足 k


class TestSixCellClassification:
    """六格判定表全覆盖（structure.md §6）。"""

    def test_closed(self):
        assert classify(ClassifyInput(
            instance_passed=[True, True, True], diff_conclusion="equivalent", n=3
        )) == MeasurementClass.CLOSED

    def test_silence(self):
        assert classify(ClassifyInput(
            instance_passed=[True, True], diff_conclusion="difference_found", n=2
        )) == MeasurementClass.SILENCE

    def test_ambiguity(self):
        assert classify(ClassifyInput(
            instance_passed=[True, False, True], diff_conclusion="equivalent", n=3
        )) == MeasurementClass.AMBIGUITY

    def test_underspecified_after_upgrade_success(self):
        assert classify(ClassifyInput(
            instance_passed=[False, False, False], diff_conclusion="na", n=3,
            upgraded_retry_passed=True,
        )) == MeasurementClass.UNDERSPECIFIED

    def test_spec_oracle_conflict(self):
        assert classify(ClassifyInput(
            instance_passed=[False, False, False], diff_conclusion="na", n=3,
            upgraded_retry_passed=False,
        )) == MeasurementClass.SPEC_ORACLE_CONFLICT

    def test_insufficient_samples(self):
        assert classify(ClassifyInput(
            instance_passed=[False], diff_conclusion="na", n=1
        )) == MeasurementClass.INSUFFICIENT

    def test_nondet_inconclusive_is_insufficient(self):
        assert classify(ClassifyInput(
            instance_passed=[True, True], diff_conclusion="inconclusive", n=2
        )) == MeasurementClass.INSUFFICIENT

    def test_empty_is_insufficient(self):
        assert classify(ClassifyInput(
            instance_passed=[], diff_conclusion="na", n=0
        )) == MeasurementClass.INSUFFICIENT


def rec(delta, iid, passed, cls):
    return MeasurementRecord(wave_id="W", spec_delta_id=delta, instance_id=iid,
                             passed=passed, diff_conclusion="equivalent",
                             classification=cls)


class TestHealth:
    def test_metrics_computation(self):
        ms = [
            rec("D1", "I1", True, "closed"), rec("D1", "I2", False, "closed"),
            rec("D1", "I3", False, "closed"),
            rec("D2", "I4", False, "silence"), rec("D2", "I5", False, "silence"),
            rec("D2", "I6", False, "silence"),
        ]
        h = compute_health(ms, bound_ratio=0.8)
        # 事件按 (delta, class) 去重：D1=closed 一个事件，D2=silence 一个事件
        assert h.spec_closure == pytest.approx(0.5)
        assert h.spec_entropy == pytest.approx(1 / 2)   # 1 个沉默事件 / 2 个 delta
        assert h.criterion_coverage == 0.8
        assert h.rework_rate == pytest.approx(5 / 6)

    def test_empty_ledger(self):
        h = compute_health([], bound_ratio=1.0)
        assert h.criterion_coverage == 1.0 and h.spec_closure == 0.0

    def test_degradation_triggers(self):
        ms = [rec("D1", f"I{i}", i == 0, "closed") for i in range(10)]  # 90% rework
        h = compute_health(ms, bound_ratio=1.0)
        triggered = check_degradation(h)
        assert any("rework_rate" in t for t in triggered)

    def test_no_degradation_on_healthy(self):
        ms = [rec("D1", "I1", True, "closed"), rec("D1", "I2", True, "closed"),
              rec("D1", "I3", True, "closed")]
        h = compute_health(ms, bound_ratio=1.0)
        assert check_degradation(h) == []
