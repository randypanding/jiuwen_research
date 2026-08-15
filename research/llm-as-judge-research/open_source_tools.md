# LLM-as-a-Judge / 大模型自动评估 开源项目材料索引（审查后）

> 审查日期：2026-08-15。收录标准：最近三个月（2026-05-15 后）有活跃更新，或具有重大代表意义。已通过 GitHub 实测核实链接、更新时间与 stars。
> 本次审查：剔除 7 个低价值/停更项目，保留 12 个并标注非活跃项，新增 5 个活跃或代表性项目。

## 一、评测框架（近三个月活跃）

| 名称 | GitHub 仓库 | Stars 量级 | 最近更新 | 功能说明 | 主要用途 |
|---|---|---|---|---|---|
| DeepEval | https://github.com/confident-ai/deepeval | ~1.7 万 | 2026-08-13 | pytest 基 LLM 评测框架，50+ 指标（G-Eval、RAG、Agentic、多轮），LLM-as-a-judge 与 ArenaGEval。 | Python 团队落地 LLM 评测、指标化测试 |
| RAGAS | https://github.com/explodinggradients/ragas | ~1.3 万 | 活跃（仓库已迁移至新组织，URL 重定向有效） | RAG 管线评测库，忠诚度/答案相关性/上下文精度召回，测试集生成。 | 评估调优 RAG 应用 |
| promptfoo | https://github.com/promptfoo/promptfoo | ~2.3 万 | 2026-08-13（v0.122.0） | 提示词测试评测工具，LLM-as-a-judge 断言（llm-rubric、g-eval、factuality），CI 集成，已并入 OpenAI 仍开源。 | Prompt 对比、模型质量评估、CI 评测 |
| TruLens | https://github.com/truera/trulens | ~3.3 千 | 2026-07-29（v2.10.0） | RAG Triad 三元组评测 + 实验追踪 + Dashboard，集成 LangChain/LlamaIndex，Snowflake 维护。 | RAG 可观测性、反馈追踪 |
| OpenCompass | https://github.com/open-compass/opencompass | ~7.3 千 | 2026-08-12 | 上海 AI Lab 评测平台，100+ 数据集，GenericLLMEvaluator 用于 judge 评测。 | 通用能力评测、多模型横向对比 |
| lm-evaluation-harness | https://github.com/EleutherAI/lm-evaluation-harness | 高 | 持续维护（2025-12 CLI 重构） | EleutherAI 评测框架，单命令跑数百 benchmark，HF Open LLM Leaderboard 后端。 | 复现公开分数、标准评测 |
| Inspect | https://github.com/UKGovernmentBEIS/inspect_ai | 中高 | 2026-08-04 | 英国 AI 安全研究所官方开源的前沿 LLM/Agent 评测框架，含 model-graded（LLM-as-judge）评测、沙箱与 200+ 预置任务。 | 前沿模型/Agent 安全与能力评测 |

## 二、开源 Judge 模型与评测基准

| 名称 | GitHub 仓库 | Stars 量级 | 最近更新 | 功能说明 | 主要用途 |
|---|---|---|---|---|---|
| Prometheus-Eval | https://github.com/prometheus-eval/prometheus-eval | ~1.1 千 | 2025-04-25（代表性但非活跃） | KAIST 开源评估 LM，Prometheus 2 (8x7B) 支持绝对评分与成对排序，含 Prometheus-Vision。 | 开源细粒度生成质量评估 |
| JudgeLM | https://github.com/baaivision/JudgeLM | ~440 | 2025-02-11（代表性但已停更） | LLaMA 微调可扩展判官，单/多角色/多模态，ICLR 2025。 | 大规模自动化评测与排序 |
| Skywork-Reward-V2 | https://github.com/SkyworkAI/Skywork-Reward-V2 | 低 | 2025-07-03（权重在 HF） | 昆仑万维奖励模型，0.6B-8B 多规模，RewardBench 领先（代码仓库近乎停更，权重在 HuggingFace）。 | 偏好对齐、RLHF 奖励信号 |
| RewardBench | https://github.com/allenai/reward-bench | ~730 | 2026-02-16 | AllenAI 奖励模型评测基准，统一推理代码与数据格式。 | 横向评测奖励模型 |
| CompassJudger | https://github.com/open-compass/CompassJudger | 低 | 2025-07-15（代表性但已停更约1年） | OpenCompass 一体化判官（1/2），支持评分/比较/格式评测/批判。 | 通用判官 + 可验证奖励评估 |
| JudgeLRM | https://github.com/NuoJohnChen/JudgeLRM | 中 | 2025-12-09 | 用 RL 训练的判官推理模型系列，JudgeLRM-3B 超 GPT-4、7B 超 DeepSeek-R1，专注成对评测。 | 推理型判官评估 |

## 三、LLM-as-Judge 专门工具库

| 名称 | GitHub 仓库 | Stars 量级 | 最近更新 | 功能说明 | 主要用途 |
|---|---|---|---|---|---|
| OpenEvals | https://github.com/langchain-ai/openevals | 中 | 2026-08-06 | LangChain 的 LLM-as-judge 评测库，`create_llm_as_judge` + 预置 prompt，多模态/RAG/轨迹评测，Python/TS。 | 快速搭建判官评测 |
| agentevals | https://github.com/langchain-ai/agentevals | 中 | 活跃（OpenEvals 官方推荐 Agent 评测分支） | 基于 OpenTelemetry 轨迹、框架无关的 Agent 行为评测方案。 | Agent 行为评测 |
| Verdict | https://github.com/haizelabs/verdict | ~340 | 2025-11-05（代表性但近期无更新） | 扩展"判官时计算"，组合推理/验证/辩论/聚合为复合判官。 | 构建复合式判官 |
| FastChat (MT-Bench / LLM-Judge) | https://github.com/lm-sys/FastChat | 高 | 长期维护 | LLM-as-a-Judge 奠基基准（MT-Bench 多轮 + Chatbot Arena），GPT-4 判官单答/成对评分实现。 | 最经典的开源判官评测实现 |

> 审查结论：剔除了 7 个低价值/停更/链接不实项目 —— Auto-J (GAIR-NLP，停更2.5年且低星)、microsoft/llm-as-judge（仅33星）、reaatech/llm-judge-toolkit（0星）、archminor/llm-as-a-judge（0星）、syed-waleed-ahmed/LLM-as-Judge（1星）、wenxuec/llm-judge（0星）、puja-ui/LLM-as-a-Judge（0星）。保留项中 5 个为"代表性但近期无更新"已标注。"Prometheus 3" 未检索到官方发布。