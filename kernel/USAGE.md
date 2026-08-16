# swarmkernel 使用总说明——从安装到人类下命令

> 适用版本：PR#3 当前 HEAD（commit `4b52a35`，测试 531 passed）。
> 本文是 kernel 包的端到端使用手册：包内开发内容、本地集成 agent 的落地步骤、全面测试方法，以及人类操作者的日常用法。

---

## 一、这个包是什么

`kernel/` 是 Spec-as-Source Agent Swarm 的**参考内核**：契约、门禁、oracle 引擎、信息不对称总线的纯函数实现。它**不含任何 LLM 调用、不调度进程、不碰文件系统之外的世界**——所有"动手"的部分（构建、跑测试、派发模型调用）由你的 harness 层实现，内核只负责**裁决**。

设计基石（不可绕过的不变量）：

- **Admit = H ∧ S**：只有 8 个硬门全绿且软门无 veto 才准入，软门永远只能否决（`SoftVerdict` 无 PASS 成员）。
- **Silence is not consent**：证据缺失 = ERROR = 阻断，绝不放行。
- **三态退出**：ADMITTED(0) / REJECTED(1) / INCONCLUSIVE(2)，CI 对 2 是重试不是修复。
- **R0-R3 分级**：一次性实例(R0) → 内部消费(R1) → 外部契约(R2，可 fan-out，H4 兜底) → 冻结制品(R3，禁 fan-out，golden 把守)。

## 二、开发内容总览

| 模块 | 职责 | 关键点 |
|---|---|---|
| `contracts` | 30+ 个冻结契约 | 构造期强制不变量（judge≥builder、veto 必须带 citation、代数防伪造）；spec 双层表示（人读 Markdown+frontmatter / 机判 canonical JSON+sha256）；六态波次状态机+转移表 |
| `oracle` | 确定性测量引擎 | 差分引擎（指纹聚类 O(K²)、声明式浮点容差、D8 完整记录 don't-care 依赖）；golden 库（COMPARE/REGENERATE 模式锁，再生需人工令牌）；契约面提取与破坏性变更分类（根级 Schema 也检测）；漂移追踪 |
| `gates` | H1-H8 硬门+准入代数 | 每门声明 `relative_cost`；执行策略 M0/M1 全跑全记录、M2+ 按成本升序 fail-fast；`decide()` 直读 JudgeProtocol 的 D6 声明；R3 的 golden 检查独立前置 |
| `bus` | 信息不对称总线 | 信封 sha256 封口防篡改；holdout 永不路由给 builder（结构性禁令）；全程投递审计 |
| `cli` | CI 适配器 | 三态退出码；伪造记录 exit 1（要人介入），不可读输入 exit 2（重跑） |

测试：**531 条全绿**（Python 3.12），含 8 条 meta 变异测试（每门注入一个缺陷证明它真的会红）。

## 三、本地集成落地（6 步）

### 第 0 步：安装

```bash
cd kernel
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"
python -m pytest tests        # 应见 531 passed
```

### 第 1 步：写 Spec（人类的主要工作面）

用 `SpecDocument` 建模后渲染为 Markdown 人读、JSON 机判：

```python
from swarmkernel.contracts.spec import SpecDocument, Clause, DontCareRegion
from swarmkernel.contracts.spec_md import render_spec_markdown, verify_spec_markdown

spec = SpecDocument(spec_id="SPEC-CART", version="1.2.0", domain="checkout",
                    clauses=[...], dont_care=[...])
text = render_spec_markdown(spec)          # 存入 spec/ 目录，供人审阅
assert verify_spec_markdown(text, spec)    # 人改了 Markdown 或模型变了 → False
```

关键约束：

- 条款 ID 必须形如 `L2-CART.TOTAL-001`（层级前缀+域+序号）；
- 想参与准入的条款必须有机械 witness 绑定（`WitnessBinding`，指向 H1-H8 的具体检查）；
- 自由度必须显式注册为 `DontCareRegion`（带 selector 和 normalizer），未注册的差异就是缺陷。

### 第 2 步：登记 R 级

```python
from swarmkernel.contracts.spec import RLevelRegistry, RegenerationUnit, RLevel

registry = RLevelRegistry(units=[
    RegenerationUnit(id="UNIT-CART", title="cart", r_level=RLevel.R1,
                     paths=["cart/"], surface_paths=["cart/api.py"],
                     clause_ids=["L2-CART.TOTAL-001"]),
    # R2 必须列 external_consumers；R3 必须列 frozen_golden_ids（构造器强制）
])
```

### 第 3 步：准备 Oracle

- **PublicOracle**（builder 可见）：属性测试、蜕变关系、冒烟入口、冻结的接口面 digest。
- **HoldoutOracle**（仅 architect/verifier 持有）：场景、golden、rubric、JudgeProtocol、变异探针。物理上放仓内 `oracle/holdout/` 目录，靠总线路由禁令隔离；跨团队后拆独立仓（D25 渐进策略）。
- **GoldenStore**：CI 用 `GoldenStore(records)`（COMPARE 模式，写操作直接抛错）；只有人类显式授权才能再生：

```python
from swarmkernel.oracle.golden import GoldenStore, GoldenMode
store = GoldenStore(records, mode=GoldenMode.REGENERATE, authorisation="human-token-xxx")
```

### 第 4 步：实现 Harness 适配器（内核之外你唯一要写的代码）

四个适配函数，产出内核要的证据：

| 适配器 | 产出（填入 GateContext） |
|---|---|
| 构建/静态 | `build={"compiled": bool, "error": str}`、`static={"type_errors": n, "lint_errors": n}` |
| 测试运行器 | `unit_tests={"total","failed","errors","assertion_rate"}`、`property_tests={"falsified": []}`、`invariant_results={clause_id: bool}` |
| 探针执行器 | 对每个实例跑探针 → `InstanceReport`（各通道 Observation：return/exception/stdout/…） |
| Judge 调度 | 按 rubric 派发评判 → `ScreenedSample` 列表（判词三值，veto 必带 citation） |

R3 单元额外把 golden 比对结果 `store.compare(gid, actual, env)` 填入 `golden_comparisons`。

### 第 5 步：跑一个完整波次

```python
from swarmkernel.contracts.wave import FanoutPlan, UncertaintySignal, WaveManifest, wave_transition, WaveStatus
from swarmkernel.oracle.differ import DifferentialEngine, DifferentialInput
from swarmkernel.gates.hard import default_registry
from swarmkernel.gates.algebra import decide

# 1) 定 N：多数派公式 U=0.4·rework+0.3·novelty+0.3·R级 → N∈{1,3,6}；R3 恒为 1
plan = FanoutPlan.decide("UNIT-CART", UncertaintySignal(
    historical_rework_rate=0.3, new_clause_count=2, r_level=RLevel.R1))

# 2) 波次声明（frozen_surface_digest = 冻结窗口的接口 horizon）
manifest = WaveManifest(wave_id="W-1", spec_id="SPEC-CART", spec_version="1.2.0",
                        frozen_surface_digest="sha256:...", unit_ids=["UNIT-CART"],
                        fanout=[plan])
# 状态推进只能走：PLANNED→FROZEN→BUILDING→MEASURING→ADMITTING→COMMITTED，跳步即抛错
wave_transition(WaveStatus.FROZEN, WaveStatus.BUILDING)

# 3) 派发 N 个构建 → 收集 InstanceReport → 差分
diff_report = DifferentialEngine(dont_care=spec.dont_care).run(
    DifferentialInput(unit_id="UNIT-CART", delta_id="D-1", spec_version="1.2.0",
                      reports=reports, passing_instance_ids=..., dont_care=spec.dont_care),
    "DR-1")

# 4) 组装证据上下文，跑门（M0/M1 全跑；M2+ 可 run_for_stage(ctx, stage) fail-fast）
ctx = GateContext(unit_id="UNIT-CART", instance_id="inst-a", r_level=RLevel.R1,
                  spec=spec, spec_delta=delta, fanout_plan=plan,
                  build=..., static=..., unit_tests=..., property_tests=...,
                  holdout_oracle=holdout, holdout_results={...},
                  differential_report=diff_report, invariant_results=..., ...)
results = default_registry().run_all(ctx)

# 5) 软门（可选但推荐）
from swarmkernel.gates.soft import SoftGateEngine
soft, fitness = SoftGateEngine().evaluate(samples, builder_tier=2,
        builder_identity="builder-a", judge_tier=3)  # 默认 any_veto 聚合

# 6) 裁决（R2/R3 需 human_approved=True 才可能 admit）
decision = decide(unit_id="UNIT-CART", instance_id="inst-a", r_level=RLevel.R1,
                  results=results, soft=soft, judge_protocol=holdout.judge_protocol)
print(decision.admitted, decision.outcome, decision.exit_code, decision.reasons)
```

裁决结果落 `EvidenceReceipt`（准入事务回执），成功即 COMMITTED 波次。

### 第 6 步：CI 集成

```bash
python -c "...decide(...)..." > decision.json
swarmkernel decision.json; echo "exit=$?"
# 0=ADMITTED  1=REJECTED(修代码)或伪造记录(要人查)  2=INCONCLUSIVE(重跑/升级)
```

仓库已含 `.github/workflows/kernel-ci.yml`（3.11/3.12/3.13 矩阵 + meta 步骤）。

（可选）多角色进程间用总线通信：`seal(message_id=..., contract=..., sender_role=Role.ARCHITECT, ...)` 构造信封后 `bus.publish(envelope)`——digest 封口+能力矩阵+holdout 禁令全程生效，`bus.refusals()` 可审计每次拒绝。

## 四、全面测试方法（三层）

**第 1 层：内核自测**

```bash
python -m pytest tests              # 531 条，全部行为契约
python -m pytest tests -m meta      # 8 条反空转证明：每门对它声称能抓的缺陷必须变红
python -m pytest tests -m contract  # 契约 wire 往返
```

**第 2 层：集成冒烟（你的 harness 接好后）**

用一个最小单元走全流程：写 2 条款 spec → R1 登记 → N=3 fan-out → 三个实例（让其中两个行为等价、一个有差异）→ 差分应为 SILENCE 或 AMBIGUITY → 门 H5 红 → decision REJECTED。这条链路通了，说明所有适配器接线正确。

**第 3 层：对抗验收（上线前做一次）**

- **篡改**：手工改 `Envelope.payload` 不改 digest → 总线抛 `DeliveryError`。
- **伪造**：直接构造 `admitted=True` 但 `hard_passed=False` 的决策 → 构造期抛 "algebra violated"；经 CLI 喂入 → exit 1。
- **绕过**：给 R3 单元塞 `fanout_plan.n=3` → 构造器抛错（R3 禁 fan-out）；plan 的 R 级与登记不符 → `H5.FANOUT_LEVEL_MISMATCH` ERROR。
- **CI 写 golden**：COMPARE 模式下 `store.put(...)` → 抛 `GoldenStoreWriteError`。
- **门禁短路**：抽掉任一证据字段 → 对应门 ERROR 而非 PASS。

## 五、人类接下来怎么用这套系统

人类操作者的日常只有四个接触点，其余都是 agent/CI 在跑：

**1. 下命令**——向 leader agent 下达的是**域意图**（"给购物车加多币种支持"），不是代码指令。agent 会：起草 spec delta → 登记 R 级 → 开波次 → 多实例构建 → 门禁 → 给你回裁决。

**2. 批准（R2/R3 单元）**——凡外部契约或冻结制品，`decide(human_approved=False)` 永远不 admit（exit 2 等你）。你批准的动作就是回一句"批准"，harness 记入 `EvidenceReceipt.human_approval_by` 后重跑裁决。

**3. 授权 golden 再生（R3 专属，罕见）**——当且仅当 R3 制材的预期输出**有意**变更时，你发一个显式令牌，harness 用 `GoldenMode.REGENERATE + authorisation=令牌` 重铸基线。没有令牌物理上无法写 golden——这是防止"改期望来迁就坏代码"的最后闸门。

**4. 读结果**——每个波次结束看三样：

- `decision.outcome`：ADMITTED 收工 / REJECTED 看 reasons 里的 finding code（如 `H5.SILENCE` = spec 没写清楚，**去补 spec 而不是改代码**；`H4.UNDECLARED_BREAKING_CHANGE` = 先声明破坏再改版本号）/ INCONCLUSIVE 按 code 处理（`ADMIT.HUMAN_APPROVAL_REQUIRED` 就是你该出场了）；
- `dont_care_touched`：这个 CLOSED 结论依赖了哪些注册自由度，review 时用它反查 spec 是否给多了自由；
- `bus.refusals()`：有没有角色试图越权拿 holdout。

**心法一句话**：REJECTED 几乎总是 spec 的错而不是代码的错——先修 spec、再声明、再让 agent 重新生成；你批准的是**意图与契约**，机器裁决**行为与证据**，两者的边界就是那三态退出码。

---

至此闭环完成：spec 由人写、构建由 agent 干、门禁由内核裁、异常由人拍板。对 openjiuwen 子模块零侵入，上游更新随时可同步。
