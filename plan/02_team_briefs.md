# 团队任务书（T1–T12）

> 通用纪律（所有团队）：
> 1. 契约唯一来源 `swarmdev/contracts/`；跨包交互只走信封/schema，禁止旁路；
> 2. 本包测试不依赖网络与真实 LLM（用确定性假件）；跑 `python3 -m pytest swarmdev/tests -q` 保持全绿；
> 3. 不得放宽判据；不得给 builder 角色加能力；不得让 CI 自动写黄金输出；
> 4. 交付 = 代码 + 测试 + 契约兼容证明（与 swarmdev 的往返序列化测试）。

---

## T1 ｜ Spec 仓与治理服务
**输入**：`01_CONTRACTS.md` §1–2；research `03_Spec版本化.md`、`spec-traceability/advice_Q1`。
**产出**：
1. `specrepo/` 仓目录规范：`specs/<domain>/<spec_id>.md`（ADR-1 格式）+ `registry/r_artifacts.yaml` + `deltas/<delta_id>.json` + `sidecar/contract_hashes.json`。
2. CLI `specctl`：
   - `specctl lint <file>`：frontmatter/semver/条款 ID/dont_care 引用/见证绑定义务检查（复用 `SpecDoc` schema 反序列化即完成大半）；
   - `specctl delta <old> <new>`：生成结构化 `SpecDelta`（条款级增删改+BC/NBC 归类），写 `deltas/`；NBC 无 `requires_human_approval` 即失败；
   - `specctl hash-record <file>`：写契约哈希 sidecar（复用 `swarmdev.drift.contract_hash`）。
3. 服务化（M1）：git 钩子在 spec 分支强制执行 lint+delta 校验；spec 变更广播 spec-delta 事件（信封 `SPEC_CONVERGENCE` 前置）。
**验收**：试点域全部 spec lint 零错误；构造 NBC delta 未带批准字段→CI 红；BC delta 误升 major→红。测试放 `swarmdev/tests/specrepo/`。
**依赖**：无。**禁改**：contracts schema（要改先走契约变更流程）。

## T2 ｜ 门禁引擎与 CI
**输入**：`swarmdev/gates/*`（参考实现即基线）、`03_CI_GATES.md`。
**产出**：
1. 生产 GateRunner 封装：命令白名单化、超时、日志落 `evidence_refs`；jiuwenbox 沙箱适配（可用则沙箱跑 H1–H3，不可用按 `best_effort` 降级并在收据注明 `sandbox:off`——证据锚点 `jiuwenswarm/jiuwenbox/.../landlock.py:25`、policy `compatibility` 字段）。
2. CI workflow 模板（`.github/workflows/` 已有 swarmdev 版）：PR 级全门、夜间批处理（LLM 语义漂移层，T7 交付）、merge queue 阻断配置；分支保护：oracle/测试/CI 定义文件走 CODEOWNERS 独占（architect+human），builder 身份无写权限。
3. OwnershipGuard 生产化：oracle 文件哈希清单入库；H2 前后校验（已实现，补 CI 缓存与清单刷新流程）。
**验收**：8 门在 CI 全跑；注入"builder 改 oracle 文件"用例必红；沙箱缺失时降级路径有回归测试。
**依赖**：T1（spec 引用）。

## T3 ｜ Oracle 服务（holdout vault + 校准）
**输入**：`swarmdev/oracle/*`；research `llm-as-judge`、`信息不对称 05`、`oracle_ci_gate 最终建议`。
**产出**：
1. holdout vault：`OracleBundle` 独立 git 仓（与实现仓分库分权限），读取一律经能力令牌（`HoldoutStore` 语义）；轮换协议：`rotate(new_scenarios, epoch)` epoch 单调；场景 3 个月退役、月度新增；canary 场景（带水印输入）用于泄露取证，只抽查不作验收。
2. 场景运行服务：`ScenarioRunner` 包成常驻 worker（队列制，verifier 专属身份）；超时/资源限额；结果写 `GateOutcome.evidence_refs`。
3. 校准例行：金标集 50–100 条入库（`CalibrationItem`）；`JudgeCalibrator` 每次 judge 模型/prompt/rubric 变更强制重跑；κ<0.6 ⇒ 发 `DRIFT_ALERT` 同级的软门禁停用事件（信封走 leader→human），**禁止放宽判据替代**。
4. judge 面板：同档位多次采样为默认；跨厂商面板仅高风险争议启用；pairwise 一律交换顺序双跑。
**验收**：builder/leader 令牌读 vault→CapabilityError（复用已有测试）；κ 计算对拍已知值；轮换 epoch 回退被拒；canary 命中能定位泄露会话。
**依赖**：T1。

## T4 ｜ 差分测试与黄金输出
**输入**：`swarmdev/oracle/diff_engine.py,golden.py`；research `r3-golden-output`、`04_经典差分测试`、`03_测试输入生成`。
**产出**：
1. 输入生成器三件套（插在 `DifferentialGate.input_factory` 位）：a) 种子化随机；b) Hypothesis 属性驱动；c) 覆盖率引导（试点域先用语句覆盖，平台期再上符号执行补反例——仅 R3 关键路径）。
2. 统计通道：预算内重采样 + SPRT 三值判定（α=0.05/β=0.10），INCONCLUSIVE 不默认通过，升级人工（以 `GateStatus.INCONCLUSIVE` 表达）；低频 flaky 检测放夜间。
3. 黄金审批流：`GoldenStore.save` 的 `approved_by` 必须由人类身份签发（接 T12 的审批 UI/CLI）；manifest 记录 spec_hash/seed/lock_hash；期望基准与现状快照分目录；waiver 登记（期限+责任人）入库。
4. 非确定性控制：同种子重放不一致即 FAIL；`.r3info` manifest 不一致则比对无效（BLOCKED）。
**验收**：注入行为差异（e2e 的 silence_impl 模式）必被检出；黄金无审批保存被拒（已有测试）；SPRT 仿真数据判定正确率达标。
**依赖**：T3。

## T5 ｜ 准入与波次服务
**输入**：`swarmdev/admission/*`；PDR §9；research `spec-concurrency`（起步基线=Git 分支+breaking 门禁，不上 Temporal）。
**产出**：
1. orchestrator 服务化：`AdmissionOrchestrator` 包成常驻服务；builder_factory 对接 jiuwenswarm 临时团队（`lifecycle=temporary`，T6 交付适配层）；波次状态持久化到 sqlite checkpointer（`CheckpointerFactory type=persistence, db_type=sqlite`，锚点 `agent-core/.../checkpointer.py:60`），事件断点可续跑（`interrupt_agent_execute` 语义对接人类中断）。
2. 准入提交：COMMITTING = git merge（原子）+ 收据归档 `receipts/<wave>/`；ROLLED_BACK = 丢弃实例目录 + 分支删除；**收据永久保留**（含失败波次）。
3. 并发控制（起步版）：同域波次串行（锁=spec 分支占用）；跨域并行；接口冻结窗口 = 波次 epoch，builder 只能读冻结面（H4 快照）。
4. 回滚演练脚本：构造已 COMMITTED 的前向修复流程（不回滚已提交，宪法语义）。
**验收**：e2e 六场景服务化复跑全绿；杀进程后波次可从 checkpointer 续跑；并发两波次同域必串行。
**依赖**：T1,T2,T3。

## T6 ｜ 角色与团队 harness（openJiuwen 装配）
**输入**：`swarmdev/teams/harness_map.py`（绑定表即施工图）；侦察证据见主计划 §1.3。
**产出**（按角色装配，全部经 jiuwenswarm/agent-core 现成机制）：
1. leader：`TeamManager` 持久会话团队；只编排（tools 白名单=任务/消息工具族，锚点 `agent-core/.../tool_task.py`、`tool_message.py`）。
2. architect：DeepAgent(TaskLoop)+Workflow 嵌套；持有 vault 读权限；产出 WAVE_PLAN 信封。
3. builder：临时团队 fan-out；`permissions.tools` 按 `config.yaml:895+` 收紧（bash=deny、只读检索=allow）；无 vault 凭据（Auth Proxy 层面拒绝，不靠提示词）。
4. verifier：`WorkflowAgent` 固定流水线（节点=H1..H8+S，条件分支仅允许"失败短路"，不允许"跳过"）。
5. judge：verifier 工作流内节点，经 IntelliRouter 指定档位（`IntelliRouterModelClient`）；`TierAssignment` 校验在装配期执行。
6. spec moderator/steward：持久 DeepAgent；**TEAM_MEMORY 写入只经其手**（利用 `manager.py:340` 的 role 检查，把 builder 角色固定为非 leader）。
7. reconciler/moderator：cron 拉起的一次性 DeepAgent。
8. deep agent：`SkillEvolutionRail(auto_save=False)` + `EvolutionApprovalRuntime` 接人类批准 UI。
9. cartographer：TaskTool 子代理（见 T8）。
**验收**：临时团队解散后无记忆提取记录（auto_extract 关闭可查）；builder 会话日志不含 holdout 内容（审计脚本）；verifier 工作流无跳过分支（IR 静态检查）。
**依赖**：T2,T3。

## T7 ｜ 漂移服务（H7 生产化）
**输入**：`swarmdev/drift/*`；research `spec-traceability`（漏斗编排）。
**产出**：
1. reconciler 服务：定时（心跳）跑 `DriftDetector`（哈希层+标签层）→ `DRIFT_ALERT` 信封；修复时延计时入指标。
2. H7 入 CI：PR 级只跑哈希+标签（秒级）；夜间批处理加 LLM 语义层（只对可疑切片，DocPrism 式 incompleteness/incorrectness 二分，误标分流）。
3. RTM 双轨起步：硬轨=`@REQ-CL-xx@` 标签规范（已实现扫描器）；软轨（LLM 恢复候选链接）M2 再上。
4. 处置分级：advisory→告警；hard→阻断合并（先 A/B 两周校准误报率再转硬阻断）。
**验收**：注入未知标签/偷改条款（不动版本号）必被拦（已有回归测试）；告警→修复时延报表可出。
**依赖**：T1。

## T8 ｜ Cartographer（代码寻址 agent-as-tool）
**输入**：research `code-search-agent 最终报告`（BM25+结构检索 > 纯 agentic 探索；语义搜索 65.2% vs agentic 46.2%）。
**产出**：
1. MCP 检索服务器（≤3 工具）：`code_search`（BM25 word 级、32–64 行 chunk）、`symbol_locate`（ripgrep 精确兜底）、`impact_graph`（依赖图多跳）。
2. 增量索引：按 commit SHA 触发、只对变更函数重算；暴露索引滞后量（stale_warning）。
3. 返回契约：`{file, line_range, confidence ∈ EXTRACTED|INFERRED|AMBIGUOUS, snippet, budget_truncated}`；原始片段为主、摘要为辅；两档预算（签名层/全文层）。
4. 接入：主链路以 agent-as-tool 调用（`DeepAgent.create_subagent`），内部多轮轨迹不回主上下文；档位 L。
**验收**：试点域定位任务命中率基线≥阈值（自建 20 题评测集）；主链路前缀缓存命中率不降（cached_tokens 监控）。
**依赖**：T6。

## T9 ｜ 指标与健康度
**输入**：`swarmdev/metrics/health.py`；PDR §13。
**产出**：
1. 采集：波次事件流（信封审计日志即数据源）→ 闭合度、spec 熵事件数、判据覆盖率、逃逸缺陷率（人工标注回灌）、漂移率、judge κ、单位准入成本（token 三档计价：缓存读 0.1×/写 1.25×/普通 1×，cached_tokens 单列）。
2. 降级触发器自动化（三条已实现，补两条）：κ<0.6→软门禁停用；闭合度<阈值→降自治；漂移风暴→冻结 fan-out 转 B 标定流水线；成本超基线 3 倍→告警+降 N；oracle 反复冲突→升级人类议题。
3. 人类报告面：只报 L1/L2 相关、改进提案、健康度评分（PDR §9 负面清单：不含代码 diff、实例选择、RU 升降档）。
**验收**：五触发器各有注入测试；报表样例经 human 角色信封送达。
**依赖**：T5。

## T10 ｜ 试点域收割（M0，brownfield）
**目标域**：`agent-tools/packages/infer_router` 的 `routing/` + `config/`（ADR-13）。
**产出**：
1. spec 收割：cartographer+spec steward 从现有代码收割 L1/L2（全部条款初始 `validation_state=draft` → 逐条走 parsed→model_checked→human_confirmed 闭环）；既有行为写成**约束条款**并标 R1（PDR §4.4：世界既有行为不构成真值，构成约束，写回 spec 才生效）。
2. holdout 场景库 v1：覆盖路由决策/熔断/配置解析的关键路径（≥20 场景，先确认"如预期失败"再固定）。
3. 门禁上线：H1（compile+类型）/H2（现有 pytest）/H4（surface 快照基线）/H7（标签+哈希）在 infer_router 仓 CI 生效。
4. 漂移基线：收割完成即录契约哈希，此后改动必须带 spec-delta。
**验收**：判据覆盖率（有见证条款占比）≥0.8；unverifiable 清单经人类确认；连续 1 周 H7 无误报风暴。
**依赖**：T1,T2,T7。

## T11 ｜ 规则变更提案通道（deep agent）
**输入**：`SkillEvolutionRail(auto_save=False)`、`EvolutionApprovalRuntime`（锚点见主计划 §1.3）；PDR §14.8。
**产出**：
1. 提案器：监测逃逸缺陷/档位需求/返工率异常 → 生成 RULE_PROPOSAL 信封（含案例证据链）。
2. 批准流：人类批准 → 新 session 装载（session 内冻结纪律：判据/判别侧不变，PDR §10）。
3. 案例库：所有例外产生后果后强制入库（案例→规则的唯一通道）。
**验收**：auto_save=True 配置被装配期拒绝（策略检查测试）；未经批准的提案不影响任何运行中 session。
**依赖**：T6。

## T12 ｜ 运行手册与上游同步
**产出**：部署手册（单机拓扑端口表/环境变量）、runbook（降级演练、轮换操作、回滚演练、judge 重校准）、CAPABILITY_MAP 锚点复核脚本（上游 submodule 升级时自动跑行号核对）。
**验收**：按手册可在全新机器 30 分钟内拉起 M0 全栈；一次完整降级演练有记录。
**依赖**：T1–T11 文档输入。
