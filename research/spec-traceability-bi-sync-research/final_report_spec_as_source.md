# Spec-as-Source 范式下从 Spec 到代码的可追踪性与双向同步：研究总报告

> 日期：2026-08-15
> 研究范围：43 篇论文 + 31 个开源项目，全部经过逐一核验与精读，按 A/B/C 三档评分
> 产出结构：本报告为总入口；三个子问题的详细建议在 `advice_Q1_rtm_generation.md`、`advice_Q2_drift_detection.md`、`advice_Q3_bi_sync.md`；全部论文与项目的逐条精读与评分见 `spec_as_source_survey_master_review.md` 及各方向精读报告。

---

## 一、研究问题（原始提问）

**总问题：在 Spec-as-Source 范式下，如何实现从 Spec 到代码的可追踪性（Traceability）与双向同步？**

三个子问题：

- **Q1 需求追踪矩阵的自动化生成**：如何自动追踪 Spec 中的每条 L1/L2 条款到代码实例的映射关系？
- **Q2 Spec-Code 漂移的实时检测与报告**：如何高效地实现 Spec↔Code 漂移检测（H7），并区分"合规性偏离"与"良性演进"？
- **Q3 双向同步的原子操作**：当 Spec 变更时，如何自动触发代码的再生或标记为待更新？

---

## 二、研究过程与方法

研究分四个阶段完成，全部材料可在本目录逐一复核：

1. **广搜**：三个方向并行检索 IEEE/ACM/Springer/arXiv/GitHub，初版收集 78 条（`collection_1/2/3` 三个清单）。
2. **审查**：逐条核验真实性、作者信息与链接，按"近三个月更新"与"重大意义"两个维度筛选，补充 2026 年最新论文（R2Code、DocPrism、Spec Growth Engine、JDomInO、DeltaMCP、IncreRTL 等）与活跃项目（GitHub Spec Kit、SpecSeal、ArchGuard 等），修正若干归属错误（详见各 collection 文件的"审查说明"）。
3. **精读与评分**：6 个并行精读任务覆盖全部 43 篇论文与 31 个项目，每条按"采用价值、对问题的解决程度、与 Spec-as-Source 范式的适应程度"评 A/B/C 三档（`spec_as_source_survey_master_review.md`）。
4. **建议生成**：三个并行任务分别围绕 Q1/Q2/Q3 交叉阅读全部材料并补读关键论文原文，产出三份建议文档（`advice_Q1/Q2/Q3`）。

---

## 三、研究材料总览与评分

### 3.1 论文评分总表（43 篇：A 19 / B 20 / C 4）

**方向一：需求可追踪性与 RTM 自动化（14 篇，A 7 / B 7）**

| 论文 | 年份 | 核心贡献 | 评分 |
|---|---|---|:--:|
| Gotel & Finkelstein, An Analysis of the Requirements Traceability Problem | 1994 | 领域奠基：pre-RS/post-RS 框架，问题界定 | A |
| Antoniol et al., Recovering Traceability Links between Code and Documentation | 2002 | IR 自动恢复追踪链的开山之作（单向） | B |
| Hayes et al., Advancing Candidate Link Generation (RETRO) | 2006 | 候选链接+分析师反馈的人机协同范式 | B |
| Cleland-Huang et al., Software Traceability: Trends and Future Directions | 2014 | ICSE FOSE 权威综述 | B |
| Cleland-Huang et al., Grand Challenges of Traceability | 2017 | 把"链接演化"写入十年研究议程 | B |
| Guo et al., Semantically Enhanced Traceability Using DL | 2017 | 深度学习进入追踪（Bi-GRU） | B |
| Lin et al., Traceability Transformed (Trace BERT) | 2021 | 预训练+迁移学习，MAP 较 VSM +60.31% | A |
| Wang et al., **R2Code** (COMPSAC 2026) | 2026-04 | 自反思 LLM 框架：F1 +7.4%，token −41.7% | A |
| Alturayeif et al., **TraceLLM** (Requirements Eng. 31(6)) | 2026-02 | 系统化提示工程，8 模型 4 数据集 SOTA F2 | A |
| Hey et al., Requirements TLR via RAG (REFSQ 2025) | 2025 | LLM+RAG 做需求间追踪 | B |
| Zou et al., NL-PL Traceability Needs More than Textual Similarity | 2025-09 | 实证文本相似度不足，图+LLM 策略 F1 +3.68%/+8.84% | A |
| Nipane et al., **SpecMap** | 2026-01 | 层级化 LLM Agent：token −84%、耗时 −80%、符号级映射 | A |
| Wang et al., T-SimCSE | 2026-03 | 免标注 SimCSE+特异性重排 | B |
| Schlathölter, **ReqToCode** (preprint) | 2026-03 | 可追踪性作为编译期可验证的结构属性+分级生命周期 | A |

**方向二：Spec↔Code 漂移检测（14 篇，A 5 / B 8 / C 1）**

| 论文 | 年份 | 核心贡献 | 评分 |
|---|---|---|:--:|
| Murphy et al., Software Reflexion Models | 1995 | 漂移检测奠基机制（收敛/发散/缺失三弧） | A |
| De Silva & Balasubramaniam, Controlling Architecture Erosion: A Survey | 2012 | 架构侵蚀防治权威综述 | B |
| Li et al., Automated Identification of Violation Symptoms | 2023 | 从评审文本自动识别违规症状（GPT-4o F1=0.851） | A |
| Knodel & Popescu, Comparison of Compliance Checking Approaches | 2007 | 13 维方法选型指南 | B |
| Caracciolo et al., Unified Approach (Dictō/Probō) | 2015 | 声明式 DSL 统一合规检查 | B |
| Heitmeyer et al., Automated Consistency Checking of Requirements Specs | 1996 | 规格内部一致性（与 Spec↔Code 漂移错位） | C |
| Panthaplackel et al., Deep Just-In-Time Inconsistency Detection | 2021 | 提交前注释-代码不一致检测 | B |
| Dau et al., DocChecker | 2024 | 代码 LLM 检测+修复注释不一致 | B |
| Grabowski, **The Spec Growth Engine** | 2026-06 | Spec 图+drift gate（漂移作为阻塞合并条件） | A |
| Maddila et al., **ARCTIC** (Code Review to Code Critique) | 2026-07 | 意图↔产物漂移量化（QWK=0.907）+spotlight | A |
| Vasilevski et al., Beyond Correctness (AQJ) | 2026-06 | 补丁级架构合规裁决 | B |
| Xu et al., **DocPrism** (ISSTA 2026) | 2025-11 | LCEF 显式区分 incompleteness(良性) vs incorrectness(违规)：误标率 98%→14%，F1 0.22→0.77 | A |
| Mohamed et al., Documentation Drift Review (MIUCC 2025) | 2025 | 文档漂移治理综述 | B |
| Nguyen et al., CARL-CCI | 2025-12 | 结构化 diff 提升 JIT 检测（F1 +13.54%） | B |

**方向三：双向同步与规范驱动代码再生（15 篇，A 7 / B 5 / C 3）**

| 论文 | 年份 | 核心贡献 | 评分 |
|---|---|---|:--:|
| Foster et al., Combinators for Bidirectional Tree Transformations | 2005/07 | lens 理论（get/put + PutGet/GetPut 往返律） | A |
| Stevens, Bidirectional Model Transformations in QVT | 2007 | 一致性关系语义框架 | A |
| Czarnecki et al., GRACE-BX Cross-Discipline Perspective | 2009 | 跨学科综述 | B |
| Diskin et al., From State- to Delta-Based BX | 2011 | 增量同步代数（弱可撤销/弱可逆） | A |
| Voigtländer, Bidirectionalization for Free! | 2009 | 语义式双向化 | B |
| Ko & Hu, BiGUL | 2016 | 形式化验证的 putback 核心语言 | A |
| Hildebrandt et al., Survey of TGG Tools | 2013 | 增量双向模型变换工具版图 | B |
| Burgueño et al., Automation in MDE | 2024 | MDE 自动化与 AI 前瞻综述 | B |
| Zhang et al., **JDomInO** | 2026-08 | 共享元模型的模型-代码往返工程（正向确定性生成+反向重建） | A |
| Pujara et al., **DeltaMCP** | 2026-05 | OpenAPI 变更→语义 diff→变更单元→LoRA 定向再生 | A |
| Wu, AssumptionMiner | 2026-07 | 隐式假设追踪+AST 定向再生 | B |
| Zhang et al., Round-trip Engineering for Tactical DDD (Vision) | 2026-03 | 愿景论文 | C |
| Chen et al., **IncreRTL** | 2026-03 | 需求变更→追踪定位→增量再生 RTL+验证闭环 | A |
| Amrollahi et al., Faithful Autoformalization via Roundtrip Verification | 2026-04 | NL↔形式化忠实性（与代码再生正交） | C |
| Piskala, Spec-Driven Development: From Code to Contract | 2026-01 | spec-first/spec-anchored/spec-as-source 三级纲领 | C |

### 3.2 开源项目评分总表（31 个：A 9 / B 12 / C 10）

**A 级项目（9 个）**

| 项目 | 所属方向 | 核心价值 |
|---|---|---|
| ArDoCo/Core (KIT KASTEL) | 可追踪性 | 研究级文档↔架构模型追踪+不一致检测，活跃（2026，MIT，55 releases） |
| Loom (jsuppe) | 可追踪性 | `loom sync` 自动生成活文档式 RTM、内容哈希建链、Driftgraph 漂移告警（recall 100%/FPR 12%，scope 限定） |
| ArchUnit (TNG) | 漂移检测 | Java 架构合规测试事实标准（v1.5.0/2026-08，2.3K+ 依赖方） |
| jQAssistant | 漂移检测 | Neo4j 图规则引擎，Cypher 写架构约束（v2.9.1/2026-02） |
| ArchGuard (Tgenz1213) | 漂移检测 | LLM 语义比对 ADR↔代码，可解释违规推理，CI 门禁 |
| SpecSeal (xantus-ai) | 漂移检测 | 行为契约哈希：文案润色不触发、契约变化才标 stale（v0.1，机制最贴范式） |
| GitHub Spec Kit | 双向同步 | 官方 SDD 工具包，`converge` 把 spec-代码差距转为待办任务（v0.16.3/2026-08-13，高度活跃） |
| OpenAPI Generator | 双向同步 | spec-first 代码生成行业标准（纯单向、全量覆盖再生） |
| eMoflon::IBeX (TU Darmstadt) | 双向同步 | TGG 增量双向图变换，模型层真正的双向同步引擎（活跃） |

**B 级项目（12 个）**：TraceBERT、reqtrace、shtracer、CoEST Datasets、RETRO.NET Dataset、ArchUnitNET、HUSACCT、DriftBench、Eclipse Epsilon、Eclipse Henshin、Eclipse ATL、Echo (HASLab)。

**C 级项目（10 个）**：TraceLab、ArDoCo/STD、ReqForge、OpenReqEU、DCL2Check、ARCADE、DocChecker、deep-jit-inconsistency-detection、Boomerang、FunnyQT（多数因停更、作用域错位或粒度过粗）。

### 3.3 证据图景的三个结构性事实

1. **RTM 自动生成研究密集且快速演进**（词法 IR→语义 DL→预训练 BERT→LLM/Agent），但几乎全部是**单向链接恢复**，且基准全部停留在制品级，条款级（L1/L2 逐条）评测集不存在。
2. **漂移检测的瓶颈不是"检出"而是"区分"**：DocPrism 实验证明不加区分的 LLM 检测会把 82–97% 的函数误标为不一致，直接导致告警疲劳与工具被弃用；唯一显式做"良性间隙 vs 实质违规"二分的是 DocPrism LCEF。
3. **双向同步存在"理论-工程断层"**：lens/QVT/delta-BX/BiGUL 提供了严格的形式化地基但停留在模型/字符串层；面向代码文本的落地方案（DeltaMCP、IncreRTL、Spec Kit）活跃但缺少形式化保证。**没有任何现有项目同时满足"确定性双向同步 + 直接面向代码文本 + 活跃维护"**——这正是本研究方向的核心空白与机会。

---

## 四、对三个子问题的建议（详细版见 advice_Q1/Q2/Q3 文档）

### 4.1 Q1：需求追踪矩阵的自动化生成

**核心判断**：RTM 不应是事后恢复的产物，而应是生成过程的内建副产品（trace-by-construction）；事后恢复只作为存量代码的引导与断链修复。Gotel & Finkelstein 的实证表明，多数"可追踪性差"的根源是需求起源结构丢失而非链接断裂。

**推荐方案：双轨制 + 四层流水线**

- **硬轨**（终态）：代码中以标签/原生元素显式声明条款归属——reqtrace 的 `@trace-start/@trace-end`、shtracer 的 `@REQ-001@` 层间标签，最终收敛到 ReqToCode 的语言原生 Traceable 元素（编译期可验证、构建过程自动校验）。
- **软轨**（存量引导）：LLM 流水线自动恢复候选链接，校验后写入 RTM，并逐步固化为硬轨标签。

四层流水线：

1. **候选链生成（高召回低成本）**：SpecMap 式层级裁剪（仓库级→文件级→符号级，token −84%、耗时 −80%、文件级准确率 73.3%）+ TraceBERT/T-SimCSE 嵌入召回兜底。
2. **语义精判（高精度）**：R2Code 的 BAN 跨层对齐+SRCV 自反思校验（F1 +7.4%、token −41.7%）为主力，配 TraceLLM 提示配方（label-aware+diversity 采样，SOTA F2）与 Zou et al. 的图结构/领域信息注入（F1 +3.68%/+8.84%）跨越 NL-PL 语义鸿沟。
3. **人机裁决**：沿用 RETRO 候选链+分析师反馈范式，低置信链接人工确认并回流为 few-shot 示例。
4. **RTM 产出与固化**：Loom `loom sync` 活文档矩阵或 reqtrace/shtracer 标签矩阵入 CI 门禁；已确认链接写回代码标签（软轨→硬轨固化）。

**关键保留**：现有基准（CoEST/RETRO.NET）均为制品级，条款级需自建 gold set，公开指标不可直接外推；认证场景链接必须可审计，纯 LLM 判决不可直接入库。

### 4.2 Q2：Spec↔Code 漂移检测与"合规偏离 vs 良性演进"区分

**核心判断**：没有任何单一工作覆盖"检测→量化→分类→阻断/豁免"完整闭环，答案必然是组合方案。漂移检测之难是结构性的：NL-PL 语义鸿沟、天然抽象间隙（直接 LLM 提示误标 >90%）、漂移静默性、双向归因模糊、全量语义检测成本爆炸。

**"合规性偏离 vs 良性演进"的四维判据**：

| 判据 | 定义 | 机制对应物 |
|---|---|---|
| J1 行为契约是否变化 | 触及验收标准/NFR 还是仅措辞润色 | SpecSeal 行为契约哈希（文案润色不触发） |
| J2 不一致的性质 | incompleteness（良性间隙） vs incorrectness（实质违规） | DocPrism LCEF 三分类（Over-Promise/Direct Mismatch/Under-Promise） |
| J3 影响面与可逆性 | 根不变量/公开契约 vs 局部可逆重构 | Spec Growth Engine HARD/SOFT/AUTO 治理门 |
| J4 显式意图背书 | 变化可否追溯到 Spec/ADR 正式变更 | ARCTIC 意图预测（F1=0.86）+同提交 Spec 更新 |

良性演进的正确含义是"被检测出并被裁决放行的受控演化"，而非"未被发现的分歧"。

**推荐方案：三层流水线**

- **检测层（漏斗编排，先便宜后昂贵）**：契约哈希（SpecSeal 式，O(1)，pre-commit）→ 结构规则（ArchUnit/jQAssistant + Spec Growth Engine 四类硬错误：孤儿代码/未声明依赖/绕过契约依赖/缺失依赖契约）→ LLM 语义（DocPrism LCEF/ArchGuard/ARCTIC spotlight，只跑可疑切片，全仓扫描降为夜间批处理）。
- **分类层（哈希触发 + LCEF 裁决）**：哈希未变直接放行；哈希变化且有同提交 Spec 背书按受控演进放行；其余触发 LCEF 语义二分——incorrectness 进入处置、incompleteness 记为文档缺口待办、灰区用 ARCTIC 连续漂移分数排序后人工裁决。实证锚点：误标率 98%→14%，F1 0.22→0.77，>96% 报警为实质违规。
- **处置层（三级力度）**：drift gate 硬阻断（结构性断链无良性解释空间）→ ReqToCode 式降级生命周期（弃用警告逐级升级到构建失败，填补"立即阻断"与"永久豁免"之间的空白）→ 带审计与过期时间的人工豁免（archguard-ignore 式）。

**落地节奏**：先告警后阻断；结构/哈希通道随构建实时跑，语义通道只跑可疑切片；用 DriftBench 的 7 类漂移分类学做报告标签与检测器自评测。

### 4.3 Q3：双向同步的原子操作

**核心判断**：原子操作应定义为四元组 `sync(δ_spec) = ⟨变更检测, 追踪定位, 增量传播, 验证确认⟩`，原子性指"要么完整达成（无关区域逐字节不变），要么完整放弃（回到旧状态但把受影响区域标记为待更新）"。"标记待更新"不是失败兜底，而是原子操作的一种合法终止态——带升级路径的一致性债务管理。

**三条正确性判据**（来自 BX 理论地基）：

- **往返律**（Foster et al.）：PutGet = 再生必须落实变更；GetPut = 无变更则零扰动。IncreRTL 的任务模板（只生成受影响片段、未变更行区间与接口不变）是 GetPut 的工程化表述；其反面证据是"微小需求修改也会使全量再生结果显著偏离"，即全量再生天然违反 GetPut。
- **一致性关系**（Stevens）：同步目标是回到一致性关系之内而非收敛唯一输出，这为 LLM 再生的非确定性留出语义空间，也解释了全量覆盖再生为何破坏人工定制（非医源性）。
- **增量传播**（Diskin et al.）：沿 delta 局部更新，且传播应可撤销（回滚约束）。

**"自动再生" vs "标记待更新"的路由判据**（任一不满足即降级为标记）：目标区是否纯生成、变更是否可判定、追踪链接是否高置信（IncreRTL 阈值 θ_agg=0.6）、影响是否局部、有无自动验证、生成器是否确定。

**推荐方案：双轨处置路由器 + 三重护栏**

- **变更检测**：结构化 Spec 用 Oasdiff 式语义 diff 切分端点级变更单元（DeltaMCP 实测原始 diff 可超 50 万 token，必须切分）；NL Spec 用 LLM+CoT 分解为原子需求五要素（IncreRTL）；行为契约哈希做低成本预筛（SpecSeal）。
- **追踪定位**：追踪矩阵法（IncreRTL：语法保持分块→层级候选→双维打分→LLM 补链→人工验证）/ AST 依赖图法（AssumptionMiner）/ 层级收窄法（SpecMap，冷启动）。
- **自动再生**：契约/骨架层用确定性模板（OpenAPI Generator/JDomInO 正向路径），语义层用受约束 LLM 再生——三重护栏缺一不可：变更单元（防上下文稀释）、追踪锚点（定位再生范围）、接口冻结（unchanged line ranges，IncreRTL 模板）；定制逻辑经适配层保护（DeltaMCP 实证：资源占用约为全量再生 1/3 以下且质量更优）。
- **标记待更新制度链**：SpecSeal 哈希检测 → ReqToCode 分级生命周期（警告→构建失败）→ Spec Growth Engine drift gate 合并门禁；Agent 驱动场景用 Spec Kit 的 `converge`（差距评估→追加待办任务）。
- **验证与回滚**：编译/测试/仿真+往返校验；一变更单元一提交、门禁前置、验证失败即回退、分级升级窗四层回滚设计。

---

## 五、综合结论与行动建议

### 5.1 贯穿三个子问题的一条主线

三个子问题不是并列的三件事，而是同一条闭环的三个环节：**Q1 产出的追踪矩阵是 Q2 漂移门禁与 Q3 增量再生的定位输入**（IncreRTL 已证明"追踪链接定位→定向增量再生"的用法）。因此建议以"追踪链接"为第一优先级基础设施，先建 Q1，再叠 Q2 门禁，最后上 Q3 再生。

### 5.2 建议的分阶段实施路径

1. **第一阶段（基础设施）**：给 Spec 条款上稳定 ID 与行为契约段标注；部署哈希通道+结构规则（ArchUnit/jQAssistant）；跑通软轨 LLM 流水线（SpecMap 裁剪+R2Code 精判）产出 RTM；全部只告警不阻断，积累漂移存量与链接精度基线。
2. **第二阶段（裁决能力）**：接入 DocPrism LCEF 式语义二分与豁免台账；部署 Q3 路由器，在纯生成区试点确定性再生+受约束 LLM 再生；自建条款级 gold set 与 DriftBench 式回归集。
3. **第三阶段（强制力）**：达标通道转 drift gate 阻断；上线降级生命周期；向 ReqToCode 式编译期 Traceable 硬链接收敛，使漂移"结构上不可能静默发生"。

### 5.3 研究机会（空白即贡献点）

1. **条款级（L1/L2）追踪评测基准缺失**：自建 gold set 既是验收标准，也是可发表的社区贡献。
2. **"检测→量化→违规/良性分类→阻断/豁免"完整闭环无端到端先例**：四维判据（J1–J4）的合成决策表是可验证的研究假设。
3. **形式化 BX 理论与 LLM 再生的桥接**：把 delta-BX 变更代数与 BiGUL 式可验证 put 嫁接到"追踪引导的 LLM 再生"，用测试门逼近往返律，是"确定性双向同步+面向代码文本+活跃维护"这一空白的最有价值切入点。

### 5.4 诚实的保留

- ReqToCode（arXiv:2603.13999）为未评审 preprint 且无实证评测，方向价值高但不宜作为首期唯一依赖；SpecSeal 处于 v0.1（仅 TS/JS）；DocPrism 作用域是代码↔文档，推广到正式 L1/L2 条款需重新校准。
- 组合闭环方案属综合创新，必须先在自己项目上 A/B 校准（先告警后阻断），公开指标不可直接外推。
- 完全无人化的 RTM 与漂移裁决在当前证据下不应作为承诺目标；人机协同（RETRO、豁免台账、评审回流）是精度与可信的来源。

---

## 附：本目录文件清单

| 文件 | 内容 |
|---|---|
| `final_report_spec_as_source.md` | 本报告（总入口） |
| `advice_Q1_rtm_generation.md` | Q1 详细建议：RTM 自动生成的双轨制与四层流水线 |
| `advice_Q2_drift_detection.md` | Q2 详细建议：漂移检测三层流水线与四维判据 |
| `advice_Q3_bi_sync.md` | Q3 详细建议：原子操作四元组与双轨处置路由器 |
| `spec_as_source_survey_master_review.md` | 全部 43 篇论文+31 个项目的精读总结与 ABC 评分总表 |
| `collection_1_requirements_traceability.md` | 方向一审查后精选清单 |
| `collection_2_drift_detection.md` | 方向二审查后精选清单 |
| `collection_3_bi_sync_generation.md` | 方向三审查后精选清单 |
| `RTM_可追踪性_Spec到Code_14篇精读报告.md` | 方向一论文逐篇精读 |
| `RTM自动化开源项目精读报告.md` | 方向一项目逐条精读 |
| `Spec_Code_Drift_14papers_精读报告.md` | 方向二论文逐篇精读 |
| `spec-code-drift-projects-review.md` | 方向二项目逐条精读 |
| `Spec-as-Source_BX_论文精读报告.md` | 方向三论文逐篇精读 |
| `spec-to-code-bidi-projects.md` | 方向三项目逐条精读 |
