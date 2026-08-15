# 规格驱动双向同步、规范变更触发代码再生、双向工程 —— 审查后精选清单

> 检索日期：2026-08-15。本清单为**审查后**版本：逐条核验真实性、按"时效性（近三个月内，2026-05-15 之后）"与"重大意义"两个维度筛选，并补充 2026 年最新论文与活跃开源项目。
>
> 审查结论：**双向变换(bx)理论奠基保留（重大意义）、spec-as-source 最新工具链保留（时效性）、GitHub Spec Kit 确认高度活跃、JDomInO 标题已修正为正式标题。** 本主题是三个子问题中最"工程化落地"的方向，近三个月产出密集。

---

## 一、论文（Papers）

### 1.1 双向变换理论 / MDE 奠基（保留理由：重大意义）

| 标题 | 作者 | 年份 | 出处 / 链接 | 一句话贡献 | 保留理由 |
|---|---|---|---|---|---|
| Combinators for Bidirectional Tree Transformations | Foster, Greenwald, Moore, Pierce, Schmitt | 2005/2007 | ACM POPL 2005 / TOPLAS（dl.acm.org/doi/10.1145/1047659.1040325） | 提出 lens（get/put 成对）+ 可组合组合子，双向变换理论奠基。 | 奠基之作 |
| Bidirectional Model Transformations in QVT: Semantic Issues | P. Stevens | 2007 | MoDELS 2007 | 讨论 QVT 双向模型变换的一致性/可持续性/健壮性语义问题。 | 双向变换语义 |
| Bidirectional Transformations: A Cross-Discipline Perspective（GRACE-BX） | Czarnecki, Foster, Hu, Lämmel, Schürr, Terwilliger | 2009 | GSD uwaterloo GRACE 报告 | 跨学科综述双向变换并倡议建立 bx benchmark。 | 权威综述 |
| From State- to Delta-Based Bidirectional Model Transformations | Diskin, Xiong, Czarnecki, Ehrig, Hermann, Orejas | 2011 | SoSyM（2021 获 MODELS MIP） | 从状态级推广到 delta/变化级，支持增量同步与对称情形。 | 增量同步理论 |
| Bidirectionalization for Free! | J. Voigtländer | 2009 | ICFP 2009 | 从参数多态前向函数自动推导后向 put（语义双向化），无需专用双向语言。 | 自动双向化 |
| BiGUL: A Formally Verified Core Language for Putback-Based Bidirectional Programming | Ko, Hu | 2016 | PEPM 2016 | 以 putback 为核心、经形式化验证的双向核心语言，前向函数自动派生。 | 形式化 bx |
| A Survey of Triple Graph Grammar Tools | Anjorin, Leblebici, Schürr 等 | 2015 | SoSyM/会议 | 系统综述 TGG 双向模型变换工具（eMoflon、HenshinTGG 等）。 | TGG 综述 |
| The Past, Present, and Future of Automation in MDE | Burgueño, Di Ruscio, Sahraoui, Wimmer | 2024 | arXiv:2405.18539 | MDE 自动化综述，梳理模型变换/代码生成与未来 AI 辅助方向。 | 权威综述 |

### 1.2 最新双向同步 / 规范再生论文（2025–2026，保留理由：时效性 + 直接相关）

| 标题 | 作者 | 年份/月份 | 出处 / 链接 | 一句话贡献 | 时效标注 |
|---|---|---|---|---|---|
| **Keeping Models and Code in Sync: Roundtrip Engineering for Tactical DDD（JDomInO）** | W. Zhang, M. Herb, W.C.D. Cheng, M. Wagner, B. Jiang, T. Liu, A. Koziolek | 2026-08 | arXiv:2608.05612 | 战术 DDD 双向同步工具链：共享元模型，正向由领域模型确定性生成 Java、反向从代码重构领域模型；并指出结构化模型可作 AI 助手"精度上下文层"。**【标题已修正为正式标题，JDomInO 为工具名】** | **近三个月内（重点）** |
| **DeltaMCP: Incremental Regeneration via Spec-Aware Transformation for MCP servers** | 作者见 arXiv | 2026-05 | arXiv:2605.28148 | spec-as-source 典型：OpenAPI 规范变更时仅增量再生受影响 MCP server 工具，用 Oasdiff 语义差异+端点级变更单元+LoRA，显著低于全量再生。 | **近三个月内（重点）** |
| **AssumptionMiner: Extracting, Tracing, Revising Implicit Assumptions in LLM Code Generation** | 作者见 arXiv | 2026-07 | arXiv:2607.22898 | 把 LLM 代码生成的隐式假设做成一等工作（可检查假设层），基于 AST 依赖图"仅对受影响代码定向再生"。 | 近三个月内 |
| Round-trip Engineering for Tactical DDD: A Constraint-Based Vision | 作者见 arXiv | 2026-03 | arXiv:2603.26987 | DDD 原生元模型+实时约束验证+双向同步机制，JDomInO 的愿景前作。 | 相关（姊妹作） |
| **IncreRTL: Traceability-Guided Incremental RTL Generation under Requirement Evolution** | L. Chen, R. Chen, X. Li, S. Li, R. Gong, L. Wang | 2026-03 | arXiv:2603.25769 | 首个面向需求演化的 LLM 驱动 RTL 增量生成：追踪链接定位+增量再生受影响代码段，配套 EvoRTL-Bench。 | **重大意义（直接命中"规范变更→代码再生"）** |
| Faithful Autoformalization via Roundtrip Verification and Repair | 作者见 arXiv | 2026-04 | arXiv:2604.25031 | 用"往返验证"（形式化→译回自然语言→再形式化→逻辑等价校验）在无标注下验证保真度并修复。 | 相关 |
| **Spec-Driven Development: From Code to Contract in the Age of AI Coding Assistants** | D. B. Piskala | 2026-01 | arXiv:2602.00180 | SDD 综述，提出 spec-first / spec-anchored / spec-as-source 三级规范强度，分析 GitHub Spec Kit 等工具。 | **重大意义（综述框架）** |

---

## 二、开源项目（Open-Source Projects）

| 名称 | 组织/作者 | 年份 | 链接 | 一句话贡献 | 时效/活跃度 |
|---|---|---|---|---|---|
| **GitHub Spec Kit** | GitHub | 2025– | github.com/github/spec-kit | "规范驱动开发"官方工具包：Specify CLI（`specify init`）+ `/speckit.*` 斜杠命令，适配 30+ AI 编码代理。**【已核验：MIT，~1785 提交，最新 v0.16.3（2026-08-13），高度活跃】** | **近三月活跃（重点）** |
| OpenAPI Generator | OpenAPITools | 2018– | github.com/OpenAPITools/openapi-generator | spec-first 代码生成：从 OpenAPI 规范生成多语言服务端存根与 SDK，消除规范-实现漂移。 | 经典+活跃 |
| eMoflon::IBeX | TU Darmstadt 等 | 2015– | github.com/eMoflon/emoflon-ibex | 基于 TGG 的增量双向图变换工具套件，从单一规范生成同步器与翻译器。**【已核验：GPL-3.0】** | 双向变换代表 |
| Eclipse Epsilon | Eclipse / York | 2010– | eclipse.dev/epsilon | EGL 代码生成、ETL M2M、EVL 校验，支持模型到文本/双向一致性。 | 相关 |
| Eclipse Henshin | Eclipse 社区 | 2010– | github.com/eclipse-henshin/henshin | 图变换 EMF 模型变换引擎，衍生 HenshinTGG 支持双向。 | 相关 |
| Eclipse ATL | Eclipse / NaoMod | 2008– | eclipse.dev/atl | 主流单向 M2M 变换语言与工具，常与双向化方法结合。 | 相关 |
| Echo | HASLab（INESC TEC） | 2014– | github.com/haslab/echo | 基于 QVT-R/ATL 的双（多）向模型变换，一致性检查+最小修复（check/enforce），v0.3。**【已核验】** | 双向变换代表 |
| Boomerang | Foster 等（UPenn/Cornell） | 2008– | github.com/boomerang-lang/boomerang | 面向字符串数据的双向编程语言（resourceful lenses），同一程序驱动 get+put。 | 双向理论落地 |
| FunnyQT | jgralab | 2014– | github.com/jgralab/funnyqt | Clojure 模型查询/变换库，支持 EMF 模型双向同步及 schema/实例协同演化。 | 相关 |

---

## 三、审查说明与行动项

- **核验动作**：GitHub Spec Kit 确认为高度活跃（最新提交 2026-08-14、v0.16.3 2026-08-13）；JDomInO 标题修正为"Keeping Models and Code in Sync..."（JDomInO 为工具名）；eMoflon::IBeX、Echo 均真实。IncreRTL 信息准确。
- **重大补充**：JDomInO（近三月）、DeltaMCP（近三月）、Spec-Driven Development 综述、IncreRTL 是本主题最贴合的"双向同步 + 规范触发再生"前沿，建议精读。
- **理论 vs 工程对照**：理论基线（lens/TGG/delta）回答"双向同步的数学基础"，工程落地（Spec Kit、OpenAPI Generator、DeltaMCP、JDomInO）回答"如何在实际栈上做 spec-as-source"。二者结合可覆盖"规范变更→自动触发代码再生/标记"的完整链路。
- **剔除**：初版中"Performing Incremental Generation of Code in MDE（2011）"与"Least-change QVT-R/ATL（2014）"年代较旧、近三年无活跃更新，已从主表移除（可作背景）。

---

（三份文档为同一研究主题的三个子方向，交叉见各文档"审查说明"。建议下一步：按待精读清单精读标注为"重点/重大意义"的条目，再进入深度分析。）