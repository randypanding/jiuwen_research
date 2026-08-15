"""测量层：实例作为测量仪器（structure.md §6）。

- 自适应 fan-out：N 由不确定度 U 驱动，不是常量（G5 的解）
- 六格判定：把 N 份实例的通过分布 + 差分结论映射为 spec 状态类别
- 健康度：spec 闭合度/熵/判据覆盖率/返工率（降级触发的数据面）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------- 自适应 fan-out ----------------
@dataclass
class FanoutConfig:
    # U = w_rework*rework + w_novelty*novelty + w_risk*risk，各输入 [0,1]
    w_rework: float = 0.4
    w_novelty: float = 0.3
    w_risk: float = 0.3
    n_low: int = 1        # U < u_low → N=n_low（常规 R0 单实例）
    n_mid: int = 3        # u_low <= U < u_high → N=n_mid
    n_high: int = 6       # U >= u_high → N=n_high
    n_cap: int = 8        # 硬顶（同质扩 N 有信息论上限：2 异构 ≈ 16 同质）
    u_low: float = 0.3
    u_high: float = 0.7
    early_stop_k: int = 2  # 前 k 个实例全过同一 oracle 组即收敛（不跑满 N）


def risk_from_r_level(r: str) -> float:
    return {"R0": 0.1, "R1": 0.5, "R2": 0.8, "R3": 1.0}.get(r, 0.5)


@dataclass
class FanoutDecision:
    n: int
    uncertainty: float
    breakdown: dict = field(default_factory=dict)
    early_stop_enabled: bool = True


def compute_fanout(rework_rate: float, novelty: float, r_level: str,
                   cfg: Optional[FanoutConfig] = None) -> FanoutDecision:
    """N 自适应：不确定度触发测量，而非常量 fan-out。

    R3 例外：冻结制品禁止 fan-out 重采样（INV11）——N 恒为 1，
    测量走黄金比对/统计通道，不走多实例差分。
    """
    cfg = cfg or FanoutConfig()
    rework_rate = min(max(rework_rate, 0.0), 1.0)
    novelty = min(max(novelty, 0.0), 1.0)
    risk = risk_from_r_level(r_level)
    u = cfg.w_rework * rework_rate + cfg.w_novelty * novelty + cfg.w_risk * risk
    if r_level == "R3":
        return FanoutDecision(
            n=1, uncertainty=round(u, 4),
            breakdown={"rework": rework_rate, "novelty": novelty, "risk": risk,
                       "note": "R3: fanout forbidden (INV11); golden/statistical channel"},
            early_stop_enabled=False,
        )
    if u < cfg.u_low:
        n = cfg.n_low
    elif u < cfg.u_high:
        n = cfg.n_mid
    else:
        n = cfg.n_high
    # 顺序依赖强 / 工具重度任务：调用方应传低 novelty 并自行禁用早停
    early_stop = True
    return FanoutDecision(
        n=min(n, cfg.n_cap), uncertainty=round(u, 4),
        breakdown={"rework": rework_rate, "novelty": novelty, "risk": risk},
        early_stop_enabled=early_stop,
    )


def should_early_stop(passed_sequence: list[bool], cfg: Optional[FanoutConfig] = None) -> bool:
    """前 k 个实例全过 → 早停收敛（省 token；oracle 一致性优先）。"""
    cfg = cfg or FanoutConfig()
    k = cfg.early_stop_k
    if len(passed_sequence) < k:
        return False
    return all(passed_sequence[:k])


# ---------------- 六格判定 ----------------
class MeasurementClass(str, Enum):
    CLOSED = "closed"                      # 全通过 + 差分为空：spec 相对 oracle 已闭合
    SILENCE = "silence"                    # 全通过 + 行为差分：spec 的沉默
    AMBIGUITY = "ambiguity"                # 部分通过部分失败：spec 分歧
    UNDERSPECIFIED = "underspecified"      # 全失败→升档成功：对当前档位不可解
    SPEC_ORACLE_CONFLICT = "spec_oracle_conflict"  # 全失败→升档仍失败：规范级事件
    INSUFFICIENT = "insufficient"          # N<3 且有失败：补采样


@dataclass
class ClassifyInput:
    instance_passed: list[bool]            # 每个实例的门禁通过与否
    diff_conclusion: str                   # equivalent | difference_found | inconclusive | na
    n: int                                  # 实际实例数
    upgraded_retry_passed: Optional[bool] = None  # 全失败后升档重试结果


def classify(inp: ClassifyInput) -> MeasurementClass:
    """六格判定表（structure.md §6 的机械实现）。

    处置归属：
      CLOSED → 选实例准入（admission pipeline A）
      SILENCE / AMBIGUITY → spec moderator（pipeline B 收敛 spec）
      UNDERSPECIFIED → spec 澄清 + 记录档位需求
      SPEC_ORACLE_CONFLICT → spec steward + architect 会诊（规范级事件）
      INSUFFICIENT → 补生成至 >=3
    """
    if not inp.instance_passed:
        return MeasurementClass.INSUFFICIENT
    n_pass = sum(inp.instance_passed)
    all_pass = n_pass == len(inp.instance_passed)
    all_fail = n_pass == 0

    if all_fail:
        if inp.upgraded_retry_passed is None:
            if inp.n < 3:
                return MeasurementClass.INSUFFICIENT
            return MeasurementClass.AMBIGUITY  # 信息不足以区分 4/5，先按分歧处置
        if inp.upgraded_retry_passed:
            return MeasurementClass.UNDERSPECIFIED
        return MeasurementClass.SPEC_ORACLE_CONFLICT

    if not all_pass:
        if inp.n < 3:
            return MeasurementClass.INSUFFICIENT
        return MeasurementClass.AMBIGUITY

    # 全通过：看差分
    if inp.diff_conclusion == "difference_found":
        return MeasurementClass.SILENCE
    if inp.diff_conclusion == "inconclusive":
        return MeasurementClass.INSUFFICIENT  # 非确定性未消除，测量未完成
    return MeasurementClass.CLOSED


# ---------------- 健康度 ----------------
@dataclass
class HealthReport:
    spec_closure: float = 0.0        # CLOSED 占比
    spec_entropy: float = 0.0        # 单位 delta 的沉默+分歧事件数
    criterion_coverage: float = 0.0  # bound L1/L2 条款占比
    rework_rate: float = 0.0         # 失败实例占比（fan-out U 的反馈输入）
    insufficient_rate: float = 0.0
    escape_rate: float = 0.0         # 过 H∧S 后被证伪（外部输入）

    def to_dict(self) -> dict:
        return {
            "spec_closure": round(self.spec_closure, 4),
            "spec_entropy": round(self.spec_entropy, 4),
            "criterion_coverage": round(self.criterion_coverage, 4),
            "rework_rate": round(self.rework_rate, 4),
            "insufficient_rate": round(self.insufficient_rate, 4),
            "escape_rate": round(self.escape_rate, 4),
        }


def compute_health(measurements: list, bound_ratio: float,
                   escape_events: int = 0,
                   admitted_count: Optional[int] = None) -> HealthReport:
    """measurements: MeasurementRecord 列表（含被弃实例，INV2 保证保留）。

    事件计数按 (spec_delta_id, classification) 去重：一次波次的沉默/分歧
    是一个事件，不随实例数放大。
    """
    total = len(measurements)
    if total == 0:
        return HealthReport(criterion_coverage=bound_ratio)
    events: set[tuple[str, str]] = set()
    for m in measurements:
        events.add((m.spec_delta_id, m.classification))
    closed = sum(1 for d, c in events if c == "closed")
    silence = sum(1 for d, c in events if c == "silence")
    ambiguity = sum(1 for d, c in events if c == "ambiguity")
    insufficient_records = sum(1 for m in measurements if m.classification == "insufficient")
    passed = sum(1 for m in measurements if m.passed)
    n_deltas = max(len({m.spec_delta_id for m in measurements}), 1)
    admitted = admitted_count if admitted_count is not None else closed
    return HealthReport(
        spec_closure=closed / max(closed + silence + ambiguity, 1),
        spec_entropy=(silence + ambiguity) / n_deltas,
        criterion_coverage=bound_ratio,
        rework_rate=(total - passed) / total,
        insufficient_rate=insufficient_records / total,
        escape_rate=(escape_events / admitted) if admitted else 0.0,
    )


# ---------------- 降级触发（structure.md §13）----------------
DEGRADATION_RULES = [
    # (指标, 阈值方向, 阈值, 动作)
    ("escape_rate", ">", 0.05, "oracle 不可信 → 回退阶段，人类 L2 之外额外确认"),
    ("spec_entropy", ">", 2.0, "漂移/分歧风暴 → 冻结 fan-out，转 B 标定流水线"),
    ("rework_rate", ">", 0.5, "单位准入成本超预算 → 降低 N、缩小再生单元、提高档位门槛"),
]


def check_degradation(report: HealthReport) -> list[str]:
    """降级永远是回退阶段，不是改判据。返回触发的动作清单。"""
    triggered = []
    d = report.to_dict()
    for metric, op, threshold, action in DEGRADATION_RULES:
        val = d.get(metric, 0.0)
        if op == ">" and val > threshold:
            triggered.append(f"{metric}={val} > {threshold}: {action}")
    return triggered
