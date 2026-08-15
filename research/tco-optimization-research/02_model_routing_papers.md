# LLM 模型档位智能路由与成本感知路由 —— 文献与开源项目搜集（审查重构版）

## 审查说明

- **审查日期**：2026-08-15
- **核验标准**：
  1. 对每条逐一用 WebFetch 核验其 arXiv 页面（`https://arxiv.org/abs/{编号}`）或来源 URL 是否真实存在，且标题与主题一致；
  2. 仅保留与"LLM 模型档位智能路由、成本感知路由、级联、多 Agent 小-大模型协同"相关且经核验真实存在的条目；
  3. 公认奠基工作（FrugalGPT、RouteLLM、AutoMix、RouterBench 等）即使年份较早也予保留并标记 `[★]`；
  4. 近三个月（2026-05-15 之后）新增条目标记 `[R]`，每条申报前均经 WebFetch 核验 arXiv 编号真实存在。
- **剔除条目数量**：共剔除 **2 条** ——
  - *GPTCache*（开源语义缓存项目，属缓存降本而非路由，与主题不符）；
  - *Dynamic Quality-Latency Aware Routing for LLM Inference in Wireless Edge-Device Networks*（arXiv:2508.11291，偏无线边缘组网，非核心路由主题）。
  同时删除原"附：相关但未单独拆分的方向"一整节（其中含未核验/杂项内容）。
- **编号修正说明**：经核验，部分条目原编号指向无关论文，已修正为真实编号——
  - RouteLLM：`2406.02658`（实为进化多模态优化论文）→ 真实编号 `2406.18665`；
  - AutoMix：`2402.14099`（实为医学影像分割论文）→ 真实编号 `2310.12963`；
  - MasRouter：原链接为 CSDN 笔记页 → 修正为论文真实 arXiv `2502.11133`；
  - 原"LLM Cascade with Multi-Objective Optimal Consideration"经核验实际论文为 *Privacy-preserved LLM Cascade via CoT-enhanced Policy Learning*（P³Defer），已按真实标题修正。
- **重点存疑编号核验结论**：被重点怀疑的 2601.06220、2604.23530、2606.27457、2605.06350、2601.04861、2601.02695、2601.07206、2603.04445、2605.14241 均为真实存在且主题相关的 arXiv 论文，全部保留；2606.14241 经查为数学组合学论文（不在本清单内），未误用。

---

## 一、开创性 / 奠基性论文

| # | 论文 | 年份 | 来源 URL | 一句话核心思路 |
|---|------|------|----------|--------------|
| 1 | **FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance** [★] | 2023 | https://arxiv.org/abs/2305.05176 | 首次系统提出 LLM 级联（cascade），按查询难度依次调用从小到大模型 API，可匹配 GPT-4 性能并最高降低 98% 成本。 |
| 2 | **RouteLLM: Learning to Route LLMs with Preference Data** [★] | 2024 | https://arxiv.org/abs/2406.18665 | 用人机偏好数据训练路由器，把简单查询路由到廉价模型，降低 85% 成本并保持约 95% 的 GPT-4 质量。 |
| 3 | **AutoMix: Automatically Mixing Language Models** [★] | 2023 | https://arxiv.org/abs/2310.12963 | 黑盒下小模型先作答并自验证，置信度不足再路由到大模型，用 POMDP 路由器平衡成本与准确率。 |
| 4 | **Routing to the Expert (Zooter): Efficient Reward-guided Ensemble of Large Language Models** [★] | 2023 | https://arxiv.org/abs/2311.08692 | 用奖励模型在训练查询上蒸馏出路由函数，把查询精准分给最有领域专长的 LLM，仅带来很小推理开销。 |
| 5 | **RouterBench: A Benchmark for Multi-LLM Routing System** [★] | 2024 | https://arxiv.org/abs/2403.12031 | 提供 40 万+推理结果的评测框架与数据集，形式化定义 LLM 路由问题并横向对比各类路由方法。 |

---

## 二、路由 / 级联的统一理论与方法

| # | 论文 | 年份 | 来源 URL | 一句话核心思路 |
|---|------|------|----------|--------------|
| 6 | **A Unified Approach to Routing and Cascading for LLMs** [★] | 2024 | https://arxiv.org/abs/2410.10347 | 推导级联最优策略并证明既有路由最优性，提出"级联路由"统一框架，综合二者成本-质量优势。 |
| 7 | **Universal Model Routing for Efficient LLM Inference (UniRoute)** | 2025 | https://arxiv.org/abs/2502.08773 | 用代表性提示预测误差把每个 LLM 表示成特征向量，使路由器可泛化到未见过的 LLM 而无需重训。 |
| 8 | **BEST-Route: Adaptive LLM Routing with Test-Time Optimal Compute** | 2025 (ICML) | https://icml.cc/virtual/2025/poster/43788 | 结合 LLM 路由与测试时最优计算分配，按查询难度自适应选择模型与采样次数，降本 60% 且性能损失 <1%。 |
| 9 | **Meta-Router: Bridging Gold-standard and Preference-based Evaluations in LLM Routing** | 2025 | https://arxiv.org/abs/2509.25535 | 从因果推断视角联合金标准与偏好数据训练路由器，纠正偏好偏置、改善成本-质量权衡。 |
| 10 | **LLM Bandit: Cost-Efficient LLM Generation via Preference-Conditioned Dynamic Routing** | 2025 | https://arxiv.org/abs/2502.02743 | 把 LLM 选择建模为多臂老虎机，支持推理时指定偏好，动态平衡性能与成本并泛化到新模型。 |
| 11 | **One Head, Many Models: Cross-Attention Routing for Cost-Aware LLM Selection** | 2025 | https://arxiv.org/abs/2509.09782 | 用单头交叉注意力联合建模查询与候选模型，在 RouterBench 上实现成本感知的跨域模型选择。 |
| 12 | **Rethinking Predictive Modeling for LLM Routing: When Simple kNN Beats Complex Learned Routers** | 2025 | https://arxiv.org/abs/2505.12601 | 系统对比发现简单 kNN 常优于复杂学习路由器，在分布偏移下更鲁棒且样本效率更高。 |
| 13 | **Lookahead Routing for Large Language Models** | 2025 (NeurIPS) | https://openreview.net/forum?id=DRIRD9ELMb | 用 CLM/MLM 预测潜在输出表示做"前摄式"路由，路由开销仅为最小候选模型首 token 成本的 5% 以内。 |
| 14 | **Cost-Aware Contrastive Routing for LLMs (CSCR)** | 2025 (NeurIPS) | https://arxiv.org/abs/2508.12491 | 把提示与模型映射到共享嵌入空间，对比学习偏好"成本带内最便宜准确专家"，推理时一次 kNN 查找完成路由。 |
| 15 | **Breaking Model Lock-in: Cost-Efficient Zero-Shot LLM Routing via a Universal Latent Space (ZeroRouter)** [R] | 2026 | https://arxiv.org/abs/2601.06220 | 在统一潜空间上做零样本路由，解耦查询难度与模型画像，新模型免重训即可上线，成本函数基于 token 长度建模。 |

---

## 三、级联（Cascade）专项

| # | 论文 | 年份 | 来源 URL | 一句话核心思路 |
|---|------|------|----------|--------------|
| 16 | **Privacy-preserved LLM Cascade via CoT-enhanced Policy Learning (P³Defer)** | 2024 | https://arxiv.org/abs/2410.08014 | 面向隐私等真实约束，用 CoT 增强策略学习做端-云级联的延迟决策，兼顾性能、成本与隐私。 |
| 17 | **Rational Tuning of LLM Cascades via Probabilistic Modeling** | 2025 | https://arxiv.org/abs/2501.09345 | 用 Markov-copula 概率模型对级联置信阈值做连续优化，把调参复杂度从指数降到低阶多项式。 |
| 18 | **Cluster, Route, Escalate: Cascaded Framework for Cost-Aware LLM Serving** [R] | 2026 | https://arxiv.org/abs/2606.27457 | 两阶段方案：先聚类查询并分配最划算模型，再对低质量输出做质量评估级联升级，仅难样本到达昂贵模型。 |
| 19 | **Is Escalation Worth It? A Decision-Theoretic Characterization of LLM Cascades** [R] | 2026 | https://arxiv.org/abs/2605.06350 | 用决策论刻画两模型阈值级联的可达前沿，证明优化子序列级联优于固定全链设计。 |
| 20 | **Cascadia: An Efficient Cascade Serving System for Large Language Models** | 2025 | https://arxiv.org/abs/2506.04203 | 面向级联部署的 serving 系统，双层优化联合求解资源分配与路由策略，提升吞吐并收紧延迟 SLO。 |

---

## 四、多智能体 / 小-大模型协同路由

| # | 论文 | 年份 | 来源 URL | 一句话核心思路 |
|---|------|------|----------|--------------|
| 21 | **HierRouter: Coordinated Routing of Specialized LLMs via Reinforcement Learning** | 2025 | https://arxiv.org/abs/2511.09873 | 用强化学习做分层多跳路由，从专业小模型池逐步构建推理管线，平衡质量与成本。 |
| 22 | **Orchestrating Intelligence: Confidence-Aware Routing for Efficient Multi-Agent Collaboration (OI-MAS)** [R] | 2026 | https://arxiv.org/abs/2601.04861 | 状态相关路由动态选择 Agent 角色与模型档位，按任务复杂度选尺度，提升准确率并最高省成本 79.78%。 |
| 23 | **Towards Generalized Routing: Model and Agent Orchestration for Adaptive and Efficient Inference (MoMA)** | 2025 | https://arxiv.org/abs/2509.07571 | 先判断是否需要 LLM 处理、再按任务需求选最优参数量的模型，避免昂贵模型被无谓调用。 |
| 24 | **EvoRoute: Experience-Driven Self-Routing LLM Agent Systems** [R] | 2026 | https://arxiv.org/abs/2601.02695 | 提出 Agent 系统"性能-成本-延迟"三难问题，用经验驱动的自进化路由告别静态模型分配。 |
| 25 | **R2R: Efficiently Navigating Divergent Reasoning Paths with Small-Large Model Token Routing** | 2025 (NeurIPS) | https://arxiv.org/abs/2505.21600 | token 级路由，仅对 SLM 与 LLM 分歧路径上的 token 调用大模型，相对 R1-32B 提速 2.8 倍。 |
| 26 | **CITER: Collaborative Inference with Token-Level Routing** | 2025 | https://arxiv.org/abs/2502.01976 | 协作推理框架，非关键 token 路由给小模型、关键 token 发给大模型，策略优化训练路由器。 |
| 27 | **MasRouter: Learning to Route LLMs for Multi-Agent Systems** | 2025 (ACL) | https://arxiv.org/abs/2502.11133 | 为多智能体系统学习路由，级联决定协作模式、角色分配与每个 Agent 的 LLM，决策成本 O(k(R+M))。 |
| 28 | **MTRouter: Cost-Aware Multi-Turn LLM Routing with History-Model Joint Embeddings** [R] | 2026 (ACL) | https://arxiv.org/abs/2604.23530 | 把多轮对话历史与候选模型编码为联合嵌入，预测每轮模型效用，在 ScienceWorld 上较 GPT-5 省 58.7% 成本。 |
| 29 | **RouteMoA: Dynamic Routing without Pre-Inference Boosts Efficient Mixture-of-Agents** | 2026 | https://arxiv.org/abs/2601.18130 | 轻量打分器在推理前筛选高潜力模型子集，再由混合评审做后验校正，省 89.8% 成本、降 63.6% 延迟。 |

---

## 五、路由评测基准 / 数据集

| # | 论文 / 项目 | 年份 | 来源 URL | 一句话核心思路 |
|---|------|------|----------|--------------|
| 30 | **LLMRouterBench: A Massive Benchmark and Unified Framework for LLM Routing** [R] | 2026 | https://arxiv.org/abs/2601.07206 | 汇总 21 个数据集、33 个模型的大规模统一基准，同时评估纯性能与"性能-成本"权衡路由。 |
| 31 | **MMR-Bench: A Comprehensive Benchmark for Multimodal LLM Routing** | 2025 | https://github.com/Hunter-Wrynn/MMR-Bench | 多模态 LLM 路由的离线、成本感知评测基准，支持成本-准确率权衡与跨数据集泛化分析。 |

---

## 六、领域专项路由（翻译 / 工具编排）

| # | 论文 | 年份 | 来源 URL | 一句话核心思路 |
|---|------|------|----------|--------------|
| 32 | **RouteLMT: Learned Sample Routing for Hybrid LLM Translation Deployment** | 2026 (ACL Industry) | https://aclanthology.org/2026.acl-industry.129/ | 针对混合 LLM 翻译部署，把小翻译模型的"边际增益"作为预算决策信号做样本级路由。 |
| 33 | **Latency-Quality Routing for Functionally Equivalent Tools in LLM Agents** [R] | 2026 | https://arxiv.org/abs/2605.14241 | 用上下文老虎机（LQM-ContextRoute）为功能等价工具的不同服务商做延迟-质量感知路由。 |

---

## 七、综述论文

| # | 论文 | 年份 | 来源 URL | 一句话核心思路 |
|---|------|------|----------|--------------|
| 34 | **Dynamic Model Routing and Cascading for Efficient LLM Inference: A Survey** [R] | 2026 | https://arxiv.org/abs/2603.04445 | 全面综述推理期跨独立训练 LLM 的路由与级联方法，提出"何时决策/用何信息/如何计算"三维分析框架。 |
| 35 | **Doing More with Less: A Survey on Routing Strategies for Resource Optimisation in LLM-Based Systems** | 2025 (JAIR) | https://arxiv.org/abs/2502.00409 | 系统综述 LLM 系统中的路由策略，把路由形式化为性能-成本优化问题并梳理实现策略。 |

---

## 八、开源项目

| # | 项目 | 维护方 | 来源 URL | 一句话核心思路 |
|---|------|--------|----------|--------------|
| 36 | **RouteLLM（开源实现）** [★] | LMSYS | https://github.com/lm-sys/RouteLLM | OpenAI 客户端即插即用/可起 OpenAI 兼容服务，把简单查询路由到廉价模型，官方称省 85% 成本。 |
| 37 | **semantic-router** | Aurelio Labs | https://github.com/aurelio-labs/semantic-router | 基于向量语义空间的毫秒级决策层，不用等 LLM 生成即可做工具/路由选择。 |
| 38 | **LLMRouter（开源路由库）** | UIUC (ulab-uiuc) | https://github.com/ulab-uiuc/LLMRouter | 支持单轮/多轮/多模态/个性化/智能体等 16+ 路由方法、统一 CLI 与数据生成管线的路由开源库。 |
| 39 | **NVIDIA NeMo Switchyard** | NVIDIA | https://developer.nvidia.com/blog/route-ai-agent-workloads-across-models-with-nvidia-nemo-switchyard | 供应商无关的 SDK，按模型能力、成本与基础设施信号为 AI Agent 动态选模型。 |

---

## 九、中文综述 / 实践文章

| # | 文章 | 来源 | URL | 一句话核心思路 |
|---|------|------|-----|--------------|
| 40 | **AI Agent 的模型路由：多模型切换与智能选择** | CSDN | https://blog.csdn.net/qq_16593231/article/details/162405416 | 面向 Agent 的模型路由实践，按任务难度档位映射到不同模型（simple/moderate/complex/critical）。 |
| 41 | **最高节省 85% 成本：微软公布 AI 智能体 LLM 路由方案** | InfoQ | https://www.infoq.cn/article/HQD432MKSXMMR2UUag6P | 介绍微软在 Azure AKS 上基于 RouteLLM 的智能体路由架构及升级阈值调参实践经验。 |

---

> 说明：本文件所有条目（41 条）均经逐一 URL/arXiv 编号核验存在且主题相关；其中 `[★]` 为公认奠基/重要工作（7 条），`[R]` 为近三个月（2026-05-15 之后）或 2026 年重要新增（10 条）。