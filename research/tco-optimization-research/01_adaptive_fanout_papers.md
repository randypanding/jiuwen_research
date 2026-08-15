# 多Agent系统自适应Fan-out策略与动态N值 —— 文献清单（审查重构版）

## 审查说明
- **审查日期**：2026-08-15
- **核验方式**：对每条逐条使用 WebFetch 复核 arXiv 页面（https://arxiv.org/abs/{编号}）确认真实存在；对博客/新闻/OpenReview/GitHub-notes 等非一手来源，因无法核验为权威一手文献或主题相关性弱，予以剔除。
- **核验标准**：仅保留「确实存在且可公开核验」且与「多Agent系统自适应Fan-out、动态N值、基于不确定性的Token预算分配、验证器驱动重试、Agent扩展律」直接相关的条目；"宁缺毋滥"。
- **重点怀疑编号核验结果**：文件中原被重点怀疑（可能虚构）的 7 个编号 — 2608.03961、2605.26849、2604.14853、2603.08999、2603.11445、2602.07072、2601.23219 — 经 WebFetch 逐一核验，**全部真实存在且与主题相关，予以保留**，无一虚构。
- **剔除条目数量**：原文件 45 条中剔除 19 条（非一手来源/博客/新闻/OpenReview 笔记/主题相关性弱的条目，以及 MARS、M1-Parallel、TDAG 等主题关联度较低的 arXiv 文献）。
- **新增条目数量**：经 WebSearch 补充并经 WebFetch 核验真实存在的高质量论文 4 条。
- **最终保留**：共 30 条（原保留 26 条 + 新增 4 条）。
- **标记说明**：[R]=近三个月内（2026 年近期/近三月发布）文献；[★]=公认重要/奠基性文献。

---

## 一、自适应 Fan-out / 动态 N 值选择（采样与分支）

1. **Best-of-∞: Asymptotic Performance of Test-Time LLM Ensembling** [★]
   - 年份：2025（ICLR 2026）
   - URL: https://arxiv.org/abs/2509.21091
   - 核心思路：分析多数投票下 best-of-N 的 N→∞ 极限，提出按"答案一致性"自适应选择 N 的生成方案，效率分配推理计算，并扩展到多 LLM 加权集成。
   - 核验状态：已核验

2. **AdaBoN: Adaptive Best-of-N Alignment**
   - 年份：2025
   - URL: https://arxiv.org/abs/2505.12050
   - 核心思路：两阶段算法，先用小探索预算估计每个 prompt 的奖励分布，再按需自适应分配剩余采样预算，实现 prompt 自适应地决定 best-of-N 的 N。
   - 核验状态：已核验

3. **Adaptive Rectification Sampling for Test-Time Compute Scaling (AR-Sampling)**
   - 年份：2025
   - URL: https://arxiv.org/abs/2504.01317
   - 核心思路：用过程奖励模型(PRM)作为验证器，在自修正过程中自适应地决定在哪个步骤触发反思，动态调整 N 与 token 开销。
   - 核验状态：已核验

4. **Interpretable Adaptive Sampling for LLM Test-Time Scaling** [R]
   - 年份：2026
   - URL: https://arxiv.org/abs/2608.03961
   - 核心思路：用分级模糊控制器把复杂度、置信度、熵等可解释信号映射为每个 prompt 的整数采样预算，实现自适应 N 且可解释。
   - 核验状态：已核验

5. **Strategic Scaling of Test-Time Compute: A Bandit Learning Approach** [★]
   - 年份：2025（ICLR 2026）
   - URL: https://arxiv.org/abs/2506.12721
   - 核心思路：把跨查询的测试时计算分配建模为 bandit 学习问题，按实时估计的查询难度自适应分配计算，难题多算、易题少算。
   - 核验状态：已核验

6. **Uncertainty-Aware Budget Allocation for Adaptive Test-Time Reasoning (UAB)** [R]
   - 年份：2026
   - URL: https://arxiv.org/abs/2605.26849
   - 核心思路：两阶段凹整数优化框架，用负对数似然(ANLL)预估难度，用贪心算法把剩余采样预算分配给高不确定问题，实现自适应采样。
   - 核验状态：已核验

7. **Parallelism Meets Adaptiveness: Scalable Documents Understanding in Multi-Agent LLM Systems**
   - 年份：2025（AAAI 2026 Workshop）
   - URL: https://arxiv.org/abs/2507.17061
   - 核心思路：在文档理解多Agent系统中动态并行多个 Agent，由评估器打分挑选最优输出，将并行度(fan-out)与自适应相结合。
   - 核验状态：已核验

---

## 二、基于不确定性的 Token / 计算分配

8. **A Survey of Test-Time Compute: From Intuitive Inference to Deliberate Reasoning** [★]
   - 年份：2025
   - URL: https://arxiv.org/abs/2501.02497
   - 核心思路：系统综述测试时计算扩展，涵盖重复采样、自修正、树搜索等，阐述 System-1 到 System-2 的过渡，是自适应算力分配的基础性综述。
   - 核验状态：已核验（新增）

9. **SelfBudgeter: Adaptive Token Allocation for Efficient LLM Reasoning**
   - 年份：2025
   - URL: https://arxiv.org/abs/2505.11274
   - 核心思路：训练模型自估计问题所需推理预算，用预算引导的 GRPO 保持精度同时按难度动态分配 Token，平均压缩响应长度 61%。
   - 核验状态：已核验

10. **EAGER: Entropy-Aware GEneRation for Adaptive Inference-Time Scaling**
    - 年份：2025
    - URL: https://arxiv.org/abs/2510.11170
    - 核心思路：依据 token 级熵分布感知不确定度，仅在高熵 token 处分支到多条推理路径，把节省的预算重分配给最需要探索的实例。
    - 核验状态：已核验

11. **Learning When to Sample: Confidence-Aware Selective Sampling for Reasoning** [R]
    - 年份：2026
    - URL: https://arxiv.org/abs/2603.08999
    - 核心思路：基于句子级数值与语言特征估计置信度，自适应决定是依赖单条轨迹还是触发多路径采样，高置信接受、低置信多次运行。
    - 核验状态：已核验

12. **Seer Self-Consistency: Advance Budget Estimation for Adaptive Test-Time Scaling (SeerSC)**
    - 年份：2025
    - URL: https://arxiv.org/abs/2511.09345
    - 核心思路：用 System1 快速计算答案熵提前预估预算，再在 System2 下做动态自一致性，兼顾 token 效率与延迟。
    - 核验状态：已核验

13. **Adaptive Test-Time Compute Allocation for Reasoning LLMs via Constrained Policy Optimization** [R]
    - 年份：2026
    - URL: https://arxiv.org/abs/2604.14853
    - 核心思路：把计算分配形式化为"平均预算下最大化准确率"的约束优化，用拉格朗日松弛+二分搜索得到每实例最优计算量，训练轻量分类器在线执行。
    - 核验状态：已核验

14. **DynScaling: Efficient Verifier-free Inference Scaling via Dynamic and Integrated Sampling**
    - 年份：2025
    - URL: https://arxiv.org/abs/2506.16043
    - 核心思路：用多臂 bandit 按已采样响应的不确定性把推理预算自适应地分配到各查询，无需外部验证器即可高效扩展。
    - 核验状态：已核验

---

## 三、基于验证器 / 重试 / 自适应采样的并行

15. **Verified Multi-Agent Orchestration: A Plan-Execute-Verify-Replan Framework (VMAO)** [R]
    - 年份：2026（ICLR 2026 Workshop）
    - URL: https://arxiv.org/abs/2603.11445
    - 核心思路：LLM 验证器作为编排级信号，对 Agent 输出做完整性评估并驱动自适应重规划，配置式停止条件平衡质量与算力开销。
    - 核验状态：已核验

16. **BEACON: Bayesian Optimal Stopping for Efficient LLM Sampling**
    - 年份：2025
    - URL: https://arxiv.org/abs/2510.15945
    - 核心思路：用贝叶斯序贯搜索在线更新奖励分布后验，当继续采样的边际收益不足以覆盖成本时停止，从而确定最优 N。
    - 核验状态：已核验

17. **Adaptive Inference-Time Compute: LLMs Can Predict if They Can Do Better, Even Mid-Generation**
    - 年份：2024
    - URL: https://arxiv.org/abs/2410.02725
    - 核心思路：用生成式奖励模型让 LLM 在生成中途预测重启是否产生更好结果，据此决定多采样、早停或剪枝，无需外部奖励模型。
    - 核验状态：已核验

18. **Generative Verifiers: Reward Modeling as Next-Token Prediction (GenRM)** [★]
    - 年份：2024（ICLR 2025）
    - URL: https://arxiv.org/abs/2408.15240
    - 核心思路：把验证建模为下一 token 预测，支持 CoT 与多数投票提升验证精度，为验证器驱动的 best-of-N 选择提供坚实基础。
    - 核验状态：已核验

19. **Enhancing Large Language Model Reasoning with Reward Models: An Analytical Survey**
    - 年份：2025
    - URL: https://arxiv.org/abs/2510.01925
    - 核心思路：系统综述 ORM/PRM 在 best-of-N 采样与候选选择中的应用，是验证器选择与动态 N 设计的背景综述。
    - 核验状态：已核验

---

## 四、成本高效的多Agent编排 / Token 预算优化

20. **BAMAS: Structuring Budget-Aware Multi-Agent Systems**
    - 年份：2025（AAAI 2026 Oral）
    - URL: https://arxiv.org/abs/2511.21572
    - 核心思路：用整数线性规划在预算内选择最优 LLM 集合，用强化学习选择协作拓扑，达到成本-性能最优，成本最高降 86%。
    - 核验状态：已核验

21. **Controlling Performance and Budget of a Centralized Multi-agent LLM System with RL (CoRL)**
    - 年份：2025
    - URL: https://arxiv.org/abs/2511.02755
    - 核心思路：用双目标强化学习同时最大化性能与最小化推理成本，支持多预算条件下集中式控制器的自适应行为。
    - 核验状态：已核验

22. **Scaling Test-time Compute for LLM Agents** [★]
    - 年份：2025
    - URL: https://arxiv.org/abs/2506.12928
    - 核心思路：首个系统研究测试时扩展应用于语言 Agent 的工作，探索并行采样、顺序修订、验证器与多样性 rollout 等策略及其算力取舍。
    - 核验状态：已核验（新增）

---

## 五、Agent 扩展律（Scaling Laws）与动态Agent扩展

23. **Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters** [★]
    - 年份：2024
    - URL: https://arxiv.org/abs/2408.03314
    - 核心思路：发现不同难度 prompt 下测试时计算扩展效果迥异，提出 per-prompt compute-optimal 策略，比 best-of-N 效率提升 4 倍以上。
    - 核验状态：已核验

24. **Inference Scaling Laws: An Empirical Analysis of Compute-Optimal Inference** [★]
    - 年份：2024
    - URL: https://arxiv.org/abs/2408.00724
    - 核心思路：实证研究 greedy、majority voting、best-of-n、加权投票、树搜索等策略在模型规模与 token 预算下的成本-性能权衡。
    - 核验状态：已核验

25. **Scaling LLM Inference with Optimized Sample Compute Allocation (OSCA)**
    - 年份：2024
    - URL: https://arxiv.org/abs/2410.22480
    - 核心思路：把采样配置与样本数选择形式化为学习问题，学习最优混合分配以在有限计算下提升精度，并验证在 agentic 工作流中的有效性。
    - 核验状态：已核验

26. **Towards a Science of Scaling Agent Systems** [★]
    - 年份：2025
    - URL: https://arxiv.org/abs/2512.08296
    - 核心思路：跨 260 种配置研究 agent 数量、协调结构、模型能力与任务性质对性能的影响，揭示"多Agent并非总是更好"的扩展律。
    - 核验状态：已核验

27. **AgentSpawn: Adaptive Multi-Agent Collaboration Through Dynamic Spawning** [R]
    - 年份：2026
    - URL: https://arxiv.org/abs/2602.07072
    - 核心思路：通过运行时复杂度指标触发自适应 spawn 策略动态增加子 Agent，在 SWE-bench 上较静态基线完成率提升 34%。
    - 核验状态：已核验

28. **MonoScale: Scaling Multi-Agent System with Monotonic Improvement** [R]
    - 年份：2026
    - URL: https://arxiv.org/abs/2601.23219
    - 核心思路：提出扩展感知的自适应更新协议，使开放式多Agent系统随 Agent 池扩大而端到端性能稳定单调提升。
    - 核验状态：已核验

29. **Understanding Agent Scaling in LLM-Based Multi-Agent Systems via Diversity** [R]
    - 年份：2026
    - URL: https://arxiv.org/abs/2602.03794
    - 核心思路：信息论框架证明 MAS 扩展受内在任务不确定性而非 Agent 数量限制，异质性可提升有效通道数，2 个多样 Agent 可匹敌 16 个同质 Agent。
    - 核验状态：已核验（新增）

30. **Scaling Behavior of Single LLM-Driven Multi-Agent Systems** [R]
    - 年份：2026
    - URL: https://arxiv.org/abs/2606.00655
    - 核心思路：实证表明 MAS 性能不随 Agent 数单调提升而是回报递减，由协同增益与协调开销的权衡决定，为 MAS 扩展律提供基础理解。
    - 核验状态：已核验（新增）

---

### 附：剔除条目汇总（19 条）
- **非一手/难核验来源（16 条）**：ST-BoN（NeurIPS 论文笔记 GitHub 链接）、Anytime Verified Agents AVA（OpenReview 附件）、Adaptive Inference Scaling via Monte Carlo（OpenReview）、Know What You Don't Know IAS（nips.cc 虚拟链接）、Multi-Agent Collaboration via Evolving Orchestration（博客）、Agentic Supernet（腾讯新闻）、Maestro（OpenReview）、AgentBalance（博客）、Adaptive LLM Routing（GitHub 项目）、DSA（期刊链接）、CBDR（生物通新闻）、TestTimeScaling 机制（CSDN）、LangGraph 动态分流（CSDN）、StreamMA（掘金）、Taming the Swarm Breyta（工程博客）、ATOMiK（GitHub 文档）。
- **真实存在但主题关联度较低（3 条）**：MARS（2509.20502，固定评审架构而非自适应 fan-out）、Optimizing Sequential Multi-Step Tasks / M1-Parallel（2507.08944，并行路径而非动态 N）、TDAG（2402.10178，任务分解为主而非算力预算）。