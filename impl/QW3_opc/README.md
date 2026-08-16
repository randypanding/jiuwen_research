# opc/ — OPC Swarm 内核参考实现

PDR-001（见根目录 `structure.md`）范式的机械层参考实现：**门禁（H1–H8）、oracle（holdout 场景 + judge 工作流）、差分引擎（H5）、准入账本、契约间通信总线与信息不对称强制**。全部模块已实测（`tests/` 64 例，`ruff E9,F` 干净）。

## 快速开始

```bash
cd opc
uv venv --python 3.12
uv pip install -e '.[test]'
.venv/bin/python -m pytest tests -q          # 64 passed
.venv/bin/python -m opc.fixtures_gen          # 重新生成演示 fixtures（payments 域）
```

## CLI

| 命令 | 作用 |
|---|---|
| `opc-spec-lint --spec-dir spec` | spec 仓校验（schema/条款 ID/见证覆盖/R 级规则/L1 引用） |
| `opc-gate --gate H1..H8 --instance-dir … --spec-dir … --contract-id … [--holdout-dir --baseline-dir --corpus-file --golden-dir --policy-file]` | 单门运行，JSON 报告，pass=0 / 否则 1 |
| `opc-gate-runner … [--waivers-file …]` | 全门合取 + 软门禁，输出 AdmissionVerdict |
| `opc-oracle --holdout-dir … --instance-dir …` | holdout 场景执行 |
| `opc-diff --instance id=dir … --corpus-file … --entrypoint mod:fn [--redact path]… [--dont-care scope]…` | 实例间行为差分 |
| `opc-admit ledger-verify --ledger …` / `opc-admit package-workspace --spec-dir … --dest-dir … --holdout-dir …` | 账本体检 / builder 工作区净化打包 |

## 模块地图

- `schemas/` — 全部跨模块数据契约（pydantic，extra=forbid）：spec/gates/oracle/diff/evidence/wave/events
- `specrepo/lint.py` — spec 仓 lint（unverifiable 条款必须 advisory；R3 必须声明 frozen_outputs）
- `gates/` — H1–H8 + waivers + runner（`Admit = ∧H ∧ S`，三值判定，INCONCLUSIVE 不放行，waiver 带 owner/期限）
- `oracle/scenarios.py` — 场景执行器（executable/metamorphic，子进程隔离，redaction，canary 字段）
- `oracle/judge.py` — judge 工作流（k 采样、无证据丢弃、分裂弃权、换序一致性、模型关系三查、档位地板、RelayPackage 最小中继）
- `diff/engine.py` — 差分引擎（字段路径差分、don't-care 归域、min_instances 信息不足规则）
- `world/ledger.py` — 哈希链准入账本（append-only，篡改可检出）
- `world/bus.py` — 契约间消息总线（ROUTING_TABLE + builder 信息不对称强制 + 违规审计）
- `world/sanitizer.py` — builder 工作区净化（排除 oracle 目录、canary/本体扫描、bundle 哈希）
- `world/admission.py` — 波次事务（staging→admit→commit/abort；丢弃必须有测量结论）
- `metrics/` — 健康指标（闭合度/spec 熵/弃权率/漂移率/返工率/成本）
- `fixtures_gen.py` — payments 演示域生成器（inst-a 正解 / inst-b 等价变体 / inst-c 半上舍入分歧 / inst-evil 恶意）

## 测试地图

- `tests/unit/` — schema 语义、准入代数、账本防篡改（含 hypothesis 属性测试）、差分引擎规则
- `tests/contract/` — **契约间通信**：round-trip、路由合法性、builder 隔离、judge 契约、净化器、完整波次生命周期
- `tests/gate_semantics/` — 每门的通过/失败语义、runner 准入组合、waiver 生命周期、spec-lint 反例

## 扩展指南

- 新门禁：继承 `opc.gates.base.Gate`，注册进 `opc.gates.runner.ALL_GATES`，在 `tests/gate_semantics/` 加正反用例。
- 新场景类型：扩展 `ScenarioRunner.run` 分支 + schema `oracle_type` 枚举。
- 新 judge 后端：实现 `JudgeClient` 协议（`model_id` + `sample(context)`），工作流规则不可绕过。
- 契约变更：schemas 为 extra=forbid，字段增删必须同步 round-trip 测试与消费者（契约测试会红）。
