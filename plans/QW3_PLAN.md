# OPC 开发 Swarm 最终工程计划（PLAN.md · 主文档）

> 输入：`structure.md`（PDR-001 范式决策记录，前提约束，不重开）；`research/` 全部研究结论（外脑建议，采纳与否见 §3）；openJiuwen 实际代码（11 个 submodule，已检出并核对）。
> 输出：本文档 + `PLAN_WPS.md`（任务分解）+ `PLAN_HARNESS.md`(角色接线) + `PLAN_CI.md`（门禁与校准）+ `opc/`（已实测参考实现，64 个测试通过）。
> 执行方式：实施团队按 `PLAN_WPS.md` 的 WP 认领任务；每个 WP 的验收标准是机械可判定的（测试/门禁退出码），不需要再做架构决策——所有跨模块决策已由本文档锁定。

---

## 1. 系统定位与边界

在 openJiuwen（Agent Core + JiuwenSwarm Harness 为主，Agent Studio 不参与运行时）之上构建 **OPC 型开发 swarm**：1 名人类 + N 个 agent，按 PDR-001 的「Spec-as-Source 本体 + 门禁与事务物理层」运行。

五层对应（PDR-001 §4）：

| 层 | 承载 | 实现 |
|---|---|---|
| 0 宪法 | 不可协商不变量 | `opc/fixtures/policy.yaml constitution` + H6 静态扫描 + jiuwenswarm Permission/Security rails + jiuwenbox 沙箱 |
| 1 规范 Spec | 唯一真值 | `spec/` 仓（L1/L2/L3 + registry.yaml），`opc-specrepo` 工具链 |
| 2 判据 Oracle | 场景 holdout + 机械见证 + judge rubric | `oracle_store/`（holdout + rubrics），`opc-oracle`，architect 持有 |
| 3 实例 Instance | 可丢弃代码 | 波次 staging 目录（git 分支），builder fan-out 产出 |
| 4 世界 World | 已准入代码库 | `world/` 主分支 + 准入账本 `ledger.jsonl` |

**不做清单（负范围，防止范围漂移）**：
1. 不修改任何 submodule 源码；一切通过扩展点（rails / extensions / providers / 配置）实现。上游缺口走提案通道。
2. 不使用 Studio 中央路由（PDR-001 §11 已排除）；不引入 A2X 分布式（`team.runtime.mode=local`）。
3. 不做无人化双向同步（spec→code 再生只做“标记待更新 + 定向再生试点”，见 spec-bi-sync 研究结论）。
4. P0 不做学习式路由/bandit、不做 TEE、不做 MPC；均为 P2+ 可选项。
5. 不触碰 C++/Java 组件（agent-protocol SDK、agent-studio 后端、agent-memory 平台）。

---

## 2. 工程决策记录（D1–D15，全部已锁定）

| 编号 | 决策 | 内容 | 理由/证据 |
|---|---|---|---|
| D1 | 语言栈 | Python ≥3.11、uv、pydantic v2、PyYAML、pytest、ruff(`--select E9,F`)、hypothesis | agent-core/jiuwenswarm 均为 Python；不引入第二运行时 |
| D2 | 代码布局 | 本仓新增 `opc/`（内核，已交付）、`swarm/`（角色 harness）、`spec/`、`oracle_store/`、`world/`、`.github/workflows/` | 与 submodule 物理隔离；submodule 只读 |
| D3 | Spec 仓结构 | `spec/registry.yaml`（spec_version+migration_stage）、`spec/L1/<domain>.md`、`spec/L2/<ContractId>.contract.yaml`、`spec/policy.yaml`；条款稳定 ID `REQ-<domain>-NNN`；don't-care 条目 `DC-*`（`unspecified`/`undefined` 双轨） | spec-traceability 研究：稳定 ID 是 RTM/漂移门禁的前提；spec-formalization 研究：don't-care 必须显式 |
| D4 | 见证绑定 | 每条款 ≥1 机械见证或显式 `advisory`；见证目标语法：`H2:<test 节点 id>`、`H3:<SCN-id>`、`S:<rubric id>`；`opc-spec-lint` 强制（unverifiable 条款只否决不放行） | PDR-001 §8；oracle_ci_gate 研究“无机械见证不得放行” |
| D5 | Oracle 仓 | `oracle_store/holdout/<domain>/SCN-*.yaml`（ScenarioSpec schema，含 canary）、`oracle_store/rubrics/*.yaml`、`oracle_store/golden/*.golden.json`；与 builder 工作区物理隔离，sanitizer+canary 强制；每月轮换 + 哈希承诺 | 信息不对称研究：holdout 策展、新鲜度、canary 取证 |
| D6 | 门禁体系 | H1–H8 均为确定性 CLI（`opc-gate`），统一 `GateReport`（三值判定）；`opc-gate-runner` 合取；waiver 为人类批准、带 owner 与过期时间的 YAML；**INCONCLUSIVE 永不准入**；软门禁 S 单调否决 | PDR-001 §8 门禁代数；`opc/` 已实测（`tests/gate_semantics`） |
| D7 | Judge | `JudgeClient` 协议可插拔；工作流规则固定：k=3 采样、无证据样本丢弃、分裂→弃权、成对换序一致性、模型关系三查（同模/谱系/同族拒绝）、judge 档位 ≥ builder 档位；输出仅 reject/no_reject | llm-as-judge 研究全部最佳实践；`opc/oracle/judge.py` 已实测 |
| D8 | 差分引擎 | 规范化 redaction → 字段路径差分 → don't-care 归域；`min_instances=3` 信息不足规则（全绿但 <3 实例→INCONCLUSIVE）；R3 走 golden 字节级比对；“全部通过+空差分”=spec 闭合信号 | PDR-001 §6；差分测试研究（Csmith/EMI/Mica 范式）；`opc/diff` 已实测 |
| D9 | 波次与准入 | wave=`WaveManifest`（接口冻结+spec-delta 割集）+ git 分支 `wave/<wave_id>`；实例在 staging（权重）；准入=全门禁通过→账本追加→merge（状态）；失败=abort+补偿记录；会话续跑用 agent-core `Checkpointer(type=persistence, db_type=sqlite)` | PDR-001 §5 准入相变；spec-concurrency 研究“波次=唯一原子边界”；`opc/world` 已实测 |
| D10 | 证据收据 | `EvidenceReceipt` 内容寻址 + 哈希链账本；被丢弃实例必须携带测量结论（无结论拒收）；收据包含 H1–H8 报告哈希、judge 判词、差分结论、漂移检查结果 | PDR-001 §9 PR 重定义；`opc/world/ledger.py` 防篡改已实测 |
| D11 | 角色拓扑 | 治理队（persistent：leader/spec_steward/spec_moderator/reconciler）；交付队（temporary：delivery-leader + builder×N，即用即散不写记忆）；标定队（独立队+独立记忆域）；verifier=确定性工作流而非自主 agent；architect=DeepAgent agentic 过程；cartographer=agent-as-tool（弱档高缓存）；deep agent=只提案不生效 | PDR-001 §10；jiuwenswarm lifecycle=temporary/persistent 原生语义（`docs/zh/AgentTeam.md:247-265`、`config.yaml:1216-1222`） |
| D12 | 通信协议 | 跨契约消息统一 `Envelope`+`ROUTING_TABLE`（`opc/world/bus.py`）；运行层映射到 `team.create_task / team.send_message / team.view_task / team.update_task / team.verify_task`（agent-core `agent_teams/tools/tool_task.py:240/450/577/1132`）；信息不对称不变量在 bus 层强制并已测试 | 信息不对称研究：隔离必须在应用层强制，不靠 prompt |
| D13 | 模型档位 | 三档 RU-L/RU-M/RU-H（`swarm/tiers.yaml`）；P0 规则路由：architect=RU-H 固定；builder=RU-M 起、Oracle 失败升 RU-H（单任务最多 2 次）；cartographer=RU-L 固定；judge≥builder；成本经 `usage.json` 归集供 H8 | TCO 研究档位表 + 升级触发；jiuwenswarm `models.defaults` 多配置 + 运行时切换（`config.yaml:235-245`） |
| D14 | 健康与降级 | `opc.metrics.compute_health`：闭合度/spec 熵/弃权率/漂移率/返工率/成本；降级触发由 leader 侧 watchdog rail 判定→回退 `migration_stage` 一级 + 生成案例记录 | PDR-001 §13；`opc/metrics` 已实现 |
| D15 | 迁移梯度 | M0 收割→M1 锚定→M2 再生→M3 工厂；阶段记录在 `registry.yaml:migration_stage`；晋级条件全部机械化（见 §7），不满足则门禁策略自动收紧（低阶段禁止 fan-out 丢弃语义） | PDR-001 §12；`opc-spec-lint` 读取该字段 |

---

## 3. 研究结论采纳裁决

| 研究簇 | 采纳 | 部分采纳/改造 | 不采纳（理由） |
|---|---|---|---|
| oracle_ci_gate | 外部确定性 oracle、执行层隔离（executor/grader 分离）、残差分层、门禁前移、退出码机械化、隐藏/轮换 oracle、oracle 信号质检（无断言测试不计强度） | Wilson 三判定：P0 用三值判定但不上 Wilson 区间（样本量不足，留 P2） | “AI 审 AI 作独立门禁”（与 PDR-001 一致，judge 仅软否决） |
| r3-golden-output | 双轨 oracle（黄金比对护栏 + 独立正确性预言机）、规范化/字段剥离、CI 永不自动写黄金、更新须 diff 评审 + 独立证据、`.r3info` manifest、SPRT 三值（P2） | golden manifest 简化为 `*.golden.json` 内嵌 entrypoint/inputs/expected/redact；SPRT/T² 留 P2 | 直接依赖 Reprise/agrepl（单作者早期，仅作设计参考） |
| llm-as-judge | k 采样+多数、成对换序一致、证据强制、低精度量表、kappa≥0.6 门槛、三协议校准、judge≥builder 档位 | 校准集 50–100 条自建（WP4 交付物） | 高精度 1–10 打分；众包偏好标签 |
| spec-concurrency | 波次=唯一原子边界、staging 收集→裁决→提交→补偿四阶段、frontier 门控思想（提交前确认无更早未完成工作） | P0 用 git 分支 + `opc.world.AdmissionController` 承载事务；不引入 Temporal/TiKV（单机优先，D15） | CRDT 主路线、纯悲观长锁 |
| spec-traceability | 稳定条款 ID、哈希通道（提交清单承诺契约哈希）、结构通道（见证存在性）、先告警后阻断、豁免台账（waiver 带期限）、F2 为主指标 | H7 实现哈希+结构+覆盖三通道；语义通道（LCEF 式 LLM 裁决）留 P1 夜间批处理 | 完全无人双向同步 |
| TCO 优化 | 三角色档位表、Oracle 失败升级（≤2 次）、N∈{1,3,6}、N 硬上限 ≤8、R3 禁早停、前缀稳定化（系统提示+spec 前置、动态内容后置）、缓存命中作一等指标 | 自适应 N 的三信号（返工率/新颖性/R 级）P0 用模糊规则；bandit 校准留 P1 | 学习式路由器 P0 落地（冷启动风险）；GPTCache 语义缓存（误命中风险大于收益，仅观察） |
| 信息不对称 | 隔离前置设计、bus/应用层强制、canary 取证、场景轮换（月度更新 3 个月退役）、反馈降维（仅回传聚合分数）、模型关系三查、judge 不收 builder 推理链（最小充分中继 RelayPackage） | TEE/水印/出口监视器留 P2；P0 用 sanitizer+canary+ROUTING_TABLE 达到同等不变量并有测试 | 零中继（过度隔离伤判别质量） |
| code-search-agent | cartographer=检索代理而非探索代理；BM25+AST 符号为主、dense 兜底；返回证据包（file:line+依据+置信度+最小闭包）；两档预算；行为路由强制；评估用“成功调整后成本” | P0 用 ripgrep+universal-ctags+tree-sitter 自建轻量索引服务；不直接依赖外部 MCP 搜索服务器（多数已停滞） | 纯 agentic 探索子 agent（46.2% 成功率反证） |
| 上下文管理 | 稳定前缀布局（spec 全量入 prompt 且低频变动，正合 PDR-001 C3）、逐出优先于摘要、子 agent 隔离返回 schema（≤150 token 摘要 + 位置）、CORVUS 式文件引用注册表（路径+hash 而非快照） | ContextEngine 用 agent-core 现成 `ContextEngineConfig`（窗口+压缩召回），参数见 PLAN_HARNESS | 静态 AGENTS.md 灌背景（实测负收益） |
| spec 形式化 | pre/post/invariant 作为 L2 断言单元、refinement-as-implication 作版本兼容语义（P1 起用模型检查抽查）、don't-care 显式双轨、SemVer+BC/NBC 机械检查（oasdiff 式规则自研简版） | P0 的 L2 表达式不接模型检查器，先做“可写、可绑定、可差分”；TLC/Why3 后端留 P2 | 自研完整形式化语言内核（本期成本不划算）；nl2spec/fm-universe 微调（数据量不足） |
| 差分测试引擎（顶层） | 多实现互为 oracle（fan-out 即默认形态）、执行差分为主判据、输入语料=固定 corpus+LLM 生成（P1）、失败最小化（P1）、蜕变关系兜底（H3 metamorphic 场景类型） | 符号执行/形式化等价证明留 P2+ | 神经嵌入相似度作判据（只能预筛） |

---

## 4. 系统架构与契约划分

### 4.1 模块与契约

```
                        人类（L1 定义 / L2 diff 否决 / 规则批准）
                                   │  human_gateway 角色
        ┌──────────────────────────┼──────────────────────────────┐
        │                          │                              │
  ┌─────▼─────┐  C1 spec   ┌──────▼──────┐   C5 提案/豁免   ┌────▼─────┐
  │ specrepo  │◄──────────►│  architect  │◄────────────────►│deep_agent│
  │ (spec仓)  │            │ (波次切分)   │                  │(提案器)  │
  └─────┬─────┘            └──────┬──────┘                  └──────────┘
        │ C1                      │ C2 WaveManifest
        │                         ▼
  ┌─────▼─────┐   C6 task   ┌──────────┐   C2' staging   ┌───────────┐
  │ spec_     │◄────────────┤  leader  ├────────────────►│ builders  │
  │ steward/  │             │ (编排)    │                 │ (临时×N)  │
  │ moderator │             └────┬─────┘                 └─────┬─────┘
  └───────────┘                  │                             │ C3 InstanceRecord
                                 │                             ▼
  ┌───────────┐  C4 alarm  ┌─────▼─────┐  C3 submit   ┌───────────────┐
  │reconciler │───────────►│   world   │◄─────────────┤   verifier    │
  │(漂移守护) │            │(准入账本) │              │(确定性工作流: │
  └───────────┘            └───────────┘              │ opc-gate-runner)│
                                                      └───────┬───────┘
                    oracle_store(holdout/rubrics/golden) ◄────┘ 只有 verifier/architect 可读
```

契约清单（全部 schema 在 `opc/src/opc/schemas/`，跨模块通信测试在 `opc/tests/contract/`，已实测）：

| 契约 | Schema | 生产者 | 消费者 | 载体 |
|---|---|---|---|---|
| C1 spec | `ContractSpec`/`SpecRepoManifest` | 人类+architect+spec_steward | 全角色（builder 只见净化副本） | spec 仓 YAML |
| C2 wave | `WaveManifest`/`AdmissionTransaction` | architect/leader | verifier/world | JSON（bus payload） |
| C3 instance | `InstanceRecord`/`GateReport` | builder/verifier | leader/world | bus + 文件系统 |
| C4 oracle | `ScenarioSpec`/`JudgeVerdict`/rubric | architect/critic | verifier/judge | oracle_store + RelayPackage |
| C5 evidence | `EvidenceReceipt`/`LedgerEntry`/`WaiverEntry` | world/人类 | 审计、metrics | ledger.jsonl + waivers.yaml |
| C6 events | `Envelope`/`Topic` + ROUTING_TABLE | 各角色 | bus 订阅者 | EventBus（P0 进程内）→ team.* 工具（运行层） |
| C7 diff | `DiffReport`/`Divergence` | DiffEngine | spec_moderator（沉默/分歧裁决输入） | JSON |

**契约通信不变量（已在 `tests/contract/test_contract_communication.py` 固化为测试）**：
1. 路由合法性：仅 `ROUTING_TABLE` 中的 (src,dst,topic) 可投递；违规 raise 并记入违规日志。
2. builder 只收 `TASK_ASSIGN`；其 payload 出现 `scenarios/rubric/judge_verdict/golden_outputs` 等 oracle 侧键即阻断。
3. `INSTANCE_SUBMIT` 只能由 builder 发出。
4. builder 工作区打包（sanitizer）排除 oracle/holdout/golden 目录；canary 或场景本体出现即 `HoldoutLeak`。
5. judge 只消费 `RelayPackage`（claims+evidence+scenario_ids），builder 推理链与 rubric 不外泄。
6. 账本 append-only，哈希链可验证；篡改任意条目 verify() 必失败。
7. 被丢弃实例无测量结论 → 拒收（AdmissionError）。

### 4.2 门禁到角色的守护映射（PDR-001 §8 落地）

| 门 | 实现 | 守护对象 | 执行者 | 阶段策略 |
|---|---|---|---|---|
| H1 | `opc-gate --gate H1`：compileall + ruff(`E9,F`) | 语法/结构底线 | verifier | 全阶段必需 |
| H2 | `opc-gate --gate H2`：pytest 退出码 + **oracle 信号质检**（AST 扫描无断言测试，“All Smoke No Alarm”防线） | 局部行为 | verifier | 全阶段必需 |
| H3 | `opc-gate --gate H3`：holdout 场景执行（executable/metamorphic），必需场景集=契约 H3 见证并集 | L1 意图主体 | verifier（唯一持有 holdout 读权） | 全阶段必需；无绑定场景=拒绝准入 |
| H4 | `opc-gate --gate H4`：AST 公开面提取 + 对世界基线的破坏性变更检测（R0 限契约符号，R1+ 全公开面） | L2 机械见证、R1/R2 兼容 | verifier | 有基线即启用 |
| H5 | `opc-gate --gate H5`：golden（R3）/fan-out 差分（N≥2）；N=1 且无 golden → INCONCLUSIVE，仅 waiver 可过 | spec 沉默、R3 逐行语义 | verifier | M1 起必需 |
| H6 | `opc-gate --gate H6`：secret 扫描 + 危险调用 AST 黑名单 + 依赖 denylist（`policy.yaml constitution`） | 宪法可机械化部分 | verifier | 全阶段必需 |
| H7 | `opc-gate --gate H7`：提交清单契约哈希（SpecSeal 式）+ 见证存在性 + 接口符号存在 + 覆盖复核 | 真值一致性 | verifier+reconciler（运行期巡检） | 全阶段必需 |
| H8 | `opc-gate --gate H8`：usage.json token 预算 + bench.json 延迟预算 | 经济与非功能 | verifier | 全阶段必需（无证据=INCONCLUSIVE） |
| S | `JudgeWorkflow`（rubric 外置，k=3，弃权即否决） | 不可机械化残差 | judge（独立档位） | M1 起启用；校准不达标自动停用（降级触发 2） |

### 4.3 信息不对称强制面（物理+协议）

| 边界 | 机制 | 验证 |
|---|---|---|
| builder ⇏ holdout | sanitizer 打包（排除目录+canary+本体扫描）；holdout 仓独立目录权限 | `test_builder_bundle_*` |
| builder ⇏ rubric | RelayPackage 最小中继；ROUTING_TABLE 无 builder→judge 直连 | `test_relay_never_carries_raw_reasoning` |
| 生成者 ⇏ 判别 | builder 不订阅 GATE_REPORT/MEASUREMENT_REPORT；INSTANCE_SUBMIT 只进 verifier | `test_builder_only_receives_task_assign` |
| judge 独立性 | 模型关系三查 + 档位地板，工作流内建拒绝 | `test_judge_same_family_refused`/`test_judge_weaker_tier_refused` |
| 反馈降维 | builder 收到的返工信息仅含“失败门 + check id + 摘要”，不含场景输入/期望值（WP6 实现 leader 侧过滤器，附测试） | WP6 验收项 |

---

## 5. 数据与目录布局（目标态）

```
/workspace
├── PLAN.md / PLAN_WPS.md / PLAN_HARNESS.md / PLAN_CI.md   # 本计划
├── opc/                     # 参考实现（已交付，测试全绿）
│   ├── src/opc/…            # schemas/specrepo/gates/oracle/diff/world/metrics
│   ├── tests/…              # unit + contract + gate_semantics（64 例）
│   └── fixtures/            # payments 演示域（含 4 个实例：正/等价/分歧/恶意）
├── spec/                    # WP1：spec 仓（registry.yaml/L1/L2/policy.yaml）
├── oracle_store/            # WP2：holdout/rubrics/golden（独立权限，.gitignore 视环境而定）
├── swarm/                   # WP5：角色 harness（tiers.yaml/roles/*.yaml/rails/*.py）
├── world/                   # WP6：主工作树 + ledger.jsonl + waivers.yaml
├── waves/                   # WP6：波次 staging（wave/<id>/…）
├── cartographer/            # WP7：索引与检索服务（BM25+ctags+tree-sitter）
├── agent-core/ … skillhub/  # submodule（只读）
└── .github/workflows/       # WP3：门禁工作流
```

---

## 6. 关键运行时流程

### 6.1 交付流水线（A 线）一波次时序

```
architect 从 spec 依赖图切出波次割集
  → 发布 WaveManifest（C2，含 contract_ids/spec_delta_refs/fanout_n/R 级）
  → leader 校验 fan-out 政策（R2/R3 禁 fan-out）并 team.create_task 派发 N 个 builder 任务
  → 每个 builder 收到净化工作区（sanitizer 输出，bundle_hash 记录在任务 payload）
  → builder 采样实例 → INSTANCE_SUBMIT（携 opc_submission.json：契约哈希+spec_version）
  → verifier 对每实例顺序跑 H1..H8（确定性 CLI），产出 GateReport（C3）
  → H5：同波次实例互相差分（min_instances=3；不足则按 §4.2 处置）
  → judge 对选中候选跑 S（RelayPackage）
  → GateRunner 合取（waiver 校验）→ AdmissionVerdict
  → world.admit()：收据入账（哈希链）→ git merge wave 分支（原子提交）
  → ADMIT_COMMIT 广播；被丢弃实例的测量结论进 MEASUREMENT_REPORT → spec_moderator
失败路径：任一门 FAIL → 该实例 rejected；全部失败 → 升级档位重采（≤2 次）→ 仍败 → 规范级事件（spec moderator+architect 会诊，人类议题）
```

### 6.2 标定流水线（B 线）

触发：闭合度下降/漂移风暴/新领域探路/审计抽样。与 A 线同构但**全部丢弃代码**，产出 spec-delta、oracle 补强、案例记录；使用独立标定队（不同 leader、不同 TEAM_MEMORY 域、独立 session 前缀）。成功定义=定位到沉默/分歧，而非实例通过。

### 6.3 漂移守护（reconciler 心跳）

每 N 分钟（P0=30min）：对每个契约跑 H7 结构/哈希通道 + 世界主树接口面快照对比 → 漂移事件 → DRIFT_ALARM → leader 冻结相关波次 fan-out（降级触发 3）→ 人类裁决台账（waiver 或 spec-delta）。

---

## 7. 里程碑与晋级条件（全部机械判定）

| 阶段 | 范围 | 晋级条件（自动校验脚本 `opc-milestone-check`，WP1 交付） |
|---|---|---|
| M0 收割 | 目标域 spec 收割；H1–H4+H7 上线；cartographer 可用 | 目标域每模块有 L2 契约且 lint 通过；H7 结构通道对世界主树跑通 0 误报（告警模式运行 ≥1 周） |
| M1 锚定 | R0 可丢弃重生；H5 差分门启用；S 启用 | 目标域 H3 场景覆盖：每 L2 契约 ≥3 个 holdout 场景；judge 校准 kappa≥0.6（WP4 标注集）；闭合度基线建立 |
| M2 再生 | R0/R1 常规 fan-out | 连续 3 个波次零逃逸缺陷（逃逸=过 H∧S 后被人举证证伪，登记在案例台账）；judge 弃权率 ≤20% |
| M3 工厂 | R0/R1 默认再生、R2 演进、R3 冻结 | 健康分 ≥ 阈值连续 4 周；提案通道通过率 ≥30% 且无被否决宪法类提案 |

降级触发（PDR-001 §13，watchdog 实现见 PLAN_HARNESS §6）：逃逸率超限→回退一级并加人类确认；kappa 跌破→S 停用；漂移风暴→冻结 fan-out 转 B 线；单位准入成本超预算且闭合度不升→降 N/缩单元；oracle 与 spec 反复冲突→人类议题。

---

## 8. 风险登记册（Top 10）

| # | 风险 | 缓解 | 责任 WP |
|---|---|---|---|
| R1 | 门禁配置被 agent 单方面修改 | 门禁定义文件 CODEOWNERS=人类；CI 中禁止 agent 身份写 `.github/`、`opc/gates/`（分支保护+路径保护） | WP3 |
| R2 | holdout 泄漏（注释/命名/风格隐写） | P0：canary+净化+路由强制；P1：交付侧注释剥离与标识符规范化（信息不对称研究四件套之二）；泄漏=规范级事件 | WP2/WP7 |
| R3 | judge 校准失真 | 三协议校准门禁（kappa/稳定性/偏差审计）不达标 S 自动停用；月度复审 | WP4 |
| R4 | 差分测试“假绿”（环境噪声） | redaction 清单+`elapsed_ms` 类字段默认剔除；失败分诊三分类（真回归/有意变更/噪声）；噪声重复出现→进 don't-care 裁决 | WP6 |
| R5 | 上游 openjiuwen 变更破坏接线 | submodule 指针锁定（本仓 HEAD 已锁 11 个 SHA）；升级走独立 WP + 全量契约测试回归 | 全部 |
| R6 | token 成本失控 | H8 预算门 + swarmflow_budget 团队预算 + 每波次成本入 metrics；超预算触发降 N | WP6/WP8 |
| R7 | 波次悬挂（frontier 停滞） | 波次超时（默认 2h）→abort+补偿；staging 定期清理 | WP6 |
| R8 | 账本/收据丢失 | ledger.jsonl 随主仓 git 提交；收据内容寻址可重建 | WP6 |
| R9 | 逃逸缺陷归因困难 | 收据链+GATE 报告归档（每 PR 附 artifacts 路径）+案例台账 | WP8 |
| R10 | 实施团队绕过契约直连 | 跨模块只允许经 `opc.schemas` + bus；契约测试纳入 CI 必跑；静态检查禁止直接 import 他模块内部符号（ruff/import-linter 规则） | WP3 |

---

## 9. 参考实现（opc/）使用说明

已交付并实测的内核（执行 agent 直接复用/扩展，不得推倒重写）：

- 安装：`cd opc && uv venv --python 3.12 && uv pip install -e '.[test]'`
- 测试：`.venv/bin/python -m pytest tests -q`（64 例全绿）
- CLI：`opc-spec-lint / opc-gate / opc-gate-runner / opc-oracle / opc-diff / opc-admit`
- 演示：`fixtures/` 含 payments 域完整样例（inst-a 正解 / inst-b 等价变体 / inst-c 分歧（半上舍入）/ inst-evil 恶意）
- 扩展点：新门禁=继承 `opc.gates.base.Gate` 并注册 `runner.ALL_GATES`；新场景类型=扩展 `ScenarioRunner`；新 judge 后端=实现 `JudgeClient` 协议

**实测结论摘录**（详见 `opc/tests/`）：
- inst-a 全门通过（H5 以 waiver 放行 N=1）→ admitted=true（软门 S 需另行提供）
- inst-c 触发 H5 FAIL：“2 divergence(s) in constrained region: spec silence or ambiguity candidate”（H2/H3 全绿下检出沉默——C6 仪器生效）
- inst-evil 被 H2（无断言测试）+H6（secret/危险调用）双门拦截
- 契约被篡改后 H7 provenance 通道 FAIL（哈希漂移检出）
- 账本篡改任意条目 verify() 失败；builder 泄漏 canary 触发 HoldoutLeak
