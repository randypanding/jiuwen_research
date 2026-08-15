# 方向三：Agent Swarm / Spec 驱动 / 团队共享记忆（审查后精选版）

> 研究子问题：Agent Swarm 整体架构、Spec 驱动开发、团队共享记忆，以及"由判别方/协调者裁定经验写入"的机制。
> 审查时间：2026-08-15。筛选标准：**三个月内（≥2026-05-15）新增/活跃 或 有重大意义**。所有条目均已核验为真实存在（无幻觉编号）。

## A. 近三个月内核心新作 / 活跃项目（RECENT，≥2026-05-15）

| # | 标题 | 类型 | 来源 | 时间 | 与本子问题相关性 |
|---|------|------|------|------|------------------|
| A1 | Governed Shared Memory for Multi-Agent LLM Systems（MemClaw / ArgusFleet） | 论文 | arXiv:2606.24535 | 2026-06 | 直接对应"治理型共享记忆"：定义泄漏/过期传播/矛盾持久化/溯源崩溃四类失败，用策略化传播裁定写入 |
| A2 | Beyond Self-Talk: A Communication-Centric Survey of LLM-Based Multi-Agent Systems | 论文/综述 | arXiv:2502.14321（v3 2026-05-26） | 2026-05 更新 | 从通信视角分析 Agent 协调/协议，为"判别方如何裁定"提供分类框架 |
| A3 | GATEMEM: Benchmarking Memory Governance in Multi-Principal Shared-Memory Agents | 论文(基准) | arXiv:2606.18829 | 2026-06 | 多主体共享记忆治理基准，联合评测访问控制、主动遗忘与长程效用，直接命中"判别方裁定+共享记忆"评估缺口 |
| A4 | GitHub Spec Kit（Specify CLI / spec-kit） | 开源项目 | github.com/github/spec-kit | 最近 commit 2026-05-27，~1006 commits | 官方 SDD 工具链，用规格驱动 Agent 开发，支持 Claude Code/Copilot/Gemini 等多 Agent，活跃维护 |
| A5 | LangGraph | 开源项目 | github.com/langchain-ai/langgraph | 最近 commit 2026-08-09，7039 commits | 图驱动的多 Agent 状态化编排+持久记忆，极高活跃度，支撑实现层 |

## B. 奠基 / 重大意义（SIGNIFICANT）

| # | 标题 | 类型 | 来源 | 时间 | 与本子问题相关性 |
|---|------|------|------|------|------------------|
| B1 | AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation | 论文 | arXiv:2308.08155（Microsoft） | 2023 | 多 Agent 对话协作基石，可构"开发+资深 Reviewer"评审模式（活跃维护） |
| B2 | MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework | 论文 | arXiv:2308.00352 | 2023 | SOP/角色分工流水线让 Agent 互验中间结果，贴近"判定方裁定"（活跃维护） |
| B3 | ChatDev: Communicative Agents for Software Development | 论文 | ACL 2024, arXiv:2307.07924 | 2023 | 虚拟软件公司角色协作，含 communicative dehallucination 校验 |
| B4 | Open Agent Specification (Agent Spec): A Unified Representation for AI Agents | 论文 | arXiv:2510.04173 | 2025 | 平台无关的 Agent 配置语言标准，为规格化 Agent 描述提供规范基础 |
| B5 | INMS: Memory Sharing for LLM-based Agents | 论文 | arXiv:2404.09982（v3 2026-03） | 2024 | 共享对话式记忆池奠基工作，2026 仍修订维护，支撑团队经验沉淀 |

## C. 相关背景（非近期但主题契合，供谱系参考）

| # | 标题 | 类型 | 来源 | 时间 | 与本子问题相关性 |
|---|------|------|------|------|------------------|
| C1 | Collaborative Memory: Multi-User Memory Sharing with Dynamic Access Control | 论文 | arXiv:2505.18279 | 2025 | 私有/共享双层记忆+溯源权限校验，"团队共享记忆+写入治理"模型 |
| C2 | RUMAD: Reinforcement-Unifying Multi-Agent Debate | 论文 | arXiv:2602.23864 | 2026-02 | 将多智能体辩论/协调建模为 RL，动态裁定通信轮次，与"协调者裁定/共识"相关 |
| C3 | AI agents coordinate via majority-following beyond human scale | 论文 | Science Advances, doi:10.1126/sciadv.aea6091 | — | 从复杂系统角度研究多数跟随与共识临界规模，为"裁定/共识"提供理论视角 |

## D. 开源项目（判别方 / 协调者 / 共识裁定）

| # | 名称 | 类型 | 来源 | 与本子问题相关性 |
|---|------|------|------|------------------|
| D1 | Multi-Agent Council Review | 开源项目 | github.com/dustdustpy/multi-agent-council | 多 Agent 独立评审后"理事会投票共识"，仅公布达成共识的建议——判别方裁定典型实现（活跃度建议复核） |
| D2 | Conclave | 开源项目 | github.com/signalnine/conclave | Claude/Gemini/Codex 多评审共识，按"全一致→高优先级→多数→单一"分组，关键问题阻断，即经验写入的共识门槛（活跃度建议复核） |
| D3 | guilde-lite Multi-Agent Consensus Patterns | 开源项目(文档) | github.com/pagerguild/guilde-lite | 落地多 Agent 共识判定模式（2/3 多数通过、置信度计算），与"协调者裁定写入"方法论直接对应 |
| D4 | Awesome Agent Swarm | 开源项目(资源清单) | github.com/evomap/awesome-agent-swarm | 聚合 swarm 框架、智能、治理、评审 Benchmark 的分类清单，便于检索后续素材 |
| D5 | Governed Collaborative Memory as Artificial Selection（Viewpoint） | 开源/观点 | Snseam/awesome-agent-memory 收录 | 将记忆治理视为"选择机制"，裁定哪些记忆入库/拒绝/弃权/取代，与"经验写入机制"直接对应 |

## 审查记录（本版删除或调整的条目）

- 删除（非近期、非奠基、单版弱维护）：LLMs Working in Harmony Survey(2504.01963)、SIER(2505.17115)、SwarmSys(2510.10047)、MIRIX(2507.07957，偏个人多模态记忆离题)。
- 降级到背景：Collaborative Memory(2505.18279)、RUMAD(2602.23864，2026-02 略早于窗口)。
- 说明：D 组社区开源项目（Multi-Agent Council、Conclave 等）活跃度建议在 GitHub 复核；本版审查核验了论文与 spec-kit/langgraph 的 commit 时间，未逐一对其余仓库做确认。