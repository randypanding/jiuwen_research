# 需求可追踪性 / RTM 自动化 / Spec→Code 追踪 14 篇论文精读报告

**研究总问题**：Spec-as-Source 范式下，从 Spec（需求/规格）到代码的可追踪性（Traceability）与双向同步。
**评分维度**：① 对总问题及三个子问题（需求追踪矩阵 RTM 自动生成 / Spec↔Code 漂移检测 / 双向同步）的解决与回答程度；② 采用价值；③ 与该范式的适应程度。
**评分等级**：A（强相关、高价值、显著推进） / B（相关但为背景、单向恢复或增量改进） / C（弱相关或未解决核心问题）。

> 说明：所有信息均来自抓取的 arXiv 摘要页、IEEE Xplore 摘要页、Springer 章节页及检索到的摘要片段。IEEE/Springer 部分论文因版权限制仅能获取摘要（Abstract），已逐篇标注可信度。禁止编造——凡未直读原文正文之处，结论以摘要为依据。

---

## 1. An Analysis of the Requirements Traceability Problem

- **作者**：Orlena C. Z. Gotel, Anthony C. W. Finkelstein
- **年份/出处**：1994；Proceedings of the First International Conference on Requirements Engineering (ICRE 1994 / RE'94)，IEEE，pp. 94–101，DOI:10.1109/ICRE.1994.292398
- **可信度**：高（该领域奠基作，摘要与学界共识高度一致）
- **方法要点**：基于对 100+ 从业者的经验研究和现有工具评估，不是提出算法，而是界定"需求可追踪性问题"本身。首创区分 **pre-RS traceability（需求规格之前的追踪）** 与 **post-RS traceability（需求规格之后的追踪）**，说明为何不可能有"包治百病"的统一解决方案，并给出理解其多面性（traceability for whom & why）的框架。
- **关键结论/评价指标**：指出多数"可追踪性差"的问题，根源在于无法追溯需求来源（起源/贡献结构被丢失），而非追踪链本身断裂；强调"谁、为何、如何"追踪决定了方法选择。
- **与 Spec-as-Source 可追踪性与双向同步的关系**：奠定了整个领域的概念地基。pre-RS/post-RS 划分正是"Spec 作为源代码唯一事实来源"这一范式的理论源头——它明确了 Spec 在工程流程中的轴心地位，并指出追踪必须同时覆盖"向前（Spec→实现）"与"向后（回溯源）"两个方向。
- **评分**：**A**
- **一句话理由**：它不是解法，却是定义"Spec-as-Source 追踪与双向同步"这一总问题的奠基之作，理解本领域任何后续工作都绕不开它。

---

## 2. Recovering Traceability Links between Code and Documentation

- **作者**：Giuliano Antoniol, Gerardo Canfora, Gerardo Casazza, Andrea De Lucia, Ettore Merlo
- **年份/出处**：2002；IEEE Transactions on Software Engineering 28(10)，pp. 970–983，DOI:10.1109/TSE.2002.1041053
- **可信度**：高（IEEE 摘要页已直读，含引言）
- **方法要点**：假设程序员为程序元素（函数、变量、类型、类、方法）使用有意义的名字，从标识符助记符中提取应用域知识；用**概率模型（probabilistic IR）**与**向量空间模型（VSM）**两种信息检索模型，在两次案例研究（C++→手册页、Java→功能需求）中自动恢复代码与自由文本文档间的追踪链。
- **关键结论/评价指标**：两种模型均能有效恢复代码-文档追踪链；对比了两者的优缺点并给出改进方向。是"基于 IR 的事后追踪恢复"这一主线的开山之作。
- **与 Spec-as-Source 的关系**：直接对应"Spec→代码链接自动生成"子问题（RTM 自动化的 IR 路线鼻祖）。但它是**单向的事后恢复**，依赖词法/术语重合，尚无漂移检测与双向同步；对 Spec 与代码语义鸿沟处理有限。
- **评分**：**B**
- **一句话理由**：开创了自动追踪链接恢复的主流方法论，但仅止于词法 IR 的单向事后恢复，未触及漂移检测与双向同步。

---

## 3. Advancing Candidate Link Generation for Requirements Tracing: The Study of Methods

- **作者**：Jane Huffman Hayes, Alex Dekhtyar, Senthil Karthikeyan Sundaram
- **年份/出处**：2006；IEEE Transactions on Software Engineering 32(1)，pp. 4–19，DOI:10.1109/TSE.2006.3
- **可信度**：高（IEEE 摘要页已直读）
- **方法要点**：面向验证与确认（V&V/IV&V）分析师的动态候选链接生成。四项贡献：① 依据分析师职责为追踪工具定义目标；② 引入若干新度量来验证目标达成；③ 将**分析师反馈**纳入追踪过程；④ 实现原型工具 **RETRO（REquirements TRacing On-target）**并做实证评估。
- **关键结论/评价指标**：RETRO 有效支持其目标；证明把人为反馈引入候选链接生成可提升追踪质量，并给出可客观测量的目标元素评估结果。
- **与 Spec-as-Source 的关系**：直接服务"RTM 自动生成"子问题——把恢复出的链接作为候选供分析师确认，是"人机协同生成追踪矩阵"的典型范式；仍是单向 IR+反馈，未处理漂移与双向同步。
- **评分**：**B**
- **一句话理由**：是"候选链接生成+分析师反馈"路线的重要代表，但单向、面向人工确认，未解决 Spec↔Code 漂移与双向同步。

---

## 4. Software Traceability: Trends and Future Directions (ICSE FOSE)

- **作者**：Jane Cleland-Huang, Orlena Gotel, Jane Huffman Hayes, Patrick Mäder, Andrea Zisman
- **年份/出处**：2014；ICSE/FOSE (Future of Software Engineering)，pp. 55–69
- **可信度**：中高（抓取到摘要片段："builds upon a prior body of work to highlight the state-of-the-art... compelling areas of research"；作者列表来自学界公认信息，未逐字直读正文）
- **方法要点**：综述/路线图性质。系统梳理软件可追踪性研究现状：对早期工作做了深入分析，发现研究集中于工具与可视化、特定领域应用、以及用 IR 技术实现追踪链的（半）自动化创建。
- **关键结论/评价指标**：强调可追踪性在安全关键系统（如 FAA 认证）中被强制要求，实践中却常被"事后补建"；提出有待解决的研究空白与未来方向。
- **与 Spec-as-Source 的关系**：为"RTM 自动生成/漂移/同步"划定研究版图与缺口，是定位本课题所处坐标的参考；本身不提供具体解法。
- **评分**：**B**
- **一句话理由**：有价值的领域综述与路线图，用于理解上下文与空白，但不对三个子问题给出可落地的解法。

---

## 5. Grand Challenges of Traceability: The Next Ten Years

- **作者**：Giuliano Antoniol, Jane Cleland-Huang, Jane Huffman Hayes, Michael Vierhauser（含社区多篇立场文章）
- **年份/出处**：2017；arXiv:1710.03129（Natural Bridge 研讨会论文集）
- **可信度**：高（arXiv 摘要页已直读）
- **方法要点**：2007 年首届"Grand Challenges of Traceability"会议提出面向"有效、可信、无处不在"的可追踪性研究目标；本文是十年后（2017）的进度评估。围绕追踪实践的四个过程轴（Trace Strategizing 策略制定、Trace Link Creation and Evolution 链接创建与演化、Trace Link Usage 链接使用、实际应用）汇编立场论文，并设两个分会场讨论**追踪数据集/基准的创建与共享**、以及**工业落地采用**的挑战。
- **关键结论/评价指标**：野心是让可追踪性"始终在场、内建于工程流程，并'了无痕迹地消失'"；强调数据集与基准对研究社区的关键作用。
- **与 Spec-as-Source 的关系**：把"链接的创建与演化（Evolution）"明确列为核心挑战之一，直接对应"漂移检测与双向同步"的研究议程；同时呼吁数据集/基准，为 Spec→Code 可追踪研究铺路。属议程设定，非具体解法。
- **评分**：**B**
- **一句话理由**：把"链接演化与维护"正式写入研究议程并驱动数据集建设，为漂移/同步问题提供框架性指引，但无实现方案。

---

## 6. Semantically Enhanced Software Traceability Using Deep Learning Techniques

- **作者**：Jin Guo, Jinghui Cheng, Jane Cleland-Huang
- **年份/出处**：2017；IEEE/ACM 39th ICSE，pp. 3–14（arXiv:1804.02438）
- **可信度**：高（arXiv 摘要页已直读）
- **方法要点**：针对 IR/ML 方法"不理解语义、不整合领域知识"的缺陷，提出用深度学习建模制品语义。提出追踪网络架构：**Word Embedding + 循环神经网络（RNN）**，词嵌入学习领域语料知识，RNN 学习需求制品的句子语义；在 Positive Train Control（列车控制）领域用已有追踪链训练了 360 种配置，选出 **Bi-GRU（双向门控循环单元）** 为最优模型。
- **关键结论/评价指标**：Bi-GRU 显著优于 VSM（向量空间模型）与 LSI（潜在语义索引）等当时 SOTA 追踪方法。是"语义化自动追踪链接生成"的里程碑。
- **与 Spec-as-Source 的关系**：显著推进"RTM 自动生成"子问题的语义层面（Spec 与代码的语义对齐）；但仍为**单向链接恢复**，领域特定（列车控制），且需大量带标签训练数据。
- **评分**：**B**
- **一句话理由**：把语义/领域知识引入自动追踪的关键一步，但单向恢复、领域受限、依赖标注，未触及漂移与双向同步。

---

## 7. Traceability Transformed: Generating More Accurate Links with Pre-Trained BERT Models (Trace BERT / T-BERT)

- **作者**：Jinfeng Lin, Yalin Liu, Qingkai Zeng, Meng Jiang, Jane Cleland-Huang
- **年份/出处**：2021；IEEE/ACM 43rd ICSE，pp. 324–335（arXiv:2102.04411）
- **可信度**：高（arXiv 摘要页已直读）
- **方法要点**：提出 **T-BERT** 框架，用预训练 BERT 在自然语言制品（需求/问题描述）与源码间生成追踪链接。针对**数据稀疏**问题，用**三步训练策略**从数据丰富的相邻 SE 任务迁移知识；对比三种 BERT 架构（Single-/Siamese-/等），并用于恢复开源项目 issue↔commit 链接。
- **关键结论/评价指标**：Single-BERT 准确性最高，Siamese-BERT 以显著更短耗时取得相近结果；三种模型均优于经典 IR。在三个真实 OSS 项目上，最佳 T-BERT 相比 VSM 在 MAP 上平均提升 **60.31%**；RNN 因数据不足严重欠拟合，而 T-BERT 通过预训练+迁移学习克服了该问题。
- **与 Spec-as-Source 的关系**：是"RTM 自动生成"子问题在准确率上的重大突破，并通过迁移学习缓解标注数据瓶颈，具有高采用价值；本质仍是**单向恢复**，未覆盖漂移检测与双向同步。
- **评分**：**A**
- **一句话理由**：以预训练+迁移学习大幅提升 Spec/需求→代码链接准确率（MAP +60%），是 RTM 自动化的核心构建块与广泛采用基线。

---

## 8. R2Code: A Self-Reflective LLM Framework for Requirements-to-Code Traceability

- **作者**：Yifei Wang, Jacky Keung, Xiaoxue Ma, Zhenyu Mao, Kehui Chen, Yishu Li
- **年份/出处**：2026；IEEE **COMPSAC 2026**（arXiv:2604.22432）
- **可信度**：高（arXiv 摘要页已直读）
- **方法要点**：面向需求→代码追踪的 LLM 语义框架，三组件：① **分解增强双向对齐网络（BAN）**，把需求语义四层级与代码结构对齐，支持跨层语义匹配；② **自反思一致性校验（SRCV）**，以"解释引导的一致性检查"标定链接可靠性；③ **动态上下文自适应检索（DCAR）**，按语义重叠权重调整检索粒度、过滤上下文以提效。
- **关键结论/评价指标**：在 5 个跨多领域、两种编程语言的公开数据集上，平均 F1 较最强基线提升 **7.4%**，并通过自适应上下文控制把 token 消耗降低最多 **41.7%**。
- **与 Spec-as-Source 的关系**：直接改进"RTM 自动生成"子问题——跨层级语义对齐+自反思校验提升链接可靠性，动态检索降低推理成本，契合 Spec-as-Source 下大批量 Spec→Code 追踪的经济性要求；仍偏单向恢复，双向同步未展开。
- **评分**：**A**
- **一句话理由**：自反思+动态检索的 LLM 方案在准确率与成本上双优（F1+7.4%、token−41.7%），显著增强大规模 Spec→Code 追踪的可用性。

---

## 9. TraceLLM: Leveraging Large Language Models with Prompt Engineering for Enhanced Requirements Traceability

- **作者**：Nouf Alturayeif, Irfan Ahmad, Jameleddine Hassine
- **年份/出处**：2026；Requirements Engineering 31, 6 (2026)（arXiv:2602.01253 / DOI:10.1007/s00766-026-00460-1）
- **可信度**：高（arXiv 摘要页已直读，含期刊出处）
- **方法要点**：系统化的"提示工程+示例选择"追踪框架。含严格的**数据集划分、迭代式提示细化、上下文角色与领域知识增强**，并在 **zero-shot 与 few-shot** 下评估。用 8 个 SOTA LLM、4 个基准数据集（航空航天、医疗等，覆盖需求/设计元素/测试用例/法规）。
- **关键结论/评价指标**：取得 SOTA **F2 分数**，优于传统 IR 基线、微调模型及此前 LLM 方法；识别出"label-aware、diversity-based"示例采样策略最有效。结论：追踪性能不仅取决于模型容量，更取决于**提示工程质量**；可支撑"候选链接由人工分析师复核"的半自动追踪流程。
- **与 Spec-as-Source 的关系**：把"RTM 自动生成"落到 LLM 提示工程与示例选择这一可工程化层面，强调半自动（人机协同）适配，非常适合 Spec-as-Source 下控制成本与可追溯性的落地；仍为单向链接恢复，双向同步未涉及。
- **评分**：**A**
- **一句话理由**：用系统化提示工程在 8 模型/4 数据集上取得 SOTA F2，把 Spec→代码追踪的自动化落地为可复制、可工程化的半自动流程。

---

## 10. Requirements Traceability Link Recovery via Retrieval-Augmented Generation (REFSQ 2025)

- **作者**：Tobias Hey, Dominik Fuchß, Jan Keim, Anne Koziolek
- **年份/出处**：2025；REFSQ 2025，LNCS，Springer，DOI:10.1007/978-3-031-88531-0_27
- **可信度**：中高（抓取到该章引用列表与作者 LiSSA/RAG 相关资料；摘要来自检索到的论文 PDF 片段，未逐字直读正文）
- **方法要点**：用 **LLM + 检索增强生成（RAG）** 做**需求间（inter-requirements）**可追踪性链接恢复。在六个基准数据集上评估，引入 chain-of-thought（思维链）提示。
- **关键结论/评价指标**：思维链提示有益；**开源模型表现与闭源商模型相当**；方法整体可超越 SOTA 与基线方法。贡献集中在"需求↔需求"链接，而非需求↔代码。
- **与 Spec-as-Source 的关系**：与总问题**部分相关**——它解决的是 Spec 内部（需求间）的追踪一致性，是 Spec 侧事实来源完整性的基础，但不直接覆盖 "Spec→代码" 的跨制品追踪、漂移检测或双向同步。
- **评分**：**B**
- **一句话理由**：RAG 思路对提升 Spec 侧需求间追踪有价值，但对象是需求-需求而非 Spec-code，未触及总问题的跨制品双向同步核心。

---

## 11. Natural Language-Programming Language Software Traceability Link Recovery Needs More than Textual Similarity

- **作者**：Zhiyuan Zou, Bangchao Wang, Peng Liang, Tingting Bi, Huan Jin
- **年份/出处**：2025；arXiv:2509.05585（投稿期刊，45 页）
- **可信度**：高（arXiv 摘要页已直读）
- **方法要点**：通过大规模经验评估揭示：在 NL-PL（自然语言-编程语言）制品追踪中，**仅靠文本相似度有语义鸿沟局限**。据此提出融入多种领域特定辅助策略：在**异构图表 Transformer（HGT）**上以边类型注入策略，在 **prompt-based Gemini 2.5 Pro** 上以附加输入信息注入策略；以需求→代码追踪作为 NL-PL 代表任务评估。
- **关键结论/评价指标**：两种多策略模型均优于未注入策略的原模型；相较于 SOTA 方法 HGNNLink，在 12 个开源项目上多策略 HGT 平均 F1 提升 **3.68%**、Gemini 2.5 Pro 提升 **8.84%**。
- **与 Spec-as-Source 的关系**：正中总问题要害——Spec 是自然语言、代码是编程语言，两者间的语义鸿沟正是 Spec-as-Source 追踪的难点；该文直接把这个鸿沟作为研究主题，通过图结构+LLM 策略改善需求→代码链接，是"RTM 自动生成"在 NL-PL 语义上的强推进。仍为单向恢复。
- **评分**：**A**
- **一句话理由**：用大规模实证证明文本相似度不足以支撑 Spec→代码追踪，并以图+LLM 多策略显著提升需求-代码链接质量，直击范式核心难点。

---

## 12. SpecMap: Hierarchical LLM Agent for Datasheet-to-Code Traceability Link Recovery in Systems Engineering

- **作者**：Vedant Nipane, Pulkit Agrawal, Amit Singh
- **年份/出处**：2026；arXiv:2601.11688
- **可信度**：高（arXiv 摘要页已直读）
- **方法要点**：面向嵌入式系统**数据手册（datasheet）→代码**的层级化 LLM 映射：不做直接的规格-代码匹配，而是**逐层收窄搜索空间**——仓库级结构推断 → 文件级相关度估计 → 细粒度**符号级对齐**；不仅做函数级映射，还覆盖宏、结构体、常量、配置参数、寄存器定义等 C/C++ 系统级代码元素。
- **关键结论/评价指标**：在多个开源嵌入式仓库、手工标注的 datasheet-code 真值上，比传统 IR 基线大幅提升，文件级映射准确率最高达 **73.3%**；把 LLM token 总消耗降低 **84%**、端到端运行时间降低约 **80%**。可支撑规格覆盖分析与标准合规验证等下游应用。
- **与 Spec-as-Source 的关系**：是"Spec→代码可追踪性"的高适配实现——把底层规格（datasheet）作为事实来源，建立到系统级代码的精确链接，并通过层级化裁剪实现大规模成本可控；对"RTM 自动生成"给出符号级细粒度方案。仍为单向链接恢复，未含漂移与双向同步。
- **评分**：**A**
- **一句话理由**：层级化 LLM Agent 把 datasheet→代码追踪做到符号级细粒度，同时大幅降本（token−84%、耗时−80%），高度契合 Spec-as-Source 的大规模落地需求。

---

## 13. Enhancing Requirements Traceability Link Recovery: A Novel Approach with T-SimCSE

- **作者**：Ye Wang, Wenqing Wang, Kun Hu, Qiao Huang, Liping Zhao
- **年份/出处**：2026；arXiv:2603.11800
- **可信度**：高（arXiv 摘要页已直读）
- **方法要点**：基于预训练语言模型 **SimCSE** 的追踪链接恢复方法。先用 SimCSE 计算需求与目标制品的相似度，再用新指标 **specificity（特异性）** 对目标制品重排序，最后在需求与 top-K 目标之间建立链接。**无需标注数据**（无监督）。
- **关键结论/评价指标**：在十个公开数据集上与多种方法对比，T-SimCSE 在 **recall 与 MAP（平均精度均值）** 上取得更优表现。
- **与 Spec-as-Source 的关系**：服务于"RTM 自动生成"子问题，优势是**免标注**、通用性强，缓解了标注数据稀缺痛点；但方法本质是"SimCSE 相似度+特异性重排"的增量改进，未超越相似度范式的语义鸿沟，也未涉及漂移检测与双向同步。
- **评分**：**B**
- **一句话理由**：以无监督 SimCSE+特异性重排在 recall/MAP 上稳步提升 Spec 侧链接恢复，但属增量改进，未突破相似度范式的根本局限。

---

## 14. ReqToCode: Embedding Requirements Traceability as a Structural Property of the Codebase

- **作者**：Thorsten Schlathölter
- **年份/出处**：2026；arXiv:2603.13999（23 页，preprint，未同行评审）
- **可信度**：中（arXiv 摘要页已直读；标注为未评审 preprint）
- **方法要点**：与"事后修复断链"的主流路线相反，主张**预防性追踪**：把可追踪的系统元素直接嵌入代码库，使可追踪性成为**可编译期验证的系统结构属性**，而非外部文档任务。核心概念是 **Traceable**——语言原生、由生成产生的代码元素，代表单条需求并携带元数据；开发者在实现与测试代码中引用 Traceable，形成**硬性、双向的链接**，在**构建过程**中自动校验。需求变更时通过**分级生命周期**响应：从弃用警告到构建失败，给团队可操作的信号而非突然断裂。
- **关键结论/评价指标**：描述了架构原则、Traceable 生命周期，并用一个贯穿"需求定义→制品生成→代码集成→构建期校验"的通用示例说明。属概念/方法学论文，无大规模基准评测。
- **与 Spec-as-Source 的关系**：**与总问题契合度最高**——它把 Spec 直接作为代码库的结构性事实来源，构造"硬性双向链接"，用构建期校验实现**漂移检测**（链接失效即编译失败），并用分级生命周期支撑**双向同步**（需求变更经警告到失败逐级传导）。正好覆盖总问题的三个子问题，是"编译期约束强制同步"的范式代表；但未同行评审、无实证评测，成熟度待验证。
- **评分**：**A**
- **一句话理由**：唯一直接针对"漂移检测+双向同步+Spec-as-Source"三者的方案，用编译期强制链接把可追踪性内建为代码结构属性，方向前瞻，但尚缺实证与评审。

---

## 汇总分级表

| # | 论文（简称） | 年份 | 核心贡献 | RTM自动生成 | 漂移检测 | 双向同步 | 评分 |
|---|---|---|---|---|---|---|---|
| 1 | Gotel & Finkelstein | 1994 | 问题界定 / pre-post-RS 框架 | 半 | — | — | **A** |
| 2 | Antoniol et al. | 2002 | 概率+VSM 恢复链接 | 强(单向) | — | — | **B** |
| 3 | Hayes et al. (RETRO) | 2006 | 候选链接+分析师反馈 | 强(单向) | — | — | **B** |
| 4 | Cleland-Huang et al. (FOSE) | 2014 | 综述/路线图 | 半 | — | — | **B** |
| 5 | Grand Challenges of Traceability | 2017 | 研究与数据集议程 | — | 半(演化) | — | **B** |
| 6 | Guo et al. (Bi-GRU) | 2017 | 语义深度学习链接 | 强(单向) | — | — | **B** |
| 7 | Trace BERT | 2021 | 预训练+迁移学习 | 强(单向) | — | — | **A** |
| 8 | R2Code | 2026 | 自反思 LLM+动态检索 | 强(单向) | — | — | **A** |
| 9 | TraceLLM | 2026 | 提示工程框架 | 强(单向) | — | — | **A** |
| 10 | REFSQ RAG | 2025 | RAG 需求间追踪 | 半(需求↔需求) | — | — | **B** |
| 11 | Zou et al. | 2025 | 超越文本相似度(NL-PL) | 强(单向) | — | — | **A** |
| 12 | SpecMap | 2026 | 层级 LLM Agent | 强(单向) | — | — | **A** |
| 13 | T-SimCSE | 2026 | 无监督 SimCSE+特异性 | 中(相似度) | — | — | **B** |
| 14 | ReqToCode | 2026 | 编译期结构属性追踪 | 中 | **强** | **强** | **A** |

**总体观察**：14 篇中，A 级 7 篇（1、7、8、9、11、12、14），B 级 7 篇（2、3、4、5、6、10、13），无 C 级。绝大多数论文集中在"RTM 自动生成"这一子问题上（且基本为单向链接恢复），方法演进路径为：**问题界定(1994) → 词法 IR(2002/2006) → 语义深度学习(2017) → 预训练 BERT 迁移学习(2021) → LLM/RAG/Agent(2025-2026)**。**"漂移检测与双向同步"是明显的研究空白**，仅 ReqToCode(№14) 以编译期强制链接直接正面回应，其余论文均未覆盖——这正是 Spec-as-Source 范式下最具价值、也最待突破的方向。