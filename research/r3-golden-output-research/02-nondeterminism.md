# 方向二：非确定性的容忍与检测（审查版）

> 子问题：如何区分代码再生的非确定性（如随机性、并发时序、LLM 采样）与真正的行为偏差？
> 覆盖主题：Flaky Test 检测与分类、LLM 输出非确定性与 AI 代码可复现性、非确定性系统的差分测试、统计/概率验证、确定性重放与种子管理、可复现构建。
> 审查日期：2026-08-15。筛选标准：近三个月（2026-05-15 之后）有更新/发表，或具有重大意义。

## 审查说明

本轮对上一版 28 条做了逐条核验与补充检索，主要动作：

- **修正链接**：NonDex、iDFlakies、IDoFT 三个仓库均已迁移（旧 `ucd-plse/*` 链接 404），更新为 `TestingResearchIllinois/NonDex`、`UT-SE-Research/iDFlakies`、`TestingResearchIllinois/IDoFT`。
- **更正出处**：Lam 等《A Large-Scale Longitudinal Study of Flaky Tests》实为 OOPSLA 2020（非 ISSTA 2020），无 arXiv 版。
- **剔除弱条目**：移除长期无人维护的项目（kotlarmilos/flaky-tests 停更 5.6 年、conan-deterministic-examples 停更 7 年、nondex-rs 停更 1.8 年）与相关性弱的硬件重放论文（BugNet、SReplay）。
- **新增近三月/重大意义条目**：LLM 非确定性归因（温度/随机性两篇 2026-06/07）、AI 生成代码可复现性实证、AgentAssay 统计验证、在线 SMC 置信序列、AI 智能体确定性重放工具群（agrepl/rewind/Reprise）、Debian 14 强制可复现构建等。
- **时效标注**：每条标注【近三月】【重大意义】【经典】【活跃】/【低活跃】。

---

## 一、非确定性检测与分类（Flaky Test）

| # | 标题 | 类型 | 链接 | 出处/年份 | 简介 | 时效/意义 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | NonDex: A Tool for Detecting and Debugging Wrong Assumptions on Java API Specifications | 论文（附开源工具） | https://dl.acm.org/doi/pdf/10.1145/2950290.2983932 （工具 https://github.com/TestingResearchIllinois/NonDex） | ACM FSE 2016 | 检测开发者对 Java API"未确定规范"（如 HashSet 迭代顺序）的错误假设，主动扰动非确定性行为暴露潜在 bug。 | 【经典/活跃】"主动注入/放大非确定性以检测隐藏行为偏差"的典型范式（2026-03 更新）。 |
| 2 | iDFlakies | 开源项目 | https://github.com/UT-SE-Research/iDFlakies | UT-SE-Research（原 ucd-plse 迁移），2019 至今 | 检测与分类"顺序依赖型" flaky tests 的工具，支持 Maven/Gradle，配套论文 ISSTA 2019。 | 【低活跃】2024-11 后更新放缓，但仍是顺序依赖检测的标杆工具。 |
| 3 | IDoFT（Illinois Dataset of Flaky Tests） | 开源数据集 | https://github.com/TestingResearchIllinois/IDoFT | TestingResearchIllinois（原 ucd-plse 迁移），2020 | 最大 flaky tests 数据集之一（6,446 个 flaky tests / 423 个项目），含 flakiness-introducing commit 信息。 | 【活跃】2026-05 更新，为训练/评估非确定性检测方法提供基准数据。 |
| 4 | A Large-Scale Longitudinal Study of Flaky Tests | 论文 | https://dl.acm.org/doi/10.1145/3428270 （PDF https://mir.cs.illinois.edu/~marinov/publications/LamETAL20LongitudinalFlakyTests.pdf） | OOPSLA 2020（Lam 等） | 对 26 个 Java 项目 201 个 flaky tests 的长期研究，明确区分"顺序依赖型"与"非确定型（ND）"两类并分析根因与修复。 | 【经典】提供"非确定性 vs 行为偏差"的实证分类框架。注意：原资料误标 ISSTA 2020，已更正为 OOPSLA 2020。 |
| 5 | Test Flakiness' Causes, Detection, Impact and Responses: A Multivocal Review | 论文（综述） | https://arxiv.org/abs/2212.00908 | arXiv 2212.00908, 2022 | 多语言综述，系统梳理 flaky test 成因（随机性、并发时序、网络等）、检测方法、影响与修复策略。 | 【经典】全景式给出非确定性来源清单与检测手段。 |
| 6 | Understanding and Improving Flaky Test Classification（FlakyLens） | 论文 | https://www.cs.cornell.edu/~saikatd/papers/flakylens-oopsla25.pdf （工具 https://github.com/UT-SE-Research/FlakyLens） | OOPSLA 2025 | 改进 flaky test 分类方法，更准确区分不同 flakiness 根因，并分析分类对修复的影响。 | 【重大意义】分类是"容忍 vs 检测"决策的前置步骤。 |
| 7 | How Far Are We from Detecting Flaky Tests: On the Limits of Code-Based Detection | 论文 | https://arxiv.org/abs/2607.09345 | arXiv 2607.09345, 2026-07 | 指出基于代码的 flaky 检测"成功"多为任务与基准构造的假象，复现三个已发表检测器，提出 C-IDoFT 反事实基准与 FlakeCI 语料。 | 【近三月】对"静态检测"路线的方法学批判，提示应转向动态/统计手段。 |
| 8 | Detecting Flaky Tests in Quantum Software: A Dynamic Approach | 论文 | https://arxiv.org/html/2512.18088v1 | arXiv 2512.18088, 2025-12 | 首次大规模动态刻画量子软件 flaky tests（Qiskit terra 10,000 次执行），用 Wilson 置信区间量化重跑预算。 | 【重大意义】示范"用统计置信区间决定重跑次数"的方法，可直接迁移。 |
| 9 | Understanding Reproducibility and Characteristics of Flaky Tests Through Test Reruns in Java Projects | 论文 | https://experts.illinois.edu/en/publications/understanding-reproducibility-and-characteristics-of-flaky-tests-/ | IEEE TSE（Luo 等） | 对 Java 项目测试套件重跑 4000 次，发现许多"非顺序依赖"测试实际依赖顺序。 | 【重大意义】用大规模重跑实证"重跑次数与判定可靠性"的关系。 |
| 10 | Regression-Test History Data for Flaky-Test Research | 论文+数据集 | https://www.sosy-lab.org/research/pub/2024-FTW24.Regression-Test_History_Data_for_Flaky_Test_Research.pdf | FTW 2024（Sosy-Lab） | 基于 IDoFT 构建 flaky tests 的回归测试历史数据集，以 flakiness-introducing commit 为边界组织历史。 | 【重大意义】提供"非确定性何时引入、何时暴露"的时间维度数据。 |
| 11 | Differential Testing of Concurrent Classes（CONDIFF） | 论文 | https://valerio-terragni.github.io/assets/pdf/terragni-icst-2025.pdf | ICST 2025 | 面向并发类的差分测试，显式处理线程交错这一非确定性来源，穷举交错对比两个版本行为差异。 | 【重大意义】"非确定性系统差分测试"的典型代表。 |
| 12 | Differentially Testing Database Transactions for Fun and Profit（DT²） | 论文 | https://dl.acm.org/doi/fullHtml/10.1145/3551349.3556924 | ISSTA 2022 | 对多 DBMS 做并发事务差分测试，提出"事务测试协议"保证并发事务确定性执行，消除非确定性干扰。 | 【重大意义】示范"先消除/控制非确定性，再做差分"的方法论。 |

## 二、LLM 非确定性与 AI 代码可复现性（与 R3 再生成场景最直接相关）

| # | 标题 | 类型 | 链接 | 出处/年份 | 简介 | 时效/意义 |
| --- | --- | --- | --- | --- | --- | --- |
| 13 | Necessary but Not Sufficient: Temperature Control and Reproducibility in LLM-as-Judge Safety Evaluations | 论文 | https://arxiv.org/abs/2606.26185 | arXiv 2606.26185, 2026-06 | 温度=0 也不能消除 LLM 判断翻转：690 次 API 调用中即使强制贪心解码仍有 1–2/7 边界项不可复现；Claude Opus 4.7/4.8 已弃用 temperature 参数。 | 【近三月】LLM 采样非确定性的实证边界，直接支撑"黄金输出"差异归因。 |
| 14 | Randomness in large language models: What researchers need to know (and report) | 论文 | https://arxiv.org/abs/2607.24372 | arXiv 2607.24372, 2026-07 | 系统梳理 LLM 运行间随机性来源（采样、静默模型更新等），给出"T=0 是否存活、本地/API 可控性"对照表与报告规范。 | 【近三月】非确定性来源分类框架，可用于区分随机性与真行为偏差。 |
| 15 | AI-Generated Code Is Not Reproducible (Yet): An Empirical Study of Dependency Gaps in LLM-Based Coding Agents | 论文 | https://arxiv.org/abs/2512.22387 | arXiv 2512.22387, 2025-12 | 仅 68.3% 的 AI 生成项目可复现；Python 89.2%、JS 61.9%、Java 44.0%。 | 【重大意义】AI 代码可复现性实证基线。 |
| 16 | AgentAssay and the Regression Testing Gap: Statistical Verification for Non-Deterministic Codex CLI Agent Workflows | 博客/工具 | https://codex.danielvaughan.com/2026/06/27/agentassay-regression-testing-non-deterministic-codex-cli-agent-workflows-behavioral-fingerprinting/ | 2026-06-27（非学术来源） | 对非确定性 Codex CLI 智能体工作流做行为指纹与统计验证/回归测试。 | 【近三月】非确定性 AI 工作流的统计验证，与"黄金输出"机制直接对应。 |

## 三、统计/概率验证

| # | 标题 | 类型 | 链接 | 出处/年份 | 简介 | 时效/意义 |
| --- | --- | --- | --- | --- | --- | --- |
| 17 | A Survey of Statistical Model Checking | 论文（综述） | https://experts.illinois.edu/en/publications/a-survey-of-statistical-model-checking/ | ACM TOMACS 28(1), 2018（Agha & Palmskog） | 统计模型检验（SMC）权威综述，介绍用随机采样与假设检验验证随机系统性质。 | 【经典】"统计/概率验证非确定性行为"的理论框架。 |
| 18 | Bayesian Statistical Model Checking with Application to Stateflow/Simulink Verification | 论文 | https://www.cs.cmu.edu/~emc/papers/Conference%20Papers/Bayesian%20Statistical%20Model%20Checking%20with%20Application%20to%20Stateflow-Simulink%20Verification.pdf | FM 2015（Zuliani/Platzer/Clarke） | 基于贝叶斯统计的 SMC，面向含随机转移的混合系统，验证性质成立概率是否超过阈值。 | 【经典】少量采样下给出概率性判定，适合"概率化黄金输出"验证。 |
| 19 | Numerical vs. Statistical Probabilistic Model Checking: An Empirical Study | 论文 | https://www.cs.ox.ac.uk/david.parker/papers/tacas04.pdf | TACAS 2004（PRISM 团队） | 对比数值精确求解与统计（序贯接受抽样）两类概率模型检验方法。 | 【经典】"精确验证 vs 统计验证"的取舍依据。 |
| 20 | Confidence Sequences for Online Statistical Model Checking of Markov Decision Processes | 论文 | https://arxiv.org/abs/2606.25797 | arXiv 2606.25797, 2026-06 | 为在线 SMC 设计置信序列，比经典 union-bound 方法平均少 50x 采样，并给出高效工具实现。 | 【近三月】统计验证方法学新进展，可用于非确定性行为判定。 |

## 四、确定性重放与种子管理

| # | 标题 | 类型 | 链接 | 出处/年份 | 简介 | 时效/意义 |
| --- | --- | --- | --- | --- | --- | --- |
| 21 | rr（Mozilla 记录-重放调试器） | 开源项目 | https://github.com/rr-debugger/rr | Mozilla，持续维护 | Linux 下确定性记录-重放调试器，可精确复现任意执行轨迹并支持时间旅行调试。 | 【近三月】确定性重放标杆实现（2026-08-15 当日更新），用于复现并发/时序非确定性 bug。 |
| 22 | DRT（Deterministic concurrency testing and record/replay runtime） | 开源项目 | https://github.com/Yumekaz/DRT | GitHub | 面向 Python 的确定性并发测试与记录/重放运行时，记录调度决策与随机 API 输入、重放执行。 | 【活跃】"记录非确定性来源 + 重放 + 种子调度"集成一体（2026-04 更新）。 |
| 23 | Deterministic Replay for AI Agent Systems（agrepl） | 论文+工具 | https://arxiv.org/abs/2607.16200 （工具 https://github.com/taiwrash/agrepl） | arXiv 2607.16200, 2026-04；工具 2026-07 更新 | 为 AI 智能体系统提供确定性重放方案，配套 agrepl 工具（MIT）。 | 【近三月】AI 智能体确定性重放，与"代码再生非确定性"场景高度相关。 |
| 24 | rewind | 开源工具 | https://github.com/logannye/rewind | GitHub, 2026-06 | 基于主种子派生的块级重放：每块一个 checkpoint + 块内种子，随机性块局部化、可独立重放。 | 【近三月】种子管理新思路，随机性局部化。 |
| 25 | Reprise | 开源工具 | https://github.com/itsshreyasbhardwaj-design/reprise | GitHub, 2026-07 | AI 智能体确定性 record/replay 与 time-travel 调试，MCP-native，逐字节重放 LLM/工具/MCP 调用。 | 【近三月】AI 智能体确定性重放工具。 |

## 五、可复现构建

| # | 标题 | 类型 | 链接 | 出处/年份 | 简介 | 时效/意义 |
| --- | --- | --- | --- | --- | --- | --- |
| 26 | Reproducible Builds | 开源项目 | https://reproducible-builds.org/docs/env-variations/ | reproducible-builds.org，持续维护 | 可复现构建社区项目，系统梳理构建环境差异（时间戳、随机种子、主机名、DNS 等）导致非确定性的来源与消除方法。 | 【近三月】持续维护（2026-05 月度报告已发布），从"构建产物确定性"角度给出非确定性来源清单。 |
| 27 | Linux Kernel Reproducible Builds 文档 | 文档/工程实践 | https://kernel.org/doc/html/latest/kbuild/reproducible-builds.html | kernel.org | Linux 内核实现可复现构建的官方文档，如 CONFIG_RANDSTRUCT 需预生成随机种子（randstruct.seed）。 | 【活跃】真实工程中"随机种子固定"的权威实践。 |
| 28 | Debian 14 "Forky" 强制可复现构建（迁移门禁） | 里程碑/新闻 | https://needhelp.icu/blogs/debian-reproducible-builds-mandate | 2026-05-10 宣布 | Debian 成为首个强制所有包可复现构建的主流发行版，迁移系统开始拦截不可复现包（forky amd64 复现率 97.2%）。 | 【近三月/重大意义】可复现构建制度化里程碑。 |

## 检索说明与缺口

- 未检索到 2026-05-15 之后针对"黄金输出/逐行语义敏感 R3 制品"的直接论文，上述 LLM 非确定性（第 13-16 条）与统计验证（第 20 条）为最接近的相邻证据。
- "概率程序（Probabilistic Programs）验证"方向与统计模型检验（第 17-20 条）高度重叠，如需可定向补充（如 PSI、STAN 等工具）。
- 第 16 条 AgentAssay 为非学术来源（个人博客），权威性稍弱但内容与主题直接对应，使用前建议二次核验。
