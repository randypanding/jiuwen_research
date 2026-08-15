# LLM-as-a-Judge 学术论文材料索引（审查后）

> 审查日期：2026-08-15。收录标准：更新时间在 2026-05-15 之后（近三个月），或具有重大意义/高影响力的经典论文。已逐条核实链接真实性。
> 本次审查修正：Auto-J 链接错误、LLMBar 标题校正，并补充 9 篇 2026 年 5-8 月新论文。

## 一、奠基性论文

| # | 标题 | 作者/机构 | 年份 | 链接 | 一句话摘要 |
|---|------|-----------|------|------|-----------|
| 1 | Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena | Lianmin Zheng 等（UC Berkeley / LMSYS） | 2023 | https://arxiv.org/abs/2306.05685 | 奠基之作，系统分析位置/冗长/自我增强偏差并提出缓解，引入 MT-Bench 与 Chatbot Arena，NeurIPS 2023。 |
| 2 | G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment | Yang Liu 等（Microsoft） | 2023 | https://arxiv.org/abs/2303.16634 | 用带 CoT 的 GPT-4 以"填表"范式评估 NLG 输出，EMNLP 2023。 |
| 3 | Self-Rewarding Language Models | Weizhe Yuan 等（Meta AI / NYU） | 2024 | https://arxiv.org/abs/2401.10020 | 模型自身通过 LLM-as-a-Judge 提示提供训练奖励，迭代 DPO，ICML 2024 里程碑。 |
| 4 | JudgeLM: Fine-tuned Large Language Models are Scalable Judges | Lianghui Zhu 等 | 2023 | https://arxiv.org/abs/2310.17631 | 微调开源 LLM 作可扩展 judge，分析位置/知识/格式偏差，ICLR 2025。 |
| 5 | Prometheus: Inducing Fine-grained Evaluation Capability in LLMs | Seungone Kim 等（KAIST） | 2023 | https://arxiv.org/abs/2310.08491 | FEEDBACK COLLECTION 数据集 + 13B 评估模型，ICLR 2024。 |
| 6 | Prometheus 2: An Open Source LM Specialized in Evaluating Other LMs | Seungone Kim 等（KAIST） | 2024 | https://arxiv.org/abs/2405.01535 | 同时支持直接评分与成对排序两种模式，EMNLP 2024。 |
| 7 | Prometheus-Vision: VLM as a Judge for Fine-Grained Evaluation | Seongyun Lee 等（KAIST / NAVER） | 2024 | https://arxiv.org/abs/2401.06591 | 首个开源视觉语言评估模型。 |
| 8 | FollowBench: A Multi-level Fine-grained Constraints Following Benchmark | Yuxin Jiang 等（NUS） | 2023 | https://arxiv.org/abs/2310.20410 | 多级细粒度约束遵循基准，ACL 2024。 |
| 9 | Generative Judge for Evaluating Alignment (Auto-J) | Junlong Li, Pengfei Liu 等（上海交大） | 2023 | https://arxiv.org/abs/2310.05470 | 生成式 judge，同时支持成对比较与单点评分。已修正正确链接。 |

## 二、系统性综述（2024-2026）

| # | 标题 | 年份 | 链接 | 一句话摘要 |
|---|------|------|------|-----------|
| 10 | A Survey on LLM-as-a-Judge | 2024 | https://arxiv.org/abs/2411.15594 | 全面综述，形式化定义与分类，聚焦构建可靠判官系统，v6 (2025)。 |
| 11 | From Generation to Judgment: Opportunities and Challenges of LLM-as-a-judge | 2024 | https://arxiv.org/abs/2411.16594 | 沿"评判什么/如何评判/如何基准测试"构建系统分类，EMNLP 2025。 |
| 12 | When AIs Judge AIs: The Rise of Agent-as-a-Judge Evaluation for LLMs | 2025 | https://arxiv.org/abs/2508.02994 | 综述 Agent-as-a-Judge 新范式（单作者短综述，影响力有限，优先级最低）。 |

## 三、经典与近期方法（2023-2026）

| # | 标题 | 年份 | 链接 | 一句话摘要 |
|---|------|------|------|-----------|
| 13 | Evaluating Large Language Models at Evaluating Instruction Following (LLMBar) | 2024 | https://arxiv.org/abs/2310.07641 | 元评估基准，测试判官能否识别欺骗性输出，ICLR 2024。已校正正式标题。 |
| 14 | Judging the Judges: A Systematic Investigation of Position Bias | 2024 | https://arxiv.org/abs/2406.07791 | 9 个 judge 在 22 个任务上的位置偏差系统研究，AACL-IJCNLP 2025。 |
| 15 | Self-Taught Evaluators: Improving Data Efficiency | 2024 | https://arxiv.org/abs/2408.02666 | 用合成数据迭代自训练评估器，无需人类标注。 |
| 16 | JudgeLRM: Large Reasoning Models as a Judge | 2025 | https://arxiv.org/abs/2504.00050 | RL 训练面向评估的推理模型，推理判官代表工作。 |
| 17 | JudgeBench: A Benchmark for Evaluating LLM-based Judges | 2024 | https://arxiv.org/abs/2410.12784 | 覆盖知识/推理/数学/代码的判官基准，ICLR 2025。 |
| 18 | The Alternative Annotator Test for LLM-as-a-Judge | 2025 | https://arxiv.org/abs/2501.10970 | alt-test 统计程序，证明 LLM 标注可替代人类。 |
| 19 | Reasoning Model Is Superior LLM-Judge, Yet Suffers from Biases | 2026 | https://arxiv.org/abs/2601.03630 | 比较推理模型与非推理 LLM 判官，提出 PlanJudge，ACL 2026 EvalEval。 |
| 20 | M-Prometheus: A Suite of Open Multilingual LLM Judges | 2025 | https://arxiv.org/abs/2504.04953 | 3B-14B 多语言开源 judge 系列（Unbabel）。 |
| 21 | LLMs Cannot Reliably Judge (Yet?): Robustness Assessment | 2025 | https://arxiv.org/abs/2506.09443 | 评估判官在对抗攻击/提示模板/模型选择下的鲁棒性。 |
| 22 | Time To Impeach LLM-as-a-Judge: Programs are the Future (PAJAMA) | 2025 | https://arxiv.org/abs/2506.10403 | 程序化判官替代直接评分，降低成本提升可靠性。 |
| 23 | The Silent Judge: Unacknowledged Shortcut Bias in LLM-as-a-Judge | 2025 | https://arxiv.org/abs/2509.26072 | 揭示未言明的捷径偏差，CoT 理由掩盖真实决策，NeurIPS 2025 Workshop。 |
| 24 | PandaLM: Automatic Evaluation Benchmark for LLM Instruction Tuning | 2023 | https://arxiv.org/abs/2306.05087 | 7B 模型达到 GPT-3.5 评估能力的 93.75%，ICLR 2024。 |
| 25 | Evaluating LLM Performance via Debates | 2024 | https://arxiv.org/abs/2406.11044 | LLM 辩论 + judge 评分自动排名。 |
| 26 | ChatEval: Towards Better LLM-based Evaluators through Multi-Agent Debate | 2023 | https://arxiv.org/abs/2308.07201 | 多智能体评审团，自主讨论评估回答质量。 |

## 四、2026 年新增（2026-05-15 之后发布）

| # | 标题 | 机构 | 发布日期 | 链接 | 一句话摘要 |
|---|------|------|---------|------|-----------|
| 27 | Reliability without Validity: A Systematic, Large-Scale Evaluation of LLM-as-a-Judge Models | Justin D. Norman 等 | 2026-06-17 | https://arxiv.org/abs/2606.19544 | 迄今最大规模判官元评估：21 判官 × 9 供应商 × ~54 万次判定，揭示"κ 通缩"、重测一致性与位置偏差悖论。 |
| 28 | LongJudgeBench: Benchmarking LLM-as-a-Judge for Long-Form Output Evaluation | 清华大学 | 2026-06-01 | https://arxiv.org/abs/2606.01629 | 首个长文本输出判官元评估基准（候选输出均 ~9250 token），发现判官跨场景不稳定。 |
| 29 | RankJudge: A Multi-Turn LLM-as-a-Judge Synthetic Benchmark Generator | 多机构 | 2026-05-20 | https://arxiv.org/abs/2605.21748 | 多轮对话判官合成基准生成器，逐轮注缺陷并用 Bradley-Terry 排名评估 21 个判官模型。 |
| 30 | Generating and Refining Dynamic Evaluation Rubrics for LLM-as-a-Judge | 多机构 | 2026-05-28 | https://arxiv.org/abs/2605.30568 | 无需人工标注自动生成细粒度动态 rubric，微调 14B 生成器优于大型闭源模型。 |
| 31 | Mitigating Scoring Bias in LLM-as-a-Judge via Random Number Generation | JAIST | 2026-08-06 | https://arxiv.org/abs/2608.05726 | 通过随机数生成 token 量化并修正判官打分偏差，4 任务上优于此前校准方法。 |
| 32 | A Consensus-Based Framework for Relative Preference Evaluation of LLMs | Mohtashim Khan | 2026-07-19 | https://arxiv.org/abs/2607.21632 | 多 LLM 盲评投票的共识式相对偏好评估框架，"相对智能指数 (RII)" 聚合跨领域偏好。 |
| 33 | CodeJudgeBench: Benchmarking LLM-as-a-Judge for Coding Tasks | 新加坡国立大学 | 2026-07 | https://aclanthology.org/2026.acl-long.888/ | ACL 2026 正式论文：代码判官元评估基准，小推理模型可超越非推理大模型，对顺序/变量名不稳定。 |
| 34 | Style Wins, Substance Loses: A Diagnosis of LLM-as-Judge in Idea Generation | 多机构 | 2026-08 | https://arxiv.org/html/2608.01666v1 | 诊断判官在创意生成中重风格轻实质的偏差，提出 SciStyleExtractor 偏置控制。 |
| 35 | Human-in-the-Loop Nugget Annotation for Accountable LLM-as-a-Judge Evaluations | 多机构 | 2026-06 | https://arxiv.org/pdf/2606.29033v2 | 针对判官"橡皮图章效应"提出人机协同 nugget 标注提升可追责性。 |

> 审查结论：现有 26 篇均因重大意义保留（无整体剔除）；修正了 Auto-J 链接 (→2310.05470) 与 LLMBar 标题。新增 9 篇均发布于 2026-05-15 之后。部分 2026 预印本需注意同行评审状态。