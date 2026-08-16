# 01 · 系统架构：拓扑、角色映射与 Harness 配置

> 所有 openJiuwen 引用均锁定于 CAPABILITY_MAP.md 所列 commit。路径:行号为实施时的精确落点。

## 1. 分层视图

```
第0层 宪法            spec/constitution.md（自然语言不变量，H6 的可机械化投影 + judge 引用源）
第1层 规范 Spec       spec/domains/<domain>/spec.json（C01：L1/L2/L3 + 条款 + 见证绑定 + dontcare）
第2层 判据 Oracle     holdout/<domain>/*/suite.json（C06）+ rubrics/（architect 私有）+ 门禁族 H1-H8
第3层 实例 Instance   instances/<wave>/<task>/<instance>/（可丢弃 worktree）
第4层 世界 World      目标代码仓 main 分支（已准入代码 + receipts/ 证据链）
```

物理层工具链 = `swarmfoundry`（已实现并测试）。

## 2. 团队拓扑（团队边界与生命周期）

| 团队 | 形态 | 生命周期 | 成员（角色） | openJiuwen 承载 |
|---|---|---|---|---|
| T-CTRL 交付控制 | 持久团队 | persistent | leader、architect（按需唤起）、cartographer（agent-as-tool） | jiuwenswarm team mode（modes.team.jiuwen_team，lifecycle=persistent） |
| T-NORM 规范委员会 | 持久团队 | persistent | spec steward、spec moderator、reconciler | 同上；TEAM_MEMORY.md 四分类（agent-core/openjiuwen/agent_teams/memory/extractor.py:L47-L50） |
| T-CAL 标定团队 | 持久团队 | persistent | 标定 leader、critic | 同上；独立记忆域（不同 team_name ⇒ 独立 TEAM_MEMORY） |
| T-BUILD-<wave>-<task> | 临时团队 | temporary | builder ×N（fan-out） | lifecycle=temporary（jiuwenswarm/agents/harness/team/config_loader.py:L550）；启动清理 remove_team_mode_session_dirs_at_startup（session_metadata.py:L1301-L1342） |
| verifier | 无团队（工作流进程） | 按波次任务 | SwarmFlow 工作流 + 工具化 gate runner | agent-core SwarmFlow（workflow/engine/runner.py:L113-L178），无自主决策 |
| judge panel | 无团队（工作流步骤） | 按门禁批次 | 无 agent，仅模型调用 | verifier 工作流内的 judge 步骤（D-16） |
| refactor / moderator / deep agent | 定时/事件唤起的单体 agent | 任务级 | 各自单体 | DeepAgent + cron/事件触发；SkillEvolutionRail(auto_save=False) |

隔离要求复核（structure.md §10）：
- leader 不判别（无 judge 工具、无 holdout 挂载）；
- architect 不在生成团队内（T-CTRL 之外的独立 session，持有 holdout/rubric 目录）；
- builder 临时、无记忆写、无 holdout（D-22 三层）；
- spec moderator 与 leader 分离（不同团队 T-NORM vs T-CTRL）。

## 3. 角色 → openJiuwen 精确映射

### 3.1 leader（编排、波次推进、事件驱动）
- 形态：jiuwenswarm team mode 的 leader 成员（TeamAgent leader 角色）。
- 波次推进脚本：SwarmFlow 工作流 `waves/run_wave.py`（META + `async def run(args)`，静态校验 loader.py:L48-L109），由 leader 经 SwarmflowTool 启动（agent-core/openjiuwen/agent_teams/workflow/tool_swarmflow.py:L50-L58），journal 落 `waves/journals/<wave_id>.journal`。
- 任务面：create_task/view_task/send_message 直接复用 agent_teams 工具（tool_task.py:L225/L441；message_manager.py:L27-L164）。
- 事件回流：team.task/team.member/team.message 事件（jiuwenswarm/common/schema/message.py:L256-L258 → team_helpers.py:L209-L244）映射到 C10 ledger。
- 检查点/回滚：Checkpointer redis 后端（agent-core/openjiuwen/extensions/checkpointer/redis/checkpointer.py:L229）+ session rewind（jiuwenswarm interface_deep.py:L42）。

### 3.2 architect（切波次、DoD、verification/rubric、RU 粒度）
- 形态：DeepAgent（create_deep_agent，agent-core/openjiuwen/harness/factory.py:L454-L485）+ enable_task_loop，独立 session。
- 产出物：WavePlan（C09）写入 `waves/plans/<wave_id>.json`；holdout 场景骨架与 rubric 写入 holdout 库；接口冻结面 = ContractSurface（C05，`swarmfoundry surface-extract` 产物）存 `waves/freeze/<wave_id>/`。
- holdout 持有：architect 进程的文件访问策略允许 holdout 库读写；其上下文 id 与 builder 完全隔离（ContextEngine full_context_id = session_id_context_id，agent-core/openjiuwen/core/context_engine/context_engine.py:L138）。

### 3.3 builder（采样实例，临时 fan-out）
- 形态：T-BUILD-* 临时团队成员；每个成员一个独立实例 worktree `instances/<wave>/<task>/inst-<i>/`。
- 工具白名单：code mode 工具族（code-todo 等，jiuwenswarm/agents/harness/code/tools/code_todo_tools.py:L42-L115）+ bash/write（沙箱内）+ cartographer 只读检索；无 team 管理工具、无记忆写工具、无网络（沙箱 NetworkPolicy isolated，jiuwenbox/src/jiuwenbox/models/policy.py:L445-L654）。
- 输入注入（上下文经济，D-21）：system prompt = spec L1/L2/L3 恒定段 + 接口面（ContractSurface 摘要）+ 自测指引；spec-delta 会话尾部注入。
- 禁止项机械检查：rails 白名单 + jiuwenbox files.deny 指向 holdout/rubrics 路径。

### 3.4 verifier（只执行判据）
- 形态：SwarmFlow 确定性工作流（无 LLM 决策步骤），步骤：装载 GateContext → 顺序跑 H1..H8（swarmfoundry GateRunner）→ judge 面板（S）→ 产 AdmissionDecision（C03）→ 回传 gate.result/admission.decision（C10）→ 登记 receipt（C04）。
- 执行环境：H1/H2/H3/H5 的实例执行在 jiuwenbox（verifier policy：禁出站网络、只读挂 holdout、实例目录可写）。
- 禁止项：不写判据（rubric 只读）、不改 spec、不做实例选择（选择由 leader 按"闭合度+次要判据"执行，记录于 receipt.notes）。

### 3.5 spec moderator / spec steward / reconciler（T-NORM）
- moderator：消费 measurement.event（C11）；裁决沉默→登记 DontCareEntry（C01）或产 spec-delta；裁定实现细节是否入 TEAM_MEMORY（经 T-NORM leader 写，manager.py:L335 仅 leader 可写）。
- steward：条款一致性、版本（spec.json version 单调递增）、re-seal 通道唯一执行者（`swarmfoundry spec-seal`）。
- reconciler：定时跑 `gates-run --H7-only`（即 H7DriftGate 单独执行）+ 漂移上报；只上报与阻断，不改 spec（structure.md §10）。

### 3.6 cartographer（agent-as-tool）
- 形态：TaskTool 子 agent（agent-core/openjiuwen/harness/tools/subagent/task_tool.py:L55-L211；子 session 隔离 + 独立 workspace 子目录 + subagents=None）。
- 检索底座（M1 起）：MCP 检索服务（BM25+向量+AST 图多视图，code-search-agent-research §6），索引缓存目录不入上下文前缀（D-21）。
- 返回契约：`{file, lines, why, min_dependency_closure, confidence}`；不确定时返回候选集而非猜测；CI 失败定位用 SHERLOC 式假设驱动流程（输出"定位+诊断"注入修复 agent）。

### 3.7 critic / refactor / moderator / deep agent
- critic（T-CAL）：红队攻击 spec 与实例，产出进 holdout 库（新场景 PR）而非直接改代码。
- refactor：准入后熵重置；硬约束"不得改变契约面"= 前后 ContractSurface diff 无 breaking（H4 复用）+ 全门禁重跑。
- moderator（可读性治理）：定时扫描世界库，产出 spec-delta 或 refactor 请求。
- deep agent：监测健康指标（C12）→ RuleProposal（C13）→ 人类批准 → 新 session 生效（SkillEvolutionRail/EvolutionApprovalRuntime：agent-core/openjiuwen/harness/rails/evolution/skill_evolution_rail.py:L141-L152、approval_runtime.py:L17-L119）。

## 4. Harness 配置矩阵（每个角色的关键装配）

| 角色 | rails（priority 序） | 记忆策略 | 上下文策略 | 模型档 | 沙箱 policy |
|---|---|---|---|---|---|
| leader | stream_event、code_agent_mode（如需）、team_plan_approval、permission_interrupt | 团队记忆读写（leader 可写） | 全量 team 上下文 | TIER-M/H 混合 | 正常 |
| architect | security（BaseSecurityRail priority=90）+ 无 code rail | 独立 session 记忆 | holdout/rubric 隔离域 | TIER-H | 只读+holdout 可写 |
| builder | code_agent_mode_rail（CodeAgentModeRail，jiuwenswarm/agents/harness/code/rails/code_agent_mode_rail.py:L105）、permission rail（bash=deny 出网类）、**无** memory rail、**无** evolution rail | 无记忆写（temporary） | spec 恒定段前缀 + delta 尾注 | TIER-M | isolated + files.deny(holdout,rubrics) |
| verifier | 无自主 rail（工作流进程） | 无 | 无 LLM 上下文（judge 步骤除外） | —（judge=TIER-H） | 禁出站 |
| judge | 无工具 | 无 | rubric+匿名化交付物摘要（去来源/时间戳） | TIER-H | — |
| spec moderator/steward | memory rail、无 code rail | TEAM_MEMORY（leader 角色写） | 测量事件+spec 全文 | TIER-H | 正常 |
| reconciler | 无 | 只读 | H7 报告 | TIER-L | 只读 |
| cartographer | 无 | 无（用后即弃） | 检索预算上限 + 结果尾部追加 | TIER-L | 只读 |
| critic | security rail | 标定域记忆 | spec+实例（可见！B 线不限 holdout 给 critic，但其产出隔离） | TIER-H | 隔离 |
| refactor | code rail | 无写 | 世界代码+契约面 | TIER-M | 正常 |
| deep agent | SkillEvolutionRail(auto_save=False) | 提案库 | 健康指标+案例 | TIER-H | 只读 |

Rail 装配点：单 agent 侧 interface_code.py `_build_agent_rails`（jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L650-L737）；team 侧 providers（jiuwenswarm/agents/swarm/providers/code_rails.py:L47-L56、member_rails.py）。新 rail 一律经 RailManager 热插拔机制（extensions_config.json）或 providers `@harness_element` 注册，不改核心。

## 5. 角色提示词骨架（system prompt 恒定段，入版本库 `prompts/<role>.md`）

> 实施要求：每个角色 prompt 必须以"宪法不变量引用段"开头（15 条，structure.md §14 原文），随后是角色职责段与信息边界声明段。以下为骨架，完整文案由各 WP 按此结构撰写并纳入 rubric 校准。

```
[宪法段] 以下不变量在你的整个会话内不可协商：<structure.md §14 全 15 条原文>
[角色段] 你是 <role>。你的唯一职责是 <范式函数>。你不做 <显式禁止清单>。
[边界段] 你可见：<>。你不可见：<>。你若收到越界材料，必须拒收并上报 reconciler。
[输出段] 你的产出必须采用契约 <Cxx> 的 JSON 形态，经 <method> 发送。
[冻结段] 你在本会话内不得修改自己的判据/规则/工具；改进只能以 RuleProposal(C13) 提交。
```

builder 特有追加段：`[交付段] 你交付的是可丢弃实例。不要询问人类；不要假设未定义行为——无法从 spec 推出时，按 dontcare 登记清单执行；清单未覆盖的差异会被仪器检出并由 spec moderator 裁决。`

judge 特有追加段：`[判词段] 你只输出三值判词之一：veto（必须附证据引用）/no_veto/abstain（说明信息缺口）。你永不输出"豁免硬门禁"。你评审的交付物已匿名化，不得推测其来源。`

## 6. openJiuwen 缺口清单（不修改 submodule，扩展方式处理）

| 缺口 | 处理方式 | 承载 WP |
|---|---|---|
| holdout 可见性的沙箱策略编排（builder deny / verifier 只读挂） | jiuwenbox policy API 编排脚本（GET/PUT /api/v1/policies），无代码改动 | WP3 |
| receipt 与 git 分支的绑定 | swarmfoundry CLI + world 仓 hook（post-commit 校验），无 openJiuwen 改动 | WP4 |
| judge 面板模型家族校验 | swarmfoundry gates/judge 配置校验器 | WP6 |
| cartographer 多视图索引 | 独立 MCP 服务进程（新仓 `codesearch-mcp`），经 mcp.servers 配置接入（jiuwenswarm/common/mcp_config.py:L43-L120） | WP8 |
| SwarmFlow 内调用 GateRunner | gate runner 作为工具函数直接在 workflow 脚本内 import（同进程），无需新协议 | WP7 |
| 健康指标采集 | ObservabilityConfig OTLP（agent-core/openjiuwen/extensions/observability/config.py:L53-L62）+ receipts 聚合脚本 | WP13 |
| A2X 客户端漂移（jiuwenswarm 内嵌版与上游分叉，CAPABILITY_MAP §3.4） | 本期不用 A2X 预约；若 M2 需要，提案改回依赖上游包 | 提案通道 |

## 7. 单机运行拓扑（M0–M2）

```
jiuwenswarm gateway + agentserver（team.runtime.mode=local）
 ├─ T-CTRL / T-NORM / T-CAL 持久团队（同进程多 team_name）
 ├─ T-BUILD-* 临时团队（随波次起灭）
 ├─ SwarmFlow 引擎（verifier 工作流）
 ├─ jiuwenbox 沙箱服务（JiuwenBoxRunner 自动拉起，jiuwenswarm/server/sandbox/jiuwenbox_runner.py:L161-L211）
 └─ redis（Checkpointer + KV；JIUWEN_KV_URL）
holdout 库：独立 git 仓，文件系统权限 + 沙箱策略双控
world 库：目标代码仓，admit/<receipt_id> 分支模型（07_repo_layout §3）
```
