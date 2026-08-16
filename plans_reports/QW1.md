# QW1 工程计划文档集总结报告

> 本报告基于 `/workspace/plans/QW1/plan/` 目录下 10 个 markdown 文档逐文件读取整理而成。
> 内容忠实原文，关键决策引用原句并注明出处文件（文件名 + 章节）。
> 若某维度在某文档中无对应内容，则标注"无"。

---

## 1. 目标与核心范式

### 1.1 总体目标（00_总览.md）
- 标题即点明目标："openJiuwen 开发型 Agent Swarm 工程计划"，且声明"本计划是 structure.md（PDR-001『Spec-as-Source 为本体、门禁与事务为物理层』）的唯一落地文件"（00 文档引言）。
- "前提约束全部来自 PDR-001，本文档不再重复论证范式，只给出工程实现"（00 文档引言）。
- 参考实现为 `swarm-kernel/`（"已实现并通过 86 个测试，执行团队以它为契约权威与验收基准"）（00 文档引言）。

### 1.2 Spec-as-Source 范式（00 / 01 / 05 文档）
- 系统分层（00 文档 §2，与 PDR-001 §4 对齐）五层：
  - 第0层 宪法 → `constitution.yaml`（"自然语言不变量 15 条 + judge 可引用"）
  - 第1层 Spec → spec_repo（"L1/L2/L3 三层条款、稳定ID、条款摘要、R级、don't-care 区"）
  - 第2层 Oracle → oracle 目录（"holdout 场景库 + 语料生成器 + 基线契约面 + rubric（对 builder 不可见）"）
  - 第3层 Instance → "builder fan-out 产物（staging/ 下，可丢弃）"
  - 第4层 World → "已准入代码库（world/ 下，携带 EVIDENCE.json + 账本）"
- 物理实现一律遵守（00 文档 §2）："`Admit = H1..H8 全 PASS ∧ judge 不否决`；`inconclusive/error 一律不准入`"。
- M0 阶段范式前提（08 文档 M0）："真值事实上在代码，目标：建立 spec 与基础门禁"——即先收割 spec，再以 spec 为真值源。

### 1.3 PDR 层级（PDR-001 决策记录体系）
- 范式决策记录位于 `structure.md`，状态"已锁定，不再重开"（00 文档 §1 交付物地图）。
- PDR-001 是唯一范式来源，各计划文档反复引用其章节：PDR-001 §4（系统分层）、§7（信息不对称）、§10（12 角色）、§11（物理拓扑/local 优先）、§12（迁移梯度与"代码可丢弃"）、§13（降级触发器）。
- "不得跨阶段。在 oracle 覆盖率不足的域宣布『代码可丢弃』是本范式唯一致命误用（PDR-001 §12）"（00 文档 §4）。

### 1.4 宪法（宪法护栏）
- 宪法 = 第0层，`constitution.yaml`，"自然语言不变量 15 条 + judge 可引用"（00 文档 §2）。
- 宪法机械化投影：agent-core Guardrail（RiskLevel→CRITICAL AbortError）+ Rails；"H6 策略集落 Guardrail 配置"（00 文档 §3、01 文档 §1 缺口表）。
- 07 文档 §2 将宪法条款与测试锚点绑定：如 §3 门禁必含机械见证、§4 硬门禁优先代数、§5 生成≠判别、§9 多实例差异必须被解释、§10 漂移默认缺陷、§11 R3 禁丢弃重采样、§12 准入原子+证据+可回滚、§13 可丢弃主体不写记忆、§14 判别档位≥生成档位。

---

## 2. 系统组成模块清单

### 2.1 交付物地图（00 文档 §1）
| 交付物 | 位置 | 作用 |
|---|---|---|
| 范式决策记录 | `structure.md` | 已锁定的范式来源 |
| 参考内核（契约/门禁/oracle/差分/准入/测量/judge） | `swarm-kernel/` | 契约权威与验收基准，已实现+测试通过 |
| CI 门禁工作流 | `.github/workflows/swarm-kernel-gates.yml` | 门禁 CI，已实现+本地验证 |
| 门禁集成脚本 | `ci/run_all_gates.sh` | 本地门禁演示/断言，已实现+本地验证 |
| 玩具契约域 fixtures | `swarm-kernel/fixtures/` | "可复现验收基准" |
| 工程计划文档集 | `plan/` | 本文档集 |

### 2.2 新建/复用组件总表（00 文档 §3）
| 组件 | 复用 | 新建 |
|---|---|---|
| 角色载体与编排 | jiuwenswarm 声明式装配（swarm/assembly.py）、agent-core AgentTeams/TeamRuntime | 各角色 harness 配置（04 文档） |
| 临时 builder fan-out | jiuwenswarm `lifecycle: temporary`（只读父记忆、销毁不留痕） | fan-out 编排策略（N 自适应） |
| 波次事务与续跑 | agent-core Session/Checkpointer/PersistenceCheckpointer | wave 事务封装（swarm_kernel.pipeline + 账本） |
| 上下文隔离 | ContextEngine session_id+context_id | bus session_scope 强制校验 |
| 硬门禁 | —（"不用自主 agent 决定跑不跑"） | swarm_kernel.gates（H1–H8，WorkflowAgent 式确定性流水线） |
| 软门禁 | IntelliRouter 档位 | swarm_kernel.judge（judge workflow + 校准集） |
| 记忆治理 | TEAM_MEMORY.md 四分类、SharedMemoryManager 单写者 | 记忆写入裁定通道（spec moderator 批准） |
| 宪法护栏 | Guardrail（RiskLevel→CRITICAL AbortError）+ Rails | H6 策略集落 Guardrail 配置 |
| spec↔code 漂移 | — | swarm_kernel.spec_repo/drift（锚点哈希制） |
| 演进受控 | dev_tools.tune、SkillEvolutionRail（auto_save=False） | RuleProposal 通道（swarm_kernel.contracts.evolution） |

### 2.3 范式要素 → 框架承载 → 缺口映射（01 文档 §1）
- 临时 builder fan-out：openjiuwen 承载为 jiuwenswarm `lifecycle: temporary`（config_loader.py、remote_member_bootstrap.py teardown wrapper、session_metadata.py 清理）；新建 `FanoutRequest/InstanceSubmission` 契约。
- 判别侧记忆沉淀：SharedMemoryManager、extractor.py `[decision]/[lesson]/[member]/[context]` 四分类单写者；新建"记忆写入须经判别侧裁定的裁定通道（总线 ACL 已建 MemoryWrite 规则）"。
- 宪法机械化投影：Guardrail + Rails；新建 H6 策略集→Guardrail/Rail 配置表。
- 确定性门禁流水线：WorkflowAgent/PregelGraph；新建 H1–H8 gate runner（生产化时挂 WorkflowAgent）。
- 波次事务边界：Session/Checkpointer/InteractiveInput；新建准入账本+原子提交+回滚（swarm_kernel.admission）。
- 上下文隔离：ContextEngine（session_id+context_id 池）；新建 ContractEnvelope.session_scope 强制。
- 编排与通信：TeamRuntime（Card+Provider、P2P/PubSub、task_* 工具）、SwarmFlow；新建波次 DAG 事件协议。
- 模型档位：IntelliRouterModelClient、allocator.py；新建静态档位映射表 + Oracle 失败驱动升档。
- 演进受控：SkillEvolutionRail（auto_save=False）、dev_tools/tune、rsi/auto_harness；新建 RuleProposal 通道。
- spec/DSL-IR 同构：agent-studio DSL→IR（IRAdapter.java → ir_converter.py）、版本-发布-回滚；新建"spec 仓自身（不依赖 Studio）"。
- 代码定位隔离缓冲：Agent-as-tool/TaskTool、deepsearch search_tools；新建 cartographer 返回 schema 契约（紧凑 JSON ≤150 token 结论 + file:line 定位）。
- 沙箱与推理隐私：jiuwenbox（bubblewrap+Landlock+seccomp+Inference Privacy Proxy）；新建 builder 沙箱策略（禁网、只读 oracle 拒绝挂载）。

---

## 3. 架构选择

### 3.1 通信方式：总线/事件/契约（00 / 01 / 02 / 06 文档）
- **进程内 ContractBus**（pub/sub + ACL + 审计）；跨进程 **FileRelay**（NDJSON，topic→文件）（02 文档 §1）。
- 消息统一封装为 **ContractEnvelope**（base.py），字段含 envelope_id、schema_name、schema_version、producer_role、consumer_role?、topic、session_scope、confidentiality、ts、payload、payload_sha256；`seal()` 计算 payload canonical sha256，接收方 `verify_seal()` 破损即拒收（02 文档 §1）。
- 全局铁律（00 文档 §6）："所有跨组件消息走 ContractEnvelope（带封条哈希与保密级）；绕过总线直传 = 违反隔离纪律，测试会失败"。
- 事件驱动：leader 持久团队"事件订阅(MonitorEventType)"、create_task/send_message（01 文档 §2 物理拓扑）；"波次 DAG 事件协议（04 文档角色间消息契约）"（01 文档 §1）。
- 物理拓扑（01 文档 §2）："单机：`team.runtime.mode=local`，inprocess transport；分布式（pyzmq+A2X+PG+NFS）M3 之后再评估"；"每角色独立 context_id（ContextEngine），总线 session_scope 与之一致；跨域订阅必须显式通配并接受审计"。
- session_scope 约束："必须等于订阅方域，或订阅方显式 `*`（仅 reconciler/观测类允许）"（02 文档 §1）。
- 契约即团队边界："跨团队交互只允许使用本文列出的契约消息；字段增删 = 规则变更提案"（02 文档引言）。

### 3.2 信息不对称实现（06 文档，PDR-001 §7）
- 总纲原句："信息不对称是硬约束，不是礼仪"（06 文档引言）；"reward hacking 的信息前提 = builder 能看到判据。消除前提即消除该类攻击面"（06 文档 §1）。
- 核心不变量："View(builder) ∩ View(verifier 判据) ⊆ 公开集（spec L1/L2/L3 + 接口面 + 自测框架）"（06 文档 §1）。
- 存储隔离矩阵（06 文档 §2）：spec 可见（全量）；接口冻结面可见；holdout 场景库 / 差分语料生成器 / rubric / 黄金输出 / 判词逐样本明细对 builder **deny**；mock 场景集可见。
- 落地手段（06 文档 §2）：文件系统（jiuwenbox 挂载策略对 oracle 目录整体 deny + rail 级二次拦截 Guardrail HIGH→AbortError）；工具白名单（builder 无 oracle 检索工具；cartographer 对 oracle 路径返回"不可见"而非内容）；进程级（holdout 只注入 verifier workflow 上下文，独立 context_id，不进共享记忆）。
- 注入点与中继净化（06 文档 §3）：builder→编排器仅 InstanceSubmission（"CoT/中间产物留在沙箱内，随临时团队销毁"）；编排器→judge 用脱敏后的提交摘要（JudgeWorkflow._sanitize 去除 builder_identity/chain_of_thought/timestamps，匿名化默认开）；judge→builder 仅聚合结论（通过/否决+条款级原因）。
- 保密级（06 文档 §4 / 02 文档 §2）：public / holdout / judge_internal / memory_restricted 四级；holdout 可读者为 verifier、architect、system、human；judge_internal 可读者为 verifier、architect、system；memory_restricted 可读者为持久角色（临时 builder 禁读）。
- 生产者约束（06 文档 §4）：JudgeVerdict 生产者 ∈ {verifier}；MemoryWrite 生产者 ∈ {spec moderator 裁定后}。
- 双流水线隔离（06 文档 §5）：B 标定线"独立 leader、独立记忆域、独立 session 前缀；B 线 builder 同样不见 A 线 holdout"；"B 线成功定义 = 学到沉默/分歧位置；代码全部丢弃，只产出 spec-delta、oracle 补强、案例记录（账本断言：B 线无 admission 记录）"。
- 审计：bus 审计日志记录每次投递与拒绝；拒绝事件入 EventLog(kind=isolation_denial)；"每周健康度报告包含 isolation_denial 计数；非零值必须逐条归因"（06 文档 §6）。
- 已知边界与代价（06 文档 §7）：本地单机下 deny 依赖"沙箱与纪律双重保障"；TEE/机密飞地"暂不采纳"（保留 KMS+审计作 M3 备选）；MPC 判官、水印溯源"不采纳（过度设计）"；判官面板仅高风险判定启用，默认单判官多采样。

### 3.3 角色 Harness 如何配置（04 文档）
- 12 角色 = PDR-001 §10 的范式函数；用 jiuwenswarm 声明式装配落地。
- 团队拓扑（04 文档 §0）：
  - 指挥团队：persistent，leader、architect(过程)、verifier(workflow)，团队记忆（只读继承给临时团队）
  - spec 治理团队：persistent，spec steward、spec moderator、reconciler，独立记忆域
  - 交付 builder 群：**temporary**（每波次即散），只读父记忆、无 TEAM_MEMORY、销毁不留痕
  - 标定 builder 群：temporary（B 流水线专用），与 A 线不同 leader/记忆域
  - 辅助：agent-as-tool，cartographer，无记忆
  - 后处理：独立会话，refactor、moderator，不写实现记忆
  - 演进：rail+提案器，deep agent，只提案
- 逐角色要点（04 文档 §1）：leader（persistent、code.team、工具白名单、禁 judge/spec 写/holdout 读，档位中高 RU-M/H）；architect（DeepAgent 外层 TaskLoop+create_subagent、写 oracle 场景与 rubric、持 holdout 全量、RU-H 预路由锁定）；builder（temporary、输入仅 spec+接口冻结面+本地自测、无 holdout/rubric/端到端场景、RU-M、oracle 失败升档≤2 次、禁记忆写/judge/spec 写/与 builder 通信）；verifier（WorkflowAgent 确定性流水线 H1→H8→judge、持 holdout+rubric、产出 GateSuiteResult/ScenarioOutcome/JudgeVerdict、judge 档位≥builder 档位）；spec moderator（L1、触发 MeasurementEvent silence/divergence、登记 DontCareDeclaration、MemoryWrite 唯一合法生产者）；spec steward（L1、spec 仓维护、L2 diff 呈报人类、NBC 必须人类批准）；reconciler（L1–L4 定时/心跳、drift scan、session_scope=`*` 唯一通配订阅者之一）；cartographer（TaskTool 弱档 RU-L 高缓存、返回紧凑 JSON≤150 token、连续失败升 RU-M≤1 次）；critic（红队、产出新场景提案进 oracle 由 architect 审入、不直接改代码）；refactor（准入后独立会话重写 R0/R1、契约面不得改变、必须过 H4+H5）；moderator（可读性治理、产出 spec-delta 提案或 refactor 请求）；deep agent（产出 RuleProposal 状态 draft → 人类批准 → 新 session 装载，当前 session 恒不生效）。
- 隔离矩阵配置断言（04 文档 §2，T7 必须写成测试）：①builder 白名单无 oracle 路径读取 + 文件系统 deny（Guardrail HIGH→AbortError）；②builder 无 send_message 到 verifier/judge topic 权限；③judge workflow context_id ≠ 任何 builder context_id；④临时团队 teardown 后会话目录/A2X 预约/blank card 全部回收；⑤RAIL_WHITELIST 之外 rail 不得注入成员。
- 模型档位表（04 文档 §3）：RU-H = architect、judge(verifier 内)、spec 会诊（预路由锁定不级联）；RU-M = builder（默认）、leader、spec moderator/steward（oracle 失败升档≤2 次）；RU-L = cartographer（连续失败升 RU-M≤1 次）。成本口径："计入缓存有效成本；以『成功调整后单位准入成本』评估（健康度 admission_cost_tokens 为其一维）"。

---

## 4. 契约定义

### 4.1 权威与范围（02 文档）
- "唯一权威：swarm-kernel/contracts"；"权威实现：`swarm-kernel/swarm_kernel/contracts/`（31 个模型，tests/contract 全量覆盖）"。
- "契约即团队边界。跨团队交互只允许使用本文列出的契约消息；字段增删 = 规则变更提案"。
- 全局铁律："契约改动 = 规则变更提案，任何团队不得私改 `swarm_kernel/contracts/`；需要改时走 RuleProposal → 人类批准 → 新 session 生效"（00 文档 §6）。

### 4.2 契约/制品清单（02 文档 §3）
- **spec 域（spec.py）**：SpecClause（clause_id、level L1/L2/L3、r_level、text、contract_body(pre/post/invariant/assume/guarantee)、dont_care[]、witness_kind/refs、status、version；digest=canonical sha256；anchor=`@spec ID #digest16`；"无见证的 active 条款=unverifiable，只能作 advisory"）；DontCareDeclaration（kind 三分类 output_freedom/unreachable_state/ignorable_output，只允许 spec moderator 登记）；SpecDoc（真值载体）；SpecDelta（add/modify/remove + BC/NBC，"含 NBC → requires_human_approval=True"）。
- **波次与 fan-out（wave.py、fanout.py）**：WavePlan（波次=接口冻结窗口+事务边界）；FanoutRequest（"**R3 强制 n=1**；n∈[1,8] 硬顶"）；InstanceSubmission（"只含 claim+证据引用，不含 CoT"）；MeasurementEvent（六分类：closed/silence/divergence/tier_upgrade/conflict/insufficient_samples）。
- **门禁与判据（gates.py、oracle.py）**：GateResult（gate_id H1..H8、verdict pass/fail/inconclusive/error、attempts、witness_refs[]、details）；GateSuiteResult（"hard_pass = 8 门全 PASS；inconclusive/error/缺门均不算过"）；HoldoutScenario（grading 二类 FAIL_TO_PASS/PASS_TO_PASS，confidentiality=holdout）；Rubric/RubricItem/BiasControls（bias：samples≥1、position_swap、anonymize、abstain_on_disagreement、min_calibration_kappa）；JudgeVerdict（kind veto/no_veto/abstain、"**无豁免字段**（schema 层禁止）；veto 无证据引用自动降级 abstain"）。
- **准入域（admission.py）**：EvidenceReceipt（complete = 硬门全过 ∧ 漂移干净）；AdmissionDecision（"admit 必附回滚句柄"）；LedgerEntry（哈希链、篡改可检）。
- **治理域（drift.py、evolution.py、health.py）**：DriftEvent/AnchorRecord（state ok/stale/orphan/unimplemented，"stale/orphan/unimplemented=阻断"）；RuleProposal（"**may_apply_current_session 恒 False**；生效必须指定未来 session"）；HealthSnapshot（closure_rate、spec_entropy_events_per_delta、witness_coverage、unverifiable_clauses、escape_defect_rate、drift_alert_rate、judge_kappa、judge_abstention_rate、rework_rate、admission_cost_tokens、stage M0-M3，"人类报告面只含这些 + L1/L2 事项"）。

### 4.3 实例打包契约（02 文档 §4，builder 交付物/H 门禁输入）
```
<instance_dir>/
  swarm_entry.py    # 适配器：def run(inputs: dict) -> Any；门禁加载器 fresh-load
  contract.json     # {"exports": [...], "signatures": {...}, "dependencies": [{"name","license"}]}
  report.json       # {"tokens": float, "seconds": float, "bytes": float}
  tests/            # builder 自测（H2）；不是 holdout
  <实现文件>         # L1/L2 条款锚点注释：# @spec REQ-XXX #<digest16>
```
缺失规则："无 swarm_entry.py → H3/H5 error；无 contract.json → H4 fail；无 report.json → H8 inconclusive；无锚点 → H7 unimplemented（L1/L2）"。

### 4.4 格式与版本化策略（02 文档 §5、§3）
- **格式**：Pydantic 模型（"Python ≥3.11；swarm-kernel 运行依赖仅 pydantic≥2.7 + pyyaml"，01 文档 §5）；"JSON Schema 导出作为跨语言消费凭据（`ContractModel.model_json_schema()`），测试 tests/contract 已对全部 31 模型做 schema 校验"（02 文档 §5）。未提及 OpenAPI。
- **版本化策略**（02 文档 §5）：①每个契约模型带 contract_version（整数），信封 schema_version 同步；②"加字段（可选）= BC；改语义/删字段 = NBC → 需 RuleProposal 人类批准，且消费方双版本兼容期 ≥1 个波次"；③JSON Schema 导出作跨语言凭据。
- spec 版本策略（01 文档 §3.1）："NBC→major、add/modify→minor、remove-only-BC→patch（已实现 versioning.py）"。

---

## 5. CI 门禁与 Oracle

### 5.1 H1–H8 每个门的具体判据（05 文档 §1，判定输入均为机械可测）
| 门 | 守护对象 | 判定输入 | 判定要点 |
|---|---|---|---|
| H1 | 构建/类型/静态 | 命令列表（默认 compileall），退出码 | 退出码 |
| H2 | 单元/属性测试 | pytest（实例自带 tests/），退出码 | 退出码 |
| H3 | 场景 holdout 套件 | ScenarioGrader，"FAIL_TO_PASS∧PASS_TO_PASS 全过" | 场景结果 JSON（见证） |
| H4 | 契约面/破坏性变更 | contract.json vs baseline + 波次冻结摘要 | removed_exports/changed_signatures |
| H5 | 差分/黄金输出 | 组内差分（seed 语料）或黄金比对 | 差分报告/快照 manifest |
| H6 | 不变量与护栏 | 密钥扫描、危险模式、禁用依赖、许可 denylist、体积 | problems 列表 |
| H7 | spec↔code 漂移 | 锚点摘要比对 | stale/orphan/unimplemented 计数 |
| H8 | 成本/资源预算 | report.json vs GateConfig 预算 | 超支维度 |

### 5.2 退出码与判定代数（05 文档 §2，"不可改"）
- "0 = pass；1 = fail（任一门 FAIL）；2 = inconclusive（含 error/缺门/缺件）"。
- "`Admit = 八门全 PASS ∧ judge 不 veto`；veto 只否决不救场；inconclusive 永不准入"。
- "优先级：FAIL 优先于 inconclusive（一门 FAIL 即整体 FAIL）"。
- flaky 策略（05 文档 §3）："确定性门禁默认单次尝试；标注 flaky 的套件最多重试至 n 次"；"Wilson 95% 区间 lower≥0.4 → pass；upper≤0.6 → fail；否则 inconclusive（n=1 按点估计）"；inconclusive 进隔离区台账（不删除），"连续 3 次 inconclusive 强制转人工分诊"。

### 5.3 Oracle 引擎能力（00 / 01 / 02 / 05 / 07 文档）
- **黄金输出（golden）**：R3 制品使用黄金库（`oracle/golden/` + manifest，"approved_by 必填"）；"CI 永不自动写黄金（GoldenPolicyError，CI=true 时 write 被拒，测试覆盖）"（05 文档 §5）；"更新流程：轨道 B（标定流水线）产出证据 → 人类评审 diff → approved_by 落 manifest → 生效"；"manifest 不一致 = 比对无效（fail-closed）；缺快照 = fail-closed"；"R3 制品禁止 fan-out（FanoutRequest schema 拒绝 n>1）"。
- **差分（differential）**：H5 门"组内差分（seed 语料）或黄金比对"（05 文档 §1）；差分语料由 oracle 私有 corpus.py `gen_corpus(seed,n)` 生成（01 文档 §3.2）；归一化（redactions 配置剥离时间戳/随机 id 等）（03 文档 T3.2）；同行为对照 good vs good2 判"无差分"、异行为 divergent_a/b 判"有差分"且定位到未定义区输入（07 文档 §3）。
- **don't-care 区**：SpecClause 的 `dont_care[]` + DontCareDeclaration（kind：output_freedom/unreachable_state/ignorable_output），"只允许 spec moderator 登记"（02 文档 §3.1）；"don't-care 一等公民三分类……'隐式默认推断脆弱，须显式标注'结论（dont_care 强制显式）"（09 文档 §10）。
- **兼容性（H4 契约面）**：contract.json 与基线契约面 + 波次冻结接口摘要比对，"removed_exports/changed_signatures"；refactor 后"契约面不得改变：必须过 H4（对比基线）+ H5（差分恒空）才允许替换"（04 文档 §1 refactor）。
- **可追踪性（H7 漂移 + 锚点）**：锚点哈希漏斗（01 文档 §3.6）"①摘要比对（stale/orphan/unimplemented）→ 硬阻断；②豁免台账（带过期审计）；③（M2+）LLM 语义复核只跑可疑切片、夜间批扫"；"起步基线全部只告警积累精度，M1 起对收割域转强制"；锚点格式 `# @spec <ID> #<digest16>`（01 文档 §3.1）。
- **强度分级（R 级）**：条款带 r_level（R0/R1/R2/R3）；R3 强制 n=1、禁早停、黄金输出+冻结清单（02 文档 §3.2、03 文档 T1.2、08 文档 M3）；R0/R1 常规 fan-out，R2 演进，R3 冻结（08 文档 M3）。
- **场景编写规范**（05 文档 §4）：expectation 支持 equals/approx(tol)/contains/json_equals 四种，其他形态=判 fail（防真空断言）；FAIL_TO_PASS 为本 delta 必须转绿场景、PASS_TO_PASS 为回归保持绿；"场景先行：spec-delta 未附场景引用前，该条款 unverifiable，只能 advisory"；oracle 独立性"禁止从实例目录加载任何判分代码"；"场景输入不得出现在 builder 可见的任何训练/示例材料中；场景库定期轮换（M2+）"。

### 5.4 门禁上线路径（05 文档 §7，先告警后阻断）
- M0："H1–H4+H7 全部以『告警模式』接入目标域 CI，积累精度基线（2 个波次）"。
- M1："收割域内 H3/H4/H7 转强制阻断；H5 对 R0 启用差分；H8 按预算强制"。
- M2+："全族强制；judge 软门禁在 kappa≥0.6 的域启用否决权"。

### 5.5 waiver 与豁免（05 文档 §6）
- "豁免只能来自 oracle/waivers.yaml（条款 ID、原因、过期时间、批准人）；过期自动失效"。
- "豁免不改判据：只是把某条款暂时移出放行依据（降为 advisory），硬门禁数量不减少"。

---

## 6. 测试策略

### 6.1 测试金字塔与目录（07 文档 §1）
| 层 | 目录 | 覆盖 | 时长目标 |
|---|---|---|---|
| 契约层 | tests/contract | 31 模型 schema/roundtrip、R3 禁 fan-out、NBC 审批、judge 无豁免字段、提案不当前生效、收据完备性 | <5s |
| 单元层 | tests/unit | oracle 判分、差分、黄金、八门、Wilson、judge、测量、准入、漂移、健康度 | <60s |
| 通信层 | tests/communication | bus ACL（holdout/judge/记忆/会话域/通配）、FileRelay 往返、篡改检测、NDJSON roundtrip | <5s |
| E2E 层 | tests/e2e | 全链路四路径：closed→准入、silence→阻断、bad→拒入、准入→回滚 | <120s |

- 原则原句："门禁与 oracle 本身必须被测试（『判据的可信度先于判据的使用』）"（07 文档引言）。

### 6.2 测试输入生成
- 差分语料生成器 `gen_corpus(seed,n)`（"含未定义区探测输入"；"种子固定可复现；覆盖 dont_care 声明的全部 scope"）（03 文档 T3.1）。
- fixtures 反例永久保留："每个门禁至少：1 正例（good 过）+ 1 反例（对应 bad 实例挡）；反例 fixture 永久保留在 fixtures/instances/"（07 文档 §4）。
- EvalPlus 式测试增强（M2 场景轮换）（09 文档 §11）；"端点保持变异（M3）：Set-Revert/Redundant-Set 型变异语料"（03 文档 T3.5）。
- judge 校准集："100–300 条人工双标；kappa 计算与门槛 ≥0.6"（03 文档 T5.3、09 文档 §4）。

### 6.3 差分测试可信度保障（07 文档 §3）
1. 同行为对照 good vs good2 必须判"无差分"；2. 异行为对照 divergent_a vs divergent_b 必须判"有差分"且定位到未定义区输入；3. 确定性：同 seed 两次运行 pairwise 与 divergent_inputs 完全一致；4. 模块缓存陷阱回归：多实例同进程加载必须 fresh-load（"test_e2e silence 路径即为该回归的守护测试"）。

### 6.4 属性测试/不变量测试锚点（07 文档 §2）
- 宪法条款↔测试绑定：§3 门禁必含机械见证（H3/H5/H7 产生 witness_refs）；§4 硬门禁优先代数（suite_exit_code FAIL 优先、veto 拒入）；§5 生成≠判别（builder 产 JudgeVerdict 被拒）；§9 多实例差异必须被解释（silence 阻断+don't-care 处置）；§10 漂移默认缺陷（stale 锚点→H7 FAIL）；§11 R3 禁丢弃重采样（FanoutRequest R3 n>1 抛错、CI 写黄金被拒）；§12 准入原子+证据+可回滚（EVIDENCE.json、账本链、回滚恢复 6 用例）；§13 可丢弃主体不写记忆（builder MemoryWrite 被拒）；§14 判别档位≥生成档位（配置断言）。
- oracle/门禁自身测试义务（07 文档 §4）：expectation 未知形态=fail（防真空）；运行异常=fail 不逃逸；Wilson 边界用例（0/0、1/1、0/3、3/3、2/3）全覆盖；账本篡改检测可复现（test_ledger_tamper_detected）；judge 位置翻转不一致→abstain、veto 无引用→降级 abstain、脱敏断言。

### 6.5 自修复/反馈循环
- 测试角度：E2E 四路径之一即"准入→回滚"；builder 产物缺件→对应门禁 inconclusive/fail，通过机制拒绝而非修复（02 文档 §4 缺失规则）。
- 系统层面反馈循环（01 文档 §3.5 测量与收敛）：MeasurementEvent 六分类处置路由固定（pipeline.run_fanout_pipeline）：closed→选实例准入（次级判据字典序最小名）；silence→冻结准入，spec moderator 登记 don't-care 或补条款后重测；divergence→spec moderator 收敛 spec，oracle 不动；tier_upgrade→升档重采样（≤2 次）；conflict→升级规范级事件（steward+architect 会诊）；insufficient_samples→补生成至 ≥3。
- deep agent 提案通道（RuleProposal）与人类批准后新 session 装载形成演进反馈（03 文档 T8.6、04 文档 deep agent）。
- 05 文档 §4 "场景先行"：条款未附场景引用前只能 advisory 不作放行依据——这是规范级自校验。

---

## 7. 交付节奏

### 7.1 phase/wave 定义
- **Phase = M0–M3 里程碑梯度**（00 文档 §4，对齐 PDR-001 §12 迁移梯度）；"不得跨阶段"。
- **Wave = 波次**：波次 = "接口冻结窗口 + 事务边界"（02 文档 WavePlan 约束）；波次状态机 "collecting→adjudicating→committing→committed"（03 文档 T8.1）。

### 7.2 M0–M3 阶段内容（00 / 08 文档）
- **M0 收割**：spec 仓建立、目标域 spec 收割、H1–H4+H7 上线（告警模式）；门槛"`ci/run_all_gates.sh` 全绿；锚点扫描对收割域 0 孤儿 0 陈旧"。
- **M1 锚定**：holdout 场景库达阈值、H5 差分门可用、R 级注册表上线；门槛"目标域每 L1/L2 条款 ≥1 硬见证（witness_coverage=1.0）；差分引擎对 fixtures 判定正确"。
- **M2 再生**：R0/R1 常规 fan-out；judge 校准上线；门槛"连续 3 波次零逃逸；judge kappa ≥0.6（对标注集）"。
- **M3 工厂**：R0/R1 默认再生、R2 演进、R3 冻结；deep agent 提案通道；门槛"健康度快照各指标进入阈值带；降级触发器全部有测试覆盖"。

---

## 8. 角色/团队分工

### 8.1 团队划分（00 文档 §5 + 03 文档全篇）
| 团队 | 负责 | 关键交付 |
|---|---|---|
| T1 spec 仓 | spec_repo、R 级注册表、版本化 | ClauseRegistry、锚点规范、SemVer 策略 |
| T2 oracle 与硬门禁 | gates H1–H8、场景库、门禁 CI | gate runner、场景判分、Wilson flaky 策略 |
| T3 差分与黄金输出 | diff 引擎、golden 库、R3 冻结 | 确定性语料、快照 manifest、批准流 |
| T4 准入事务 | admission、账本、回滚、PR 语义 | 原子提交、证据收据、哈希链 |
| T5 judge 软门禁 | rubric、workflow、校准 | kappa 校准集、偏置控制、弃权策略 |
| T6 漂移与观测 | H7、健康度、降级触发 | drift 检测、EventLog、HealthSnapshot |
| T7 swarm 角色 harness | 12 角色 jiuwenswarm 配置、信息隔离 | 角色 YAML、ACL rail、holdout 访问控制 |
| T8 波次与编排 | leader 编排、wave DAG、fan-out 策略 | pipeline 接入、N 自适应、档位路由 |

- "每个团队只解决本部分内问题；跨团队交互一律走 02 文档定义的契约"（00 文档 §5）。
- 团队依赖 DAG（03 文档末尾）："T1（spec仓）→ T2（oracle/门禁）→ T4（准入）→ T8（编排）；T1→T6；T3/T5 并接；T7 与 T2/T5 并行，集成测试依赖 T2/T5 产物"。
- 契约对所有人冻结："任何团队发现契约缺陷 → 提 RuleProposal，不得私改"（03 文档末尾）。

### 8.2 12 角色分工（04 文档 §1，详见本文档 §3.3）

---

## 9. TCO/成本优化

### 9.1 模型路由（档位映射）
- 静态档位映射表（04 文档 §3）：RU-H = architect、judge(verifier 内)、spec 会诊（预路由锁定不级联）；RU-M = builder（默认）、leader、spec moderator/steward（oracle 失败升档≤2 次）；RU-L = cartographer（连续失败升 RU-M≤1 次）。
- 档位路由（03 文档 T8.4）："预路由为主：architect→高档锁定；builder 默认中档、oracle 失败升档≤2 次；cartographer 弱档"；"路由决策日志可回放"。
- 判别侧档位约束："judge 档位 ≥ builder 档位"（04 文档 §1 verifier、03 文档 T7.6）。
- 09 文档 §7（TCO 研究）："静态档位映射 + oracle 失败驱动升档（≤2 次）"为采纳项。

### 9.2 缓存
- "前缀缓存友好布局（稳定段置顶、动态追加尾部、diff 指令）"（09 文档 §7 采纳项）。
- "会话亲和（避免模型切换冷却缓存）"（09 文档 §8 采纳项，进 04 文档 cartographer 契约）。
- cartographer "弱档位 RU-L、高缓存命中"（04 文档 §1 cartographer）。
- "成本口径 = 缓存有效成本"（09 文档 §7；04 文档 §3 同样口径）。

### 9.3 fan-out（N 自适应）
- N 自适应先验定档（03 文档 T8.3）："返工率0.4+新颖性0.3+R级0.3 → N∈{1,3}起步，硬顶8 + 早停；R3 禁早停；N 决策入 EventLog 可审计"。
- "ANLL 单样本探索、oracle 一致性早停、N∈[1,8] 硬顶、R3 禁早停"（09 文档 §7 采纳）。
- 三信号先验定档（09 文档 §7）：返工率/新颖性/R级。
- 双流水线物理隔离的 B 标定线（03 文档 T8.5）："A 交付 / B 标定两条 leader（不同记忆域、不同 session 前缀）；B 线产物全部丢弃代码、只产 spec-delta/oracle 补强（账本断言）"。
- 成本观测维度：HealthSnapshot.admission_cost_tokens；健康度阈值带"单位准入成本 ≤预算；超且闭合度未改善 → 降 N、缩再生单元"（08 文档阈值带）；"以『成功调整后单位准入成本』评估"（04 文档 §3）。

---

## 10. 验收标准与阶段推进

### 10.1 总体验收方式（00 文档 §7）
- 内核回归："cd swarm-kernel && python -m pytest tests -q（86 用例全绿）"。
- 门禁演示："./ci/run_all_gates.sh（good 过、bad/secret/drift 挡，退出码语义正确）"。
- 阶段验收："按 08 文档 checklist 逐项机械化勾选"。

### 10.2 M0–M3 机械化门槛 checklist（08 文档）
- **M0 收割**：spec/spec.json 存在且 `unverifiable_clauses()==[]`；`drift scan` 退出码 0；`ci/run_all_gates.sh` 复制成功 good/bad 0/1；H1–H4+H7 告警模式 ≥2 波次误报台账归档；12 角色 harness 装配校验通过。
- **M1 锚定**：witness_coverage==1.0；H3/H4/H7 转强制 + H5 差分对 fixtures 判定正确；准入事务上线（staging/world/账本/回滚六用例复刻通过）；信息隔离审计（oracle deny 生效、isolation_denial 归零或有归因）；judge workflow 以 scripted/离线后端跑通。
- **M2 再生**：连续 3 波次 escape_defect_rate==0；judge kappa≥0.6 且 abstain 率≤20%；closure_rate 基线建立；五条降级触发器全有回归测试；N 自适应日志可回放 + R3 禁早停断言。
- **M3 工厂**：健康度指标连续 4 周处阈值带内；RuleProposal ≥3 次闭环且无当前 session 生效事件；B 线独立运行 ≥4 周零准入；单位准入成本环比下降或稳定。

### 10.3 健康度阈值带（08 文档，起步值，两波次后校准）
| 指标 | 目标带 | 越界动作 |
|---|---|---|
| closure_rate | ≥0.6 | 检查 spec 质量与 N 配置 |
| spec_entropy_events_per_delta | ≤0.5 | 冻结 fan-out 转 B 线 |
| witness_coverage | ==1.0（已收割域） | 跌破→该域回退 M0 |
| escape_defect_rate | ≤0.02 | 超→降级触发器 1（回退阶段+额外确认） |
| judge_kappa | ≥0.6 | 跌破→软门禁停用（不影响硬门禁） |
| drift 告警密度 | 基线 ±50% | 突增且修复时延上升→漂移风暴处置（冻结 fan-out） |
| 单位准入成本 | ≤预算 | 超且闭合度未改善→降 N、缩再生单元 |

### 10.4 降级触发器（08 文档，PDR-001 §13）
1. 逃逸缺陷率超阈 → 该域回退一阶段 + 生成规则变更案例。
2. kappa 跌破 → 软门禁停用，暂停该域自动准入。
3. 漂移风暴 → 冻结 fan-out，转 B 标定流水线。
4. 成本超预算且闭合度无改善 → 降 N、缩再生单元、提档位门槛。
5. oracle 与 spec 反复冲突（同条款多次全失败）→ 升级人类规范议题。
- 原则："每阶段有机械化门槛，未达标不得进入下一阶段；降级永远是回退阶段，不是改判据"（08 文档引言）。
- 人类报告面（唯一呈报）："L1/L2 相关事项、deep agent 改进提案、HealthSnapshot 健康度评分。不含：代码 diff、实例选择、RU 升降档执行细节、个别例外"（08 文档末尾）。

---

## 11. 研究采纳决策表（09_研究采纳决策表.md）

> 定位："research/ 各研究为外脑建议；本表是采纳裁决（采纳/改造采纳/推迟/不采纳），全部给出理由"。

### 11.1 oracle_ci_gate_research → "大量采纳"
- 确定性硬门禁→统计软门禁→人工残差分层：**采纳**（"H1–H8 硬 + judge 软 + 人类只审 L2 diff"）。
- FAIL_TO_PASS / PASS_TO_PASS 判分语义：**采纳**（ScenarioGrading 已实现）。
- 首试判分、禁止自改后自评、oracle 文件生成者不可改：**采纳**（grader first_attempt；oracle ACL deny）。
- Wilson 置信区间三判定 + flaky 隔离区：**采纳（阈值改造）**（wilson_verdict(0.4/0.6)，n=1 点估计；台账制）。
- 退出码机械门禁：**采纳**（0/1/2 语义钉进 CI 断言）。
- promptfoo/DeepEval/Harbor 等现成评测框架：**改造采纳**（"不裸依赖（早期项目风险）；自建判分器，语义对齐"）。
- LLM 预言机终审：**不采纳**（"LLM 只起草/分诊，终审必须机械或人类"）。

### 11.2 r3-golden-output-research → 采纳
- 双轨制（黄金输出仅作护栏 + 独立预言机）、manifest 批准纪律、CI 永不自动写黄金、缺快照 fail-closed——"全部采纳，已实现于 GoldenStore 并有测试"。
- 分层流水线 L0–L3："L0–L2 采纳，L3 端点保持变异推迟到 M3"。

### 11.3 信息不对称协议研究 → 核心采纳，重装备推迟
- **采纳**：IAM deny + mock 分离、编排器净化中继（脱敏）、反馈降维、顺序交换/匿名化、会话隔离、View(B)∩View(V)⊆公开集不变量（已实现为 ACL+测试）。
- **推迟/不采纳**：TEE/机密飞地（"M3 评估 KMS+审计即可"）、双人密钥分存、MPC 判官、水印溯源、出口容量账本、季度行为纠缠审计（"小团队过度设计"）。

### 11.4 llm-as-judge-research → 采纳主干
- 多采样+多数投票、位置交换双跑（翻转不计/abstain）、匿名化、弃权机制、veto 必须引用证据、kappa≥0.6 上线门槛——"全部采纳（JudgeWorkflow 已实现，ScriptedJudgeBackend 供离线测试）"。
- 跨厂商判官面板仅高风险判定保留选项；alt-test 100–300 双标纳入 T5.3。

### 11.5 spec-concurrency-research → 轻量化采纳
- **采纳**：波次=唯一原子边界、暂存区+epoch、副作用二分（可缓冲/外部化/不可逆门控）、结构化合并兜底思想。
- **不采纳（推迟）**：Temporal 控制面、Percolator/TiKV 数据面、Atomix frontier 2PC——"当前写者少（steward/moderator），文件锁+提交时摘要校验足够；并发压力实测上升后再引入"。

### 11.6 spec-traceability-bi-sync-research → 采纳机制，自研实现
- **采纳**：稳定条款 ID + 行为契约段哈希 + 代码锚点绑定（SpecSeal 思想，"自研为 ANCHOR_RE + ClauseRegistry，避开其 v0.1 只支持 TS/JS 的限制"）；stale/orphan/unimplemented 三态分类；先告警后阻断渐进上线；豁免台账带过期审计；双轨 RTM（硬轨=代码锚点；软轨=LLM 恢复候选链后固化为锚点，M2+）。
- **推迟**：DocPrism LCEF 语义裁决（"需自项目 A/B 校准"）；jQAssistant/ArchUnit 结构规则（"目标域为 Python 时以锚点+H6 策略替代"）。

### 11.7 tco-optimization-research → 采纳策略层
- **采纳**：三信号先验定档（返工率/新颖性/R级）、ANLL 单样本探索、oracle 一致性早停、N∈[1,8] 硬顶、R3 禁早停；静态档位映射 + oracle 失败驱动升档（≤2 次）；前缀缓存友好布局（稳定段置顶、动态追加尾部、diff 指令）；成本口径=缓存有效成本。
- **推迟**：contextual bandit 在线学习路由（P2 阶段）、嵌入+kNN 预路由（P1 之后）。

### 11.8 llm-context-management-research / context-management-research → 采纳
- 会话亲和（避免模型切换冷却缓存）、cartographer 隔离检索层（探索轨迹不外泄、schema 化紧凑返回、失败即丢弃）、注册表引用代替快照 append——"采纳进 04 文档 cartographer 契约"。
- CORVUS/dscache 类工具"作为观测选项，不硬依赖"。

### 11.9 code-search-agent-research → 采纳混合形态
- "检索层+行为路由+agentic 兜底"混合（"而非纯探索子 agent，后者交接静默失败率高"）——采纳；BM25+chunk 基线起步；返回契约（≤150 token 结论 + file:line + 置信 + 新鲜度）已写入 04 文档；deepsearch search_tools 作为检索能力复用源。

### 11.10 spec 形式化研究（根目录 01–06 与最终报告）→ 谨慎采纳
- **采纳**：DbC 轻量断言契约体（pre/post/invariant/assume/guarantee 字段，MachineContract 已实现）；don't-care 一等公民三分类（output_freedom/unreachable_state/ignorable_output，已实现）；SemVer+BC/NBC 机器校验（versioning.py 已实现）；"隐式默认推断脆弱，须显式标注"（dont_care 强制显式）。
- **不采纳（本期）**：TLA+/Alloy/NuSMV 全量形式化（"验证成本高、团队门槛高；保留 refinement-as-implication 作为 M3+ 对 R2 契约的可选加强"）；SpecRL/VERIMED 等新工具（"成熟度不足，只跟踪"）。
- 防真空：expectation 未知形态判 fail + witness 绑定义务（无见证条款=advisory），对应研究中"ensures true 型空规格"风险。

### 11.11 差分测试研究（01/04 差分、02 行为等价）→ 采纳执行级
- **采纳**：种子语料差分（Csmith 思想的轻量版）、canonical 归一化+redaction、product-program/trace alignment 思想简化为"同输入集行为对比"（"够用且可判定"）、EvalPlus 式测试增强（M2 场景轮换）。
- **不采纳**：神经表示等价粗筛（"不作判据"）、全量符号执行（"成本不可控"）。

### 11.12 统一裁决原则（09 文档 §12）
1. "凡进入门禁判定路径的，必须是机械可复现的（退出码/摘要/哈希链）；LLM 判断一律降为起草、分诊、软否决"。
2. "凡研究建议引入新基础设施（Temporal/TiKV/TEE/MPC），默认推迟到实测压力证明必要"。
3. "凡单作者/早期开源项目，只借鉴设计不裸依赖"。

---

## 附：维度覆盖对照（某文档缺某维度 = 无）

| 维度 | 主要出处 | 其他出处 |
|---|---|---|
| 1. 目标与核心范式 | 00、01、05、07 | — |
| 2. 系统组成模块 | 00、01 | — |
| 3. 架构选择 | 00、01、02、04、06 | — |
| 4. 契约定义 | 02 | 01、03 |
| 5. CI门禁与Oracle | 05 | 00、01、02、03、07 |
| 6. 测试策略 | 07 | 03、09 |
| 7. 交付节奏 | 00、08 | 02、03 |
| 8. 角色/团队分工 | 00、03、04 | — |
| 9. TCO/成本优化 | 03、04、08、09 | 01 |
| 10. 验收标准与阶段推进 | 08 | 00、03 |
| 11. 研究采纳决策表 | 09 | — |

- 单文档维度"无"的情况：00_总览.md 不包含维度 11（研究采纳决策）与维度 6（测试策略细节）；01 文档无维度 7（交付节奏以 phase 形式的 M0-M3 只出现于 00/08）与维度 11；02 文档无维度 11；03 文档无维度 11；04 文档无维度 11 与维度 5 的门禁细节（仅档位/隔离相关）；05 文档无维度 11 与维度 9（成本）；06 文档无维度 5/7/10/11 的详细内容（仅信息不对称相关）；07 文档无维度 7/10/11；09 文档仅覆盖维度 11 与其他文档的采纳映射，不含独立的新系统组成/验收细节。
