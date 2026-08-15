# 子代理建议二：工程选型与 Swarm 架构

> 依据：`精读总结与评分表.md`（67 项 ABC 评分）、`curated/01`、`curated/02`、`curated/04`，以及对 8 个一手来源的直接核验。

## A. 选型结论

### A1. 编排框架

| 推荐序 | 项目 | 理由 | 成熟度 |
|---|---|---|---|
| **首选** | **LangGraph** | checkpoint 持久化 + durable execution（故障后从断点精确恢复）、human-in-the-loop、短期工作记忆与长期持久记忆分层、subgraphs 上下文隔离；被 Klarna、Replit、Elastic 等用于生产，43K 依赖方、7,039 commits、提交至 2026-08-09，MIT 协议 [3] | ★★★★★ 最成熟（稳定版 1.2 系） |
| 备选 1 | **OpenAI Agents SDK** | Swarm 官方继任者；Handoffs/agents-as-tools、Sessions 自动历史管理、Sandbox Agents、内置 Tracing；provider-agnostic（支持 100+ LLM）；提交至 2026-07、v0.17.7（2026-06-24）[4] | ★★★★ 官方背书但 **pre-1.0** |
| 备选 2 | **JiuwenSwarm** | 唯一把"团队 token 预算"做成一等公民的 swarm 框架（Swarmflow 原生支持 HITL + team token budget + 运行树监控）；Leader/Teammate 分布式蜂群、Skill 自进化；2,058 commits、95 贡献者、提交至 2026-08-13，Apache-2.0 [6] | ★★★ 极活跃但**非常年轻**（2026-03 首发，当前 v0.2.4.beta） |
| 备选 3 | CrewAI | 极活跃（v1.15.16，2026-08-14），但记忆默认关闭、缺显式上下文经济化机制，评分表列 B 档 | ★★★★ 框架成熟但上下文管理非其强项 |

### A2. 记忆层

| 推荐序 | 项目 | 理由 | 成熟度 |
|---|---|---|---|
| **首选（跨会话长期记忆）** | **Mem0** | User/Session/Agent 三级记忆；新算法（2026-04）：单次 ADD-only 抽取、实体链接、语义+BM25+实体多信号融合检索、时间推理；LoCoMo 92.5 / LongMemEval 94.4；官方提供 LangGraph、CrewAI 集成指南；2,579 commits、402 贡献者、提交至 2026-08-13，Apache-2.0 [1] | ★★★★☆ 生态最成熟；注意官方明示 benchmark 含平台私有优化，开源版增益"方向相似但数值不等同"[1] |
| 首选（时间敏感事实/溯源） | **Zep / Graphiti** | 时间上下文图：事实带有效性窗口（失效而非删除）、episode 溯源、语义+关键词+图遍历混合检索**不依赖 LLM 摘要**（检索期零摘要 token 成本）；Graphiti 为 OSS 引擎、Zep 为托管层（sub-200ms）；提交至 2026-07 [2] | ★★★★ 机制独特；注意活跃度中等、Kuzu 后端已弃用 [2] |
| 首选（任务内短期压缩） | **TencentDB Agent Memory** | 符号短时记忆（冗长工具日志 offload 到外部文件，上下文只留 Mermaid 符号画布 + node_id 按需回查原文）+ L0→L3 金字塔长时记忆；官方实测：WideSearch token −61.38% 且通过率相对 +51.52%、SWE-bench token −33.09%、PersonaMem 48%→76%；全本地 SQLite、零外部 API [5] | ★★★ 新（2026-04 init），数据亮眼但仅 OpenClaw/Hermes 插件形态 |

**组合建议**：短期（任务内）用 TencentDB Agent Memory 式符号 offload，长期（跨会话/跨 agent）用 Mem0 或 Graphiti——两者正交，不冲突。

### A3. 压缩 / 检索 / 成本组件

- **即插即用**：LLMLingua-2（B 档，token 分类式压缩 2–5×、即插即用）；tokencost / llm-token-counter（成本核算与监控，评分表 B 档）。
- **缓存策略**（最大单一省钱杠杆）：《Don't Break the Cache》跨 OpenAI/Anthropic/Google 实测成本降 41–80%、TTFT 改善 13–31%（评分表 A 档）；执行 OpenAI 官方铁律"静态前置、动态后置"，OpenAI 客户案例命中率从 60% 提到 87%（评分表 B 档）。
- **机制借鉴（研究级，无现成组件）**：ACON（峰值 token −26–54%、精度保留 >95%）、TokenPilot（成本降 56–87% 且保缓存连续性）、ACE（raw/abstract/drop 三态可逆弹性）、CWL（确定性 LLM-free 逐出，单会话 8000 万 token 无可测退化）、CASTER（路由省推理成本 72.4%）。

## B. 推荐的 Swarm 上下文架构设计

**核心原则：默认隔离、按需共享、摘要回流、缓存友好。**

1. **隔离为主，共享为辅（有直接量化证据）**
   - DACS 实测：orchestrator 双模式——Registry 模式只存每 agent ≤200 token 的状态摘要，agent 发出 SteeringRequest 时才进入 Focus 模式注入该 agent 全量上下文、其余 agent 压缩为注册条目。steering 准确率 90.0–98.4% vs 扁平上下文基线 21.0–60.0%，错误 agent 污染从 28–57% 降至 0–14%，上下文效率比最高 3.53×，且优势随 agent 数 N 与决策密度 D 增大 [7]。
   - 注意：DACS 为单一作者 preprint、200 次合成场景试验 [7]，应作为设计参数参考而非绝对结论。
   - 《Shared vs Separate Context》提供了共享/分离的概率分析框架与 Response Consistency Index，但纯理论推导、无实证 [8]——共享上下文有一致性收益，但须付出溢出与噪声管理成本。
   - 若确需共享记忆，按 MemClaw 施加治理四原语（scoped retrieval / temporal supersession / provenance / policy），防四类失效：未授权泄漏、过期传播、矛盾持久化、来源崩塌（评分表 B 档，来源追踪可 100% 重建 depth-4）。

2. **Fan-out / Fan-in（orchestrator–worker）**
   - 采用 Anthropic 官方推荐的多 agent 结构：orchestrator fan-out 到独立上下文的子 agent，子 agent 只回传**摘要级结果**而非完整轨迹（评分表 A 档 Anthropic 指南；Claude Code sub-agents 为工业界范式）。
   - 证据：《Less Context, Better Agents》把上下文裁剪到最近 5 次工具调用，token 减约 63.9% 而完成率显著上升（工作区材料记录 79% 与 91.6% 两种口径）；Chain of Agents 顺序分段把复杂度从 n² 降到 nk。

3. **Checkpoint / 断点续跑**
   - 用 LangGraph durable execution 持久化状态：以"恢复成本"换"重算成本"，避免长任务失败后整段重跑导致的 token 重复支出 [3]。

4. **交接（handoff）模式**
   - 交接时转移**精简上下文**而非全量历史：OpenAI Agents SDK 的 Handoffs / agents-as-tools + Sessions 限长 + 回调裁剪 + 自动压缩（三件套全可配置）[4]。
   - 跨角色信息用 MetaGPT 式 SOP 结构化中间产物（固定 schema）取代自由对话，减少冗余 token。
   - 长任务用 RECAP 式有界滑动窗口（活跃上下文 O(K·L)）+ 结构化重注入（Robotouille 基准 +32%/+29%）。

5. **压缩时机必须服从缓存连续性**
   - 《Don't Break the Cache》警示：朴素 full-context 缓存可能反增延迟；压缩/逐出操作应尽量保持前缀稳定。TokenPilot 的 Lifecycle-Aware Eviction 与 ACE 的可逆压缩是"压缩不破坏缓存"的参考机制。

## C. 集成与迁移建议

1. **OpenAI Swarm 迁移路径（Swarm 已弃用，勿用于新项目）**
   - 直接迁移到 OpenAI Agents SDK：Swarm 的 `handoff` 概念对应 SDK 的 Handoffs/agents-as-tools；手写历史管理替换为 Sessions（自动会话历史、限长、裁剪、自动压缩）[4]。
   - Swarm"无全局共享状态、上下文随交接转移"的设计范式可保留为架构原则，但其 stateless 教学级实现不可用于生产。

2. **分阶段落地路线**
   - **阶段 1（骨架）**：编排迁至 LangGraph，启用 checkpoint 与 subgraph 隔离 [3]。
   - **阶段 2（长期记忆）**：接入 Mem0（有官方 LangGraph 集成指南）承担 User/Session/Agent 级跨会话记忆 [1]；若业务强依赖"事实何时为真/何时失效"，换 Graphiti（需自备 Neo4j/FalkorDB）[2]。
   - **阶段 3（任务内压缩）**：引入 TencentDB Agent Memory（OpenClaw/Hermes 插件形态）或按其思路自建"工具日志 offload + Mermaid 画布 + node_id 回查"[5]。
   - **阶段 4（成本可观测）**：tokencost/llm-token-counter 埋点 + LangSmith 或 Agents SDK Tracing；按 agent/团队设 token 预算（JiuwenSwarm 的 team token budget 是现成参照 [6]）。

3. **缓存纪律**：系统提示、工具定义等静态内容前置且保持稳定，动态内容后置；避免会话中途改写前缀（OpenAI 官方规范 + Don't Break the Cache 结论）。

## D. 风险与注意事项

1. **活跃度 / 生态风险**
   - **LangMem**：实质代码更新止于 2025-07，已放缓，不建议作为记忆层主力（评分表 B 档）。
   - **Letta（原 MemGPT）**：主仓已转 legacy，活跃开发转移到 letta-code，选型需谨慎。
   - **Graphiti**：机制优秀但提交节奏中等（核验到 2026-07-02），且 Kuzu 后端已弃用（上游项目停止维护）[2]；选 Neo4j 或 FalkorDB。
   - **TencentDB Agent Memory**：官方 Tencent 仓文件级更新核验到 2026-05 中旬，与评分表"提交至 2026-08-11"（疑为镜像仓数据）存在出入，正式采用前建议复核 [5]；且项目仅约 4 个月历史。
   - **JiuwenSwarm**：极活跃（提交至 2026-08-13）但处于 v0.2.x beta，API 与产品形态可能变动 [6]。
   - **OpenAI Agents SDK**：官方维护但 pre-1.0（v0.17.7），存在接口变动风险 [4]。

2. **研究 → 生产的落差**：A 档论文中 ACON、TokenPilot、ACE、Leyline、CWL 等均无开箱即用开源组件，只能自研借鉴；DACS 为合成场景 preprint [7]；《Shared vs Separate Context》纯理论无实证 [8]。

3. **数据可信度**：Mem0 官方明示其 benchmark 含托管平台私有优化，开源 SDK 效果会打折 [1]；SAMEP 宣称的冗余降 73% 为推算值非实测（评分表已标低置信）。

4. **位置偏差**：Lost in the Middle 系列证明"塞更多上下文不等于更准"（中间位置性能掉 20%+），盲目压缩也可能触发位置偏差——任何压缩/裁剪策略都需在自有任务上 A/B 验证。

5. **成本归因**：按 AWS Agentic AI Lens 的 AGENTCOST01/02/05 原则做多 agent 成本归因，否则 swarm 规模扩大后无法定位烧钱的 agent/环节。

## Sources

1. Mem0 GitHub README — https://github.com/mem0ai/mem0
2. Graphiti (getzep) GitHub README — https://github.com/getzep/graphiti
3. LangGraph GitHub README — https://github.com/langchain-ai/langgraph
4. OpenAI Agents SDK GitHub README — https://github.com/openai/openai-agents-python
5. TencentDB Agent Memory GitHub README — https://github.com/Tencent/TencentDB-Agent-Memory
6. JiuwenSwarm GitHub README — https://github.com/openJiuwen-ai/jiuwenswarm
7. DACS: Dynamic Attentional Context Scoping, arXiv:2604.07911 — https://arxiv.org/abs/2604.07911
8. Shared vs Separate Context, arXiv:2504.07303 — https://arxiv.org/abs/2504.07303
