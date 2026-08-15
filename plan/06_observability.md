# 06 · 观测、健康度与降级

## 1. 七项核心指标（C12 HealthMetrics，schema 与判定已实现并测试）

| 指标 | 计算口径 | 采集源 |
|---|---|---|
| spec 闭合度 closure_rate | 波次内"closed"判定的 task 数 / 全部完成 task 数 | measurement 事件流 |
| spec 熵 spec_entropy | 单位 spec-delta 引发的 silence+divergence 事件数 | measurement 事件流 |
| 判据覆盖率 witness_coverage | 有机械见证的 L1/L2 条款占比；unverifiable 计数 | specrepo.coverage（已实现） |
| 逃逸缺陷率 escape_defect_rate | 过 H∧S 后在后续（B 线/线上）被证伪 / 准入总数 | receipts × B 线发现 × 线上缺陷回流（人工标记） |
| 漂移率 drift_alerts + drift_fix_latency_h | H7 报警数 / 修复时延中位数 | reconciler 报告（WP5） |
| judge 校准 judge_kappa + judge_abstain_rate | 与标注集 Cohen kappa；弃权率 | 校准管线（WP6） |
| 返工率 rework_rate 与单位准入成本 unit_admission_cost | 重跑 task / 总 task；tokens+spend / 准入数 | journals + receipts |

## 2. 人类报告面（每波次 + 每周）

只含：L1/L2 相关事项、健康度评分（上表归一化加权）、deep agent 提案列表、降级事件。
**不含**：代码 diff、实例选择细节、RU 升降档过程、个别例外（structure.md §9）。字段白名单由 WP13 测试强制。

## 3. 健康度评分（0–100）

```
score = 100
  - 30 × min(1, escape_defect_rate / 0.02)      # 逃逸最重
  - 20 × (judge_kappa < 0.6 时 1，否则线性衰减)
  - 15 × min(1, drift_alerts / 5)
  - 15 × min(1, unverifiable_clauses / max(1,total_normative) / 0.1)
  - 10 × min(1, rework_rate / 0.5)
  - 10 × min(1, unit_admission_cost / budget)
```

## 4. 降级触发与动作（D-27，evaluate_downgrades 已实现）

| 触发 | 机械动作（WP13/WP14 实现） | 恢复条件 |
|---|---|---|
| escape_defect_rate > 2% | 该域回退一迁移阶段；新增"人类 L2 之外额外确认"卡点 | 连续 2 窗口回落阈值内 + 根因案例入规则库 |
| judge_kappa < 0.6 | S 门禁停用（硬门禁不动）；该域暂停自动准入 | kappa 回归 ≥0.6 |
| drift_alerts 突增（>5/窗口 且时延升） | 冻结该域 fan-out；转 B 标定流水线 | 漂移清零 + reconciler 报告 |
| 成本超预算 ∧ 闭合度未改善 | 降 N、缩再生单元、升档位门槛（配置项自动调整 + 案例记录） | 成本回落 ∧ 闭合度改善 |
| spec↔oracle 反复冲突 | 升级人类议题（规范级） | 人类裁决 |

降级永远是回退阶段，不是改判据（structure.md §13）。

## 5. 成本核算纪律（TCO 研究采纳）

1. 全部 LLM 调用收敛到 IntelliRouter 部署组（D-19），调用侧记账（tokens_in/out、按部署组单价折算 spend_units）；
2. 成本函数计入缓存折扣（前缀缓存命中部分按折扣价计），防"切换模型致两侧缓存冷却"的隐性成本；
3. 每 spec-delta 预算池化（波次级），跨 task 再分配；
4. 月度成本报告按域/角色/档位三维聚合（WP13）。

## 6. 校准与演练日历

| 项 | 频率 | 负责 |
|---|---|---|
| judge kappa 回归 | rubric/模型/模板变更时 + 每月 | WP6 管线自动 |
| holdout 轮换 | 90 天 | WP3 rotate 工具 |
| 红队注入演练（门禁可信性） | 每季度 | WP14 drills |
| 回滚演练 | 每季度 | WP4 rollback_drill |
| 标定波次（B 线） | 每域每月 ≥1 次 | T-CAL |
| N 抽样校准（常规 R0 域抽 10% task 跑 N=3） | 每波次 | run_wave 内置 |
