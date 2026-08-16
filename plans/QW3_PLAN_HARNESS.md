# 角色 Harness 接线手册（PLAN_HARNESS.md）

> 目标：把 PDR-001 §10 的 12 个角色逐一落到 openJiuwen 的真实 API 上。所有 API 引用均核对自本仓锁定的 submodule SHA（见 CAPABILITY_MAP.md 头部）。执行 agent 按本文档逐节实现 WP5/WP6。

## 0. 底座事实（先读）

1. 单体构建：`create_deep_agent(model, *, card, tools, mcps, subagents, rails, max_iterations, workspace, skills, backend, sys_operation, language, prompt_mode, ..., enable_security_rail=True, ...)`
   — `agent-core/openjiuwen/harness/factory.py:L454-485`。**rails 传 AgentRail 实例列表；记忆一律经 rails（MemoryRail 等），无独立 memory 参数。**
2. Rail 基类钩子（全部 async，上下文 `AgentCallbackContext`）：`before_invoke / after_invoke / on_user_message / before_model_call / after_model_call / on_model_exception / before_tool_call / after_tool_call / on_tool_exception / before_task_iteration / after_task_iteration`；类属性 `priority`（小先大后按框架排序）
   — `agent-core/openjiuwen/core/single_agent/rail/base.py:L672-820`。DeepAgent 场景继承 `DeepAgentRail`（`agent-core/openjiuwen/harness/rails/base.py:L28`）。
3. 宪法级中止：rail/guardrail 中 `raise AbortError(reason, cause, details)` 终止回调链
   — `agent-core/openjiuwen/core/runner/callback/errors.py:L16-61`；BaseGuardrail 事件驱动 + CRITICAL→AbortError — `agent-core/openjiuwen/core/security/guardrail/guardrail.py:L42-387`。
4. 团队运行时：`TeamRuntimeManager` — `agent-core/openjiuwen/agent_teams/runtime/manager.py:L104`；团队规格 `TeamAgentSpec` — `agent-core/openjiuwen/agent_teams/schema/blueprint.py:L198`；jiuwenswarm 侧装配 `TeamManager.create_team/get_or_create_team/interact` — `jiuwenswarm/jiuwenswarm/agents/harness/team/team_manager.py:L1124-1299`。
5. 团队工具（leader/成员可用的 LLM 工具 id）：`team.create_task / team.view_task / team.update_task / team.claim_task / team.member_complete_task / team.verify_task`（`agent-core/openjiuwen/agent_teams/tools/tool_task.py:L240/450/577/933/1035/1132`）、`team.checkpoint / team.list_checkpoints / team.shutdown_member / team.approve_plan / team.approve_tool / team.list_members`（`tool_member.py:L293/362/639/681/731/785`）。**波次 DAG 的任务语义全部映射到 team.create_task/view_task/update_task/verify_task。**
6. 生命周期：`lifecycle: temporary|persistent`（`jiuwenswarm/resources/config.yaml:L1216-1222`、`config_loader.py:L550`、`remote_member_bootstrap.py:L118-128`）。临时团队成员 shutdown 不做记忆提取（`remote_member_bootstrap.py:L1733-1760`）——**builder 临时 fan-out 不写记忆由此机制天然保证**。
7. 团队记忆：TEAM_MEMORY.md 四分类 `[decision]/[lesson]/[member]/[context]`，全员只读、Leader 提取 agent 唯一写入方（`docs/zh/记忆.md:L216-261`、`config.yaml:L1325-1359`）。治理队用 persistent + 共享记忆；标定队用独立 team_name（记忆按 team_name 隔离）。
8. 检查点：`CheckpointerFactory.create(CheckpointerConfig(type="persistence", conf={"db_type":"sqlite", ...}))`（`agent-core/openjiuwen/core/session/checkpointer/checkpointer.py:L41-125`；jiuwenswarm 用法示例 `server/runtime/agent_adapter/interface_deep.py:L978-1023`）。波次中断/续跑复用 session.rewind 族（`agent_ws_server.py:L4098-4376`）。
9. 扩展装载：jiuwenswarm 扩展 SDK（`extensions/sdk/base.py:L15-128`，清单 `extension.yaml`）与用户 rail 热插拔（`agents/harness/common/plugins/rail_manager.py:L207-235`，路径 `~/.jiuwenswarm/agent/workspace/extensions/<name>/rail.py`）。**本项目全部自定义 rail 走此通道，不改上游。**
10. 上下文引擎：`ContextEngineConfig`（`agent-core/openjiuwen/core/context_engine/schema/config.py:L23-113`），经 `DeepAgentSpec.context_engine_config` 传入。

## 1. 角色 → 形态映射总表

| 角色 | 形态 | 生命周期 | 档位 | rails（自定义） | tools 白名单 | 关键 API |
|---|---|---|---|---|---|---|
| leader（治理） | 持久 DeepAgent，team leader | persistent | RU-M | stream/ask-user（框架自带）+ watchdog_rail | team.* 全族 + opc-health（只读） | TeamManager.create_team |
| leader（交付） | 持久 DeepAgent | persistent（波次内） | RU-M | feedback_redaction_rail | team.create_task/view_task/update_task/verify_task | 同上 |
| architect | agentic 过程：DeepAgent + enable_task_loop + 子代理 | 按需会话 | RU-H | judge_freeze_rail（只读 rubric） | 读 spec/代码 + wave_planner（@tool） | create_deep_agent(subagents=[...]) |
| builder | 临时 spawn 成员 | temporary | RU-M（升 RU-H≤2 次） | builder_isolation_rail + constitution_rail | bash/write/read（jiuwenbox 白名单，无 oracle_store） | team.spawn（member_name/display_name/desc/prompt，见 `remote_member_bootstrap.py:L424-435`） |
| verifier | 确定性工作流进程（非 LLM agent） | 常驻服务 | — | verifier_determinism_rail（守护） | opc-gate* CLI 子进程 | verify_pipeline.py（WP6） |
| spec moderator | 持久 DeepAgent | persistent | RU-H | — | 读差分/测量报告 + spec-delta 起草工具 | 治理队成员 |
| spec steward | 持久 DeepAgent | persistent | RU-M | — | spec 仓读写（L2 变更必生成人类 diff） | 治理队成员 |
| reconciler | 定时进程 + 持久 agent 上报 | persistent | RU-L | — | opc-gate --gate H7 + 巡检 cron | watchdog/心跳 |
| cartographer | agent-as-tool（TaskTool 子 agent） | 每次调用 | RU-L | 无状态 | locate/impact/ci_diagnose 三工具 | SubAgentConfig + TaskTool（`agent-core/openjiuwen/harness/tools/subagent/task_tool.py:L55-246`） |
| critic | 按需 DeepAgent | 临时 | RU-H | — | 红队工具 + 场景起草（入 oracle 不入库需 architect 复核） | MEASUREMENT_REPORT→architect |
| refactor | 按需 DeepAgent（准入后） | 临时 | RU-M | 契约面冻结检查（过 H4/H5 才提交） | 编辑工具 | 同 builder 但见基线 |
| moderator（可读性） | 定时 agent | persistent | RU-L | — | 只读 + spec-delta 请求 | 产出走提案通道 |
| deep agent（演进） | 持久监测 + 提案器 | persistent | RU-M | 只提案不生效（提案通道 WP9） | 读 metrics/案例台账 | proposals schema |

## 2. 团队拓扑（jiuwenswarm 配置）

`swarm/teams/governance.yaml`（映射到 `modes.team.jiuwen_team` 配置段，`config.yaml:L1216-1359`）：

```yaml
team_name: opc-governance
lifecycle: persistent
teammate_mode: build_mode
spawn_mode: inprocess
enable_swarmflow: false          # P0 不启用流程编排
enable_permissions: true
leader:
  member_name: gov-leader
  display_name: 治理队长
agents:
  leader: $agent_leader
predefined_members:
  - member_name: spec-steward
    role_type: teammate
    desc: "spec 仓长期维护：条款一致性、版本、L2 diff 起草"
  - member_name: spec-moderator
    role_type: teammate
    desc: "由测量结论裁决 spec 收敛：沉默→自由度/补条款；分歧→澄清"
  - member_name: reconciler
    role_type: teammate
    desc: "漂移守护：H7 巡检、告警、冻结建议"
memory:
  enabled: true
  scenario: coding
  auto_extract: true             # persistent 队才生效
  shared_memory: true
```

`delivery.yaml`：`team_name: opc-delivery-<wave_id>`，`lifecycle: temporary`，成员按需 `team.spawn`（builder-1..N）。**临时队 auto_extract 自动不触发**（上游机制），满足“可丢弃主体不得写长期记忆”。

`calibration.yaml`：同 delivery 但 `team_name: opc-calibration-*`，独立记忆域；leader 不同人设（标定队长），prompt 显式声明“目标是发现 spec 沉默/分歧，全部丢弃代码”。

## 3. 波次 DAG 协议（team.* 使用契约）

| 步骤 | 工具 | 关键字段约定 |
|---|---|---|
| 波次立项 | leader 写 `waves/<wave_id>/manifest.json`（WaveManifest） | 与 bus 的 C2 envelope 哈希一致 |
| 任务切分 | `team.create_task` | task 描述必须含：contract_id、spec_delta_ref、bundle_hash、R 级、返工预算、验收=门禁集合；**禁止包含场景输入/期望** |
| 任务领取/进度 | `team.claim_task` / `team.update_task` | builder 进度只报百分比与阻塞类别，不报实现细节给 leader 以外角色 |
| 提交 | builder → `team.member_complete_task` + INSTANCE_SUBMIT envelope | 附 opc_submission.json（契约哈希） |
| 判别 | verifier 外部流程（非 team 工具） | GateReport 归档 |
| 验收 | leader `team.verify_task` | 仅当 AdmissionVerdict.admitted 才通过；否则 update_task 返工（反馈经 feedback_redaction_rail 过滤） |
| 复盘 | `team.view_task` 汇总 | 丢弃实例测量结论入 MEASUREMENT_REPORT |

## 4. rails 实现规格（WP5 逐个交付）

所有 rail：继承 `DeepAgentRail`，放 `swarm/rails/<name>/rail.py` + `extension.yaml`（经 rail_manager 热插拔或启动装配），priority 约定：constitution=5（最先）、builder_isolation=10、judge_freeze=20、verifier_determinism=30、feedback_redaction=60（晚于常规提示注入）、watchdog=90。

1. **constitution_rail**：`before_tool_call` 钩子内对 bash/write 类工具做参数级检查（正则命中 secret/危险调用/denylist 依赖安装）→ 命中即 `raise AbortError`（CRITICAL 语义）。静态面由 H6 兜底，此 rail 是运行时护栏（PDR-001 H6 的双保险）。
2. **builder_isolation_rail**：`before_tool_call` 拦截路径包含 `oracle_store/`、`waves/*/holdout`、`*.golden.json`、`rubrics/` 的读写；`after_model_call` 对 builder 出站消息做 canary 扫描（命中→AbortError+违规记录）。
3. **judge_freeze_rail**：会话开始时记录 `oracle_store/rubrics/**` 与 `opc/gates/**` 哈希基线；任何写工具命中这些路径→拒绝；会话结束校验基线未变。
4. **verifier_determinism_rail**：守护 verify_pipeline 进程（非 LLM）：校验管线 YAML 无 `llm:` 节点；若检测到 LLM 调用（除 judge 客户端白名单）→ 中止并告警。
5. **feedback_redaction_rail**：leader 对 builder 的返工消息（`team.update_task`/send_message 前）经过滤器：保留 {gate_id, check_id, 摘要≤200 字}，删除 {场景输入, 期望值, rubric 片段, 判词原文}。实现为纯函数 `redact_feedback(payload) -> payload'`，可单测。
6. **watchdog_rail**：每波次结束读取 `world/metrics.jsonl` 尾窗，按 PLAN.md §7 五条触发规则产出降级建议事件（不直接改 stage——经提案通道人类批准；唯一例外：S 门停用为自动软降级，因判据不可信时“降低自治级别而非放宽判据”是宪法条款 15 的直接执行）。

## 5. 模型档位与路由（tiers.yaml 语义）

```yaml
tiers:
  RU-L: {model_ref: models.defaults[2], roles: [cartographer, moderator, reconciler]}
  RU-M: {model_ref: models.defaults[1], roles: [builder, leader, spec_steward, deep_agent]}
  RU-H: {model_ref: models.defaults[0], roles: [architect, spec_moderator, critic, judge]}
escalation:
  builder: {trigger: oracle_fail, target: RU-H, max_times_per_task: 2}
  cartographer: {trigger: retrieval_fail_streak>=3, target: RU-M}
judge_floor: "builder 档位 rank"          # JudgeWorkflow.tier_table 消费
families: {qwen-*: fam-qwen, gpt-*: fam-gpt, claude-*: fam-anthropic}   # 三查用
prefix_discipline:                        # 上下文经济纪律（全员）
  stable_prefix: [role_card, tool_defs, spec_full_or_contract_excerpt]
  append_only: [task_delta, tool_results, timestamps]
```

路由 P0 为纯规则（上表）；`models.defaults` 多配置 + 运行时 switch 用 jiuwenswarm 现成机制（`config.yaml:L235-245`、`agent_ws_server.py:L5501-5617`）。成本归集：observability（`ObservabilityConfig`，agent-core `extensions/observability/config.py:L53-62`）+ LLM trace 日志解析（可复用 `agent-tools/dev_tools_suite/log_parse`，零依赖）→ 写 `usage.json` 供 H8。

## 6. 沙箱与权限

- builder 沙箱：jiuwenbox（Landlock+Seccomp+bubblewrap+cgroup，`jiuwenswarm/jiuwenbox/src/jiuwenbox/supervisor/*`）；挂载白名单=净化工作区 + 依赖缓存；网络=允许 PyPI 镜像（可关），禁止访问 oracle_store 服务端口。
- 权限引擎：`permissions.enabled=true`，`permission_mode: strict`（builder 侧），工具级 allow/ask/deny 按角色卡配置（`config.yaml:L885-998`）；verifier/world 侧服务进程以专用账号运行，持有 oracle_store 读权。
- 审批流：builder 的破坏性 shell 前置确认保持开启（上游默认）；wave merge 不需要人类审批（R0/R1），R2/R3 变更的人类介入点在 **L2 契约 diff**（spec 仓 PR），不在代码 PR——与 PDR-001 §9 一致。

## 7. 会话与事务边界

| 边界 | 机制 |
|---|---|
| 波次内中断恢复 | Checkpointer(persistence/sqlite) + session.rewind（仅治理队会话；builder 临时会话失败即重采样，不做细粒度恢复——实例可丢弃） |
| 准入原子性 | admit()→账本→git merge --no-ff 同一事务脚本；任一步失败→abort（补偿记录+revert） |
| 判别侧冻结 | 一个波次=一个 verifier session；session 内门禁定义/rubric 哈希基线不变（judge_freeze_rail + CI 校验） |
| 演进生效边界 | 提案批准后仅新 session 装载（配置加载时机=会话启动，天然满足） |
