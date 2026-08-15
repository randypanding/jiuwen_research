# Spec-as-Source 范式下可追踪性与双向同步 —— 精读综述与评分总表

> 研究总问题：**在 Spec-as-Source 范式下，如何实现从 Spec 到代码的可追踪性（Traceability）与双向同步？**
> 三个子问题：
> - **Q1** 需求追踪矩阵（RTM）的自动化生成：自动追踪 Spec 中每条 L1/L2 条款到代码实例的映射关系
> - **Q2** Spec↔Code 漂移的实时检测与报告：区分"合规性偏离"与"良性演进"（H7）
> - **Q3** 双向同步的原子操作：Spec 变更时自动触发代码再生或标记为待更新
>
> **评分标准**：A（强相关、高价值、显著推进） / B（相关但为背景/局部贡献） / C（弱相关或已停滞）
> 精读日期：2026-08-15。所有信息均通过 WebFetch 抓取原文/摘要页/仓库页确认，禁止编造，如无法获取原文已在特定位注明。

---

# 第一部分：需求可追踪性（RTM 自动化 / Spec→Code 追踪映射）

## 一、论文精读与评分（14 篇）

### 1.1 奠基/经典论文

| # | 标题 | 作者 | 年份/出处 | 方法要点 | 关键结论 | 与总问题关系 | 评分 |
|---|------|------|----------|----------|----------|-------------|:----:|
| 1 | An analysis of the requirements traceability problem | Gotel, Finkelstein | 1994 / IEEE ICRE | 基于 100+ 从业者实证研究，区分 pre-RS/post-RS 追踪，揭示追踪问题的多面性 | 多数"追踪差"的根源是需求来源不可追溯，而非追踪链本身断裂；定义了领域的概念地基 | 非解法，但定义了"Spec-as-Source 追踪与双向同步"的理论起点 | **A** |
| 2 | Recovering Traceability Links between Code and Documentation | Antoniol et al. | 2002 / IEEE TSE 28(10) | 概率模型 + VSM 两种 IR 模型，从标识符中提取领域知识，自动恢复代码↔文本文档追踪链 | 两种模型均有效，在 C++→手册与 Java→需求两案例中验证 | 开山之作，但单向词法 IR 事后恢复，无漂移检测与双向同步 | **B** |
| 3 | Advancing Candidate Link Generation for Requirements Tracing (RETRO) | Hayes, Dekhtyar, Sundaram | 2006 / IEEE TSE 32(1) | 定义追踪工具目标、引入新度量、把分析师反馈纳入候选链接生成，实现 RETRO 原型 | 人机协同可提升追踪质量，RETRO 有效支持其目标 | 人机协同的 RTM 自动生成范式，仍为单向 IR+反馈，未涉漂移与双向 | **B** |
| 4 | Software Traceability: Trends and Future Directions | Cleland-Huang et al. | 2014 / ICSE FOSE | 领域综述，系统梳理研究现状，聚焦于工具与可视化、IR 自动创建 | 强调安全关键系统中可追踪性被强制要求但常"事后补建" | 划定研究版图与缺口，定位课题坐标，无具体解法 | **B** |
| 5 | Grand Challenges of Traceability: The Next Ten Years | Cleland-Huang et al. | 2017 / arXiv:1710.03129 | 围绕策略制定、链接创建与演化、链接使用、实际应用四轴汇编立场论文 | 把"链接创建与演化"明确列为核心挑战之一，推动数据集建设 | 把"链接演化"与"数据集"写入研究议程，为漂移/同步提供框架性指引 | **B** |
| 6 | Semantically Enhanced Software Traceability Using Deep Learning | Guo, Cheng, Cleland-Huang | 2017 / ICSE (arXiv:1804.02438) | Word Embedding + RNN (Bi-GRU) 建模语义，学习领域语料知识 | Bi-GRU 显著优于 VSM 与 LSI，语义化自动追踪链接的里程碑 | 语义层面推进 RTM 自动生成，但单向恢复、领域受限、需大量标注数据 | **B** |
| 7 | Traceability Transformed (Trace BERT / T-BERT) | Lin et al. | 2021 / ICSE (arXiv:2102.04411) | 预训练 BERT + 三步迁移学习策略，克服数据稀疏，Single/Siamese/Twin 三种架构 | Single-BERT 准确率最高，MAP 较 VSM 平均提升 60.31%，预训练克服 RNN 欠拟合 | RTM 自动生成的重大突破，高采用价值，仍为单向恢复 | **A** |

### 1.2 最新 LLM 方法（2025–2026）

| # | 标题 | 作者 | 年份/出处 | 方法要点 | 关键结论 | 与总问题关系 | 评分 |
|---|------|------|----------|----------|----------|-------------|:----:|
| 8 | **R2Code: A Self-Reflective LLM Framework** | Wang, Keung et al. | 2026-04 / IEEE COMPSAC 2026 | BAN 双向对齐 + SRCV 自反思校验 + DCAR 自适应检索，跨层级语义匹配 | 5 数据集平均 F1 +7.4%，token 最多 -41.7% | 在准确率与成本上双优，显著增强大规模 Spec→Code 追踪可用性 | **A** |
| 9 | **TraceLLM: LLM with Prompt Engineering** | Alturayeif, Ahmad, Hassine | 2026-02 / Requirements Eng. 31(6) | 系统化提示工程+示例选择，8 个 LLM、4 基准数据集，zero/few-shot 评估 | 取得 SOTA F2，label-aware + diversity 采样最有效；提示工程质量 > 模型容量 | 把 RTM 自动生成落到可工程化的提示工程层面，半自动人机协同 | **A** |
| 10 | Requirements Traceability Link Recovery via RAG | Hey, Fuchß, Keim, Koziolek | 2025 / REFSQ, Springer | LLM + RAG 做需求间（inter-requirements）追踪链接恢复，6 基准数据集 | 思维链提示有益；开源模型与闭源相当；贡献在"需求↔需求"而非需求↔代码 | 解决 Spec 内部（需求间）追踪一致性，是 Spec 侧基础但不覆盖跨制品 | **B** |
| 11 | NL-PL Traceability Needs More than Textual Similarity | Zou, Wang, Liang, Bi, Jin | 2025-09 / arXiv:2509.05585 | 大规模实证揭示文本相似度不足，用 HGT 图策略+Gemini 2.5 Pro 多策略 | 12 项目 F1 较 HGNNLink +3.68% / +8.84%，直击 NL-PL 语义鸿沟 | 直击范式核心难点（Spec 是 NL，代码是 PL），用图+LLM 提升链接质量 | **A** |
| 12 | **SpecMap: Hierarchical LLM Agent** | Nipane, Agrawal, Singh | 2026-01 / arXiv:2601.11688 | 逐层收窄搜索空间：仓库级结构推断→文件级相关度→符号级对齐 | 文件级准确率 73.3%，token 消耗降低 84%，耗时降低约 80% | 层级化 LLM Agent 把 datasheet→代码追踪做到符号级细粒度且大幅降本 | **A** |
| 13 | Enhancing Traceability Link Recovery: T-SimCSE | Wang, Wang, Hu, Huang, Zhao | 2026-03 / arXiv:2603.11800 | SimCSE 无监督预训练 + specificity 重排，无需标注数据 | 10 数据集 recall/MAP 领先 | 免标注优势，增量改进，未突破相似度范式根本局限 | **B** |
| 14 | **ReqToCode: Embedding Traceability as Structural Property** | T. Schlathölter | 2026-03 / arXiv:2603.13999 (preprint) | Traceable 元素嵌入代码库，编译期可验证结构属性，分级生命周期响应需求变更 | 概念方法学论文，无大规模评测；用构建期校验实现漂移检测与双向同步 | 唯一直接正面回应"漂移检测+双向同步+Spec-as-Source"三者，方向前瞻但缺实证 | **A** |

### 论文评分汇总

| 评分 | 篇数 | 条目 |
|:----:|:----:|------|
| A | 7 | #1(奠基)、#7(Trace BERT)、#8(R2Code)、#9(TraceLLM)、#11(NL-PL)、#12(SpecMap)、#14(ReqToCode) |
| B | 7 | #2(Antoniol)、#3(RETRO)、#4(FOSE)、#5(Grand Challenges)、#6(DL)、#10(RAG)、#13(T-SimCSE) |
| C | 0 | — |

---

## 二、开源项目精读与评分（11 个）

| # | 名称 | 组织 | 技术栈 | RTM 自动生成 | 追踪链接 | 双向同步 | 漂移检测 | 活跃度 | 评分 | 一句话理由 |
|---|------|------|--------|:-----------:|:--------:|:--------:|:--------:|:------:|:----:|-----------|
| 1 | TraceLab | CoEST | C# .NET | 否(实验平台) | 有(实验) | 否 | 否 | 停滞(2018) | C | 学术 TLR 实验平台，已停更，非生产工具 |
| 2 | TraceBERT | jinfenglin | Python/CodeBERT | 间接(模型底座) | 有(NL→PL) | 否 | 否 | 停滞(2021) | B | 可作 RTM 模型底座，但仅研究代码、无产品化 |
| 3 | **ArDoCo/Core (ARCOTL)** | KIT KASTEL | Java | 间接(TLR 引擎) | 有(文档↔PCM) | 部分(检测) | **有** | **高(2026)** | **A** | 研究级文档↔模型可追踪性+不一致检测，活跃度高 |
| 4 | ArDoCo/STD | ArDoCo | Java | 部分(基线) | 有(字符串匹配) | 否 | 否 | 归档(2023) | C | 轻量 TLR 基线，已归档 |
| 5 | **Loom** | juuppe | Python+SQLite+MCP | **有**(loom sync) | **有**(内容哈希) | **部分**(活文档) | **有**(Driftgraph) | **高(2026)** | **A** | 几乎逐点命中总问题，专为 AI/Spec-as-Source 设计 |
| 6 | reqtrace | philipmiesbauer | Python | **有**(RTM 报告) | 有(标签↔需求) | 部分 | 弱 | 高(2026) | B | 需求即代码+RTM，缺漂移检测与真双向同步 |
| 7 | shtracer | qq3g7bad | POSIX Shell | **有**(JSON 矩阵) | 有(层间 FROM 链) | 否 | 部分(标签级) | **高(2026)** | B | 零依赖 CI 原生，标签级一致性检查，无语义漂移 |
| 8 | ReqForge | Haider094 | Python+LangChain | 有(需求↔测试) | 有(测试↔需求) | 否 | 否 | 早期(2026) | C | 需求→测试并产 RTM，但仅覆盖需求↔测试一环 |
| 9 | OpenReqEU | OpenReq 联盟 | 多语言微服务 | 否 | 部分(需求间) | 否 | 否 | 停滞(2020-24) | C | 大型 RE 工具生态，已停滞，不聚焦 Spec↔Code |
| 10 | CoEST Datasets | CoEST | 数据基准 | — | 提供标注链接 | — | — | 静态 | B | 行业标准评测数据，用于验证 RTM 精度 |
| 11 | RETRO.NET Dataset | Notre Dame | 数据基准 | — | 提供 gold standard | — | — | 静态 | B | 需求↔代码追踪评测基准 |

### 最高评分项目
- **A 级**：ArDoCo/Core（研究级文档↔模型追踪+不一致检测）、Loom（RTM 自动生成+漂移检测+双向活文档，最契合范式）
- **B 级**：TraceBERT、reqtrace、shtracer、CoEST Datasets、RETRO.NET
- **C 级**：TraceLab、ArDoCo/STD、ReqForge、OpenReqEU

---

# 第二部分：Spec↔Code 漂移检测（H7：合规偏离 vs 良性演进）

## 一、论文精读与评分（14 篇）

### 1.1 奠基/关键框架论文

| # | 标题 | 作者 | 年份/出处 | 方法要点 | 与 H7 关系 | 评分 |
|---|------|------|----------|----------|-----------|:----:|
| 1 | **Software Reflexion Models** | Murphy, Notkin, Sullivan | 1995 / FSE'95 | 高阶层级模型(HLM)+源码模型(SM)+映射(Map)，得到收敛/发散/缺失三类弧 | 漂移检测奠基机制，但违规/良性裁决靠人工 | **A** |
| 2 | Controlling Software Architecture Erosion: A Survey | De Silva, Balasubramaniam | 2012 / JSS 85(1) | 综述架构侵蚀防治：最小化/预防/修复三类，覆盖一致性检查等全部策略 | 完整问题空间地图，必读背景，无直接判决 | **B** |
| 3 | **Automated Identification of Violation Symptoms** | Li, Liang, Avgeriou | 2023 / arXiv:2306.08616 | 从代码评审评论自动识别架构侵蚀违规症状，SVM+word2vec F1=0.808, GPT-4o F1=0.851 | 自动化检测违规症状，实证强，未分良性 | **A** |
| 4 | A Comparison of Static Architecture Compliance Checking | Knodel, Popescu | 2007 / WICSA | 13 维度对比反射模型/关系一致性/组件访问三类方法 | 合规检查方法选型指南，无判决机制 | **B** |
| 5 | A Unified Approach (Dicto/Probo) | Caracciolo, Lungu, Nierstrasz | 2015 / WICSA | Dictō DSL 声明式约束+Probō 第三方工具编排自动验证 | 规范形式化与合规执行实践，单向合规判定 | **B** |
| 6 | Automated Consistency Checking | Heitmeyer, Jeffords, Labaw | 1996 / ACM TOSEM 5(3) | SCR 表格形式化分析，检测规格内部类型错误/非确定性/缺失分支 | 检查规格内部自洽性，非 Spec↔Code 漂移 | **C** |
| 7 | Deep Just-In-Time Inconsistency Detection | Panthaplackel et al. | 2021 / AAAI (arXiv:2010.01625) | 深度学习学习注释-代码变更相关性，提交前判断不一致 | JIT 漂移检测+更新思路，但仅注释、二分类 | **B** |
| 8 | DocChecker: Bootstrapping Code LLM | Dau, Guo, Bui | 2024 / EACL Demo | 自举方式检测+合成注释修复，ICCD 任务 72.3% 准确率 | 检测+修复闭环，窄作用域(注释)，一律视为错误 | **B** |

### 1.2 最新漂移检测论文（2026）

| # | 标题 | 作者 | 年份/出处 | 方法要点 | 与 H7 关系 | 评分 |
|---|------|------|----------|----------|-----------|:----:|
| 9 | **The Spec Growth Engine** | H. Grabowski | 2026-06 / arXiv:2606.27045 | 机器可读 Spec 图+Spine 上下文组装器+**drift gate**（Spec↔Code 发散作为阻塞合并条件） | 范式核心之作，直接回答"如何检测并阻断漂移"，但未区分违规 vs 良性 | **A** |
| 10 | **ARCTIC (Code Review to Code Critique)** | Maddila et al. | 2026-07 / arXiv:2607.29516 | 意图预测+反向翻译漂移检测+代码聚光，QWK=0.907 | 漂移量化(连续分数)工程化实证强，但意图非正式 Spec | **A** |
| 11 | Beyond Correctness (AQJ) | Vasilevski et al. | 2026-06 / arXiv:2606.14948 | Architecture Quality Judge 智能体评判补丁是否符合架构约定 | 合规性裁决成分，接近但未成漂移框架 | **B** |
| 12 | **DocPrism** | Xu, Wahab, Holmes, Lemieux | 2025/2026 / ISSTA'26 (arXiv:2511.00215) | LCEF 方法，把不一致二分：incompleteness(良性间隙) vs incorrectness(实质违规)，只报警后者 | 误标率从 98%→14%，F1 从 0.22→0.77，**直接命中 H7 区分核心** | **A** |
| 13 | Documentation Drift Review | Mohamed et al. | 2025 / MIUCC | 文档漂移综述，覆盖启发式/同步/AI/LLM 方案 | 背景与趋势参考价值高，无判决机制 | **B** |
| 14 | CARL-CCI: Larger Is Not Always Better | Nguyen et al. | 2025 / SANER 2026 (arXiv:2512.19883) | 结构化代码 diff 分解为 ADD/DEL/KEEP 活动序列，CodeT5+ 检测 | F1 最高提升 13.54%，二分类，窄作用域 | **B** |

### 论文评分汇总

| 评分 | 篇数 | 条目 |
|:----:|:----:|------|
| A | 5 | #1(Reflexion Models)、#3(违规症状)、#9(Spec Growth Engine)、#10(ARCTIC)、#12(DocPrism) |
| B | 8 | #2(综述)、#4(对比)、#5(Dicto)、#7(JIT)、#8(DocChecker)、#11(AQJ)、#13(综述)、#14(CARL-CCI) |
| C | 1 | #6(Heitmeyer SCR) |

**关键发现**：对 H7"区分合规偏离 vs 良性演进"，**DocPrism 的 LCEF** 是唯一显式把不一致二分（incompleteness=良性 vs incorrectness=违规）并只报警后者的工作，命中度最高。

---

## 二、开源项目精读与评分（11 个）

| # | 名称 | 组织 | 技术栈 | 漂移检测 | 架构一致性 | Spec↔代码对比 | 合规偏离识别 | 活跃度 | 评分 | 一句话理由 |
|---|------|------|--------|:--------:|:----------:|:-------------:|:------------:|:------:|:----:|-----------|
| 1 | **ArchUnit** | TNG | Java | 部分(规则) | ✔ | ✘(代码内规则) | 部分(二元) | ★★★★★ | **A** | 生态级架构合规测试库，但属于代码内规则→代码结构校验 |
| 2 | ArchUnitNET | TNG | C# | 部分(规则) | ✔ | ✘ | 部分(二元) | ★★★★ | **B** | ArchUnit C# 移植，生态/体量小于 Java 版 |
| 3 | **jQAssistant** | BUSHIDO | Java+Neo4j | 部分(手写规则) | ✔ | ✘ | 部分(约束) | ★★★★★ | **A** | 图数据库规则/合规引擎，灵活极活跃，但规则手写无自动漂移 |
| 4 | DCL2Check | ASERG-UFMG | Java/Eclipse | ✘ | ✔(规范驱动) | ✔(DCL) | 部分 | ✗(停更) | C | 理念契合(规范驱动合规检查)，但已停更 |
| 5 | HUSACCT | HU Utrecht | Java/C# | ✘ | ✔(SACC) | ✔(意图vs实现) | ✔ | ✗(停滞) | B | 最直白贴合"意图架构 vs 实现"思想，但已停更 |
| 6 | ARCADE | Garcia(UCI) | Java | ✘(衰变度量) | 恢复/度量 | ✘ | ✗ | ✗(停滞) | C | 架构恢复/衰变度量研究台，非 Spec↔Code 漂移 |
| 7 | **ArchGuard** | Tgenz1213 | Go+LLM | ✔(ADR vs 代码) | ✔ | ✔(ADR) | ✔(可解释) | ★★★★★ | **A** | LLM 语义比对 ADR↔代码，可解释违规推理，最贴合合规偏离判定 |
| 8 | **SpecSeal** | xantus-ai | TypeScript | ✔(哈希契约) | 部分 | ✔(spec↔code) | ✔(直观) | ★★★(早期) | **A** | **与 H7 及 Spec-as-Source 契合度最高**：行为契约哈希天然区分文本性编辑与行为性偏离 |
| 9 | DocChecker | FSoft-AI4Code | Python/ML | 注释↔代码 | ✘ | ✘ | ✘ | ✗(停更) | C | 注释不一致检测，非需求 Spec↔代码 |
| 10 | deep-jit-inconsistency | panthap2 | Python/ML | 注释↔代码(JIT) | ✘ | ✘ | ✘ | ✗(研究物) | C | 评论-代码 JIT 研究，非规范驱动 |
| 11 | DriftBench | rigour-labs | Python | ✔(7 类分类学) | ✔(Arch Drift) | 部分 | ✔(基准) | ★★★★ | B | 提供漂移分类学与评测基准，定位评测而非同步工具 |

### 最高评分项目
- **A 级**：ArchUnit（生态级合规测试）、jQAssistant（灵活合规引擎）、ArchGuard（LLM ADR↔代码合规判定）、**SpecSeal**（行为契约哈希，天然区分良性/违规，最贴合 H7）
- **B 级**：ArchUnitNET、HUSACCT、DriftBench
- **C 级**：DCL2Check、ARCADE、DocChecker、deep-jit

---

# 第三部分：双向同步与规范驱动代码再生（Q3：双向同步原子操作）

## 一、论文精读与评分（15 篇）

### 1.1 双向变换理论 / MDE 奠基

| # | 标题 | 作者 | 年份/出处 | 方法要点 | 与 Q3 关系 | 评分 |
|---|------|------|----------|----------|-----------|:----:|
| 1 | **Combinators for Bidirectional Tree Transformations (Lenses)** | Foster et al. | 2005/2007 / POPL/TOPLAS | get/put 成对 lens + 组合子 + PutGet/GetPut 往返律公理 | 定义双向同步原子操作的语义基石（往返律即同步正确性判据） | **A** |
| 2 | **Bidirectional Model Transformations in QVT** | P. Stevens | 2007 / MoDELS | 引入一致性关系(consistency relation)概念，讨论非医源性/正确性/完备性 | 明确"同步"=一致性关系约束下保持两模型同步，规约同步正确性条件 | **A** |
| 3 | GRACE-BX: A Cross-Discipline Perspective | Czarnecki et al. | 2009 / ICMT | 跨 PL/DB/MDE 综述双向变换，统一术语，展望 BX 社区 | 跨学科全景与术语统一，未给具体原子操作 | **B** |
| 4 | **From State- to Delta-Based Bidirectional Model Transformations** | Diskin, Xiong, Czarnecki | 2011 / SoSyM | 从状态级推广到 delta/变化级，建立增量同步代数框架 | 增量双向同步理论分水岭，支撑"变更→只再受影响部分" | **A** |
| 5 | Bidirectionalization for Free! | J. Voigtländer | 2009 / POPL（非 ICFP） | 语义式双向化，从参数多态 get 自动导出 put（free theorem） | 自动补反向的技术路线，但机制受限(纯函数式+参数多态) | **B** |
| 6 | **BiGUL: Formally Verified Putback-Based BX** | Ko, Hu | 2016 / PEPM | 以 put 为第一公民的极简核心语言，在 Agda 中完整形式化验证 | put 反向原子操作可形式化验证编程，反向同步安全内核 | **A** |
| 7 | A Survey of TGG Tools | Hildebrandt et al. | 2013 / ECEASST 57 | 系统调研基于 TGG 的双向模型变换工具（MoTE/eMoflon/HenshinTGG） | 增量双向同步成熟工具版图，但为综述 | **B** |
| 8 | Automation in MDE: A Look Back, and Ahead | Burgueño et al. | 2024 / arXiv:2405.18539 | MDE 自动化历史与 AI 前瞻综述 | 宏观动机与背景，无双向同步机制 | **B** |

### 1.2 最新双向同步 / 规范再生论文（2026）

| # | 标题 | 作者 | 年份/出处 | 方法要点 | 与 Q3 关系 | 评分 |
|---|------|------|----------|----------|-----------|:----:|
| 9 | **JDomInO: Keeping Models and Code in Sync** | Zhang et al. | 2026-08 / arXiv:2608.05612 | 共享元模型 + 正(模型→Java)反(Java→模型)双路径，12 类 building block 验证 | 直接实现模型/代码双向同步与结构再生，正面路径即"规范→代码生成" | **A** |
| 10 | **DeltaMCP: Incremental Regeneration** | Pujara, Zhu, Chen | 2026-05 / arXiv:2605.28148 | OpenAPI 规范变更→Oasdiff 语义差异→端点级变更单元→LoRA 增量再生 MCP 工具 | **几乎完全对应 Q3**：规范变更→定向增量再生受影响代码 | **A** |
| 11 | AssumptionMiner | J. Wu | 2026-07 / arXiv:2607.22898 | 隐式假设作为一等工件，AST 依赖图支持"仅再生受修订假设影响的代码" | 机制接近(变更→定向再生)，但对象是隐式假设而非正式 Spec | **B** |
| 12 | Round-trip Engineering for Tactical DDD (Vision) | Zhang et al. | 2026-03 / arXiv:2603.26987 | DDD 原生元模型+实时约束校验+双向同步的愿景 | 与 Q3 同题但纯愿景，无实现 | **C** |
| 13 | **IncreRTL: Incremental RTL Generation** | Chen et al. | 2026-03 / arXiv:2603.25769 | 需求-代码追踪链接定位→定向增量再生受影响 RTL 代码，配套 EvoRTL-Bench | **直接命中 Q3**：需求变更→追踪定位→增量再生，机制完整 | **A** |
| 14 | Faithful Autoformalization via Roundtrip Verification | Amrollahi et al. | 2026-04 / arXiv:2604.25031 | 往返验证(NL↔形式化) + 诊断引导的受限修复 | 正交问题(NL↔形式化忠实性)，不涉及代码再生 | **C** |
| 15 | Spec-Driven Development: From Code to Contract | D.B. Piskala | 2026-01 / arXiv:2602.00180 | 提出 spec-first/spec-anchored/spec-as-source 三级，分析工具链 | Spec-as-Source 范式纲领指南，无双向同步原子操作 | **C** |

### 论文评分汇总

| 评分 | 篇数 | 条目 |
|:----:|:----:|------|
| A | 7 | #1(Lenses)、#2(QVT)、#4(Delta-BX)、#6(BiGUL)、#9(JDomInO)、#10(DeltaMCP)、#13(IncreRTL) |
| B | 5 | #3(GRACE-BX)、#5(Bidir for Free)、#7(TGG Survey)、#8(MDE Automation)、#11(AssumptionMiner) |
| C | 3 | #12(DDD Vision)、#14(Autoformalization)、#15(SDD Guide) |

**关键发现**：对 Q3"双向同步原子操作"，最直接命中的是 **DeltaMCP**（OpenAPI 规范变更→增量再生）与 **IncreRTL**（需求变更→追踪定位→增量再生）；**JDomInO**（共享元模型双向同步）同样高度契合。Lenses/QVT/Delta-BX/BiGUL 提供语义与形式化地基。

---

## 二、开源项目精读与评分（9 个）

| # | 名称 | 组织 | 技术栈 | 双向同步 | 规范驱动代码生成/再生 | 活跃度 | 评分 | 一句话理由 |
|---|------|------|--------|:--------:|:---------------------:|:------:|:----:|-----------|
| 1 | **GitHub Spec Kit** | GitHub | Python CLI + AI Agent | Agent 驱动(converge/analyze 闭环) | ✔(核心范式) | ★★★★★(2026-08) | **A** | 范式契合度最高且活跃，converge/analyze 实现"Spec 变更→补任务→再实现"闭环 |
| 2 | **OpenAPI Generator** | OpenAPITools | Java | 无原生(全量覆盖再生) | ✔(行业标准) | ★★★★★(2026-08) | **A** | 规范驱动代码生成行业标准，采用价值无可匹敌，但纯单向 |
| 3 | **eMoflon::IBeX** | TU Darmstadt | Java/Xtend + TGG | ✔(TGG 前向/后向，增量解释) | ✔(模型/规则级) | ★★★★(2026-06) | **A** | **真正的**双向变换引擎，增量式同步，与"变更触发再同步"语义最贴合 |
| 4 | Eclipse Epsilon | Eclipse | Java + EGL/ETL/EVL | 无原生(ECL+EVL+EML 拼装) | ✔(EGL) | ★★★★(2026-07) | **B** | 活跃+代码生成强，但双向需人工拼装 |
| 5 | Eclipse Henshin | Eclipse | Java/EMF 就地变换 | 受限(外生 trace) | 部分 | ★★★(2025-06) | **B** | 成熟图变换引擎，双向受限，活跃度下降 |
| 6 | Eclipse ATL | Eclipse (MMT) | Java 声明式 M2M | 无原生(需外部工具) | ✔(单向 M2M→代码) | ★★★(2026-07) | **B** | 经典稳定单向 M2M 标准，无原生双向 |
| 7 | Echo | HASLab | Java+Alloy+QVT-R/ATL | **强**(双向/多向最小修复) | 部分(模型级) | ✗(停更 2018) | **B** | 学术价值极高(双向最小修复)，但已停更 |
| 8 | Boomerang | boomerang-lang | OCaml (lens) | **强**(字符串级 get/put) | 否 | ✗(停更) | **C** | 双向语义(lens)最严谨，但面向字符串而非 Spec→代码 |
| 9 | FunnyQT | JGraLab | Clojure | **有**(funnyqt.bidi) | 否(模型查询/变换) | ✗(停更 2019) | **C** | 自带真双向 API，但定位模型变换且停更 |

### 最高评分项目
- **A 级**：GitHub Spec Kit（范式契合+活跃）、OpenAPI Generator（行业标准）、eMoflon::IBeX（真双向+活跃）
- **B 级**：Eclipse Epsilon、Henshin、ATL、Echo
- **C 级**：Boomerang、FunnyQT

---

# 第四部分：综合评分总表

## 全部论文评分汇总（43 篇）

| 子方向 | 评分 | 篇数 | 论文列表 |
|-------|:----:|:----:|---------|
| 需求可追踪性 (RTM) | **A** | 7 | Gotel(1994)、Trace BERT(2021)、R2Code(2026)、TraceLLM(2026)、NL-PL(Zou 2025)、SpecMap(2026)、ReqToCode(2026) |
| 需求可追踪性 (RTM) | **B** | 7 | Antoniol(2002)、RETRO(2006)、FOSE(2014)、Grand Challenges(2017)、DL(Guo 2017)、RAG(2025)、T-SimCSE(2026) |
| 需求可追踪性 (RTM) | **C** | 0 | — |
| 漂移检测 (H7) | **A** | 5 | Reflexion Models(1995)、违规症状(2023)、Spec Growth Engine(2026)、ARCTIC(2026)、DocPrism(2025) |
| 漂移检测 (H7) | **B** | 8 | 侵蚀综述(2012)、合规对比(2007)、Dicto(2015)、JIT注释(2021)、DocChecker(2024)、AQJ(2026)、漂移综述(2025)、CARL-CCI(2025) |
| 漂移检测 (H7) | **C** | 1 | Heitmeyer SCR(1996) |
| 双向同步 (Q3) | **A** | 7 | Lenses(2005)、QVT(2007)、Delta-BX(2011)、BiGUL(2016)、JDomInO(2026)、DeltaMCP(2026)、IncreRTL(2026) |
| 双向同步 (Q3) | **B** | 5 | GRACE-BX(2009)、Bidir for Free(2009)、TGG Survey(2013)、MDE Automation(2024)、AssumptionMiner(2026) |
| 双向同步 (Q3) | **C** | 3 | DDD Vision(2026)、Autoformalization(2026)、SDD Guide(2026) |
| **总计** | **A** | **19** | |
| | **B** | **20** | |
| | **C** | **4** | |

## 全部项目评分汇总（31 个）

| 子方向 | 评分 | 数量 | 项目列表 |
|-------|:----:|:----:|---------|
| 需求可追踪性 (RTM) | **A** | 2 | ArDoCo/Core、Loom |
| 需求可追踪性 (RTM) | **B** | 5 | TraceBERT、reqtrace、shtracer、CoEST Datasets、RETRO.NET |
| 需求可追踪性 (RTM) | **C** | 4 | TraceLab、ArDoCo/STD、ReqForge、OpenReqEU |
| 漂移检测 (H7) | **A** | 4 | ArchUnit、jQAssistant、ArchGuard、SpecSeal |
| 漂移检测 (H7) | **B** | 3 | ArchUnitNET、HUSACCT、DriftBench |
| 漂移检测 (H7) | **C** | 4 | DCL2Check、ARCADE、DocChecker、deep-jit |
| 双向同步 (Q3) | **A** | 3 | GitHub Spec Kit、OpenAPI Generator、eMoflon::IBeX |
| 双向同步 (Q3) | **B** | 4 | Eclipse Epsilon、Henshin、ATL、Echo |
| 双向同步 (Q3) | **C** | 2 | Boomerang、FunnyQT |
| **总计** | **A** | **9** | |
| | **B** | **12** | |
| | **C** | **10** | |

---

# 第五部分：关键发现与空白分析

## 针对三个子问题的核心结论

### Q1：RTM 自动化生成（从 Spec 条款到代码实例的映射）

**最佳方案**：R2Code（LLM 自反思+动态检索，F1+7.4%、token-41.7%）+ TraceLLM（提示工程 SOTA F2）形成"LLM 追踪链路"层，配合 Loom（`loom sync` 自动生成活文档式 RTM）+ ArDoCo/Core（文档↔模型追踪链接）。**方法演进路径**：词法 IR(2002) → 语义 DL(2017) → 预训练 BERT(2021) → LLM+Agent(2025-2026)。

### Q2：Spec↔Code 漂移检测（区分合规偏离 vs 良性演进）

**最佳方案**：**DocPrism** 的 LCEF 方法（显式区分 incompleteness=良性 vs incorrectness=违规，误标率 98%→14%，F1 0.22→0.77） + **Spec Growth Engine** 的 drift gate（漂移作为阻塞合并条件）+ **SpecSeal** 的行为契约哈希（文本性编辑自动豁免）。**核心空白**：目前无专门论文显式同时处理"检测→量化→违规/良性分类→阻断/豁免"完整闭环。

### Q3：双向同步原子操作（Spec 变更→代码再生/标记待更新）

**最佳方案**：**DeltaMCP**（OpenAPI 变更→定向增量再生 MCP 工具）+ **IncreRTL**（需求变更→追踪定位→增量再生 RTL）+ **JDomInO**（共享元模型双向同步）+ **GitHub Spec Kit**（Agent 驱动 converge 闭环）。**理论地基**：Lenses（往返律）、QVT（一致性关系）、Delta-BX（增量同步代数）、BiGUL（可验证 put）。**核心空白**：目前无项目同时满足"确定性双向同步 + 直接面向代码文本 + 活跃维护"。

## 交叉空白

1. **"L1/L2 条款→代码实例"的细粒度双向追踪**：现有工具多为文档/需求级（整个人工制品），而非条款级（L1/L2 逐条）。ReqToCode 的 Traceable 元素概念最接近，但无实证。
2. **"合规偏离 vs 良性演进"的自动区分**：DocPrism 的 LCEF 是唯一直接方案，但作用域限于注释/文档。SpecSeal 的哈希契约可区分文本编辑 vs 行为变更，但仅限 TS/JS。
3. **"确定性的双向同步 + 标记待更新"**：DeltaMCP 和 IncreRTL 是"变更→再生"的落地标杆，但缺少"标记待更新"（而非自动再生）的降级路径。ReqToCode 的分级生命周期（弃用警告→构建失败）填补了这一空缺，但尚无实证。
4. **形式化 BX 理论与 AI 时代的衔接**：Lenses/TGG/Delta-BX 提供了严格的数学基础，但与 LLM 代码生成/Agent 驱动的工作流之间缺乏桥接。

---

*本文件由 6 个子 agent 并行精读后汇总生成。全部 43 篇论文和 31 个项目均通过 WebFetch 抓取 arXiv/IEEE/ACM/Springer/GitHub 页面确认，各子 agent 报告的详细精读内容可作为独立文件查阅（见工作区对应文件）。*