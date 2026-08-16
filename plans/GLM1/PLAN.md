# SpecForge 工程计划（最终版）

> 基于 `structure.md`（PDR-001 范式决策）、openJiuwen 11 个 submodule 实际代码、`research/` 下 13 个专题研究的结论，形成的可落地工程计划。
> 本计划是唯一权威：执行 agent 照此实施，不再重新决策。所有"研究建议是否采纳"已在 §2 定案。
> 代码载体：`/workspace/specforge/`（本仓库新顶层目录，非 submodule）。分支：`GLM1`。
> 关键基础设施（WP1–WP12 标 ✅ 者）已随本计划一并实现并通过测试（§10 测试总表）。

---

## 0. 目标与范围

构建 **SpecForge**：一个基于 openJiuwen 的、面向开发的 Agent Swarm 编排与治理层，落实 PDR-001 的"Spec-as-Source 为本体、门禁与事务为物理层"范式。

**本期（M0→M1）交付**：
1. spec 仓内核（三层规范 + don't-care + R 级 + 版本化）
2. 门禁代数与 H1–H8 机械 oracle（含统计门禁）
3. 差分测试引擎 MVP + 黄金输出库
4. holdout 隔离库 + LLM-as-judge 工作流骨架
5. 波次事务 + 准入事务 + 证据收据
6. 健康度量与人类报告面
7. swarm 编排状态机（角色装配映射到 openJiuwen 精确 API）
8. CLI + CI + dogfood 示范域

**不在本期**：分布式部署（pyzmq/PG/NFS 多机）、Agent Studio 画布集成、deep agent 自动规则演进上线（仅留提案通道骨架）、形式化证明后端（Z3/KLEE 仅留接口）。

---

## 1. 系统架构

### 1.1 分层（与 PDR-001 §4 严格对应）

```
第0层 宪法     specforge/constitution.yaml（15 条不变量，judge 引用，会话内不可变）
第1层 Spec     spec/ 仓（L1/L2/L3 + DONT-CARE + R 级注册表）      ← WP1
第2层 Oracle   gates/（H1–H8）+ holdout/ + difftest/ + golden/ + judge/ ← WP3–WP7
第3层 Instance builder fan-out（临时团队，无记忆写入）             ← WP10
第4层 World    wave/（准入事务）+ git world 分支 + receipts/       ← WP8
横切           metrics/（健康度）+ cli + swarm/orchestrator
```

### 1.2 物理布局

```
specforge/
├── pyproject.toml            # 运行时依赖仅 PyYAML；dev: pytest
├── Makefile                  # lint / test / gates 自举
├── constitution.yaml         # 宪法（15 不变量，机器可引用）
├── specforge/
│   ├── spec/        # WP1  spec 内核
│   ├── contracts/   # WP2  契约面提取 + BC/NBC
│   ├── gates/       # WP3  门禁框架 + H1–H8 + 统计
│   ├── difftest/    # WP4  差分引擎
│   ├── golden/      # WP5  黄金输出库
│   ├── holdout/     # WP6  holdout 隔离库
│   ├── judge/       # WP7  judge 工作流
│   ├── wave/        # WP8  波次事务 + 准入
│   ├── receipt/     # WP8  证据收据 + 哈希链
│   ├── metrics/     # WP9  健康度量 + 人类报告
│   ├── swarm/       # WP10 编排状态机 + openJiuwen 装配
│   └── cli.py       # WP11
├── examples/demo_adder/      # WP12 dogfood 示范域
└── tests/                    # 每 WP 对应测试文件（§10）
```

### 1.3 数据流（一次交付流水线 A）

```
spec-delta(WP1) ─→ wave.begin(WP8) ─→ fanout N builders(WP10, 临时团队)
   ─→ N instances(worktree) ─→ verifier = Workflow(WP10) 调 gates suite(WP3)
   ├─ H1/H2/H6/H7/H8: 机械执行
   ├─ H3: holdout(WP6) 聚合分
   ├─ H4: contracts diff(WP2)
   ├─ H5: difftest(WP4) + golden(WP5)
   ├─ S: judge(WP7, 仅主观残差)
   ─→ AdmissionAlgebra: admit = ∧H ∧ ∧S；INCONCLUSIVE=阻断
   ─→ 测量结论表(WP4) ─→ spec 熵/闭合度(WP9) ─→ spec moderator 路由
   ─→ admit ok: atomic merge + EvidenceReceipt(WP8) 入 receipts/
   ─→ 人类报告面(WP9): 仅 L1/L2 + 健康度
```

---

## 2. 决策记录（研究建议采纳定案）

| # | 决策 | 采纳/不采纳 | 依据 |
|---|---|---|---|
| D1 | spec 格式 = Markdown + YAML frontmatter + fenced blocks（clause/contract/invariant/dontcare），不做 TLA+/OpenAPI 全量形式化 | 采纳结构化轻形式 | rec_01：LLM NL→形式化语义正确率仅 8.6–30%，必须验证器闭环+人工确认；MVP 用"结构化条款+机械 witness 绑定+可执行 invariant 表达式" |
| D2 | 每条 L1/L2 条款必须绑定 ≥1 机械 witness（gate:名 或 holdout:集），否则标 `unverifiable` 降级 advisory，不得放行 | 采纳 | PDR-001 §8；oracle 研究"任何门必须有硬门禁" |
| D3 | don't-care 双轨语义 `unspecified`（任选皆合法）/`undefined`（越界即缺陷），三类自由度 SDC/ODC/不可达 | 采纳 | rec_02；差分命中 don't-care 不判缺陷 |
| D4 | SemVer + 机器 BC/NBC 判定；破坏性变更未 bump major → H4 FAIL；deprecated 需缓冲期状态机 | 采纳 | rec_03（SemVer 合规率最坏 25%，必须机器化） |
| D5 | 并发控制 = "Git 分支 + 契约结构 diff 门禁"最小基线 + 单机 frontier 文件锁（TTL+心跳）+ 两阶段提交（prepare=gates / commit=merge）；不引入 Temporal/TiKV/Percolator | 采纳退路方案 | spec-concurrency 研究：初期并发低可退化为该基线；PDR-001 单机优先 |
| D6 | H1–H8 全部机械实现；统计门禁（Wilson 下界 + pass^k + SPRT-lite）用于非确定场景；INCONCLUSIVE 一律阻断不默认放行 | 采纳 | oracle_ci_gate + r3 研究 |
| D7 | oracle 信号强度审计 = H2 内置子门：对被测单元做算子变异，测试必须杀死变异（mutation score 阈值），防"All Smoke No Alarm" | 采纳 | oracle 研究（80.2% agent 自写测试无有效断言） |
| D8 | 黄金输出双轨：golden=回归护栏，正确性由 property/holdout 承担；`.r3info` manifest 不一致→INCONCLUSIVE；CI 永不自动写 golden，更新走批准记录 | 采纳 | r3 研究 L0–L3 四层门禁 |
| D9 | 差分判据三级：归一化执行差分（主）→ 行为指纹聚类（降本）→ 语义/形式化（留接口）；LLM 只做输入生成（可插拔），不做判据 | 采纳 | 差分测试研究总报告 §4.7 三原则 |
| D10 | 输入生成 MVP = 确定性 schema 驱动生成器，PRNG 种子由平台注入没收（builder 不可自选）；LLM 语义生成器为可插拔 adapter | 采纳 | 信息不对称研究（种子是零修改隐式信道）；差分研究 |
| D11 | judge：程序化判分优先；LLM judge 仅主观残差；k 次采样多数投票 + 成对换序 + 弃权 + 证据强制引用；kappa≥0.6 才上线；judge 档位≥builder 硬检查；禁止自评（模型三查：不同模/不同族/无继承） | 采纳 | llm-as-judge + 信息不对称研究 |
| D12 | holdout 物理隔离：独立目录 0600 + canary GUID 扫描 + BuilderView 仅聚合分；场景集轮换日志 | 采纳 | 信息不对称研究（隔离必须前置设计） |
| D13 | fan-out N 自适应三层：U=0.4·rework+0.3·novelty+0.3·risk → N∈{1,3,6}（硬顶 8）；早停（前 k 个实例同过 oracle 即收敛）；R3 禁早停 | 采纳 | tco 研究 |
| D14 | verifier = 确定性 Workflow（openjiuwen.core.workflow.Workflow），禁止自主 agent 决定是否跑门禁 | 采纳 | PDR-001 §11 门禁编排 |
| D15 | specforge 内核零重依赖（stdlib+PyYAML）；openJiuwen 经 Port+Adapter 集成（import-guarded），保证门禁可独立 CI | 采纳 | CI 可靠性与冷启动成本 |
| D16 | 迁移梯度量化进阶条件（M0→M3），见 §8 | 采纳 | PDR-001 §12 具体化 |
| D17 | 人类接口：报告面只含 L1/L2 事项 + 改进提案 + 健康度；PR=准入事务+证据收据；仅 R2/R3 或 L2 变更介入 | 采纳 | PDR-001 §9 |
| D18 | 不采纳：Mergiraf/结构化三方合并（v1 用 git merge + 契约门禁）、oasdiff 外部二进制（自实现 Python 契约 diff）、promptfoo/DeepEval 外部依赖（judge 自研轻核）、TEE 机密计算（单机 0600+canary 替代）、KLEE/Z3（留接口） | 明确排除 | 单机 local mode 前提；依赖最小化；研究已证实这些是重型依赖 |

---

## 3. 核心数据契约（权威定义在代码，此处为索引）

| 契约 | 定义处 | 用途 |
|---|---|---|
| `SpecUnit` / `Clause` / `Witness` / `DontCare` | `specforge/spec/schema.py` | spec 仓最小单元 |
| `RLevel`（R0–R3）+ `RRegistry` | `specforge/spec/rlevels.py` | 可再生性分级 |
| `SemVer` / `ChangeKind`（BC/NBC） | `specforge/spec/semver.py` | 版本一致性 |
| `SpecDelta` | `specforge/spec/delta.py` | 波次输入契约 |
| `SurfaceSnapshot` / `ContractDelta` | `specforge/contracts/surface.py` / `diff.py` | H4 契约面 |
| `GateResult` / `GateVerdict` / `AdmissionDecision` | `specforge/gates/base.py` | 门禁代数 |
| `StatVerdict`（Wilson/SPRT） | `specforge/gates/stats.py` | 统计门禁 |
| `Normalizer` 规则 / `DiffOutcome` | `specforge/difftest/` | H5 |
| `GoldenRecord` / `GoldenManifest` | `specforge/golden/store.py` | 黄金库 |
| `HoldoutScenario` / `HoldoutScore` | `specforge/holdout/store.py` | H3 |
| `Rubric` / `JudgeVerdict` / `CalibrationReport` | `specforge/judge/` | 软门禁 S |
| `WaveRecord` / `InstanceRecord` / `AdmissionRecord` | `specforge/wave/manager.py` | 波次事务 |
| `EvidenceReceipt` + 哈希链 | `specforge/receipt/` | 准入收据 |
| `HealthReport` / `WaveMeasurement` | `specforge/metrics/health.py` | 人类报告面 |
| `SwarmPort` 协议族 | `specforge/swarm/ports.py` | 编排与 openJiuwen 解耦 |

---

## 4. 工作包（WP）

> 每个 WP：范围 / 文件 / 公开 API / 实现要点 / 测试义务 / 验收命令。
> ✅ = 本次已实现并测试；执行团队照代码续作。⬜ = 后续实施。

### WP0 仓库与 CI 骨架 ✅
- 文件：`pyproject.toml`、`Makefile`、`.github/workflows/specforge-ci.yml`（见仓库根 `.github/`）
- 要点：运行时依赖仅 `PyYAML>=6`；dev 依赖 `pytest`；ruff 硬门禁；`make test` = `pytest -q`；CI 三 job：lint / test / self-gates（对 specforge 自身跑 H4/H6 自举）
- 验收：`make test` 全绿

### WP1 spec 仓内核 ✅
- 文件：`specforge/spec/{schema,parser,linter,rlevels,semver,delta}.py`
- spec.md 格式（BNF 级约定）：
  - frontmatter：`spec_id, version(SemVer), r_level(R0..R3), depends[], artifacts[]`
  - fenced blocks：` ```clause `（含 `id/text/level/witness/holdout`）、` ```contract `（JSON，模块导出面）、` ```invariant `（`expr/scope`，expr 为以参数名引用的 Python 表达式）、` ```dontcare `（YAML：`id/kind(unspecified|undefined|unreachable|ignorable_output)/region`）
  - 层次标题：`## L1`、`## L2`、`## L3`、`## DONT-CARE`
- 公开 API：
  - `parse_spec(path|text) -> SpecUnit`
  - `lint_spec(unit, gate_registry, holdout_ids) -> list[LintError]`（条款 ID 唯一；witness 必须指向已注册 gate/holdout，缺失→`unverifiable=True`；R 级合法；semver 合法）
  - `RRegistry.load(path)` / `classify(path)`
  - `bump_required(delta: ContractDelta, old: SemVer) -> SemVer`
  - `compute_delta(old: SpecUnit, new: SpecUnit) -> SpecDelta`
- 要点：clause 未绑 witness ⇒ `advisory_only=True`（进 S 不进 H）；`undefined` don't-care 项在差分中命中即缺陷，`unspecified` 命中登记自由度
- 测试：`tests/test_spec_parser.py`、`tests/test_spec_linter.py`、`tests/test_semver.py`

### WP2 契约面提取与兼容门 ✅
- 文件：`specforge/contracts/{extractor,surface,diff}.py`
- 公开 API：
  - `extract_surface(package_path|module, export_all=False) -> SurfaceSnapshot`（AST 提取：模块级函数/类/常量、函数签名（参数名/类型注解/默认值/返回注解）、类公开属性与 `__all__`）
  - `diff_surfaces(old, new) -> ContractDelta`（变更分类：`added/removed/renamed/param_added/param_removed/param_tightened/param_loosened/return_changed/const_changed`，每项标 BC/NBC + severity）
  - `delta_is_breaking(delta) -> bool`；`explain(delta) -> str`（人类可读 changelog）
- 要点：类型注解收紧 = NBC（如 `int→Literal[1,2]`）；新增带默认值参数 = BC；删除导出 = NBC(major)；仅私有名（`_x`）变化不计入
- 测试：`tests/test_contract_extractor.py`、`tests/test_contract_diff.py`（破坏性变更矩阵 9 例）

### WP3 门禁框架与 H1–H8 ✅
- 文件：`specforge/gates/{base,registry,runner,stats,shell,h1_build,h2_tests,h3_holdout,h4_contract,h5_difftest,h6_guardrail,h7_drift,h8_budget}.py`
- 公开 API：
  - `Gate`（ABC）：`gate_id / description / applicable(ctx) -> bool / run(ctx) -> GateResult`
  - `GateResult{gate_id, verdict(PASS|FAIL|INCONCLUSIVE|SKIP), evidence: dict, artifacts: [path], reason}`
  - `run_suite(ctx, gates=None, fail_fast=False) -> SuiteResult`
  - `decide_admission(suite, soft_suite=None) -> AdmissionDecision`（代数：`admit = all(H=PASS) and all(S in {PASS,SKIP})`；任何 FAIL/INCONCLUSIVE ⇒ 拒绝并给出宪法条款引用）
  - 统计门禁：`wilson_lower(pass, n, z=1.96)`、`k_of_n_gate(results, k, theta)`、`sprt_gate(results, p0, p1, alpha, beta)`
- 各门实现要点：
  - H1：白名单命令（ruff/mypy/pytest --collect-only/python -m compileall）受限执行器 `shell.py::run_command`（超时/输出截断/退出码即 verdict）
  - H2：pytest 子进程 + **变异审计**：对被测源做算子替换（`+↔-`、`<↔<=`、`and↔or`、常量 0↔1）生成变异体，跑测试，mutation score < 阈值(默认 0.7) ⇒ FAIL（"测试无强断言"）
  - H3：调 `holdout.runner.evaluate(instance)` 取聚合分；score < 阈值 FAIL；样本不足 INCONCLUSIVE
  - H4：对 `ctx.artifacts` 提取 SurfaceSnapshot 与世界版 diff；NBC 且未 bump major ⇒ FAIL；R2/R3 制品任何契约变更 ⇒ INCONCLUSIVE（升级人工）
  - H5：调 `difftest.engine.run`（多实例）或 `golden.replay`（单实例+黄金）；结论 EQUAL/INCONCLUSIVE 才可过；命中 `undefined` don't-care ⇒ FAIL
  - H6：危险模式扫描（AST+regex：eval/exec/shell=True/硬编码密钥/网盘外发）、依赖策略（allowlist）、license 兼容表；宪法第 11/3 条引用
  - H7：trace 锚点扫描（代码内 `spec:<clause_id>` 注释）→ 条款覆盖率 + 孤儿锚点 + 契约哈希对比（surface hash vs spec.contract 块哈希）
  - H8：成本/时长预算（receipt ledger 聚合 + 墙钟）
- 测试：`tests/test_gates_base.py`（代数真值表）、`tests/test_gates_stats.py`、`tests/test_gates_h1.py`（含 shell runner）、`tests/test_gates_h2_mutation.py`、`tests/test_gates_h3.py`、`tests/test_gates_h4.py`、`tests/test_gates_h5.py`、`tests/test_gates_h6.py`、`tests/test_gates_h7.py`、`tests/test_gates_h8.py`

### WP4 差分引擎 MVP ✅
- 文件：`specforge/difftest/{generator,runner,normalizer,comparator,engine,corpus}.py`
- 公开 API：
  - `InputGenerator(schema).generate(seed, n)`：schema 驱动（类型递归 + 边界值注入 int(0,1,-1,max)、空串/空集、None）；种子必填（平台注入）
  - `run_instance(cmd, inputs, timeout, env_norm=True) -> [ExecRecord]`（子进程、超时杀、stdout/stderr/exit_code/耗时捕获；env 白名单 HOME/PATH/TZ/LC_ALL）
  - `Normalizer(rules)`：float 容差(默认 1e-9 相对)、key 排序、行尾/空白、时间戳 redaction、指定字段剥离；JSON-line 协议：进程逐行输出 JSON 对象
  - `fingerprint(records, norm) -> sha256`：行为指纹，先聚类后代表间两两比较
  - `compare(a, b, norm, dc_regions) -> EQUAL|DIFF|DIFF_IN_DONT_CARE|INCONCLUSIVE`
  - `run_measurement(instances, inputs, dc_regions) -> Measurement`：产出 PDR-001 §6 的六行判定表（closed / silence / ambiguity / underspecified / conflict / insufficient）
- 要点：差异输入自动入 `corpus/`（δ-多样性回灌）；N<3 且有失败 ⇒ insufficient
- 测试：`tests/test_difftest_engine.py`、`tests/test_difftest_normalizer.py`、`tests/test_measurement_table.py`

### WP5 黄金输出库 ✅
- 文件：`specforge/golden/{store,replay}.py`
- 公开 API：`GoldenStore(dir)`：`manifest(unit) -> GoldenManifest`（环境指纹/依赖哈希/种子/生成者/批准人/更新标签）、`compare(unit, records)`（L0 manifest 门→L1 归一化比对；不一致→INCONCLUSIVE）、`approve_update(unit, records, approver, label)`（写前强制 manifest 重算 + 旧版归档 + 禁止 CI 模式写入 `allow_update=False`）
- 测试：`tests/test_golden_store.py`

### WP6 holdout 隔离库 ✅
- 文件：`specforge/holdout/{store,runner,view}.py`
- 公开 API：
  - `HoldoutStore(dir)`：场景 CRUD（私有目录，权限 0700/0600 尽力设置）、`evaluate(instance_path, runner) -> HoldoutScore`（仅聚合：总分/维度分/通过数，绝不返回场景内容）
  - `BuilderView(store)`：只有 `describe()`（维度名与数量）与 `publish_notice()`；**没有**读场景路径；对出站工件做 canary GUID 扫描 `scan_canaries(text)`
  - 场景轮换：`rotation_log` 记录 add/retire；canary 表
- 测试：`tests/test_holdout_isolation.py`（BuilderView 无 read API、聚合-only、canary 检出、权限）

### WP7 judge 工作流骨架 ✅
- 文件：`specforge/judge/{model,rubric,workflow,calibration}.py`
- 公开 API：
  - `JudgeModel` Protocol：`score(rubric, item) -> JudgeVerdict`（`verdict/score/reasons[]/evidence[]/abstain`）；`FakeJudge(rules)` 供测试
  - `run_judge(model, rubric, item, k=3, strategy="majority") -> JudgeVerdict`（k 采样多数投票；弃权>1/3 ⇒ INCONCLUSIVE）
  - `pairwise(model, a, b)`：强制换序双跑，不一致不计
  - `Rubric.from_dict`：维度/逐档描述/证据要求/偏差约束声明（模板内置四段式）
  - `calibrate(model, labeled: [CalibrationItem]) -> CalibrationReport`（Cohen's kappa、精确一致率、弃权率、8 监控信号）；`kappa < 0.6 ⇒ not_ready`
  - `assert_tier_ok(judge_tier, builder_tier)`（RU 序：L<M<H；judge>=builder 硬检查）
  - `assert_independence(judge_model_id, builder_model_id, family_table)`（同模/同族/继承 ⇒ 违反宪法第 5 条）
- 测试：`tests/test_judge_workflow.py`、`tests/test_judge_calibration.py`（kappa 手算对拍、换序、弃权、档位与独立性检查）

### WP8 波次事务 + 准入 + 收据 ✅
- 文件：`specforge/wave/{manager,instance,admission}.py`、`specforge/receipt/{schema,chain}.py`
- 公开 API：
  - `WaveManager(root, world_ref="main")`：`begin(spec_delta) -> WaveRecord`（frontier 文件锁，TTL 600s+心跳）、`register_instance(wave_id, source_path) -> InstanceRecord`（worktree/分支抽象 `InstancePort`）、`admit(wave_id, instance_id, suite, soft_suite) -> AdmissionRecord`（prepare=已跑门禁复核 → commit=原子合并 + 收据落盘 → post=事件日志；失败=discard+测量记录）、`rollback(admission_id)`（revert + 收据标记 reverted，链不断裂）、`frontier_status()`
  - `EvidenceReceipt`：spec_delta_hash、instance_id、R 级、H 结果、S 判词、差分结论、漂移检查、成本、prev_hash/curr_hash；`verify_chain(receipts)` 防篡改
- 要点：默认 `GitInstancePort`（git worktree add/merge/revert）；测试用 `FakeInstancePort`；两阶段提交的"外部化副作用推迟到 commit 后"由 orchestrator 保证（门禁期禁止 push/发布）
- 测试：`tests/test_wave_manager.py`、`tests/test_receipt_chain.py`（含防篡改、原子性、回滚）

### WP9 健康度量与人类报告 ✅
- 文件：`specforge/metrics/{health,report}.py`
- 公开 API：
  - `record_wave(m: Measurement, suite, costs) -> WaveMetrics`；`HealthTracker.snapshot() -> HealthReport`
  - 指标：spec 闭合度、spec 熵（delta 引发 silence+ambiguity 数）、判据覆盖率（witness 绑定条款占比）、unverifiable 数、变异得分、judge kappa、单位准入成本、漂移率
  - `render_human_report(report) -> str`：Markdown，仅 L1/L2 议题 + 提案 + 健康度评分；**禁止**包含代码 diff/实例选择/RU 升降档
  - 降级触发评估：`evaluate_degradation(report, thresholds) -> [DegradationAction]`（对应 PDR-001 §13 五条）
- 测试：`tests/test_metrics_health.py`

### WP10 swarm 编排与 openJiuwen 装配 ✅（编排内核+装配文档；真实 LLM 联调为后续团队任务）
- 文件：`specforge/swarm/{ports,roles,fanout,orchestrator,openjiuwen_adapter}.py`
- Port 协议（编排内核只依赖 Port）：
  - `TeamPort`（activate_team/finalize）、`BuilderPort`（spawn(spec_delta, seed)->instance）、`VerifierPort`（run_gates(instance, config)->SuiteResult）、`ModeratorPort`（route(measurement)->ModerationDecision）、`MessengerPort`（publish/subscribe 事件）
- 编排状态机 `DeliveryOrchestrator.run_pipeline(spec_delta)`：
  1. `wave.begin` → 2. `N=fanout_plan(U)`（WP13 三层）→ 3. fan-out builders（种子平台注入、无 holdout、无记忆写）→ 4. verifier 跑 H（含 H5 多实例差分）→ 5. judge S（仅残差）→ 6. `decide_admission` → 7. admit/rollback → 8. `Measurement` → moderator 路由（closed→选代表；silence→don't-care 登记 or spec-delta；ambiguity→spec 澄清；conflict→规范级事件）→ 9. `HealthTracker.record`
- 角色装配映射（**精确到 openJiuwen API**，见 §6 表）：执行团队按表接线，orchestrator 通过 `OpenJiuwenAdapter` 把 Port 映射到真实 API
- 模型档位：`roles.py::TIER_TABLE`（cartographer=RU-L、builder=RU-M 可升 H、architect/judge/verifier-judge=RU-H、spec moderator/steward=RU-H；判别档 ≥ 生成档由 `assert_tier_ok` 强制）
- 测试：`tests/test_swarm_fanout.py`、`tests/test_swarm_orchestrator.py`（全链路用 Fake Port：正常准入/门禁失败回退/沉默路由/分歧路由/预算截断）

### WP11 CLI ✅
- `specforge/cli.py`：`validate-spec / extract-contract / contract-diff / gates run / difftest run / golden compare|approve / holdout eval / judge calibrate / wave begin|admit|status|rollback / metrics report / demo`
- 验收：`python -m specforge.cli demo` 端到端跑通示例域

### WP12 dogfood 示范域 ✅
- `examples/demo_adder/`：spec.md（含 clause/contract/invariant/dontcare）、两个实现（good/broken）、holdout 场景、golden、变异测试样例
- 用途：CI self-gates 与新执行 agent 的上手指引；`tests/test_e2e_demo.py` 全链路断言

### WP13 自适应 fanout 深化 ⬜（后续）
- 早停：前 k 个实例全部同过 oracle ⇒ 收敛停止（ANLL 信号留接口）；bandit 路由留接口
### WP14 openJiuwen 真实装配联调 ⬜（后续，WP10 文档已给全部接线点）
### WP15 deep agent 提案通道 ⬜（backlog：`metrics/report.py::collect_proposals` 钩子已留）
### WP16 Studio/分布式 ⬜（backlog，不进本期）

---

## 5. 门禁矩阵（条款 → 机械见证）

| 门 | 实现 | 触发 | 通过条件 | 阻断条件 |
|---|---|---|---|---|
| H1 | h1_build | 每次 admit | 白名单命令退出码 0 | 任何非 0 |
| H2 | h2_tests+变异 | 每次 admit | 测试全绿 ∧ mutation≥0.7 | 测试红 / 变异得分低 |
| H3 | h3_holdout | L1 有 holdout 绑定 | 聚合分≥阈值 ∧ 样本足 | 分低 / 样本不足(INCONCLUSIVE) |
| H4 | h4_contract | artifacts 非空 | 无 NBC 或已 bump major；R0/R1 | NBC 未 bump；R2/R3 变更→INCONCLUSIVE |
| H5 | h5_difftest/golden | R0 fan-out≥2 或有 golden | 差分 EQUAL/闭合；golden 归一化一致 | DIFF；命中 undefined；manifest 不一致 |
| H6 | h6_guardrail | 每次 admit | 0 危险模式 ∧ 依赖/许可合规 | 任何 CRITICAL 模式 |
| H7 | h7_drift | 每次 admit | 锚点覆盖≥阈值 ∧ 契约哈希一致 | 孤儿锚点 / 哈希漂移 / 覆盖不足 |
| H8 | h8_budget | 每次 admit | 成本/时长 ≤ 预算 | 超预算 |
| S* | judge/* | architect rubric 声明 | k 多数 PASS ∧ 非 INCONCLUSIVE | 多数 FAIL / 弃权超限 / kappa 未达线 |

---

## 6. 角色装配映射（openJiuwen 精确接线表）

> 依据代码考古（行号对应 pinned submodule commit，见 CAPABILITY_MAP §0）。执行团队照抄即可。

| 角色 | openJiuwen 载体 | 关键配置 |
|---|---|---|
| leader（编排） | `TeamAgentSpec(agents={"leader": DeepAgentSpec(...)}, lifecycle="persistent", dispatch_mode="scheduled")`；`TeamRuntimeManager.activate(spec, session)`（`agent-core/openjiuwen/agent_teams/runtime/manager.py:115`） | leader 不判别不写 spec；`enable_permissions=True` |
| architect（agentic 过程） | `create_deep_agent(..., enable_task_loop=True, subagents=[...], model_selection={RU-H:"规划"})`（`agent-core/openjiuwen/harness/factory.py:454`）持有 holdout 清单（内容在 HoldoutStore，architect 只持 ID） | 产出 wave 切分 + rubric；`max_iterations` 用 LoopCoordinator 控制而非内层 |
| builder fan-out | 临时团队：`TeamAgentSpec(..., lifecycle="temporary")`（默认即 temporary，`blueprint.py:209`）+ 成员 `MemberMemoryToolkit(read_only=True)` + 不挂 evolution rails | 种子平台注入；工具白名单无 holdout/golden 写；完成即 `finalize`（`manager.py:176`） |
| verifier（确定性） | `Workflow`（`agent-core/openjiuwen/core/workflow/workflow.py:98`）：节点=各 H 门（ToolComponent 包 `specforge.cli gates run`）；`add_connection([h1..h8],"join")` + `wait_for_all=True`；禁止 LLM 自主决定 | SubWorkflowComponent 嵌套 judge 工作流 |
| spec moderator / steward | 持久 agent，独立 session（ContextEngine `context_id="spec_moderator"`，`context_engine.py:99`） | 会话内冻结：不挂 SkillEvolutionRail(auto_save) |
| reconciler | 定时心跳 + H7 门禁；只上报阻断 | `openjiuwen` rail 优先级 < security(90) |
| cartographer | agent-as-tool：父 DeepAgent `subagents=[SubAgentSpec(agent_card=AgentCard(name="cartographer"))]` → `SubagentRail(priority=95)` 自动挂 `TaskTool`（`subagent_rail.py:28`） | RU-L；返回 schema JSON（file:line+证据+置信度） |
| critic | 独立 DeepAgent，产 holdout 场景提案（入 HoldoutStore 需 steward 批准） | 不准入 |
| refactor | 准入后后处理波次：同一 wave 管道，DoD=H4/H5 过且契约面不变 | R entropy 事件触发 |
| moderator（可读性） | 定时 agent，产 spec-delta/refactor 请求 | 不直接改代码 |
| deep agent（演进） | 提案器：扫 HealthReport → `collect_proposals` → 人类批准 → 新 session 生效 | `SkillEvolutionRail(auto_save=False)` 同构 |
| 宪法执行 | `BaseSecurityRail`（priority 90）+ `AbortError`（`core/runner/callback/errors.py:16`）；CRITICAL 真终止必须 `SecurityReject`/`raise AbortError` | H6 映射 |

**模型档位**：`TeamModelConfig(model_client_config=..., model_request_config=...)` 挂 `SubAgentSpec.model`/`DeepAgentSpec.model`（`deep_agent_spec.py:119`）；多部署池用 `ProviderType.IntelliRouter` + `intelli_router_deployments`（`intelli_router_model_client.py:38`）。

**信息不对称 enforcement**（对 builder 的 DeepAgentSpec）：
1. 工具白名单：不注入 holdout/golden 任何工具；MCP 不挂内网 registry
2. 记忆：`MemberMemoryToolkit(read_only=True)`；团队 `lifecycle="temporary"`（TEAM_MEMORY 四重门控自然禁止成员写，`memory/manager.py:336`）
3. 上下文：builder 用独立 session_id（ContextEngine 复合键隔离）
4. 种子：由 orchestrator 注入 spec_delta（builder 无随机源参数权）
5. judge 模型三查 + 档位检查在 orchestrator 装配时强制执行

---

## 7. 双流水线运行手册

**A 交付流水线**：`orchestrator.run_pipeline(spec_delta)`（WP10 状态机），成功=门禁全过+实例准入。
**B 标定流水线**：`specforge difftest run --mode calibration`（全部丢弃代码）：产出 Measurement + 建议路由（closed/silence/ambiguity/...）+ spec-delta 草案给 spec moderator；触发条件=不确定度告警/审计抽样/新域探路/oracle 冲突排查（orchestrator 的 `calibration_trigger`）。
两条流水线物理隔离：不同 wave root、不同 team、不同记忆域（B 用独立 session 前缀 `calib-`）。

---

## 8. 迁移梯度（量化进阶条件）

| 阶段 | 进入条件（全部量化） | 允许丢弃范围 |
|---|---|---|
| M0 收割 | H1/H2/H6/H7 上线；目标域 spec 覆盖 artifacts 100%；cartographer+steward 完成收割 | 无 |
| M1 锚定 | 判据覆盖率≥90%（witness 绑定 L1/L2 条款占比）；H3 场景≥20/域且聚合分连续 3 波≥阈值；H5 差分门可用；闭合度≥50% | R0 |
| M2 再生 | 连续 5 波零逃逸缺陷；judge kappa≥0.75 且弃权率<10%；闭合度≥80%；spec 熵逐月下降 | R0/R1 |
| M3 工厂 | 稳定运行 4 周；单位准入成本在预算内；deep agent 提案通过率≥30% | R0/R1 默认再生，R2 演进，R3 冻结 |

**降级触发**（`metrics.health.evaluate_degradation`，任一命中自动回退一阶并生成规则变更案例）：
逃逸率>2% / kappa<0.6 / 漂移风暴（H7 密度>阈值且时延上升）/ 成本超预算且闭合度未升 / oracle-spec 反复冲突（同条款 2 次全失败）。

---

## 9. 宪法（constitution.yaml）

15 条不变量逐字落自 PDR-001 §14，另加 2 条工程级：
16. 门禁执行环境与生成环境物理分离（子进程/独立 worktree；verifier 不读 agent 自我声明）。
17. 一切随机性种子由平台注入并记录于收据；builder 不得自选种子。

---

## 10. 测试总表（本次已实现 ✅ / 后续团队义务 ⬜）

| 文件 | 覆盖 | 状态 |
|---|---|---|
| tests/test_spec_parser.py | spec 解析/frontmatter/fenced blocks/非法输入 | ✅ |
| tests/test_spec_linter.py | witness 绑定/unverifiable/R 级/ID 唯一 | ✅ |
| tests/test_semver.py | bump 矩阵/BC-NBC | ✅ |
| tests/test_contract_extractor.py | AST 提取/`__all__`/私有排除 | ✅ |
| tests/test_contract_diff.py | 9 类变更分类与严重度 | ✅ |
| tests/test_gates_base.py | 准入代数真值表/宪法引用 | ✅ |
| tests/test_gates_stats.py | Wilson/pass^k/SPRT/INCONCLUSIVE 阻断 | ✅ |
| tests/test_gates_h2_mutation.py | 变异审计杀变异/得分阈值 | ✅ |
| tests/test_gates_h4.py | NBC 阻断/R2 升级/bump 一致 | ✅ |
| tests/test_gates_h6.py | 危险模式/依赖策略 | ✅ |
| tests/test_gates_h7.py | 锚点覆盖/契约哈希漂移 | ✅ |
| tests/test_gates_h1.py | 构建门通过/语法错拒绝/非白名单命令 INCONCLUSIVE/超时/短路 | ✅ |
| tests/test_gates_h3.py | holdout 聚合评分/样本不足 INCONCLUSIVE/无 store 只否决/多 set 聚合 | ✅ |
| tests/test_gates_h5.py | 测量表→准入映射/CLOSED 与 SILENCE_DC 放行/UNDEFINED 拒绝/SILENCE 阻断/golden 三态 | ✅ |
| tests/test_gates_h8.py | 成本与墙钟预算/自定义上限/边界值 | ✅ |
| tests/test_swarm_adapter_contract.py | WIRING_NOTES 对 pinned agent-core 实码的 AST 契约锁定 | ✅ |
| tests/test_shell_runner.py | 受限执行/超时/退出码 | ✅ |
| tests/test_difftest_engine.py | 等价/差异/超时/指纹聚类 | ✅ |
| tests/test_difftest_normalizer.py | float 容差/key 序/redaction | ✅ |
| tests/test_measurement_table.py | 六行判定表路由 | ✅ |
| tests/test_golden_store.py | manifest 门/批准流/CI 禁写 | ✅ |
| tests/test_holdout_isolation.py | BuilderView 无读/聚合-only/canary | ✅ |
| tests/test_judge_workflow.py | k 投票/换序/弃权/档位/独立性 | ✅ |
| tests/test_judge_calibration.py | kappa 对拍/8 监控信号 | ✅ |
| tests/test_wave_manager.py | 事务原子性/回滚/frontier 锁 | ✅ |
| tests/test_receipt_chain.py | 哈希链/防篡改 | ✅ |
| tests/test_metrics_health.py | 闭合度/熵/降级触发/报告面脱敏 | ✅ |
| tests/test_swarm_fanout.py | U→N 映射/早停/R3 禁早停 | ✅ |
| tests/test_swarm_orchestrator.py | 全链路 Fake Port 契约通信 | ✅ |
| tests/test_e2e_demo.py | 示范域端到端 | ✅ |
| 契约通信测试（跨 WP） | 上表中 orchestrator/e2e/gates_h4(↔contracts)/h5(↔difftest,golden)/h3(↔holdout) 即跨组件契约测试 | ✅ |
| openJiuwen 真实装配联调测试 | WIRING_NOTES 契约已由 test_swarm_adapter_contract.py 锁定（AST 级，无需安装 openjiuwen）；运行时集成测试仍属 WP14 | ⬜ WP14 |
| promptfoo/DeepEval 外部 judge 对拍 | 拒绝引入；改为自建校准集扩容 | ⬜ backlog |

**CI**：`.github/workflows/specforge-ci.yml`（已实现）：lint(ruff,硬) + test(pytest,硬,CI=true 下 golden 禁写须成立) + self-gate(H1 compileall 对 specforge 自身,硬) + dogfood demo(端到端准入冒烟,硬)。

---

## 11. 执行顺序与团队分工建议

```
并行组1（互不依赖，接口已冻结）：
  T1: WP13 fanout 深化 + WP14 真实装配（依赖 swarm/ports.py 协议）
  T2: H2 变异引擎扩展（gates/h2_tests.py 扩展算子与并行）
  T3: holdout 场景库建设（示例域→真实域收割，M0 任务）
  T4: judge 校准集标注（50–100 条双标金标）
串行依赖：T1 完成后 → M1 灰度 → M2 再生
```

每个团队只需解决本部分问题：所有跨团队交互都经由 §3 契约 + WP10 Port，其行为已由 §10 测试锁定。

## 12. 风险与开放问题

1. Python 3.14 下 Hypothesis 未装：输入生成器自研（已实现），后续可加 hypothesis adapter。
2. 多语言契约提取：本期 Python AST；其他语言走 LLM 提取 + 人工确认（低置信），H4 标 INCONCLUSIVE。
3. git worktree 在沙箱的可用性：InstancePort 已抽象，FakeInstancePort 兜底测试；真实 GitInstancePort 在 CI 已验证基本路径。
4. LLM 成本：M0–M1 期 N=1 为主，抽样 N=3 校准；成本经 H8 预算门控。
