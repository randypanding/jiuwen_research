# 00 · 工程决策记录（全部跨团队决策的最终裁决）

> 本文是各 WP 之间**唯一**的裁决依据。任何与本文冲突的实现以本文为准；修改本文须走 spec-delta + 人类批准。
> 编号 D-xx。每条含：决策、理由、被否决的备选。

---

## A. 架构与承载

**D-01 物理层独立成包 `swarmfoundry`，零三方依赖（纯 stdlib，Python ≥3.11）。**
理由：门禁与 oracle 是"机械见证"，其自身必须可审计、可在任何 CI 环境无网络安装运行；依赖面每多一个库，H1 的可信度就降一分。
否决：基于 pydantic/FastAPI 建模（引入版本与安装面）；直接写进 jiuwenswarm（门禁代码与被测生态耦合，违反 oracle 独立性，见 oracle_ci_gate_research 结论 1）。

**D-02 swarm 承载全部复用 openJiuwen 原生机制，不引入第二套编排框架。**
映射表见 [01_architecture.md](file:///workspace/plan/01_architecture.md) §3。理由：structure.md §11 已证明逐条同构；引入 LangGraph 等第二框架会制造双真值。
否决：Temporal/Saga 编排波次事务（spec-concurrency-research 建议的 Percolator/TiKV 数据面被降级为后期项——当前单机 `team.runtime.mode=local` + Checkpointer 已满足事务边界，复杂度不值）。

**D-03 verifier 采用 SwarmFlow workflow-as-code（agent-core `openjiuwen.agent_teams.workflow.engine`）编排门禁序列。**
理由：门禁必须确定性执行（structure.md §11"门禁必须确定性"）；SwarmFlow 提供 META 静态校验、journal+WAL 断点续跑、budget、parallel/pipeline 原语（agent-core/openjiuwen/agent_teams/workflow/engine/runner.py:L113-L178）。
否决：WorkflowAgent IR（节点组件面向对话流，装配成本高于收益）；由 DeepAgent 自主决定跑哪些门禁（违反确定性）。

**D-04 测试/构建类门禁（H1/H2/H3/H5 的 producer）一律在 jiuwenbox 沙箱内执行。**
接口：jiuwenbox REST（`POST /api/v1/sandboxes`、`.../exec`，见 jiuwenswarm/jiuwenbox/docs/jiuwenbox_server_api.md）；builder 与 verifier 使用**不同 policy**（网络、files.allow/deny），verifier 沙箱禁出站（信息不对称研究 §5.2 要求）。

**D-05 spec 仓、holdout 库、世界库三库物理分离。**
- spec 仓：`spec/`（本仓目录，git 管理，只允许 spec steward/moderator 经 PR 写入）；
- holdout 库：`holdout/`（独立 git 仓/独立分支，builder 沙箱 Landlock deny，verifier 只读挂载）；
- 世界库：目标代码仓（M0 试点期为 `skillhub/` 与 `deepsearch/codesearch/`）。
理由：holdout 可见性是 reward hacking 的信息前提，必须用文件系统+沙箱策略强制（信息不对称研究结论）。

**D-06 试点域选择：D1 = `skillhub marketplace/skill_review`（brownfield 收割试点），D2 = `deepsearch/codesearch`（greenfield 再生试点）。**
理由：D1 小而自包含、已有确定性引擎与测试（skillhub/marketplace/skill_review/engines/*），适合验证 H1–H4/H7 与 spec 收割全流程；D2 是空目录（deepsearch/codesearch/.gitkeep），适合验证 R0 fan-out 再生与差分仪器，且对既有世界零风险。

## B. 契约与通信

**D-07 契约权威定义 = `swarmfoundry/src/swarmfoundry/schema/` 代码；文档 [02_contracts.md](file:///workspace/plan/02_contracts.md) 只作目录与义务说明。**
理由：单一真值必须可机械校验；任何 WP 的消息必须能通过 `from_dict`。

**D-08 角色间消息一律走 C10 SwarmEnvelope；生产环境绑定 = agent-core TeamRuntime（`send` → P2P，`publish` → PubSub topic）+ jiuwenswarm E2AEnvelope WS 方法。**
`SwarmBus` 是参考实现与契约测试载体；SwarmFlow 内的 `agent()` 原语调用自动映射为团队消息。method 命名表为闭集（envelope.KNOWN_METHODS），新增 method = 契约变更。

**D-09 任务/消息 API 采用 agent-core `agent_teams` 现成工具面：create_task / claim_task / complete_task / verify_task / view_task / send_message。**
位置：agent-core/openjiuwen/agent_teams/tools/tool_task.py（TaskCreateTool:L225、ViewTaskToolV2:L441、ClaimTaskTool:L927、MemberCompleteTaskTool:L1016、VerifyTaskTool:L1117）与 message_manager.py:L27-L164。不再发明任务协议。

**D-10 证据收据（C04）是 PR 的强制附件。** 无 receipt 的准入分支禁止合并（CI 检查 `receipts/<receipt_id>.json` 存在且 `admission.admitted==true` 且 `content_hash` 与分支 tip 关联）。

## C. 门禁与 oracle

**D-11 门禁代数 fail-closed：缺门、error、skip 一律不准入（schema/gates.py `admit()`）。** 软门禁是单调否决器。无 waiver 开关；唯一例外机制是 D-12。

**D-12 例外（waiver）仅两种且都必须留下人类批准引用：H4 breaking 豁免（config gates.H4.waiver.human_approval_ref）与 R 级变更提案（C13）。** 现场任何人（含人类）不得口头豁免；事后案例进入规则变更提案（structure.md §14.8）。

**D-13 H3 holdout 规程采纳 SWE-bench 式 FAIL_TO_PASS/PASS_TO_PASS 双结构 + 定期轮换（rotation_id）。**
每个场景文件组：`suite.json`（含 env_manifest 三必选键 PYTHONHASHSEED/TZ/SEED）+ `inputs/*.json`。缺 manifest 键 → 全场景 fail（r3-golden-output-research §5.3"manifest 不一致则比对无效"）。

**D-14 R3 黄金输出双轨：轨道 A 黄金文件比对（带 redaction），轨道 B 独立判据（property_script/参考实现）。**
黄金更新必须人工审批（`oracle/golden.py update_golden` 强制），CI 永不自动写黄金；每个 `.golden` 必须伴随 `.r3info` manifest。采纳 r3-golden-output-research §4。

**D-15 差分判定：N≥2 时两两差分，任一未登记 dontcare 的分歧 = H5 失败。**
dontcare 只能由 spec moderator 登记进 spec（C01 DontCareEntry），config 中的 `dontcare_paths` 只是其机械投影，必须与 spec 登记一致（H7 校验项，WP5 实现）。

**D-16 S 门禁（judge）规程：** 结构化判词 {verdict: veto/no_veto/abstain, reasons, evidence_refs}；至少 2 名有效判官（config 可升）；judge 模型家族 ≠ builder 模型家族（自评无效化）；弃权计入但不计数；不足额 fail-closed。rubric 由 architect 持有并对 builder 不可见。采纳 llm-as-judge-research 全部最佳实践；kappa≥0.6 校准门槛放在 M2 进阶条件（06_observability §校准）。

**D-17 H7 漂移双查：seal 漂移（条款哈希未经受控 re-seal 通道变化）+ trace 漂移（规范性条款缺 `spec-clause:<ID>` 锚点）。** 采纳 spec-traceability-bi-sync-research 三层漏斗的 ①② 层（哈希+结构）；LLM 语义层（DocPrism LCEF）仅在 M2 后由 reconciler 定时跑可疑切片，不进门禁关键路径。

**D-18 H8 成本门禁量化：** 以 receipt 累计 tokens/spend 对阈值 fail；阈值按域配置（gates.H8）。采纳 tco-optimization-research 的预算池化与自动停止，阈值初始值由 architect 按域设定并走规则提案调整。

## D. 模型档位与 TCO

**D-19 三档模型表（IntelliRouter 部署组实现）：**

| 档位 | 用途 | 绑定对象 |
|---|---|---|
| TIER-L | 检索/定位/解释 | cartographer、moderator 的 wiki 草稿 |
| TIER-M | 生成 | builder（默认）、refactor |
| TIER-H | 判别/规划 | judge、architect、spec moderator、critic |

承载：agent-core IntelliRouterModelClient（openjiuwen/core/foundation/llm/model_clients/intelli_router_model_client.py）+ jiuwenswarm `models.defaults[]` 多配置 + 按角色在 TeamAgentSpec 中指定。**判别档 ≥ 生成档是硬约束**（structure.md §7.5）：judge 配置解析时校验。

**D-20 N 自适应 fan-out（初始规则版，后续走 bandit 校准）：**
U = 0.4×历史返工率 + 0.3×领域新颖度 + 0.3×R级权重；U<0.3→N=1，0.3–0.7→N=3，≥0.7→N=6；R3 或新颖度>0.8 强制 N≥3；N 硬顶 8（schema/wave.py MAX_FANOUT）。R3 禁早停。采纳 tco-optimization-research L1/L2，L3（在线 bandit）列为 M3 提案项。

**D-21 缓存纪律：** 系统提示+spec 恒定段置顶为永久前缀，动态内容置尾（context-management-research）；judge/builder/verifier 不共享 KV cache/session（ContextEngine session_id+context_id 天然隔离，D-23 复核）；holdout 与 rubric 永不进 builder 前缀。

## E. 信息不对称与记忆

**D-22 三层强制：** ① 消息层 `assert_information_asymmetry`（schema/envelope.py，已测）；② 文件系统层 holdout 独立仓 + builder 沙箱 Landlock deny（D-04/D-05）；③ 上下文层 builder 的 system prompt 只含 spec(L1/L2/L3)+接口面+自测指引，holdout/rubric 由 architect 持有、verifier 执行。H3 附加泄漏扫描（实例文本中出现 holdout id = 直接失败，h3_holdout.py 已实现）。

**D-23 记忆纪律：** 临时 builder 团队 `lifecycle: temporary`（jiuwenswarm config modes.team.jiuwen_team.lifecycle），不触发记忆提取（config.yaml:L1348 语义）；实现细节入 TEAM_MEMORY 必须经判别侧（spec moderator）裁定后由持久团队 leader 写入（agent-core SharedMemoryManager 仅 leader 可写：openjiuwen/agent_teams/memory/manager.py:L335）。

**D-24 生成者/判别者模型关系三查（judge 配置校验器实现，WP6）**：不同模型、非蒸馏后代、不同家族；至少一名判官跨厂商。

## F. 演进与治理

**D-25 演进通道 = SkillEvolutionRail(auto_save=False) + EvolutionApprovalRuntime + RuleProposal(C13)。** 所有判别侧/编排侧在 session 内冻结（structure.md §10）；deep agent 只提案；批准与生效分离（`may_apply(current_session)` 语义已测）。

**D-26 波次 = 接口冻结窗口 + spec-delta 割集 + 准入事务边界。** 波次内接口面（C05 ContractSurface）冻结；跨波次变更走 H4。波次事务：SwarmFlow journal 为检查点，准入=分支合并提交点，失败=回滚到 journal 检查点 + 丢弃实例 worktree（实例可丢弃，世界不可脏写）。

**D-27 降级触发直接采纳 structure.md §13 五条件，机械判定在 `metrics.evaluate_downgrades`（已测）；降级=回退迁移阶段，不改判据。**

**D-28 spec 并发写控制（M0–M1 简化版）**：spec 写者仅 spec steward/moderator 两角色 + 人类，经 git PR 串行；条款级租约锁与 MVCC（spec-concurrency-research 方案）推迟到实测出现并发冲突再引入——当前写者数量使该复杂度不成立。

## G. 研究结论采纳/否决总表

| 研究域 | 采纳 | 否决/推迟 |
|---|---|---|
| oracle_ci_gate_research | 机械 oracle 独立于 agent 影响力；FAIL_TO_PASS/PASS_TO_PASS；holdout 轮换；judge 仅软否决；有效断言计数；merge queue 先测后合 | 纯 AI 评审作合并门禁；提示词劝告作门禁；PR-Agent（AGPL+维护放缓）；pytest-semantix 等单点工具进生产关键路径 |
| r3-golden-output-research | 双轨黄金+独立判据；人工批准更新；.r3info manifest；SPRT 统计判定思想用于 M2 flaky 治理；差异三分类分诊 | CI 自动写黄金；"3 次全绿即证据" |
| spec-traceability-bi-sync | seal 哈希层+结构规则层进门禁；增量触发；漂移分级处置（阻断/降级/豁免审计）；双向同步六判据（本计划只允许 spec→code 单向再生，code→spec 只产提案） | LLM 语义漂移检测进关键路径（M2 后旁路）；自动 code→spec 回写 |
| spec-concurrency-research | Git 分支+结构化合并 MVP；波次=事务边界；breaking 一律人工 | CRDT 主路线；Temporal/TiKV 数据面（推迟）；条款级锁（推迟，D-28） |
| llm-as-judge-research | 多采样+结构化判词；偏置控制（匿名/交换顺序）；弃权机制；校准集 kappa≥0.6；禁自评；判官≥builder 档 | 单一 judge 放行；高分量表（用 veto/no_veto/abstain 三值） |
| tco-optimization-research | U 值三路信号定 N；档位路由表；前缀缓存纪律；预算门禁；成本计入缓存折扣 | 直接照抄论文降本阈值（必须自校准）；模型池>3 档 |
| 信息不对称协议研究 | holdout 物理隔离+泄漏扫描；可信编排器中继（verifier 只回传降维反馈）；模型关系三查；边界靠应用层硬编码而非提示词 | TEE/机密计算（当前环境不可用，列为 M3 提案）；水印取证（推迟） |
| code-search-agent-research | cartographer = MCP 检索打底 + agentic 兜底（不做纯探索子agent）；返回契约 file:line+证据+最小依赖闭包；检索结果尾部追加保前缀缓存；SHERLOC 式失败定位→修复交接 | 纯子 agent 隔离搜索（46.2% 正确率证据） |
| context-management-research / llm-context-management | spec 恒定段置顶、delta 尾部注入；context_id 隔离；子 agent 上下文预算裁剪；DACS 式摘要注册表用于 TEAM_MEMORY 注入 | spec 全量静态注入（消融证据：无增益+成本↑） |
| 差分测试/Spec 形式化（顶层研究） | 执行差分为主判据；覆盖率反馈式输入生成；Hypothesis 属性测试；pre/post 断言式契约作为 L2 可执行条款的最小形式；dontcare 显式一等公民 | TLA+/Alloy 全量形式化（当前团队技能与收益不匹配，列为 R3 域可选增强）；oasdiff 直接依赖（契约面自研 AST 提取已覆盖 Python 面，OpenAPI 面 M2 接入） |

## H. 明确不做（本期范围外）

1. Studio 中央路由多智能体不进 swarm 内核（structure.md §11 已声明）。
2. 分布式部署（pyzmq+A2X+PG+NFS）不进入本期；`team.runtime.mode=local`。
3. relay / jiuwensymbiosis / agent-tools / agent-protocol 的 C++ 部分不参与本期开发面（仅在 D6 试点需要时引用其能力清单）。
4. 不修改任何 submodule 源码；对 openJiuwen 的需求缺口一律以"扩展包 + 提案"方式处理（extension SDK / Rail 热插拔 / entry-point），缺口清单见 01_architecture.md §6。
