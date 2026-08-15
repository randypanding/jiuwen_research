# LLM/多Agent 缓存与复用 + 多Agent框架成本优化能力 — 审查重构清单

## 审查说明
- **审查日期**：2026-08-15
- **核验标准**：
  - 论文部分：逐一用 WebFetch 核验 arXiv 页面（`https://arxiv.org/abs/{编号}`）或作者/官方来源 URL，确认真实存在；编号所列 5 个重点怀疑项（2601.06007、2603.13289、2602.10986、2603.04428、2605.06472）经核验**全部真实存在**，未被剔除。
  - 开源项目部分：用 WebFetch/curl 核验 GitHub 仓库真实存在及大致 Star 量级（取自检索时仓库页）。
  - 无法核验真实存在、URL 失效或仅 0–6 Star 的无意义新项目一律删除（宁缺毋滥）。
- **剔除条目**：共删除 6 条（均为开源项目部分）：
  1. GPTSwarm（https://github.com/tsinghua-fib-lab/GPTSwarm → 页面 404，原仓库已失效/转移）
  2. LLM Cost Tracker（prajitdatta/LLM-Cost-Tracker，0 Star）
  3. llm-meter（amreshparida/llm-meter，0 星新项目）
  4. TokenTracker（he-yufeng/TokenTracker，6 Star）
  5. CostPilot（aryanjp1/costpilot，0 星新项目）
  6. tokonomix（stef41/tokonomix，0 星新项目）
- **标注说明**：`[★]` = 公认重要/奠基（正式会议或具有里程碑意义）；`[R]` = 近三月（2026-05-15 前后）内新增或近期缓存/复用研究。
- 论文部分保留 27 条，开源项目部分保留 16 条，合计 43 条。

---

## 第一部分：LLM/多Agent 缓存与复用相关论文

> 关键词覆盖：prompt caching、KV cache reuse、semantic cache、agent execution/tool-value caching、KV cache TTL/压缩、prefix cache eviction。

### 1. CachedAttention: Cost-Efficient LLM Serving for Multi-turn Conversations with Cached Attention [★]
- **年份**：2024（USENIX ATC 2024）
- **URL**：https://arxiv.org/abs/2403.19708
- **一句话思路**：分层 KV 缓存系统（GPU HBM→CPU→NVMe SSD）在会话间复用多轮对话 KV cache，分层预取/异步保存，降低重复 prefill，端到端推理成本最高降约 70%。

### 2. Prompt Cache: Modular Attention Reuse for Low-Latency Inference [★]
- **年份**：2023（MLSys 2024）
- **URL**：https://arxiv.org/abs/2311.04934
- **一句话思路**：用 schema 定义可复用 prompt 模块并预计算其 attention 状态，GPU TTFT 提升 8x、CPU 提升 60x 且无精度损失。

### 3. SGLang: Efficient Execution of Structured Language Model Programs [★]
- **年份**：2024
- **URL**：https://arxiv.org/abs/2312.07104
- **一句话思路**：RadixAttention 用 radix tree 自动管理 KV cache 公共前缀复用，跨请求共享 prefix，显著降低 prefill 成本与延迟（吞吐最高 6.4x）。

### 4. Tail-Optimized Caching for LLM Inference [★]
- **年份**：2025（NeurIPS 2025）
- **URL**：https://papers.nips.cc/paper_files/paper/2025/file/f05fe8b796dcbd67bc7bb1ea89df1793-Paper-Conference.pdf
- **一句话思路**：提出 Tail-Optimized LRU（T-LRU），把缓存容量优先分配给高延迟会话，P95 尾延迟最高降 23.9%、SLO 违约降 38.9%，并给出 LRU 在此问题上的最优性证明。

### 5. MeanCache: User-Centric Semantic Caching for LLM Web Services
- **年份**：2024（IEEE IPDPS 2025）
- **URL**：https://arxiv.org/abs/2403.02694
- **一句话思路**：对查询 embedding 做 PCA 压缩存入语义缓存，用联邦学习训练用户级相似度模型，命中/未命中决策 F-score 提高约 17%、存储降 83%。

### 6. Semantic Caching for Low-Cost LLM Serving: From Offline Learning to Online Adaptation
- **年份**：2025（INFOCOM 2026）
- **URL**：https://arxiv.org/abs/2508.07675
- **一句话思路**：把语义缓存形式化为含"不匹配代价"的驱逐问题，离线学习+在线自适应，在未知查询/成本分布下给出可证明高效的驱逐算法。

### 7. An Ensemble Embedding Approach for Improving Semantic Caching Performance in LLM-based Systems
- **年份**：2025
- **URL**：https://arxiv.org/abs/2507.07061
- **一句话思路**：用集成 embedding + 元编码器提升语义缓存相似识别，语义等价查询命中率达 92%，同时保持非等价查询 85% 的拒绝率。

### 8. GPT Semantic Cache: Reducing LLM Costs and Latency via Semantic Embedding Caching
- **年份**：2024
- **URL**：https://arxiv.org/abs/2411.05276
- **一句话思路**：基于 Redis+embedding 的内存语义缓存，减少最高 68.8% API 调用，正命中率超 97%。

### 9. Semantic Caching of Contextual Summaries for Efficient Question-Answering with Language Models
- **年份**：2025
- **URL**：https://arxiv.org/abs/2505.11271
- **一句话思路**：缓存并复用文档的中间上下文摘要供相似查询复用，减少 50–60% 冗余计算同时保持相近答案准确率。

### 10. Don't Break the Cache: An Evaluation of Prompt Caching for Long-Horizon Agentic Tasks [R]
- **年份**：2026
- **URL**：https://arxiv.org/abs/2601.06007
- **一句话思路**：跨 OpenAI/Anthropic/Google 在 DeepResearchBench 长程 agent 任务上评估 prompt caching，可降 API 成本 41–80%、改善 TTFT 13–31%，并指出 context 结构影响缓存命中。

### 11. Generative Caching for Structurally Similar Prompts and Responses (GenCache)
- **年份**：2025
- **URL**：https://arxiv.org/abs/2511.17565
- **一句话思路**：对结构相似但非完全相同的 prompt 生成可复用响应条目，agent 场景缓存命中率提升约 20%、端到端延迟降约 34%。

### 12. RelayCaching: Accelerating LLM Collaboration via Decoding KV Cache Reuse [R]
- **年份**：2026
- **URL**：https://arxiv.org/abs/2603.13289
- **一句话思路**：训练无关的推理方法，直接复用前一 agent 解码阶段 KV cache 到下一 agent prefill，KV 复用率超 80%、TTFT 最高降 4.7x。

### 13. KVComm: Online Cross-context KV-cache Communication for Efficient LLM-based Multi-agent Systems [★]
- **年份**：2025（NeurIPS 2025）
- **URL**：https://arxiv.org/abs/2510.12872
- **一句话思路**：跨上下文在线对齐 KV cache 偏移复用，五 agent 全连接场景最高 7.8x 加速，共享内容复用率超 70%。

### 14. TVCACHE: A Stateful Tool-Value Cache for Post-Training LLM Agents [R]
- **年份**：2026
- **URL**：https://arxiv.org/abs/2602.10986
- **一句话思路**：维护工具调用序列树，按最长前缀匹配复用工具结果以严格保证环境状态一致，命中率最高 70%、工具执行时间最高降 6.9x。

### 15. KVFlow: Efficient Prefix Caching for Accelerating LLM-Based Multi-Agent Workflows
- **年份**：2025
- **URL**：https://arxiv.org/abs/2507.07400
- **一句话思路**：用 Agent Step Graph 估计各 agent 未来激活时间，做细粒度置换与共享前缀管理，单工作流最高 1.83x、多并发工作流最高 2.19x 加速。

### 16. Continuum: Efficient and Robust Multi-Turn LLM Agent Scheduling with KV Cache TTL
- **年份**：2025
- **URL**：https://arxiv.org/abs/2511.02230
- **一句话思路**：为多轮 agent 工作负载引入 KV cache 的 TTL 机制，按重载成本与排队延迟决定是否固定 KV，平均任务完成时间改善超 8x。

### 17. Agentic Plan Caching: Test-Time Memory for Fast and Cost-Efficient LLM Agents [★]
- **年份**：2025（NeurIPS 2025）
- **URL**：https://arxiv.org/abs/2506.14852
- **一句话思路**：从已完成 agent 执行中抽取/存储/适配/复用"计划模板"，成本平均降 50.31%、延迟降 27.28%（区别于传统语义缓存）。

### 18. Keep the Cost Down: A Review on Methods to Optimize LLM's KV Cache Consumption [★]
- **年份**：2024（COLM 2024）
- **URL**：https://arxiv.org/abs/2407.18003
- **一句话思路**：系统性综述 KV cache 在预训练/部署/推理各阶段的压缩与复用优化方法，是 KV 缓存成本优化的权威综述。

### 19. Preble: Efficient Distributed Prompt Scheduling for LLM Serving
- **年份**：2024
- **URL**：https://arxiv.org/abs/2407.00023
- **一句话思路**：首个面向 prompt 共享的分布式 LLM 服务平台，联合优化 KV 复用与计算负载均衡，平均延迟相对 SOTA 提升 1.5x–14.5x。

### 20. GPTCache: An Open-Source Semantic Cache for LLM Applications Enabling Faster Answers and Cost Savings [★]
- **年份**：2023（NLP-OSS 2023）
- **URL**：https://aclanthology.org/2023.nlposs-1.30/
- **一句话思路**：开源语义缓存库的原理论文，通过语义相似命中直接返回结果，降低重复 LLM 调用成本与延迟（注：Anthology ID 为 2023.nlposs-1.30，卷页 212–218）。

### 21. Latent Briefing: Efficient Memory Sharing for Multi-Agent Systems via KV Cache Compaction [R]
- **年份**：2026（Ramp Labs 技术博客）
- **URL**：https://labs.ramp.com/research/latent-briefing-kv-cache/
- **一句话思路**：在递归式多 agent（RLM）架构中用任务引导的 KV cache 压缩实现跨 agent 内存共享，worker 模型 token 消耗降低约 65%。

### 22. Agent Memory Below the Prompt: Persistent Q4 KV Cache for Multi-Agent LLM Inference on Edge Devices [R]
- **年份**：2026
- **URL**：https://arxiv.org/abs/2603.04428
- **一句话思路**：将 Q4 量化 KV cache 持久化到盘并直接恢复进 attention，消除重复 prefill，TTFT 最高提速 136x。

### 23. Efficient Serving for Dynamic Agent Workflows with Prediction-based KV-Cache Management (PBKV) [R]
- **年份**：2026
- **URL**：https://arxiv.org/abs/2605.06472
- **一句话思路**：预测动态 agent 工作流中后续 agent 调用与缓存复用机会，据此管理 KV cache，动态工作流相对 LRU 最高 1.85x 加速。

### 24. Not All Tokens Are Worth Caching: Learning Semantic-Aware Eviction for LLM Prefix Caches (SAECache) [R]（新增）
- **年份**：2026
- **URL**：https://arxiv.org/abs/2605.18825
- **一句话思路**：不同 token 类型复用率差异最高达 756x，SAECache 用多队列+语义感知加权+全自适应在线学习做 prefix cache 驱逐，TTFT 改善 1.4x–2.7x。

### 25. ForkKV: Scaling Multi-LoRA Agent Serving via Copy-on-Write Disaggregated KV Cache [R]（新增）
- **年份**：2026
- **URL**：https://arxiv.org/abs/2604.06370
- **一句话思路**：用 fork-with-copy-on-write 把多 LoRA agent 的 KV cache 分解为共享+独立部分，缓解共享上下文的缓存发散，吞吐最高提升 3.0x。

### 26. TokenCake: A KV-Cache-centric Serving Framework for LLM-based Multi-Agent Applications（新增）
- **年份**：2025
- **URL**：https://arxiv.org/abs/2510.18586
- **一句话思路**：面向多 agent 的 KV 缓存中心化服务框架，时空调度器在函数调用期间卸载/预取空闲 KV 缓存，端到端延迟降超 47.06%。

### 27. Asynchronous Verified Semantic Caching for Tiered LLM Architectures (Krites) [R]（新增）
- **年份**：2026
- **URL**：https://arxiv.org/abs/2602.13165
- **一句话思路**：异步 LLM 判定语义缓存策略，在静态阈值临界区间用 LLM judge 验证并可提升静态缓存覆盖面，静态命中+验证提升最高 3.9x。

---

## 第二部分：多Agent框架/开源项目中的成本优化能力

> 关键词覆盖：LLM gateway、cost tracking、semantic caching、prefix/KV caching、observability、token budget enforcement。
> Star 规模为检索时（2026-08）的大致量级，仅供参考。

### 1. GPTCache (Zilliz) [★]
- **GitHub**：https://github.com/zilliztech/GPTCache
- **Star 量级**：约 8.2k
- **一句话成本能力**：语义缓存库，集成 LangChain/llama_index，通过相似命中直接返回结果，API 成本降低约 10x、速度提升约 100x。

### 2. LiteLLM (BerriAI) [★]
- **GitHub**：https://github.com/BerriAI/litellm
- **Star 量级**：约 56k
- **一句话成本能力**：统一 LLM 网关/代理，支持 100+ 提供商、token 用量与成本追踪计费、预算控制与 LLM 缓存（含内置 llm_cost 成本计算库），是成本优化与观测的基础设施。

### 3. Langfuse [★]
- **GitHub**：https://github.com/langfuse/langfuse
- **Star 量级**：约 33k
- **一句话成本能力**：开源 LLM 工程平台，提供 token/成本观测、追踪、评估与 prompt 管理，可对 agent 链路做成本归因与预算监控。

### 4. Helicone
- **GitHub**：https://github.com/Helicone/helicone
- **Star 量级**：约 6.1k
- **一句话成本能力**：AI Gateway + 可观测平台，代理并统计 token 成本/延迟/用量，支持按模型/功能拆分的成本分析。

### 5. AgentOps [R]
- **GitHub**：https://github.com/AgentOps-AI/agentops
- **Star 量级**：约 5.8k
- **一句话成本能力**：面向 AI agent 的可观测性 SDK，追踪 agent 会话中的 LLM 调用、token 与成本，支持预算与执行限制。

### 6. AutoGen (Microsoft) [★]
- **GitHub**：https://github.com/microsoft/autogen
- **Star 量级**：约 60k
- **一句话成本能力**：微软多 agent 对话框架，支持 token 用量观测、模型选择与消息管理，便于控制推理开销。

### 7. LangGraph (LangChain) [★]
- **GitHub**：https://github.com/langchain-ai/langgraph
- **Star 量级**：约 40k
- **一句话成本能力**：图结构多 agent 编排框架，配合 LangSmith 做 token/成本追踪，可显式控制执行路径减少冗余调用。

### 8. CrewAI [★]
- **GitHub**：https://github.com/crewAIInc/crewAI
- **Star 量级**：约 57k
- **一句话成本能力**：角色/团队多 agent 编排框架，支持任务级缓存与 token/成本统计，便于复用结果并控制预算。

### 9. MetaGPT [★]
- **GitHub**：https://github.com/FoundationAgents/MetaGPT
- **Star 量级**：约 70k
- **一句话成本能力**：多角色多 agent 软件实体框架，官方估算完整项目生成约 $2、分析设计约 $0.2，便于评估多 agent 流水线 token 成本。

### 10. AgentScope (阿里) [★]
- **GitHub**：https://github.com/agentscope-ai/agentscope
- **Star 量级**：约 29k
- **一句话成本能力**：生产级多 agent 框架，内置 token 消耗监控与预算配置（月度预算、告警阈值、超预算自动停止）。

### 11. OpenHands [★]
- **GitHub**：https://github.com/OpenHands/OpenHands
- **Star 量级**：约 84k
- **一句话成本能力**：开源自主编码 agent，自托管 + usage monitoring 与 budget enforcement（Agent Control Plane），单任务 LLM 成本低于商用编码 agent。

### 12. CAMEL
- **GitHub**：https://github.com/camel-ai/camel
- **Star 量级**：约 17.6k
- **一句话成本能力**：多 agent 框架与研究社区，提供 token 用量统计与成本相关观测能力。

### 13. Swarms (kyegomez)
- **GitHub**：https://github.com/kyegomez/swarms
- **Star 量级**：约 7.1k
- **一句话成本能力**：大规模 agent swarm 框架，官方提供成本优化 playbook，强调减少 token 流动、缓存与资源调度来降低成本。

### 14. vLLM [★]（新增）
- **GitHub**：https://github.com/vllm-project/vllm
- **Star 量级**：约 89k
- **一句话成本能力**：高吞吐 LLM 推理引擎，内置自动前缀缓存（prefix caching）复用 KV，是多 agent 高并发服务侧成本优化的基础设施。

### 15. SGLang [★]（新增）
- **GitHub**：https://github.com/sgl-project/sglang
- **Star 量级**：约 32k
- **一句话成本能力**：结构化 LLM 程序执行引擎，RadixAttention 自动复用 KV cache 公共前缀，显著降低 prefill 成本与延迟。

### 16. Google ADK (Agent Development Kit) [★]（新增）
- **GitHub**：https://github.com/google/adk-python
- **Star 量级**：约 21k
- **一句话成本能力**：Google 官方多 agent 开发框架，内置 tracing/成本观测与 A2A 协议支持，便于在多 agent 流程中监控与限制 token 开销。

---

## 附注与说明
- 论文年份与 URL 均以核验结果为准；Star 规模为检索时大致量级。
- 本清单仅保留经核验的条目（论文 27 条 + 开源项目 16 条），宁缺毋滥。
- 删除的 6 条开源项目（GPTSwarm、LLM-Cost-Tracker、llm-meter、TokenTracker、CostPilot、tokonomix）因仓库 URL 失效或无实质 Star/可信度而不保留。