# LLM-as-a-Judge 最佳实践资料索引（审查后）

> 审查日期：2026-08-15。收录标准：最近三个月（2026-05-15 后）更新/发布，或具有重大权威性/参考价值的官方文档与基准。已逐条核实链接与时效。
> 本次审查：剔除 3 条（1 条链接失效、2 条过时非权威），补充 6 条 2026 年新资料。

## 一、官方文档与厂商技术博客

| # | 标题 | 来源 | 链接 | 概述 |
|---|------|------|------|------|
| 1 | Evaluation best practices | OpenAI | https://developers.openai.com/api/docs/guides/evaluation-best-practices | 区分基准/数值指标/LLM-as-a-Judge，如何设计 evals。 |
| 2 | Custom LLM-as-a-Judge | OpenAI Cookbook | https://github.com/openai/openai-cookbook/blob/main/examples/Custom-LLM-as-a-Judge.ipynb | 1-10 分对比评分示例。 |
| 3 | Prompt Migration Guide（判官 prompt 模板） | OpenAI Cookbook | https://github.com/openai/openai-cookbook/blob/main/examples/Prompt_migration_guide.ipynb | 广为流传的判官模板：避免位置偏见、不因长度影响等。 |
| 4 | Using Evals API on Image Inputs | OpenAI Cookbook | https://cookbook.openai.com/examples/evaluation/use-cases/evalsapi_image_inputs | 图像输入的结构化 grading 步骤。 |
| 5 | Demystifying evals for AI agents | Anthropic | https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents | 单轮 vs 多轮评估、Agent 场景评估逻辑。 |
| 6 | Evaluating Single LLM Outputs With Vertex AI | Google | https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/6-ai-evaluation/evaluating-single-llm-outputs-with-vertex-ai-evaluation | Vertex AI Evaluation 单输出评估。 |
| 7 | Google ADK Docs: Criteria / LLM Judge | Google ADK | http://google.github.io/adk-docs/evaluate/criteria/index.md | 判官 LLM 按参考答案评定，多次采样 + 多数投票。 |
| 8 | Implement LLM-as-judge for multi-agent systems | Microsoft | https://learn.microsoft.com/en-us/training/modules/aaai-design-evaluation-frameworks-multi-agent-azure/3-implement-model-judge-multi-agent-evaluation | Azure 多智能体判官评估。 |
| 9 | Azure AI Foundry 安全评估透明度说明 | Microsoft | https://learn.microsoft.com/zh-cn/azure/ai-foundry/concepts/safety-evaluations-transparency-note | 安全评估如何评估仇恨/暴力/越狱等。 |
| 10 | Red teaming | Microsoft | https://github.com/MicrosoftDocs/azure-ai-docs/blob/main/articles/foundry-classic/openai/concepts/red-teaming.md | 红队测试作为负责任开发最佳实践。 |

## 二、评测框架官方文档与博客

| # | 标题 | 来源 | 链接 | 概述 |
|---|------|------|------|------|
| 11 | Introduction to LLM Evaluation Metrics | DeepEval | https://deepeval.com/docs/metrics-introduction | 预置指标基于 LLM-as-a-Judge，G-Eval/DAG/QAG。 |
| 12 | LLM-as-a-Judge in 2026: Top techniques and best practices | DeepEval | https://deepeval.com/blog/llm-as-a-judge | 对比 G-Eval/DAG/QAG 三大判官技术。 |
| 13 | LLM as a Judge | Promptfoo | https://www.promptfoo.dev/docs/guides/llm-as-a-judge/ | 生产判官模型选用建议，能力不低于被测模型。 |
| 14 | LLM Evaluation Metrics: Measuring What Matters | LangChain | https://www.langchain.com/resources/llm-evaluation-metrics | 评估器分类：参考/无参考/LLM-as-judge/代码函数。 |

## 三、评测基准 Benchmark 与榜单

| # | 名称 | 来源 | 链接 | 概述 |
|---|------|------|------|------|
| 15 | Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena | arXiv | https://arxiv.org/pdf/2306.05685.pdf | 奠基论文，MT-Bench + Chatbot Arena。 |
| 16 | AlpacaEval | Stanford | https://github.com/tatsu-lab/alpaca_eval | LLM 判官计算 Win Rate，含 2.0 与排行榜。 |
| 17 | Arena-Hard and BenchBuilder Pipeline | arXiv | https://arxiv.org/html/2406.11939v1 | 高难度基准 + BenchBuilder 流水线，验证判官质量指标。 |
| 18 | RewardBench 论文 | arXiv | https://arxiv.org/html/2403.13787 | chat/reasoning/safety 三元组基准。 |
| 19 | RewardBench 代码库 | AllenAI | https://github.com/allenai/reward-bench | 统一推理代码 + 在线排行榜。 |
| 20 | RewardBench 2 | arXiv | https://arxiv.org/pdf/2506.01937.pdf | 多技能奖励模型基准。 |
| 21 | LMArena 官方排行榜 | LMArena | https://lmarena.ai | 人工盲选投票，Elo 评分每日更新。 |
| 22 | Chatbot Arena 说明 | Hivebook | https://hivebook.wiki/wiki/chatbot-arena-lmsys-human-preference-leaderboard-with-elo-rating | LMArena 运作机制补充说明（第三方，补充级）。 |

## 四、最佳实践指南与研究综述

| # | 标题 | 来源 | 链接 | 概述 |
|---|------|------|------|------|
| 23 | A Survey on LLM-as-a-Judge | arXiv | https://arxiv.org/pdf/2411.15594v6 | 全面综述，聚焦构建可靠判官系统。 |
| 24 | LLMs-as-Judges: A Comprehensive Survey | arXiv | https://ar5iv.labs.arxiv.org/html/2412.05579 | 五视角梳理 LLMs-as-Judges 范式。 |
| 25 | Best Practices for Consistent Evaluation | mer.vin | https://mer.vin/2025/11/llm-as-a-judge-best-practices-for-consistent-evaluation/ | 主张二元/低精度评分比高精度更可靠（2025-11，补充级）。 |
| 26 | Best Practices For Creating Your LLM-as-a-Judge | Galileo | https://www.galileo.ai/blog/best-practices-for-creating-your-llm-as-a-judge | 用 AUROC、Cohen's Kappa 验证判官质量。 |
| 27 | The Complete Evaluation Guide (2026) | qaSkills | https://qaskills.sh/blog/llm-as-judge-evaluation-guide-2026 | 位置/冗长/自我偏好偏差的症状与缓解（2026-06）。 |
| 28 | Judge Prompting: Rubrics, Calibration, and Bias in 2026 | Future AGI | https://futureagi.com/blog/what-is-llm-judge-prompting-2026/ | Cohen's Kappa 校准，判官选择原则。 |
| 29 | What Are Judge Biases? | AI-TLDR | https://ai-tldr.dev/learn/evaluation-safety/llm-as-judge/llm-judge-biases/ | 三种判官偏差；跨厂商多样判官面板（2026-06 更新）。 |
| 30 | LLM-as-Judge Calibration | Eval.qa | https://www.eval.qa/learn/llm-judge-calibration.html | 冗长偏差量化与校准。 |
| 31 | Auditing and Debiasing with a Bias-Aware Panel (JURY) | IJISAE | https://www.ijisae.org/index.php/IJISAE/article/download/8407/7392/14038 | 偏倚感知面板聚合器，同行评审期刊。 |
| 32 | Judging the Judges: Bias Mitigation Strategies | arXiv | https://arxiv.org/html/2604.23178v1 | 系统评估偏差缓解策略对平局率影响。 |
| 33 | The Silent Judge: Shortcut Bias | arXiv | https://www.arxiv.org/pdf/2509.26072 | 判官被表面特征欺骗的捷径偏差。 |
| 34 | When AIs Judge AIs: Agent-as-a-Judge | arXiv | https://arxiv.org/html/2508.02994v1 | Agent-as-a-Judge 与多智能体判官综述。 |
| 35 | The Automated Arbiter: Framework Analysis | Uplatz | https://uplatz.com/blog/the-automated-arbiter-a-comprehensive-analysis-of-llm-as-judge-frameworks-for-subjective-ai-evaluation/ | 判官框架综合分析与偏差归纳（2025-10，补充级）。 |
| 36 | LLM-as-Judge Evaluation Workflow | Agent Patterns | https://github.com/agentpatterns-ai/website/blob/main/workflows/llm-as-judge-evaluation.md | 各维度独立评分、约 20 条查询起步、单一判官 + 统一 rubric（2026-06 复核）。 |

## 五、2026 年新增（2026-05-15 之后发布）

| # | 标题 | 来源 | 链接 | 概述 | 日期 |
|---|------|------|------|------|------|
| 37 | LongJudgeBench: Benchmarking LLM-as-a-Judge for Long-Form Output | arXiv | https://arxiv.org/abs/2606.01629 | 首个长文本判官元评估基准，揭示长文本可靠性缺口。 | 2026-06-01 |
| 38 | RankJudge: Multi-Turn Synthetic Benchmark Generator | arXiv | https://arxiv.org/abs/2605.21748 | 多轮对话判官合成基准生成器，Bradley-Terry 评估 21 判官。 | 2026-05-20 |
| 39 | Generating and Refining Dynamic Evaluation Rubrics | arXiv | https://arxiv.org/abs/2605.30568 | 自动生成细粒度动态 rubric，14B 生成器优于大型闭源模型。 | 2026-05-28 |
| 40 | When the Judge Is Wrong: Reliability Benchmark Against Ground Truth | GitHub (IOV Labs) | https://github.com/hankimis/llm-judge-bench | 以客观真值直接打分判官，隔离位置/冗长/自偏好偏差。 | 2026 预印本 |
| 41 | Style Wins, Substance Loses: LLM-as-Judge in Idea Generation | arXiv | https://arxiv.org/html/2608.01666v1 | 诊断创意生成中重风格轻实质偏差，SciStyleExtractor 偏置控制。 | 2026-08 |
| 42 | Human-in-the-Loop Nugget Annotation for Accountable Evaluations | arXiv | https://arxiv.org/pdf/2606.29033v2 | 针对"橡皮图章效应"提出人机协同 nugget 标注提升可追责性。 | 2026-06 |

> 审查结论：剔除 3 条 —— 原 #6 Anthropic multi-agent 链接失效(404)、Lee Hanchung 个人博客(过时非权威)、Unite.ai 科普(非权威)。保留项中 4 条标记为"补充级"（非一手权威但较新或综合）。新增 6 条均发布于 2026-05-15 之后。