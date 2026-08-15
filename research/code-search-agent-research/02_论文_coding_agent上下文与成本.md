# 论文搜集（二）：Coding Agent 上下文管理与成本优化（审查修订版）

> 方向：coding agent 架构、上下文工程（context engineering）、上下文压缩/剪枝/选择、token 成本优化、长上下文与 "Lost in the Middle"、agent 记忆与检索。
> 审查日期：2026-08-15。逐篇 WebFetch 核实 arXiv 页面。状态标记：🟢 近期高相关、🔵 奠基性/高影响力经典、🟡 窗口边缘/可选。【新增】= 本次审查补充。

## 一、近期高相关（2026-05 后提交/更新）🟢

| # | 论文标题 | 日期 | 链接 | 相关性（一句话） |
|---|---------|------|------|----------------|
| 1 | Less Context, Better Agents: Efficient Context Engineering for Long-Horizon Tool-Using LLM Agents | 2026-06 | https://arxiv.org/abs/2606.10209 | "最近工具调用+摘要"比全量历史省约 2.7 倍 token 且更可靠 |
| 2 | Token Reduction Is Not Cost Reduction: An Empirical Study of End-to-End Efficiency in API-Based Coding Agents | 2026-07 | https://arxiv.org/abs/2607.12161 | 反方证据：prompt-cache 占约 80% 账单，token 减少≠成本减少 |
| 3 | Retrieval-Augmented Code Generation: A Survey with Focus on Repository-Level Approaches | 2026-05-20 更新 | https://arxiv.org/abs/2510.04905 | 仓库级 RAG 代码生成综述（与文件一重复） |
| 4 | 【新增】SWE-Pruner Pro: The Coder LLM Already Knows What to Prune | 2026-07 | https://arxiv.org/abs/2607.18213 | 用 agent 内部表征直接剪枝工具输出，省 39% token、SWE-Bench Verified +3.8%（与文件一重复） |
| 5 | 【新增】ContextSniper: AntTrail's Token-Efficient Code Memory for Repository-Level Program Repair | 2026-07 | https://arxiv.org/abs/2607.01916 | 仓库级修复的 token 高效代码记忆，SWE-bench Lite 省 51.5% token、36.4% 成本 |
| 6 | 【新增】Self-GC: Self-Governing Context for Long-Horizon LLM Agents | 2026-07 | https://arxiv.org/abs/2607.00692 | 上下文对象生命周期治理（fold/mask/prune+可恢复 sidecar），剪 43.95% 前缀 token |
| 7 | 【新增】ACE: Pluggable Adaptive Context Elasticizer across Agents | 2026-06 | https://arxiv.org/abs/2606.31564 | 可逆上下文弹性编排（raw/abstract/drop 三态），适配 ReAct 等 4 框架 |
| 8 | 【新增】LLM Agents Are Latent Context Managers (VISTA) | 2026-06 | https://arxiv.org/abs/2606.30005 | 状态本体感知仪表盘，LOCA-Bench 上 Gemini-3-Flash 22.7%→50.7% |
| 9 | 【新增】The Devil Is in the Interface: Evaluating How Tool Architecture Shapes Coding Agent Behavior | 2026-08 | https://arxiv.org/abs/2608.11386 | 6 种工具架构对比（11700 条轨迹），CodeAct 接口省 56.3% token |
| 10 | 【新增】LLM Agents Can See Code Repositories | 2026-06 | https://arxiv.org/abs/2606.14061 | 仓库视觉结构图补充模态，输入 token 减 26%，ASE 2026 |
| 11 | 【新增】What to Keep, What to Forget: A Rate–Distortion View of Memory Compaction | 2026-07 | https://arxiv.org/abs/2607.08032 | 率失真视角统一 KV 缓存/提示/agent 记忆四层压缩 |
| 12 | 【新增】AgentMemBench: A Systematic Benchmark for Evaluating Long-Term Memory Management Strategies | 2026-06 | https://arxiv.org/abs/2608.00009 | 统一基准对比 5 种记忆管理策略 |

## 二、奠基性/高影响力经典 🔵

| # | 论文标题 | 年份 | 链接 | 相关性（一句话） |
|---|---------|------|------|----------------|
| 1 | SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering | 2024 (NeurIPS) | https://arxiv.org/abs/2405.15793 | ACI 奠基工作，定制化命令让 agent 自主导航仓库 |
| 2 | AutoCodeRover: Autonomous Program Improvement | 2024 (ISSTA) | https://arxiv.org/abs/2404.05427 | 搜索即省 token 的奠基工作（平均 $0.43 解决 issue） |
| 3 | OpenHands: An Open Platform for AI Software Developers as Generalist Agents | 2025 (ICLR) | https://arxiv.org/abs/2407.16741 | 通用 coding agent 平台，多 agent 协调参考 |
| 4 | A Survey of Context Engineering for Large Language Models | 2025 | https://arxiv.org/abs/2507.13334 | 上下文工程综述（1400+ 文献），理论框架 |
| 5 | LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models | 2023 (EMNLP) | https://arxiv.org/abs/2310.05736 | prompt 压缩经典基线，最高 20 倍压缩 |
| 6 | Lost in the Middle: How Language Models Use Long Contexts | 2023 (TACL) | https://arxiv.org/abs/2307.03172 | 长上下文位置效应经典，精简上下文的根本论据 |
| 7 | A Survey on the Memory Mechanism of LLM-based Agents | 2024 | https://arxiv.org/abs/2404.13501 | agent 记忆机制综述 |
| 8 | RepoCoder: Repository-Level Code Completion Through Iterative Retrieval and Generation | 2023 (EMNLP) | https://arxiv.org/abs/2303.12570 | 迭代检索-生成经典（与文件一重复） |

## 三、窗口边缘但直接相关（2026 上半年，建议保留）🟡

| # | 论文标题 | 日期 | 链接 | 相关性（一句话） |
|---|---------|------|------|----------------|
| 1 | Local-Splitter: A Measurement Study of Seven Tactics for Reducing Cloud LLM Token Usage on Coding-Agent Workloads | 2026-04 | https://arxiv.org/abs/2604.12301 | 实测 7 种降 token 策略省 45-79% 云端 token |
| 2 | SWE-Pruner: Self-Adaptive Context Pruning for Coding Agents | 2026-01 提交 / 05-07 更新 | https://arxiv.org/abs/2601.16746 | 自适应剪枝省 23-54% token（与文件一重复） |
| 3 | Context Pruning for Coding Agents via Multi-Rubric Latent Reasoning (LaMR) | 2026-05-14 | https://arxiv.org/abs/2605.15315 | 多准则剪枝省最多 31% token |
| 4 | CODESTRUCT: Structured Action Spaces for Efficient Coding Agents | 2026-04 | https://arxiv.org/abs/2604.05407 | 结构化动作空间省 12-38% token，ACL 2026 |

## 四、相关但窗口外（可选参考）🟡

| # | 论文标题 | 日期 | 链接 | 说明 |
|---|---------|------|------|------|
| 1 | CodeRAG: Finding Relevant and Necessary Knowledge for Retrieval-Augmented Repository-Level Code Completion | 2025 (EMNLP) | https://arxiv.org/abs/2509.16112 | 标题修正：实为 "Code Completion"（原文件误写 Code Generation） |
| 2 | GraphCodeAgent: Dual Graph-Guided LLM Agent for RAG Repo-Level Code Gen | 2025 | https://arxiv.org/abs/2504.10046 | 与文件一重复 |
| 3 | Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers | 2026-03 | https://arxiv.org/abs/2603.07670 | 标题修正：含副标题 |
| 4 | Evaluating Memory in LLM Agents via Incremental Multi-Turn Interactions | 2025-07 / 2026-03 更新 | https://arxiv.org/abs/2507.05257 | 标题修正：含副标题 |

## 五、方向信号说明（审查后更新）

- **信号最强**：上下文剪枝/压缩与上下文工程方向在 2026 年爆发（SWE-Pruner Pro、ContextSniper、Self-GC、ACE、VISTA、AgentMemBench 等），直接支撑"减少 token、保持上下文干净"。
- **出现反方/警示证据**：Token Reduction Is Not Cost Reduction（prompt-cache 占账单大头）、The Devil Is in the Interface（工具接口设计影响 token 效率）、Do Context Files Help Coding Agents（上下文文件无提升）——为"搜索 agent 设计"提供成本评估与边界警示。
- **信号相对弱**：学术界几乎没有以"专用独立代码搜索 agent"为明确研究对象的论文，现有工作多为"主 agent 内嵌搜索工具"或"检索层+主 agent"模式。
