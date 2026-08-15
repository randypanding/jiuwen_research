# 子代理建议一：上下文管理策略与方法论

> 依据：工作区 67 项精读评分成果（`精读总结与评分表.md`、`curated/` 四份审定清单、`审查报告.md`）+ 直接抓取的 9 篇 A 档论文 arXiv 原文摘要（均已核实编号、作者与量化数字）。

## A. 核心结论（5 条）

1. **上下文成本是结构性问题，不是存储问题。** ACM 论文论证：朴素累积上下文的 token 成本随对话长度**二次增长**；粗暴摘要虽把成本降为线性，但带来"准确率悬崖"；只有经过验证的压缩（validated compaction）才能同时获得线性成本与保真度 [1]。因此 swarm 系统必须在架构层（而非事后补丁）管理上下文生命周期：architecting / ingesting / scoping / anticipating / compacting 五原语 [1]。

2. **缓存是性价比最高的第一杠杆，但压缩/逐出操作必须"缓存感知"。** 跨 OpenAI/Anthropic/Google 三家、500+ 会话的实测显示：prompt caching 使 API 成本降 **41–80%**、TTFT 改善 **13–31%**；但朴素全量上下文缓存可能反而增加延迟，需把动态内容后置、排除动态工具结果 [7]。TokenPilot 进一步证明：无约束的文本剪枝/逐出会破坏前缀、导致缓存失效，"文本稀疏性 vs 缓存连续性"是需要显式管理的核心权衡，其双粒度方案在 isolated/continuous 两种模式下分别降本 **61%/56%** 和 **61%/87%** 且性能持平 [2]。

3. **"少而精的上下文"往往优于全量保留——既有成本证据也有效果证据。** 在 Microsoft Dynamics 365 企业工具调用基准上：全量历史保留只做到 71.0% 完成率（耗 148 万 token、14.56 小时）；裁剪到最近 5 次工具调用 + 自动摘要后，完成率升至 **91.6%**，token 降至 **55.3 万**（约 -63%），时长降至 5.79 小时 [4]。DACS 在 swarm 场景同样证明：orchestrator 用 Registry 摘要（每 agent ≤200 token）+ 按需 Focus 全量注入，steering 准确率 **90.0–98.4%**（扁平上下文基线仅 21.0–60.0%），跨 agent 污染从 28–57% 降至 0–14%，上下文效率比最高 **3.53×** [6]。

4. **逐出（eviction）应优先于摘要（compaction）作为常规预算控制手段。** CWL（Beyond Compaction）用类型化、依赖链接的 episode 结构 + 确定性免 LLM 逐出策略，规避摘要式压缩的四大缺陷（不可预测有损、破坏因果结构、阻塞式模型开销、压缩诱发幻觉），单会话累计 **8000 万 token 完成 89 个顺序任务，相对隔离会话无可测精度退化**，且逐出本身几乎零成本 [3]。

5. **压缩本身也要优化与蒸馏，且要与推理解耦。** ACON 以失败分析驱动、在自然语言空间迭代优化压缩准则（免微调），峰值 token 降 **26–54%** 且任务成功率超过既有压缩基线；蒸馏到小模型后还能让小 LM 作为长程 agent 性能提升最高 **46%**（代码 microsoft/acon）[5]。CoMem 则把记忆管理从主推理流程解耦，用 k-step 异步流水线掩盖摘要解码延迟，在 SWE-Bench-Verified 上相对朴素长上下文方案延迟降 **1.4×** 且保留大部分性能 [9]。

## B. 推荐的上下文管理策略组合

### B1. 缓存（优先级：P0，最先做）
| 机制 | 来源 | 量化收益 |
|---|---|---|
| 静态内容前置、动态内容后置；避免动态 function calling；把动态工具结果排除出缓存块 | Don't Break the Cache [7]；OpenAI Prompt Caching 指南/Cookbook | 成本 -41–80%、TTFT +13–31%；OpenAI 客户案例命中率 60%→87%、长 prompt TTFT 快 67% |
| 缓存友好的逐出调度：只在批量回合边界逐出、保持前缀稳定 | TokenPilot [2] | 货币支出 isolated -61%/-56%、continuous -61%/-87%，性能保持 |
| （自建推理时）KV cache 指令原语，agent 主动 splice/替换缓存片段免整段 re-prefill | Leyline 2606.01065 | cache-hit +11.2pp、延迟最多降 241ms、debug-gym 求解率 +14.3pp |

### B2. 逐出（优先级：P0，与缓存并列的常规预算闸）
| 机制 | 来源 | 量化收益 |
|---|---|---|
| 结构化 episode（typed + 依赖 DAG）+ 确定性 LLM-free 按优先序逐出；保留用户轮次与正在推理的探索上下文 | CWL / Beyond Compaction [3] | 8000 万 token / 89 任务无可测退化；避免摘要四大缺陷 |
| 残余效用监控：只在任务相关性过期时卸载内容段 | TokenPilot [2] | 56–87% 降本 |

### B3. 压缩（优先级：P1，在逐出之上做深度压缩）
| 机制 | 来源 | 量化收益 |
|---|---|---|
| 失败驱动迭代优化压缩准则 + 蒸馏小压缩器 | ACON [5] | 峰值 token -26–54%，蒸馏保留 >95% 精度，小 LM +46% |
| 逐决策步弹性三态（raw / abstract / drop）+ 无损消息层（可逆可恢复） | ACE [8] | 四框架一致优于截断与摘要基线，免训练即插即用 |
| 异步解耦压缩：记忆模型与主推理并行 | CoMem [9] | SWE-Bench-Verified 延迟 1.4×，性能大部分保留 |
| agent 自控压缩为 Knowledge 块并物理删除历史 | Focus 2601.07190 | token -22.7%、准确率持平 |
| （可选）软压缩为可缓存复用的概念嵌入 | CompLLM 2509.19228 | 2× 压缩下 TTFT 提速 4×、KV 减 50% |

### B4. 记忆分层（优先级：P1）
| 机制 | 来源 | 量化收益 |
|---|---|---|
| OS 式虚拟上下文：主上下文/外部存储分页换入换出 | MemGPT 2310.08560 | 经典范式，超窗任务可行性的基础架构 |
| ACM 五原语生命周期 | ACM [1] | 参考实现 Maximem Synap：LongMemEval 92%、LoCoMo 93.2% |
| 开源落地件：Mem0、Zep/Graphiti、TencentDB Agent Memory、LangGraph checkpoint | curated/04 | TencentDB Agent Memory 长任务 token 实测 -61% |

### B5. 注入选择 / swarm 结构（优先级：P0 对 swarm）
| 机制 | 来源 | 量化收益 |
|---|---|---|
| Orchestrator 双模式：Registry（每 agent ≤200 token 摘要）+ 触发式 Focus 全量注入 | DACS [6] | steering 准确率 90.0–98.4% vs 21.0–60.0%；污染 28–57%→0–14%；效率比最高 3.53× |
| 子执行体只保留最近 5 次工具调用 + 自动摘要 | Less Context, Better Agents [4] | token -63%、完成率 71%→91.6%、时长 14.56h→5.79h |
| Planner 精简战略上下文 + Executor 隔离工作区 | CoDA 2512.12716（WSDM'26 Oral） | 多跳 QA 最高 +6.0% |
| RL 学"最小充分证据子集"：max U(S) − λ·Len(S) s.t. Token≤B | Context-Picker 2512.14465 | 4/5 基准超过强 RAG 基线 |
| 按子任务难度路由模型 | CASTER、FrugalGPT | CASTER -72.4% 成本且成功率相当；FrugalGPT 最高省 98% |
| swarm 编排件：OpenAI Agents SDK、JiuwenSwarm | curated/04 | 工程即用 |

**组合公式（一句话）**：缓存连续性打底（Don't Break the Cache + TokenPilot）→ 结构化逐出控预算（CWL）→ 失败驱动压缩 + 弹性三态做深度压缩（ACON + ACE）→ swarm 层 Registry/Focus 隔离注入（DACS）+ 子 agent 近窗裁剪（Less Context）→ 跨会话记忆分层外置（MemGPT 范式 + Mem0/Graphiti）。

## C. 分阶段落地路线图

**阶段 0：度量先行（1 周内）**
- 用 tokencost / llm-token-counter 给每次 agent 调用记账：输入/输出/缓存命中 token、每任务成本、上下文长度曲线。
- 按 AWS Agentic AI Lens 的 AGENTCOST01/02/05 建审计口径。
- 验收：能回答"每条会话的成本-长度曲线是否呈二次增长"（ACM 预警）。

**阶段 1：缓存纪律（1–2 周，收益最快）**
- 静态 system prompt/工具定义前置、动态工具结果后置或排除出缓存块。
- 用 OpenAI 官方战术（allowed_tools、prompt_cache_key、读 cached_tokens）把命中率拉高（官方案例 60%→87%）。
- 预期：API 成本 -41–80%、TTFT +13–31%。

**阶段 2：预算化逐出（2–4 周）**
- 引入 CWL 式 episode 标注 + 依赖图 + 确定性逐出循环：设定活跃上下文上限，超预算时按"最旧且最可恢复"优先逐出。
- 逐出调度对齐批量回合边界，避免破坏缓存前缀。
- 预期：上下文稳定在天花板附近，逐出零模型成本；叠加后总体货币支出可再降约 56–87%（TokenPilot 口径）。

**阶段 3：压缩升级与 swarm 注入治理（1–2 个月）**
- 单 agent：ACE 弹性三态替代硬截断；ACON 失败驱动准则优化并蒸馏小压缩器；CoMem 异步解耦（摘要延迟敏感时）。
- Swarm：orchestrator 改造为 DACS 双模式；子 agent 采用"最近 5 次工具调用 + 摘要"窗口。
- 预期：swarm steering 准确率 +30pp 以上、污染趋零；子 agent token -63% 且完成率 +20pp。

**阶段 4：记忆分层与长期化（持续）**
- 跨会话事实/偏好外置到记忆层（Mem0 / Graphiti / TencentDB Agent Memory 按场景四选一），主上下文只留"当前最小高信号集"（Anthropic 指南原则）。
- 长任务用 checkpoint（LangGraph）断点续跑。
- 按难度路由模型（CASTER/FrugalGPT 思路）再削一层单价。
- 复审节奏：每季度对照新论文重估策略。

## D. 适用场景与风险注意事项

**适用场景差异**
- 短会话 / 单 agent（<50 轮）：阶段 0+1 通常足够。
- 长程单 agent（数百轮工具调用）：重点在阶段 2/3 的逐出+压缩。
- Agent swarm / orchestrator 型：阶段 3 的 DACS 式隔离注入是关键，N 与决策密度越大收益越大。
- 企业工具密集型（冗长工具响应）：Less Context 的近窗裁剪+摘要证据最直接。
- 自建推理服务：才值得投入 Leyline / Agent Memory Below the Prompt 类引擎层 KV 手段。

**风险与注意事项**
1. **粗暴摘要有准确率悬崖**：压缩必须可验证/可逆优先。
2. **压缩与缓存互斥风险**：任何改变序列布局的剪枝/摘要都会造成前缀失配、缓存失效。
3. **位置偏差**：Lost in the Middle 系列证明中间位置信息利用率低，"塞满上下文≠更准"。
4. **朴素全量缓存可能反噬**：必须 A/B 验证后选定缓存块策略。
5. **跨 agent 污染是隐性成本**：扁平共享上下文下错误 agent 污染可达 28–57%；共享记忆还需治理（MemClaw 四类失效）。
6. **摘要的重复压缩代价未被充分测量**：长会话要监控"压缩-再压缩"的累积失真。
7. **数据边界**：量化数字来自各论文自报基准，与业务负载可能不一致；DACS 仅 200 次试验、preprint 状态；上线前建议在自有任务集复测。
8. **弃用警示**：OpenAI Swarm 已弃用，新项目用 Agents SDK。

## Sources

1. Agentic Context Management (ACM), arXiv:2607.21503 — https://arxiv.org/abs/2607.21503
2. TokenPilot, arXiv:2606.17016 — https://arxiv.org/abs/2606.17016
3. Beyond Compaction (CWL), arXiv:2606.11213 — https://arxiv.org/abs/2606.11213
4. Less Context, Better Agents, arXiv:2606.10209 — https://arxiv.org/abs/2606.10209
5. ACON, arXiv:2510.00615 — https://arxiv.org/abs/2510.00615
6. DACS, arXiv:2604.07911 — https://arxiv.org/abs/2604.07911
7. Don't Break the Cache, arXiv:2601.06007 — https://arxiv.org/abs/2601.06007
8. ACE, arXiv:2606.31564 — https://arxiv.org/abs/2606.31564
9. CoMem, arXiv:2605.30842 — https://arxiv.org/abs/2605.30842
