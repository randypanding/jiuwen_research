# openJiuwen 开发型 Agent Swarm 最终工程计划（主计划）

> 版本 1.0.0 ｜ 前提文档：`structure.md`（PDR-001 范式决策，下称 PDR）
> 参考实现：本仓 `swarmdev/`（契约、门禁、oracle、漂移、准入、指标，**139 项测试全绿**，本计划的机制均已被可执行代码验证）
> 能力基线：`CAPABILITY_MAP.md`（锁定 11 个 submodule 的上游 commit）

---

## 0. 这份计划是什么

PDR-001 决定了范式（spec 为唯一真值、门禁与事务为物理层、人类前移到契约层）。本计划把范式落到**可直接开工**的程度：

1. 给出总体架构与 12 个工作包（T1–T12）的切分、依赖顺序、验收标准；
2. 每个工作包有独立任务书（见 `02_team_briefs.md`），执行团队只需解决本包内问题；
3. 所有跨包契约（schema + 通信协议）在 `01_CONTRACTS.md` 冻结，并已有参考实现与测试；
4. 重要 CI 门禁与 oracle 不仅定义了，而且**写出来并测过**（`swarmdev/` 内 H1–H8 门禁引擎、holdout 场景运行器、差分引擎、黄金输出库、judge 工作流与校准器、漂移检测器、准入编排器，全部带测试）；
5. CI 配置（`.github/workflows/swarmdev.yml`）已就位。

执行原则：**契约先行、机制先验证、再上生产件。** 参考实现是"机制正确性证明"，生产实现按任务书替换为分布式/持久化形态，但**不得改变契约与判定语义**。

---

## 1. 总体架构

### 1.1 分层与承载

```
第0层 宪法（PDR §14 十五条不变量）
      承载：swarmdev.contracts.roles.CAPABILITY_MATRIX（可执行投影）+ judge rubric 引用文本
第1层 Spec 仓（L1/L2/L3 + R 级注册表 + dont_care 登记）          ← T1
第2层 Oracle（holdout 场景库 + rubric + 校准集 + 差分/黄金判据）   ← T3/T4
第3层 实例空间（builder fan-out，临时团队，即用即散）              ← T6
第4层 世界（已准入代码库；波次=事务边界；准入=提交点）             ← T5
物理层 门禁引擎 H1–H8 + judge 软门禁（verifier WorkflowAgent 执行） ← T2/T6
观测层 指标与降级触发（spec 闭合度/熵/漂移率/judge κ/成本）        ← T9
```

### 1.2 系统拓扑（单机起步，对应 PDR §11「单机优先」）

```
                 ┌────────────────────────────────────────────────┐
 人类 ──L1/L2──▶ │ Spec 仓服务 T1（git 为存储，服务做校验/索引）     │
                 └───────┬───────────────────────────┬────────────┘
                         │ spec-delta 事件            │ 条款/见证查询
                 ┌───────▼───────┐           ┌───────▼────────┐
                 │ Leader 团队    │◀──波次计划─│ Architect 过程  │
                 │ (jiuwenswarm   │           │ (DeepAgent+     │
                 │  TeamManager)  │           │  Workflow 嵌套) │
                 └───────┬───────┘           └───────┬────────┘
        task fan-out     │                            │ holdout/rubric 持有
                 ┌───────▼───────┐                    │
                 │ 临时 Builder×N │            ┌───────▼────────┐
                 │ lifecycle=     │──实例提交──▶│ Verifier       │
                 │ temporary      │            │ (WorkflowAgent │
                 └───────────────┘            │  跑 H1–H8+S)   │
                                               └───────┬────────┘
                    judge(≥builder 档位)◀──JUDGE_REQUEST│
                 ┌───────────────┐    ┌───────────────▼────────┐
                 │ Judge 面板     │───▶│ 准入决策 → 证据收据      │──▶ 世界(git merge)
                 └───────────────┘    └────────────────────────┘
 旁路：Reconciler(H7 定时) / Cartographer(agent-as-tool) / Critic(红队补场景)
      / Refactor(准入后) / Moderator(可读性) / DeepAgent(提案, auto_save=False)
```

通信一律走**类型化信封**（`swarmdev.contracts.envelope.ContractBus` 语义），13 种信封的收发矩阵即信息不对称纪律的机械执行（详见 `01_CONTRACTS.md` §3）。

### 1.3 与 openJiuwen 的绑定（证据级）

| 范式件 | openJiuwen 承载 | 证据锚点 |
|---|---|---|
| builder 临时 fan-out、不写记忆 | jiuwenswarm 临时团队 `team.jiuwen_team.lifecycle=temporary`；temporary 不触发记忆 auto_extract | `jiuwenswarm/jiuwenswarm/resources/config.yaml:1219,1348`；`remote_member_bootstrap.py:118,1769` |
| 编排/事件/任务工具 | agent-core `TeamRuntime`（register_agent/send/publish/subscribe）+ `TaskCreateTool/ViewTaskTool/UpdateTaskTool/ClaimTaskTool/VerifyTaskTool` + `SendMessageTool` | `agent-core/openjiuwen/core/multi_agent/team_runtime/team_runtime.py:55,163,350,410`；`agent_teams/tools/tool_task.py:225-1117`；`tool_message.py:61` |
| 团队记忆（判别侧写入闸门） | `TEAM_MEMORY.md` 四分类，仅 leader 角色可写（`_extract_after_round_bound` role 检查） | `agent-core/openjiuwen/agent_teams/memory/manager.py:340`；`shared_memory.py:17-124`；`extractor.py:47-50` |
| verifier 确定性流水线 | `Workflow`（set_start_comp/add_workflow_comp/add_connection/add_conditional_connection/invoke）+ `WorkflowAgent`；嵌套 `SubWorkflowComponent`；checkpoint 钩子 | `agent-core/openjiuwen/core/workflow/workflow.py:98,165,268,317`；`core/application/workflow_agent/workflow_agent.py:11` |
| 硬门禁的运行时拦截（H6 投影） | `AgentRail` 12 钩子 + `RiskLevel` 五级 + CRITICAL→`AbortError` | `agent-core/openjiuwen/core/single_agent/rail/base.py:652-785`；`core/security/guardrail/guardrail.py:377` |
| 波次事务续跑 | `Checkpointer`（in_memory/persistence[sqlite|shelve]/redis）+ `interrupt_agent_execute` + `InteractiveInput` | `agent-core/openjiuwen/core/session/checkpointer/base.py:14-60`；`checkpointer.py:60`；`persistence.py:725`；`extensions/checkpointer/redis/checkpointer.py:340` |
| 上下文隔离 | ContextEngine `ContextEngineConfig`（session 级窗口/压缩） | `agent-core/openjiuwen/core/context_engine/schema/config.py:23-113` |
| 模型档位与路由 | `IntelliRouterModelClient` + `ProviderType.IntelliRouter`；团队侧 `IntelliRouterAllocator` | `agent-core/openjiuwen/core/foundation/llm/model_clients/intelli_router_model_client.py:96`；`core/foundation/llm/schema/config.py:24` |
| 演进受控（deep agent 提案） | `SkillEvolutionRail(auto_save=False)` + `EvolutionApprovalRuntime`（approve/reject/finalize） | `agent-core/openjiuwen/harness/rails/evolution/skill_evolution_rail.py:141,172`；`evolution/approval_runtime.py:17,97` |
| cartographer as tool | `DeepAgent.create_subagent` / TaskTool 派生 | `agent-core/openjiuwen/harness/deep_agent.py:1187`；`jiuwenswarm` TaskTool（`app_agentserver.py:143`） |
| 沙箱执行（H1/H2/H3 运行环境） | jiuwenbox（Landlock+Seccomp+bwrap，REST :8321，best_effort 降级） | `jiuwenswarm/jiuwenbox/.../sandbox_manager.py:135`；`supervisor/landlock.py:25` |
| 角色热插拔扩展 | jiuwenswarm `RailManager`（extensions/<name>/rail.py + extensions_config.json） | `jiuwenswarm/jiuwenswarm/agents/harness/common/plugins/rail_manager.py:52-118` |

框架未覆盖、本计划自建（参考实现已完成机制验证）：spec 仓结构与 delta 流水线、R 级注册表、holdout 库与可见性强制、差分引擎、黄金输出库、证据收据、spec 熵/闭合度指标、规则变更提案通道、契约通信总线。

---

## 2. 关键工程决策记录（ADR 摘要）

| # | 决策 | 理由/来源 |
|---|---|---|
| ADR-1 | spec 文件格式：Markdown + YAML frontmatter（version/BC-NBC 记录）+ `contract` 围栏块（assume/guarantee/invariant/dont_care/witnesses），每条款 `CL-xxx` ID；验证状态 draft/parsed/model_checked/human_confirmed | research `01_自然语言与形式化契约融合.md`（DbC 范式、LLM 语义正确率远低于句法正确率→必须闭环验证）；参考实现 `swarmdev/contracts/spec_doc.py` |
| ADR-2 | spec-delta = 结构化条目（op×target×BC/NBC），**非文本 diff**；NBC 强制 major bump + 人类批准字段；CI 用校验器强制（不靠自觉） | research `03_Spec版本化.md`（SemVer 合规最坏仅 25%；oasdiff 模式）；`swarmdev/contracts/spec_delta.py`（含 SemVer 联动校验测试） |
| ADR-3 | 门禁引擎：8 个硬门禁全部机械化，注册表拒绝"仅软门禁"；执行器 fail-fast；**agent 不得修改 oracle/测试文件**（OwnershipGuard 哈希哨兵，篡改即 FAIL） | PDR §8；research oracle_ci_gate（文件所有权隔离、退出码机械阻断）；`swarmdev/gates/*` |
| ADR-4 | holdout 可见性用**能力令牌**机械执行：`CAPABILITY_MATRIX["holdout.read"]` 不含 builder/leader；信封总线的 RECEIVER_MATRIX 同步禁止判据类信封流向 builder；SPEC_ASSIGNMENT payload 键集合冻结为 {spec_id, version, ru_id, l1_intent} | PDR §7；research 信息不对称（提示词级防御全部可破，必须硬编码在应用层）；`swarmdev/contracts/roles.py,envelope.py` + 集成测试 |
| ADR-5 | 差分判据三级：I/O 等价（归一化序列化比对）→ 行为等价（退出码/副作用）→ 形式化（仅 R3 关键路径，SymDiff/Z3 级，后置）；LLM 只做输入生成与反例探测，**不做判定** | research 差分测试/行为等价判据；`swarmdev/oracle/diff_engine.py` |
| ADR-6 | 黄金输出双轨：快照库（`.r3info` manifest：spec_hash/seed/lock_hash/approved_by）+ 独立预言；**CI 永不自动写黄金**（save 无 approved_by 抛 ApprovalRequired）；缺快照即失败 | research r3-golden-output；`swarmdev/oracle/golden.py` |
| ADR-7 | judge 工作流：多次采样多数票、abstain 合法、veto 必须带理由与证据引用、pairwise 必须交换顺序双跑；**κ≥0.6 才启用软门禁**（Cohen's kappa 对 50–100 条金标集），跌破即软门禁停用（降级而非放宽判据） | research llm-as-judge；PDR §13；`swarmdev/oracle/judge.py,calibration.py` |
| ADR-8 | fan-out 判别表直接实现 PDR §6 六行表（CLOSED/SILENCE/DIVERGENCE/TIER_GAP/SPEC_ORACLE_CONFLICT/INSUFFICIENT）；H5 集成差分是 RU 级信号（失败不株连单实例资格，转为 has_divergence），R3 的 H5 是逐实例黄金判定 | PDR §6；`swarmdev/admission/measurement.py` + orchestrator + e2e 测试（含 SILENCE 路径） |
| ADR-9 | 准入 = 波次状态机 PLANNED→COLLECTING→ADJUDICATING→COMMITTING→COMMITTED（或 ROLLED_BACK）；收据强制完整性（admitted=True 必须 H1–H8 齐全 + 无 veto，schema 层拒绝）；被丢弃实例必须携带测量结论 | PDR §4/§9、宪法不变量 2/12；`swarmdev/contracts/receipt.py,wave.py` |
| ADR-10 | 漂移检测三级漏斗：契约哈希（条款内容哈希 sidecar，秒级）→ 结构（@REQ 标签图：未知引用=hard、有见证无实现标签=advisory）→ LLM 语义层（夜间批处理，M2 再上）；reconciler 只上报不改 spec | research spec-traceability（SpecSeal/LCEF 模式）；`swarmdev/drift/*` |
| ADR-11 | 模型档位：L/M/H 三档，`TierAssignment` schema 强制 judge≥builder、verifier≥builder；起步映射 builder=M、judge=M、architect=H、cartographer=L；承载用 IntelliRouter | PDR §7.5；research TCO（每档精选 1 模型）；`swarmdev/teams/tiering.py` |
| ADR-12 | 存储：spec 仓/oracle 仓/收据全部 **git 为底**（可审计可回滚天然满足宪法不变量 12），服务层只做校验与索引；波次运行时状态用 sqlite checkpointer，分布式再切 redis | PDR §13 可回滚；openJiuwen Checkpointer 现成后端 |
| ADR-13 | 目标域试点选 **agent-tools/infer_router 的配置/路由子模块**（纯 Python、依赖干净、行为可测、blast radius 小），不选 jiuwenbox（依赖内核能力）与 agent-studio（Java 跨语言） | CAPABILITY_MAP 组件边界 + M0 风险最小化 |
| ADR-14 | 本期不引入：Temporal/Percolator 级波次事务编排（并发压力未证实）、分布式锁层、KLEE/全量演绎验证、Studio 中央路由。留档观察 | research spec-concurrency（起步基线=Git 分支+结构合并+breaking 门禁）；`06_程序合成验证.md`（演绎验证仅 B 级成熟度） |

---

## 3. 工作包总览与依赖

```
T1 spec 仓 ─┬─▶ T2 门禁 CI ─┬─▶ T5 准入与波次 ─▶ T10 试点收割(M0) ─▶ M1/M2 演进
T3 oracle ──┤               │
T4 差分/黄金 ┘      T6 角色与团队 harness ─┘
T7 漂移服务(H7 生产化)  T8 cartographer   T9 指标与降级   T11 提案通道   T12 文档与培训
```

| 包 | 名称 | 依赖 | 关键产出 | 验收门（本计划内可机器判定） |
|---|---|---|---|---|
| T1 | Spec 仓与治理 | — | spec 目录规范、delta 流水线、R 注册表、校验 CLI | `swarmdev` contracts 测试集 + spec lint 在试点域零错误 |
| T2 | 门禁引擎与 CI | T1 | GateRunner 生产封装、CI workflow、分支保护、所有权哨兵 | 8 门在 CI 全跑；篡改 oracle 文件必红 |
| T3 | Oracle 服务 | T1 | holdout vault（可见性强制）、场景运行服务、轮换协议、κ 校准例行 | builder 令牌读取 holdout 必被拒；κ 报告入库 |
| T4 | 差分与黄金 | T3 | 输入生成器（属性/覆盖率引导）、SPRT 统计通道、黄金审批流 | 差分引擎在试点域检出注入的行为差异；黄金更新必带审批 |
| T5 | 准入与波次服务 | T1,T2,T3 | orchestrator 服务化、checkpointer 持久化、收据归档、回滚演练 | e2e 六场景（已具原型测试）+ 回滚原子性测试 |
| T6 | 角色与团队 harness | T2,T3 | 12 角色 openjiuwen 装配（见 `swarmdev/teams/harness_map.py`）、记忆写入闸门、档位策略落地 | 临时团队不留痕测试；记忆写入必经 spec moderator |
| T7 | 漂移服务 | T1 | reconciler 定时任务、H7 接 CI、drift 告警信封 | 注入漂移必被 H7 拦截（已有回归测试） |
| T8 | Cartographer | T6 | MCP 检索工具（BM25+结构图）、返回契约（file:line+置信度+预算截断） | 检索命中率基线 + 主链路缓存命中不降 |
| T9 | 指标与降级 | T5 | 健康度快照服务、五个降级触发器自动化、人类报告面 | 三降级触发器单测（已有）+ 报表样例 |
| T10 | 试点域收割（M0） | T1,T2,T7 | infer_router 域 spec 收割、场景 holdout 覆盖、H1–H4/H7 全绿 | 试点域判据覆盖率≥阈值；漂移检测上线 |
| T11 | 提案通道 | T6 | deep agent 提案→人类批准→新 session 装载流程 | auto_save=False 审批流测试（复用 approval_runtime） |
| T12 | 运行手册 | 全部 | 部署手册、runbook、降级演练脚本 | 评审通过 |

任务书全文：`02_team_briefs.md`。契约全文：`01_CONTRACTS.md`。CI 规范：`03_CI_GATES.md`。

---

## 4. 里程碑（PDR §12 迁移梯度的落地排布）

| 里程碑 | 内容 | 进阶条件（机械可查） |
|---|---|---|
| M0 收割 | T1–T4、T7、T10 完成；试点域 spec 收割完，H1–H4+H7 上线 | 试点域 L2 条款 100% 有见证或显式 unverifiable 标记；漂移检测连续 1 周运行 |
| M1 锚定 | T5、T6、T9 上线；R0 单元可丢弃重生 | 场景 holdout 覆盖率达阈值；H5 差分门可用；连续 2 波次闭合度≥0.6 |
| M2 再生 | R0/R1 常规 fan-out；T4 统计通道与 T8 上线 | 连续若干波次零逃逸缺陷；judge κ≥0.6 持续达标 |
| M3 工厂 | T11 常态化；R2 演进/R3 冻结流程跑通 | deep agent 提案通道有人类批准记录；降级演练通过 |

**禁止跨阶段**：oracle 覆盖不足的域不得宣布"代码可丢弃"（PDR §12 唯一致命误用）。

---

## 5. 风险登记册（Top 项）

| 风险 | 缓解 | 责任包 |
|---|---|---|
| holdout 被"考穿"（Building to the Test） | 轮换协议（epoch 单调递增）+ 场景 3 个月退役 + canary 抽查 | T3 |
| judge 漂移（模型升级后判据失效） | 任一模型/prompt 变更触发重校准；κ<0.6 自动停软门禁 | T3/T9 |
| 沙箱在 CI 容器不可用（Landlock/bwrap 需特权） | jiuwenbox `best_effort` 降级；CI 门 H1–H3 允许非沙箱 runner，H6 策略门强制 | T2 |
| spec 收割质量不足（LLM 语义正确率低） | L2 必须过 parsed→model_checked→human_confirmed 三态闭环；收割条款默认 draft 不得作放行依据 | T1/T10 |
| 成本失控 | N 硬顶 8；预算门 H8；单位准入成本进指标，超基线 3 倍告警 | T4/T9 |
| openJiuwen 上游漂移（submodule 锁 commit） | CAPABILITY_MAP 锚点行号复核纳入 T12 runbook；升级走独立波次 | T12 |

---

## 6. 参考实现清单（已验证机制，全部带测试）

```
swarmdev/
├── contracts/   spec_doc / r_level / spec_delta / oracle / receipt / wave / envelope / roles / ids
├── gates/       runner + h1_build … h8_budget（含 OwnershipGuard 哨兵）
├── oracle/      holdout_store（能力令牌）/ scenario_runner / diff_engine / golden / judge / calibration
├── drift/       trace_tags / contract_hash / detector
├── admission/   measurement（§6 判别表）/ orchestrator（波次状态机+信封发布）
├── metrics/     health（闭合度/κ/降级触发器）
├── teams/       tiering（档位策略）/ harness_map（角色→openJiuwen 绑定表）
├── integration/ wiring（GateRunner 装配 + H7 接线）
└── tests/       139 项：契约 11 / 门禁 41 / oracle 36 / 漂移 18 / 准入 17 / 指标 5 /
                 团队 3 / 端到端 8（含 CLOSED、SILENCE、DIVERGENCE、veto、漂移、R3 黄金双路径）
```

运行：`cd swarmdev && python3 -m pytest tests/ -q`
