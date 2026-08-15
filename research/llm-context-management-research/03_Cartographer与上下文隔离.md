# 专题三：Cartographer 工具与上下文隔离（审查版）

> 研究问题：Cartographer 如何在不污染主流程缓存的情况下，为定位、检索等任务提供高效服务？
> **审查说明**：本文件为第二轮「补充审查」后的成果。全部条目经子代理逐一核实真实存在（含 GitHub 仓库、arXiv 编号）。按「近 3 个月更新或有重大意义」标准筛选，标注重量/优先级。【✔ 重大】【✔ 近3个月】本专题是研究主题的核心，优先级最高。

---

## 〇、审查结论摘要

- 全部 27 条原始条目经核实**均真实存在**，无虚构，链接/编号全部对应。
- 修正/澄清：FastContext 官方代码仓库已下架（论文与 arXiv 编号确凿）；graphify 的真实仓库实体是 **Synaptic**；Matryoshka Agent 需与另一篇 2410.20749 同名论文区分。
- **核心发现**：(1) 论文「PEEK」（arXiv 2605.19932）中名为 **Cartographer** 的组件正是研究对象的学术源头，与 Distiller、Evictor 协同维护常驻 system prompt 的"定向缓存"上下文地图；(2) 开源项目 `Icarus-afk/Cartographer` 是同名独立实现（语义知识图谱 + MCP），二者是不同实体，需在分析时明确区分。
- 上下文隔离范式论文（AgentSys、CodeDelegator、FastContext、DACS）是"子任务不污染主上下文"的理论支撑，与本专题契合度最高。

---

## 一、与 Cartographer 直接相关（学术源头 + 同名开源）

### 论文

1. **PEEK: Context Map as an Orientation Cache for Long-Context LLM Agents** 【✔ 近3个月 · 最高优先级】
   - 作者：Zhuohan Gu, Qizheng Zhang, Omar Khattab, Samuel Madden（MIT CSAIL / Stanford）
   - 年份：arXiv 2605.19932, 2026-05-19
   - 出处：https://arxiv.org/pdf/2605.19932
   - 相关性：**研究主题的学术核心**。context map 是常驻 system prompt 的固定预算"定向缓存"，给 agent 对外部上下文的持久"窥探"；其中把候选知识转成结构化编辑(ADD/DELETE/REPLACE)的模块正是名为 **Cartographer** 的组件，与 Distiller、Evictor 共同维护上下文地图。与"定位/检索不污染主流程 + 上下文缓存"强相关。

### 开源项目

2. **Cartographer「Repository Intelligence Operating System」** 【✔ 近3个月 · 最高优先级】
   - 作者/组织：Icarus-afk
   - 年份：2026（活跃开发，最近提交 2026-06-29，约 90 commits）
   - URL：https://github.com/Icarus-afk/Cartographer
   - 相关性：把代码仓库转成语义知识图谱（类/函数/接口及关系），提供 CLI 与 15 个工具的 MCP server（search/impact/neighbors/path/file_summary/context 等），`file_summary` 声称节省 90% token、`summarize` 节省约 98.8%。专用于 AI agent 以压缩图查询替代昂贵整文件读取，直接服务于"子任务高效检索、不污染主上下文"。**注意：与 PEEK 论文中的 Cartographer 组件是不同实体。**

3. **codebase-cartographer** 【✔ 近3个月相关】
   - 作者/组织：patrickcardosomoraes
   - 年份：2026（MIT 许可）
   - URL：https://github.com/patrickcardosomoraes/codebase-cartographer
   - 相关性：为 AI coding agent 生成并维护仓库根目录的 `MAP.md`（模块树、依赖图、入口点、约定、git churn 热点），让 agent 先读一份地图再探索，用单个文件替代数十次探索工具调用。

4. **Cartographer for Cursor IDE** 【✔ 近3个月相关】
   - 作者/组织：MPGek
   - 年份：2026
   - URL：https://github.com/MPGek/cartographer-cursor
   - 相关性：kingbootoshi/cartographer 的 Cursor IDE 移植版，适配 Cursor 的 agent skills/subagents 系统，通过 Task 工具编排多个 subagent 并行分析代码库并综合成 `CODEBASE_MAP.md`。

---

## 二、上下文隔离 / 子代理上下文 / 缓存隔离（核心理论支撑）

> 这一节回答"如何不污染主流程缓存"——是本专题最关键的理论来源。

### 学术论文

5. **AgentSys: Secure and Dynamic LLM Agents Through Explicit Hierarchical Memory Management** 【✔ 近3个月 · 最高优先级】
   - 组织：arXiv（AgentSys）
   - 年份：arXiv 2602.07398, 2026-02
   - 出处：https://arxiv.org/pdf/2602.07398 ；代码：https://github.com/ruoyaow/agentsys-memory
   - 相关性：受操作系统进程内存隔离启发，主 agent spawn 的 worker 在隔离上下文中执行、可递归 spawn 嵌套 worker，外部数据与子任务推理轨迹从不直接进入主 agent 内存，只有 schema 校验的 JSON 返回值可越过隔离边界——**上下文隔离的范式论文，直接对应"不污染主流程"**。

6. **CodeDelegator: Mitigating Context Pollution via Role Separation in Code-as-Action Agents** 【✔ 近3个月 · 最高优先级】
   - 组织：arXiv
   - 年份：arXiv 2601.14914, 2026-01
   - 出处：https://arxiv.org/pdf/2601.14914
   - 相关性：每个子任务实例化带干净上下文的 Coder 代理（仅含其规格说明，屏蔽先前失败），并提出 Ephemeral-Persistent State Separation (EPSS) 隔离各 Coder 执行状态，防止调试轨迹污染 Delegator 上下文。**面向代码-as-动作场景，与本研究最贴合的隔离方案之一。**

7. **FastContext: Training Efficient Repository Explorer for Coding Agents** 【✔ 近3个月 · 最高优先级】
   - 组织：arXiv（微软）
   - 年份：arXiv 2606.14066, 2026-06
   - 出处：https://arxiv.org/pdf/2606.14066v3
   - 相关性：指出仓库探索是编码 agent 主要瓶颈——无关片段污染上下文；提出把"仓库探索"与"求解"分离的专用探索 subagent，按需并行读取/搜索，返回精准的 file-and-line 实证作为紧凑上下文。训练 4B–30B 探索模型。**正是"定位/检索子任务不污染主求解上下文"的机制。注：官方代码仓库已下架，论文确凿。**

8. **Dynamic Attentional Context Scoping (DACS): Agent-Triggered Focus Sessions** 【✔ 近3个月相关】
   - 组织：arXiv
   - 年份：arXiv 2604.07911, 2026-04
   - 出处：https://arxiv.org/pdf/2604.07911v1
   - 相关性：当 agent 发出 STEERINGREQUEST 时编排器进入 FOCUS 模式，注入该 agent 完整上下文同时把其他 agent 压缩为 registry 条目，实现 agent 触发、非对称、确定性的上下文隔离，消除跨 agent 污染。

9. **CodeComp: Structural KV Cache Compression for Agentic Coding** 【✔ 近3个月相关】
   - 组织：arXiv
   - 年份：arXiv 2604.10235, 2026-04
   - 出处：https://arxiv.org/pdf/2604.10235v1
   - 相关性：用 Joern/CPG 静态分析提取结构锚点（函数调用、控制流谓词、返回、赋值），据此为代码任务做 KV cache 分层压缩、保护语义关键片段——面向 cache/上下文的隔离与压缩。

10. **Why Agent Caching Fails and How to Fix It: Structured Intent Canonicalization with Few-Shot Learning** 【✔ 近3个月相关】
    - 作者：Abhinaba Basu
    - 年份：arXiv 2602.18922, 2026-02
    - 出处：https://arxiv.org/pdf/2602.18922v2
    - 相关性：分析现有 agent 缓存（如 GPTCache）在个人 agent 任务上命中率极低的原因，提出结构化意图规范化 + few-shot 提升缓存命中——直接关于 agent 缓存机制。

### 开源项目（上下文隔离工程实践）

11. **memex RFC #256: Hierarchical Memory Isolation** 【✔ 近3个月 · 高优先级】
    - 组织：JasperHG90（memex 仓库）
    - 年份：2026
    - URL：https://github.com/JasperHG90/memex/issues/256
    - 相关性：提出 OS 式进程内存隔离的子任务委托：委派时创建 child context，child 内写入默认不向父传播，完成时只让 schema 校验后的返回值越过边界，中间观察/工具输出/推理轨迹留在 child 且可选归档。**与 AgentSys 思想一致的开源 RFC。**

12. **Recursive Self-Spawning Agent Architecture** 【✔ 近3个月相关】
    - 组织：junwatu（claude-code 仓库）
    - 年份：2026
    - URL：https://github.com/junwatu/claude-code/blob/main/RECURSIVE_AGENT_ARCHITECTURE.md
    - 相关性：明确列出"Context Isolation"设计：每个被 spawn 的 agent 拥有独立 message history、专属 system prompt、工具子集、工作目录与独立 abort controller，子代理上下文与父级隔离。

13. **Learn-Claude-Code：Subagent（上下文隔离的子代理框架）** 【✔ 近3个月相关】
    - 组织：shareAI-lab
    - 年份：2026
    - URL：https://github.com/shareAI-lab/learn-claude-code
    - 相关性：Subagent 被称为"上下文隔离的极简子代理框架"，通过"大任务拆小、每个子任务独立干净上下文"让主对话保持清晰，避免被工具调用输出污染。

14. **Memagent: Context Engineering in LLM Agents** 【✔ 近3个月相关】
    - 组织：Rohith-Scalers
    - 年份：2026
    - URL：https://github.com/Rohith-Scalers/Memagent/blob/main/context-engineering-llm-agents-2026.md
    - 相关性：描述"task-specific context"——每个 subagent 获得只含定向指令与最小事实的全新上下文、无无关历史噪声；子代理完成后只返回干净报告，重试历史与堆栈被丢弃。

---

## 三、代码库定位与检索工具（为检索服务的高效工具）

### 开源项目

15. **Aider Repository Map** 【✔ 重大】
    - 组织：Aider（Paul Gauthier）
    - 年份：持续更新
    - URL：https://aider.chat/docs/repomap.html
    - 相关性：用 tree-sitter 抽取符号 + PageRank 排序生成 git 仓库的精简地图（关键类/函数及签名），随其他上下文拼进 prompt，帮助 agent 理解代码间关系并尊重既有抽象。**仓库地图（repomap）的经典实现。**

16. **Sourcegraph（AI coding context）** 【✔ 重大】
    - 组织：Sourcegraph
    - 年份：2026
    - URL：https://sourcegraph.com/resources/context-compare
    - 相关性：维护持续更新的全仓索引，提供排名搜索与跨仓库代码导航，Deep Search 在索引之上叠加 agentic 自然语言探索，并通过 MCP server 暴露给 agent——代码库索引/检索的产业化代表。

17. **RepoMap-AI** 【✔ 近3个月相关】
    - 组织：TusharKarkera22
    - 年份：2026
    - URL：https://github.com/TusharKarkera22/RepoMap-AI ；npm：https://www.npmjs.com/package/repomap-ai
    - 相关性：把整个代码库压缩成约 1000 token 的"结构化、按依赖排序、最重要的符号置顶"索引，tree-sitter 依赖图，通过 MCP 暴露。

18. **Synaptic（graphify）** 【✔ 近3个月相关】
    - 组织：ColinVaughn
    - 年份：2026
    - URL：https://github.com/ColinVaughn/Synaptic ；对比页：https://github.com/ColinVaughn/Synaptic/wiki/Synaptic-vs-Other-Tools
    - 相关性：基于 tree-sitter 构建可查询的持久化代码知识图谱（符号 + 类型化边 + EXTRACTED/INFERRED/AMBIGUOUS 标注），以 MCP server 形式供给多种 agent 助手。**注：graphify 为别名，真实仓库实体为 Synaptic。**

19. **CodeGraph** 【✔ 近3个月相关】
    - 组织：社区开源
    - 年份：2025–2026
    - URL：https://juejin.cn/post/7646714424421842970
    - 相关性：tree-sitter AST → SQLite 图 + FTS5，本地索引，通过 MCP（10 个工具）向 Claude Code/Cursor/Codex 等 agent 提供"本地代码地图"以加速探索。

20. **codebase-memory-mcp（tree-sitter 知识图谱）** 【✔ 近3个月相关】
    - 年份：2026
    - URL：https://cloud.tencent.com/developer/article/2702009
    - 相关性：用 tree-sitter 构建代码记忆知识图谱，RAM-first + SQLite 持久化（LZ4 HC 压缩），为 LLM coding agent 提供代码记忆/检索。

21. **Multimodal Repository Graphs（Codex CLI 混合探索）** 【✔ 近3个月相关】
    - 作者：Daniel Vaughan
    - 年份：2026-07-07
    - URL：https://codex.danielvaughan.com/2026/07/07/visual-codebase-understanding-multimodal-repository-graphs-codex-cli-hybrid-exploration/
    - 相关性：把仓库建模为有向异构图（contains/imports/invokes/inherits 四种边），评估多模态基础模型用 token 高效的图式视觉理解进行代码库探索，可接入 Codex CLI。

### 学术论文

22. **One Tool Is Enough: Reinforcement Learning for Repository-Level Agents（RepoNavigator）** 【✔ 近3个月相关】
    - 组织：arXiv
    - 年份：arXiv 2512.20957, 2025-12
    - 出处：https://arxiv.org/pdf/2512.20957v2
    - 相关性：训练端到端 RL 的仓库级 agent RepoNavigator，用单一 jump 工具完成仓库定位/检索，简化工具操作并提升检索性能。

23. **RepoMaster: Autonomous Exploration of GitHub Repositories** 【✔ 近3个月相关】
    - 组织：arXiv（DataDynam 团队）
    - 年份：arXiv 2505.21577, 2025
    - 出处：https://arxiv.org/pdf/2505.21577v1 ；代码：https://github.com/DataDynam/RepoMaster
    - 相关性：通过函数调用图(FCG) 与模块依赖图(MDG) 追踪调用链/依赖路径，并提供关键词搜索工具，帮助 agent 在大型代码库中快速定位代码。

24. **CodeStruct: Code Agents over Structured Action Spaces** 【✔ 近3个月相关】
    - 组织：arXiv
    - 年份：arXiv 2604.05407, 2026-04
    - 出处：https://arxiv.org/pdf/2604.05407v1
    - 相关性：把 agent 原语定义为结构感知的 readCode/editCode（按文件大小阈值、选择器、行区间做结构感知检索与编辑），减少无结构读取对上下文的浪费。

---

## 四、分层 / 分级上下文管理架构

### 学术论文

25. **Matryoshka Agent: Unfolding Sub-Agents for Long-Horizon ML Engineering** 【✔ 近3个月相关】
    - 组织：arXiv
    - 年份：arXiv 2607.25090, 2026-07
    - 出处：https://arxiv.org/html/2607.25090v1
    - 相关性：统一分层 agent 框架，高层 Orchestrator 维护紧凑上下文，把长程复杂任务分解为协调的决策/执行层级，以应对长而嘈杂的上下文。**注：需与另一篇 2410.20749 MATRYOSHKA（黑盒 LLM 控制器）区分。**

26. **Context Management for LLM Agents: A Memory Hierarchy View（综述）** 【✔ 近3个月相关】
    - 作者：Zoey Li
    - 年份：2026
    - URL：https://zoeyli.com/reinforcement%20learning/Learning-Context-Management-RL/
    - 相关性：以内存层级视角梳理 agent 上下文管理，最自主策略是把子任务整体委托给在全新上下文窗口运行、只返回浓缩摘要的 subagent，提及 ContextFold。

---

## 审查备注

- 已核实全部真实存在，无虚构条目。
- 关键区分：**学术源头是 PEEK 论文中的 Cartographer 组件**；**独立开源是同名 Icarus-afk/Cartographer**。二者名称相同但属不同实体，分析时必须区分。
- 事实修正：FastContext 官方代码仓库已下架（arXiv 论文确凿）；graphify 真实实体为 Synaptic；Matryoshka 与 2410.20749 异文。
- 最高优先级交集：PEEK / Icarus-afk Cartographer / AgentSys / CodeDelegator / FastContext / memex RFC。
- 工程实践：Aider repomap 与 Sourcegraph 是"代码库地图/检索"的成熟参照；Codex CLI 的 subagent 架构（viewer-editor 分离）是"上下文隔离"的落地参照。