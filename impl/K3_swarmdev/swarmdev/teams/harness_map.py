from __future__ import annotations

from swarmdev.contracts import Role

# 角色 -> openJiuwen 承载件绑定表（PDR-001 §11 的工程落位）。
# 每条 binding 的 evidence 指向 agent-core / jiuwenswarm 已检出代码的锚点，
# 供各实施团队按图施工；本表是声明式的，运行时不执行。
HARNESS_BINDINGS: dict[Role, dict] = {
    Role.LEADER: {
        "carrier": "jiuwenswarm TeamManager + agent-core TeamAgent(leader)",
        "lifecycle": "persistent",
        "evidence": [
            "jiuwenswarm/jiuwenswarm/agents/harness/team/team_manager.py:269",
            "agent-core/openjiuwen/agent_teams/agent/team_agent.py:69",
        ],
        "notes": "只编排不判别；team.jiuwen_team.lifecycle=persistent",
    },
    Role.ARCHITECT: {
        "carrier": "agent-core DeepAgent(TaskLoop) + Workflow 嵌套（agentic 过程）",
        "lifecycle": "persistent",
        "evidence": [
            "agent-core/openjiuwen/harness/factory.py:454",
            "agent-core/openjiuwen/core/workflow/workflow.py:98",
        ],
        "notes": "持有 holdout；产出波次计划/DoD/rubric；不在生成团队内",
    },
    Role.BUILDER: {
        "carrier": "jiuwenswarm 临时团队（lifecycle=temporary）+ TaskTool 派生",
        "lifecycle": "temporary",
        "evidence": [
            "jiuwenswarm/jiuwenswarm/resources/config.yaml:1219",
            "jiuwenswarm/jiuwenswarm/agents/harness/team/remote_member_bootstrap.py:118",
        ],
        "notes": "即用即散；auto_extract 对 temporary 关闭；不写记忆、不见 holdout",
    },
    Role.VERIFIER: {
        "carrier": "agent-core WorkflowAgent（确定性流水线，不允许自主跳过门禁）",
        "lifecycle": "persistent",
        "evidence": [
            "agent-core/openjiuwen/core/application/workflow_agent/workflow_agent.py:11",
            "agent-core/openjiuwen/core/workflow/workflow.py:317",
        ],
        "notes": "执行 H1-H8 与 judge workflow；不写判据不改 spec",
    },
    Role.JUDGE: {
        "carrier": "verifier WorkflowAgent 内嵌节点 + IntelliRouter 档位",
        "lifecycle": "stateless-per-call",
        "evidence": [
            "agent-core/openjiuwen/core/foundation/llm/model_clients/intelli_router_model_client.py:96",
        ],
        "notes": "多次采样+集成；判官档位≥builder；输出仅 veto/no_veto/abstain",
    },
    Role.SPEC_MODERATOR: {
        "carrier": "agent-core DeepAgent + TEAM_MEMORY 写权限",
        "lifecycle": "persistent",
        "evidence": [
            "agent-core/openjiuwen/agent_teams/memory/manager.py:340",
        ],
        "notes": "沉默/分歧裁决；实现细节入团队记忆须经其裁定",
    },
    Role.SPEC_STEWARD: {
        "carrier": "agent-core DeepAgent",
        "lifecycle": "persistent",
        "evidence": [],
        "notes": "spec 版本、条款一致性、delta 归档",
    },
    Role.RECONCILER: {
        "carrier": "定时任务（cron）+ DriftDetector CLI",
        "lifecycle": "scheduled",
        "evidence": [
            "swarmdev/swarmdev/drift/detector.py",
        ],
        "notes": "只上报与阻断（DRIFT_ALERT），不自行改 spec",
    },
    Role.CARTOGRAPHER: {
        "carrier": "agent-as-tool（TaskTool 子代理），弱档位",
        "lifecycle": "per-call",
        "evidence": [
            "agent-core/openjiuwen/harness/deep_agent.py:1187",
        ],
        "notes": "返回 file:line+置信度的紧凑 JSON；内部轨迹不进主上下文",
    },
    Role.CRITIC: {
        "carrier": "独立 DeepAgent（红队），产出进 oracle 补强",
        "lifecycle": "on-demand",
        "evidence": [],
        "notes": "不准入；为 holdout 补场景",
    },
    Role.REFACTOR: {
        "carrier": "准入后独立后处理 DeepAgent",
        "lifecycle": "post-admission",
        "evidence": [],
        "notes": "不得改变契约面（H4 快照约束），须过 H4/H5",
    },
    Role.MODERATOR: {
        "carrier": "定时 DeepAgent",
        "lifecycle": "scheduled",
        "evidence": [],
        "notes": "可读性治理，产出为 spec-delta 或 refactor 请求",
    },
    Role.DEEP_AGENT: {
        "carrier": "SkillEvolutionRail(auto_save=False) + EvolutionApprovalRuntime",
        "lifecycle": "persistent",
        "evidence": [
            "agent-core/openjiuwen/harness/rails/evolution/skill_evolution_rail.py:141",
            "agent-core/openjiuwen/harness/rails/evolution/approval_runtime.py:17",
        ],
        "notes": "只提案不生效；人类批准后新 session 生效",
    },
}
