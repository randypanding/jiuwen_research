"""宪法：范式级不变量（structure.md §14）。

自然语言条款固定化，同时给出可机械化校验的投影。任何下层（spec/oracle/实例/世界）
与宪法冲突时改下层；宪法在会话内不可变，变更只能走 RuleChangeProposal → 人类批准
→ 新 session 装载（见 proposal.py）。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Invariant:
    inv_id: str
    text: str
    machine_checkable: bool  # 是否有本包内的机械校验器


INVARIANTS: tuple[Invariant, ...] = (
    Invariant("INV1", "spec 是唯一真值。代码与运行世界的现状均不构成真值，只构成约束；约束必须写回 spec 才生效。", False),
    Invariant("INV2", "代码是 spec 的采样实例。实例可以被丢弃，被丢弃的实例仍须留下其测量结论。", True),
    Invariant("INV3", "任何门禁必须包含机械见证。无机械见证的规范条款只能否决，不能放行。", True),
    Invariant("INV4", "硬门禁不通过，任何软性判断不得放行；硬门禁通过，软性判断有权否决。", True),
    Invariant("INV5", "生成者与判别者不得为同一主体，且判别所依赖的判据不得对生成者可见。", True),
    Invariant("INV6", "判别者与判据在一次会话内不得自我改变。改变只能经提案与人类批准，并自下一会话生效。", True),
    Invariant("INV7", "人类只对业务意图与开发契约行使权力。实现层不接受也不请求人类裁决。", False),
    Invariant("INV8", "例外不由现场决定。例外一旦产生后果，作为案例进入规则变更提案。", False),
    Invariant("INV9", "多实例行为差异必须被解释：或收敛为规范条款，或显式登记为允许的自由度。不得默认忽略。", True),
    Invariant("INV10", "spec 与代码不一致默认判为缺陷并阻断，除非该制品已被 spec 显式声明为锚定或冻结。", True),
    Invariant("INV11", "不可再生与逐行语义敏感的制品禁止丢弃与重采样，只允许前向演进。", True),
    Invariant("INV12", "准入必须是原子的、可回滚的，并附带完整证据收据。", True),
    Invariant("INV13", "可丢弃主体不得写入长期记忆。记忆写入须由判别侧裁定。", True),
    Invariant("INV14", "判别方的能力档位不得低于生成方。", True),
    Invariant("INV15", "当判据不可信时，正确动作是降低自治级别，而非放宽判据。", True),
)


class ConstitutionViolation(Exception):
    """违反宪法不变量。携带 inv_id 供证据收据引用。"""

    def __init__(self, inv_id: str, detail: str):
        self.inv_id = inv_id
        self.detail = detail
        super().__init__(f"[{inv_id}] {detail}")


INVARIANT_BY_ID = {inv.inv_id: inv for inv in INVARIANTS}


def assert_invariant(inv_id: str, ok: bool, detail: str) -> None:
    """机械校验辅助：ok 为 False 时抛 ConstitutionViolation。"""
    if not ok:
        raise ConstitutionViolation(inv_id, detail)
