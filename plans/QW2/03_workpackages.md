# 03 · 工作包分解（WP0–WP14）

> 每个 WP = 一个实施团队的完整任务书。执行 agent 只读本 WP + 00/02 文档 + 所引用的 swarmfoundry 代码即可开工。
> 依赖列中"→"表示先后关系；无依赖的 WP 可并行。所有 WP 的公共 DoD：`bash ci/run_gates.sh` 全绿 + 本 WP 通信测试绿。

---

## WP0 物理层基线（已完成 ✅，本文档仓库 `swarmfoundry/`）

交付物即现状：schema C01–C13、specrepo、contracts、oracle、gates、comm、cli、selftest、66 测试。后续 WP 只允许**追加**测试与经批准的契约演进（02 文档变更流程）。

---

## WP1 试点域 spec 收割（M0）

- **使命**：对 D1=`skillhub/marketplace/skill_review` 完成 spec 收割，产出合格的 spec 仓初始态。
- **输入**：CAPABILITY_MAP §SkillHub；skillhub 源码与其既有测试；structure.md §12 M0 定义。
- **交付**：
  1. `spec/constitution.md`（宪法初稿：structure.md §14 十五不变量 + 本仓安全条款）；
  2. `spec/domains/skill_review/spec.json`（C01）：L1 意图、L2 条款（覆盖：打包规范校验、checksum、版本规范、4 确定性引擎行为、语义引擎组合规则、聚合裁决）每条绑定机械见证；L3 实现说明由收割生成；
  3. `spec/registry/artifacts.json`（C02）：skill_review 各模块 R 级（validation=R2，engines/rule 模式库=R1，语义引擎 prompt=R0 等，由 architect 初审）；
  4. 初始 seal（`swarmfoundry spec-seal --repo spec/`）；
  5. 收割报告 `spec/domains/skill_review/harvest_report.md`：每条 L2 条款 ← 源码证据（file:line）映射（RTM 硬轨：条款带稳定 ID，代码侧以 `# spec-clause:<ID>` 注释回填——仅注释，不改逻辑）。
- **实施位置**：本仓 `spec/` 目录；代码注释回填仅限 skillhub 仓（PR 形式，人类 L2 批准）。
- **DoD**：`swarmfoundry spec-validate --repo spec/` 零问题；witness_coverage(skill_review) ≥ 0.9；seal 文件存在；H7 在回填后的 skill_review 上跑通（trace tag 全覆盖）。
- **禁区**：不得修改 skillhub 任何行为代码；不得写 unverifiable 条款充数（coverage 工具会暴露）。
- **依赖**：无（最先开工）。

## WP2 构建/测试门禁生产化（H1/H2 进 jiuwenbox）

- **使命**：把 H1/H2 的命令执行从本地 subprocess 升级为 jiuwenbox 沙箱执行，并支持域工具链配置。
- **输入**：C03；swarmfoundry/gates/h1_build.py、h2_unit.py；jiuwenbox REST API（jiuwenswarm/jiuwenbox/docs/jiuwenbox_server_api.md）。
- **交付**：`swarmfoundry/gates/sandbox_exec.py`：`SandboxExecutor` 抽象（本地 subprocess 与 jiuwenbox 两实现，配置选择）；H1/H2 改经 executor；域工具链配置样例（python：compileall+pytest；java：mvn -q test；ts：pnpm build+vitest）；新增测试 ≥12 条（含沙箱超时/非零退出/输出截断）。
- **DoD**：全部既有测试绿 + 新测试绿；selftest 在两种 executor 下均通过。
- **禁区**：不得让门禁结果依赖沙箱品牌（结果必须只由退出码与输出决定）。
- **依赖**：无。

## WP3 holdout 库与 H3 生产化

- **使命**：建立 holdout 独立仓、沙箱策略编排（builder deny / verifier 只读）、轮换机制与泄漏扫描生产化。
- **输入**：C06；D-05/D-13/D-22；jiuwenbox policies API（policy.py:L445-L694）。
- **交付**：
  1. holdout 仓骨架（`holdout/README` 仅面向 architect/verifier；含 D1 域首个 suite：从 skillhub 既有测试中迁移/改写 ≥20 个场景，FAIL_TO_PASS/PASS_TO_PASS 标注）；
  2. `ops/holdout_policy.py`：编排 jiuwenbox policy——builder 沙箱 `files.deny` 注入 holdout/rubrics 路径，verifier 沙箱只读挂载；
  3. 轮换工具：`ops/rotate_holdout.py`（更新 rotation_id，退役 >3 个月场景）；
  4. H3 泄漏扫描与 holdout 目录清单的一致性测试。
- **DoD**：模拟"builder 实例文本含 holdout id"必被 H3 拒绝（已有单测，补生产路径 e2e）；轮换后旧 rotation 引用全部失效；verifier 能读、builder 不能读（沙箱策略断言测试）。
- **禁区**：holdout 内容不得出现在任何 builder 可见目录/镜像/日志；轮换不得删除退役场景文件（移入 `retired/`，防历史收据失联）。
- **依赖**：→ WP1（需要域条款以绑定场景）。

## WP4 世界库集成与准入原子性

- **使命**：实现"准入 = 原子提交 + 证据收据"的世界侧机制。
- **输入**：C04；structure.md §9 PR 重定义；D-10。
- **交付**：
  1. `ops/admit.py`：准入事务脚本——校验 receipt（admitted==true 且 content_hash 匹配）→ 在 world 仓创建 `admit/<receipt_id>` 分支 → squash 合并实例 diff → 附 receipt 引用提交 → 可回滚（revert 单 commit）；
  2. world 仓 pre-merge hook：无 receipt 不合并；
  3. 回滚演练脚本 `ops/rollback_drill.sh`（准入→回滚→世界状态 byte 级一致断言）；
  4. R2/R3 人类批准卡点：admit.py 检测 r_level∈{R2,R3} 时要求 `--human-approval-ref`。
- **DoD**：回滚演练字节级一致；伪造/过期 receipt 被拒（测试 ≥8 条）；R2 无批准被拒。
- **禁区**：不得实现"部分准入"（原子性不可破）；hook 不得调用任何 LLM。
- **依赖**：无（可与 WP1–3 并行，用 mock receipt）。

## WP5 漂移守护（reconciler 生产化）

- **使命**：H7 从门禁内检查扩展为常驻守护：seal 通道管控 + trace 锚点巡检 + 漂移事件上报。
- **输入**：C01/C11；D-17；spec-traceability-bi-sync-research 三层漏斗①②。
- **交付**：
  1. `ops/reconcile.py`：定时任务（cron 或 jiuwenswarm schedule.*），对 spec 仓 + 全部世界域跑 H7DriftGate，产漂移报告 JSON（复用 GateResult 形态）；
  2. re-seal 受控通道：仅当存在已批准的 spec-delta PR 时允许 `spec-seal`，否则拒绝并告警（包装 swarmfoundry.specrepo.seal.reseal）；
  3. dontcare 一致性校验：H5 config 的 dontcare_paths 必须与 spec DontCareEntry 一一映射，不一致 = 漂移；
  4. 漂移 → measurement.event 上报 T-NORM 的通信测试。
- **DoD**：篡改条款/删除锚点/私改 dontcare 三类注入均被检出（测试）；误报率自查：纯注释润色不触发（seal 归一化已保证，补测试）。
- **禁区**：reconciler 不得自行改 spec 或 code（只上报与阻断）。
- **依赖**：→ WP1。

## WP6 judge 工作流与校准（S 门禁生产化）

- **使命**：judge 面板的生产化：模型家族校验、匿名化、rubric 装载、校准集与 kappa 门槛。
- **输入**：C08；D-16/D-19/D-24；llm-as-judge-research 全部最佳实践。
- **交付**：
  1. `swarmfoundry/gates/judge_config.py`：JudgePanelConfig（模型列表含 family 字段、min_valid、rubric_ref），校验器实现"三查"（不同模型/非蒸馏/不同家族，至少一名跨厂商）；
  2. `ops/judge_run.py`：判词采集协议——输入匿名化（去来源/路径/时间戳）、成对比较交换顺序双跑、输出结构化 JudgeVerdict；LLM 客户端走 IntelliRouter TIER-H 部署组；
  3. 校准集管线：`calibration/<domain>/gold.jsonl`（50–100 条人工判例）+ `ops/judge_calibration.py` 计算 Cohen kappa；kappa<0.6 → 产降级事件（C12 judge_kappa）；
  4. 测试：家族校验器单测、匿名化属性测试（源信息不出现在 judge 输入中）、kappa 计算与阈值行为。
- **DoD**：自评配置被拒（单测）；校准脚本在合成标注集上 kappa 计算正确（与手工计算对照）；judge 档位 < builder 档位的配置被拒。
- **禁区**：judge 不得看到 gate 结果后再判（防锚定）；判词格式不得扩展第四值。
- **依赖**：无（校准集内容依赖 WP1 域选择，可后置填充）。

## WP7 verifier 工作流（SwarmFlow）

- **使命**：把 GateRunner 装配为 SwarmFlow 确定性工作流，含 journal 续跑、沙箱执行与消息回传。
- **输入**：C03/C04/C10；D-03/D-04；agent-core workflow engine（runner.py:L113-L178，primitives.py:L413-L1032）。
- **交付**：
  1. `waves/verify_instance.py`：SwarmFlow 脚本（META + async run）：装载 GateContext → H1..H8（经 WP2 SandboxExecutor）→ judge 步骤（WP6 协议）→ admission.decision → receipt 登记请求；
  2. journal 断点续跑测试（kill -9 后 resume，结果幂等）；
  3. 与 leader 的通信联调（verify.request → gate.result → admission.decision，扩展 tests/contracts/ 用例到生产绑定层）；
  4. 成本累计：各步骤 token 记账汇入 CostRecord（H8 输入）。
- **DoD**：端到端在 staging 团队上完成一次真实准入（D1 域）；journal 续跑测试绿；工作流内无任何自主 agent 步骤（静态审查 + META 断言）。
- **禁区**：不得在工作流中加入 LLM 决策分支；不得跳过任何门禁（缺配置 = fail-closed 已由代数保证，但不得用空配置伪造通过）。
- **依赖**：→ WP2、WP6（可先以 mock 联调）。

## WP8 cartographer 检索服务

- **使命**：按 D-06 试点域建立多视图代码检索 MCP 服务与 agent-as-tool 接入；CI 失败定位协议。
- **输入**：code-search-agent-research 最终报告 §6；D-21；TaskTool（task_tool.py:L55-L211）。
- **交付**：
  1. 新仓 `codesearch-mcp`：BM25（sqlite FTS5）+ AST 符号图（复用 swarmfoundry.contracts.extract 的 AST 基建）+ 向量（可选，M1 后）三视图；MCP stdio/streamable-http 双传输；
  2. 返回契约实现：`{file, lines, why, min_dependency_closure, confidence}`，低置信返回候选集；
  3. jiuwenswarm 接入：`mcp.servers` 配置条目 + builder/leader 工具白名单；
  4. CI 失败定位模式：SHERLOC 式提示词与输出协议（定位+诊断 → 修复 agent），在 D1 域用 3 个历史失败案例回归；
  5. 缓存隔离断言：检索结果只出现在会话尾部（上下文审计测试）。
- **DoD**：D1 域 top-5 命中率 ≥70%（自建 20 条定位标注集）；builder 上下文前缀不因检索结果失效（前缀哈希稳定性测试）。
- **禁区**：不得让 cartographer 有准入权/写权限；索引文件不得入世界仓。
- **依赖**：→ WP1（需要目标域）。

## WP9 builder harness（临时团队 + 隔离）

- **使命**：builder 临时团队的完整 harness：TeamAgentSpec、rails、沙箱策略、提示词、隔离测试。
- **输入**：01_architecture §3.3/§4/§5；D-22/D-23；jiuwenswarm swarm assembly（assembly.py:L105-L207、config_specs.py:L828-L934）。
- **交付**：
  1. `harness/team_specs/builder_team.yaml`（TeamAgentSpec：lifecycle=temporary、rails 列表、工具白名单、模型档 TIER-M、memory 禁写）；
  2. builder system prompt 完整文案（按 01 §5 骨架）入 `prompts/builder.md`；
  3. 隔离验收套件 `tests/isolation/test_builder_isolation.py`（生产层）：a) 沙箱 files.deny 生效；b) 团队销毁后无记忆残留（session 目录清理断言）；c) builder 消息面无法发出判别类 method（bus 策略）；d) 上下文注入审计（无 holdout/rubric 字样）；
  4. fan-out 启动脚本（leader 侧调用 build_team/spawn_teammate 的参数模板）。
- **DoD**：隔离验收 4 项全绿；一次真实 N=3 fan-out 在 D2（greenfield）产出 3 个可跑实例。
- **禁区**：builder 不得挂载 memory/evolution/team 管理类 rail 或工具。
- **依赖**：→ WP3（沙箱策略）、WP10（leader 唤起）。

## WP10 leader harness 与波次编排

- **使命**：leader 的波次推进自动化：run_wave SwarmFlow、N 自适应、测量分类与补足、实例选择与收据登记。
- **输入**：C09/C11；D-20；structure.md §6 判别表；events.classify_measurement（已实现）。
- **交付**：
  1. `waves/run_wave.py`：SwarmFlow 脚本——读 WavePlan → ready_tasks → fan-out（WP9）→ instances_ready → verify（WP7）→ 测量分类 → 不足 N 补足（<3 且有失败）→ 沉默/分歧升级 T-NORM（measurement.event）→ 闭合实例选择（次要判据：成本→确定性→代码量，记录于 receipt.notes）→ admit（WP4）；
  2. N 自适应实现（D-20 U 值规则版，输入来自 receipts 历史聚合）；
  3. 波次预算监控（WavePlan.budget_units 超支 → 停波次 + 上报）；
  4. 通信联调：扩展 tests/contracts/ 覆盖 run_wave 全消息序列（以 mock builder/verifier）。
- **DoD**：mock 全链路透传测试绿；D2 域一次真实波次（≥2 task，含一次 N=3 补足路径）完成；预算熔断测试绿。
- **禁区**：leader 不得修改判据/选择标准于会话内（标准只能来自配置与规则提案）。
- **依赖**：→ WP4、WP7、WP9。

## WP11 T-NORM 工作流（moderator/steward/reconciler）

- **使命**：规范委员会的持久团队与其三个角色的工作流。
- **输入**：01_architecture §3.5；C11/C13；agent-core SharedMemoryManager（manager.py:L335 leader-only 写）。
- **交付**：
  1. T-NORM TeamAgentSpec（`harness/team_specs/norm_team.yaml`）与三角色 prompts；
  2. moderator 工作流：measurement.event 消费 → 裁决（dontcare 登记/spec-delta 起草/团队记忆写入裁定）；所有写动作产 PR（不直接提交）；
  3. steward 工作流：条款一致性巡检（重复 ID、孤儿见证、version 单调）+ re-seal 通道执行；
  4. reconciler 集成 WP5 ops；
  5. 裁决审计：每次裁决落 `decisions/<event_id>.json`（含依据引用），供人类抽查与 judge 校准取材。
- **DoD**：注入"沉默/分歧/档位不足/冲突"四类测量事件，各走通正确分支（通信测试）；裁决审计完整可回放。
- **禁区**：T-NORM 不得触代码实现；不得在会话内改变裁决标准。
- **依赖**：→ WP1、WP5。

## WP12 标定流水线（B 线）

- **使命**：独立标定团队：全部丢弃代码的测量波次 + critic 红队 + oracle 补强闭环。
- **输入**：structure.md §7；信息不对称研究（critic 可见实例但产出隔离）。
- **交付**：
  1. T-CAL TeamAgentSpec 与标定 leader 的 run_calibration.py（与 run_wave 同构但目标函数 = 发现沉默/分歧，成功定义 = 产出 measurement/spec-delta/oracle 补强，代码全丢弃）；
  2. critic 工作流：攻击面枚举 → 新场景草案（C06 格式）→ holdout 库 PR；
  3. 标定报告模板（spec 熵变化、新 dontcare、新条款）；
  4. B 线与 A 线记忆域隔离断言（不同 team_name、TEAM_MEMORY 不互通）。
- **DoD**：对 D1 域执行一次标定波次，产出 ≥3 条有效发现（人类确认）；隔离断言绿。
- **禁区**：B 线实例不得进入世界（准入通道物理关闭：run_calibration 不调用 admit）。
- **依赖**：→ WP10（复用编排件）、WP11。

## WP13 观测与健康度

- **使命**：C12 指标采集、健康度评分、降级自动化与人类报告面。
- **输入**：schema/metrics.py（已实现判定）；structure.md §13；ObservabilityConfig（agent-core extensions/observability）。
- **交付**：
  1. `ops/metrics_collect.py`：从 receipts/decisions/journals 聚合七指标 → HealthMetrics JSON 时序；
  2. 降级执行器：evaluate_downgrades 触发 → 阶段回退动作（冻结 fan-out 配置、暂停 S 门禁等，机械清单化）+ 案例记录（C13 素材）；
  3. 人类报告面：周报生成（仅 L1/L2 相关 + 健康度 + 提案列表，不含代码 diff/实例选择）；
  4. judge 校准一致率与弃权率看板（接 WP6 校准输出）。
- **DoD**：注入越限指标，降级动作按 D-27 触发并有审计（测试）；周报字段白名单测试（不含禁字段）。
- **禁区**：报告面不得暴露 holdout 内容与 judge rubric。
- **依赖**：→ WP6、WP10。

## WP14 CI 总集成与迁移梯度闸门

- **使命**：把上述一切接入 CI，并实现 M0→M3 阶段闸门的机械化检查。
- **输入**：structure.md §12；ci/run_gates.sh（现有基线）。
- **交付**：
  1. `.github/workflows/` 扩展：world 仓各域的门禁 job（矩阵：域 × 门禁）；
  2. `ops/migration_gate.py`：阶段进阶条件检查器（M0→M1：holdout 覆盖率≥阈值 + H5 可用 + H7 上线；M1→M2：连续 k 波次零逃逸 + kappa≥0.6；M2→M3：稳定运行窗 + 提案通道演练通过），输出可被人类一键批准的报告；
  3. 撤退演练：任一降级触发 → 自动回退阶段配置 + 通告（与 WP13 联动）；
  4. 全链路演练手册 `ops/DRILLS.md`（准入/回滚/降级/轮换/校准五演练，每季度执行）。
- **DoD**：M0→M1 闸门在 D1 域真实通过一次；五演练脚本全绿。
- **禁区**：阶段闸门不得有"临时放行"参数。
- **依赖**：→ 全部前置 WP。

---

## 依赖图（关键路径加粗）

```
WP1 ─→ WP3 ─→ WP9 ─→ WP10 ─→ WP12 ─→ WP14
 │              ↑        ↑
 ├─→ WP5 ─→ WP11        │
 ├─→ WP8                │
WP2 ─────────────→ WP7 ─┘
WP6 ─────────────↗
WP4（独立并行）──→ WP10
WP13 ← WP6/WP10 ─→ WP14
```
