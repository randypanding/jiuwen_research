# 04 · 门禁与 Oracle 运行规范

> 门禁代数：`Admit(instance) = H1∧H2∧H3∧H4∧H5∧H6∧H7∧H8 ∧ S`（fail-closed，无短路，全跑全记录）。
> 参考实现：`swarmfoundry/gates/`（全部已测）。本文规定**生产运行**时的配置与操作规程。

## 1. 门禁总表（生产配置）

| 门 | 实现 | 执行环境 | 输入 | 失败语义 | 配置键 |
|---|---|---|---|---|---|
| H1 构建/类型/静态 | h1_build.py | jiuwenbox（builder 同型 policy） | 域工具链命令表 | 任一命令非零 | gates.H1.commands/timeout_s |
| H2 单元/属性测试 | h2_unit.py | jiuwenbox | 域测试命令 + min_effective_assertions | 非零或有效断言不足 | gates.H2.commands/min_effective_assertions |
| H3 holdout 套件 | h3_holdout.py | jiuwenbox（verifier policy：禁出站） | ctx.holdout_dirs（全部域套件） | 任一场景失败或 holdout 泄漏 | 域→套件映射由 architect 维护 |
| H4 契约面兼容 | h4_contract.py | verifier 进程 | waves/freeze/<wave>/*.surface.json | breaking 且无豁免 | gates.H4.waiver.human_approval_ref |
| H5 差分/黄金 | h5_diff.py | jiuwenbox（producer）+ verifier 进程（比对） | sibling_instances + diff_suite + golden_checks | 未登记分歧或黄金不符 | gates.H5.dontcare_paths（须与 spec 一致，WP5 校验） |
| H6 宪法护栏 | h6_guard.py | verifier 进程 | 默认规则 + 域扩展 | 命中禁止模式/依赖/大小 | gates.H6.forbidden_patterns/forbidden_imports/max_file_kb |
| H7 漂移 | h7_drift.py | verifier 进程 | spec 仓 seals + 实例 trace 锚点 | seal 漂移或锚点缺失 | gates.H7.require_trace_tags |
| H8 成本预算 | h8_cost.py | verifier 进程 | ctx.costs 累计 | 超 tokens/spend 上限 | gates.H8.max_total_tokens/max_spend_units |
| S judge 面板 | judge.py | verifier 工作流步骤 | 匿名化交付物摘要 + rubric + JudgeVerdict 列表 | 否决/不足额/自评 | gates.S.min_valid_verdicts |

**操作规程**：门禁顺序固定 H1→H8→S；结果一律写入 GateResult 证据数组；verifier 工作流 journal 保留全量；任何门禁 error（异常）= 该门失败（base.py safe_run 语义），不得吞异常。

## 2. Oracle 编写规程（场景作者 = architect/critic）

场景套件目录结构（C06）：

```
holdout/<domain>/<feature>/
  suite.json          # 必含 env_manifest: {PYTHONHASHSEED, TZ, SEED}
  inputs/*.json       # 每个场景一个输入文件
  golden/*.golden + *.r3info   # 仅 R3 相关场景
  property/*.py       # property_script 判据脚本（stdin=实例 stdout）
```

**五条铁律**（源自 oracle 研究与 r3 研究）：
1. **先失败后固化**：新场景先在"已知错误实现"上确认 FAIL，再入 holdout（FAIL_TO_PASS 标注写在 suite.json description）；
2. **断言有效性**：json_assert 必须断言行为字段；禁止"只断言进程退出"充数；
3. **manifest 完备**：缺 PYTHONHASHSEED/TZ/SEED 的套件直接 fail-closed（runner 已强制）；
4. **oracle 常量独立**：期望值不得从被测实现运行结果反推（防循环论证）；来自 RFC/规范/参考实现的常量注明来源于 description；
5. **轮换**：rotation_id 每 90 天递增；退役场景进 `retired/` 不删除。

**判据类型选择顺序**（差分测试研究 §行为等价判据 + r3 研究 §6.5）：
独立参考实现 > 历史/生产实现回放 > 往返关系（property_script）> 属性 > 黄金文件。黄金只作回归护栏，必须与至少一条其他轨道并用（R3 双轨）。

## 3. 差分与黄金运行细节

- **差分输入集**：默认复用 holdout 套件的 inputs（同一份输入双用：H3 验对 spec，H5 验实例间一致）；域可另供 `diff_suite`（仅输入，不判对错）。
- **规范化**：JSON 输出按路径树比对；非 JSON 按 strip 文本比对；浮点严格相等（差异即信号，是否容忍由 spec moderator 以 dontcare 裁决，不私设 epsilon）。
- **黄金比对**：redaction 正则清单在 `.r3info`；比对前双方同规约化；更新黄金必须 `update_golden(..., human_approval, approver)`（无批准即异常，已测）。
- **SPRT 统计层（M2 引入）**：对 flaky 嫌疑场景用三值判定；INCONCLUSIVE 永不默认通过；预算耗尽转人工（r3 研究 §5.4，WP14 实现）。

## 4. judge（S 门禁）工作流规范

执行序列（verifier 工作流内，确定性）：

1. 装载 rubric（architect 持有，版本冻结于波次）；
2. 构造匿名化评审包：交付物摘要 + 关键接口 + 证据引用列表；**去除**：实例 id、builder 身份、时间戳、路径；
3. 并发调用 ≥min_valid+1 名 judge（TIER-H，家族校验通过）；三值判词 + 证据引用必填；
4. 聚合（aggregate_panel）：否决即否决；自评无效化；弃权记录；不足额 fail-closed；
5. 判词全部入 receipt（S GateResult.details）供校准取材。

**校准义务**：每域维护 50–100 条人工判例（gold.jsonl）；模型/rubric/模板任一变更触发 kappa 回归；kappa<0.6 → S 门禁停用（不影响硬门禁）+ 该域暂停自动准入（D-27/structure.md §13.2）。

## 5. 域工具链配置样例（D1 skill_review）

```toml
# gates.skill_review.toml
[gates.H1]
commands = [["python3", "-m", "compileall", "-q", "."]]
timeout_s = 300

[gates.H2]
commands = [["python3", "-m", "pytest", "tests", "-q"]]
min_effective_assertions = 40

[gates.H5]
dontcare_paths = []   # 初始无自由度

[gates.H6]
max_file_kb = 4096

[gates.H8]
max_total_tokens = 2000000
max_spend_units = 50.0

[gates.S]
min_valid_verdicts = 2
```

## 6. 门禁自身的可信性保障（oracle 的 oracle）

1. `ci/run_gates.sh` 本身是 R3 制品：修改需人类批准 + 黄金输出比对（脚本的 stdout 黄金快照）；
2. swarmfoundry 的每个门禁都有"注入失败必被捕获"的负向测试（现状：H2 负向在 test_oracle/test_wave_communication，H3 泄漏、H4 breaking、H5 分歧、H6 模式、H7 seal/锚点、H8 超支、S 否决/自评——全部已覆盖）；
3. 每季度演练：向流水线注入一个"看似通过实则带后门"的实例（红队 fixture），验证至少一个门禁拦截（WP14 drills）。
