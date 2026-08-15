# 05 · 波次与准入事务协议

## 1. 波次生命周期（状态机）

```
PLANNED ─→ FROZEN ─→ BUILDING ─→ VERIFYING ─→ MEASURING ─→ ADMITTING ─→ CLOSED
   │                      │            │            │            │
   └──────────────────────┴────────────┴────────────┴──→ ABORTED（预算/降级/人类中止）
```

| 状态 | 进入动作 | 负责角色 | 产物 |
|---|---|---|---|
| PLANNED | architect 从 spec 依赖图切出 spec-delta 割集，产 WavePlan（C09） | architect | waves/plans/<wave>.json |
| FROZEN | 提取并冻结接口面（ContractSurface）；holdout rotation 确认 | architect | waves/freeze/<wave>/*.surface.json |
| BUILDING | leader 依 N 自适应（D-20）fan-out 临时 builder 团队 | leader | instances/<wave>/<task>/inst-* |
| VERIFYING | 每实例独立跑 verifier 工作流（04 文档全门禁） | verifier | GateResult×9 / AdmissionDecision |
| MEASURING | leader 汇总 N 份结果 → classify_measurement（C11 语义，已实现） | leader | measurement.event |
| ADMITTING | 闭合则选实例 → admit 事务（WP4）；否则处置见 §3 | leader | receipt + world 合并 |
| CLOSED | journal 归档、临时团队销毁、成本入账 | leader | waves/journals/<wave>.journal |

## 2. 事件序列（C10 method，与 tests/contracts/test_wave_communication.py 完全一致）

```
leader    → builder        task.assign            {task_id, spec_delta_ref, n_fanout}
builder   → leader         task.instances_ready   {task_id, instance_ids[]}
leader    → verifier       verify.request         {task_id, instance_ids[]}
verifier  → leader         gate.result            {task_id, gates: GateResult[]}
verifier  → leader         admission.decision     AdmissionDecision(C03)
leader    → spec_moderator measurement.event      MeasurementEvent(C11)   # 仅在沉默/分歧/不足/冲突时
leader    → spec_moderator receipt.registered     {receipt_id, admitted}  # 准入后
```

约束：全部消息携带 `correlation_id = task_id`；bus ledger 全量审计；builder 发判别类 method 或收 holdout 材料 = ProtocolViolation（已测）。

## 3. 测量判别表（structure.md §6 的可执行版，classify_measurement 已实现并测试）

| 观测 | 判定 | 处置 |
|---|---|---|
| N≥3 全过 ∧ 差分空 | closed | 选实例准入；记录闭合度 |
| N≥3 全过 ∧ 有差分 | silence | measurement.event → moderator：dontcare 登记或 spec-delta；本波次该 task **不准入**（等待裁决后重跑） |
| N≥3 部分过 | divergence | moderator 收敛 spec；oracle 不动；重跑 |
| 全失败 → 升档后成功 | tier_insufficient | spec 澄清 + 记录档位需求 |
| 全失败 → 升档仍败 | spec_oracle_conflict | 规范级事件：steward+architect+人类会诊 |
| N<3 且有失败 | insufficient_instances | leader 自动补足至 ≥3 再判（run_wave 已规划，WP10） |

## 4. 准入事务（原子性定义）

准入提交点 = `ops/admit.py` 的 squash 合并 commit（WP4）。事务边界：

- **开始**：receipt 校验通过（admitted ∧ content_hash ∧ r_level 批准件齐备）；
- **原子体**：单 commit（实例 diff + receipt 引用）；
- **回滚**：`git revert <commit>`（单 commit 可完整回滚）+ 实例 worktree 丢弃（实例可丢弃）；
- **失败**：任何一步失败 → 不产生合并；world 保持原状；失败记录入 journal。

R2/R3 附加：`--human-approval-ref` 必填（admit.py 强制）；R3 同时要求黄金输出无变更或已走黄金更新审批。

## 5. 实例选择（closed 时的次要判据）

顺序：① 成本最低（该实例的 token/spend）→ ② 确定性得分最高（重复运行输出稳定度，verifier 附测）→ ③ 代码量最小。选择理由写入 receipt.notes。**人类不参与选择**（structure.md §9）。

## 6. 波次预算与熔断

- WavePlan.budget_units 为波次总预算（token 折算 + spend）；run_wave 每步记账（CostRecord 累加）；
- 超支 → 波次转 ABORTED：未完成 task 全部丢弃实例、已准入部分不回滚（已准入即世界状态）、产成本案例（C13 素材）；
- 单 task 级：builder 工具调用超时受 ability_manager 上限约束（agent-core ability_manager.py:L78-L83，DEFAULT_TOOL_CALL_TIMEOUT=300s）。

## 7. 与 Checkpointer 的事务配置

- 持久团队 session：redis checkpointer（分布式就绪但单机模式运行）；
- SwarmFlow journal：`waves/journals/`（WAL，runner.py:L141-L177）；
- 回滚路径：波次 ABORTED → journal 定位最后检查点 → 之后产生的实例 worktree 全部删除（脚本 `ops/wave_abort.py`，WP10）；
- 世界侧永不 rewind：世界的变更只经准入事务，故无"半提交"状态。
