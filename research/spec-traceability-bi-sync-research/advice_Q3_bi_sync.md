# Q3 建议文档：双向同步的原子操作 —— Spec 变更时如何自动触发代码再生或标记为待更新

> 总研究问题：Spec-as-Source 范式下，如何实现从 Spec 到代码的可追踪性（Traceability）与双向同步？
> 本文档针对子问题 **Q3：双向同步的原子操作**。
> 证据来源：工作区精读材料（`spec_as_source_survey_master_review.md`、`collection_3_bi_sync_generation.md`、`Spec-as-Source_BX_论文精读报告.md`、`spec-to-code-bidi-projects.md`、`RTM_可追踪性_Spec到Code_14篇精读报告.md`、`Spec_Code_Drift_14papers_精读报告.md`、`spec-code-drift-projects-review.md`），并对 DeltaMCP（arXiv:2605.28148）与 IncreRTL（arXiv:2603.25769）全文做了 WebFetch 原文核实。所有结论均可溯源，未核实之处已显式标注。

---

## 1. 问题定义

### 1.1 "原子操作"的语义

在 Spec-as-Source 范式中，代码是 Spec 的派生制品。当 Spec 发生变更 δ，系统必须执行一次**同步原子操作**，把代码从"与旧 Spec 一致"推进到"与新 Spec 一致"。我们将这个原子操作形式化为四元组：

```
sync(δ_spec) = ⟨ 变更检测, 追踪定位, 增量传播, 验证确认 ⟩
```

1. **变更检测**：从 Spec 的新旧版本中提取**语义级 delta** δ_spec（而非文本 diff）；
2. **追踪定位**：借助追踪链接（trace）把 δ_spec 映射到受影响的代码区域集合；
3. **增量传播**：仅对受影响区域执行 put 操作（再生或修补），不触动无关代码；
4. **验证确认**：以编译/测试/仿真/往返校验确认传播结果，失败则整体中止。

**原子性**的含义是：这次同步要么完整达成（代码进入与新 Spec 一致的状态，且无关区域逐字节不变），要么完整放弃（代码保持旧状态，但把受影响区域**标记为待更新**），绝不留下"半更新"的不一致中间态。这与 lens 理论中 `put : 视图 × 源 → 源` 的语义一致——put 本质上就是"一方变更后回填/重构另一方"的传播函数（Foster et al., POPL 2005 / TOPLAS 2007，见 `Spec-as-Source_BX_论文精读报告.md` §1）。

值得强调的是，"标记待更新"不是原子操作的失败，而是原子操作的一种**合法终止态**：它等价于"中止传播 + 在一致性关系上登记一个待清偿的一致性债务"（见 1.2 与 1.3）。

### 1.2 正确性判据：往返律、一致性关系、增量传播

Q3 的同步正确性可以用三条理论判据约束，它们分别来自 BX（Bidirectional Transformations）理论的三块基石：

**判据一：往返律（round-trip laws）—— 再生结果的验收标准。**
Lens 理论定义了良行为（well-behavedness）公理：`GetPut`（get 之后 put 回原值，应得原源）与 `PutGet`（put 之后再 get，应得新视图）（Foster et al., 2005/2007）。翻译到 Spec→代码场景：
- **PutGet 对应"再生必须落实变更"**：代码再生后，从代码回读出的行为契约必须反映 Spec 的新内容；
- **GetPut 对应"无变更则零扰动"**：若 Spec 未变更（或变更不涉及某区域），再生不得改动该区域。IncreRTL 的再生任务模板明确要求"只生成受影响代码片段，保证未变更行区间与接口不变"（arXiv:2603.25769 §3.3，图 3 任务模板），正是 GetPut 律的工程化表述；其论文同时观察到反面证据——"即使微小的需求修改也会使全量再生代码与原实现显著偏离"（§1），即全量再生天然违反 GetPut。

**判据二：一致性关系（consistency relation）—— 同步的目标态定义。**
Stevens（MoDELS 2007）指出：双向变换不应被理解为单条函数，而应理解为在某个**一致性关系**约束下保持两个模型同步的机制，并讨论了非医源性（hippocraticness，更新不得无故破坏已有内容）等性质（`Spec-as-Source_BX_论文精读报告.md` §2）。对 Q3 的两点直接推论：
- Spec↔代码之间通常存在**多个合法实现**（同一 Spec 可对应多份一致代码），因此同步的正确目标是"恢复到一致性关系之内"，而非"收敛到唯一输出"。这为 LLM 再生的非确定性留出了语义空间，也解释了为什么全量覆盖式再生（OpenAPI Generator 重跑即覆盖，见 `spec-to-code-bidi-projects.md` §2）会破坏非医源性——它抹掉了已有合法实现中的人工定制。
- 当一致性暂时无法建立（信息不足、需人工裁决、级联影响未评估）时，**把代码维持在"已知不一致但已登记"状态——即标记待更新——是一致性关系框架下的合法中间态**。这为"标记待更新"处置提供了理论正当性。

**判据三：增量传播（delta propagation）—— 同步的效率与局部性标准。**
Diskin, Xiong, Czarnecki（SoSyM/MoDELS 2011）把双向变换从状态级（state-based，整体比较）推广到 **delta 级**（delta-based，沿变更的结构与对象映射传播），建立了增量同步的代数框架，并识别出**弱可撤销性（weak undoability）与弱可逆性（weak invertibility）**两条代数律（`Spec-as-Source_BX_论文精读报告.md` §4）。对 Q3 的直接指导：
- 传播应当沿 δ_spec **局部进行**（"变更→只再受影响部分"），这正是 DeltaMCP 与 IncreRTL 的共同机制，也是"增量再生优于全量再生"的理论依据；
- 弱可撤销性约束了**回滚**：一次同步传播原则上应当可撤销（见 §3.3 回滚策略）。

**补充：可验证的 put（BiGUL）。**
Ko & Hu（PEPM 2016）的 BiGUL 以 put 为第一公民，在 Agda 中完整形式化验证：任何用 BiGUL 写出的 putback 变换都自动满足良行为约束（`Spec-as-Source_BX_论文精读报告.md` §6）。其工程启示是：**同步逻辑应以"如何更新代码侧"（put 方向）为核心来编写，而 get（从代码回读 Spec 视图）作为派生约束**；在无法形式化验证的 LLM 场景中，应退而求其次，用测试门/往返校验来逼近该保证。

### 1.3 "自动再生"与"标记待更新"的适用边界

两种处置不是优劣关系，而是同一原子操作在不同前置条件下的两种合法终止态。综合工作区证据，我们给出如下边界判据（任一项不满足即应降级为"标记待更新"）：

| 判据维度 | 倾向"自动再生" | 倾向"标记待更新" |
|---|---|---|
| 目标区域性质 | 纯生成代码、无人工修改（OpenAPI Generator 的"generated 目录不手改"约定，`spec-to-code-bidi-projects.md` §2） | 含人工定制逻辑（DeltaMCP 明确指出全量再生会抹掉 telemetry/优化/安全防护等定制逻辑，arXiv:2605.28148 §1） |
| 变更的可判定性 | 结构化 Spec 的语义差异可由工具判定（Oasdiff 分离 path/schema 级变更，arXiv:2605.28148 §3） | NL Spec 语义含糊、变更意图需人工解释 |
| 追踪链接置信度 | 链接唯一且高分（IncreRTL 中聚合分 ≥ θ_agg=0.6 的候选链接，arXiv:2603.25769 §3.2） | 链接缺失/低分/多义，需人工验证（IncreRTL 流程保留了 Manual Validation 一步） |
| 影响范围 | 局部、单一变更单元 | 级联/横切变更（AssumptionMiner 实证：定向再生可行但"级联编辑仍具挑战"，arXiv:2607.22898，见 `Spec-as-Source_BX_论文精读报告.md` §11） |
| 验证手段 | 存在编译/测试/仿真等自动验证闭环（IncreRTL 以编译+testbench 仿真收尾） | 无自动验证手段，再生结果无法被客观确认 |
| 生成器确定性 | 确定性模板可覆盖（JDomInO 正向路径对 12 类 building block 确定性生成 Java） | 必须依赖 LLM 语义再生且领域微调缺位 |

两条路线的**制度化样板**分别是：自动再生 → DeltaMCP / IncreRTL（§2.2.3）；标记待更新 → ReqToCode 分级生命周期 + SpecSeal stale 标记（§2.2.5）。ReqToCode（arXiv:2603.13999，见 `RTM_可追踪性_Spec到Code_14篇精读报告.md` §14）的机制尤其关键：它把追踪做成代码内的 **Traceable** 语言原生元素（硬性双向链接、构建期校验），需求变更时通过**分级生命周期**响应——从弃用警告逐级升级到构建失败，"给团队可操作的信号而非突然断裂"。这正是"标记待更新"的完整生命周期语义：**标记不是终点，而是带升级路径的一致性债务管理**。

---

## 2. 推荐技术路线

### 2.1 理论地基如何指导工程实现

| 理论 | 来源 | 对 Q3 工程实现的指导 |
|---|---|---|
| Lens：get/put + PutGet/GetPut | Foster et al. 2005/2007 | 定义原子操作语义原语与验收标准；工程上落实为"再生后回读契约必须等于新 Spec；未涉变更区域必须零改动" |
| QVT 一致性关系 + 非医源性 | Stevens 2007 | 同步目标是一致性关系而非唯一输出；人工定制不得被无故抹除 → 必须有保护区机制与"标记待更新"合法态 |
| Delta-based BX 代数 | Diskin et al. 2011 | 把 Spec diff 转成带作用域的**变更单元**再传播；弱可撤销性 → 同步操作设计为可回滚 |
| BiGUL 可验证 put | Ko & Hu 2016 | 以 put（代码侧更新）为核心编写同步逻辑；在 LLM 场景用测试门/往返校验逼近形式化保证 |
| TGG 增量双向 | Hildebrandt et al. 2013 综述；eMoflon::IBeX | 模型层已有成熟的"单一规范→自动生成前向/后向增量同步器"范式，可整体借鉴其增量解释架构 |

总表（`spec_as_source_survey_master_review.md` 第五部分）指出的交叉空白 4——"形式化 BX 理论与 LLM 代码生成/Agent 工作流之间缺乏桥接"——正是 Q3 技术路线要弥合的鸿沟。下面的落地机制即是桥接方案。

### 2.2 落地机制：变更检测 → 追踪定位 → 增量再生 → 验证合并

#### 2.2.1 变更检测：从文本 diff 到语义 delta

- **结构化 Spec（OpenAPI 等）**：直接采用语义差异工具。DeltaMCP 的做法是样板：先对规范做预处理（把所有被引用的参数/对象内联展开成完整表示），再用 **Oasdiff** 对比新旧两版规范，"作为语义差异工具，它隔离版本间 path 级与 schema 级变更"（arXiv:2605.28148 §3，本次已核原文）。论文实测原始 diff 可超过 50 万 token/版本对，因此必须分解为端点级变更单元——**语义 diff 是变更检测的正确粒度，但必须配合切分**。
- **NL Spec**：无现成 diff 工具，可用 LLM + CoT 提取需求的高层语义表示并分解为原子需求。IncreRTL 将每条原子需求结构化为五要素：接口、信号、触发条件、行为、状态迁移（arXiv:2603.25769 §3.2.1），这套结构化表示即是 NL 场景下的 δ_spec 载体。
- **低成本预过滤**：SpecSeal 的"行为契约哈希"提供了一个轻量前筛——代码侧以 `// @spec REQ-ID #hash` 注解引用 Spec，哈希只覆盖行为契约段（Acceptance/Non-functional），"spec 文案的润色改动不触发漂移，只有行为契约变化才标记 stale"（`spec-code-drift-projects-review.md` §8）。这等价于在变更检测阶段就把"良性编辑"与"行为变更"分开，避免无谓再生。

#### 2.2.2 追踪定位：把 δ_spec 映射到受影响代码

三条已被验证的定位路径：

1. **追踪矩阵法（IncreRTL 样板）**：语法保持的代码分块（Verilog 解析器把设计切成端口声明/寄存器声明/组合逻辑等保持语法边界的块）→ 基于层级关系的候选链接（接口↔模块头、信号↔声明层、触发条件↔条件结构、行为↔功能逻辑、状态迁移↔FSM 层）→ 双维打分（词法：关键词 Jaccard；语义：CodeBERT 余弦相似度；聚合阈值 θ_agg=0.6）→ **LLM 从高层语义视角补全缺失链接** → 人工验证得到最终追踪矩阵 M（arXiv:2603.25769 §3.2，算法 1 已核原文）。该矩阵同时服务 Q1（RTM）与 Q3（定位），印证了"追踪是同步的前提"。
2. **依赖图法（AssumptionMiner）**：基于 AST 依赖图定位受修订条目影响的代码，实证表明 AST 引导定位精度优于关键词/整文件基线（arXiv:2607.22898，见 `Spec-as-Source_BX_论文精读报告.md` §11）。适合已有结构化代码图的场景。
3. **层级收窄法（SpecMap）**：仓库级结构推断→文件级相关度→符号级对齐，文件级准确率 73.3%、token 消耗降 84%、耗时降约 80%（arXiv:2601.11688，见总表第一部分 #12）。适合追踪链接缺失时的冷启动定位。

#### 2.2.3 增量再生：两大样板

**样板 A —— DeltaMCP（结构化契约 + 定向修补，arXiv:2605.28148，已核全文）**

流水线：OpenAPI 新旧版本对 (A, A') → 内联展开预处理 → Oasdiff 语义差异 → **端点级变更单元**（每个单元含：版本 A 的旧 MCP 工具实现、版本 A' 的修订规范表示、限定到单个工具的结构化 schema 差异）→ 指令-响应格式 + 明确 guardrails → **LoRA 微调**的再生模型（在 Microsoft.Storage 的 2000+ 结构化变更样本上微调 StarCoder2-7B / CodeLlama-7B / Phi-3-Mini-4k 三个候选）→ 再生结果经**适配器逻辑补丁回现有服务器代码**。

关键证据与设计含义：
- 明确以"不覆盖现有代码、保留定制服务逻辑（telemetry、优化、safeguards）"为设计目标，直接对抗 AutoMCP 式全量再生的抹除问题；
- 性能：更新操作中平均 CPU 占用约 ±0.1%、内存约 12%，而 AutoMCP 全量再生频繁超过 ±30% 内存；生成质量亦超过全量生成基线（§1、§3）。
- 启示：**"变更单元 + 领域微调 + 适配层补丁"是结构化 Spec 场景下自动再生的完整配方**；guardrails（指令中的明确约束）是把 LLM 再生拉向"确定性变换"的关键手段。

**样板 B —— IncreRTL（追踪引导 + 局部再生 + 验证闭环，arXiv:2603.25769，已核全文）**

流水线：原始+更新需求描述 + 现有实现 → 结构化表示（CoT 原子需求五要素 + 语法保持分块）→ 构建并验证追踪矩阵 → **按矩阵定位受影响片段，任务模板约束 LLM 只再生这些片段、保持未变更行区间与接口不变**（图 3）→ 重组代码 → **编译 + testbench 仿真验证**。

关键证据与设计含义：
- 在自建 EvoRTL-Bench 上，再生一致性显著优于两个基线，且**全量再生比 IncreRTL 多消耗 23.29% token**（§1，已核原文）；
- 论文给出的反面机理值得写入设计规范：全量重生成会因"局部变更引发全局漂移"而迫使下游工程从头再来；把原实现+新需求整体塞给 LLM 虽能部分抑制漂移，但 prompt 过长会稀释显著信息、降低生成质量——**因此必须用追踪做"注意力局部化"，而不是靠加大上下文**；
- 启示：追踪链接把"再生范围"变成显式约束，验证闭环（编译/仿真）充当往返律的替代性检验。

#### 2.2.4 Agent 驱动路线：GitHub Spec Kit 的 converge 闭环

对 NL Spec 为主、无结构化契约的场景，GitHub Spec Kit（github.com/github/spec-kit，MIT，约 1785 次提交，v0.16.3 @ 2026-08-13，高度活跃）提供了 Agent 驱动的闭环（据 `spec-to-code-bidi-projects.md` §1，2026-08-15 抓取核验）：
- `/speckit.specify → plan → tasks → implement` 构成"Spec 变更 → 重新规划 → 补任务 → 再实现"的主链；
- **`/speckit.converge`**：评估代码库与 spec/plan/tasks 的差距，并把差距**追加为新的待办任务**——这是"Spec 变更 → 标记待更新 → 排队再生"的 Agent 化实现；
- **`/speckit.analyze`**：跨制品（spec/plan/tasks/代码）做一致性与覆盖度分析，充当同步前的影响评估。
- 局限：其双向同步是**非确定性**的，依赖 Agent 重新评估与再生成，而非形式化 lens/TGG 变换；因此应把它放在"验证门 + 人工评审"之内使用，或与 §2.2.5 的硬门禁叠加。

#### 2.2.5 "标记待更新"路线的制度化

- **ReqToCode 分级生命周期（arXiv:2603.13999）**：Traceable 元素（语言原生、由生成产生、代表单条需求并携带元数据）被实现/测试代码引用，形成硬性双向链接并在**构建过程**中自动校验；需求变更时按分级生命周期响应——**从弃用警告到构建失败逐级传导**。工程解读：这是把"标记待更新"做成编译器/构建系统的一等状态，软信号（警告）给人工响应窗口，硬阻断（构建失败）保证一致性债务不被无限拖欠。注意：该文为未同行评审 preprint、无大规模评测（`RTM_可追踪性_Spec到Code_14篇精读报告.md` §14），采纳时应视为"方向正确、证据待补"。
- **SpecSeal 哈希契约（xantus-ai，v0.1，TS）**：`check/coverage/map/sync/init` 命令检测 stale 注解、孤儿注解、未实现需求，可直接做 CI 质量闸门（`spec-code-drift-projects-review.md` §8）。它是"标记"动作的轻量落地：只标记、不自动改代码，把处置权留给人/Agent。
- **Spec Growth Engine drift gate（arXiv:2606.27045）**：把 Spec↔Code 发散作为**阻塞合并的条件**（drift gate），配合机器可读 Spec 图与 Spine 上下文组装器（`Spec_Code_Drift_14papers_精读报告.md` §9）。它把"标记"升级为门禁：未清偿的一致性债务不允许进入主干。注意其当前语义是"任何分歧都阻断"，需叠加豁免机制（如 ArchGuard 的 ignore 抑制）以避免误伤良性演进。

三者可组合成完整的标记链：**哈希/链接检测（SpecSeal/ReqToCode）→ 分级信号（ReqToCode 生命周期）→ 合并门禁（drift gate）**。

#### 2.2.6 模型层双向同步的补充参照

若 Spec 可建模为结构化模型（DDD 领域模型、MBSE 等），模型层 BX 工具提供现成的增量双向机制：
- **JDomInO（arXiv:2608.05612）**：共享元模型连接领域模型与 Java 代码库；正向路径由领域模型**确定性**生成 Java 代码结构（已在覆盖全部 12 类 building block 的酒店管理场景验证），反向路径从 Java 代码重建领域模型（映射逻辑通过单元测试）；并提出把结构化领域模型作为 AI 编码助手的"精度上下文层"（`Spec-as-Source_BX_论文精读报告.md` §9）。其正向路径即确定性再生的样板，反向路径即 put 方向的工程实现。
- **eMoflon::IBeX（TU Darmstadt，活跃，GPL-3.0）**：基于 TGG 的增量双向图变换，从单一规范生成前向/后向同步器，支持增量解释（`spec-to-code-bidi-projects.md` §3）——是"变更触发局部再同步"在模型层的成熟实现。
- **Echo（HASLab，已停更 2018）**：把 QVT-R/ATL 变换解释为双向/多向，对不一致模型做**最小修复**（`spec-to-code-bidi-projects.md` §7）。其"最小修复"语义与 lens 的非医源性一脉相承，可作为处置策略的设计参照（修复幅度最小化），但不建议直接采用（依赖旧生态、停更）。

### 2.3 参考架构：双轨处置路由器

综合上述证据，推荐如下 Q3 参考流水线：

```
Spec 变更
  │
  ├─(1) 变更检测：语义 diff（Oasdiff / LLM-CoT 原子需求分解 / 行为契约哈希预筛）
  │        └→ 产出：δ_spec（带作用域的变更单元集合）
  ├─(2) 追踪定位：追踪矩阵 / AST 依赖图 / 层级收窄
  │        └→ 产出：受影响代码区域 + 置信度
  ├─(3) 处置路由（按 §1.3 边界判据逐单元裁决）：
  │        ├─ 纯生成区 + 变更可判定 + 有验证闭环 ──→ 自动再生
  │        │     ├─ 结构/契约层：确定性模板再生（OpenAPI Generator/JDomInO 式）
  │        │     └─ 语义/实现层：受约束 LLM 再生（变更单元+追踪锚点+接口冻结，
  │        │        DeltaMCP/IncreRTL 式；定制逻辑经适配层保护）
  │        └─ 人工区 / 低置信链接 / 级联变更 / 无验证 ──→ 标记待更新
  │              └→ 分级信号（警告→构建失败，ReqToCode 式）+ CI 门禁（drift gate）
  ├─(4) 验证确认：编译/测试/仿真 + 往返校验（回读契约 vs 新 Spec）
  │        ├─ 通过 → 以"一变更单元一提交"合并，更新追踪矩阵与契约哈希
  │        └─ 失败 → 丢弃再生结果，回退旧状态，转"标记待更新"
  └─(5) 状态登记：RTM/追踪矩阵同步演进，一致性债务可查询、可度量
```

该架构与工作区证据的对应关系：步骤 (1) ← DeltaMCP §3 + SpecSeal；步骤 (2) ← IncreRTL §3.2 + AssumptionMiner + SpecMap；步骤 (3) ← §1.3 判据表；步骤 (4) ← IncreRTL 验证闭环 + lens 往返律；步骤 (5) ← ReqToCode 生命周期 + Spec Kit converge 任务队列。

---

## 3. 落地建议

### 3.1 确定性生成 vs LLM 再生：取舍与混合双轨

**证据面**：
- 确定性生成的标杆是 OpenAPI Generator（100+ 语言生成器、行业事实标准、极高活跃），但它**纯单向、重跑即全量覆盖**，无元素级追踪、无双向同步（`spec-to-code-bidi-projects.md` §2）；JDomInO 正向路径则展示了共享元模型下结构再生的确定性（12 类 building block 全覆盖验证）。确定性路线的优点是可复现、可测试、往返律天然成立；边界是只能覆盖结构/契约层，触不到业务语义。
- LLM 再生由 DeltaMCP（LoRA 微调 + guardrails，质量与资源均优于全量生成）与 IncreRTL（追踪约束 + 验证闭环，token 省 23.29%、一致性更优）证明可行；Spec Kit 则证明 Agent 驱动的 NL 闭环在工具层面已可用。风险是非确定性与漂移——IncreRTL 的观察（微小需求变更即可导致全量再生结果显著偏离）说明 LLM 再生**必须被约束在局部**。

**建议：三层混合双轨**：
1. **契约/骨架层 → 确定性再生**（模板/生成器），作为同步的"硬地基"，保证接口、签名、路由等永不被 LLM 扰动；
2. **语义/实现层 → 受约束 LLM 再生**，三重护栏缺一不可：变更单元（scoped 输入，防上下文稀释）、追踪锚点（定位再生范围）、接口冻结（unchanged line ranges/interfaces，IncreRTL 任务模板）；有领域数据时优先做 DeltaMCP 式 LoRA 领域微调（2000+ 结构化变更样本即可显著增强变换的确定性）；
3. **超界降级**：当变更单元过大、影响级联（AssumptionMiner 已实证级联编辑是难点）或验证手段缺位时，路由器把该单元降级为"标记待更新"，而不是强行 LLM 再生。

### 3.2 保护人工修改区

全量覆盖再生对人工修改是毁灭性的：DeltaMCP 的开篇动机即 AutoMCP 式全量再生"无法保留现有定制工具"，会抹掉 telemetry、优化与安全防护逻辑（arXiv:2605.28148 §1）；OpenAPI Generator 的一致性维持方式就是约定"generated 目录不手改"（`spec-to-code-bidi-projects.md` §2）。推荐三种互补的保护区模式：

1. **区域隔离（最基础）**：生成物落在明确标记的文件/目录/代码区域，禁止手改；人工逻辑一律放在非生成区。生成区边界用注释/注解显式标记，纳入 CI 检查。
2. **契约哈希（行为级保护）**：SpecSeal 式 `@spec REQ-ID #hash` 注解只绑定行为契约段，文案润色不触发、契约变更才标 stale（`spec-code-drift-projects-review.md` §8）。把它推广为再生范围的界定符：**再生只允许修改哈希覆盖的区段**，区段之外的人工代码物理上不受触碰。
3. **适配层隔离（结构级保护）**：DeltaMCP 的适配器逻辑——再生器产出标准件，定制逻辑挂在适配层，再生经适配层"补丁回"现有代码而非重写。这是目前唯一有实证的"再生与定制共存"机制。

另外，ReqToCode 的 Traceable 元素天然携带"该代码区由哪条需求生成"的元数据，可直接充当保护区判定的数据源（需求变更 → 只有对应 Traceable 区段进入再生候选）。

### 3.3 回滚策略

以 delta-BX 的弱可撤销性为理论约束（传播应尽量可撤销，`Spec-as-Source_BX_论文精读报告.md` §4），建议四层回滚设计：

1. **原子提交粒度**：一个变更单元 → 一个独立 commit/PR。再生、验证、合并都以变更单元为单位，任何单元可独立 revert 而不牵连其他同步结果。
2. **门禁前置**：不一致在进入主干前被拦截。drift gate（Spec Growth Engine）把 Spec↔Code 发散作为阻塞合并条件；SpecSeal 的 check/coverage 做 CI 闸门。回滚成本最低的策略是让坏同步根本不入库。
3. **验证失败即回退**：IncreRTL 的编译+testbench 仿真、DeltaMCP 的 guardrails 都是同步内的验证关卡；验证失败时丢弃再生结果、恢复旧代码，并把该单元转"标记待更新"。这实现了 §1.1 的原子性：失败即整体放弃，不产生半更新状态。
4. **软失败升级窗**：ReqToCode 分级生命周期（弃用警告 → … → 构建失败）给出回滚之外的第三条路——**债务显性化**：允许短期内带不一致运行（保留回滚/响应窗口），但升级路径保证债务最终必须清偿。建议把"标记待更新"条目的滞留时长与数量纳入度量（Loom 的 Driftgraph 提供了漂移可视化参照，见总表第二部分项目 #5）。

### 3.4 分场景落地路径

| 场景 | 推荐组合 | 样板 |
|---|---|---|
| 结构化契约 Spec（OpenAPI/gRPC） | Oasdiff 式语义 diff → 端点级变更单元 → 确定性再生骨架 + LoRA 再生适配层 → CI 门禁 | DeltaMCP（arXiv:2605.28148） |
| NL 需求 Spec（一般应用） | 追踪矩阵（层级候选+双维打分+LLM 补链+人工验证）→ 局部再生（行区间/接口冻结）→ converge 任务闭环 → 哈希标记 + 分级门禁 | IncreRTL + Spec Kit + SpecSeal + ReqToCode |
| 模型驱动（DDD/MBSE） | 共享元模型 + TGG 增量双向同步器；正向确定性生成、反向模型重建 | JDomInO + eMoflon::IBeX |
| 安全关键系统 | 上述任一路线 + 强制验证闭环（编译/仿真/形式检查），再生结果未过验证不得入库；"标记待更新"走分级失败而非静默警告 | IncreRTL 验证闭环 + ReqToCode 构建失败级 |

---

## 4. 结论

1. **Q3 的"原子操作"应定义为 ⟨变更检测, 追踪定位, 增量传播, 验证确认⟩ 四元组**，其正确性由三条判据约束：往返律（再生必须落实变更、且不扰动无关区域）、一致性关系（目标是回到一致态而非唯一输出；人工定制受非医源性保护）、增量传播（沿 delta 局部更新，且可撤销）。Lens（Foster 2005/07）、QVT 语义（Stevens 2007）、delta-BX 代数（Diskin 2011）、BiGUL 可验证 put（Ko & Hu 2016）共同构成这套判据的理论地基。

2. **"自动再生"与"标记待更新"是同一原子操作的两种合法终止态**，由六个前置判据（区域是否纯生成、变更是否可判定、链接是否高置信、影响是否局部、验证是否存在、生成器是否确定）决定路由。标记不是失败兜底，而是带升级路径的一致性债务管理——ReqToCode 的分级生命周期（弃用警告→构建失败）是其制度化样板。

3. **工程落地已有可直接借鉴的样板**：DeltaMCP 展示了结构化 Spec 下"语义 diff → 变更单元 → LoRA 定向再生 → 适配层补丁"的完整链路（资源占用约为全量再生的 1/3 以下且质量更优）；IncreRTL 展示了 NL 需求下"追踪矩阵 → 局部再生 → 编译/仿真验证"的闭环（全量再生多耗 23.29% token 且一致性更差）；GitHub Spec Kit 的 converge/analyze 提供了 Agent 驱动的差距评估与任务化机制；ReqToCode + SpecSeal + drift gate 组成"检测→分级标记→合并门禁"的标记链。

4. **核心落地建议是"双轨处置路由器 + 三重护栏"**：确定性生成守住契约/骨架层，受约束的 LLM 再生处理语义层（变更单元、追踪锚点、接口冻结三重护栏），超界变更降级为标记待更新；人工修改区通过区域隔离、契约哈希与适配层三重机制保护；回滚通过"一变更单元一提交 + 门禁前置 + 验证失败即回退 + 分级升级窗"四层设计保障。

5. **现存空白与研究机会**：总表明细（`spec_as_source_survey_master_review.md`）确认，目前没有项目同时满足"确定性双向同步 + 直接面向代码文本 + 活跃维护"——形式化 BX 工具（eMoflon、Echo、Boomerang）停在模型/字符串层且部分停更，而面向代码文本的方案（DeltaMCP、IncreRTL、Spec Kit）又缺少形式化保证。把 delta-BX 的变更代数与 BiGUL 式可验证 put 嫁接到"追踪引导的 LLM 再生"之上，并用测试门逼近往返律，是 Q3 方向最有价值的研究-工程结合点。

---

## 附：主要引用材料清单

**理论奠基**
- Foster et al., Combinators for Bidirectional Tree Transformations, POPL 2005 / TOPLAS 2007（lens，PutGet/GetPut）
- Stevens, Bidirectional Model Transformations in QVT: Semantic Issues, MoDELS 2007（一致性关系）
- Diskin, Xiong, Czarnecki, From State- to Delta-Based Bidirectional Model Transformations, SoSyM/MoDELS 2011（delta-BX，弱可撤销/弱可逆）
- Ko, Hu, BiGUL: A Formally Verified Core Language for Putback-Based BX, PEPM 2016

**2026 前沿（均已核 arXiv 摘要页，DeltaMCP/IncreRTL 已核全文节选）**
- DeltaMCP, arXiv:2605.28148（2026-05）：Oasdiff 语义差异、端点级变更单元、LoRA 微调、适配器补丁、定制逻辑保护
- IncreRTL, arXiv:2603.25769（2026-03）：需求-代码追踪矩阵（θ_agg=0.6、LLM 补链、人工验证）、局部再生、行区间/接口冻结、编译+testbench 验证、EvoRTL-Bench、token +23.29% 对比
- JDomInO, arXiv:2608.05612（2026-08）：共享元模型、正向确定性生成（12 类 building block）、反向重建、AI 精度上下文层
- ReqToCode, arXiv:2603.13999（2026-03，未评审 preprint）：Traceable 元素、硬性双向链接、构建期校验、分级生命周期（弃用警告→构建失败）
- AssumptionMiner, arXiv:2607.22898（2026-07）：AST 依赖图定向再生、级联编辑挑战
- Spec Growth Engine, arXiv:2606.27045（2026-06）：Spec 图 + drift gate 合并阻断
- SDD 综述, arXiv:2602.00180（2026-01）：spec-first/spec-anchored/spec-as-source 三级

**开源项目（核验日期 2026-08-15，见 `spec-to-code-bidi-projects.md` 与 `spec-code-drift-projects-review.md`）**
- GitHub Spec Kit（v0.16.3 @2026-08-13；converge/analyze 闭环）
- OpenAPI Generator（全量覆盖再生、generated 目录不手改约定）
- eMoflon::IBeX（TGG 增量双向）、Echo（最小修复双向，停更）
- SpecSeal（行为契约哈希、stale 标记、CI 闸门，v0.1）、ArchGuard（ADR↔代码 LLM 判定、ignore 豁免）
- Loom（loom sync RTM、Driftgraph）、SpecMap（层级定位，token −84%）
