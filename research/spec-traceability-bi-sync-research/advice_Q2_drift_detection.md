# Q2 建议：Spec-Code 漂移的实时检测与报告
## —— Spec-as-Source 范式下如何高效检测漂移（H7），并区分"合规性偏离"与"良性演进"

> 研究总问题：Spec-as-Source 范式下，如何实现从 Spec 到代码的可追踪性与双向同步。本文为子问题 Q2 的建议文档。
> 撰写日期：2026-08-15。
> 证据基础：工作区综合评分总表（`/workspace/spec_as_source_survey_master_review.md`）、方向 2 清单（`/workspace/collection_2_drift_detection.md`）、漂移方向 14 篇论文精读报告（`/workspace/Spec_Code_Drift_14papers_精读报告.md`）、11 个开源项目精读（`/workspace/spec-code-drift-projects-review.md`），并交叉参考 collection_1（ReqToCode 降级生命周期）与 RTM 项目报告（Loom Driftgraph）。关键论文均已通过 arXiv 原文/摘要页复核：DocPrism（arXiv:2511.00215，ISSTA'26/PACMSE Vol.3）、Spec Growth Engine（arXiv:2606.27045）、ARCTIC（arXiv:2607.29516）、违规症状自动识别（arXiv:2306.08616 v6）。

---

## 0. 核心结论速览（TL;DR）

1. **没有任何单一工作覆盖"检测 → 量化 → 违规/良性分类 → 阻断/豁免"完整闭环**（总表第五部分的核心空白发现）。Q2 的答案必然是**组合方案**，而非单点工具。
2. 推荐三层流水线：**检测层**（哈希 → 结构 → LLM 语义的漏斗式编排）、**分类层**（DocPrism LCEF 语义二分 + SpecSeal 行为契约哈希的确定性触发）、**处置层**（drift gate 硬阻断 + ReqToCode 式降级生命周期 + 带审计的人工豁免）。
3. 关键实证锚点：DocPrism LCEF 将误标率从 **98% 降到 14%**、F1 从 **0.22 升到 0.77**（消融实验），且跨 4 语言零微调保持 17% 低误标率与 0.63 精度；ARCTIC 漂移检测与人工标注近完美一致（**QWK=0.907**），试点中使代码错位额外降低 5.76 分（p=0.026）；违规症状辅助使开发者检测率从 **25.9% 升到 64.7%**。
4. "合规性偏离 vs 良性演进"不是单一特征可判，应由四个判据合成：**行为契约是否变化**（哈希）、**不一致的性质**（incompleteness/incorrectness）、**影响面与可逆性**（blast radius）、**是否有显式意图背书**（变更是否可追溯到 Spec/ADR 修改）。

---

## 1. 问题定义

### 1.1 漂移是什么

在 Spec-as-Source 范式下，Spec 是系统意图的权威表述，代码是意图的实现证据。**漂移（drift）** 即意图与证据之间的分歧：Spec 声称的行为/约束/边界与代码实际呈现的不一致。Reflexion Models（Murphy, Notkin, Sullivan, FSE'95）早已给出结构化刻画：对比高阶层级模型（HLM）与源码模型（SM）后得到三类弧——**收敛（convergence）、发散（divergence，代码有而设计未预测）、缺失（absence，设计预测而代码没有）**——后两者即漂移信号。Spec Growth Engine（Grabowski, arXiv:2606.27045）将其现代化表述为：**Intent Graph**（从 SPEC.md 派生的契约、不变量、验收标准）与 **Evidence Graph**（从代码静态分析派生的 imports/exports、routes/events、tests）之间的分歧。

漂移检测的目标不是"发现所有分歧"，而是**在分歧造成代价之前，把真正有害的分歧（合规性偏离）与无害甚至有益的分歧（良性演进）区分开，并以合适力度处置**。这正是 H7 的完整表述。

### 1.2 漂移检测为什么难：五个结构性原因

**（1）自然语言与编程语言之间的语义鸿沟。** Spec 是 NL，代码是 PL，两者不存在可靠的字面对应。Zou 等（arXiv:2509.05585）的大规模实证直接表明"NL-PL 追踪需要的远不止文本相似度"，需要图结构+LLM 多策略才能较 HGNNLink 提升 F1 +3.68%/+8.84%（12 个项目）。这意味着**漂移检测不可能退化为文本 diff 或相似度阈值问题**。

**（2）抽象间隙是天然的，直接报警会引发误报风暴。** 文档天然比代码更简洁，"代码细节未被文档覆盖"（DocPrism 称之为 under-promise / incompleteness）是常态而非错误。DocPrism 的实验量化了这个灾难：让 LLM 用标准提示直接判断代码-文档不一致，**LLaMA3.1-70B 会把 90–97% 的函数标为不一致，GPT-4.1 也达 82–91%**（1,991 个真实函数、20 个开源仓库、4 种语言）。如此误标率必然导致告警疲劳与工具被弃用——**区分良性间隙与实质违规不是锦上添花，而是漂移检测可用的前提**。

**（3）漂移是静默的。** 代码变了、Spec 没变，测试照样通过，linter 不报、CI 不报，"系统带着漂移上线"（Spec Growth Engine 第 2.2 节的 silent drift cycle）。在 AI 编码代理每分钟生成数百行代码的时代，陈旧 Spec 引导下的漂移累积速度远超人工开发时代——该论文特别引用了 Reflexion Models 时代即已识别的同一模式，并指出新范式放大了代价。

**（4）双向归因模糊。** 发现不一致时，错的可能是代码，也可能是过时的 Spec。DocPrism 明确指出"往往难以确定是代码还是文档有 bug"，因此其设计目标不是二元判决，而是**找出冲突片段并给出解释**，交由人裁决。任何处置机制都必须承认这种归因模糊性，避免"一律判代码错"的粗暴默认。

**（5）规模与成本的矛盾。** 语义级检测依赖 LLM，全仓库级的语义比对等于"上下文爆炸"（Spec Growth Engine 的第一失效模式；长上下文下模型质量退化有实证支撑，如某强模型在长软工基准上从 32K 到 256K 窗口时表现从 29% 崩到 3%）。因此检测必须**增量、定域、分层**：只在变更影响面上做昂贵检测，全量语义扫描降频到夜间批处理。

### 1.3 "合规性偏离 vs 良性演进"的判据构造

目前**没有一篇专门命名的论文**给出"合规性偏离 vs 良性演进"的完整判据（collection_2 审查结论）。综合现有证据，我们建议用四个正交判据合成决策，每个判据都有可落地的机制对应物：

| # | 判据 | 定义 | 机制对应物与证据 |
|---|------|------|------------------|
| J1 | **行为契约是否变化** | 变化是否触及验收标准/非功能契约等"行为承诺"，还是仅措辞润色、排版、示例更新 | SpecSeal 行为契约哈希：哈希只覆盖 Acceptance/Non-functional 段，"spec 文案的润色改动不触发漂移，只有行为契约变化才标记 stale"（`spec-code-drift-projects-review.md` 第 8 节） |
| J2 | **不一致的性质** | incompleteness（自然间隙：Spec 抽象未覆盖代码细节）= 良性；incorrectness（直接矛盾 direct mismatch、过度承诺 over-promise）= 违规候选 | DocPrism LCEF 的三分类法（arXiv:2511.00215 第 3 节：Over-Promise / Direct Mismatch / Under-Promise），只报 incorrectness |
| J3 | **影响面与可逆性（blast radius）** | 触及根不变量、公开契约、容器边界 = 高影响低可逆 → 违规风险高；仅限节点内部设计、纯重构 = 局部可逆 → 良性概率大 | Spec Growth Engine 治理门（第 5.5 节）："Authority follows blast radius and reversibility"，据此划分 HARD/SOFT/AUTO 三级决策权 |
| J4 | **是否有显式意图背书** | 该代码变化能否追溯到一次正式的 Spec/ADR 变更或明确的变更意图；无背书的变化 = 漂移嫌疑，有背书 = 受控演进 | ARCTIC 意图预测（从对话日志与元数据推断变更缘由，F1=0.86）+ 反向翻译度量意图↔产物分歧（arXiv:2607.29516）；Li/Liang/Avgeriou 从代码评审评论识别违规症状（arXiv:2306.08616） |

**合成决策规则**（建议作为分类层的裁决表）：

| 情形 | J1 契约 | J2 性质 | J3 影响面 | J4 背书 | 裁决 | 处置 |
|------|---------|---------|-----------|---------|------|------|
| A | 未变 | — | — | — | **良性**（文本性编辑） | 自动豁免，无需人工 |
| B | 变化 | — | 局部可逆 | 有（Spec 同提交更新） | **良性演进**（受控演化） | 放行（对应 SGE Rule 5 / AUTO 门） |
| C | 变化 | incorrectness | 任意 | 无 | **合规性偏离候选** | 进入处置层（阻断或降级警告） |
| D | 变化 | incompleteness | 任意 | 无 | **文档缺口**（良性但欠账） | 不阻断，记入 Spec 补全待办 |
| E | 变化 | 判定不确定 | 高影响低可逆 | 无 | **灰区** | 人工裁决：修复 / 追认（补 Spec）/ 限期豁免 |

该表的要点：**良性演进不是"没检测出来"，而是"被检测出来并被裁决放行"**——每一次放行都应留下记录（情形 B 要求 Spec 与代码同提交更新，这正是 Spec Growth Engine 的核心不变量："spec and code may never diverge silently"）。

**漂移类型的报告维度**可借用 DriftBench 的 7 类分类学（Staleness、Security、Architecture、Pattern、Logic、Standard、Agent Team Drift，`spec-code-drift-projects-review.md` 第 11 节）作为报告标签，其中 Architecture Drift 与合规性偏离概念高度吻合；该基准还专门针对"语法正确+测试通过但违反设计模式"的漂移构造评测——恰好对应漂移的"静默性"特征。

---

## 2. 推荐技术路线：检测层 → 分类层 → 处置层

### 2.1 检测层：三通道证据采集，漏斗式编排

三种检测机制在成本、确定性、语义深度上互补，应按"**先便宜后昂贵、先确定后模糊**"编排成漏斗：

**通道一：契约哈希（确定性触发器，O(1) 级成本）**
- 机制：Spec 条款带稳定 ID，行为契约段计算哈希；代码以注解引用（SpecSeal：`// @spec REQ-ID #hash`，Markdown Spec + 哈希绑定注解扫描）。检测输出三类信号：**stale 注解**（契约哈希已变）、**孤儿注解**（引用不存在的条款）、**未实现需求**（有条款无引用）。
- 性质：零语义理解、零误报（就"是否变化"而言是确定性的），但**只能回答"变没变"，不能回答"变化有害与否"**。
- 辅助证据：Loom（`loom link` 内容哈希 + Driftgraph 声明图 + 三层漂移告警通道）在 scope 限定下达到 **recall 100% / FPR 12%**（约 1,050 次试验，`RTM自动化开源项目精读报告.md`），说明哈希/声明图通道在限定范围内非常可靠。

**通道二：结构化比对（确定性规则，秒级成本）**
- 机制：Reflexion Models 式的模型对比（HLM vs SM，得到 divergence/absence 弧，可在分钟级处理数十万行代码）；以及结构规则引擎——ArchUnit（Java，v1.5.0/2026-08，2,717 commits，架构规则作为单测在 CI 运行）、ArchUnitNET（C# 移植）、jQAssistant（代码入 Neo4j，Cypher 写 concepts/constraints，v2.9.1/2026-02）。
- Spec Growth Engine 给出四类**结构性硬错误**的可直接移植清单：孤儿代码（源文件无 Spec owner）、未声明依赖（跨 Spec 边界 import）、绕过契约的依赖（import 他节点内部文件）、缺失依赖契约（目标节点无契约）。这四类都是**不需要语义理解即可判定**的漂移。
- 性质：高精度、可解释、零 LLM 成本，但表达力受限于可形式化的结构约束（Knodel & Popescu 2007 的 13 维对比表明没有一类方法全谱系覆盖）。

**通道三：LLM 语义检测（模糊语义，分钟级成本）**
- 机制与证据：
  - **DocPrism LCEF**（代码↔文档不一致检测与解释，跨 Python/TS/C++/Java）；
  - **ArchGuard**（Tgenz1213，Go CLI）：用 LLM（Ollama/OpenAI/Gemini）+ 向量检索语义比对代码变更与 ADR，输出 `[VIOLATION]` + 推理理由，支持 delta 索引、缓存、CI 退出码（注意与 Thoughtworks archguard 区分）；
  - **ARCTIC**（Microsoft 团队，arXiv:2607.29516）：漂移检测用**反向翻译**（backtranslation）度量开发者意图与代理输出的分歧，输出**连续漂移分数**而非二分类，与人工标注 **QWK=0.907**；配套 code spotlight 以 **5 倍更少的 token** 实现 2.4 倍于基线的评审质量估计——这是"只让 LLM 看最可疑区域"的直接证据；
  - **违规症状识别**（arXiv:2306.08616）：从**代码评审评论**这一被忽视的文本源检测架构侵蚀症状，SVM+word2vec F1=0.808，GPT-4o F1=0.851（OpenStack Nova/Neutron、Qt Base/Creator 四项目验证）——可作为检测层的**异步补充通道**，把评审讨论变成漂移信号源。
- 性质：唯一能跨越 NL-PL 语义鸿沟的通道，但成本高、有概率性误报，必须限制在 diff 作用域或哈希/结构通道标记的可疑区域。

**漏斗编排**：每次变更先过通道一（哈希比对，逐文件 O(1)）→ 哈希变化或结构规则触发 → 进入通道二/三；通道三只在被标记的切片上运行（ARCTIC spotlight 式聚焦）。全仓库语义扫描（DocPrism 支持 post-hoc、不依赖 diff）降为夜间批处理。这样把昂贵语义检测的调用量压缩到"契约确实变化"的子集上。

### 2.2 分类层：违规 vs 良性的二分机制

这是 H7 的核心，也是现有文献最薄的一环——总表明确指出 DocPrism LCEF 是**唯一显式把不一致二分并只报警违规侧**的工作。推荐以 LCEF 为语义裁决核心、SpecSeal 哈希为确定性前置的组合。

**（1）DocPrism LCEF 的机制细节（arXiv:2511.00215）**

LCEF = Local Categorization, External Filtering，两个组件：
- **Local Categorization**：把"判断不一致"从长程推理问题改写为**局部补全问题**——让 LLM 对具体冲突片段做三分类（Over-Promise：文档承诺了但代码未实现；Direct Mismatch：代码与文档逻辑冲突；Under-Promise：代码细节未被文档覆盖），配合 chain-of-thought 抑制臆断。前两类是 incorrectness（实质违规），第三类是 incompleteness（良性间隙）。
- **External Filtering**：在 LLM 输出之外用程序化过滤，把 under-promise 类不一致系统性地滤出报警集。

实证（均已复核原文）：
- 消融实验：**误标率从 98% 降到 14%，F1 从 0.22 升到 0.77**；整体精度从 0.14 升到 0.71；
- 4 语言（Python/TS/C++/Java）广谱评测：零微调保持 **17% 低误标率、0.63 精度**；
- 报警质量：**超过 96% 被surface 的不一致是 incorrectness 型**；
- 真实世界鲁棒性：真实 Java 数据集上 DocPrism 精度 0.47–0.67，而 SOTA 工具 C4RLLaMA 从合成数据集上的 0.83 **暴跌到 0.05–0.14**（分布偏移）——说明分类层方案必须在"自然发生的不一致"上校准，不能只信合成基准；
- 问题规模锚点：人工验证给出保守下界，**约 11% 的真实代码-文档对存在 incorrectness 不一致**——漂移不是边缘现象，值得常设门禁。

**（2）SpecSeal 行为契约哈希的机制细节**

SpecSeal（xantus-ai，TS CLI，pre-1.0/v0.1）把 J1 判据做成了确定性机制：Spec 用带稳定 ID 的 Markdown 编写，哈希**只覆盖行为契约段**（Acceptance/Non-functional）；代码用 `// @spec REQ-ID #hash` 注解绑定。由此：
- Spec 文案润色 → 契约哈希不变 → **不触发漂移**（文本性编辑自动豁免，情形 A）；
- 行为契约变化 → 哈希变化 → 引用该契约的代码被判 **stale**（进入分类/处置，情形 C/E）；
- 同时检出孤儿注解与未实现需求（可追踪性断链信号，与 Q1 联动）。
- 局限（必须如实评估）：仅 TS/JS 扫描器、单作者、无正式 Release；哈希只判"变没变"，**变好变坏仍需语义层裁决**。

**（3）组合论证：为什么是"哈希触发 + LCEF 裁决"**

两者各补对方短板，形成职责分离的二分机制：

| 职责 | SpecSeal 哈希 | DocPrism LCEF |
|------|--------------|---------------|
| 回答的问题 | 行为契约**变没变**（确定性触发） | 变了之后**是违规还是间隙**（语义裁决） |
| 误报特性 | 语义层面零误报，但无语义判断力 | 有 14–19% 误标率，需豁免/复核兜底 |
| 成本 | O(1)，可在 pre-commit 运行 | LLM 调用，须限作用域 |
| 对应判据 | J1 | J2（辅以 J3/J4） |

组合后的决策流：
1. 哈希未变 → 情形 A，直接放行，**不启动 LLM**（成本与误报双省）；
2. 哈希变化 + 变更提交中同步更新了 Spec（J4 背书成立）→ 情形 B，按受控演进放行，走治理门分级（见 2.3）；
3. 哈希变化且无同提交背书 → 触发 LCEF 语义裁决：incorrectness → 情形 C 进入处置；incompleteness → 情形 D 记为文档缺口待办；不确定 + 高影响面 → 情形 E 人工裁决；
4. ARCTIC 式连续漂移分数与 spotlight 排序用于**灰区优先级排序**，不直接做二分（其 QWK=0.907 的序数一致性适合排序而非阈值判决；试点中该分数使代码错位额外降 5.76 分，p=0.026）。

**（4）辅助分类信号**
- **违规症状通道**（arXiv:2306.08616）：评审评论中的违规症状识别作为异步信号源；受控实验证明把检测到的症状反馈给开发者可把检测率从 25.9% 提到 64.7%——人在环不仅兜底误报，还实质提升召回。
- **AQJ**（arXiv:2606.14948）：Architecture Quality Judge 用 source-grounded rubrics 评判补丁是否符合仓库架构约定（微调后 SWE-bench Verified 解决率最高 27.2%，较基线最高 +540%），可作为灰区裁决的补丁级合规打分器。
- **DriftBench 7 类分类学**：作为漂移报告的标签体系与自评测基准（用 golden_patch + drift_candidates 回归验证检测器本身）。

### 2.3 处置层：drift gate / 降级生命周期 / 人工豁免

分类结果必须落到有力度梯度的处置上，否则检测没有牙齿；力度单一（全部阻断）则会逼出"绕开门禁"的反模式。推荐三级处置：

**（1）硬阻断（drift gate）**
- 依据：Spec Growth Engine 把 spec-code 分歧定义为**阻塞性合并条件**，并给出四类无条件阻断的硬错误（孤儿代码、未声明依赖、绕过契约的依赖、缺失依赖契约）——这四类本质是**可追踪性断链**，无良性解释空间，适合直接 fail CI。
- 关键不变量："spec and code may never diverge silently"：修复路径首选是 **AI 代理在同一提交内更新受影响的 Spec**，人只审批契约级变化——即把"改代码必须改 Spec"从纪律问题变成结构强制。
- 工程落点：ArchGuard 已提供 CI 退出码与 GitHub Actions；ArchUnit/jQAssistant 的规则违反天然是测试失败。

**（2）降级生命周期（graduated degradation）**
- 依据：ReqToCode（arXiv:2603.13999）的 Traceable 元素携带**分级生命周期**：需求变更时从**弃用警告逐步升级到构建失败**，"给团队可操作的信号而非突然断裂"。这填补了"立即阻断"与"永久豁免"之间的空白——允许良性演进在限定窗口内存在，但债务随时间自动加重。
- Spec Growth Engine 的三类**不阻断只告警**信号同样适合此档：声明了依赖但无代码证据、公开导出未写入契约、契约行为缺测试证据。
- 该机制对"归因模糊"（1.2-(4)）尤其重要：当分不清代码错还是 Spec 过时，先降级警告并要求限期归因，比直接阻断更符合工程现实。注意 ReqToCode 为未评审 preprint、无实证，落地需自行验证。

**（3）人工豁免（acknowledged benign evolution）**
- 依据：Reflexion Models 的传统是发散弧交由工程师解释；ArchGuard 提供 `archguard-ignore` 抑制机制（"人工确认后免检"）。豁免是良性演进的最终确认通道，但必须**可审计、可过期**：每条豁免记录理由、裁决人、关联 Spec 条款、有效期；到期后自动重新进入检测（要么补 Spec 追认，要么重新告警）。
- 治理门分级（Spec Growth Engine 第 5.5 节）给出豁免/审批力度的判据：**HARD**（根不变量、新容器边界、破坏性契约变更 → 合并前人工批准）、**SOFT**（新组件边界、增量契约变更 → 可先行，异步人工评审）、**AUTO**（内部设计、所属节点内纯重构 → 引擎策略自决）。这实际上是把 J3 判据制度化。

**处置决策表汇总**：

| 分类层输出 | 处置 | 对应机制先例 |
|-----------|------|--------------|
| 结构性断链（孤儿/未声明依赖等） | 硬阻断 | SGE 硬错误 + drift gate |
| incorrectness + 高影响面 + 无背书 | 硬阻断或 HARD 门人工批准 | SGE 治理门、ArchGuard 退出码 |
| incorrectness + 局部 + 无背书 | 降级警告，限期修复或追认 | ReqToCode 生命周期 |
| incompleteness（文档缺口） | 不阻断，进 Spec 补全待办 | DocPrism under-promise 过滤 |
| 确认良性演进 | 记录豁免（含过期时间），同步补 Spec | archguard-ignore + 豁免审计 |

### 2.4 组合方案：端到端流水线

```
                    ┌──────────────────────────────────────────────┐
   Spec 仓库         │  SPEC.md（稳定 ID + contract/design 分离）      │
  (L1/L2 条款) ────► │  行为契约段（Acceptance/NFR）→ 契约哈希           │
                    └──────────────┬───────────────────────────────┘
                                   │ 代码注解 // @spec REQ-ID #hash
                                   ▼
 ① 哈希通道   契约哈希比对 ── 未变 → 放行（情形A）
 (pre-commit)              └ 变化 → ↓
 ② 结构通道   结构规则（ArchUnit/jQAssistant）+ SGE 四类硬错误
 (每次构建)    └ 硬错误 → 直接阻断；否则 → ↓
 ③ 语义通道   LCEF 分类（DocPrism 式）+ ArchGuard ADR 语义比对
 (仅可疑切片/  └ incorrectness → ④；incompleteness → 文档缺口待办
  PR 级)        └ 灰区 → ARCTIC 式漂移分数排序 → 人工裁决
                                   ▼
 ④ 处置层     HARD：阻断/合并前批准  SOFT：先行+异步评审  AUTO：放行
              降级生命周期（警告→构建失败）；豁免（审计+过期）
                                   ▼
 ⑤ 报告       漂移报告：条款 ID、漂移类型（DriftBench 7 类标签）、
              冲突片段+解释（DocPrism 前端式高亮）、spotlight 排序、
              豁免台账、修复时限
```

**证据汇总表**：

| 组件 | 来源 | 关键证据 |
|------|------|----------|
| 哈希触发 | SpecSeal（项目精读 §8） | 行为契约哈希天然区分文本性编辑与行为性偏离；检 stale/孤儿/未实现 |
| 哈希/声明图可靠性 | Loom Driftgraph（RTM 项目报告） | scope 限定下 recall 100% / FPR 12%（~1,050 次试验） |
| 结构硬错误 | Spec Growth Engine §5.4 | 四类阻断性硬错误 + 三类警告；Intent/Evidence 双图比对 |
| 语义二分 | DocPrism LCEF（arXiv:2511.00215） | 误标率 98%→14%，F1 0.22→0.77，精度 0.63（零微调、4 语言），>96% 报警为 incorrectness |
| 连续漂移分数 | ARCTIC（arXiv:2607.29516） | QWK=0.907；试点错位 -5.76 分（p=0.026）；spotlight 5× 省 token |
| 评审文本通道 | 违规症状（arXiv:2306.08616） | GPT-4o F1=0.851；辅助后开发者检测率 25.9%→64.7% |
| 处置梯度 | ReqToCode（arXiv:2603.13999）+ SGE §5.5 | 弃用警告→构建失败生命周期；HARD/SOFT/AUTO 治理门 |
| 报告分类学 | DriftBench（项目精读 §11） | 7 类漂移分类学 + golden_patch/drift_candidates 评测法 |

### 2.5 风险与局限（如实披露）

1. **DocPrism 作用域是代码↔文档/注释**，从方法级文档推广到正式 L1/L2 需求条款需重新校准（其 ISSTA'26 版本本身即强调真实分布与合成分布的差异）；
2. **SpecSeal 处于 v0.1**（仅 TS/JS 扫描器、单作者），生产采用前建议吸收其机制思想（契约段哈希+注解绑定）自行实现或用 Loom 的内容哈希替代；
3. **ReqToCode 降级生命周期无实证评测**（未评审 preprint），只能作为设计参照；
4. **组合闭环本身无端到端实证**——总表空白分析确认"目前无专门论文同时处理检测→量化→分类→阻断/豁免完整闭环"，本方案是综合创新，**必须在自己项目上做 A/B 校准**（先只告警不阻断，积累精度数据后再上门禁）；
5. ArchGuard（2026-01 首发）等 LLM 合规引擎尚年轻，且 ADR 粒度为"决策级"而非条款级，与 L1/L2 逐条追踪存在粒度落差。

---

## 3. 落地建议

### 3.1 CI 集成点

| 集成点 | 工具/机制 | 集成方式 | 证据/出处 |
|--------|-----------|----------|-----------|
| 结构合规测试 | **ArchUnit**（Java）/ ArchUnitNET（C#） | 架构规则写成单测，随 `mvn test`/CI 运行；依赖、分层、循环、切片约束 | v1.5.0（2026-08），2.3K+ 依赖方；规则二元、无良性/违规区分，适合通道二 |
| 图规则引擎 | **jQAssistant** | 代码扫入 Neo4j，Cypher 写 constraints；适合复杂跨制品约束与漂移查询 | v2.9.1（2026-02）；规则需手写，作为结构层后端 |
| ADR 语义门禁 | **ArchGuard**（Tgenz1213） | GitHub Action 挂 PR：LLM 比对 diff 与 ADR，输出 `[VIOLATION]`+推理；支持退出码、delta 索引、`archguard-ignore` | 项目精读 §7；注意与 Thoughtworks archguard 区分 |
| 契约哈希门禁 | SpecSeal 式 `check`（或自研等价物） | pre-commit + PR gate：stale/孤儿/未实现三类信号，JSON 输出供报告消费 | 项目精读 §8；v0.1 风险见 2.5 |
| 语义批扫 | DocPrism 式 LCEF 流水线 | nightly 全仓库 post-hoc 扫描（不依赖 diff），结果写入漂移报告 | arXiv:2511.00215 §2.2 明确支持 Post Hoc |
| 评审侧信号 | 违规症状分类器 | 评审机器人异步分析评论，发现症状即追加漂移工单 | arXiv:2306.08616 |
| 自评测 | DriftBench 式 golden_patch/drift_candidates | 定期回归验证检测器本身的 Pass Rate/DDR/Accuracy | 项目精读 §11 |

### 3.2 实时性方案：分层检测频率

"实时"应理解为**与变更事件绑定的分层响应**，而非全量实时：

| 时机 | 跑什么 | 预期延迟 | 依据 |
|------|--------|----------|------|
| 保存/pre-commit | 通道一（契约哈希、注解完整性） | 毫秒–秒 | SpecSeal check 为本地 CLI |
| 每次构建 | 通道二（ArchUnit/jQAssistant 规则、SGE 硬错误） | 秒–分钟 | 结构分析本就随构建执行 |
| 每个 PR | 通道三，仅 diff 涉及的可疑切片（哈希变化或结构触发处） | 分钟级 | ARCTIC spotlight 证明聚焦式审查 5× 省 token；Panthaplackel JIT（AAAI'21）与 CARL-CCI（SANER'26，结构化 diff 分解为 ADD/DEL/KEEP 活动序列，F1 最高 +13.54%）证明"变更时刻"检测的价值 |
| 每夜 | 全仓库语义批扫（post-hoc） | 小时级 | DocPrism 不依赖 diff，可扫存量债务 |
| 评审中 | 评审评论违规症状识别（异步） | 随评审 | arXiv:2306.08616 |

要点：**PR 级语义检测只跑在哈希/结构通道标记的区域**；全量语义扫描只做存量清欠。这样"实时"成本与仓库规模解耦。

### 3.3 误报治理

DocPrism 的核心教训是：**误报不是调参问题，而是方法论问题**——不区分 incompleteness/incorrectness，任何 LLM 检测器都会因 >90% 的误标率被弃用（alert fatigue）。治理手段按优先级：

1. **只报 incorrectness**（LCEF 外置过滤）：这是单项收益最大的措施（误标率 98%→14%）；
2. **确定性前置**：哈希/结构通道先筛，LLM 只处理契约确实变化的区域，从源头缩小误报面；
3. **排序代替阈值**：灰区用连续漂移分数 + spotlight 排序呈现（ARCTIC），让评审者先看最可疑的，而不是被均匀噪声淹没；
4. **豁免台账制度**：豁免必须带理由、裁决人、有效期；`archguard-ignore` 式行内抑制只作短效手段，到期自动复检；豁免率本身作为监控指标（豁免率飙升 = 规则失效或团队在绕门禁）;
5. **渐进上线**：第一阶段全部门禁"只告警不阻断"，人工标注积累精度基线（目标参考 DocPrism 的 0.63 精度、17% 误标率）；达标后对结构性断链与高影响面 incorrectness 先转阻断，其余保持降级警告；
6. **人在环校准回路**：把"人工裁决结果"回流为标注数据（违规症状研究表明，展示检测结果本身就把开发者检测率从 25.9% 提到 64.7%——人机协同双向增益）；定期用 DriftBench 式基准回归检测器性能。

**建议监控指标**：误标率（flag rate）、报警精度（抽检）、豁免率与豁免过期履约率、漂移中位修复时长、文档缺口积压数、stale 注解密度。

### 3.4 采用路线图（建议三阶段）

- **阶段 1（约 2–4 周，可观测性）**：给 Spec 条款上稳定 ID 与行为契约段标注；部署哈希通道（SpecSeal 或自研）+ ArchUnit/jQAssistant 结构规则；全部只告警。产出：漂移存量基线报告。
- **阶段 2（约 1–2 月，裁决能力）**：接入 LCEF 式语义分类（先用 DocPrism 验证其在自己语言栈上的表现，再按 2.2 的组合流接入）；部署灰区人工裁决流程与豁免台账；建立 DriftBench 式回归集。产出：精度/误标率基线，处置决策表落地。
- **阶段 3（持续，强制力）**：按 3.3-5 的顺序把达标通道转为阻断（drift gate）；上线降级生命周期（警告→构建失败）；把漂移报告纳入每周架构评审。产出：闭环运营，漂移从"社会/纪律问题"转为"结构上不可能静默发生"（SGE 的目标表述）。

---

## 4. 结论

1. **漂移检测之难是结构性的**：NL-PL 语义鸿沟、天然抽象间隙（直接 LLM 提示误标 >90%）、漂移的静默性（测试与 CI 天然看不见）、双向归因模糊、以及全量语义检测的成本爆炸。任何"单一检测器解决一切"的路线在证据上不成立。
2. **"合规性偏离 vs 良性演进"可以用四维判据操作性定义**：行为契约是否变化（J1，哈希可判）、不一致性质是 incompleteness 还是 incorrectness（J2，LCEF 可判）、影响面与可逆性（J3，治理门可判）、是否有显式意图背书（J4，意图预测/同提交 Spec 更新可判）。良性演进的正确含义是"被检测出并被裁决放行的受控演化"，而非"未被发现的分歧"。
3. **推荐技术路线是三层组合**：检测层用"哈希 → 结构 → LLM 语义"漏斗（SpecSeal 式契约哈希触发、ArchUnit/jQAssistant/SGE 硬错误过滤、DocPrism LCEF/ArchGuard/ARCTIC 聚焦裁决）；分类层用"哈希确定性触发 + LCEF 语义二分"组合（实证：误标率 98%→14%、F1 0.22→0.77、>96% 报警为 incorrectness）；处置层用"drift gate 硬阻断 + ReqToCode 式降级生命周期 + 带审计过期的人工豁免"三级力度，并以 HARD/SOFT/AUTO 治理门按 blast radius 分配决策权。
4. **落地关键在 CI 分层集成与误报治理**：结构/哈希通道随构建实时跑，语义通道只跑可疑切片并辅以夜间全量清欠；上线先告警后阻断，用豁免台账和回归基准持续校准。
5. **诚实的保留**：该闭环在现有文献中无端到端先例（这正是研究空白与机会所在），且关键组件各有成熟度短板（DocPrism 限于代码-文档域、SpecSeal v0.1、ReqToCode 无实证）。建议以自己项目为实验场，先建基线再加强制力，把每一次人工裁决沉淀为分类器的校准数据——这本身就是对 Q2 最有价值的研究贡献方向。

---

## 附：主要证据出处

| 证据 | 出处 |
|------|------|
| LCEF 误标率 98%→14%、F1 0.22→0.77、精度 0.63、17% 误标率、11% 下界、三分类法 | DocPrism, Xu/Wahab/Holmes/Lemieux, arXiv:2511.00215（ISSTA'26, PACMSE Vol.3, DOI:10.1145/3832248），本次已核原文 |
| Intent Graph vs Evidence Graph、四类硬错误、三类警告、HARD/SOFT/AUTO 治理门、六条增长规则、silent drift 与 context explosion | The Spec Growth Engine, Grabowski, arXiv:2606.27045，本次已核原文 |
| 反向翻译漂移检测 QWK=0.907、意图预测 F1=0.86、spotlight 2.4×/5× token、试点 -5.76 分（p=0.026） | ARCTIC, Maddila et al., arXiv:2607.29516，本次已核摘要 |
| 违规症状 SVM+word2vec F1=0.808、GPT-4o F1=0.851、检测率 25.9%→64.7% | Li/Liang/Avgeriou/Wang, arXiv:2306.08616（v6），本次已核摘要 |
| Reflexion Models 三弧与分钟级规模 | Murphy/Notkin/Sullivan, FSE'95（精读报告 §1） |
| 架构侵蚀防治三分类、无单一策略结论 | De Silva & Balasubramaniam, JSS 85(1), 2012（精读报告 §2） |
| 合规检查 13 维对比 | Knodel & Popescu, WICSA 2007（精读报告 §4） |
| JIT 注释漂移检测与更新 | Panthaplackel et al., AAAI 2021, arXiv:2010.01625（精读报告 §7） |
| CARL-CCI 结构化 diff、F1 +13.54% | Nguyen et al., arXiv:2512.19883（SANER 2026）（精读报告 §14） |
| AQJ 补丁合规裁决、27.2%/+540% | Vasilevski et al., arXiv:2606.14948（精读报告 §11） |
| SpecSeal 行为契约哈希、stale/孤儿/未实现、v0.1 状态 | `/workspace/spec-code-drift-projects-review.md` §8 |
| ArchUnit/jQAssistant/ArchGuard/DriftBench 细节 | `/workspace/spec-code-drift-projects-review.md` §1/§3/§7/§11 |
| Loom Driftgraph（recall 100%/FPR 12%，~1,050 试验） | `/workspace/RTM自动化开源项目精读报告.md` Loom 条目 |
| ReqToCode Traceable 与降级生命周期（弃用警告→构建失败） | `/workspace/RTM_可追踪性_Spec到Code_14篇精读报告.md` §14（arXiv:2603.13999） |
| "无工作覆盖检测→量化→分类→阻断/豁免完整闭环"的空白判断 | `/workspace/spec_as_source_survey_master_review.md` 第五部分 |
