# PR3 深入分析报告：Spec-as-Source Agent Swarm 参考内核实现

> 分析对象：`/workspace/plans/PR3/kernel/`（Python 参考内核，来自 GitHub PR #3 "Reference kernel for the spec-as-source Agent Swarm"）
> 范式依据：`/workspace/plans/PR3/structure.md`（PDR-001「Spec-as-Source 为本体、门禁与事务为物理层」）
> 分析性质：纯研究，未修改任何文件。

---

## 0. 结论摘要

该内核是一个**「契约即机制」的可执行化参考实现**：把 PDR-001 范式决策（spec 为唯一真值、准入 = H∧S、信息不对称、双流水线、R0–R3 可再生性分级）翻译成一组**不可被绕过、只能用构造器表达**的 Pydantic 契约 + 确定性门禁/预言机引擎 + 订阅制信息不对称总线。全代码约 60 个模块文件，`pytest` 实测 **466 个测试全部通过（1.84s）**，是 PR 描述「约 400 测试」的准确数字。

内核最重要的三个设计主张：

1. **软门禁永远不能放行**——用类型系统（`SoftVerdict` 没有 `PASS` 成员）而不是文档来保证。
2. **信息不对称是路由失败而非礼仪**——builder 对 holdout 的不可见是 `ContractBus` 在订阅/投递时机械拒绝的结果，不是提示词里的一句请求。
3. **构造器优于评审清单**——结构性不变量（版本号必须匹配破坏性变更、拒绝必须带理由、代数不能伪造等）全部在 `model_validator` 里强制，任何一个绕过代数的运行时代码都会在构造时报错。

---

## 1. 目录结构与总体设计

```
kernel/
├── pyproject.toml                 # 仅依赖 pydantic>=2.7 + PyYAML；测试依赖 pytest/hypothesis/jsonschema
├── src/swarmkernel/
│   ├── contracts/                 # 契约层：base/gate/spec/oracle/instance/governance/wave
│   ├── gates/                     # 门禁层：algebra/base/hard(H1-H8)/soft
│   ├── oracle/                    # 预言机引擎：dontcare/differ/golden/compat/surface/traceability/strength
│   └── bus/                       # 信息不对称总线：bus/envelope/policy
└── tests/
    ├── conftest.py                # 唯一共享 fixture：完整合法的 UNIT-CART 制品集
    ├── contracts/                 # test_roundtrip / test_structural_invariants
    ├── gates/                     # test_algebra / test_hard_gates / test_soft
    ├── oracle/                    # test_compat/differ/dontcare/golden/strength/traceability
    └── bus/                       # test_asymmetry / test_handoff
```

四层结构严格对齐 PDR-001 §4 的分层（宪法 → 规范 → 判据 → 实例 → 世界）：

- **contracts/**：范式里所有跨团队制品的类型。`Contract` 基类强制三件事（`base.py`）：`ARTIFACT_CLASS` 分类（信息不对称轴）、`CONTRACT_VERSION` 语义化版本（SemVer）、`digest()` 内容寻址（供 H7 漂移检测 / R3 黄金冻结 / 证据收据）。`CONTRACT_REGISTRY`（`contracts/__init__.py`）是**闭集**注册表——不在表内的契约无法穿越团队边界。
- **gates/**：PDR-001 §8 的门禁代数。`algebra.py` 是「全平台最重要的一个决定」，独立纯函数、可穷举性质测试；`hard.py` 实现 H1–H8；`soft.py` 是单调否决器。
- **oracle/**：判据的可执行引擎，全部确定性、离线、无 LLM、无网络、无文件系统依赖（差分引擎的 `DifferentialInput` 就是一个纯 dataclass，注释明说「必须能从单元测试直接调用」）。
- **bus/**：进程内契约总线，把三个失败模式从「被劝阻」变成「不可能」（`bus.py` 头注释）：投递给不该看的人、投递接收方看不懂的版本、丢失谁看了什么的记录。同步、确定性，使整条波次交接链可以在无运行时环境下端到端单测。

每个硬门禁都是一条「从证据到裁决」的纯函数，三条不变量写死在 `gates/base.py`：**沉默不等于同意**（缺证据 → ERROR 而非 PASS）、**失败必须携带 finding**、**永不修改输入**。

---

## 2. contracts/ 模块详解（结构性不变量如何被类型强制）

### 2.1 base.py：版本化、分类、内容寻址

- `SemVer`：最小实现，只保留门禁需要的三种比较（`compatible_with`、`bump(severity)`）。`bump()` 把 `ChangeSeverity` 一比一映射为版本号义务——BREAKING→major+1，ADDITIVE→minor+1，否则 patch+1。
- `ChangeSeverity`：`NONE/PATCH/ADDITIVE/BREAKING`，`rank` 提供偏序，`max_of()` 取最坏项。注释引用了研究结论「3075 个公开 API 中最多 25% 真正遵守 SemVer」——兼容性不能交给纪律，必须机器检查。
- `ArtifactClass`：信息不对称的坐标轴。关键成员 `ORACLE_PUBLIC`（builder 本地可跑的自检子集）与 `ORACLE_HOLDOUT`（场景 holdout + rubric，**永不**对生成者可见）。任何新制品必须在此分类否则总线拒绝路由。
- `Role`：PDR-001 §10 的闭集角色表（HUMAN/LEADER/ARCHITECT/BUILDER/VERIFIER/…/JUDGE），无 ad-hoc 角色。
- `Contract.digest()`：`model_dump(mode="json", exclude=_volatile_fields())` 再 `digest_of`。**易变字段（created_at/produced_at/observed_at）被排除**，保证同一内容在不同时刻 digest 稳定。`canonical_json`（`sort_keys=True, separators=(",",":"), ensure_ascii=False`）是全平台唯一的序列化规则，确定性是 H7/R3 的地基。
- `Contract` 的 `model_post_init`：子类声明 `CONTRACT_VERSION`，除非调用者显式传不同值否则自动继承——保证「契约类声明的版本」与「实例携带的版本」一致。

### 2.2 gate.py：门禁代数的不变量

- `GateStatus`：`PASS/FAIL/ERROR/NOT_APPLICABLE`。`ERROR` 是失败而不是跳过（「跑不起来的门禁不是门禁」）；`admits` 属性只认 PASS 与 NOT_APPLICABLE（后者只能由 R 级注册表声明，不能由实例自封）。
- `GateResult._failure_must_be_explained`：FAIL/ERROR 必须带 finding，否则拒绝构造——「无法行动的失败最终会被关掉」。同时 `GateResult` 只允许硬门禁，软门禁用 `SoftGateResult`（`test_soft_gate_cannot_masquerade_as_hard`）。
- `SoftVerdict`：**没有 PASS 成员**（VETO/NO_VETO/ABSTAIN）。注释：「这是有意为之且承重的」——软门禁无法放行是**说不出口**而不是「约定俗成」。
- `JudgeSample._veto_needs_citation`：无引用的否决无法构造（§8：judge 必须引用证据）。
- `SoftGateResult._judge_not_weaker_than_builder`：judge 档位 < builder 档位直接构造失败（宪法 §14）。
- `HardGateReport.passed`：**缺门禁 == 未通过**（`required - seen` 非空即 False），「沉默从不表示同意」。
- `AdmissionDecision._algebra_holds`：**结构性复述 `Admit = H ∧ ¬S`**。`admitted` 必须等于 `hard_passed and not soft_vetoed`，且拒绝必须带理由——即使绕过了 `algebra.admit()`，伪造的准入记录也无法构造（`test_admission_record_cannot_be_forged`）。

### 2.3 spec.py：规范契约（唯一真值层）

- **Clause 是真值的原子单位**而非整份文档：稳定永不重用的 id、内容 `revision` digest、强制的 witness 绑定。
- 契约语义 = DbC + assume/guarantee：`requires/ensures/invariant`（Meyer 1992）+ `assumes/guarantees`（Pacti / 接口自动机），把环境自由「委派」出去而非逐条指定。
- **Don't-care 是一等公民**：三类别（`DontCareCategory`: output_freedom/unreachable_state/ignorable_output，对应 Damiani & De Micheli 的 SDC/ODC 分类）与双轨道（`FreedomTrack`: unspecified=任一选择合法 / undefined=越界即缺陷，来自 CH2O/Krebbers）。**两条轨道被混用是缺陷**：`DontCareRegion._undefined_has_no_normalizer` 禁止 undefined 区携带 normalizer（否则「到达禁区」会被静默合法化）。
- 只有 safety 与 liveness 可被断言（Alpern-Schneider 分解）——任何没被断言的都是 don't-care **by construction**，这是 spec 膨胀的上界。
- `Clause.is_verifiable`：只要任一 witness 是机械见证（非 NONE/ADVISORY）即可验证。§8 的可执行形式：**无机械见证的 L1/L2 条款只能是 advisory，只能否决不能放行**。`SpecDocument.unverifiable_clauses()` 是它的清点器。
- `SpecDelta._version_bump_matches_severity`：版本号必须携带严重度（oasdiff v1.27 的 `api-version-not-bumped` 检查），构造不一致的 delta 直接报错——BREAKING 必须 major+，ADDITIVE 必须 minor+，PATCH 必须 patch+。
- `RegenerationUnit._consistency`：R2 必须有外部消费者、R3 必须有冻结黄金 id、R0 不得有消费者（PDR-001 §5 的可再生性分级一致性）。
- `RLevel` 属性：`allows_fanout`(R0/R1)、`allows_discard`(仅R0)、`requires_golden`(R3)、`requires_human_approval`(R2/R3)。

### 2.4 oracle.py：判据契约（architect 产出）

类型层面就把两条硬隔离编码进去：

- `OracleBundle` 拆成 **public 半**（builder 可本地运行：properties/metamorphic/smoke）与 **holdout 半**（architect 持有：scenarios/golden/rubric/judge_protocol/mutation_probes），是**不同类、不同 ArtifactClass**，总线据此拒绝把 holdout 路由给生成者。`_halves_agree` 强制两半共享 bundle_id/unit_id。
- `OracleGrade`：BRONZE/SILVER/GOLD/DIAMOND 四级执行级强度，DIAMOND 要求通过**变异探针**——「不能失败的 oracle 是空洞 oracle」。
- `Scenario._must_assert_something` + `_must_bind_a_clause`：断言为空的场景无法构造（空洞场景比没有场景更糟，因为它虚增覆盖率）。
- `JudgeProtocol`：LLM-as-judge 固定 workflow（samples=3、position_swap、require_citation、min_model_tier≥2 等），会话期冻结。
- `MutationProbe`：故意破坏的变体，验证 oracle 本身能检出——这是唯一的、自身无需被信任的机械防空洞工具。
- `RubricCriterion` 的 `veto_when` 刻意用否定句书写——rubric 只能移除实例。

### 2.5 instance.py：实例契约（可丢弃的采样）

- `InstanceManifest` 刻意很薄（instance_id/unit_id/spec_version/delta_id/builder_id/model_tier/seed/tree_digest）。
- `InstanceReport._no_holdout_leakage`：**结构性绊线**——builder 的 notes 里出现 `holdout/rubric/scenario:` 字样即拒绝构造（`test_instance_report_may_not_leak_holdout`）。
- `DivergenceVerdict`：PDR-001 §6 的测量分类表（CLOSED/SILENCE/AMBIGUITY/UNSOLVED_AT_TIER/INFEASIBLE/INSUFFICIENT），注释直言「**这张表就是范式本身**」。
- `Divergence.covered_by_dont_care` 区分「被许可的自由」与「缺陷」；`DifferentialReport._passing_is_subset` 强制通过集是实例集的子集。

### 2.6 governance.py：治理契约（自带失败检测）

- `HealthMetrics.downgrades(t)`：可执行化 §13 的五个撤退条件（逃逸缺陷率、judge 校准、漂移风暴、成本超支、oracle 冲突）。
- `next_stage()`/`may_advance_to()`：降级永远是**阶段回退**而非放宽判据；进阶不可跳级且带阈值前置（M1 需 witness 覆盖≥0.7，M2 需 ≥0.85 + 零逃逸 + 校准，M3 需逃逸=0 + 闭合度≥0.9）。
- `RuleChangeProposal._no_self_activation`：规则变更的唯一合法通道，deep agent 提案 → 人类批准 → **下一 session 生效**；`effective_session_id` 不得等于 `observed_session_id`（判据在测量中途变动会使测量不可比）。

### 2.7 wave.py：波次事务契约

- `UncertaintySignal.score()`：有界 [0,1] 的确定不确定度分，驱动自适应 fan-out（解决 G5 token 成本）。
- `FanoutPlan.decide()`：闭集决策函数——**R3 永不 fan-out**（`_r3_never_fans_out`），审计样本强制 N≥3，score<0.25→N=1、<0.55→N=3、<0.8→N=5、否则 N=7。
- `WaveManifest`：接口冻结窗 + spec-delta 割集 + 准入事务边界。**B 标定流水线永不 COMMIT**（`_fanout_covers_units`，`test_calibration_pipeline_can_never_commit`）。
- `EvidenceReceipt`（重定义的 PR）：**准入事务 + 证据收据**。`_receipt_completeness`：admitted 必须有选中实例、必须引用硬门禁报告 digest、**必须 drift_clean**（宪法 §10）、R2/R3 必须有人类批准记录；被丢弃实例必须留下测量结论（宪法 §2）。

---

## 3. gates/ 模块详解

### 3.1 algebra.py：`Admit = H ∧ S`

`admit(hard, soft)` 是全部决策：`hard.passed` 为 False → 拒绝；soft 是 VETO → 拒绝；否则通过。两条被穷举证明的性质：

- **No rescue（不可救场）**：对任意软判词 S，H 未全过则永不通过——硬门禁之外没有任何东西能创造准入权。
- **Monotonicity of the veto（否决单调）**：VETO 恒拒绝，去掉否决只可能增加通过。软门禁只能做减法。

`decide()` 在代数之外叠加一个**治理前置条件**：R2/R3 需要记录在案的人类批准，且**人类批准不能救活失败的单元**（`test_human_approval_cannot_rescue_a_failing_unit`）。实现上刻意「在代数之后应用」，把 `hard_passed=False; admitted=False`，使契约自身的代数校验器仍然成立——**代数是纯合取、保持可证**。

`REQUIRED_GATES` 无分级别豁免：H5 在 R0 从门内报 `not applicable`，把「跳过决策」作为证据记录而不是作为缺省。

### 3.2 hard.py：H1–H8 逐门判据

| 门 | 判据 | 关键 finding 代码 |
|---|---|---|
| H1 构建/类型/静态 | `build.compiled` + `static.type_errors/lint_errors` | `H1.BUILD_FAILED` 等 |
| H2 单元+属性 | 空套件、失败、**反空洞断言率**（`assertion_rate < 1.0` 即 `H2.VACUOUS_TESTS`——「全绿但不断言的套件是最贵的绿」）、属性反例 | `H2.NO_TESTS/H2.VACUOUS_TESTS/H2.PROPERTY_FALSIFIED` |
| H3 holdout | 场景没跑 / 失败 / **inconclusive 永不默认通过**（三值构造） | `H3.SCENARIOS_NOT_RUN/H3.SCENARIO_FAILED/H3.INCONCLUSIVE` |
| H4 契约面 | `classify(old, new)` 结构变更；breaking 但无 spec-delta → `H4.UNDECLARED_BREAKING_CHANGE`；delta 低报严重度 → `H4.SEVERITY_UNDERSTATED`。**H4 抓未声明/低报的破坏，而非禁止破坏**——「正确声明过的变更也过不了的门会被团队绕过去」 | 上述 + `H4.SYMBOL_REMOVED` 等 |
| H5 差分/黄金 | 仅 `CLOSED` 放行；`SILENCE/AMBIGUITY/UNSOLVED_AT_TIER/INFEASIBLE/INSUFFICIENT` 全阻断；R3 必须带黄金 store + comparisons，黄金失配带环境漂移 | `H5.<VERDICT>/H5.GOLDEN_MISMATCH` |
| H6 不变量/护栏 | 有 invariant 的条款必须被评估过（`H6.INVARIANT_UNCHECKED`）、违规、运行时护栏 trip | `H6.*` |
| H7 漂移 | `TraceabilityEngine` 三段漏斗；只 block `DANGLING_ANCHOR/STALE_ANCHOR/STRUCTURAL_DRIFT`；unverifiable 条款与孤儿条款**先警告后阻断**（否则门会被关掉）；过期豁免 `H7.EXEMPTION_EXPIRED` | `H7.*` |
| H8 预算 | 有 limit 未测量 → `H8.UNMEASURED`；超限 → `H8.BUDGET_EXCEEDED` | 同上 |

`witness_kinds_satisfied(ctx)` 返回上下文**实际提供**的机械见证类型，配合测试 `test_a_declared_witness_with_no_gate_behind_it_is_detectable` 检查「声明的见证背后真的有门」——声明了但没有门，等于没有见证。

### 3.3 soft.py：单调否决器

- **judge 档位 ≥ builder 档位**：`screen()` 拒收弱 judge 样本；同时 `SoftGateResult` 契约层再强制一次（双层防御，`test_the_tier_rule_is_also_enforced_by_the_contract_itself`）。
- **否决必须引用**：`JudgeSample` 构造时强制。
- **禁止自评**：`screen(forbid_self_review)` 拒收 `judge_identity == builder_identity`。
- **位置交换**：`position_swap_agreement is False` 时丢弃否决（两序不一致 = 噪声而非裁决）。
- **弃权合法**：强制二选一会制造不存在的信号；弃权从分母剔除，且**全弃权 = ABSTAIN 而非 NO_VETO**。
- **一致性被测量而非假定**：Cohen's kappa 取**最差配对**而非平均（`test_kappa_uses_the_worst_pair_not_the_average`），对「恒定 rater」返回 0 而非 1（`test_kappa_of_a_constant_rater_is_zero_not_one`）。kappa 低于阈值（默认 0.6）或轮次 <2 → judge **unfit** → 软门禁**禁用**（`disabled_reason`），即 §13 降级 2。
- 聚合模式是**闭集** `{any_veto, majority_veto, unanimous_veto}`；默认 `any_veto` 是单样本配置下唯一安全的模式。被拒样本**丢弃**而非转成否决——「畸形否决是坏 judge 的证据，不是缺陷的证据」。
- `ScreenedSample` 刻意把身份元数据放在**载荷之外**（`JudgeSample` 不带 author 字段——身份字段只是 prompt 里又一个可以撒谎的东西）。

---

## 4. oracle/ 模块详解

### 4.1 dontcare.py：选择器语言 + 闭集 normalizer

- 选择器语法刻意极小（`channel[.path]`，支持 `*`/`[i]`/`[*]`），纯结构匹配不 eval。
- **Normalizer 是闭集**：`identity/sort_list/round:3|6|9/mask_uuid/mask_timestamp/mask_address/strip_whitespace/exception_type_only/drop`。开放集合会让 builder 自造 normalizer 定义掉真实差异——这正是信息不对称要防的 reward hacking。未知 normalizer 在**编译期**报错而非第一次比较时报错（避免一个波次跑到一半崩掉）。
- `DontCareMask.apply` 返回 `(normalised, touched)`；`_walk_apply` 用 `seen` 追踪**命中但未改变值**的区域——「匹配到但碰巧没改值」仍然管辖比较，只报变化会低估裁决依赖的自由度（缺陷 #4 的修复点）。
- 默认 normalizer：`output_freedom`→`sort_list`，其余→`drop`（`ignorable_output` 全擦除为 `<don't-care>`）。默认 `identity` 会把已声明自由静默变 no-op，「两害取其轻」。
- `covering_region()` 回答「是哪个单区域让 a/b 无法区分」，使被许可的差分可被归因。

### 4.2 differ.py：差分引擎（§6 的测量仪器）

- 流水线：`normalise(don't-care) → fingerprint → cluster → pairwise diff(仅 representative)`。**先聚类**把 N 实例的 O(N²) 比较降为 K 个簇代表的 O(K²)，K 通常 1–3（研究 4.5 LDB 的推荐）。
- 三档等价阶梯：IO（return+exception）/ BEHAVIOURAL（+stdout/stderr/exit_code/side_effect）/ SEMANTIC（**只声明**为升级钩子，从不自称证明等价——差分只能证不等价）。IO 级忽略 stdout 但 BEHAVIOURAL 不忽略（`test_io_level_ignores_stdout_but_behavioural_does_not`）。
- `verdict()` **逐字实现** §6 决策表：0 实例→INSUFFICIENT；有失败且实例<3→INSUFFICIENT（先补采样再判，`min_instances_for_verdict=3`）；全过无缺陷差分→CLOSED；全过有未决差分→SILENCE；部分过→AMBIGUITY；全败且升级后→INFEASIBLE，否则 UNSOLVED_AT_TIER。
- `delta_diversity`：NEZHA 式探针多样性（产生 >1 种归一化观测的探针占比），是探针预算的调度信号——多样性 0 的探针集采样再多也测不出 spec 沉默。
- `cluster()` 用 `sorted(ids)[0]` 选代表、`run()` 用 `sorted(reps)` 组合——保证确定性（缺陷 #8 的修复）。

### 4.3 compat.py：破坏性变更分类（H4 的机械半边）

- 两层验证：**结构层**（此处实现，oasdiff 变更目录风格，覆盖类内全覆盖无假阴性）+ **语义层**（声明而非伪造，`SemanticRefinementCheck` 钩子；无检查器注册时语义兼容报 `UNKNOWN`——「无机械见证只能否决不能放行」）。`SemanticRefinementCheck` 只能把裁决**加强**为 INCOMPATIBLE，**绝不能**把结构 BREAKING 降级为兼容。
- 每条规则有稳定代码（`H4.*`）供证据收据引用并回溯到规范条款。
- 参数比较矩阵：删除必选参数/失去默认/默认值改变/类型改变/收窄参数种类/必选参数新增/**位置参数重排**均 BREAKING；`**kwargs` 吸收的删除算 PATCH；可选参数新增/加默认算 ADDITIVE。`H4.PARAM_DEFAULT_CHANGED` 专门抓「签名不变但默认值悄悄变」——这是人类从不注意的漂移类（ConflictLens 的 Assignment Override）。
- **JSON Schema 根节点**与嵌套属性同等待遇（`_compare_schema_node` 拆出来供根节点使用）——否则顶层类型从 string→integer 会静默漏报（缺陷 #5 的修复，测试 `test_changing_a_schema_type_is_breaking`）。
- `severity = max_of(...)`：严重度取**最坏变更**而非最后一个。

### 4.4 surface.py：契约面提取（L2 的机械见证）

- **只 `ast`，不 import 不执行**——「门禁绝不能为了裁决 builder 代码而去运行 builder 代码」。输出是平铺、排序、JSON 可序列化的结构，可 digest、可冻结为波次接口地平线、可被 compat diff。
- 尊重 `__all__`（显式 `__all__` 即声明面）；私名（单下划线）不算面；`SyntaxError`/不可读文件显式记 `error` 而非空面——把「读不了」报告为错误，否则会 diff 成「全部删除」或「无变化」（`test_missing_file_is_reported_not_silently_empty`、`test_unparseable_source_is_an_explicit_failure_not_an_empty_surface`）。
- 支持现代语法（`/` 纯位置参数、`*`、`**kw`、async def、类注解属性），`test_surface_extraction_survives_modern_syntax` 参数化覆盖。

### 4.5 traceability.py：spec↔code 漂移检测（H7）

- 三段漏斗最便宜优先：L0 锚点解析 → L1 digest 比较 → L2 结构分析 → L3 语义（默认关闭的钩子，模型意见只能否决不能放行）。
- **两类失败模式刻意区分**：孤儿条款（有 spec 无代码 = 活没干）与过期锚点（代码变了 spec 没更 = spec 没跟）——修法不同。
- 漂移基线**传参而非存于 Anchor**：锚点自带「期望 digest」会让改代码的人同一次提交里把期望也改了，正是门要抓的漂移（`test_the_baseline_is_not_owned_by_the_anchor`）。基线由 spec 仓拥有，仅在条款修订时更新。
- 豁免必须有 owner + 过期时间，过期即失效（`test_an_exemption_needs_an_owner_and_an_expiry`）；`@spec: <id>` 源码标记可反向发现（`test_source_markers_are_discoverable`、`anchors_from_source`）——漂移可以双向发生。

### 4.6 golden.py：R3 黄金输出管理

三条规则都因「违反它们烧过真实项目」而存在：

1. **CI 永不写黄金**：`COMPARE` 模式物理上无法变更；再生是独立、需人类授权的模式（`REGENERATE` 无授权令牌直接构造失败——缺陷 #9 的修复）。
2. **基线与快照物理分离**：期望值来自冻结 store，产出值来自运行，不存在「运行结果变成它自己被比较的基线」的代码路径。
3. **黄金是回归守卫而非正确性证明**：`GoldenSuite.validate()` 拒绝只有黄金的 R3 套件，必须另绑独立正确性 oracle（变形关系/参考实现/往返性质）。

- 黄金**只追加**（append-only，`supersede` 保留历史并重定向，多版本共存优于强制迁移）；缺失黄金 = 失败而非通过（否则删黄金成为最便宜的过关方式）。
- `R3Info` 仿 Debian `.buildinfo` 的可复现清单（python/platform/timezone/locale/SOURCE_DATE_EPOCH/依赖 digest），区分「代码变了」与「世界变了」——环境漂移被报告但**永不自动通过**（`is_environment_suspect`：报告给人裁，绝不自动通过也绝不自动通过）。

### 4.7 strength.py：oracle 强度审计

- 评级梯（执行级，与 PDR-001 对齐）：**Bronze** 跑通且断言了什么 → **Silver** + 双判据（证明修复且没弄坏别的，即 SWE-bench 的 FAIL_TO_PASS+PASS_TO_PASS）→ **Gold** + 绑定规范条款且覆盖其声明案例 → **Diamond** + 通过变异探针（每个探针都被杀死）。
- **Diamond 以下不得作为 R2/R3 准入的唯一证据**（「Nothing below Diamond may be the sole evidence for an R2/R3 admission」）。
- `run_mutation_probes`：探针注入 oracle 声称能抓的缺陷，若没有场景失败则探针存活、oracle 的声称是假的——这是唯一不需要自身被信任的机械防空洞工具（`test_a_surviving_mutation_probe_caps_the_grade_at_gold`、`test_no_mutation_probes_means_diamond_is_unattainable`）。
- 空 bundle = BRONZE 而非错误；阈值可配置但默认严格（`min_clause_coverage=1.0, min_mutation_score=1.0`）。

---

## 5. bus/ 模块详解：信息不对称总线

### 5.1 policy.py：能力矩阵（白名单）

`DEFAULT_MATRIX: (Role, ArtifactClass) -> frozenset{READ,WRITE}`，**缺席即拒绝**——新增制品对每个角色不可见，直到有人显式授权。关键非显然单元（注释原文）：

- **BUILDER 对 ORACLE_HOLDOUT 双向无访问**——全表最重要的一格。
- BUILDER 连 `JUDGE_VERDICT` 也不能读——「知道你怎么被打分，就足以优化分数而非目标」。
- VERIFIER 不能写 `SPEC_L2`——能改契约的 verifier 可以靠改写「正确」的定义让任何实现正确。
- JUDGE 只读匿名 `INSTANCE_REPORT` 不读 `INSTANCE`——看不到作者线索。
- ARCHITECT 写 L2 但**不能写 holdout**——定义契约的人不得同时定义秘密考题。
- `TEAM_MEMORY` 仅 SPEC_STEWARD/LEADER 可写——临时角色不写记忆（§7.3）。

`check_separation` 处理矩阵表达不了的**身份级**规则：自评（judge 评审自己写的实例）、**oracle 作者不得是其主题**（`sender_identity == subject_identity` 拒绝，缺陷 #3 的修复）、holdout 永不路由给 builder。

### 5.2 bus.py：订阅制投递 + 全量审计

- **订阅时拒绝**（`subscribe` 对每个请求类做 `can_read`，无权限即 `DeliveryError`）——把运行时泄漏变成**接线错误**，第一次跑测试就发现而非上线后（`test_builder_cannot_even_subscribe_to_the_holdout` 注释明说这一点）。
- `_decode` 三重校验：未知契约类型拒绝（闭注册表）、**契约 major 版本不匹配拒绝**、**制品类被贴标签（relabelling）拒绝**。
- `_authorise_send` + 投递时逐订阅者 `can_read` + `check_separation`：**每个被投递者、每个被拒的投递都有审计记录**（`DeliveryRecord` 为每个尝试留一行，包括拒绝——「被拒绝是最值得记录的日志事件」）。
- `strict` 模式下对显式收件人的拒绝**大声失败**（raise），绝不静默吞掉——「看起来成功的被拒投递就是不对称泄漏的样子」。
- `who_saw`/`refusals`/`view_of` 提供取证；`view_of(builder) ∩ view_of(verifier) ⊆ public` 是 §7 的实际谓词，测试断言的是**真实投递结果**而非意图。

### 5.3 envelope.py：封口信封

- 路由决策只读 header **不碰 payload**——「要看内容才能路由的决策，就是能被内容骗的决策」。
- `Envelope._seal`：`payload_digest` 构造时计算、投递时 `verify()` 重算——中间人改写 payload 收件人必察觉（`test_tampered_payload_is_rejected`）。
- `seal()` 的制品类**从契约类读取**而非调用者提供——发件人无法把 holdout 贴成 public（`test_relabelling_an_artifact_class_is_refused`）。

---

## 6. 测试覆盖与方法论

实测：`PYTHONPATH=src python -m pytest` → **466 passed in 1.84s**（`.pytest_cache` 中 nodeids 亦为 466 项）。

### 6.1 总体方法论

1. **一次只破坏一件事**（`tests/gates/test_hard_gates.py` 头注释）：从「全部证据良好」的上下文出发，恰好弄坏一项，断言**恰好负责它的门**失败。「在别人缺陷上点火的门与从不点火的门一样无用——两者都毁掉红灯的诊断价值」。`test_the_reference_context_passes_every_gate` 是阴性测试的地基——它挂了，下面所有阴性测试都无意义。
2. **穷举证明而非举例**（`test_algebra.py`）：no-rescue 性质对**全部**失败门子集 × 全部软判词穷举（`itertools.combinations(HARD, n_failures)` 参数化 0..8），覆盖整个可达状态空间。
3. **攻击面测试而非表格复述**（`tests/bus/test_asymmetry.py` 头注释）：「政策表说 X」的测试只是复述表格；这些测试是「攻击不奏效」测试，每条都是必须失败的违规尝试。
4. **构造器证明结构性不变量**（`test_structural_invariants.py` 头注释）：每个测试对应一个真实项目会用 code-review 清单来执行的规则；**清单会腐化，构造器不会**。
5. **fixture 永不触网/触文件/触模型**（`conftest.py` 头注释）：全部 fixture 是「一个想象单元 UNIT-CART 的完整合法制品集」，测试一次变异一项，观察恰好一个失败。

### 6.2 覆盖分布（按 nodeids 统计）

| 测试文件 | 数量 | 重点 |
|---|---|---|
| `contracts/test_roundtrip.py` | ~180 | 每个契约都声明 SemVer、声明 ArtifactClass、能出 JSON Schema、**拒绝未知字段**（`extra="forbid"`）、round-trip 序列化、digest 稳定且顺序无关、注册表非空 |
| `contracts/test_structural_invariants.py` | ~30 | SoftVerdict 无 PASS、无引用的否决、弱 judge、失败门必须带 finding、缺门禁 = 未通过、**准入记录不可伪造**、拒绝必须带理由、场景必须断言且绑定条款、BREAKING 必须升 major、R3 必须有黄金、R0 无消费者、B 流水线不 COMMIT、实例报告不得泄漏 holdout |
| `gates/test_algebra.py` | 23 | no-rescue（穷举）、否决单调（穷举）、缺门/error 非通过、软门禁无 PASS、弃权不阻断、人类批准只前置不救场、**裁决记录不可伪造**、确定性 |
| `gates/test_hard_gates.py` | ~45 | 每个门：好的上下文 → 弄坏一项 → 该门恰好失败；H4 接受正确声明/拒绝未声明/拒绝低报；H5 阻断全部非 CLOSED 裁决、R0 不适用、R3 需要黄金、环境漂移报告 |
| `gates/test_soft.py` | ~25 | kappa 语义（恒定 rater=0、最差配对、噪声≈0）、聚合模式、位置交换保否决/丢否决、弃权率报告、unfit judge 禁用而非信任、档位契约层强制 |
| `oracle/test_compat.py` | ~40 | 增删函数/方法/参数/属性/枚举/基类/默认值/类型注解的严重度；**根 schema 类型变更 BREAKING**；语义检查器不能挽救结构破坏；面提取稳定性与现代语法 |
| `oracle/test_differ.py` | ~25 | §6 决策表逐行、聚类收缩等价行为且尊重 don't-care、代表确定性、delta diversity、IO 忽略 stdout、缺探针不是静默通过、实例<3 且失败 = INSUFFICIENT |
| `oracle/test_dontcare.py` | ~20 | 选择器匹配嵌套路径/通配、normalizer 闭集、drop 占位符、掩码不掩盖真实差异、**covering region 归因**、undefined vs unspecified 不可互换 |
| `oracle/test_golden.py` | ~20 | 仅追加、supersede 保留历史、compare 不能写、**再生需人类授权**、缺黄金失败、独立 oracle 强制、R3Info digest 稳定 |
| `oracle/test_strength.py` | ~20 | 四阶梯单调、存活探针封顶 GOLD、无探针到不了 DIAMOND、回归套件封顶 BRONZE、clause 覆盖测量、审计器仍测断言率 |
| `oracle/test_traceability.py` | ~25 | 锚点到删除文件/改名符号阻断、基线不归锚点所有、豁免需 owner+过期、过期豁免失效、漂移双向、语义漂移仅 advisory、孤儿警告不阻断 |
| `bus/test_asymmetry.py` | ~25 | 订阅即拒绝、生成角色读不到 holdout、伪造 holdout 发不出、**builder view ∩ verifier view ⊆ public**、拒绝被记录而非静默、临时角色不写记忆、judge 不得评自己、oracle 作者不得是主题 |
| `bus/test_handoff.py` | ~9 | 完整波次交接 `architect→builder→verifier→judge→leader` 端到端、major 不匹配拒绝、minor 差异接受、载荷精确存活、贴标签拒绝、send 无收件人大声失败、**篡改拒绝** |

---

## 7. 写测试暴露出的 9 个实现缺陷（PR 描述）

内核的路线是「先写会失败的测试，再让实现通过」。下列 9 个缺陷均通过某个阴性测试暴露，修复后在对应模块里留下机制性防御：

| # | 缺陷 | 暴露测试 | 修复（当前代码中的机制） |
|---|---|---|---|
| 1 | **H4 无法通过「正确声明过的破坏性变更」**：只堵未声明的 breaking，导致团队会绕门 | `tests/gates/test_hard_gates.py::test_h4_accepts_a_correctly_declared_breaking_change`（及 `test_h4_fails_on_an_undeclared_breaking_change`、`test_h4_fails_when_the_delta_understates_the_change`） | `hard.py` 的 `H4ContractSurface`：breaking 且无 delta → `H4.UNDECLARED_BREAKING_CHANGE`；delta 低报严重度 → `H4.SEVERITY_UNDERSTATED`；「正确声明过的变更可过、但被声明为 warning 报告」 |
| 2 | **Envelope 双重编码/可篡改**：payload 在构造与投递间可能被改写而收件人不知 | `tests/bus/test_handoff.py::test_tampered_payload_is_rejected` | `envelope.py` 的 `Envelope._seal`：`payload_digest` 构造时计算并在投递时 `verify()` 重算，不一致抛 `ValueError` |
| 3 | **Oracle 自评 / 作者即主题**：oracle 作者可以给自己的 oracle 打分 | `tests/bus/test_asymmetry.py::test_an_oracle_author_may_not_grade_itself`、`test_architect_cannot_author_the_holdout` | `policy.py::check_separation`：对 `ORACLE_HOLDOUT/ORACLE_PUBLIC`，`sender_identity == subject_identity` 即拒绝「作者不得是其主题」 |
| 4 | **DontCareMask 命中记录问题**：只记录「值变了」的区域，漏掉「匹配到但值恰好没变」的自由 | `tests/oracle/test_dontcare.py::test_covering_region_names_the_region_that_forgave_the_difference`、`test_covering_region_is_none_for_a_real_divergence` | `dontcare.py::_walk_apply` 的 `seen` 出参 + `DontCareMask.apply` 返回 `touched` 集合；`covering_region` 可归因「哪个区域豁免了这次差异」 |
| 5 | **根级 JSON Schema 类型变更不可见**：只比较嵌套属性，顶层 type 变了也报干净 | `tests/oracle/test_compat.py::test_changing_a_schema_type_is_breaking` | `compat.py` 抽出 `_compare_schema_node` 供根节点使用；`classify_json_schema` 先对根节点比较（`H4.SCHEMA_TYPE_CHANGED`），再递归属性 |
| 6 | **H7 漂移检测假阴性**：锚点解析不足，删除文件/改名符号可能漏报 | `tests/oracle/test_traceability.py::test_an_anchor_to_a_deleted_file_blocks`、`test_an_anchor_to_a_renamed_symbol_blocks` | `traceability.py` 的三段漏斗（L0 解析存在性 → L1 digest → L2 结构），`AnchorResolver.exists/content_digest/structural_digest` 分离文件级与符号级锚点，`DANGLING_ANCHOR`/`STALE_ANCHOR` 阻断 |
| 7 | **软门禁 judge 档位绕过**：档位规则只在 engine 层，契约可被直接构造绕过 | `tests/contracts/test_structural_invariants.py::test_judge_weaker_than_builder_is_refused`、`tests/gates/test_soft.py::test_the_tier_rule_is_also_enforced_by_the_contract_itself` | `contracts/gate.py::SoftGateResult._judge_not_weaker_than_builder`：`judge_model_tier < builder_model_tier` 直接构造失败——**契约层**兜底，engine 层只是第一道 |
| 8 | **差分引擎簇代表选择偏置**：未排序导致代表不稳定、结果不确定 | `tests/oracle/test_differ.py::test_representatives_are_deterministic` | `differ.py::cluster` 用 `sorted(ids)[0]` 选代表、`run` 用 `sorted(reps)` 做组合——相同输入恒得相同报告（引擎头注释：`Deterministic. Same inputs always yield the same report.`） |
| 9 | **黄金再生无授权**：`REGENERATE` 模式可被无凭据调用，等于 CI 可变黄金 | `tests/oracle/test_golden.py::test_regenerate_mode_requires_human_authorisation`（及 `test_authorised_regeneration_is_allowed`、`test_compare_mode_cannot_write`） | `golden.py::GoldenStore.__init__`：`REGENERATE` 模式缺授权令牌即 `GoldenStoreWriteError`；`put`/`supersede` 在 `COMPARE` 模式物理无法写 |

**模式总结**：9 个缺陷里 6 个是「机制缺口」（第 1、2、4、5、6、8 号：实现没覆盖某个该堵的路径），3 个是「信任边界缺失」（第 3、7、9 号：策略/档位/授权只在流程层而未进机制层）。修复的共同手法是把规则**下沉到构造器/契约校验器/总线**，让违规「说不出口」或「构造不出来」，而非靠纪律。

---

## 8. 关键设计权衡与可迁移要点

1. **用类型表达安全性质**：`SoftVerdict` 无 PASS、`AdmissionDecision` 自证代数、`Envelope` 自算 digest、`SpecDelta` 自检版本义务——「不可表达」是最强的约束。
2. **确定性一切**：门禁是纯函数、差分/表面提取/漂移/审计全部确定性离线、fixture 不触网——这是「无运行时可单测」与「结果可进证据收据」的前提。
3. **信息不对称 = 路由机制**：能力矩阵白名单 + 订阅时拒绝 + 投递时复核 + 全量审计 + 取证视图，把「看不见 holdout」从礼仪变成物理约束。
4. **软门禁只做减法**：可被禁用而不削弱任何东西（disabled_reason），因为软门禁本来就只能否决；judge 一致性不足时的正确动作是**降自治**而非放宽判据。
5. **门禁不堵正确路径**：H4 接受正确声明的破坏、H5 在 R0 报 n/a、豁免需 owner+过期——防止「绕门」成为团队的理性选择。
6. **防空洞是一等工程**：H2 断言率、oracle strength 变异探针、judge kappa——三个独立层面都在测量「声称的验证能力是否真空洞」。

---

## 9. 附录：验证记录

- `PYTHONPATH=src python -m pytest` → `466 passed in 1.84s`（本环境全新安装 pydantic/PyYAML/pytest/hypothesis/jsonschema 后实测）。
- 未修改 `kernel/` 下任何文件；唯一写入为本报告 `/workspace/plans_reports/PR3.md`。
