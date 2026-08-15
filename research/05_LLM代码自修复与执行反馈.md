# 方向 5：LLM 代码自我修复 / 自调试 / 执行反馈

> 搜索方向：LLM 生成代码的自我修复、自调试、执行反馈驱动的改进与选择。
> 本文件为原始搜集结果，不做分析。

## 学术论文（20 篇）

1. **Debug like a Human: A Large Language Model Debugger via Verifying Runtime Execution Step by Step (LDB)** — Li Zhong, Zilong Wang, Jingbo Shang 等（UC San Diego），ICLR 2024 — https://arxiv.org/pdf/2402.16906v5 — 将程序切分为基本块，逐步跟踪运行时中间变量值作为执行反馈，驱动 LLM 修复生成代码。
2. **LeDex: Training LLMs to Better Self-Debug and Explain Code** — Nan Jiang 等（Purdue），2024 — https://arxiv.org/html/2405.18649 — 用"错误代码解释 + 代码精炼"的链式轨迹训练模型，通过执行验证过滤数据以提升自调试能力。
3. **RLEF: Grounding Code LLMs in Execution Feedback with Reinforcement Learning** — Jie Liu 等，2024 — https://arxiv.org/html/2410.02089v2 — 端到端强化学习教模型利用执行反馈迭代改进代码，优于独立采样。
4. **PerfCodeGen: Improving Performance of LLM Generated Code with Execution Feedback** — Salesforce AI Research，FORGE 2025 @ ICSE（获 ACM SIGSOFT 杰出论文奖）— https://arxiv.org/html/2412.03578 — 基于测试用例执行时的运行时反馈做自精炼，提升生成代码性能。
5. **An Iterative Test-and-Repair Framework for Competitive Code Generation (FixAudit)** — 2026 — https://arxiv.org/html/2604.05560v2 — 从单个初始候选出发，通过"失败测试→修复"的测试-修复循环迭代改进代码。
6. **AgentForge: Execution-Grounded Multi-Agent LLM Framework for Autonomous Software Engineering** — 2026 — https://arxiv.org/pdf/2604.13120v1 — Planner/Coder/Tester/Debugger/Critic 五智能体框架，用沙箱执行验证与执行反馈驱动修复。
7. **CYCLE: Learning to Self-Refine the Code Generation** — Yangyu Huang 等，2024 — https://arxiv.org/pdf/2403.18746 — 代码自动跑测试套件，将失败用例与执行反馈回灌模型进行自精炼。
8. **SelfEvolve: A Code Evolution Framework via Large Language Models** — Shuyin Ouyang 等，2023 — https://arxiv.org/pdf/2306.02907 — 利用错误信息（含执行反馈）迭代修订 buggy 程序，形成代码进化循环。
9. **Self-Edit: Fault-Aware Code Editor for Code Generation** — Kechi Zhang 等，2023 — https://arxiv.org/pdf/2305.04087v5.pdf — 在示例测试上执行生成代码，将执行结果包装成注释引导"故障感知编辑器"修正。
10. **CodeChain: Towards Modular Code Generation Through Chain of Self-revisions with Representative Sub-modules** — Hung Le 等，2023 — https://ar5iv.labs.arxiv.org/html/2310.08992 — 通过"自修订链"复用/适配代表性子模块，迭代修订代码。
11. **Natural Language to Code Translation with Execution (MBR-Exec)** — Freda Shi, Daniel Fried, Marjan Ghazvininejad, Luke Zettlemoyer, Sida I. Wang，2022 — https://arxiv.org/pdf/2204.11454 — 执行每个候选程序以近似语义等价，用执行结果做最小贝叶斯风险解码选择。
12. **CodeRanker: A Neural Ranker for Predicting the Correctness of Sampled Programs** — Tianyi Zhang 等（Microsoft Research），2022 — https://www.microsoft.com/en-us/research/wp-content/uploads/2022/10/code_ranker_final.pdf — 以代码执行正确性为监督信号训练神经排序器，用于不执行情况下选择正确候选。
13. **Sifting through the Chaff: On Utilizing Execution Feedback for Ranking the Generated Code Candidates** — 2024 — https://arxiv.org/pdf/2408.13976v2.pdf — 利用执行反馈（而非仅分类标签）对生成代码候选排序，改进 CodeRanker 类方法。
14. **Top Pass: Improve Code Generation by Pass@k-Maximized Code Ranking** — 2024 — https://arxiv.org/html/2408.05715 — 以最大化 pass@k 为目标对候选程序排序，提升执行通过率。
15. **RepairAgent: An Autonomous, LLM-Based Agent for Program Repair** — Islem Bouzenia, Premkumar Devanbu, Michael Pradel，2024 — https://arxiv.org/pdf/2403.17134v1.pdf — 将 LLM 作为自主智能体，通过信息收集、搜索与候选修复实验（含测试执行验证）修复缺陷。
16. **Agentic Program Repair from Test Failures at Scale: A Neuro-symbolic approach with static analysis and test execution feedback** — 2025 — https://arxiv.org/html/2507.18755 — ReAct 智能体基于测试失败与静态分析反馈，在大规模软件上执行修复动作。
17. **RLTF: Reinforcement Learning from Unit Test Feedback** — Jiate Liu 等，2023 — https://ar5iv.labs.arxiv.org/html/2307.04349 — 在线 RL 框架，以多粒度单元测试反馈作为奖励信号精炼程序合成模型。
18. **CodeRL: Mastering Code Generation through Pretrained Models and Deep Reinforcement Learning** — Hung Le, Yue Wang 等，NeurIPS 2022 — https://openreview.net/references/pdf?id=Q44NYaKcM — 以单元测试预测正确性的 critic 提供稠密反馈，指导代码生成 actor 迭代改进。
19. **StepCoder: Improve Code Generation with Reinforcement Learning from Compiler Feedback** — Shun Zhang 等，2024 — https://arxiv.org/html/2402.01391v1 — 将代码生成拆分为"已完成代码 + 剩余代码"，用编译器反馈做 RL 训练。
20. **InterCode: Standardizing and Benchmarking Interactive Coding with Execution Feedback** — Yangruibo Ding 等，ICLR 2024 — https://www.proceedings.com/content/075/075280-2879open.pdf — 标准化"代码-执行反馈"交互式编码基准，验证执行反馈对模型提升的显著作用。

> 补充备选：Self-Correcting Code Generation Using Small Language Models (CoCoS)（2025, arXiv:2505.23060）；Revisit Self-Debugging with Self-Generated Tests（2025, arXiv:2501.12793）；Helping LLMs Improve Code Generation Using Feedback from Testing and Static Analysis（2024, arXiv:2412.14841）；Semantic Voting: Execution-Grounded Consensus for LLM Code Generation（2026, arXiv:2605.08680）；ReflexiCoder: Teaching LLMs to Self-Reflect on Generated Code and Self-Correct It via Reinforcement Learning（ACL 2026）。

## 开源项目（10 个）

1. **SWE-agent** — Princeton NLP / Stanford — https://github.com/SWE-agent/SWE-agent — 把 LLM 变成软件工程智能体，通过 Agent-Computer Interface 在真实仓库中修复 GitHub issue（SWE-bench 12.29%）。
2. **OpenHands（原 OpenDevin）** — All-Hands-AI — https://github.com/All-Hands-AI/OpenHands — 自主编码智能体，读仓库、编辑文件、运行 shell 与测试并重试直至完成，Docker 沙箱隔离执行。
3. **Aider** — Aider-AI — https://github.com/Aider-AI/aider/ — 终端 AI 结对编程，每次改动后自动 lint 和跑测试，依据测试反馈修复问题。
4. **AutoCodeRover** — AutoCodeRoverSG — https://github.com/AutoCodeRoverSG/auto-code-rover — 自主程序修复工具，AST 感知代码搜索 + 测试执行验证，SWE-bench lite 修复率高。
5. **Agentless** — OpenAutoCoder — https://github.com/OpenAutoCoder/Agentless — 无 agent 脚手架，简单"定位→修复→验证"流程，SWE-bench 50.8%（Claude）。
6. **RepairAgent** — sola-st — https://github.com/sola-st/RepairAgent — 首个自主 LLM 程序修复智能体，规划并执行修复动作，在 Defects4J 上验证。
7. **PerfCodeGen** — SalesforceAIResearch — https://github.com/SalesforceAIResearch/perfcodegen — 论文官方仓库，用执行反馈提升 LLM 生成代码性能。
8. **InterCode** — Princeton NLP — https://github.com/InterCode-AI/InterCode — 交互式编码基准（含执行反馈），提供 Bash/SQL 环境的代码-执行交互评测。
9. **Web-Based Multi-Round Dialogue Code Repair Agent** — zetaolin913 — https://github.com/zetaolin913/Web-Based-Multi-Round-Dialogue-Code-Repair-Agent — 网页版多轮对话代码修复代理，集成沙箱执行与迭代修复验证。
10. **Agentic Code Fixer** — antonella-schiavoni — https://github.com/antonella-schiavoni/agentic-code-fixer — 多智能体生成补丁候选并评估，自动化代码修复系统。

## 备注

- 已按要求跳过 Self-Debugging、Reflexion、Self-Refine、CodeT 四个方向的重复条目。
- 部分 2026 年条目（FixAudit、AgentForge、Semantic Voting、ReflexiCoder）为 arXiv/ACL 预印本或新近录用，作者信息未完整核实。
