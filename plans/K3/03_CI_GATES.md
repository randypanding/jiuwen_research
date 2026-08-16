# CI 门禁与 Oracle 运行规范

## 1. 门禁栈（PDR §8 的落地形态）

`Admit(instance) = H1∧H2∧H3∧H4∧H5∧H6∧H7∧H8 ∧ S(软门禁无 veto)`

| 门 | 实现 | 执行时机 | 失败语义 |
|---|---|---|---|
| H1 构建/静态 | `BuildGate`（命令白名单，参考 `swarmdev/gates/h1_build.py`） | 每实例 | FAIL 短路（fail_fast 可配） |
| H2 单元/属性 | `UnitGate` + `OwnershipGuard` 哈希哨兵 | 每实例 | 测试败或 oracle 文件被改→FAIL |
| H3 场景 holdout | `HoldoutGate`+`ScenarioRunner`（verifier 身份读 vault） | 每实例 | 任一场景败→FAIL |
| H4 契约面 | `ContractGate`（ast surface vs 冻结快照） | 每实例 | 快照项缺失=破坏→FAIL；新增放行 |
| H5 差分/黄金 | `DifferentialGate`（R<R3 集成差分；R3 黄金比对） | RU 级/实例级 | R<R3：转 has_divergence 信号；R3：缺快照/不匹配→FAIL |
| H6 不变量/护栏 | `InvariantGate`（危险模式+import 白名单）+ agent-core `AgentRail`/`RiskLevel`（CRITICAL→AbortError，运行时层） | 每实例 | FAIL |
| H7 spec↔code 漂移 | `DriftGate`+`DriftDetector`（哈希+@REQ 标签；LLM 层夜间） | 每实例+夜间 | hard 事件→FAIL |
| H8 成本预算 | `BudgetGate`（token/时长） | 每实例 | 超支 FAIL；缺记录 INCONCLUSIVE（不放行） |
| S 软门禁 | `JudgeWorkflow`（k 采样多数票，κ≥0.6 才启用） | 候选实例 | veto→否决；abstain→转人工，不误阻 |

**执行纪律**：
- 门禁必须确定性执行——verifier 是 `WorkflowAgent` 固定流水线，不允许自主跳过；
- INCONCLUSIVE 不放行也不永久阻塞：升级人工或补采样（研究 oracle_ci_gate 三值判定）；
- agent 身份对 oracle/测试/CI 定义文件零写权限（CODEOWNERS + vault 分库 + OwnershipGuard 三重）；
- 软门禁永不救场：收据 schema 层拒绝"H 败 S 过而 admitted"（`EvidenceReceipt._admission_algebra`）。

## 2. CI 流水线分层（研究 oracle_ci_gate 六阶段栈的裁剪版）

| 阶段 | 内容 | 载体 |
|---|---|---|
| L0 本地 | spec lint + 契约 schema 校验 | `specctl lint`（pre-commit） |
| L1 PR 级 | H1–H8 全门（沙箱可用则沙箱）+ 收据校验 | `.github/workflows/swarmdev.yml` 为模板；merge queue 阻断 |
| L2 夜间 | LLM 语义漂移层、低频 flaky 重放（n≥ln(α)/ln(1−p̂)）、变异审计（mutmut 变异得分抽检 oracle 信号强度） | cron workflow |
| L3 波次级 | 准入事务（T5）：收据归档、回滚演练 | orchestrator 服务 |
| L4 例行 | judge κ 重校准、holdout 轮换、逃逸缺陷回灌评估集 | T3/T9 |

分支保护：spec 仓与 oracle 仓独立；实现仓 `main` 只接受带完整收据的准入合并；oracle 仓变更必须 architect+human 双签。

## 3. Oracle 运营纪律（防 reward hacking 清单）

1. 场景轮换：epoch 单调（schema 强制），场景 3 个月退役，防"考穿"；
2. 信号强度审计：oracle 测试按 No/Weak/Strong 分级，无有效断言不计入验证强度；周期性变异测试抽检；
3. LLM 只起草断言、永不批准；批准前人工对照 spec 语义（LLM 预言机倾向捕获"实际行为"）；
4. canary 水印场景只用于泄露取证抽查，不作验收；
5. judge 偏置控制：输入匿名化、异家族判官、prompt 冻结版本化、pairwise 交换顺序双跑；
6. 验证器协同演化：模型升级⇒重校准⇒κ 报告入库，这是例行工作不是一次性投入。

## 4. 判据覆盖与不可验证条款

- 每条 L1/L2 条款 ≥1 硬见证或 holdout 场景，否则 `unverifiable`（advisory，不放行）——`SpecDoc.witness_coverage()` 直接产出指标；
- 判据覆盖率未达阈值的域，**禁止**进入"可丢弃"语义（PDR §12 唯一致命误用）。
