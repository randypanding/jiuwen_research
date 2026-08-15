# 策展清单 03：Oracle / CI-gate 相关开源项目与工具（核验后）

> 审查更新日期：2026-08-15。
> 收录标准：三个月内（2026-05-15 后）活跃更新，或即便非三个月内但代表该方向的事实标准/标杆。
> 星数为核验所得近似值（2026-08 检索）。`[活跃]` = 近 3 个月有更新；`[近期新增]` = 近 3 个月新增。

## 分组 B：Agent 验证 / 测试 / 评估框架（oracle 核心）

| 项目 | 仓库 | 星数(约) | 定位 | 相关性 | 许可证 | 状态 |
|---|---|---|---|---|---|---|
| SWE-bench / Verified | github.com/SWE-bench/SWE-bench | ~5k | 真实 issue 评测、hidden-test 即事实 oracle | 高（oracle 标杆） | Apache-2.0 | 稳定基准 |
| SWE-agent | github.com/SWE-agent/SWE-agent | ~19k | reference agent+评测器一体 | 高 | MIT | 活跃 |
| Inspect AI | github.com/UKGovernmentBEIS/inspect_ai | 数千 | 英国 AISI/I-X 官方评测框架 | 高 | MIT | [活跃] |
| DeepEval | github.com/confident-ai/deepeval | ~17.6k | pytest 风格 LLM/agent 评测，LLM-as-judge | 高 | Apache-2.0 | [活跃] |
| promptfoo | github.com/promptfoo/promptfoo | ~23k | LLM 评测+断言+CI 门禁，llm-as-judge | 高（oracle+CI 双满足） | MIT | [活跃] |
| Harbor (agent 评测) | github.com/harbor-framework/harbor | ~2k | 容器化 agent 评测框架，承载 Terminal-Bench 2.0 | 高 | MIT | 活跃 |
| agentevals | github.com/esara/agentevals | 较低 | 基于 OpenTelemetry 轨迹的 agent 行为评测 | 高 | 待核 | 活跃 |
| AgentOps | github.com/AgentOps-AI/agentops | ~5.4k | agent 追踪/回放/质量评测 | 中高 | MIT | [活跃] |
| Langfuse | github.com/langfuse/langfuse | ~25k | LLM/agent 可观测性+评测 | 中 | MIT | [活跃] |

## 分组 C：CI 门禁 / 质量门禁 / AI 代码评审（CI-gate 核心）

| 项目 | 仓库 | 星数(约) | 定位 | 相关性 | 许可证 | 状态 |
|---|---|---|---|---|---|---|
| PR-Agent (Qodo Merge) | github.com/qodo-ai/pr-agent | ~11k | 开源 AI PR 评审，可嵌入 CI 门禁 | 高 | Apache-2.0 | [活跃]（社区接管） |
| Trunk | github.com/trunk-io/trunk | 数千 | lint/格式化+merge queue+质量门禁 | 高 | MIT | [活跃] |
| Mergify | github.com/Mergifyio/mergify | 数千 | 规则驱动 merge queue，先测后合 | 高 | Apache-2.0 | [活跃] |
| Danger | github.com/danger/danger | ~5k | 把评审规则编码进 CI 的文件级门禁 | 中高（规则 oracle） | MIT | 稳定 |
| Sweep | github.com/sweepai/sweep | ~7k | AI junior dev 自动提 PR，验证在 CI 完成 | 中 | Apache-2.0 | 活跃 |
| GitHub Agentic Workflows | github.com/github/github-agentic-workflows | 新 | Actions 内 agent 化 CI 工作流，隔离/受限输出/审计 | 高（CI-gate 官方落地） | 见仓库 | [近期新增][活跃] |

## 分组 D：Oracle / Validator / LLM-as-Judge 实现 + agent 流程门禁（CI-gate 工具）

| 项目 | 仓库 | 星数(约) | 定位 | 相关性 | 许可证 | 状态 |
|---|---|---|---|---|---|---|
| pytest-semantix | github.com/labrat-akhona/pytest-semantix | 较低 | pytest 语义断言，验证 LLM 输出含义 | 高（pytest-based oracle） | MIT | [活跃] |
| semantic-test-action | github.com/labrat-akhona/semantic-test-action | — | 把 pytest-semantix 跑进 GitHub Action CI | 高（oracle+CI） | MIT | [近期新增] |
| nullius | github.com/TejasViswa/nullius | 较低 | claim_gate 阻止 agent 无证据宣称"测试通过/已修复" | 高（反幻觉验证门禁） | 待核 | [活跃] |
| right-hooks | github.com/ychua/right-hooks | 较低 | 物理钩子强制 Think→Plan→…→Ship 完整生命周期 | 高（CI 式流程 gate） | 待核 | [活跃] |
| spec-agent | github.com/MarcusViniciusBarcelos/spec-agent | 较低 | `verify` 作为 CI/PR 门禁，非零退出码阻断 | 高 | 待核 | 活跃 |
| specs | github.com/sweepai/specs | — | spec-driven 开发规范与 CLI | 中高（规格即 gate 源头） | 见仓库 | [活跃] |
| AgentEval | github.com/AgentEvalHQ/AgentEval | — | 工具调用时间线、随机评测、guardrails-as-code | 高 | 待核 | [活跃] |
| agenticevals | github.com/itseffi/agenticevals | — | 环境 rollout、任务轨迹、校验器 | 高 | 待核 | [活跃] |
| safe-agent | github.com/ArielSmoliar/safe-agent | — | 5 个 drop-in agent 安全技能（skill 校验/成本看门狗等） | 中高 | 待核 | [活跃] |
| agent-evals | github.com/thinkwright/agent-evals | — | agent 配置静态分析+越界行为现场测试 | 中高 | 待核 | [活跃] |
| AgentNeo | github.com/raga-ai-hub/AgentNeo | ~1k | agent 可观测性 | 中 | 待核 | [活跃] |

## 分组 A：开源 Coding Agent（验证对象，中相关；仅列代表）

OpenHands（github.com/OpenHands/OpenHands，~69k，MIT，活跃）、Aider（github.com/Aider-AI/aider，~48k，Apache-2.0，活跃）、Cline（github.com/cline/cline，~40-58k，Apache-2.0，活跃）、Gemini CLI（github.com/google-gemini/gemini-cli，~25k）、Qwen Code、OpenInterpreter（~50k，AGPL-3.0）。这些是 CI-gate/oracle 的"受检对象"。

## 审查说明（相对此前版本的重要修改）

- **Harbor 澄清**：主题相关的 agent 评测框架是 `harbor-framework/harbor`（承载 Terminal-Bench，MIT）；此前可能与 CNCF 容器仓库 `goharbor/harbor`（无关）混淆，已明确区分。
- **Roo Code**：多个来源称其团队 2026-04 宣布停止维护/关闭，近 3 月活跃度存疑，已从主表移除，需以仓库 archived 状态为准。
- **仓库归属修正**：SWE-bench 已迁至 SWE-bench 组织（Apache-2.0）；PR-Agent 现为 `qodo-ai/pr-agent`（约 11k 星，社区接管）；agentevals 为 `esara/agentevals`（非 langchain-ai）。
- **新增** GitHub Agentic Workflows（官方 agent 化 CI）、semantic-test-action、specs、AgentEval、agenticevals、safe-agent、agent-evals、AgentNeo 等近三个月新增/显著活跃项目。
- **候选歧义**：skillgate、agent-guardrails、CI-Copilot 等在 GitHub 存在多个同名仓库，本表以相关性最高的候选为准，未擅自指定唯一仓库，使用前请复核。
- **非开源对照**：CodeRabbit、Greptile 等为商业 SaaS，仅作参照。
- 星数/许可证中标注"待核"的为新项目或未二次确认项，使用时请以仓库当前信息为准。