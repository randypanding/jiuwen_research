# 子代理建议三：成本建模与治理

> 依据：工作区 `精读总结与评分表.md`（67 项 ABC 评分）、`curated/03_论文与规范_成本优化.md`、`curated/01`、`curated/02`、`审查报告.md` 的既有精读记录，另本次直接抓取了 AWS Agentic AI Lens 成本章节（AGENTCOST01/05/07）与 OpenAI Prompt Caching 官方指南原文。论文数字均引自工作区已完成的原文精读记录，未重新核验的条目已标注。

## A. 成本建模方法

**1. 承认二次增长是基本盘。** ACM（arXiv 2607.21503，A 档）论证：朴素"全量累积上下文"的 agent，token 成本随对话长度**二次增长**；粗略摘要可把成本压回线性，但伴随准确率悬崖。任何成本模型的第一假设应是"不做上下文治理的 swarm，成本随轮次超线性爆炸"，而多 agent 协调还会叠加乘性开销（AWS 原文："multi-agent coordination adds multiplicative overhead"）[1][2]。

**2. 计量口径：三档计价 + 缓存单列。** 按 OpenAI 官方文档，输入 token 实际分三类计费：**缓存读取按未缓存输入价的 0.1×（新模型）、缓存写入按 1.25×、其余按 1×**；GPT-4o 等旧模型缓存折扣为 50%（缓存输入 $1.25/M），且无写入费；可缓存前缀最小 1,024 tokens（旧模型 1,024–2,048），GPT-5.6+ TTL 30 分钟（复用可刷新）[5]。成本公式 `cost = prompt_tokens×单价 + completion_tokens×单价` 中必须把 `cached_tokens` 与 `cache_write_tokens` 从普通输入中拆出，否则成本归因系统性失真 [5]。

**3. 归因粒度：到 reasoning-cycle 级，而非账单级。** AWS AGENTCOST05 要求成本可归因到 **reasoning-cycle / agent / workflow / tenant** 四级，orchestration 开销与 worker 执行成本必须可分离；多 agent 场景用 **workflow trace ID 贯穿每次 handoff**，产出真实的 cost-per-workflow-completion；并把技术遥测翻译为 **cost-per-decision、cost-per-task-completion、ROI** 三类业务指标 [3]。AGENTCOST01 补充：跟踪每个 workflow 的 **orchestration-to-execution token 比率与 supervisor-to-worker 比率**，作为 swarm 结构成本的体检指标 [2]。

**4. 预算建模单位：按 agent loop 设 token 预算，而非按 step 上限**（raw/03 工程指南记录，P2 级参考）；会话级长任务可参照 CWL（2606.11213）的实测锚点——单会话 8,000 万 token 内完成 89 个任务无可测退化，说明"预算内按优先序逐出"在极端长度下仍成立（评分表记录）。

**5. 成熟度参照系。** AGENTCOST05 给出 5 级成熟度：L1 仅账户级账单 → L2 标签分类法（agent-id/agent-role/workflow-id/task-type/environment）→ L3 trace ID 全程传播 + 比率看板 → L4 租户配额强制执行、消费超历史基线 3 倍触发 noisy-neighbor 告警 → L5 成本归因持续反哺架构决策 [3]。建议多数团队以 L3 为首个里程碑。

## B. 降本杠杆清单与预期量化收益

按"收益确定性 × 落地成本"排序，数字均标注来源：

| # | 杠杆 | 机制 | 量化收益（来源） |
|---|------|------|------------------|
| 1 | **Prompt caching 优先且保护前缀** | 静态指令/工具/共享上下文前置，动态内容后置；`prompt_cache_key`；GPT-5.6+ 用显式 breakpoint / explicit-only 模式 [5] | 跨 OpenAI/Anthropic/Google 500 会话实测：**成本降 41–80%，TTFT 改善 13–31%**（Don't Break the Cache, 2601.06007, A 档）；缓存输入计费 0.1×（新模型）[5]；OpenAI Cookbook 记录客户命中率 60%→87%、长 prompt TTFT 快 67% |
| 2 | **缓存友好的上下文逐出** | 逐出决策感知缓存连续性（Lifecycle-Aware Eviction） | TokenPilot（2606.17016, A 档）：**货币支出降 56–87%**（isolated/continuous 两种口径），性能保持 |
| 3 | **服务端 KV cache 指令化编辑** | agent 主动删除/替换缓存片段而非整段重算 | Leyline（2606.01065, A 档）：cache-hit **+11.2pp**、延迟最多降 241ms、debug-gym 求解率 **+14.3pp** |
| 4 | **上下文压缩（hard）** | 失败驱动压缩准则 + 蒸馏小压缩器 | ACON（2510.00615, A 档）：峰值 token **降 26–54%，保留 >95% 准确率**，蒸馏后小 LLM +46%；LLMLingua 系：最高 20× 压缩损失极小、LLMLingua-2 压缩 2–5×、延迟加速 1.6–2.9× |
| 5 | **软压缩 + 跨查询复用** | 分段压缩为概念嵌入，可缓存 | CompLLM（2509.19228, A 档）：2× 压缩下 **TTFT 提速 4×、KV 减 50%**，2K 训练推广到 10 万+ 上下文 |
| 6 | **结构化剪枝/逐出** | 只留最近 K 次工具调用；类型化 episode + 确定性 LLM-free 逐出 | Less Context, Better Agents（2606.10209, A 档）：**token -63.9%，完成率提升**（本地记录为 71%→79% 与 71%→91.6%，存在出入，引用前以原文为准）；CWL（2606.11213）：逐出成本近零 |
| 7 | **模型路由/级联** | 按任务难度动态选模，平凡子任务不派强模型 | CASTER（多 agent 路由, A 档）：比全强模型**推理成本降 72.4%**、成功率相当；FrugalGPT（2305.05176）：匹配 GPT-4 级性能、**最高省 98%**；Cluster-Route-Escalate（2606.27457）：保留 97%+ 精度；CSCR（2508.12491）：accuracy-cost 改进至多 25% |
| 8 | **Swarm 结构隔离** | orchestrator 只见注册摘要、被调度 agent 独享全量上下文；handoff 传结构化消息而非全历史 | DACS（2604.07911, A 档）：steering 准确率 **90.0–98.4% vs 21–60%**，上下文效率 **3.53×**；AWS 规范：handoff 只传最小上下文，令协调成本随任务复杂度而非对话长度增长 [2] |
| 9 | **记忆外置与持久化复用** | KV 持久化到磁盘、切换恢复而非重 prefill；外部记忆替代历史注入 | Agent Memory Below the Prompt（2603.04428, A 档）：**TTFT 最高 +136×、冷 prefill 15.7s→577ms、固定内存容纳 4× 多 agent**；开源侧 TencentDB Agent Memory 实测 token **-61%**（审查报告记录） |
| 10 | **框架内建三件套** | session 限长 + 裁剪回调 + 自动压缩；checkpoint 断点续跑；团队级 token 预算 | OpenAI Agents SDK / LangGraph / JiuwenSwarm（均 A 档项目）；Anthropic《Effective context engineering》定调三大杠杆：compaction、结构化笔记、多 agent 子代理委派 |

**组合逻辑**：缓存（杠杆 1–3）是"不损效果的免费午餐区"，应最先做；压缩与逐出（4–6）是"有精度代价的主战场"，需配 A/B 评估；路由与隔离（7–8）改变的是钱花在哪，而非花多少 token；持久化（9）针对多会话/多租户场景。

## C. 治理规范与工具链建议

**治理规范：直接采用 AWS Agentic AI Lens 成本支柱。** 注意：该 Lens 的成本能力实际为 **AGENTCOST01–07 共七项**（工作区此前仅记录了 01/02/05），本次原文确认完整结构为：01 推理与执行成本、02 模型调用与 token、03 记忆与状态成本、04 工具服务成本、05 成本可见性与归因、06 发现与部署、07 成本治理与持续优化 [1]。落地要点：

1. **预算强制（AGENTCOST01 + 07）**：每个 agent 设显式终止契约——迭代上限、会话级 token 预算、置信度提前退出；控制手段要在**控制平面强制执行**（策略引擎/网关），而非依赖 agent 自律 [2][4]。预算分层：per-cycle / per-task / per-day 三级 + 自动熔断（intelligent cutoffs），熔断优先采用**分级限流（graduated throttling）而非二元关停**，保住任务完成率 [4]。
2. **结构规范（AGENTCOST01）**：agent 层级尽量浅；handoff 用结构化 schema 消息替代完整历史转发；协作 agent 默认共享记忆而非逐次转发上下文；可确定性路由的决策不用 LLM 做监督（先做 determinism 分析）；可重复 workflow 默认 plan-then-execute [2]。
3. **监控与归因（AGENTCOST05）**：统一标签分类法（agent-id / agent-role / workflow-id / task-type / environment）打到每次调用；workflow trace ID 贯穿所有 handoff 与工具调用；看板跟踪 cost-per-reasoning-cycle、cost-per-task-completion、orchestration-to-execution 比率；多租户设配额并对"超基线 3 倍"消费告警 [3]。
4. **异常检测必须 agent 特化（AGENTCOST07）**：针对三类 agent 特有 escalation——推理循环 token 尖峰、工具调用风暴、记忆增长——在遥测指标上跑 2σ/3σ 异常检测；通用基础设施监控会漏掉它们 [4]。建立分类 runbook：不同异常类型走不同排查路径。
5. **持续优化闭环**：月度成本评审 + 优化变更经 A/B 测试验证后再全量推广 + CI/CD 中设成本门禁（cost gates）防回归 [4]。

**工具链建议**：
- **计价与计数**：`tokencost`（Python，覆盖 400+ LLM 单价，适合多厂商统一计价与成本对比，B 档）；`llm-token-counter`（TypeScript/tiktoken 精确计数，含对话格式开销，适合前端与 TS 栈）；更简的 `llm-cost`（C++ 单头文件）列为备选。三者可嵌入 CI 与运行时做 token/成本审计（评分表 B 档记录）。
- **缓存遥测**：从响应的 `usage.input_tokens_details.cached_tokens` / `cache_write_tokens` 读缓存读/写量，监控"写入高而读取低"的失效模式 [5]。
- **框架层**：优先选内建成本原语的编排栈——OpenAI Agents SDK（session 限长/裁剪/自动压缩三件套，全可配置）、LangGraph（checkpoint 断点续跑避免重跑浪费）、JiuwenSwarm（团队 token 预算为一等公民 + Dreaming 睡眠期记忆整合）、TencentDB Agent Memory（分层记忆，token -61% 实测）、Mem0 / Graphiti（记忆层避免重复注入，Graphiti 免 LLM 摘要检索）。

## D. 风险与注意事项

1. **缓存极易被上下文编辑打破**。官方铁律：breakpoint 之前的任何修改都会使该前缀失效（"A change before the breakpoint changes the prefix and will prevent a cache hit"）[5]。推论：agent 循环中对历史消息的插入/重排/时间戳注入是缓存杀手；时间戳、随机 ID 等易变内容必须移到前缀之外。
2. **缓存本身可以反噬**。GPT-5.6+ 缓存写入按 **1.25×** 计费：若 `cache_write_tokens` 持续高而 `cached_tokens` 低（隐式 breakpoint 把每轮变化的后缀反复写入），成本不降反升，应切换 explicit-only 模式 [5]。另外 Don't Break the Cache 发现朴素 full-context 缓存策略可能**反增延迟**，并非所有缓存姿势都赚。且 GPT-5.6+ 不再回退匹配最长公共前缀，不设 `prompt_cache_key` 和 breakpoint 时命中率会显著低于旧模型行为 [5]。
3. **压缩有精度悬崖，且缺乏测量**。ACM 指出粗略摘要虽把成本从二次降为线性，但触发准确率悬崖；率失真综述（2607.08032）进一步指出：agent 场景中"反复压缩"的累积信息损失至今缺乏系统测量。任何压缩/逐出上线前必须配成本-质量 A/B（对应 AGENTCOST07 的 Evaluations 要求）。
4. **位置偏差**：Lost in the Middle 系列证明相关信息落在长上下文中部时性能显著下降（U 型曲线），且压缩/剪枝可能改变关键信息位置而间接伤效果——成本-效果平衡必须同时权衡长度、位置与缓存连续性三个变量（评分表核心结论）。
5. **Swarm 特有风险**：handoff 传全历史会让协调成本随对话长度而非任务复杂度增长（AWS 列为常见问题）[2]；共享记忆存在四类失效——未授权泄漏、过期信息传播、矛盾持久化、来源崩塌（MemClaw），污染会同时损害效果并浪费 token；多租户需配额防 noisy-neighbor [3]。
6. **数字的适用边界**：FrugalGPT 的 98% 节省是上限场景且依赖质量评估器可靠性，级联还会增加延迟；CASTER/ACON 需训练或蒸馏投入；AWS 规范为原则性框架、无量化基线（审查报告已指出）；SAMEP 的 73% 冗余下降为推算值非实测（低置信）；本地记录中 TokenPilot（56–87% vs 61%/56%）与 Less Context Better Agents（79% vs 91.6%）存在口径出入，正式引用前建议核对原文。
7. **治理与自主性的张力**：预算控制不是越严越好——AWS 明确警示"把成本控制与 agent 自主性视为互斥"是常见误区，过度限制会伤任务完成率，应采用分级限流与审批工作流 [4]。

**一句话总结**：先建计量（三档计价 + 四级归因），再上缓存（前缀纪律，41–80% 成本空间），然后按任务做压缩与逐出（26–64% token 空间，须配质量 A/B），用路由决定钱花在哪（最高 72–98% 空间），最后以分层预算 + agent 特化异常检测 + CI 成本门禁收口治理。

## Sources
1. [AWS Well-Architected Agentic AI Lens – Cost optimization](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/cost-optimization.html)
2. [AWS Agentic AI Lens – AGENTCOST01 Reasoning and execution cost optimization](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentcost01.html)
3. [AWS Agentic AI Lens – AGENTCOST05 Agent cost visibility and attribution](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentcost05.html)
4. [AWS Agentic AI Lens – AGENTCOST07 Agent cost governance and continuous optimization](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentcost07.html)
5. [OpenAI – Prompt caching guide](https://developers.openai.com/api/docs/guides/prompt-caching)
