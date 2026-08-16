# 02 · 契约目录（C01–C13）

> 权威定义 = `swarmfoundry/src/swarmfoundry/schema/` 代码（D-07）。本文只描述每个契约的**用途、生产方、消费方、通信测试义务**。任何实现先跑通 `tests/contracts/` 对应测试再谈功能。

| 契约 | 名称 | 权威定义 | 生产方 | 消费方 | 传输方法（C10 method / 文件） | 通信测试 |
|---|---|---|---|---|---|---|
| C01 | SpecDomain（L1/L2/L3 条款 + 见证绑定 + dontcare） | schema/spec.py | spec steward/moderator（经人类 L1/L2 批准） | 全员只读；门禁 H7；coverage 统计 | 文件 `spec/domains/<d>/spec.json` | test_schema_roundtrip::test_c01_*；test_specrepo.py 全文件 |
| C02 | RRegistry（制品 R 级登记） | schema/spec.py | architect 提案 + 人类批准 | leader（fan-out 决策）、H4/H5 | 文件 `spec/registry/artifacts.json` | test_c02_*（R3 必须 golden_ref 等） |
| C03 | GateResult / AdmissionDecision（门禁代数） | schema/gates.py | verifier | leader、receipt、人类报告面 | gate.result / admission.decision | test_gates_algebra.py（7 例）；test_wave_communication happy path |
| C04 | EvidenceReceipt（证据收据） | schema/receipt.py | leader（登记） | 人类审计、H10 合并检查、deep agent | receipt.registered + `receipts/*.json` | test_c04_receipt_roundtrip；happy path 收据登记步 |
| C05 | ContractSurface / SurfaceDiff（契约面） | schema/surface.py + contracts/* | architect（冻结基线）、H4（现提取） | H4、refactor、波次冻结 | 文件 `waves/freeze/<wave>/*.surface.json` | test_surface.py（5 例 breaking 分类） |
| C06 | ScenarioSuite（holdout 场景） | schema/oracle.py | architect/critic（B 线） | verifier（H3）、差分引擎（H5） | 文件 `holdout/<domain>/*/suite.json` | test_oracle.py（含 manifest fail-closed） |
| C07 | DiffReport（实例间差分） | schema/diff.py | verifier（H5） | spec moderator（沉默裁决） | gate.result details + measurement.event | test_diff_engine.py（3 例） |
| C08 | JudgeVerdict / PanelDecision | schema/judge.py | judge 面板（verifier 步骤） | S 门禁聚合 | judge.verdict（内部步骤） | test_judge_panel.py（6 例） |
| C09 | WavePlan / WaveTask | schema/wave.py | architect | leader（SwarmFlow run_wave） | 文件 `waves/plans/<wave>.json` + task.assign | test_c09_*（环检测/依赖/fanout 上限） |
| C10 | SwarmEnvelope（消息信封 + method 闭集 + 信息不对称） | schema/envelope.py + comm/bus.py | 全员 | 全员 | 生产绑定：agent-core TeamRuntime send/publish（MessageEnvelope，agent-core/openjiuwen/core/multi_agent/team_runtime/envelope.py:L13-L48）与 jiuwenswarm E2AEnvelope（jiuwenswarm/common/e2a/models.py:L87-L160） | test_envelope_protocol.py（5 例）+ test_wave_communication.py（5 例，含越权/泄漏/路由失败） |
| C11 | MeasurementEvent（spec 熵仪器读数） | schema/events.py | leader（N-fan-out 后） | spec moderator | measurement.event | test_c11_* + test_wave_communication::divergence |
| C12 | HealthMetrics / Thresholds / 降级判定 | schema/metrics.py | 观测聚合（WP13） | 人类、deep agent | health.metrics + 报告面 | test_events_metrics.py |
| C13 | RuleProposal（演进提案通道） | schema/proposal.py | deep agent/任何角色 | 人类批准 → 下一 session | rule.proposal + `proposals/*.json` | test_c13_*（生效会话语义） |

## 契约变更流程（对契约本身的变更）

1. 提案方提交 spec-delta（修改 schema 代码 + 对应测试 + 本文档条目）；
2. `schema_version` 单调递增；旧版本兼容窗口 = 一个完整波次（双版本并行解析）；
3. H4 对 schema 包自身生效：`swarmfoundry.schema` 的公开 API 面即契约面，破坏性变更需人类 L2 批准（waiver 机制 D-12）。

## 生产绑定对照表（swarmfoundry 参考实现 → openJiuwen 生产件）

| swarmfoundry 参考件 | 生产绑定 | 绑定说明 |
|---|---|---|
| comm/bus.py SwarmBus | agent-core TeamRuntime.send/publish + TeamTaskManager | SwarmBus.send(recipient_role) → TeamRuntime.send(MessageEnvelope)；订阅 → register_direct_message_handler（Messager ABC，agent-core/openjiuwen/agent_teams/messager/messager.py:L20-L97） |
| SwarmEnvelope | E2AEnvelope（WS 线格式） | method→ReqMethod 映射；payload 原样置 E2AEnvelope.params（jiuwenswarm/common/e2a/models.py:L87-L160） |
| GateRunner | SwarmFlow verifier 工作流步骤 | workflow 脚本内 `from swarmfoundry.gates.runner import GateRunner`（同进程） |
| 沙箱执行（H1/H2/H3/H5 producer） | jiuwenbox REST exec | 每个 producer 命令 → `POST /api/v1/sandboxes/{id}/exec`；policy 按角色（D-04） |
| 证据登记 | git hook + receipts/ | world 仓 pre-merge 检查 receipt 存在且 admitted（WP4） |
| 模型家族校验 | IntelliRouter deployments 元数据 | deployments 需声明 family 字段；judge 步骤读取（WP6） |

## 契约通信测试矩阵（全部已实现并绿色）

| 测试文件 | 覆盖 |
|---|---|
| tests/unit/test_schema_roundtrip.py | C01–C13 全部 schema 的序列化往返 + 非法输入拒绝 + schema_version 不匹配拒绝 |
| tests/unit/test_gates_algebra.py | C03 代数语义：合取、单调否决、缺门 fail-closed、error 非 pass |
| tests/unit/test_judge_panel.py | C08 聚合：否决、弃权、自评无效化、重复判官、不足额 fail-closed |
| tests/unit/test_envelope_protocol.py | C10 信息不对称策略五场景 |
| tests/contracts/test_wave_communication.py | 端到端消息链：task.assign→instances_ready→verify.request→gate.result→admission.decision→receipt.registered；correlation 一致性；method 序列断言；builder 越权发判词被拒；holdout 泄漏被拒；无路由 loud-fail |
| tests/e2e/test_admission_pipeline.py | CLI 全链路（gates-run 拒绝路径 + 收据 + spec-validate/seal + surface 提取/diff） |
