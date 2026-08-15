# CI 门禁布置与 Oracle 校准手册（PLAN_CI.md）

## 1. 门禁在 CI 中的位置（纵深栈，oracle_ci_gate 研究阶段 0–6 的本地化）

```
阶段0 任务前   spec-lint（见证覆盖）+ holdout 入库四道质量闸（WP2）
阶段1 agent 运行时（builder 本地快环）
               jiuwenswarm reliability detectors（tool_error/repeat_tool/…, config.yaml:L1229-1287）
               + constitution_rail（AbortError 即时中止）
阶段2 实例提交（verifier，确定性硬门禁）
               opc-gate-runner：H1→H8 顺序执行，fail-fast 可配（P0 全跑以收集测量）
               干净环境：每次新 venv/容器，禁 builder 缓存残留
阶段3 并行软门禁  JudgeWorkflow（S），仅当 H 全过后执行（省成本）
阶段4 人类面     仅 L2 契约 diff（spec 仓 PR）+ R2/R3 显式批准 + waiver 审批；不看代码 diff
阶段5 合并       world.admit()：账本追加 + git merge --no-ff（先测后合）
阶段6 合并后慢环  夜间：reconciler 全树 H7 巡检；judge 校准回归；holdout 轮换检查；
               逃逸缺陷回灌评估集（新场景入 oracle_store 并更新见证）
```

## 2. GitHub Actions 工作流（WP3 实现，语义如下）

```yaml
# .github/workflows/opc-gates.yml（骨架）
on: [pull_request]
jobs:
  lint:        # ruff --select E9,F（opc/ + swarm/ + cartographer/）
  unit:        # opc pytest tests/unit
  contract:    # opc pytest tests/contract（必需，独立 job 防被跳过）
  gate-semantics:  # opc pytest tests/gate_semantics
  gates-smoke:     # opc-gate-runner 对 fixtures 双跑：
                   #   无 waiver：期望 exit=1 且 blocking 含 H5（证明门禁未架空）
                   #   有 waiver + soft PASS：期望 admitted=true（证明 waiver 链路）
  import-boundaries:  # import-linter 契约（模块边界，防绕契约直连）
```

分支保护：main 必需全部 check；`paths-ignore` 一律不用（宁可多跑）；agent 服务账号对 `.github/`、`opc/gates/`、`opc/schemas/`、`oracle_store/` 无写权限（CODEOWNERS=人类）。

**门禁自身的门禁**（防“形同虚设”）：每月一次变异自检——对门禁代码注入语义变异（如把 `==` 改为 `!=`），验证 gate-semantics 套件必然变红；变异存活=该门禁测试形同虚设，列入整改。

## 3. Oracle 校准与体检（周期性例行）

| 例行 | 频率 | 方法 | 阈值 | 不达标动作 |
|---|---|---|---|---|
| judge 一致性 | 每周/换模型 | 校准集双标 + Cohen kappa | κ≥0.6 | S 停用（软降级），转人工残差 |
| judge 稳定性 | 每周 | 同题重判 + 换序一致率 | ≥0.9 / 一致 | 同上 |
| judge 偏差审计 | 每月 | 长度扰动/来源线索注入对照 | 无显著偏移 | rubric 修订（人类批准） |
| oracle 信号质检 | 每 PR | H2 内置（无断言测试不计强度） | 全弱→FAIL | 拒收 |
| 变异得分（oracle 体检） | 每月 | 对实例代码注入变异，H2/H3 应检出 | 检出率≥0.8 | 补场景/断言（architect） |
| 逃逸缺陷复盘 | 事件驱动 | 过 H∧S 后被证伪 → 案例台账 + 回灌新场景 | 率≤阈值（M2 起） | 降级一级 |
| holdout 新鲜度 | 每月 | 轮换批次 + 退役清单 + 哈希承诺核对 | 按 WP2 节奏 | 冻结相关域准入 |
| flaky 治理 | 持续 | 场景失败分诊三分类；噪声入 don't-care 裁决 | 同一场景连续噪声→隔离 | spec moderator 裁决 |

## 4. 统计门禁升级路线（P2，本期仅预留接口）

- Wilson 三判定 / SPRT（α=0.05, β=0.10）用于 S 门重复采样与 R3 统计比对；`JudgeVerdict`/`DiffReport` 已为三值判定设计，P2 增加采样预算字段即可。
- 行为指纹 + Hotelling T²：检测“功能全绿但行为漂移”（对 LLM 采样制品尤其重要）；数据来源=H5 runs 的 normalized_output。
- 重放预算公式：`n ≥ ln(α)/ln(1−p̂)`；“跑 3 次都绿”不构成证据——此结论必须写进 verifier 运行手册。

## 5. 本地等价与调试

- `scripts/ci_local.sh`：按顺序执行 §2 全部 job（无 GitHub 环境可用），退出码语义与 CI 一致。
- 单门调试：`opc-gate --gate H3 --instance-dir … --spec-dir … --contract-id … --holdout-dir …`
- 全门调试：`opc-gate-runner … --waivers-file …`（JSON 输出含每门 verdict 与 waiver 引用）
- 账本体检：`opc-admit ledger-verify --ledger world/ledger.jsonl`
- 差分调试：`opc-diff --instance a=… --instance b=… --corpus-file … --entrypoint payments:compute_fee --redact elapsed_ms`
