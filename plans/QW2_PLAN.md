# OPC 开发 Swarm 工程总计划（Master Plan）

> 前提约束：[structure.md](file:///workspace/structure.md)（PDR-001 范式决策记录）。本计划不重开其中任何已锁定决策。
> 代码基线：CAPABILITY_MAP.md 所列 11 个 submodule 锁定 commit。
> 研究输入：`research/` 全部研究简报，采纳/否决清单见 [00_decisions.md](file:///workspace/plan/00_decisions.md)。

## 一句话

以 **spec 为唯一真值**、**门禁代数为物理层**、**openJiuwen 原生团队/工作流/护栏机制为承载**，构建 1 人类 + N agent 的开发 swarm；本计划把全部跨团队工程决策固化为**契约（C01–C13）**，把门禁与 oracle 实现为**已测试的可执行代码（`swarmfoundry/`）**，各实施团队只需在自己工作包（WP）内工作。

## 计划文档索引

| 文档 | 内容 | 读者 |
|---|---|---|
| [plan/00_decisions.md](file:///workspace/plan/00_decisions.md) | 全部工程决策 + 研究采纳/否决表 | 所有人（必读，唯一裁决依据） |
| [plan/01_architecture.md](file:///workspace/plan/01_architecture.md) | 系统架构：拓扑、角色→openJiuwen 精确映射、团队边界、harness 配置、提示词骨架 | 架构/各 WP leader |
| [plan/02_contracts.md](file:///workspace/plan/02_contracts.md) | 契约目录 C01–C13：权威定义位置、生产方/消费方、通信测试义务 | 所有 WP |
| [plan/03_workpackages.md](file:///workspace/plan/03_workpackages.md) | 工作包分解 WP0–WP14：范围、输入输出契约、文件清单、DoD、禁区 | 各实施团队 |
| [plan/04_gates_oracles.md](file:///workspace/plan/04_gates_oracles.md) | H1–H8 + S 门禁运行规范、oracle/holdout 编写与管理规程 | architect / verifier / 域团队 |
| [plan/05_waves_delivery.md](file:///workspace/plan/05_waves_delivery.md) | 波次生命周期、准入事务、事件协议、回滚、PR 重定义 | leader / 交付团队 |
| [plan/06_observability.md](file:///workspace/plan/06_observability.md) | 健康指标、spec 熵、成本核算、降级触发 | 人类 / deep agent |
| [plan/07_repo_layout.md](file:///workspace/plan/07_repo_layout.md) | 仓库布局、分支模型、环境、CI 拓扑、迁移梯度 M0–M3 执行脚本 | 所有人 |

## 已交付且实测通过的基线（WP0）

`swarmfoundry/`（物理层参考实现，全部契约的权威定义与 CI 门禁本体）：

- 契约 schema C01–C13（`src/swarmfoundry/schema/`，纯 stdlib，JSON roundtrip 校验）
- spec 仓：装载/校验、条款密封哈希（seal）、见证覆盖统计（`specrepo/`）
- 契约面提取 + 破坏性变更检测（`contracts/`，H4 机械见证）
- oracle 引擎：场景执行（5 类判据）、R3 黄金输出（人工审批纪律）、实例间差分（`oracle/`）
- 门禁族 H1–H8 + S（judge 面板聚合）+ 门禁代数 `Admit=∧H∧∧S`（`gates/`，fail-closed）
- 证据收据（EvidenceReceipt）与登记
- 契约通信参考总线 + 信息不对称强制（`comm/`）
- CLI（`swarmfoundry spec-validate/spec-seal/surface-*/oracle-run/gates-run/selftest`）

验证状态（本仓库当前 HEAD 实测）：

```bash
cd /workspace && PYTHON=/workspace/.venv/bin/python bash ci/run_gates.sh   # ALL GATES PASSED
cd /workspace/swarmfoundry && /workspace/.venv/bin/python -m pytest tests -q  # 66 passed
/workspace/.venv/bin/swarmfoundry selftest                                    # 13/13
```

## 实施路线（详见 07_repo_layout.md §迁移梯度）

- **M0 收割（WP1–WP6 并行）**：在试点域建立 H1–H4+H7 与 spec 收割；verifier 工作流上线。
- **M1 锚定（WP7–WP10）**：holdout 覆盖率达标后 R0 可丢弃重生；H5 差分门启用；波次事务跑通。
- **M2 再生（WP11–WP12）**：常规 N-fan-out；judge 校准达标；标定流水线（B 线）运行。
- **M3 工厂（WP13–WP14）**：健康度驾驶舱、deep agent 提案通道闭环、全指标达标。

## 给执行 agent 的三条铁律

1. **契约以代码为准**：任何 WP 的输入输出必须通过 `swarmfoundry.schema` 的 `from_dict` 校验与 `tests/contracts/` 中的通信测试；改契约 = 走 spec-delta + 人类 L2 批准。
2. **fail-closed**：门禁缺证据、缺 holdout、缺 seal、judge 不足额，一律拒绝准入；不得加"跳过"开关。
3. **信息不对称是机制不是礼仪**：builder 的沙箱策略、上下文注入、消息路由三层都必须通过 `assert_information_asymmetry` 级别的机械检查。
