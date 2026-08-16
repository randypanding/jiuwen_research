# SwarmForge 工程计划（最终版·可执行）

> 本计划是 PDR-001（`structure.md`）的工程落地文档。目标：在 openJiuwen 之上建成
> "Spec-as-Source 为本体、门禁与事务为物理层"的开发 agent swarm。
>
> **状态**：契约内核（`swarmforge/` 包）已实现并通过 134 项测试（含门禁拦截性测试、
> oracle 测试、契约间通信测试、端到端波次流转测试）。各执行团队照本计划在契约之上
> 开发，只需解决本部分内的问题，不需要再做跨模块工程决策。
>
> **如何使用本计划**：§3 的全局决策（D1–D22）不可推翻；§6 的团队分工按团队认领，
> 每个团队读 §5（契约）+ 自己的 §6 小节即可开工；所有 openjiuwen API 引用均已在
> 实际代码中验证（§2）。

---

## 1. 系统一览

```
                    ┌─────────────────────────────────────────────┐
                    │  人类（OPC）：L1 定义/L2 diff 否决/提案批准      │
                    └───────────────┬─────────────────────────────┘
                                    │ report.* / approve.*
        ┌───────────────────────────┼──────────────────────────────┐
        │                   SwarmForge 控制面（本计划范围）           │
        │                                                           │
        │  spec仓 ──→ architect(切波次) ──→ builder×N(临时团队)       │
        │   ↑                                │（不见 holdout/judge） │
        │   │                        verifier(执行 H1-H8 + S)        │
        │   │                                │                      │
        │  spec_moderator ←── 测量结论(六格判定) ──→ admission(2PC)    │
        │   (收敛 spec)                        │证据收据(哈希链)      │
        │  reconciler(H7 漂移)                 ↓                    │
        │  deep_agent(提案) ──→ 人类批准 ──→ 新 session 生效          │
        └───────────────────────────┼──────────────────────────────┘
                                    │ World（已准入代码库，git）
```

两条流水线（物理隔离）：
- **A 交付流水线**：spec-delta → fan-out N → 门禁 → 选一实例准入。
- **B 标定流水线**：不确定度告警/审计抽样触发 → 全部代码丢弃 → 只产出 spec-delta /
  oracle 补强 / don't-care 登记。

## 2. 已验证的 openJiuwen 框架事实（实现依据，均经实地代码核验）

| 能力 | 实际位置（已核验） | 用途 |
|---|---|---|
| TeamRuntime（P2P send + PubSub，topic 支持 `*`/`?` fnmatch 通配） | `agent-core/openjiuwen/core/multi_agent/team_runtime/team_runtime.py`；匹配在 `subscription_manager.py:_match_pattern` | 总线跨进程底座 |
| 团队 harness（TeamAgentSpec / TeamLifecycle TEMPORARY/PERSISTENT） | `agent-core/openjiuwen/agent_teams/schema/blueprint.py:209`、`schema/team.py:74` | builder 临时 fan-out / 判别侧持久团队 |
| 团队记忆（TEAM_MEMORY.md，仅持久团队 leader 在 round-end 可写；四分类 decision/lesson/member/context 是 prompt 约定） | `agent_teams/memory/{shared_memory,extractor,manager}.py`；三重门控 `manager.py:_extract_after_round_bound` | 判别侧裁定写入（INV13） |
| messager（inprocess/pyzmq/hybrid） | `agent_teams/messager/` | 分布式模式传输 |
| spawn（注册与拉起分离；process/inprocess 两模式） | `agent_teams/spawn/` | builder 拉起 |
| worktree 隔离 + 团队工作区（锁/版本/auto_commit） | `openjiuwen/harness/tools/worktree`、`agent_teams/team_workspace/manager.py` | 实例物理隔离 |
| swarmflow 工作流引擎（默认关，`enable_swarmflow`） | `agent_teams/workflow/{engine,runner}.py` | 波次编排可选承载 |
| Workflow IR（组件图 + BranchRouter + LoopGroup） | `openjiuwen/core/workflow/{workflow,components/flow}` | verifier 门禁流水线编排 |
| Checkpointer + interrupt 恢复 | `core/session/checkpointer/` | 波次事务边界/续跑 |
| ContextEngine（session_id+context_id 池化） | `core/context_engine/context_engine.py` | 角色上下文隔离 |
| DeepAgent + AgentRail（priority + 12 钩子 + @rail 装饰器） | `harness/deep_agent.py`、`core/single_agent/rail/base.py` | 角色 rail 装配 |
| Guardrail（事件驱动；RiskLevel.CRITICAL → AbortError） | `core/security/guardrail/guardrail.py` | 宪法机械化（H6） |
| Reliability（Severity → LOCAL_STEER/ESCALATE_USER） | `agent_teams/reliability/` | 异常分级处置 |
| 模型档位（model_pool/model_router/model_intelli_router 三互斥） | `agent_teams/schema/team.py:379-389` | RU-L/M/H 分档 |
| KV 缓存（Anthropic 式消息块 cache_control） | `core/foundation/llm/model_clients/anthropic_model_client.py` | 前缀缓存纪律 |
| jiuwenbox 沙箱（bubblewrap+Landlock+seccomp+网络隔离+egress 白名单） | `jiuwenswarm/jiuwenbox/src/jiuwenbox/supervisor/`；集成 `openjiuwen/extensions/sys_operation/sandbox/providers/jiuwenbox.py` | builder 执行隔离 |
| 技能演进 rail（auto_save=False 人工审批） | `jiuwenswarm/jiuwenswarm/agents/swarm/providers/evolution_rails.py` | deep agent 提案通道 |
| dev_tools.tune / agent_evolving | `openjiuwen/dev_tools/tune/`、`openjiuwen/agent_evolving/`（均完整可用） | 提示词/技能自优化 |

**关键纠偏**（与 `structure.md` §11 假设的差异，已按代码实证修正）：
1. "临时团队只读父记忆、不留痕" **不是框架自动语义**：TEMPORARY 只保证不写
   TEAM_MEMORY.md 与跳过会话持久化调度；仍写 DB 与文件系统。**必须**：(a) builder
   角色不挂任何 memory-write/evolution rail（`harness/roles.py` 白名单已实现）；
   (b) 团队解散走显式 `delete_team(force=True)`。
2. "AgentHints" 类不存在；KV 缓存控制是消息块级 `cache_control`。
3. Studio 的 DSL→IR 与版本发布不在 swarm 内核路径上（多智能体中央路由不用）。
4. Python 版本约束：`>=3.11,<3.14`（jiuwenswarm 与 openjiuwen 一致）。

## 3. 全局决策记录（D1–D22，不可推翻）

- **D1 语言/依赖**：控制面 Python 3.11+。`swarmforge` 核心零三方依赖（仅标准库）
  ——门禁必须能在最简环境机械执行；openjiuwen 仅是可选依赖（`[openjiuwen]` extra，
  只被 bus bridge 与角色装配引用）。
- **D2 spec 物理形态**：文件系统 + git。L2 契约用 JSON（`domains/<domain>.spec.json`）
  ——机械可判等、diff 友好、零依赖；不用 YAML。
- **D3 条款结构**：`clause_id`（REQ-*/CON-*/IMP-*）+ layer + witnesses[] + anchors[]。
  **无见证的 L1/L2 条款 status=unverifiable，只能否决不能放行**（INV3 的可执行形式，
  `specrepo/schema.py:SpecClause.status`）。
- **D4 R 级注册**：首条命中规则生效，未命中默认 R0；`ALLOWED_OPERATIONS`/
  `REQUIRED_GATES` 矩阵驱动操作守卫与门禁选择（INV11）。
- **D5 门禁代数**：`Admit = H ∧ S`；adjudicate 纯函数；blocking FAIL → REJECT，
  INCONCLUSIVE → ESCALATE（永不静默放行）；S 只能 veto/abstain，永不豁免 H。
- **D6 证据来源链**：验证性证据必须由判别侧角色（verifier/architect/ci/sandbox/human）
  产出；builder 自报证据 → EvidenceRejected → ESCALATE（防伪造，已测试）。
- **D7 门禁顺序**（fail-fast，成本升序）：H1 → H6 → H8 → H7 → H2 → H4 → H3 → H5 → S。
- **D8 oracle 双库**：open（builder 可见自测）/ holdout（物理分目录 + 角色强制 + 审计
  日志，拒绝尝试也留痕）。场景 = FAIL_TO_PASS + PASS_TO_PASS 双结构。
- **D9 差分引擎**：与执行解耦（输入执行轨迹）；normalizer 剥非确定性 → 指纹 →
  发散检测 → don't-care 归约 → 扰动复判（不稳定 → INCONCLUSIVE 统计通道）。
- **D10 黄金输出**：manifest（code/deps/seed/normalizer 哈希）不一致 → 比对无效
  （INCONCLUSIVE），绝不据此放行/阻断；字节级精确比对；CI 永不自动写黄金。
- **D11 准入事务**：WAL 两阶段 + 幂等键（delta_id/receipt_id）；崩溃恢复对无终态
  BEGIN 显式 ROLLBACK；rollback 保留测量结论（INV2）。
- **D12 收据账本**：append-only JSONL + 哈希链（防篡改，断点可定位，已测试）。
- **D13 总线**：InProcessBus（单机/测试）+ OpenJiuwenBusAdapter（跨进程，权限矩阵
  前置强制——TeamRuntime 本身无权限概念，不能裸用）；topic 规范 `<域>.<对象>.<动作>`，
  **身份（wave_id 等）放信封不嵌 topic**；deny-by-default 权限矩阵；装配期连线检查
  （悬空订阅/死信/越权声明报错）。
- **D14 自适应 fan-out**：U = 0.4·rework + 0.3·novelty + 0.3·risk(R级)；
  U<0.3→N=1，0.3–0.7→N=3，≥0.7→N=6，硬顶 8；前 k=2 实例全过同组 oracle 即早停；
  **R3 恒 N=1 禁早停**（INV11：冻结制品禁重采样，测量走黄金/统计通道）。
- **D15 模型档位**：RU-L/M/H 三档。角色地板：architect/critic/deep_agent/judge=
  RU-H；builder=RU-M（升不降，R2/R3 任务锁 RU-H 地板）；cartographer/moderator=
  RU-L。INV14：judge 档位 ≥ builder 档位（装配期校验）。
- **D16 角色装配**：RoleSpec（rails 白名单/tools 白名单/memory_writable/lifecycle/
  sandbox policy/model tier）→ 宪法校验（INV5/6/13）→ openjiuwen
  `build_team` 配置片段生成器。builder 恒 temporary + 无记忆写 rail + 无判据工具。
- **D17 沙箱策略**：builder 执行走 jiuwenbox policy（fs 只读 spec 面与自 worktree、
  写仅 staging、网络 isolated + egress 白名单仅模型网关）。
- **D18 H8 预算**：per-wave token/wall-clock 双帽；超限 = 门禁 FAIL（阻断准入而非杀
  进程）；三档计价读数（cached 0.1×/write 1.25×/normal 1×）记入收据 cost 字段。
- **D19 漂移检测**：`@spec:<clause_id>` 注解硬轨 + 四类硬错误（orphan/missing_anchor/
  bypass/stale）直接阻断；R3 路径豁免 missing_anchor；J1 行为契约哈希 = 仅 L2 bound
  条款的规范化哈希（文案润色不触发）。
- **D20 提案通道**：RuleChangeProposal（kind/rationale/evidence_refs/
  effective_from_session）；same-session 生效被机械拒绝（INV6）；批准 ≠ 生效，
  新 session 装载 `effective_for(session)`。
- **D21 上下文纪律**（研究结论强制采纳）：prompt 静态前置（宪法+spec 快照+工具定义
  逐字节稳定）+ 动态后置（测试日志/时间戳/中间结果一律尾部）；builder 之间禁止共享
  中间产物；子 agent 只回传摘要级结果；判别侧与编排侧 session/checkpoint 隔离。
- **D22 迁移梯度**：M0 收割 → M1 锚定 → M2 再生 → M3 工厂（structure.md §12），
  阶段进阶条件是硬验收（见 §7），**oracle 覆盖率不足的域禁止宣布代码可丢弃**。

**采纳研究结论的要点**（详见 `research/`，此处为已固化进设计的部分）：
LLM-as-judge 多数决 + 三值判定（弃权永不默认通过）+ 判官档位 ≥ 被测；场景 holdout
私有化 + 双结构判定 + 拒绝尝试审计；oracle 信号分级（无断言自测不计入验证强度）；
差分四象限输入（主流程/边界/历史事故/敏感输入）；SemVer 不自律、破坏性变更由 H4 机械
判定；同质 N≤8 上限；判据不可信 → 降自治而非放宽判据。

## 4. 仓库与目录结构

```
/workspace（本仓库，superproject）
├── structure.md              # PDR-001 范式（不可变前提）
├── ENGINEERING_PLAN.md       # 本文件
├── swarmforge/               # ✅ 已实现并测试（契约内核，本计划的地基）
│   ├── pyproject.toml        # 零依赖；[openjiuwen] / [test] extras
│   ├── swarmforge/
│   │   ├── constitution/     # 15 条不变量 + ConstitutionViolation + 校验辅助
│   │   ├── specrepo/         # schema(条款/见证/don't-care/delta) + store(原子写/版本链/接口锁) + rregistry
│   │   ├── oracle/           # schema(场景/rubric/judge/golden) + holdout(隔离+审计) + differential(引擎)
│   │   ├── gates/            # algebra(代数+证据链) + h_gates(H1-H8+S) + registry(runner)
│   │   ├── admission/        # wave(状态机) + receipt(哈希链) + transaction(2PC+WAL+恢复)
│   │   ├── bus/              # bus(权限矩阵+连线检查) + bridge(openjiuwen 适配)
│   │   ├── measurement/      # fanout(N 自适应) + classify(六格) + health + 降级
│   │   ├── harness/          # roles(角色装配+宪法校验) + tiers(档位) + proposal(提案)
│   │   └── reconciler.py     # 漂移扫描（H7 证据生产）
│   └── tests/                # ✅ 134 passed（9 个测试文件）
├── swarm-app/                # ⬜ 团队 T1-T7 的实现区（见 §6）
│   ├── orchestrator/         # leader 运行时（wave 编排、事件循环）
│   ├── executor/             # builder 沙箱执行面（openjiuwen 集成）
│   ├── verifier-runner/      # verifier 执行面（H 门执行器 + judge workflow）
│   ├── architect/            # 波次切分 agentic 过程
│   ├── moderation/           # spec moderator/steward/reconciler 常驻
│   ├── calibration/          # B 流水线（标定团队）
│   └── report/               # 人类报告面 + 健康度面板
├── specs/                    # 运行时 spec 仓（git 管理，SpecStore 布局）
└── research/                 # 外脑研究（只读参考）
```

## 5. 契约规格（团队间接口，全部已实现并有测试）

### 5.1 数据契约（swarmforge 中的权威定义）

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

### 5.2 证据 kind 契约（verifier 执行面必须产出的 payload 形态）

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

### 5.3 Topic 命名与权限矩阵（信息不对称的物理层）

Topic（身份放信封）：`wave.sealed / wave.assign.<pool> / build.instance.<id>.completed /
gate.completed / measurement.classified / spec.delta.proposed / admit.committed /
drift.detected / oracle.proposal.* / proposal.submitted / report.health`。

权限矩阵权威定义在 `bus/bus.py` 的 `PUBLISH_MATRIX` / `SUBSCRIBE_MATRIX`（deny-by-default）。
核心不变量（已测试）：builder 永远不能 publish `gate.*`、subscribe `holdout.*`/
`measurement.*`；任何越权 → `BusPermissionError(INV5)`；holdout 场景内容只有
verifier/architect/human/calibration_leader 可读且全部留审计。

### 5.4 波次状态机

`DRAFT → SEALED(接口锁) → FANOUT → VERIFY → CLASSIFY → ADMITTING → COMMITTED`
，`CLASSIFY → CONVERGING → SEALED` 为标定回路；非法转移抛
`IllegalTransition`（表驱动，`admission/wave.py::LEGAL_TRANSITIONS`）。

### 5.5 六格判定 → 处置路由

| 判定 | 条件 | 处置 |
|---|---|---|
| CLOSED | 全过 + 差分等价 | 选实例准入（A 流水线） |
| SILENCE | 全过 + 差分发现 | spec moderator：don't-care 登记或 spec-delta（B） |
| AMBIGUITY | 部分过 | spec moderator 收敛 spec（B） |
| UNDERSPECIFIED | 全败→升档过 | spec 澄清 + 记录档位需求 |
| SPEC_ORACLE_CONFLICT | 全败→升档仍败 | spec steward + architect 会诊（规范级事件） |
| INSUFFICIENT | N<3 有败 / 差分不确定 | 补采样 / 统计通道 |

## 6. 团队分工（T1–T7）：每队只解决自己部分的问题

> 通用 DoD：代码 + 单测 + 与 swarmforge 契约的集成测试全绿；不修改 swarmforge
> 契约定义（发现契约问题走提案通道）；所有事件经总线、所有证据带来源。

### T1 orchestrator（leader 运行时）
- **输入**：`WaveTracker`、`InProcessBus/OpenJiuwenBusAdapter`、`SpecStore`、
  `compute_fanout`、`AdmissionTransaction`、`ReceiptLedger`。
- **职责**：实现 leader 的完整事件循环——
  收 `spec.delta.proposed` → 建波次 → `acquire_lock(InterfaceLock)` →
  `transition(SEALED)` + publish `wave.sealed` → 按波次 R 级并集
  `RRegistry.required_gates()` 计算门禁集合 → `compute_fanout(health.rework_rate,
  novelty, r_level)` 定 N → 逐 builder 发 `wave.assign.<pool>` → 收齐
  `build.instance.*.completed`（或超时重派）→ `transition(VERIFY)` 通知 verifier →
  收 `gate.completed`+`measurement.classified` → 按六格路由：CLOSED→`begin()+commit()`
  准入事务并 publish `admit.committed`；SILENCE/AMBIGUITY→`transition(CONVERGING)` 交
  T5；UNDERSPECIFIED→spec 澄清任务；CONFLICT→publish `report.escalation`。
- **验收测试**：模拟证据注入走完 DRAFT→COMMITTED 与 CONVERGING→SEALED 两回路；
  锁冲突时第二波次正确排队；builder 超时重派幂等。

### T2 executor（builder 执行面）
- **输入**：`builder_role()` RoleSpec、`build_team_spec_fragment()`、jiuwenbox policy。
- **职责**：把 RoleSpec 落成 openjiuwen `TeamAgentSpec`（`agents` dict 用
  `DeepAgentSpec`，`lifecycle=TEMPORARY`，`team_mode=predefined`，
  `spawn_mode=process`，worktree isolation）；写 jiuwenbox policy YAML 模板
  （builder-default：`filesystem_policy.read_only=[specs/,world/.git]`、
  `read_write=[.worktree/<instance>]`、`network.mode=isolated` +
  `egress.allowed_domains=[model-gateway]`）；builder 完成后收产物到 staging 并
  publish `build.instance.<id>.completed`（payload 含 worktree 路径 + diff 清单）。
- **红线**（宪法校验已实现，执行面不得绕过）：builder 无记忆写 rail、无 evolution
  rail、tools 白名单不含 `holdout.read/rubric.read/judge.invoke/golden.verify`；
  builder 间禁止共享中间产物（各自独立 worktree + 独立 session）。
- **验收测试**：装配出的 TeamAgentSpec 片段过 `validate_role`；两个 builder 的
  worktree/session 互不可见；沙箱内越界写被 jiuwenbox 拒绝（集成测试用
  `jiuwenbox-server` internal 模式）。

### T3 verifier-runner（判别执行面）
- **输入**：`GateRunner`、证据 kind 契约（§5.2）、`HoldoutStore`、
  `DifferentialEngine`、`GoldenGate`、`reconciler.check_drift`、`JudgeRubric`。
- **职责**：对每个实例在干净沙箱中依次生产证据——H1（构建：uv/make）、H2（pytest）、
  H3（执行 holdout 场景：场景 stimulus 灌入实例的入口，比对 expected；
  PASS_TO_PASS 回归集）、H4（契约面提取：公开符号/HTTP 面/事件 schema 指纹，与
  world 基线 diff）、H5（N>1 时跑差分：holdout 输入 + `DiffInputGenerator.perturb`
  扰动输入，执行收集轨迹交 `DifferentialEngine.compare`；R3 走
  `GoldenGate.verify_manifest`+`compare`）、H6（从沙箱策略引擎导出违规清单）、
  H7（`check_drift` 扫实例树 vs spec 快照）、H8（从模型网关 usage 账单聚合）、
  S（judge workflow：k=3 采样多数决，rubric 从 `oracle/rubrics/` 装载，
  输出 `JudgeOutput` 列表）。全部证据 `producer_role="verifier"|"ci"|"sandbox"`。
  最后 publish `gate.completed` + `measurement.classified`（含 `classify()` 结果）。
- **judge 实现规范**：判官模型档位 ≥ builder（`validate_tier_assignment`）；
  prompt 四段（任务+维度/逐档 rubric/先依据后 JSON 分/偏差声明）；先证据后结论；
  允许 abstain；判官与 builder 不同族（跨厂商优先）。
- **验收测试**：对 §5.2 每种证据 kind 的生产函数单测；H5 在 N=3 合成实例上复现
  EQUIVALENT/DIFFERENCE_FOUND/INCONCLUSIVE 三态；判词无 evidence_citations 时按
  veto 处理（防无据否决）。

### T4 architect（波次切分 agentic 过程）
- **输入**：`SpecStore`（全量条款+锚点）、`RRegistry`、健康度。
- **职责**：DeepAgent 外层 TaskLoop（`create_deep_agent`）+ Workflow 嵌套：从 spec
  依赖图（条款 anchors 与 witnesses 的引用关系）切割互不相交的 spec-delta 割集；
  为每个新/改 L2 条款绑定见证（gate 引用或提出 holdout 场景草案——场景正文交
  critic 红队后入 holdout 库）；写 DoD 与 rubric 草案；产出
  `SpecDelta + InterfaceLock 条款清单` 给 T1。
- **约束**：architect 不在生成团队内；产出物只经 `spec.delta.proposed` 与
  `wave.plan` 发布；场景草案先标注 `visibility=holdout`。
- **验收测试**：割集条款集两两不相交（能各自获锁）；无见证条款被
  `validate_delta_solvency` 标记；切割结果覆盖率（锚点条款 100% 归属某波次）。

### T5 moderation（spec moderator / steward / reconciler 常驻）
- **输入**：`measurement.classified` 事件、`SpecStore.apply_delta`、
  `DontCareEntry`、`check_drift`、`ProposalBook`。
- **职责**：
  - spec_moderator：收 SILENCE → 对差异维度裁定（登记 don't-care，dimension 用
    glob：`*.receipt_no`）或出 spec-delta（补条款+见证）；收 AMBIGUITY → 收敛条款；
    裁定实现细节是否入团队记忆（写 TEAM_MEMORY.md 仅经持久团队 leader 角色）。
  - spec_steward：条款一致性、版本链维护、SPEC_ORACLE_CONFLICT 会诊。
  - reconciler：定时/心跳对 world HEAD 跑 `check_drift`，报 `drift.detected`，
    只上报不自行改 spec。
- **验收测试**：SILENCE→don't-care 登记→同轨迹复判变 EQUIVALENT（端到端测试已含
  此回路，T5 补充 LLM 裁定 mock）；stale clause 告警到 diff 修复的闭环时延统计。

### T6 calibration（B 流水线标定团队）
- **输入**：`compute_fanout`、`MeasurementLedger`、独立 holdout 副本（不同记忆域）。
- **职责**：审计抽样（周期性对 R0 域跑 N=3 校准 spec 熵）；新领域探路；oracle 冲突
  排查；**全部代码丢弃**，只产出 spec-delta/oracle 补强/案例（走
  `spec.delta.proposed` / `oracle.proposal.*`）。与 A 流水线不同 leader、不同记忆域。
- **验收测试**：标定波次的收据 `instance_id=""`（无一准入）且测量保留；抽样触发的
  N 与 `FanoutConfig` 一致。

### T7 report（人类报告面 + 健康度）
- **输入**：`compute_health`、`check_degradation`、`ReceiptLedger`、`ProposalBook`。
- **职责**：人类可见面**只含** L1/L2 事项、deep agent 提案、健康度评分（闭合度/
  熵/覆盖率/逃逸率/返工率/成本）；R2/R3 或 L2 变更的准入请求列表（human_involved
  审批队列）；降级触发告警。**绝不含**代码 diff、实例选择、RU 升降档细节。
- **验收测试**：报告 schema 字段白名单测试（出现 diff/实例字段即 fail）；提案批准
  后 `effective_for(next_session)` 生效。

## 7. 里程碑（与迁移梯度对齐，进阶条件为硬验收）

| 阶段 | 内容 | 进阶条件（量化） |
|---|---|---|
| P0 地基（✅ 完成） | swarmforge 契约内核 + 134 测试 | 全绿（已完成） |
| P1 执行面 | T1-T3 跑通单域（M0 收割域）端到端：spec→fan-out→门禁→准入→收据 | 连续 20 个波次零未分类异常；H1-H8 全部有真实证据源 |
| P2 收割 | T4+T5 对目标域完成 brownfield spec 收割（L2 从代码反推+锚点+见证绑定）+ H7 上线 | 判据覆盖率 ≥ 70%；bound L2 条款锚点覆盖 100% |
| P3 标定 | T6 上线；don't-care 登记;judge 标注集校准（kappa ≥ 0.6 才启用 S） | spec 闭合度 ≥ 60%；逃逸缺陷率 < 5%（对应 M1→M2） |
| P4 工厂 | R0/R1 默认再生；deep agent 提案通道闭环 | 连续若干波次零逃逸；提案通过率稳定（对应 M3） |

**降级规则**（自动，`check_degradation` 已实现阈值初值）：escape_rate > 5% → 回退
阶段 + 人类额外确认；spec_entropy > 2.0 → 冻结 fan-out 转 B 流水线；rework_rate >
50% → 降 N/缩单元/升档位门槛。降级永远是回退阶段，不是改判据；判据变更只走提案。

## 8. 测试策略（门禁自身也要被测——已执行）

已实现（`swarmforge/tests/`，134 项全绿）：
1. **门禁拦截性**：每个 H 门构造坏证据样本必须 FAIL（H1 构建失败/H2 属性失败/H3
   回归/H4 未声明破坏性变更/H5 沉默与黄金失配/H6 路径越界与违禁依赖/H7 四类漂移/
   H8 超预算）。
2. **代数真值表**：H FAIL 时 S 无法救场；S veto 可否决；abstain 永不默认通过；
   INCONCLUSIVE → ESCALATE。
3. **防绕过**：builder 伪造证据被证据来源链拒绝并升级；总线越权（publish gate.*、
   subscribe holdout.*/measurement.*）抛 INV5；holdout 读取审计含拒绝尝试。
4. **事务**：commit 原子性、失败自动回滚、崩溃恢复、幂等重放；rollback 保留测量
   （INV2）；收据哈希链篡改可定位断点。
5. **契约间通信**：连线检查（悬空订阅/死信/越权声明）；全事件流
   wave.sealed→build→gate→measurement→admit 按权限矩阵流转；审计日志完整。
6. **端到端**：A 流水线全绿准入 + B 流水线沉默→don't-care→复判等价回路 + 信息不
   对称红队（builder 三通道全拒）。
7. **宪法投影**：角色装配（INV5/6/13）、档位（INV14）、提案（INV6 same-session
   拒绝）。

各团队补充：T1-T7 各自验收测试（见 §6）；CI 上 `python -m pytest swarmforge/tests
swarm-app/*/tests` 全绿为合并条件（merge queue 先测后合）。

## 9. 运行配置基线

- 单机模式：`team.runtime.mode=local`（jiuwenswarm config.yaml）；bus 用
  InProcessBus；Checkpointer 用 in_memory/sqlite。
- 分布式（后期）：`mode=distributed` + pyzmq messager + `OpenJiuwenBusAdapter`
  （权限矩阵仍在适配层强制）+ Redis checkpointer。
- 模型池基线（示例，按实际供应商调整）：RU-L=qwen3-30b 级、RU-M=qwen3-max 级、
  RU-H=glm-5 级；`model_pool_strategy="by_model_name"`；judge 与 builder 跨族。
- 前缀缓存纪律：宪法+spec 快照+工具定义置顶且逐字节稳定；所有时间戳/随机 id 出
  前缀区（D21）。

## 10. 风险与已决策的坑（执行团队不必再踩）

1. **临时团队≠不留痕**：见 §2 纠偏 1；builder 装配必须走白名单。
2. **门禁配置只读**：gate 阈值/rubric/judge prompt 对 builder 只读且版本化
   （INV6 会话内冻结）；变更走提案。
3. **SemVer 不自律**：兼容性由 H4 机械判定，版本号与变更严重度一致性检查。
4. **同质 fan-out 有上限**：N≤8；异构优先（提示策略/档位多样化）。
5. **快照/黄金只证明"没变"不证明"对"**：黄金更新必须独立证据（轨道 B：蜕变/参考
   实现）+ 人工批准。
6. **判据不可信时降自治**：S 未校准（kappa<0.6）则该域不启用软门禁自动准入，
   转 ESCALATE。
7. **非确定性预算现实**：低频翻转（10⁻³ 级）检出需千次级重跑——放夜间批任务，
   不在准入关键路径。
8. **跨仓版本碎片**：openjiuwen 依赖统一钉 develop commit（jiuwenswarm
   `Makefile update-openjiuwen`），升级走提案。
9. **静态图盲区**：动态分发/反射调用静态扫不到，"0 依赖"结论按"未证明"处理。
10. **世界仓库**：准入 = git fast-forward 合入 world 分支 + tag（收据哈希引用），
    任何绕过事务的直推被 CI 拒绝（branch protection + admit tag 校验钩子）。

---

## 附：快速验证

```bash
cd /workspace/swarmforge && python3 -m pytest tests/   # 134 passed
```

契约 API 速查：

```python
from swarmforge.specrepo import SpecStore, SpecDocument, SpecClause, SpecDelta, RRegistry, InterfaceLock
from swarmforge.oracle import HoldoutStore, DifferentialEngine, OutputNormalizer, GoldenGate
from swarmforge.gates import GateRunner, GateContext, EvidenceItem
from swarmforge.admission import WaveTracker, AdmissionTransaction, ReceiptLedger, MeasurementLedger
from swarmforge.bus import InProcessBus, Envelope, validate_wiring
from swarmforge.measurement import compute_fanout, classify, ClassifyInput, compute_health
from swarmforge.harness import builder_role, verifier_role, validate_role, validate_tier_assignment
```
