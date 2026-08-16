# OPC Swarm 工作包分解（PLAN_WPS.md）

> 每个 WP 独立可验收：验收标准全部是“跑某命令退出码为 0 / 某测试通过”。执行 agent 按依赖顺序认领；除文中标注的决策外**不需要再做架构判断**。
> 依赖图：WP0(已完成) → WP1 → WP2 → WP3；WP4 依赖 WP2；WP5 依赖 WP1；WP6 依赖 WP1–WP5；WP7 依赖 WP5；WP8 依赖 WP6；WP9 依赖 WP5；WP10 依赖 WP1+WP7。
> 公共纪律：不改 submodule；新增代码过 `ruff check --select E9,F`；每个 WP 必须附测试；提交信息格式 `WP<n>: <摘要>`。

---

## WP0 内核参考实现（已完成，验收通过）

交付物：`opc/`（schemas/specrepo/gates/oracle/diff/world/metrics + 64 测试 + fixtures）。
执行 agent 的第一步永远是：`cd opc && uv venv && uv pip install -e '.[test]' && .venv/bin/python -m pytest tests -q`，确认全绿后再动工；任何后续 WP 破坏该套件即视为回归。

---

## WP1 Spec 仓与工具链

**目标**：建立 `spec/` 真值仓与机械化 lint，锁定条款 ID/见证绑定/R 级声明。

任务：
1. 初始化 `spec/`：`registry.yaml`（`spec_version: 0.1.0`, `migration_stage: M0`）、`policy.yaml`（constitution：`dependency_denylist`、`dangerous_calls_deny`；budget：`max_prompt_tokens/max_completion_tokens/max_p95_latency_ms` 初值由 architect 与人类共同签署）、`L1/<domain>.md` 模板、`L2/<ContractId>.contract.yaml` 模板（从 `opc/src/opc/fixtures_gen.py:CONTRACT_YAML` 复制结构）。
2. 目标域收割（与 WP10 协同）：为选定的第一个域（建议：`opc/` 自身，即“以本项目自身为 brownfield 收割试点”）写 L1 意图 + L2 契约；每条款绑定见证。
3. pre-commit 钩子：`opc-spec-lint --spec-dir spec`（失败阻断提交）；CI 同样运行。
4. 交付 `opc-milestone-check`（新增 `opc/src/opc/milestones.py` + CLI）：读取 registry/场景库/案例台账，输出 §7 晋级条件核对表（JSON + 退出码）。
5. 测试：`tests/unit/test_milestones.py`（构造各阶段状态，断言晋级/滞留判定）。

验收：`opc-spec-lint` 对 `spec/` 退出码 0；故意构造无见证条款时退出码 1（已有测试模式：`tests/gate_semantics/test_gates_e2e.py::TestSpecLintSemantics`）；`opc-milestone-check --stage M0` 在当前状态输出可判定结果。

---

## WP2 Oracle 仓与 holdout 治理

**目标**：`oracle_store/` 策展管线（场景 CRUD + canary + 轮换 + 哈希承诺）。

任务：
1. 目录：`oracle_store/holdout/<domain>/SCN-*.yaml`、`oracle_store/rubrics/*.yaml`、`oracle_store/golden/*.golden.json`、`oracle_store/manifest.jsonl`（每批入库一条：batch_id/时间/场景 id 列表/内容哈希承诺）。
2. 场景编写规范（每域 M1 前 ≥3 个场景，覆盖该域全部 H3 见证）：executable 场景必须含 `expected` 或 `assertions`；无法精确预期时用 metamorphic；rubric 型必须同时在 `rubrics/` 有文件且该条款另有硬见证（advisory 除外）。
3. canary：每场景生成唯一 canary（`CANARY-<rand>-<scn>-<rand>`）；`ScenarioSpec.canary` 已支持。
4. 轮换日历：`swarm/cron/holdout_rotation.md` 运行手册（每月新增 ≥1 批、场景 3 个月退役、退役场景移入 `oracle_store/archive/` 并不再从见证绑定引用）；退役时同步更新契约见证（走人类 L2 diff）。
5. 访问控制：`oracle_store/` 只允许 verifier/architect 服务账号读（文件系统权限 + 打包排除双保险）；builder 沙箱挂载白名单不含该路径（jiuwenbox 配置项见 PLAN_HARNESS §7）。
6. 测试：场景 schema 校验测试（非法场景被拒）；`opc-oracle --holdout-dir oracle_store/holdout --instance-dir opc/fixtures/instances/inst-a` 退出码 0。

验收：`opc/tests/contract` 的 sanitizer 测试继续通过；新增“轮换演练”脚本 `scripts/rotate_holdout.sh`（演练态）跑通一次；manifest.jsonl 哈希与文件一致（提供 `opc-oracle-verify` 子命令）。

---

## WP3 CI 门禁集成

**目标**：门禁成为不可绕过的机械闸门。

任务：
1. `.github/workflows/opc-gates.yml`：PR 触发；jobs：`lint`（ruff E9,F）、`unit`（opc 全套 pytest）、`contract`（tests/contract 单列必需）、`gates-demo`（对 fixtures inst-a 跑 opc-gate-runner，期望：无 waiver 时 H5 阻断，验证门禁未被架空）。
2. 分支保护：`main` 必需上述 check；禁止 agent 服务账号推送 `.github/`、`opc/gates/`、`opc/schemas/`（路径规则 + CODEOWNERS=人类）。
3. GateReport 归档：verifier 每次运行把报告 JSON 写入 `world/artifacts/<wave>/<instance>/<gate>.json`，收据以相对路径引用（H8 的审计面）。
4. 静态边界检查：`import-linter` 契约文件 `.importlinter`：禁止 `swarm.*` 直接 import `opc.gates.*` 内部实现（只能经 `opc.gates.runner`/`base`）；禁止任何模块 import `oracle_store` 内容到 builder 侧包。
5. 测试：workflow 本地等价脚本 `scripts/ci_local.sh`（无 GitHub 环境下复现同一 job 序列，退出码语义一致）。

验收：`scripts/ci_local.sh` 退出码 0；人为把某门禁判 PASS 改为 FAIL 后脚本退出码 1（变异自检，防门禁空转——oracle 信号质检思想用于门禁自身）。

---

## WP4 Judge 接入与校准

**目标**：S 门从协议落到真实模型，并完成上线校准。

任务：
1. `swarm/judge/openjiuwen_judge.py`：实现 `JudgeClient`，经 agent-core `BaseModelClient`（`agent-core/openjiuwen/core/foundation/llm/model_clients/base_model_client.py:44`）调用 judge 档位模型；prompt 四段式（任务→rubric 档位→CoT→JSON），输出 schema 固定为 `{verdict, reasons[], evidence[]}`；无证据输出由工作流丢弃（已实现）。
2. rubric 库：`oracle_store/rubrics/RUB-*.yaml`（每域 ≥1，含维度/权重/档位描述）；rubric 变更走人类批准（diff 评审）。
3. 校准集：人工标注 50–100 条 `{RelayPackage, 人类判词}`，存 `oracle_store/calibration/<domain>.jsonl`（标注人=人类+architect 双人）。
4. 校准程序 `swarm/judge/calibrate.py`：Cohen kappa（阈值 0.6）+ 重测稳定性（同题重判一致率 ≥0.9）+ 位置/长度偏差审计（交换顺序一致率）；输出 `calibration_report.json`，未达标则 S 门在 `tiers.yaml` 中标记 disabled。
5. 模型关系登记：`swarm/tiers.yaml` 增加 `families`/`descendants` 映射，供 `ModelLineageRegistry` 消费；judge 档位 rank ≥ builder 档位 rank（工作流已强制）。
6. 测试：用 MockJudge 覆盖“真实客户端的适配层”（序列化/重试/超时）；校准脚本对合成标注数据（故意一致/故意分裂）给出正确的达标/不达标结论。

验收：`calibrate.py` 在合成数据上 kappa 计算正确（与手工计算一致）；S 门 disabled 状态下 runner 行为为“S=INCONCLUSIVE 阻断”（已有语义测试）。

---

## WP5 角色 Harness（swarm/ 骨架）

**目标**：把 PDR-001 §10 的 12 个角色全部落成可运行的 jiuwenswarm 配置+rail。接线细节见 `PLAN_HARNESS.md`，此处列交付物：

1. `swarm/tiers.yaml`：RU-L/RU-M/RU-H 三档模型绑定（`models.defaults` 引用）+ 角色默认档位 + 升级规则（builder Oracle 失败→RU-H，≤2 次）+ judge 档位地板。
2. `swarm/roles/*.yaml`：12 个角色卡（AgentCard 字段：name/description + DeepAgentSpec 片段：tools 白名单/rails/skills/max_iterations/context_engine_config）。
3. `swarm/teams/governance.yaml`（persistent 队：leader/spec_steward/spec_moderator/reconciler）、`delivery.yaml`（temporary 模板：delivery-leader + spawn builder）、`calibration.yaml`（独立记忆域）。
4. `swarm/rails/`：
   - `constitution_rail.py`（BaseGuardrail 子类：危险工具调用→CRITICAL→AbortError，映射 H6 运行时侧）
   - `builder_isolation_rail.py`（builder 侧：拦截对 oracle_store 路径的读写工具调用；出站内容扫描）
   - `judge_freeze_rail.py`（session 内禁止 rubric/judge 配置变更的写工具）
   - `verifier_determinism_rail.py`（verifier 工作流内禁止 LLM 决策节点，仅允许脚本调用）
   - `feedback_redaction_rail.py`（leader→builder 返工消息过滤器：只保留门/check id/摘要，剔除场景输入与期望值）
   - `watchdog_rail.py`（消费 metrics：降级触发 → 调 `opc-milestone-check --demote` 并生成案例记录）
5. rail 测试：每个 rail 一个 pytest（模拟 ctx 输入断言拦截/放行；参照 `jiuwenswarm/agents/harness/team/rails/team_permission_policy_rail.py:15` 的写法）。

验收：`pytest swarm/tests -q` 全绿；`swarm/validate.py` 用 agent-core 的 `DeepAgentSpec.model_validate` 校验全部角色 YAML 可解析（离线构建，不实际调用模型）。

---

## WP6 波次编排器（leader/world 运行时）

**目标**：把 §6.1 时序变成可运行的单机进程。

任务：
1. `swarm/orchestrator/wave_planner.py`：architect 侧工具——输入 spec 依赖图（契约间 l1_refs/interface 引用），输出波次割集（拓扑分层，环=报错）；产出 WaveManifest（fanout_n 由不确定度模糊规则：返工率 0.4/新颖性 0.3/R 级 0.3，阈值 0.3/0.7，N∈{1,3,6}，上限 6；R3 或新颖性>0.8 强制高档）。
2. `swarm/orchestrator/dispatch.py`：leader 侧——经 `team.create_task` 派发 builder 任务（payload 含 bundle_hash、契约 id、R 级、返工预算）；builder 侧 spawn 用 `lifecycle=temporary`。
3. `swarm/orchestrator/verify_pipeline.py`：verifier 确定性管线——按序调用 `opc-gate` CLI（子进程、退出码判定），收集 GateReport，写 `world/artifacts/`；对 N≥2 波次调用 H5 差分（corpus=`oracle_store/corpus/<domain>.json`，由 architect 维护）。
4. `swarm/orchestrator/admit.py`：world 侧——`AdmissionController` 事务（staging→admit→commit/abort），merge 策略=`--no-ff` wave 分支；abort 时 git revert + 补偿记录。
5. `swarm/orchestrator/measurement.py`：丢弃实例测量结论 + 差分报告 → MEASUREMENT_REPORT envelope → spec_moderator 队列（SQLite 持久化，`world/queues.db`）。
6. 测试：以 fixtures payments 域跑**离线端到端**（mock team.* 调用层，真跑 opc-gate 子进程）：三实例波次 → inst-a 准入、inst-b 丢弃（带结论）、inst-c 触发沉默事件路由到 moderator 队列；断言账本长度、envelope 序列、无 builder 泄漏。

验收：`pytest swarm/tests/test_wave_e2e.py -q` 全绿；`swarm/demo/run_wave_demo.sh` 在无人干预下跑完一个波次并打印收据摘要。

---

## WP7 cartographer 与上下文经济

**目标**：代码定位 agent-as-tool（弱档高缓存），保护主链路缓存与上下文纯净。

任务：
1. `cartographer/indexer.py`：universal-ctags 符号表 + ripgrep 词法 + tree-sitter 结构图（调用/导入），增量（git diff 触发重建受影响文件）；索引落 `cartographer/.index/`（gitignore）。
2. `cartographer/service.py`：MCP 风格三工具面（最小工具面）：`locate(query) -> 证据包`、`impact(symbol) -> 影响闭包`、`ci_diagnose(failure_log) -> 定位+诊断注入`（SHERLOC 式）。返回 schema 冻结：`{status, answer_summary≤150tok, locations[{path,lines,symbol,confidence}], graph_evidence, token_budget_used, stale_warning}`（与 PLAN.md §4.3 上下文研究结论一致）。
3. 作为 TaskTool 子 agent 挂载（`SubAgentConfig` + RU-L 档），主 agent 行为路由：`PreToolUse` hook 拦截对大文件的全量读取并改道 `locate`。
4. 缓存纪律：cartographer prompt 前缀（角色卡+工具定义+索引摘要）逐字节稳定；查询追加在尾部；返回体恒定 schema（KV 前缀缓存友好）。
5. 测试：对 `opc/` 仓自建索引，查询“H5 差分判定在哪个文件”返回 `opc/src/opc/diff/engine.py` 及行段；`ci_diagnose` 对注入的 pytest 失败日志返回正确文件。

验收：`pytest cartographer/tests -q` 全绿；定位评测集 ≥20 条，file 级命中率 ≥80%（评测脚本入库）。

---

## WP8 健康指标与降级 watchdog

任务：
1. `swarm/metrics/collector.py`：从 ledger/artifacts/queues 汇总 `WaveMeasurement`（闭合度、沉默/分歧事件、token、返工、漂移告警、judge 判词）→ `world/metrics.jsonl`。
2. 健康日报：`opc-health`（调 `opc.metrics.compute_health`）输出 JSON+人类可读摘要，仅含 L1/L2 相关事项（不含代码 diff/实例选择细节——人类报告面约束）。
3. `watchdog_rail.py` 落地降级触发 1–5（PLAN.md §7）：每条触发对应一个可单测的规则函数；降级动作=修改 `registry.yaml:migration_stage`（走人类批准队列）+ 案例记录（WP9 提案格式）。
4. 测试：合成 4 周数据触发各降级路径；断言 stage 回退与案例生成。

验收：`pytest swarm/tests/test_watchdog.py -q` 全绿；`opc-health --json` 字段与 `HealthSnapshot` schema 一致。

---

## WP9 规则变更提案通道（deep agent）

任务：
1. `swarm/proposals/schema.py`：`Proposal{proposal_id, kind: rule_change|ru_change|tier_change|harness_change, case_refs[], diff 描述, 影响面, 状态}`；状态机 `draft→submitted→approved/rejected→effective(next session)`。
2. deep agent 只提案不生效：提案写入 `world/proposals/`；生效必须由人类在 `human_gateway` 批准后写入对应配置，并**仅对新 session 生效**（jiuwenswarm 会话隔离天然满足；配置加载发生在会话启动）。
3. 冻结不变量守卫：`judge_freeze_rail` + CI 检查“当前 session 内 rubric/门禁定义文件哈希不变”（会话开始时记录基线哈希）。
4. 测试：提案状态机全路径；“未批准提案不得改变任何门禁行为”回归测试（构造提案后跑 runner，断言行为不变）。

验收：`pytest swarm/tests/test_proposals.py -q` 全绿。

---

## WP10 brownfield 收割试点（M0 主战役）

**目标域**：`opc/` 自身 + jiuwenswarm 团队协作面（team.* 协议）。

任务：
1. cartographer 对目标域建索引；spec_steward（人类共写）产出 L1 意图（≤1 页/域）。
2. L2 收割：从现有代码接口面（`opc.gates.surface.extract_surface` 可直接用于 opc 域；jiuwenswarm 域用 ctags）生成契约初稿 → 人类 diff 评审 → 见证绑定（H2 目标=现有测试节点；H3 场景新写 ≥3/域）。
3. H7 告警模式运行一周：对世界主树每日跑结构通道，误报台账清零后转阻断（WP3 的 CI 开关）。
4. Daikon 式候选（可选）：对 opc 跑测试轨迹挖不变量，作为 postcondition 候选供人类筛选（研究 rec_01 采纳项，置信过滤后才入契约）。

验收：`opc-milestone-check --stage M0→M1` 判定通过；两域契约 lint 全绿；H7 告警模式 7 天日志归档。

---

## 执行顺序与并行窗口

```
周1: WP1 + WP2（并行） + WP3
周2: WP4 + WP5（并行）
周3: WP6（依赖 1–5 集成）+ WP7 并行
周4: WP8 + WP9 + WP10 启动（M0 收割进入观察期）
```
集成验收（每周末）：`scripts/ci_local.sh` + `opc` 全套测试 + 当周 WP 验收命令全绿；任何破坏契约测试的改动必须回滚。
