# 05 CI 门禁与 Oracle 集成规范

> 门禁必须确定性：由 WorkflowAgent/CLI 机械执行，不由自主 agent 决定跑不跑（PDR-001 §11）。
> 参考实现已全部通过测试：`swarm_kernel/gates/`、`ci/run_all_gates.sh`、`.github/workflows/swarm-kernel-gates.yml`。

## 1. 门禁族与实现对照

| 门 | 守护对象 | 实现（swarm_kernel.gates.hard_gates） | 判定输入 |
|---|---|---|---|
| H1 | 构建/类型/静态 | h1_build：命令列表（默认 compileall），可配 | 退出码 |
| H2 | 单元/属性测试 | h2_unit：pytest（实例自带 tests/） | 退出码 |
| H3 | 场景 holdout 套件 | h3_holdout：ScenarioGrader，FAIL_TO_PASS∧PASS_TO_PASS 全过 | 场景结果 JSON（见证） |
| H4 | 契约面/破坏性变更 | h4_contract_surface：contract.json vs baseline + 波次冻结摘要 | removed_exports/changed_signatures |
| H5 | 差分/黄金输出 | h5_differential：组内差分（seed 语料）或黄金比对 | 差分报告/快照 manifest |
| H6 | 不变量与护栏 | h6_invariants：密钥扫描、危险模式、禁用依赖、许可 denylist、体积 | problems 列表 |
| H7 | spec↔code 漂移 | h7_drift：锚点摘要比对 | stale/orphan/unimplemented 计数 |
| H8 | 成本/资源预算 | h8_budget：report.json vs GateConfig 预算 | 超支维度 |

## 2. 退出码与判定代数（不可改）

- 0 = pass；1 = fail（任一门 FAIL）；2 = inconclusive（含 error/缺门/缺件）。
- `Admit = 八门全 PASS ∧ judge 不 veto`；veto 只否决不救场；inconclusive 永不准入。
- 优先级：FAIL 优先于 inconclusive（一门 FAIL 即整体 FAIL，参照 suite_exit_code 实现与测试）。

## 3. flaky 策略（Wilson 三判定，已实现 wilson_verdict）

- 确定性门禁默认单次尝试；标注 flaky 的套件最多重试至 n 次。
- 判定：Wilson 95% 区间 lower≥0.4 → pass；upper≤0.6 → fail；否则 inconclusive（n=1 按点估计）。
- inconclusive 用例进隔离区台账（不删除）；连续 3 次 inconclusive 强制转人工分诊。

## 4. oracle 场景编写规范（T2 执行）

1. 场景 YAML 字段固定（scenario_id/title/inputs/expectation/grading/tags）；expectation 支持 equals/approx(tol)/contains/json_equals 四种，其他形态 = 判 fail（防真空断言）。
2. FAIL_TO_PASS：本 delta 必须转绿的场景；PASS_TO_PASS：回归场景，必须保持绿。
3. 场景先行：spec-delta 未附场景引用前，该条款 unverifiable，只能 advisory，不作放行依据。
4. oracle 独立性：checker/语料只放 oracle 目录，禁止从实例目录加载任何判分代码（grader 只从实例加载 run 适配器）。
5. 防污染：场景输入不得出现在 builder 可见的任何训练/示例材料中；场景库定期轮换（M2+）。

## 5. 黄金输出纪律（R3，T3 执行）

1. CI 永不自动写黄金（GoldenPolicyError，CI=true 时 write 被拒，测试覆盖）。
2. 更新流程：轨道 B（标定流水线）产出证据 → 人类评审 diff → approved_by 落 manifest → 生效。
3. manifest 不一致 = 比对无效（fail-closed）；缺快照 = fail-closed。
4. R3 制品禁止 fan-out（FanoutRequest schema 拒绝 n>1，测试覆盖）。

## 6. waiver 与豁免

- 豁免只能来自 oracle/waivers.yaml（条款 ID、原因、过期时间、批准人）；过期自动失效。
- 豁免不改判据：只是把某条款暂时移出放行依据（降为 advisory），硬门禁数量不减少。

## 7. 门禁上线路径（先告警后阻断）

1. M0：H1–H4+H7 全部以"告警模式"接入目标域 CI，积累精度基线（2 个波次）。
2. M1：收割域内 H3/H4/H7 转强制阻断；H5 对 R0 启用差分；H8 按预算强制。
3. M2+：全族强制；judge 软门禁在 kappa≥0.6 的域启用否决权。

## 8. CI 工作流规范（新域套用）

按 `.github/workflows/swarm-kernel-gates.yml` 三段式复制：
1. 测试段：契约 / 单元 / 通信 / e2e 四组独立 job（失败定位粒度到层）。
2. 演示段：good 必须 exit 0；bad 必须 exit 1；drift 必须 exit 1（用断言脚本钉住退出码语义，防止门禁静默退化）。
3. 制品段：suite-*.json 报告上传 artifact（证据收据的 H 侧输入）。
