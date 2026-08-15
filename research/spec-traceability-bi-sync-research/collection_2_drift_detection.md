# 规范与代码漂移检测（Spec–Code Drift Detection）—— 审查后精选清单

> 检索日期：2026-08-15。本清单为**审查后**版本：逐条核验真实性、按"时效性（近三个月内，2026-05-15 之后）"与"重大意义"两个维度筛选，并补充 2026 年最新论文与活跃开源项目。
>
> 审查结论：**奠基/综述类经典论文保留（重大意义）、2026 年 LLM 漂移检测新论文全部保留（时效性）、存疑条目作者已核实、仓库大小写/归属已修正。** 特别说明：本主题下"合规性偏离 vs 良性演进"尚无专门命名的独立论文，最贴近的是架构腐化综述与违规症状识别框架，已标注。

---

## 一、论文（Papers）

### 1.1 奠基 / 关键框架论文（保留理由：重大意义）

| 标题 | 作者/组织 | 年份 | 出处 / 链接 | 一句话贡献 | 保留理由 |
|---|---|---|---|---|---|
| Software Reflexion Models | Murphy, Notkin, Sullivan | 1995 | SIGSOFT/FSE'95; cs.ubc.ca/~murphy/papers/rm/reflexion_model_fse95.pdf | 经典"反思模型"：用高层模型作透镜对比代码，自动标出设计与实现一致/偏离，后续一致性核对方法之源头。 | 奠基之作 |
| Controlling Software Architecture Erosion: A Survey | De Silva, Balasubramaniam | 2012 | JSS 85(1):132–151, DOI:10.1016/j.jss.2011.07.036 | 架构腐化综述，将防治手段分"最小化/预防/修复"三类，是"合规偏离 vs 良性演进"判定的核心背景。 | 权威综述 |
| Towards Automated Identification of Violation Symptoms of Architecture Erosion | Li, Liang, Avgeriou | 2023 | arXiv:2306.08616 | 系统梳理架构侵蚀"违规症状"并自动化识别，为区分有害漂移与可接受偏离提供判据。 | 偏离判定框架 |
| A Comparison of Static Architecture Compliance Checking Approaches | Knodel, Popescu | 2007 | WICSA'07, DOI:10.1109/WICSA.2007.1 | 13 维度对比三类静态架构合规检查方法，给出选型指引。 | 方法基线 |
| A Unified Approach to Architecture Conformance Checking | Caracciolo, Lungu, Nierstrasz | 2015 | WICSA 2015, DOI:10.1109/WICSA.2015.11 | 用 Dictō DSL 声明式描述约束、Probō 第三方工具自动验证，统一架构合规检查。 | 框架代表作 |
| Automated Consistency Checking of Requirements Specifications | Heitmeyer, Jeffords, Labaw | 1996 | ACM TOSEM 5(3):231–261 | SCR 表格形式化分析，自动检测需求规格的类型错误/非确定性/遗漏。 | 需求侧一致性奠基 |
| Deep Just-In-Time Inconsistency Detection Between Comments and Source Code | Panthaplackel, Li, Gligoric, Mooney | 2021 | AAAI 2021; arXiv:2010.01625 | 提交前"及时"判断注释-代码不一致，文档-代码漂移检测代表。 | DL 代表 |
| DocChecker: Bootstrapping Code LLM for Detecting/Resolving Code-Comment Inconsistencies | Dau, Guo, Bui | 2024 | EACL 2024 Demo; aclanthology.org/2024.eacl-demo.20 | 代码-文本预训练模型检测并修复注释-代码不一致，SoTA（F1≈74.3%）。 | LLM 代表 |

### 1.2 最新漂移检测论文（2026，保留理由：时效性 + 直接相关）

| 标题 | 作者/组织 | 年份/月份 | 出处 / 链接 | 一句话贡献 | 时效标注 |
|---|---|---|---|---|---|
| **The Spec Growth Engine: Spec-Anchored, Code-Coupled, Drift-Enforced Architecture** | 作者见 arXiv | 2026-06 | arXiv:2606.27045 | 可机读 spec 图（contract/design 分离）+ 垂直切片增长协议 + **drift gate（spec↔code 发散作为阻塞合并条件）**，直接面向 AI 辅助开发的 spec-code 漂移治理。 | **重大意义（直接命中 H7）** |
| **From Code Review to Code Critique: Intent, Drift, and Spotlight for AI-Generated Diffs** | 作者见 arXiv | 2026-07 | arXiv:2607.29516 | 面向 AI 生成 diff 的规模化解码，含六主题分类与漂移检测（与人工标注 QWK=0.907），识别代码与意图的对齐漂移。 | 时效性 |
| **Beyond Correctness: Architectural Reasoning in Code LLMs via Scalable Labeling** | 作者见 arXiv | 2026-06 | arXiv:2606.14948 | Architecture Quality Judge（AQJ）：纯静态结构分析评估补丁是否符合仓库架构约定，规模化标注并微调 LLM 架构推理。 | 时效性 |
| DocPrism: Multi-lingual Detection of Incorrectness Inconsistencies | C. Lemieux（UBC） | 2026（ISSTA'26） | arXiv:2511.00215（ISSTA 版见 carolemieux.com） | 轻量多语言代码-文档"错误性"不一致检测，LCEF（局部分类+外部过滤）引导 LLM。**【作者已核实】**(1) | 时效性 |
| A Review on Detecting and Managing Documentation Drift in Software Development | A. Mohamed 等 6 人 | 2025（MIUCC） | IEEE DOI:10.1109/MIUCC66482.2025.11196773 | 文档漂移治理综述，覆盖启发式/同步算法/AI 与 LLM 方案。**【作者与标题已核实/补全】**(2) | 综述背景 |
| Larger Is Not Always Better: Leveraging Structured Code Diffs for Comment Inconsistency | 作者见 arXiv | 2025-12 | arXiv:2512.19883 | CARL-CCI：将代码 diff 分解为带活动标签序列（ADD/DEL/KEEP），轻量结构信息比更大模型更有效。 | 方法创新 |

---

## 二、开源项目（Open-Source Projects）

| 名称 | 组织/维护者 | 年份 | 链接 | 一句话贡献 | 时效/活跃度 |
|---|---|---|---|---|---|
| ArchUnit | TNG | 2015– | github.com/TNG/ArchUnit | 纯 Java 声明式定义并在 CI 断言架构/依赖/分层/循环规则，应用最广的架构一致性护法工具。 | 经典+活跃 |
| ArchUnitNET | TNG | 2018– | github.com/TNG/ArchUnitNET | ArchUnit 的 C# 移植，IL 字节码分析验证 .NET 分层与依赖规则。 | 活跃 |
| jQAssistant | BUSHIDO 社区 | 2013– | github.com/jqassistant-tool/jqassistant | 代码解析进 Neo4j，用 Cypher 写规则自动验证，实现"事实 vs 规则"的结构化漂移检测。 | 活跃 |
| DCL2Check | ASERG-UFMG | 2013– | github.com/aserg-ufmg/dcl2check | DCL 声明式依赖约束合规检查，检测被禁止/允许的依赖关系。 | 相关 |
| HUSACCT | HUSACCT 团队 | 2014– | github.com/HUSACCT/HUSACCT | SACC（实现架构 vs 设计架构一致性监控），支持语义丰富模块化架构。 | 相关 |
| ARCADE | Garcia（UCI） | 2012– | bitbucket.org/joshuaga/arcade | 架构恢复与"架构衰变"评估工作台，跨版本度量量化漂移累积。 | 相关 |
| **ArchGuard** | Tgenz1213 | 2024– | github.com/Tgenz1213/ArchGuard | 基于 ADR 的语义合规引擎，用 LLM（Ollama）推理代码变更是否违反架构决策，阻止违规提交。**【归属大小写已修正，注意与 Thoughtworks archguard 区分】(3)** | 活跃+直接相关 |
| **SpecSeal** | xantus-ai | 2024– | github.com/xantus-ai/spec-seal | 对规范行为契约做哈希（快照式），规范变化即代码被判过期，检测"规范变了代码没跟上"。 | 直接相关 |
| DocChecker | FSoft-AI4Code | 2023– | github.com/FSoft-AI4Code/DocChecker | 论文复现工具：代码-文本预训练模型检测修复注释-代码不一致。 | 相关 |
| deep-jit-inconsistency-detection | panthap2 | 2021 | github.com/panthap2/deep-jit-inconsistency-detection | AAAI'21 复现包，提交前注释-代码不一致检测。 | 相关 |
| **DriftBench** | rigour-labs | 2025– | github.com/rigour-labs/driftbench | 面向 AI 代码生成的全谱 PR 漂移&意图保持基准：检测"语法正确+测试通过但违反设计模式"的漂移。**【已核验，注意与同名的 infra-drift 项目区分】** | 活跃+直接相关 |

---

## 三、审查说明与行动项

- **核验动作**：(1) DocPrism 作者确认为 Caroline Lemieux（UBC），arXiv 版为 2511.00215，ISSTA 版标题略有差异；(2) IEEE 综述为 2025 MIUCC 会议论文，标题补全"In Software Development"，6 位作者已确认；(3) ArchGuard 归属修正为 `Tgenz1213/ArchGuard`。均真实存在。
- **重大补充**：Spec Growth Engine（drift gate）是当前最直接命中"Spec↔Code 漂移检测 + 阻塞合并"主题的新作，建议精读。
- **关于"合规性偏离 vs 良性演进"**：目前无专门命名论文，判定依据来自 De Silva&B（2012）综述与 Li/Liang/Avgeriou（2023）违规症状框架；Spec Growth Engine 的"drift gate"与 ReqToCode（collection_1）的"降级生命周期"共同提供了工程化判定的两端思路。
- **剔除**：初版中"基于图论和 FSM 的 UML 模型与代码一致性检测（2019 中文文献）"价值边缘且年代旧，已从主表移除（可作背景）。
- **商业工具参考**（非开源）：Lattix、Sonargraph、Sotograph，供对照。