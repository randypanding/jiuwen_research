# 07 · 仓库布局、分支模型与迁移梯度执行

## 1. 本仓（swarm HQ）布局

```
/workspace（jiuwen_research → 本仓）
├── structure.md               # PDR-001（宪法前件，只读）
├── CAPABILITY_MAP.md          # 能力基线（只读）
├── research/                  # 研究档案（只读）
├── PLAN.md                    # 计划总入口
├── plan/                      # 00–07 计划文档（本文档集）
├── swarmfoundry/              # 物理层实现 + 测试（WP0，已完成）
├── ci/run_gates.sh            # CI 门禁主入口（R3 级制品）
├── .github/workflows/         # CI 拓扑
├── spec/                      # spec 仓（唯一真值）【WP1 建立】
│   ├── constitution.md
│   ├── domains/<domain>/spec.json + harvest_report.md
│   └── registry/artifacts.json + seals.json
├── prompts/<role>.md          # 角色 system prompt（版本化）【WP9–11】
├── harness/team_specs/*.yaml  # TeamAgentSpec【WP9–11】
├── waves/                     # 波次工件【WP10】
│   ├── plans/<wave>.json      # WavePlan
│   ├── freeze/<wave>/         # ContractSurface 冻结面
│   ├── run_wave.py verify_instance.py run_calibration.py   # SwarmFlow 脚本
│   └── journals/<wave>.journal
├── instances/<wave>/<task>/   # 可丢弃实例（.gitignore，随时可清）
├── receipts/                  # 证据收据（入库，审计链）
├── decisions/                 # 裁决审计（T-NORM）
├── proposals/                 # RuleProposal 库（C13）
├── calibration/<domain>/      # judge 标注集
├── ops/                       # 运维脚本（admit/rollback/rotate/reconcile/metrics/migration_gate/drills）
└── agent-core/ jiuwenswarm/ ...（11 个 submodule，只读基线，不修改）
```

独立仓：
- `holdout`（D-05）：holdout 场景库；访问控制 = git 权限 + 文件系统 + 沙箱策略三层。
- `codesearch-mcp`（WP8）：cartographer 检索服务。
- 世界库 = 目标代码仓（试点期：skillhub、deepsearch 的 codesearch 目录所在仓）。

## 2. 环境与凭据

| 项 | 值 |
|---|---|
| Python | ≥3.11（CI 用 3.12；本沙箱 3.14 已验证） |
| swarmfoundry 安装 | `pip install ./swarmfoundry`（零依赖） |
| 测试 | `pytest`（唯一测试依赖） |
| jiuwenswarm 运行 | 按其 README/config（team.runtime.mode=local；redis：JIUWEN_KV_URL） |
| 模型 | IntelliRouter 三档部署组：TIER-L/M/H（D-19）；端点经 jiuwenswarm models.defaults[] |
| 凭据 | 模型/仓库 token 一律环境变量注入；H6 默认规则扫描密钥泄漏 |

## 3. 世界库分支模型

```
main（已准入世界状态）
 └── admit/<receipt_id>    # 准入分支：单 squash commit（实例 diff + receipt 引用）
      └── 合并方式：merge --no-ff（保留 receipt 可追溯性）
回滚 = git revert <merge-commit>（05 文档 §4）
```

pre-merge hook（world 仓）：检查 `receipts/<receipt_id>.json` 存在、admitted==true、content_hash 匹配、r_level≥R2 时 human_approval_ref 存在。

## 4. CI 拓扑

| Job | 触发 | 内容 |
|---|---|---|
| swarmfoundry-ci（已建） | push/PR 本仓 | compileall → pytest → selftest → 门禁完整性 |
| plan-lint（WP14） | plan/ 或 swarmfoundry/schema 变更 | 契约 schema 面向自身跑 H4（与上一版本 diff，breaking 需 waiver 引用） |
| world-<domain>-gates（WP14） | 世界库域 PR | 该域 gates.<domain>.toml 全门禁（矩阵） |
| holdout-rotation-check（WP14） | 每日 | rotation 超期告警 |

## 5. 迁移梯度执行（structure.md §12 的落地脚本）

### M0 收割（当前→第 1 里程碑）
并行开工：WP1、WP2、WP4、WP6、WP8（检索先行铺底）。
**进阶闸门（migration_gate.py 检查项）**：
- [ ] D1 域 spec.json 通过 validate，witness_coverage≥0.9，seal 建立；
- [ ] H1–H4+H7 在 D1 域真实跑通（skill_review 既有代码作为首个"实例"过门禁）；
- [ ] trace tag 回填 PR 合入；reconciler 上线（WP5 最小版）；
- [ ] 人类看 L1/L2 与代码 diff 的流程演练 1 次。

### M1 锚定
开工：WP3、WP5 完整版、WP7、WP9、WP10。
**进阶闸门**：
- [ ] D1 holdout ≥20 场景且 FAIL_TO_PASS 标注完整；H3 生产化（沙箱+泄漏扫描）；
- [ ] H5 差分门在 D2（greenfield）N=3 fan-out 上产出首个"silence"或"closed"读数；
- [ ] admit/rollback 演练通过（字节级一致）；
- [ ] spec 闭合度连续 2 波次可测（有读数即达标，不要求阈值）。

### M2 再生
开工：WP11、WP12、WP13。
**进阶闸门**：
- [ ] 连续 3 波次零逃逸缺陷（D1+D2）；
- [ ] judge kappa≥0.6（校准集达标），弃权率 <25%；
- [ ] B 线首个标定波次完成且发现 ≥3 条有效；
- [ ] R0/R1 常规 fan-out 再生运行（实例丢弃流程无人工介入）。

### M3 工厂
开工：WP14 收尾 + 运营。
**达成标志**：健康度评分连续 4 周 ≥70；deep agent 提案通道完成一次"提案→批准→新 session 生效"闭环；五演练全绿。

**跨阶段禁令**：闸门未过不得进入下一阶段；在 oracle 覆盖率不足的域宣布"代码可丢弃" = 取消门禁 = 范式致命误用（structure.md §12 末）。

## 6. 执行 agent 快速上手（每个 WP 的第一步）

```bash
# 0. 环境
cd /workspace && uv venv .venv && uv pip install --python .venv/bin/python pytest ./swarmfoundry
# 1. 读：PLAN.md → plan/00_decisions.md → plan/02_contracts.md → 本 WP 节
# 2. 跑基线，确认接手时全绿
PYTHON=.venv/bin/python bash ci/run_gates.sh
# 3. 按 WP 交付清单实现；每完成一个契约面，先写/跑对应通信测试
cd swarmfoundry && ../.venv/bin/python -m pytest tests -q
# 4. 提交前：ci/run_gates.sh 全绿；契约变更必须走 02 文档变更流程
```
