# 04 角色 Harness 配置规范（jiuwenswarm 落地）

> 12 个角色 = PDR-001 §10 的范式函数。本文给出每角色的 jiuwenswarm 配置决定。
> 依据：jiuwenswarm 声明式装配（agents/swarm/assembly.py、config_specs.py）、RAIL_WHITELIST（team_runtime_inheritance.py）、lifecycle（config_loader.py）、skills-visibility、modes.team.*.memory。

## 0. 团队拓扑（已决）

| 团队 | 生命周期 | 成员 | 记忆域 |
|---|---|---|---|
| 指挥团队 | persistent | leader、architect(过程)、verifier(workflow) | 团队记忆（只读继承给临时团队） |
| spec 治理团队 | persistent | spec steward、spec moderator、reconciler | 独立记忆域，spec 仓为工作对象 |
| 交付 builder 群 | **temporary**（每波次即散） | builder ×N | 只读父记忆，无 TEAM_MEMORY，销毁不留痕 |
| 标定 builder 群 | temporary（B 流水线专用） | builder ×N | 与 A 线不同 leader、不同记忆域 |
| 辅助 | agent-as-tool | cartographer | 无记忆 |
| 后处理 | 独立会话 | refactor、moderator | 不写实现记忆 |
| 演进 | rail+提案器 | deep agent | 只提案 |

## 1. 逐角色配置

### leader（编排）
- team.leader persona；`lifecycle: persistent`；模式 `code.team`。
- 工具白名单：create_team/clean_team/create_task/view_task/update_task/send_message、swarm-kernel CLI（gates/admit/drift）、EventLog 查询。
- rails：task_planning（开）、evolution（leader 进化+创建侧）。
- 禁止：judge 工具、spec 写工具、holdout 读取。
- 档位：中高档（RU-M/H）。

### architect（切波次/DoD/rubric，agentic 过程）
- 形态：DeepAgent 外层 TaskLoop + create_subagent（非单一 agent）；独立 context_id。
- 产出物：WavePlan、SpecDelta 草案、Rubric、DoD；写 oracle 目录（唯一写者之一，与 verifier 分权：architect 写场景与 rubric，verifier 只执行）。
- 持有：holdout 全量。档位：RU-H 预路由锁定，不级联降级。
- 禁止：进入 builder 团队上下文；写 world/。

### builder（采样实例，临时 fan-out）
- 团队 `lifecycle: temporary`；成员只读父记忆（read_only_source=parent_workspace_path）。
- 输入仅：spec（L1/L2/L3）+ 接口冻结面（WavePlan.frozen_interfaces）+ 本地可跑自测框架；**无 holdout、无 rubric、无端到端场景**。
- 工具白名单：代码读写（沙箱内）、运行自测（H2 类）、打包提交（InstanceSubmission）；禁网（依赖镜像除外，jiuwenbox 策略）。
- 输出契约：02 文档 §4 实例打包格式。CoT 不出沙箱（submission 只含 claim+证据引用）。
- 档位：RU-M；oracle 失败升档 ≤2 次（T8 路由）。禁止：记忆写、judge、spec 写、与其他 builder 通信（fan-out 独立性）。

### verifier（执行判据，workflow 为主）
- 形态：WorkflowAgent 确定性流水线（H1→H2→H3→H4→H5→H6→H7→H8→judge workflow），不得由自主 agent 决定跳过任何门。
- 持有：holdout + rubric；执行 judge 工作流（采样/交换/弃权由 swarm_kernel.judge 固定）。
- 产出：GateSuiteResult、ScenarioOutcome、JudgeVerdict。
- 禁止：写判据（rubric/场景改动走 architect）、改 spec、救场豁免。
- 档位：judge 档位 ≥ builder 档位（IntelliRouter deployments 独立池）。

### spec moderator（L1，持久）
- 触发输入：MeasurementEvent（silence/divergence）。
- 动作：登记 DontCareDeclaration 或产出 spec-delta 草案（交 steward 落库）；裁定实现细节是否入团队记忆（MemoryWrite 的唯一合法生产者）。
- session 内冻结：判据与裁决规则不变。

### spec steward（L1，持久）
- spec 仓维护：条款一致性、版本（next_version 校验）、L2 diff 呈报人类。
- 人类接口：L2 diff 视图 + 否决权（NBC 必须人类批准）。

### reconciler（L1–L4，定时/心跳）
- 执行 H7 策略侧：drift scan 定时 + 波次后触发；发现漂移即 DriftEvent 上报并阻断（不自行改 spec）。
- session_scope=`*` 观测权限（唯一允许的通配订阅者之一），全量审计。

### cartographer（agent-as-tool）
- 形态：TaskTool 包装的检索服务；弱档位 RU-L、高缓存命中。
- 返回契约：紧凑 JSON（结论 ≤150 token、file:line+置信度、commit SHA 新鲜度、token 预算截断）；探索轨迹留在本层，失败即丢弃，不回传过程。
- 用途：代码定位、CI 失败点定位与初步解释；无准入权。连续检索失败升 RU-M（≤1 次）。

### critic（红队）
- 输入：spec + 已准入实例的公开面；产出：新场景提案进 oracle（architect 审入），不直接改代码。

### refactor（熵重置后处理）
- 准入后独立会话重写 R0/R1 实现；**契约面不得改变**：必须过 H4（对比基线）+ H5（差分恒空）才允许替换。

### moderator（可读性治理）
- 定时巡检：wiki、依赖树视角；产出 = spec-delta 提案或 refactor 请求，不直接改代码。

### deep agent（演进，rail+提案器）
- 监测：档位策略、RU 升降档案例、规则冲突、harness 优化点。
- 产出：RuleProposal（status=draft）→ 人类批准 → 新 session 装载。当前 session 恒不生效（schema 保证，已测试）。

## 2. 隔离矩阵（配置断言项，T7 必须写成测试）

1. builder 工具白名单不含任何 oracle 路径读取；文件系统 deny（Guardrail HIGH→AbortError）。
2. builder 无 send_message 到 verifier/judge topic 的权限（bus ACL 兜底）。
3. judge workflow 的 context_id ≠ 任何 builder context_id。
4. 临时团队 teardown 后：会话目录、A2X 预约、blank card 全部回收（jiuwenswarm 既有语义，测试断言目录不存在）。
5. RAIL_WHITELIST 之外的 rail 不得注入成员（team_runtime_inheritance 语义保持）。

## 3. 模型档位表（起步）

| 档位 | 角色 | 路由策略 |
|---|---|---|
| RU-H | architect、judge(verifier 内)、spec 会诊 | 预路由锁定，不级联 |
| RU-M | builder（默认）、leader、spec moderator/steward | oracle 失败升档 ≤2 次 |
| RU-L | cartographer | 连续失败升 RU-M ≤1 次 |

成本口径：计入缓存有效成本；以"成功调整后单位准入成本"评估（健康度 admission_cost_tokens 为其一维）。
