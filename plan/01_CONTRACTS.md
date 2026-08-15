# 契约书（Schemas + 通信协议）

> 权威定义 = `swarmdev/contracts/` 代码本身（pydantic schema，拒绝非法构造）。
> 本文是人读视图。任何生产实现必须通过"与 swarmdev 契约的往返序列化兼容测试"方可接入。

---

## 1. Spec 文档（`spec_doc.py`）

**文件形态**（ADR-1）：每个 spec 一个 Markdown 文件 + YAML frontmatter：

```markdown
---
spec_id: SPEC-infer-router-0001
domain: infer_router.routing
version: 1.2.0
bc_nbc_log:
  - {delta: DLT-..., compatibility: bc}
l1_approved_by: human:owner
---
# L1 业务意图
（为什么、给谁、成功是什么——人类批准文本）

# L2 开发契约
## CL-RT-01 会话亲和路由
- assumes: 请求携带 session_id；worker 列表非空
- guarantees: 同 session_id 的连续请求路由到同一 worker（worker 存活期间）
- invariants: 路由决策不修改 KV 缓存块归属
- dont_care: DC-01（worker 故障时的重选目标不做约束）
- witnesses:
  - {kind: holdout_scenario, ref: SCN-affinity-01}
  - {kind: differential, ref: DIFF-affinity-01}
- validation_state: model_checked
- r_level: R1

# L3 实现说明（链接）
- l3/routing_notes.md
```

**机器模型**：`SpecDoc{spec_id, domain, version(semver 强校验), l1_intent, l1_approved_by, l2_clauses[], l3_links[], dont_care[]}`；
`L2Clause{clause_id(^CL-…), assumes[], guarantees[], invariants[], witnesses[], validation_state, r_level_declared}`。

**硬规则**（schema 与 CI 双重执行）：
1. `is_verifiable == witnesses 非空`。无见证条款自动进 `unverifiable_clauses()`，只能作 advisory，不得作放行依据（PDR §8）。
2. `dont_care` 必须引用已存在条款，且必须写明 `out_of_domain_behavior ∈ {arbitrary, blocking}`（research 02：不允许留白）。
3. `witness_coverage()` 是判据覆盖率指标的分子来源。

## 2. R 级注册表（`r_level.py`）与 spec-delta（`spec_delta.py`）

- `RArtifact{artifact_id, path_pattern, level(R0–R3), declared_by_spec}`；未登记制品默认 R0。
- 规则函数即宪法：`fanout_allowed(<R3)`、`discard_allowed(≤R1)`、`requires_human_approval(≥R2)`；`WaveTask` schema 直接拒绝 R3+fanout>1。
- `SpecDelta{from_version, to_version, entries[{op, target_kind, compatibility(BC/NBC), requires_human_approval}]}`：
  - 任一 NBC ⇒ 必须 major bump 且 NBC 条目必须 `requires_human_approval=True`；
  - 纯 BC ⇒ 禁止 major bump；schema 层拒绝违规版本号组合。

## 3. 信封协议（`envelope.py`）——契约间通信的唯一合法通道

13 种信封 + 接收矩阵（**机械执行，违反即 VisibilityError/CapabilityError**）：

| 信封 | 发送方所需能力 | 合法接收角色 |
|---|---|---|
| WAVE_PLAN | wave.plan（architect） | leader |
| SPEC_ASSIGNMENT | wave.plan | builder, leader |
| INSTANCE_SUBMISSION | instance.build（builder） | verifier, leader |
| GATE_RESULTS | gate.execute（verifier） | leader, architect |
| JUDGE_REQUEST | gate.execute | judge |
| JUDGE_VERDICT | judge.verdict.write（judge） | verifier, leader |
| HOLDOUT_RESULTS | holdout.read | verifier, architect |
| MEASUREMENT_REPORT | gate.execute | spec_moderator, architect |
| SPEC_CONVERGENCE | spec.l2.write | spec_steward, human |
| DRIFT_ALERT | drift.report（reconciler） | leader, human |
| ADMISSION_RECEIPT | admission.decide（leader） | leader, architect, spec_steward, moderator, human |
| MEMORY_WRITE_REQUEST | spec.read | spec_moderator |
| RULE_PROPOSAL | rule.proposal（deep_agent） | human |

**载荷冻结**：`SPEC_ASSIGNMENT.payload` 键集合恒为 `{spec_id, version, ru_id, l1_intent}`（集成测试断言）——holdout/rubric/判据永不进入 builder 可达信封。
**能力矩阵**（`roles.py CAPABILITY_MATRIX`，宪法不变量的可执行投影）：builder 无 holdout.read / judge.execute / memory.write；rule.approve 仅 human；判别能力（gate.execute、judge.*）与生成能力（instance.build）互斥于角色集。

## 4. Oracle 契约（`oracle.py`）

- `HoldoutScenario{scenario_id, spec_clause_ids[], title, setup_commands[], run_command, env, timeout_s, expectation{exit_code, stdout_regex, stderr_regex, files_exist[], files_contain{}}, rotation_epoch, confidential=true}`。
- `OracleBundle{bundle_id, spec_id, spec_version, scenarios[], rubrics[], calibration_items[]}`——bundle 与 spec 版本绑定，spec 升级必须重挂 bundle。
- `JudgeRubric{dimensions[{dimension_id, levels[{level,label,observable_criteria}], weight}], abstain_allowed, evidence_required}`；一个 rubric 只评一个目标。
- `JudgeVerdict{verdict ∈ veto|no_veto|abstain, reasons[], evidence_refs[], samples, agreement_ratio}`；schema 拒绝无理由 veto；**不存在"豁免硬门禁"字段**。
- `CalibrationItem{artifact_summary, gold_verdict}`：金标集 50–100 条，人工标注。

## 5. 门禁结果与证据收据（`receipt.py`）

- `GateOutcome{gate_id(H1–H8), status ∈ pass|fail|blocked|inconclusive|skipped, evidence_refs[], details, duration_s}`。
- `EvidenceReceipt`：PR 的机器形态。`admitted=True` 时 schema 强制：H1–H8 outcome 齐全、全 pass、软判词无 veto。字段含 chosen/discarded 实例（**每个被丢弃实例必带 measurement_conclusion**）、差分结论、漂移结果、commit_ref / rollback_ref（原子性与可回滚）。

## 6. 波次（`wave.py`）与测量（`admission/measurement.py`）

- `Wave` 状态机：`PLANNED→COLLECTING→ADJUDICATING→COMMITTING→COMMITTED`，任意非终态可 `ROLLED_BACK`；COMMITTED 后只能前向修复（不可回滚已提交）。
- `WaveTask{ru_id, spec_delta_ref, artifact_ids[], r_level, fanout{n_target 1..8, uncertainty_signals{}}}`。
- 判别表（PDR §6 的六行，`classify_fanout(results, has_divergence, min_samples=3)`）：

| 观测 | Outcome | 处置 |
|---|---|---|
| n<min 且有失败 | INSUFFICIENT | 补采样至 ≥3 再判 |
| 全过且无差分 | CLOSED | 选次优判据实例准入（成本最小，平手取 id 序） |
| 全过但有差分 | SILENCE | 不准入；测量报告交 spec moderator 裁定自由度/补条款 |
| 部分过部分败 | DIVERGENCE | 不准入；spec moderator 收敛 spec，oracle 不动 |
| 当前档全败、高档过 | TIER_GAP | spec 澄清 + 记录档位需求 |
| 全档全败 | SPEC_ORACLE_CONFLICT | 规范级事件，steward+architect 会诊 |

- H5 语义细化（ADR-8）：R<R3 时 H5 是 RU 级集成差分信号（失败转 has_divergence，不株连单实例）；R3 时 H5 为逐实例黄金比对。

## 7. 接口冻结与兼容

- 角色 harness 绑定表：`swarmdev/teams/harness_map.py`（每角色 carrier/lifecycle/证据锚点）。
- 档位策略：`swarmdev/teams/tiering.py`（judge/verifier ≥ builder，schema 强制）。
- 门禁装配：`swarmdev/integration/wiring.build_gate_runner(...)`（唯一合法装配入口；生产实现保持同签名扩展）。
- H7 接线：`wiring.drift_detector_callable(DriftDetector)`。

## 8. 契约间通信测试清单（已实现于 `swarmdev/tests/`）

1. 契约 schema 自洽（11 项）：semver/见证义务/dont_care 引用/R3 fanout 拒绝/delta SemVer 联动/收据准入代数/波次状态机/能力矩阵不变量。
2. 总线可见性（含在 1 与 e2e）：builder 读判据信封→VisibilityError；builder 发门禁结果→CapabilityError；HOLDOUT_RESULTS 发给 builder→VisibilityError。
3. 端到端 8 项：CLOSED 准入（含收件完整性+信封审计）、SILENCE（过门实例行为差分→不准入+测量报告入总线）、DIVERGENCE（混合成败→回滚+丢弃结论）、judge veto 否决、@REQ 漂移标签→H7 拦截、R3 无黄金拒绝、R3 人类批准黄金后准入、H7 接线直测。
4. 门禁/单元级 95 项：oracle 篡改哨兵、场景超时、holdout 令牌、golden 审批、judge 采样/位置偏置、κ 数值、预算门、fail-fast。

**新增跨包接口的准入规则**：任何新信封/schema 字段必须先改 `swarmdev/contracts/` 并补测试，绿后方可在生产实现中使用（契约变更走 spec-delta 流程）。
