"""角色装配：RoleSpec → openjiuwen TeamAgentSpec/DeepAgentSpec 配置片段。

范式的角色约束在此机械校验（constitution 投影）：
- INV13：builder（可丢弃主体）不挂记忆写 rail、不挂 evolution rail
- INV5 ：builder 的 tools 白名单不含 holdout/判据访问面；bus 角色分离
- INV6 ：判别侧角色（verifier/spec_moderator/judge）session 内不挂自演进 rail
- 临时 builder fan-out：lifecycle=TEMPORARY（框架原生语义）+ 显式禁写 rail
  （"不留痕"不是 TEMPORARY 的自动副作用，必须白名单化——实地考察结论）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..constitution import ConstitutionViolation
from .tiers import ModelTier, role_floor

#: 判别侧角色（session 内冻结，不得自演进）
ADJUDICATING_ROLES = frozenset({"verifier", "spec_moderator", "spec_steward", "judge"})

#: 可丢弃主体（不得写长期记忆）
DISCARDABLE_ROLES = frozenset({"builder"})

#: 危险 rail：可丢弃主体与判别侧一律禁挂
MEMORY_WRITE_RAILS = frozenset({
    "swarm.member_skill_evolution",
    "swarm.team_skill_evolution",
    "swarm.team_skill_create",
})
#: 允许 builder 挂的 rail 白名单（jit 审批走 leader，不写盘）
BUILDER_ALLOWED_RAILS = frozenset({
    "core.team.tool",          # 协同工具
    "core.team.policy",        # 系统提示词 section（恒挂载）
    "core.team.workspace",     # 工作区
    "team.permission",         # allow/ask/deny 收紧
})

#: builder 工具白名单（deny-by-default 之外的显式授予）
BUILDER_TOOLS = frozenset({
    "read_file", "write_file", "list_dir", "run_tests",
    "bash(sandboxed)", "search_code", "submit_instance",
})
#: 判据面工具：builder 永不可见（INV5）
VERIFIER_ONLY_TOOLS = frozenset({
    "holdout.read", "rubric.read", "judge.invoke", "golden.verify",
})


@dataclass
class RoleSpec:
    role: str
    bus_role: str                       # 总线权限角色（可与 role 不同，如 judge→verifier）
    lifecycle: str = "temporary"        # temporary | persistent
    model_tier: ModelTier = ModelTier.RU_M
    model_function: str = "generation"  # generation | judgement
    rails: frozenset[str] = frozenset({"core.team.tool", "core.team.policy"})
    tools: frozenset[str] = frozenset()
    memory_writable: bool = False
    sandbox_policy: str = ""            # jiuwenbox policy 文件引用
    max_iterations: int = 15
    # openjiuwen TeamAgentSpec 映射提示（build_team 配置片段的键）
    oa_spec_hints: dict = field(default_factory=dict)


def builder_role(model_tier: ModelTier = ModelTier.RU_M,
                 sandbox_policy: str = "builder-default") -> RoleSpec:
    """临时 builder：即用即散、不写记忆、不见判据。"""
    return RoleSpec(
        role="builder", bus_role="builder", lifecycle="temporary",
        model_tier=model_tier, model_function="generation",
        rails=BUILDER_ALLOWED_RAILS, tools=BUILDER_TOOLS,
        memory_writable=False, sandbox_policy=sandbox_policy,
        oa_spec_hints={"team_mode": "predefined", "spawn_mode": "process",
                       "worktree_isolation": "worktree"},
    )


def verifier_role() -> RoleSpec:
    return RoleSpec(
        role="verifier", bus_role="verifier", lifecycle="persistent",
        model_tier=role_floor("verifier", "judgement"),
        model_function="judgement",
        rails=frozenset({"core.team.tool", "core.team.policy"}),
        tools=VERIFIER_ONLY_TOOLS | {"run_oracle", "diff.execute"},
        memory_writable=False,
    )


def validate_role(spec: RoleSpec) -> None:
    """角色装配的宪法校验（装配期执行，violation 即拒绝上线）。"""
    if spec.role in DISCARDABLE_ROLES:
        if spec.memory_writable:
            raise ConstitutionViolation(
                "INV13", f"discardable role '{spec.role}' must not write long-term memory")
        bad = spec.rails & MEMORY_WRITE_RAILS
        if bad:
            raise ConstitutionViolation(
                "INV13", f"discardable role '{spec.role}' mounts memory-writing rails: {sorted(bad)}")
        leaked = spec.tools & VERIFIER_ONLY_TOOLS
        if leaked:
            raise ConstitutionViolation(
                "INV5", f"builder tools leak verifier-only surface: {sorted(leaked)}")
    if spec.role in ADJUDICATING_ROLES:
        bad = spec.rails & MEMORY_WRITE_RAILS
        if bad:
            raise ConstitutionViolation(
                "INV6", f"adjudicating role '{spec.role}' must be frozen in-session "
                        f"(no evolution rails): {sorted(bad)}")
        if spec.lifecycle != "persistent":
            raise ConstitutionViolation(
                "INV6", f"adjudicating role '{spec.role}' must be persistent within session")


def build_model_pool_entries(tier: ModelTier, models_by_tier: dict) -> list[dict]:
    """生成 openjiuwen TeamAgentSpec.model_pool 配置片段。

    models_by_tier: {"RU-L": [{name, api_base, api_key_env, provider}...], ...}
    返回 [{"model_name":..., "api_base":..., "provider":...}, ...]
    """
    entries = []
    for m in models_by_tier.get(tier.value, []):
        entries.append({
            "model_name": m["name"],
            "api_base": m.get("api_base", ""),
            "api_key_env": m.get("api_key_env", ""),
            "provider": m.get("provider", "openai"),
            "tags": [tier.value],
        })
    return entries


def build_team_spec_fragment(members: list[RoleSpec],
                             models_by_tier: dict) -> dict:
    """生成 openjiuwen build_team 的 members 配置片段（数据，不是执行）。"""
    out = {"predefined_members": []}
    for m in members:
        validate_role(m)
        out["predefined_members"].append({
            "member_name": m.role,
            "display_name": m.role,
            "desc": f"{m.role} ({m.model_tier.value}, {m.lifecycle})",
            "model_name": None,  # 由 model_pool 分配
            "role_type": "TEAMMATE" if m.role != "leader" else "LEADER",
            "options": {
                "lifecycle": m.lifecycle,
                "rails": sorted(m.rails),
                "tools_allowlist": sorted(m.tools),
                "memory_writable": m.memory_writable,
                "sandbox_policy": m.sandbox_policy,
                "model_tier": m.model_tier.value,
                "model_pool_entries": build_model_pool_entries(m.model_tier, models_by_tier),
                "worktree_isolation": m.oa_spec_hints.get("worktree_isolation",
                                                          "worktree" if m.role == "builder" else ""),
                "oa_hints": dict(m.oa_spec_hints),
            },
        })
    return out
