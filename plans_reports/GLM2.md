# GLM2 工程计划总结报告

> 本文基于以下文档（忠实原文，关键点注明出处行号/小节）：
> - `/workspace/plans/GLM2/ENGINEERING_PLAN.md`（主计划，本文简称 **EP**）
> - `/workspace/plans/GLM2/structure.md`（PDR-001 范式决策记录，本文简称 **SD**）
> - `/workspace/plans/GLM2/CAPABILITY_MAP.md`（openJiuwen 原生能力清单，本文简称 **CM**）
> - `/workspace/plans/GLM2/README.md`（仅标题 `jiuwen_research`，无实质内容）
>
> 本报告为研究任务产出，未修改任何源文件，仅新增本报告。

---

## 1. 目标与核心范式（spec-as-source、PDR）

### 1.1 总体目标
- EP L3-4：本计划是 PDR-001（`structure.md`）的工程落地文档，"目标：在 openJiuwen 之上建成 **'Spec-as-Source 为本体、门禁与事务为物理层'的开发 agent swarm**"。
- EP L6-8：契约内核（`swarmforge/` 包）已实现并通过 134 项测试；各执行团队照本计划在契约之上开发，不需要再做跨模块工程决策。
- EP L10-12：§3 全局决策（D1–D22）不可推翻；§6 按团队分工认领；所有 openjiuwen API 引用均已在实际代码中验证（§2）。

### 1.2 PDR 到底指什么（已核实，非臆测）
- SD L1：`# PDR-001 范式决策记录：Agent Swarm 软件开发范式选型` —— **PDR = 范式决策记录（Paradigm Decision Record）**，即 `structure.md` 这一份文档本身。
- EP L3 与 EP L140（仓库结构图中 `structure.md # PDR-001 范式（不可变前提）`）、`swarmforge/swarmforge/__init__.py` L3（"范式见 /workspace/structure.md (PDR-001)"）三处均指向同一文档。
- 5 层模型见 **SD §4 "决策：分层范式与严格优先序"（L79-94）**，自上而下授权：
  - **第0层 宪法**：不可协商不变量，固定化自然语言，会话内不可变；
  - **第1层 规范 Spec（唯一真值）**：L1 业务意图（人类定义、人类批准）/ L2 开发契约（人类看 diff、可否决）/ L3 实现说明（机器所有，人类不看不批）；
  - **第2层 判据 Oracle**（场景 holdout + 机械见证 + judge rubric）← architect 产出；
  - **第3层 实例 Instance**（代码，可丢弃）← 临时 builder fan-out 产出；
  - **第4层 世界 World**（已准入代码库、制品、运行环境）。
- **优先序（SD L96-101，冲突裁决规则不可绕过）**：宪法 > spec > oracle > 实例 > 世界；`准入 = 硬门禁通过 ∧ 软门禁通过`；代码与 spec 不一致 = **spec 漂移事件**，默认判定为缺陷并阻断；世界的既有行为不构成真值、只构成约束（必须写回 spec 才生效）。

### 1.3 范式核心表述
- SD L10：采纳「Spec-as-Source 为本体、门禁与事务为物理层」的分层范式；**不采纳**传统波次-PR 范式作为治理主体，也**不采纳**纯 StrongDM 式无门禁全丢弃。
- SD L14-16（三句话表述）：
  1. "真值只有一处：spec。代码是 spec 在某次采样下的实例"；实例的价值在于揭示 spec 的**沉默**（未定义）与**分歧**（歧义），交付只是副产品；
  2. "P1 的机械部分全部保留并加强，但被剥夺真值权威"——CI 门禁、PR、波次变成"准入事务协议 + 机械化 oracle"；
  3. "人类退出实现层，前移到契约层"——人类只在 L1/L2 行使权力，L3 与代码 diff 不看不批。
- SD L18（一句话理由）：生成并行且廉价、准入串行且昂贵；选择"可有界化的失效模式"。
- SD §1 四轴拆分（L26-33）：A 真值载体=spec、B 准入权威=硬门禁∧软门禁（人类仅对 L2 否决）、C 变更单元=再生单元、D 收敛机制=实例测量→spec 收敛→单实例准入。这是"分层"而非"折中"。
- SD §2 六条决定性约束 C1-C6（L41-51）：受体带宽唯一不可并行段、共享可变状态并发代价超线性、上下文经济决定单位成本、复利只能沉淀在可被 agent 读取的载体、熵（补丁累积 vs 再生重置）、**只有多实例并行才产生"spec 熵"这个可观测量（C6）**。
- SD §3 失效模式对照（L57-75）：P1 核心失效（F1 人审带宽/F3 意图丢失/F4 正确性靠测试/F6 多路差异被抹平）在 swarm 下**不可有界**；P2 失效（G1 oracle 债/G2 不可再生制品/G3 再生非确定性/G4 brownfield 冷启动/G5 token 成本/G6 不可人类审计）全部可用"分级+边界+显式代价"有界化 → 故选 P2 为本体。

---

## 2. 系统组成模块清单

### 2.1 本计划要构建的系统（EP §4 仓库与目录结构，L136-165）
- `structure.md`：PDR-001 范式（不可变前提）。
- `ENGINEERING_PLAN.md`：本计划文件。
- **`swarmforge/`（✅ 已实现并测试，契约内核）**，子包：
  - `constitution/`：15 条不变量 + ConstitutionViolation + 校验辅助（L145）；
  - `specrepo/`：schema（条款/见证/don't-care/delta）+ store（原子写/版本链/接口锁）+ rregistry（L146）；
  - `oracle/`：schema（场景/rubric/judge/golden）+ holdout（隔离+审计）+ differential（引擎）（L147）；
  - `gates/`：algebra（代数+证据链）+ h_gates（H1-H8+S）+ registry（runner）（L148）；
  - `admission/`：wave（状态机）+ receipt（哈希链）+ transaction（2PC+WAL+恢复）（L149）；
  - `bus/`：bus（权限矩阵+连线检查）+ bridge（openjiuwen 适配）（L150）；
  - `measurement/`：fanout（N 自适应）+ classify（六格）+ health + 降级（L151）；
  - `harness/`：roles（角色装配+宪法校验）+ tiers（档位）+ proposal（提案）（L152）；
  - `reconciler.py`：漂移扫描（H7 证据生产）（L153）；
  - `tests/`：134 passed（9 个测试文件）（L154）。
- `swarm-app/`（⬜ 团队 T1-T7 实现区，L155-162）：`orchestrator`（leader 运行时/波次编排/事件循环）、`executor`（builder 沙箱执行面）、`verifier-runner`（H 门执行器+judge workflow）、`architect`（波次切分 agentic 过程）、`moderation`（spec moderator/steward/reconciler 常驻）、`calibration`（B 流水线标定团队）、`report`（人类报告面+健康度面板）。
- `specs/`：运行时 spec 仓（git 管理，SpecStore 布局，L163）。
- `research/`：外脑研究（只读参考，L164）。

### 2.2 两条物理隔离流水线（EP §1，L38-41）
- **A 交付流水线**：spec-delta → fan-out N → 门禁 → 选一实例准入。
- **B 标定流水线**：不确定度告警/审计抽样触发 → 全部代码丢弃 → 只产出 spec-delta / oracle 补强 / don't-care 登记。
- SD §7 双流水线对照（L152-158）：B 流水线成功定义 = "学到了 spec 的沉默/分歧位置（即使无一实例通过也算成功）"，且"不同 leader、不同记忆域"。

### 2.3 已验证的 openJiuwen 框架事实（EP §2，L43-73，均实地代码核验）
| 能力 | 位置（EP L47-64） | 用途 |
|---|---|---|
| TeamRuntime（P2P send + PubSub，`*`/`?` fnmatch 通配） | `agent-core/openjiuwen/core/multi_agent/team_runtime/team_runtime.py` | 总线跨进程底座 |
| 团队 harness（TeamAgentSpec / TeamLifecycle TEMPORARY/PERSISTENT） | `agent_teams/schema/blueprint.py:209` 等 | builder 临时 fan-out / 判别侧持久团队 |
| 团队记忆（TEAM_MEMORY.md，仅持久团队 leader 写，四分类） | `agent_teams/memory/`，三重门控 | 判别侧裁定写入（INV13） |
| messager（inprocess/pyzmq/hybrid） | `agent_teams/messager/` | 分布式模式传输 |
| spawn（注册与拉起分离） | `agent_teams/spawn/` | builder 拉起 |
| worktree 隔离 + 团队工作区 | `openjiuwen/harness/tools/worktree`、`team_workspace/manager.py` | 实例物理隔离 |
| swarmflow 工作流引擎（默认关） | `agent_teams/workflow/` | 波次编排可选承载 |
| Workflow IR（组件图+BranchRouter+LoopGroup） | `openjiuwen/core/workflow/` | verifier 门禁流水线编排 |
| Checkpointer + interrupt 恢复 | `core/session/checkpointer/` | 波次事务边界/续跑 |
| ContextEngine（session_id+context_id 池化） | `core/context_engine/` | 角色上下文隔离 |
| DeepAgent + AgentRail（priority + 12 钩子） | `harness/deep_agent.py`、`core/single_agent/rail/base.py` | 角色 rail 装配 |
| Guardrail（RiskLevel.CRITICAL → AbortError） | `core/security/guardrail/` | 宪法机械化（H6） |
| Reliability（Severity → LOCAL_STEER/ESCALATE_USER） | `agent_teams/reliability/` | 异常分级处置 |
| 模型档位（model_pool/router/intelli_router 三互斥） | `agent_teams/schema/team.py:379-389` | RU-L/M/H 分档 |
| KV 缓存（Anthropic 式 cache_control） | `.../anthropic_model_client.py` | 前缀缓存纪律 |
| jiuwenbox 沙箱（bubblewrap+Landlock+seccomp+网络隔离+egress 白名单） | `jiuwenswarm/jiuwenbox/.../supervisor/` | builder 执行隔离 |
| 技能演进 rail（auto_save=False 人工审批） | `jiuwenswarm/.../evolution_rails.py` | deep agent 提案通道 |
| dev_tools.tune / agent_evolving | `openjiuwen/dev_tools/tune/`、`openjiuwen/agent_evolving/` | 提示词/技能自优化 |

### 2.4 关键纠偏（EP L66-73，与 structure.md §11 假设的差异）
1. "临时团队只读父记忆、不留痕"**不是框架自动语义**：TEMPORARY 只保证不写 TEAM_MEMORY.md 与跳过会话持久化调度；仍写 DB 与文件系统。**必须**：(a) builder 角色不挂 memory-write/evolution rail（`harness/roles.py` 白名单已实现）；(b) 团队解散走显式 `delete_team(force=True)`。
2. "AgentHints" 类不存在；KV 缓存控制是消息块级 `cache_control`。
3. Studio 的 DSL→IR 与版本发布不在 swarm 内核路径上（多智能体中央路由不用）。
4. Python 版本约束：`>=3.11,<3.14`。

### 2.5 下层 openJiuwen 生态组件（CM §1 组件概览 L28-40，供参考）
- **Agent Core**（`agent-core/`，Python，~927k 行）：Agent SDK 内核（ReAct/Deep 单体、多智能体 Team、LLM 抽象、记忆/存储、工具与 MCP、检查点、runner、harness 扩展装配）。包名 `openjiuwen`，是整个生态唯一被多组件以库依赖引入的公共内核（CM §3.1）。
- **Agent Studio**（Java+Python+TS）：低代码 Agent/工作流 IDE 与管理平台，编排产物下发到 Runtime（CM §2.2）。
- **Agent Runtime**（Python）：Agent 托管运行时，IR 执行、会话/流式 API、A2A 暴露（CM §2.3）。
- **Agent Memory**（Python 内核 + Java 服务）：记忆抽取/检索/融合/遗忘 + 多租户平台服务（CM §2.4）。
- **Agent Protocol**（C++/Python）：A2A C++ SDK、MCP C++ SDK、AgentRegistry（A2X）注册/发现（CM §2.5）。
- **Agent Tools**（Python）：infer_router（KV-Cache 亲和的 OpenAI 兼容 LLM 网关）、vLLM 亲和调度插件、开发者工具集（CM §2.7）。
- **DeepSearch**（`deepsearch/`，Python，~119k 行）：深度研究 Agent——树搜索式研究循环、9 种 Web 搜索后端、抓取与 LLM 抽取、引用溯源、报告导出（DOCX/PDF/HTML）、本地知识库 RAG、SSE 流式+人在回路（CM §2.9，详细 L894-997）。
- **JiuwenSwarm**（`jiuwenswarm/`，Python，~442k 行）：面向编码/终端场景的 Agent 集群产品——TeamManager、WebSocket 协议、ACP/MCP、**多层沙箱 jiuwenbox**（Landlock+Seccomp+bubblewrap+cgroup+网络隔离）、Code Mode、分级权限与审批流、子 Agent 派生、流式事件管线（CM §2.8，详细 L778-890）。
- **JiuwenSymbiosis**（`jiuwensymbiosis/`，Python，~53k 行）：具身智能/机器人本体接入层——机械臂（Piper/SO-101）控制、GroundingDINO+SAM2 视觉抓取、TraceRail 轨迹回放、诊断/安全/恢复 rail、语音前端、NiceGUI 操作台（CM §2.10，详细 L1001-1126）。
- **Relay**（`relay/`，TypeScript，OfficeClaw）：桌面/服务端 Agent 工作台——多 Provider 路由与协议翻译、Anthropic 网关反代、Socket.IO 流式、回调令牌安全、技能体系（本地+远端 SkillHub）、MCP 工具服务、三层身份鉴权、外发连接器中枢、JiuwenClaw Python 边车（子进程+本地 IPC）（CM §2.11，详细 L1130-1233）。
- **SkillHub**（Python+TSX）：技能/插件市场——技能包发布检索、Playground 试跑（HTTP 代理到独立 skill-runner 进程）（CM §2.6、§3.6）。
- **跨组件交互协议（CM §3，L1237-1327）**：生态**不存在统一服务总线或统一注册中心**，实际存在四种耦合方式——①Python 包内嵌依赖（agent-core 星形中心）；②语言间 HTTP（Studio↔Runtime Feign、Memory Java↔Python、SkillHub↔Runner）；③协议化边界（A2A/MCP/ACP，覆盖不完整）；④源码复制（A2X Registry 客户端内嵌 jiuwenswarm 且已漂移）。三种 agent-core 依赖形态（git 分支/`>=`下限/`==`钉版）并存，组件不能在同一 Python 环境共存。
- **CM §4 待确认/模糊地带（L1330-1416）**：多个能力默认全关或为占位（如 jiuwenswarm 的 a2ui/symphony/enable_swarmflow 默认 false；agent-runtime 租户隔离被显式关闭；deepsearch 的 codesearch 为空目录；relay 的 SymlinkManager 为 no-op 桩），"不应被当作可用能力计入基线"。

---

## 3. 架构选择（通信、总线/信封、信息不对称实现）

### 3.1 全局决策 D1-D22 中与架构相关的条目（EP §3，L75-128）
- **D1 语言/依赖（L77-79）**：控制面 Python 3.11+；`swarmforge` 核心**零三方依赖（仅标准库）**——门禁必须能在最简环境机械执行；openjiuwen 仅是可选依赖（`[openjiuwen]` extra）。
- **D2 spec 物理形态（L80-81）**：文件系统 + git；L2 契约用 **JSON**（`domains/<domain>.spec.json`）——机械可判等、diff 友好、零依赖；**不用 YAML**。
- **D3 条款结构（L82-84）**：`clause_id`（REQ-*/CON-*/IMP-*）+ layer + witnesses[] + anchors[]；无见证的 L1/L2 条款 `status=unverifiable`，只能否决不能放行（INV3 可执行形式）。
- **D4 R 级注册（L85-86）**：首条命中规则生效，未命中默认 R0；`ALLOWED_OPERATIONS`/`REQUIRED_GATES` 矩阵驱动操作守卫与门禁选择。
- **D5 门禁代数（L87-88）**：`Admit = H ∧ S`；adjudicate 纯函数；blocking FAIL→REJECT，INCONCLUSIVE→ESCALATE（**永不静默放行**）；S 只能 veto/abstain，永不豁免 H。
- **D6 证据来源链（L89-90）**：验证性证据必须由判别侧角色（verifier/architect/ci/sandbox/human）产出；builder 自报证据 → EvidenceRejected → ESCALATE（防伪造，已测试）。
- **D11 准入事务（L98-99）**：WAL 两阶段 + 幂等键（delta_id/receipt_id）；崩溃恢复对无终态 BEGIN 显式 ROLLBACK；rollback 保留测量结论（INV2）。
- **D12 收据账本（L100）**：append-only JSONL + 哈希链（防篡改、断点可定位，已测试）。
- **D13 总线（L101-104）**：见 3.2。
- **D19 漂移检测（L118-120）**：`@spec:<clause_id>` 注解硬轨 + 四类硬错误（orphan/missing_anchor/bypass/stale）直接阻断；R3 路径豁免 missing_anchor；J1 行为契约哈希 = 仅 L2 bound 条款的规范化哈希。
- **D21 上下文纪律（L124-126）**：prompt 静态前置（宪法+spec 快照+工具定义逐字节稳定）+ 动态后置（测试日志/时间戳/中间结果一律尾部）；builder 之间禁止共享中间产物；子 agent 只回传摘要级结果；判别侧与编排侧 session/checkpoint 隔离。

### 3.2 通信方式 / 总线 / 信封
- **总线两实现（EP D13）**：`InProcessBus`（单机/测试）+ `OpenJiuwenBusAdapter`（跨进程，权限矩阵前置强制——TeamRuntime 本身无权限概念，不能裸用）。底层复用 TeamRuntime 的 P2P send + PubSub（EP L47）。
- **Topic 规范**：`<域>.<对象>.<动作>`；**身份（wave_id 等）放信封不嵌 topic**（EP L102-103）。
- **deny-by-default 权限矩阵** + **装配期连线检查**（悬空订阅/死信/越权声明报错）（EP L103-104）。
- **信封**：`Envelope(topic, type, sender_role, payload, wave_id)`（EP §5.1，L180）。
- **运行配置基线（EP §9，L359-368）**：单机模式 `team.runtime.mode=local` + InProcessBus + Checkpointer（in_memory/sqlite）；分布式 `mode=distributed` + pyzmq messager + `OpenJiuwenBusAdapter`（权限矩阵仍在适配层强制）+ Redis checkpointer；`model_pool_strategy="by_model_name"`。
- **波次状态机（EP §5.4，L209-213）**：`DRAFT → SEALED(接口锁) → FANOUT → VERIFY → CLASSIFY → ADMITTING → COMMITTED`，`CLASSIFY → CONVERGING → SEALED` 为标定回路；非法转移抛 `IllegalTransition`（表驱动 `LEGAL_TRANSITIONS`）。

### 3.3 信息不对称实现（"信息不对称是硬约束，不是礼仪"——SD §7，L160）
1. **场景 holdout 对 builder 不可见**（SD L162）：builder 只见 spec（L1/L2/L3）+ 接口面 + 本地可跑自测；端到端场景集与判据 rubric 由 architect 持有、verifier 执行；目的：消除 reward hacking 的信息前提。
2. **生成者不得参与判别**（SD L163）：builder 不进入 verifier/spec moderator/judge 任何环节；judge 不得评审自身参与生成的实例。
3. **临时 builder 不写任何记忆**（SD L164）：实现细节只写团队记忆且须经判别侧同意；"可丢弃实例的偶然选择不得污染后续采样的先验"。
4. **spec moderator 与 leader 分离、与 architect 分离**（SD L165）：leader 只编排；architect 产出任务划分/DoD/verification；spec moderator 只裁决 spec 收敛；三者上下文互不污染。
5. **judge 模型档位 ≥ builder 档位**（SD L166，EP INV14 装配期校验）。

物理层落地：EP §5.3（L198-207）Topic 清单与权限矩阵——builder **永远不能** publish `gate.*`、subscribe `holdout.*`/`measurement.*`；任何越权 → `BusPermissionError(INV5)`；holdout 场景内容只有 verifier/architect/human/calibration_leader 可读且全部留审计；EP D8（L92-93）：oracle 双库 = open（builder 可见自测）/ holdout（物理分目录 + 角色强制 + 审计日志，**拒绝尝试也留痕**）。

---

## 4. 契约定义（契约/制品、格式、版本化）

### 4.1 数据契约（EP §5.1，L169-181，swarmforge 中的权威定义）
| 契约 | 权威定义 | 序列化 |
|---|---|---|
| 条款/文档/delta/don't-care | `specrepo/schema.py` | `to_dict()/from_dict()` |
| R 级规则 | `specrepo/rregistry.py::RRegistry` | JSON |
| 场景/判词/黄金 manifest/差分报告 | `oracle/schema.py` | JSON |
| 门禁证据 | `gates/algebra.py::EvidenceItem(kind, producer_role, payload)` | JSON |
| 门禁结果/准入判定 | `gates/algebra.py::GateResult / adjudicate()` | JSON |
| 收据 | `admission/receipt.py::EvidenceReceipt`（哈希链） | JSONL |
| 测量记录 | `admission/transaction.py::MeasurementRecord` | JSONL |
| 事件信封 | `bus/bus.py::Envelope(topic, type, sender_role, payload, wave_id)` | JSON |
| 角色/档位/提案 | `harness/{roles,tiers,proposal}.py` | JSON |

### 4.2 证据 kind 契约（EP §5.2，L183-196，verifier 执行面必须产出的 payload 形态）
| kind | 生产者 | payload 必备字段 | 消费门 |
|---|---|---|---|
| `build_report` | ci/sandbox | compile_ok, type_errors[], lint_errors[] | H1 |
| `test_report` | ci | total, passed, failed, errors, property_failures[] | H2 |
| `scenario_results` | verifier | results[{scenario_id,outcome}], fail_to_pass[], pass_to_pass[] | H3 |
| `contract_diff` | verifier | breaking[], major_bump_declared | H4 |
| `diff_report` | verifier | DifferentialReport.to_dict() | H5 |
| `golden_result` | verifier | verdict(pass/fail/inconclusive), detail | H5 |
| `guard_report` | sandbox | path_violations[], declared_deps[], license_violations[], secret_findings[] | H6 |
| `drift_report` | verifier | orphans[], missing_anchors[], bypasses[], stale_clauses[] | H7 |
| `budget_report` | ci | tokens_used, token_cap, wallclock_used_s, wallclock_cap_s | H8 |
| `judge_outputs` | verifier | [{verdict: veto/no_veto/abstain, reasons[], evidence_citations[]}] | S |

### 4.3 格式与版本化
- **格式**：JSON（spec/场景/门禁结果/证据/信封）、JSONL（收据账本、测量记录）、YAML 仅用于 jiuwenbox 沙箱 policy 模板（EP T2，L250）。D2 明确"不用 YAML"指 L2 契约。
- **版本化**：
  - `specrepo/store` 提供"原子写/版本链/接口锁"（EP L146）；RRegistry 规则 JSON（EP L174）。
  - 收据 = append-only JSONL + **哈希链**（D12），防篡改、断点可定位。
  - 黄金输出 manifest = code/deps/seed/normalizer 哈希（D10）。
  - 门禁配置/rubric/judge prompt 对 builder **只读且版本化**（INV6 会话内冻结），变更走提案（EP L373-374）。
  - J1 行为契约哈希 = 仅 L2 bound 条款的规范化哈希（文案润色不触发）（D19）。
- **六格判定→处置路由（EP §5.5，L215-224）**也是契约级约定：CLOSED（选实例准入）、SILENCE（don't-care 登记或 spec-delta，B）、AMBIGUITY（moderator 收敛 spec，B）、UNDERSPECIFIED（spec 澄清+记录档位需求）、SPEC_ORACLE_CONFLICT（steward+architect 会诊，规范级事件）、INSUFFICIENT（N<3 有败/差分不确定 → 补采样/统计通道）。

---

## 5. CI 门禁与 Oracle 机制

### 5.1 门禁代数（D5、SD §8）
- `Admit(instance) = H(instance) ∧ S(instance)`，H 为硬门禁合取、S 为软门禁合取，**缺一不可，任何门禁不得只有 S**（SD L172）。
- 规范条款到机械见证映射义务（SD L174）：**每条 L1/L2 条款必须绑定 ≥1 个硬见证或 ≥1 个 holdout 场景；否则标记 `unverifiable`，只能作为 advisory 参与软门禁，不得作为放行依据**。
- blocking FAIL → REJECT，INCONCLUSIVE → ESCALATE（永不静默放行）；S 只能 veto/abstain，永不豁免 H（EP D5）。

### 5.2 H1-H8 门禁清单（SD §8 表，L178-187；EP D7 顺序）
| 代号 | 门 | 守护对象 |
|---|---|---|
| H1 | 构建 / 类型 / 静态分析 | 语法与结构底线 |
| H2 | 单元与属性测试 | 局部行为 |
| H3 | 场景 holdout 套件 | oracle 主体，L1 意图 |
| H4 | 契约面提取 + 破坏性变更检测 | L2 的机械见证，R1/R2 级兼容性 |
| H5 | 实例间差分测试 / 黄金输出 | spec 沉默、R3 逐行语义 |
| H6 | 不变量与运行时护栏（危险操作、依赖策略、许可、沙箱边界） | 宪法的可机械化部分 |
| H7 | spec↔code 漂移检测 | 真值一致性（reconciler 的机械部分） |
| H8 | 成本 / 资源 / 性能预算 | 经济与非功能约束 |

- **执行顺序（D7，L91）**：H1 → H6 → H8 → H7 → H2 → H4 → H3 → H5 → S（fail-fast、**成本升序**）。
- **verifier 生产证据方式（EP T3，L265-273）**：H1 构建（uv/make）；H2 pytest（含 property_failures[]）；H3 执行 holdout 场景（stimulus 灌入入口比对 expected，PASS_TO_PASS 回归集）；H4 契约面提取（公开符号/HTTP 面/事件 schema 指纹，与 world 基线 diff）；H5（N>1 跑差分：holdout 输入 + `DiffInputGenerator.perturb` 扰动输入 → `DifferentialEngine.compare`；**R3 走 `GoldenGate.verify_manifest` + compare**）；H6 从沙箱策略引擎导出违规清单；H7 `check_drift` 扫实例树 vs spec 快照；H8 从模型网关 usage 账单聚合；S = judge workflow（k=3 采样多数决，rubric 从 `oracle/rubrics/` 装载）。

### 5.3 Oracle 引擎清单与强度分级
- **Oracle 引擎清单**：`oracle/` 子包 = schema（场景/rubric/judge/golden）+ `HoldoutStore`（隔离+审计）+ `DifferentialEngine` + `GoldenGate`（EP L147、L401-403）；T3 输入还包括 `JudgeRubric`、`reconciler.check_drift`（EP L263-264）。
- **oracle 双库（D8）**：open（builder 可见自测）/ holdout（物理分目录 + 角色强制 + 审计日志）；场景 = FAIL_TO_PASS + PASS_TO_PASS 双结构（EP L92-93）。
- **差分引擎（D9）**：与执行解耦（输入执行轨迹）；normalizer 剥非确定性 → 指纹 → 发散检测 → don't-care 归约 → 扰动复判（不稳定 → INCONCLUSIVE 统计通道）（EP L94-95）。
- **黄金输出（D10）**：manifest（code/deps/seed/normalizer 哈希）不一致 → 比对无效（INCONCLUSIVE），绝不据此放行/阻断；**字节级精确比对；CI 永不自动写黄金**（EP L96-97）。
- **强度分级（EP §7/§10）**：
  - 判据覆盖率门槛（P2 进阶条件 ≥70%；bound L2 条款锚点覆盖 100%，EP L329）。
  - "无断言自测不计入验证强度"（研究采纳，EP L132）。
  - judge 校准（kappa ≥ 0.6 才启用 S，EP L330）；判据不可信 → 降自治而非放宽判据（EP L379-380）。
  - 降级触发：escape_rate > 5% → 回退阶段 + 人类额外确认；spec_entropy > 2.0 → 冻结 fan-out 转 B 流水线；rework_rate > 50% → 降 N/缩单元/升档位门槛（EP L333-335）。
- **宪法 15 条不变量（SD §14，L304-322）**：其中 INV3（门禁必须含机械见证）、INV4（硬门禁不过软门禁不得放行）、INV5（生成者与判别者不得同一、判据不得对生成者可见）、INV6（判别者与判据会话内不得自我改变）、INV13（可丢弃主体不得写入长期记忆）、INV14（判别方档位 ≥ 生成方）、INV15（判据不可信 → 降自治而非放宽判据）等，均已被 EP 引用为可执行不变量（INV2/5/6/11/13/14 等）。

---

## 6. 测试策略

### 6.1 门禁自身已被测（EP §8，L337-357，swarmforge/tests 134 项全绿）
1. **门禁拦截性**：每个 H 门构造坏证据样本必须 FAIL（H1 构建失败/H2 属性失败/H3 回归/H4 未声明破坏性变更/H5 沉默与黄金失配/H6 路径越界与违禁依赖/H7 四类漂移/H8 超预算）。
2. **代数真值表**：H FAIL 时 S 无法救场；S veto 可否决；abstain 永不默认通过；INCONCLUSIVE → ESCALATE。
3. **防绕过**：builder 伪造证据被证据来源链拒绝并升级；总线越权（publish gate.*、subscribe holdout.*/measurement.*）抛 INV5；holdout 读取审计含拒绝尝试。
4. **事务**：commit 原子性、失败自动回滚、崩溃恢复、幂等重放；rollback 保留测量（INV2）；收据哈希链篡改可定位断点。
5. **契约间通信**：连线检查（悬空订阅/死信/越权声明）；全事件流 wave.sealed→build→gate→measurement→admit 按权限矩阵流转；审计日志完整。
6. **端到端**：A 流水线全绿准入 + B 流水线沉默→don't-care→复判等价回路 + 信息不对称红队（builder 三通道全拒）。
7. **宪法投影**：角色装配（INV5/6/13）、档位（INV14）、提案（INV6 same-session 拒绝）。

### 6.2 测试输入生成 / 差分 / 属性测试 / 反馈循环
- **测试输入生成**：差分四象限输入（**主流程/边界/历史事故/敏感输入**，研究采纳，EP L133）；`DiffInputGenerator.perturb` 扰动输入用于 H5（EP L268）。
- **差分测试**：D9 五步（normalizer → 指纹 → 发散检测 → don't-care 归约 → 扰动复判），是"一等硬门禁 H5"，用于检出"全绿但语义未定"的沉默（SD L142）。
- **属性测试**：H2 证据含 `property_failures[]` 字段（EP L188），"单元与属性测试"守护局部行为（SD L180）。
- **反馈循环**：六格判定→处置路由（EP §5.5）将测量结论回流到 spec moderator（SILENCE→don't-care/spec-delta；AMBIGUITY→收敛条款）；B 流水线产出 spec-delta/oracle 补强/案例；T5 reconciler 定时/心跳跑 `check_drift` 只上报不自行改 spec（EP L302-303）；每次准入产出证据收据（审计闭环）。
- **各团队补充验收测试**（EP §6 每队"验收测试"）：T1 模拟证据注入走完两回路+锁冲突排队+builder 超时重派幂等；T2 装配片段过 `validate_role`+两 builder worktree/session 互不可见+沙箱越界写被 jiuwenbox 拒绝；T3 每种证据 kind 生产函数单测+H5 三态复现+判词无 citations 按 veto 处理；T4 割集两两不相交+无见证条款被标记+锚点 100% 归属；T5 SILENCE→don't-care→复判等价+stale 闭环时延统计；T6 标定波次收据 `instance_id=""` 且测量保留；T7 报告 schema 白名单（出现 diff/实例字段即 fail）+提案 `effective_for(next_session)` 生效。
- **CI 合并条件**：`python -m pytest swarmforge/tests swarm-app/*/tests` 全绿为合并条件（**merge queue 先测后合**，EP L356-357）。

---

## 7. 交付节奏（phase / wave / milestone）

### 7.1 里程碑 P0-P4（EP §7，L323-331，进阶条件为**硬验收**）
| 阶段 | 内容 | 进阶条件（量化） |
|---|---|---|
| P0 地基（✅ 完成） | swarmforge 契约内核 + 134 测试 | 全绿 |
| P1 执行面 | T1-T3 跑通单域（M0 收割域）端到端：spec→fan-out→门禁→准入→收据 | 连续 20 个波次零未分类异常；H1-H8 全部有真实证据源 |
| P2 收割 | T4+T5 对目标域完成 brownfield spec 收割（L2 从代码反推+锚点+见证绑定）+ H7 上线 | 判据覆盖率 ≥ 70%；bound L2 条款锚点覆盖 100% |
| P3 标定 | T6 上线；don't-care 登记；judge 标注集校准（kappa ≥ 0.6 才启用 S） | spec 闭合度 ≥ 60%；逃逸缺陷率 < 5%（对应 M1→M2） |
| P4 工厂 | R0/R1 默认再生；deep agent 提案通道闭环 | 连续若干波次零逃逸；提案通过率稳定（对应 M3） |

### 7.2 波次（wave）作为基本交付单元（SD L206）
波次 = **接口冻结窗口 + 独立可验证的 spec-delta 割集 + 一个准入事务边界**；波次划分由 architect（集成了 workflow 的 agentic 过程）从 spec 依赖图上切割。对应 EP §5.4 状态机 DRAFT→…→COMMITTED。

### 7.3 迁移梯度 M0-M3（SD §12，L263-272；EP D22）
M0 收割（真值=代码、无丢弃）→ M1 锚定（R0 可丢弃重生）→ M2 再生（R0/R1 常规 fan-out）→ M3 工厂（R0/R1 默认再生、R2 演进、R3 冻结）。**不得跨阶段："在 oracle 覆盖率不足的域宣布'代码可丢弃'，等于取消门禁"（SD L274，本范式唯一致命误用方式）**。

### 7.4 降级规则（自动，`check_degradation` 已实现阈值初值，EP L333-335）
escape_rate > 5% → 回退阶段 + 人类额外确认；spec_entropy > 2.0 → 冻结 fan-out 转 B 流水线；rework_rate > 50% → 降 N/缩单元/升档位门槛。**"降级永远是回退阶段，不是改判据；判据变更只走提案"**。

---

## 8. 角色 / 团队分工

### 8.1 范式级角色集（SD §10，L217-230，自洽校验"完备且无冲突"）
| 角色 | 范式函数 | 层 | 形态 | 隔离要求 |
|---|---|---|---|---|
| leader | 编排、波次推进、事件驱动 | 3-4 | 持久 agent | 不判别、不写 spec；session 内不自演进 |
| architect | 切分波次、DoD、编写 verification 与 rubric、裁定再生单元粒度 | 2 | agentic 过程（workflow+agent 集成） | 不在生成团队内；持有 holdout |
| builder | 采样实例 | 3 | 临时 worker fan-out | 不见 holdout、不写记忆、不参与判别 |
| verifier | 只执行判据：跑 H 全族、跑 S 的 judge workflow | 2-3 | workflow 为主 | 不写判据、不改 spec |
| spec moderator | 由测量结论裁决 spec 收敛；裁定实现细节是否入团队记忆 | 1 | 持久 agent | 与 leader、builder 分离；session 内不自演进 |
| spec steward | spec 分歧长期维护、条款一致性与版本 | 1 | 持久 agent | 与 leader 分离 |
| reconciler | 制订并执行 H7 漂移守护策略，发现漂移即上报 | 1-4 | agent + 定时/心跳 | 只上报与阻断，不自行改 spec |
| cartographer | 代码定位、检索、CI 失败点定位与初步解释 | 3 | agent as tool | 无准入权；弱档位、高缓存命中 |
| critic | 红队攻击 spec 与实例，为 oracle 补场景 | 2 | agent | 不准入；产出进 oracle 而非直接改代码 |
| refactor | 准入后质量提升后处理（熵重置） | 4 | 独立后处理 | 不得改变契约面，须过 H4/H5 |
| moderator | 代码库可读性治理 | 4 | agent + 定时 | 产出为 spec-delta 或 refactor 请求，不直接改代码 |
| deep agent（演进） | 监测并提案：模型档位策略、RU 升降档、规则变更、harness 优化 | 0-2 | Rail + 提案器 | 只提案不生效；生效需人类批准且限于新 session |

- 人类 = OPC（EP L20：L1 定义/L2 diff 否决/提案批准），人类报告面**只含** L1/L2 事项、deep agent 提案、健康度评分，"绝不含代码 diff、实例选择、RU 升降档细节"（EP L318-319）。

### 8.2 工程团队 T1-T7（EP §6，L231-321；每队"输入/职责/红线/验收测试"）
- **T1 orchestrator（leader 运行时）**：完整事件循环——收 `spec.delta.proposed` → 建波次 → `acquire_lock(InterfaceLock)` → `transition(SEALED)` + publish `wave.sealed` → `RRegistry.required_gates()` 计算门禁集合 → `compute_fanout(...)` 定 N → 逐 builder 发 `wave.assign.<pool>` → 收齐 `build.instance.*.completed`（或超时重派）→ `transition(VERIFY)` → 按六格路由准入/收敛/澄清/上报。
- **T2 executor（builder 执行面）**：把 RoleSpec 落成 openjiuwen `TeamAgentSpec`（`lifecycle=TEMPORARY`、`team_mode=predefined`、`spawn_mode=process`、worktree isolation）；写 jiuwenbox policy YAML 模板（builder-default：`filesystem_policy.read_only=[specs/,world/.git]`、`read_write=[.worktree/<instance>]`、`network.mode=isolated` + `egress.allowed_domains=[model-gateway]`）；红线：builder 无记忆写 rail、无 evolution rail、tools 白名单不含 `holdout.read/rubric.read/judge.invoke/golden.verify`、builder 间禁止共享中间产物。
- **T3 verifier-runner（判别执行面）**：在干净沙箱中依次生产 H1-H8 + S 证据（见 §5.2），全部证据 `producer_role="verifier"|"ci"|"sandbox"`；judge 规范：判官档位 ≥ builder、prompt 四段（任务+维度/逐档 rubric/先依据后 JSON 分/偏差声明）、先证据后结论、允许 abstain、判官与 builder 不同族（跨厂商优先）。
- **T4 architect（波次切分）**：DeepAgent 外层 TaskLoop + Workflow 嵌套，从 spec 依赖图（条款 anchors 与 witnesses 引用关系）切割互不相交的 spec-delta 割集；为新/改 L2 条款绑定见证（gate 引用或 holdout 场景草案交 critic 红队）；产出 `SpecDelta + InterfaceLock 条款清单`。
- **T5 moderation（spec moderator/steward/reconciler 常驻）**：moderator 收 SILENCE→登记 don't-care（dimension 用 glob：`*.receipt_no`）或出 spec-delta；收 AMBIGUITY→收敛条款；裁定实现细节是否入团队记忆（写 TEAM_MEMORY.md 仅经持久团队 leader 角色）；steward 负责条款一致性、版本链维护、SPEC_ORACLE_CONFLICT 会诊；reconciler 定时/心跳对 world HEAD 跑 `check_drift`，报 `drift.detected`，只上报不自行改 spec。
- **T6 calibration（B 流水线标定团队）**：审计抽样（周期性对 R0 域跑 N=3 校准 spec 熵）；新领域探路；oracle 冲突排查；**全部代码丢弃**，只产出 spec-delta/oracle 补强/案例；与 A 流水线不同 leader、不同记忆域。
- **T7 report（人类报告面+健康度）**：只含 L1/L2 事项、deep agent 提案、健康度评分（闭合度/熵/覆盖率/逃逸率/返工率/成本）；R2/R3 或 L2 变更准入请求列表（human_involved 审批队列）；降级触发告警。
- **通用 DoD（EP L228-229）**：代码 + 单测 + 与 swarmforge 契约的集成测试全绿；不修改 swarmforge 契约定义（发现契约问题走提案通道）；所有事件经总线、所有证据带来源。

---

## 9. TCO / 成本优化

- **N 自适应 fan-out（D14，EP L105-107）**：`U = 0.4·rework + 0.3·novelty + 0.3·risk(R级)`；U<0.3→N=1，0.3–0.7→N=3，≥0.7→N=6，硬顶 8；前 k=2 实例全过同组 oracle 即早停；**R3 恒 N=1 禁早停**（INV11：冻结制品禁重采样，测量走黄金/统计通道）。fan-out "是按不确定度触发的测量而非常量"（SD G5/L144）。
- **模型档位 RU-L/M/H（D15，EP L108-110）**：角色地板 architect/critic/deep_agent/judge=RU-H；builder=RU-M（升不降，R2/R3 任务锁 RU-H 地板）；cartographer/moderator=RU-L；INV14 judge 档位 ≥ builder 档位（装配期校验）。示例基线（EP L365-366）：RU-L=qwen3-30b 级、RU-M=qwen3-max 级、RU-H=glm-5 级；judge 与 builder 跨族。
- **H8 预算（D18，EP L116-117）**：per-wave token/wall-clock 双帽；超限 = 门禁 FAIL（**阻断准入而非杀进程**）；三档计价读数（cached 0.1× / write 1.25× / normal 1×）记入收据 cost 字段。
- **上下文纪律（D21，EP L124-126）**：prompt 静态前置（宪法+spec 快照+工具定义逐字节稳定）+ 动态后置（测试日志/时间戳/中间结果一律尾部）；builder 之间禁止共享中间产物；子 agent 只回传摘要级结果；判别侧与编排侧 session/checkpoint 隔离。KV 前缀缓存纪律见 EP L61、L367-368（宪法+spec 快照+工具定义置顶且逐字节稳定；时间戳/随机 id 出前缀区）。
- **C3 上下文经济（SD L45）**：代码库大且高频变动 → 前缀缓存持续失效、上下文膨胀；spec 小且低频变动 → 可全量入 prompt、可稳定缓存。
- **成本观测指标**：返工率与单位准入成本（token/时长）构成健康度成分（SD L290）；降级成本控制（EP L334-335）：spec_entropy>2.0 冻结 fan-out 转 B 流水线、rework_rate>50% 降 N/缩单元/升档位门槛。
- **非确定性预算现实（EP §10 风险 7，L381-382）**：低频翻转（10⁻³ 级）检出需千次级重跑——放夜间批任务，不在准入关键路径。

---

## 10. 验收标准与阶段推进

- **阶段进阶条件均为量化硬验收**（EP §7，见第 7 节表格；D22 注明"阶段进阶条件是硬验收"）。
- **迁移梯度进阶条件（SD §12 表，L269-272）**：M0 需 cartographer + spec steward 完成目标域 spec 收割、H1-H4 建立、H7 上线；M1 需场景 holdout 覆盖率达阈值、H5 差分门可用、spec 闭合度稳定；M2 需连续若干波次零逃逸缺陷、judge 与标注集校准一致率达阈值；M3 需稳定运行、deep agent 提案通过率与规则库成熟。
- **核心观测指标（SD §13，L282-290）**：spec 闭合度、spec 熵、判据覆盖率（含 `unverifiable` 条款数）、逃逸缺陷率、漂移率、judge 校准一致率（含弃权率）、返工率与单位准入成本。
- **降级触发（SD L292-298）**：①逃逸缺陷率超阈值→oracle 不可信→回退到需人类 L2 之外额外确认；②judge 校准一致率跌破阈值→软门禁停用（不影响硬门禁）→暂停自动准入；③漂移风暴→冻结 fan-out 转 B 流水线；④单位准入成本超预算且闭合度未改善→降 N/缩单元/提高档位门槛；⑤oracle 与 spec 反复冲突→升级为规范级人类议题。
- **六格判定路由**作为每波次的运行期验收分诊（EP §5.5）：CLOSED→准入；SILENCE/AMBIGUITY→B 流水线收敛；UNDERSPECIFIED→spec 澄清+档位需求记录；SPEC_ORACLE_CONFLICT→规范级会诊；INSUFFICIENT→补采样/统计通道。
- **团队级验收**：T1-T7 各自验收测试（见 §8.2）；CI 上 `python -m pytest swarmforge/tests swarm-app/*/tests` 全绿为合并条件（merge queue 先测后合）。
- **世界仓库推进（EP §10 风险 10，L386-387）**：准入 = git fast-forward 合入 world 分支 + tag（收据哈希引用）；任何绕过事务的直推被 CI 拒绝（branch protection + admit tag 校验钩子）。

---

## 11. 研究采纳决策

### 11.1 已固化进设计的要点（EP L130-134）
1. **LLM-as-judge 多数决 + 三值判定**（弃权永不默认通过）+ **判官档位 ≥ 被测**（EP L131；SD L166 / INV14）。
2. **场景 holdout 私有化 + 双结构判定**（FAIL_TO_PASS + PASS_TO_PASS）+ **拒绝尝试审计**（EP L131-132；SD L162）。
3. **oracle 信号分级**：无断言自测不计入验证强度（EP L132）。
4. **差分四象限输入**：主流程/边界/历史事故/敏感输入（EP L133）。
5. **SemVer 不自律**、破坏性变更由 H4 机械判定（EP L133、L375）。
6. **同质 N ≤ 8 上限**（EP L133、L376）。
7. **判据不可信 → 降自治而非放宽判据**（EP L134、L379-380；SD INV15）。
8. **D21 上下文纪律**：标注"（研究结论强制采纳）"（EP L124），对应 research/ 中 context-management / llm-context-management 等研究。
9. **差分测试为一级硬门禁（H5）**、don't-care 声明区、N 为自适应测量参数（SD §6 推论，L142-144）。

### 11.2 研究输入目录（EP L164；实际存在）
`research/` 下含：llm-as-judge-research、oracle_ci_gate_research、r3-golden-output-research、spec-concurrency-research、spec-traceability-bi-sync-research、tco-optimization-research、context-management-research、llm-context-management-research、信息不对称协议研究、code-search-agent-research、sub_agent_recommendations 等（均含"最终建议/最终报告"类文件），以及顶层散落研究文档（如"测试输入生成与属性测试""差分测试_LLM生成代码""DontCare区与未定义自由""Spec版本化与增量演化"等）。

### 11.3 已在风险清单中固化、执行团队不必再踩的坑（EP §10，L370-387）
1. 临时团队≠不留痕（见 §2.4 纠偏 1）。
2. 门禁配置只读：gate 阈值/rubric/judge prompt 对 builder 只读且版本化（INV6 会话内冻结），变更走提案。
3. SemVer 不自律：兼容性由 H4 机械判定，版本号与变更严重度一致性检查。
4. 同质 fan-out 有上限：N≤8；异构优先（提示策略/档位多样化）。
5. **快照/黄金只证明"没变"不证明"对"**：黄金更新必须独立证据（轨道 B：蜕变/参考实现）+ 人工批准。
6. 判据不可信时降自治：S 未校准（kappa<0.6）则该域不启用软门禁自动准入，转 ESCALATE。
7. 非确定性预算现实：低频翻转放夜间批任务，不在准入关键路径。
8. 跨仓版本碎片：openjiuwen 依赖统一钉 develop commit（jiuwenswarm `Makefile update-openjiuwen`），升级走提案。
9. **静态图盲区**：动态分发/反射调用静态扫不到，"0 依赖"结论按"未证明"处理。
10. 世界仓库：准入 = git fast-forward 合入 world 分支 + tag（收据哈希引用）。

### 11.4 参考文献（SD §15 尾部，L333-334）
- [Spec.md is not the problem. Treating it as the source of truth is.](https://kotrotsos.medium.com/spec-md-is-not-the-problem-treating-it-as-the-source-of-truth-is-46c93afd7f6a)
- [Determinism in the age of LLMs](https://conikeec.substack.com/p/determinism-in-the-age-of-llms)

---

## 附：PDR 术语核实结论
- 本仓库中 **PDR = PDR-001「范式决策记录」（Paradigm Decision Record）**，即 `/workspace/plans/GLM2/structure.md` 这一文档（SD L1；EP L3/L140；swarmforge `__init__.py` L3）。
- 任务提示所称"5 层模型：宪法/规范层/Oracle 层/实例层/世界层"与 SD §4（L79-94）完全一致：**第0层宪法 → 第1层规范 Spec（L1/L2/L3）→ 第2层判据 Oracle → 第3层实例 Instance → 第4层世界 World**（注意：规范层内含 L1/L2/L3 子层）。
- "PDR 层级"不应理解为字面意义的"PDR 文档的层级结构"，而应理解为 PDR-001 文档所定义的**范式五层模型**；本报告 §1.2 已给出完整原文依据。
