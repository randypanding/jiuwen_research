"""波次状态机：接口冻结窗口 + spec-delta 割集 + 准入事务边界。

转移合法性表驱动；非法转移直接抛错（流程纪律是机械的，不是礼仪）。
每次合法转移发总线事件（wave.*，leader 角色）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class WaveState(str, Enum):
    DRAFT = "draft"            # architect 切割 spec-delta 割集（草稿）
    SEALED = "sealed"          # 接口冻结：InterfaceLock 已获取
    FANOUT = "fanout"          # N 个 builder 并行采样实例
    VERIFY = "verify"          # verifier 跑 H 全族 + S
    CLASSIFY = "classify"      # 六格判定（测量结论归类）
    ADMITTING = "admitting"    # 准入事务 2PC 进行中
    CONVERGING = "converging"  # spec 沉默/分歧 → spec moderator 收敛
    COMMITTED = "committed"    # 实例准入世界（终态，锁释放）
    ABORTED = "aborted"        # 波次放弃（终态，测量结论保留）


#: 合法转移表（驱动一切状态变更）
LEGAL_TRANSITIONS: dict[WaveState, frozenset[WaveState]] = {
    WaveState.DRAFT: frozenset({WaveState.SEALED, WaveState.ABORTED}),
    WaveState.SEALED: frozenset({WaveState.FANOUT, WaveState.ABORTED}),
    WaveState.FANOUT: frozenset({WaveState.VERIFY, WaveState.ABORTED}),
    WaveState.VERIFY: frozenset({WaveState.CLASSIFY, WaveState.ABORTED}),
    WaveState.CLASSIFY: frozenset({WaveState.ADMITTING, WaveState.CONVERGING,
                                   WaveState.ABORTED}),
    WaveState.ADMITTING: frozenset({WaveState.COMMITTED, WaveState.ABORTED}),
    WaveState.CONVERGING: frozenset({WaveState.SEALED, WaveState.ABORTED}),
    WaveState.COMMITTED: frozenset(),
    WaveState.ABORTED: frozenset(),
}


class IllegalTransition(Exception):
    def __init__(self, wave_id: str, frm: WaveState, to: WaveState):
        self.wave_id, self.frm, self.to = wave_id, frm, to
        legal = sorted(s.value for s in LEGAL_TRANSITIONS[frm])
        super().__init__(
            f"wave {wave_id}: illegal transition {frm.value} -> {to.value} "
            f"(legal: {legal})")


EVENT_BY_TRANSITION = {
    (WaveState.DRAFT, WaveState.SEALED): "wave.sealed",
    (WaveState.SEALED, WaveState.FANOUT): "wave.fanout",
    (WaveState.FANOUT, WaveState.VERIFY): "wave.verify",
    (WaveState.VERIFY, WaveState.CLASSIFY): "wave.classify",
    (WaveState.CLASSIFY, WaveState.ADMITTING): "wave.admitting",
    (WaveState.CLASSIFY, WaveState.CONVERGING): "wave.converging",
    (WaveState.ADMITTING, WaveState.COMMITTED): "wave.committed",
    (WaveState.CONVERGING, WaveState.SEALED): "wave.resealed",
}


@dataclass
class WaveRecord:
    wave_id: str
    domain: str
    state: WaveState = WaveState.DRAFT
    spec_delta_id: str = ""
    fanout_n: int = 0
    history: list[tuple[str, str]] = field(default_factory=list)  # (from, to)

    def to_dict(self) -> dict:
        return {
            "wave_id": self.wave_id, "domain": self.domain,
            "state": self.state.value, "spec_delta_id": self.spec_delta_id,
            "fanout_n": self.fanout_n,
            "history": [list(h) for h in self.history],
        }


class WaveTracker:
    """波次状态机跟踪器。on_transition 回调用于发总线事件。"""

    def __init__(self, on_transition: Optional[Callable[[WaveRecord, str], None]] = None):
        self.waves: dict[str, WaveRecord] = {}
        self.on_transition = on_transition

    def create(self, wave_id: str, domain: str, spec_delta_id: str = "") -> WaveRecord:
        rec = WaveRecord(wave_id=wave_id, domain=domain, spec_delta_id=spec_delta_id)
        self.waves[wave_id] = rec
        return rec

    def transition(self, wave_id: str, to: WaveState) -> WaveRecord:
        rec = self.waves[wave_id]
        frm = rec.state
        if to not in LEGAL_TRANSITIONS[frm]:
            raise IllegalTransition(wave_id, frm, to)
        rec.state = to
        rec.history.append((frm.value, to.value))
        event = EVENT_BY_TRANSITION.get((frm, to))
        if event and self.on_transition:
            self.on_transition(rec, event)
        return rec

    def get(self, wave_id: str) -> WaveRecord:
        return self.waves[wave_id]
