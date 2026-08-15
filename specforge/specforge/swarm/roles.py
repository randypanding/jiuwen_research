"""Role definitions + model tier table (PDR-001 section 10).

12 roles, each mapped to: openJiuwen carrier + tier + isolation obligations.
The wiring map below is normative for WP14 (see PLAN.md section 6).
"""
from __future__ import annotations

from dataclasses import dataclass, field

TIER_TABLE: dict[str, str] = {
    "cartographer": "RU-L",     # weak tier, cache-friendly, as-tool
    "builder": "RU-M",          # may escalate to RU-H after oracle failure (<=2 per task)
    "architect": "RU-H",        # never cascade-probe (no cheap validation signal)
    "verifier-judge": "RU-H",   # judge tier >= builder tier (constitution #14)
    "spec-moderator": "RU-H",
    "spec-steward": "RU-H",
    "leader": "RU-M",
    "critic": "RU-M",
    "reconciler": "RU-L",
    "refactor": "RU-M",
    "moderator": "RU-L",
    "deep-agent": "RU-H",
}

ESCALATION_POLICY = {
    "builder": {"to": "RU-H", "max_escalations_per_task": 2,
                "trigger": "oracle failure or repeated compile errors"},
    "cartographer": {"to": "RU-M", "max_escalations_per_task": 1,
                     "trigger": "consecutive retrieval misses"},
}

SESSION_FREEZE_ROLES = ("leader", "spec-moderator", "spec-steward")
# judges and orchestrators must NOT self-evolve within a session (constitution #6)


@dataclass
class RoleSpec:
    name: str
    carrier: str                 # openJiuwen carrier (class + config sketch)
    team: str                    # persistent-team name or "wave-temporary"
    isolation: list[str] = field(default_factory=list)


ROLE_MAP: dict[str, RoleSpec] = {
    "leader": RoleSpec(
        "leader",
        "TeamAgentSpec(agents={'leader': DeepAgentSpec}, lifecycle='persistent', dispatch_mode='scheduled')",
        "governance",
        ["不判别、不写 spec", "session 内不自演进"]),
    "architect": RoleSpec(
        "architect",
        "create_deep_agent(enable_task_loop=True, subagents=[...], model_selection={RU-H})",
        "governance",
        ["持有 holdout 清单(仅 ID)", "不进生成团队"]),
    "builder": RoleSpec(
        "builder",
        "TeamAgentSpec(lifecycle='temporary') 成员 + MemberMemoryToolkit(read_only=True)",
        "wave-temporary",
        ["不见 holdout", "不写记忆", "不参与判别", "种子平台注入"]),
    "verifier": RoleSpec(
        "verifier",
        "Workflow: H1..H8 为 ToolComponent 节点, add_connection([h1..h8], 'join') + wait_for_all",
        "governance",
        ["确定性工作流", "不写判据不改 spec"]),
    "spec-moderator": RoleSpec(
        "spec-moderator", "持久 agent, context_id='spec_moderator'", "governance",
        ["与 leader/architect 上下文隔离", "session 内冻结"]),
    "spec-steward": RoleSpec(
        "spec-steward", "持久 agent, context_id='spec_steward'", "governance",
        ["与 leader 分离", "session 内冻结"]),
    "reconciler": RoleSpec(
        "reconciler", "agent + 定时心跳, 执行 H7 策略侧", "governance",
        ["只上报与阻断，不自行改 spec"]),
    "cartographer": RoleSpec(
        "cartographer",
        "agent-as-tool: 父 agent subagents=[SubAgentSpec(name='cartographer')] -> TaskTool",
        "shared",
        ["无准入权", "返回 schema JSON(file:line+证据+置信度)"]),
    "critic": RoleSpec(
        "critic", "独立 DeepAgent, 产 holdout 场景提案", "governance",
        ["不准入", "产出进 oracle 需 steward 批准"]),
    "refactor": RoleSpec(
        "refactor", "独立后处理波次(同 wave 管道)", "wave-temporary",
        ["不得改变契约面，须过 H4/H5"]),
    "moderator": RoleSpec(
        "moderator", "agent + 定时, 可读性治理", "governance",
        ["产出为 spec-delta 或 refactor 请求"]),
    "deep-agent": RoleSpec(
        "deep-agent", "Rail + 提案器(参考 SkillEvolutionRail auto_save=False)", "governance",
        ["只提案不生效", "生效需人类批准且限于新 session"]),
}


def role(name: str) -> RoleSpec:
    return ROLE_MAP[name]
