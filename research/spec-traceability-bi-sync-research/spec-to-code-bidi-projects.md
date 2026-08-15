# Spec→Code 双向同步 / 双向工程 / 规范驱动代码生成 —— 9 个开源项目精读报告

> 研究总问题：Spec-as-Source 范式下从 Spec 到代码的可追踪性（Traceability）与双向同步。
> 评分依据：① 对子问题"双向同步原子操作（Spec 变更时自动触发代码再生或标记为待更新）"的解决程度；② 采用价值；③ 与该范式的适应程度；④ 项目活跃度。
> 评分等级：A / B / C。
> 数据来源：逐一通过 WebFetch 抓取各项目 GitHub 仓库页 / README / 官方文档（2026-08-15 抓取）。

---

## 1. GitHub Spec Kit

- **名称**：Spec Kit（核心 CLI 为 `specify`）
- **作者/组织**：GitHub（GitHub 官方开源项目）
- **年份**：约 2024–2025 年立项，持续快速迭代（截至 2026-08 已 1785 次提交，版本到 0.16.x）
- **技术栈/功能**：Python 编写的 CLI（`specify-cli`，PyPI/uv 发布），面向任意 AI 编码 Agent 的"规范驱动开发（Spec-Driven Development）"工具包。提供 `/speckit.constitution`、`/speckit.specify`、`/speckit.plan`、`/speckit.tasks`、`/speckit.implement`、`/speckit.converge`、`/speckit.analyze`、`/speckit.checklist`、`/speckit.clarify` 等斜杠命令/skill，并支持 30+ 个 AI 编码 Agent 集成、扩展（extensions）、预置（presets）、包（bundles）。
- **关键能力**：
  - 规范驱动代码生成/再生：核心范式就是"先定义 Spec 再生成实现"，`/speckit.implement` 依据 spec/plan/tasks 生成代码。
  - 追踪性/回环同步：`/speckit.converge` 会把"代码库与 spec/plan/tasks 的差距"评估出来并追加为新的待办任务；`/speckit.analyze` 做跨产物（spec/plan/tasks/代码）的一致性与覆盖度分析。这是对"Spec 变更后标记待更新/再生成"的**Agent 驱动**实现。
  - 双向同步：**非确定性的**，依赖 Agent 重新评估与再生成，而非形式化的 lens/TGG 双向变换；但"Spec 变更 → 提示/追加任务 → 再实现"的闭环流程是明确的。
- **活跃度/维护状态**：极高活跃。最近提交 2026-08-14，152 个 issue、162 个 PR，社区扩展/预置生态活跃，有月度 newsletter 与中文 README。
- **评分**：**A**
- **一句话理由**：它是与本范式（Spec-as-Source + Agent 生成代码）最直接契合、且活跃度最高的项目，虽双向同步靠 Agent 驱动而非形式化，但通过 `converge`/`analyze` 实现了"Spec 变更→标记待更新/再生成"的闭环。

---

## 2. OpenAPI Generator

- **名称**：OpenAPI Generator
- **作者/组织**：OpenAPITools（OpenAPI Tools 组织，非 OAI 官方）
- **年份**：2017 年从 Swagger Codegen 分叉而来，持续发布（当前 master 7.25.0，7.24.0 为最新稳定版）
- **技术栈/功能**：Java/Scala 实现，Maven/Gradle/CLI/Docker/在线多种形态；根据 OpenAPI Spec（支持 1.0–3.1，3.1 为 beta）自动生成 API 客户端 SDK、服务端 stub、文档、配置等，覆盖 100+ 语言/框架生成器。
- **关键能力**：
  - 规范驱动代码生成：是业界事实标准，纯单向前向生成（Spec → 代码）。
  - 双向同步/round-trip：**无原生双向同步**。重新运行时直接覆盖生成目录（约定"generated 目录不手改"），无内置"代码变更回流 Spec"或"diff 合并"机制；一致性靠用户用 `openapi-generator` 重新生成来维持。
  - 追踪性：无内置 spec→代码元素级追踪模型。
- **活跃度/维护状态**：极高活跃。22975 次提交、5k+ issue、604 个 PR，商业公司广泛采用（有赞助商），文档/允许页面活跃。
- **评分**：**A**
- **一句话理由**：规范驱动代码生成领域采用价值与活跃度无可匹敌的行业标准，但纯单向、无原生双向同步——再生依赖全量覆盖。

---

## 3. eMoflon::IBeX

- **名称**：eMoflon::IBeX
- **作者/组织**：TU Darmstadt（达姆施塔特工业大学）eMoflon 团队
- **年份**：2016 年立项，持续维护（2313 次提交）
- **技术栈/功能**：Eclipse 插件/RCP 生态，Java + Xtend + Xtext；基于 Triple Graph Grammars（TGG）与单向图变换的**增量式解释器**；配套 Democles 与 HiPE（并行）两个模式匹配引擎；文本规则语言（eMoflon::IBeX UI）。
- **关键能力**：
  - 双向同步：TGG 先天支持**前向/后向**双向模型同步，是模型级双向变换的成熟实现。
  - 增量式：支持增量解释，适合"变更触发局部再同步"（对应 Spec 变更自动触发再生/待更新的原子操作的需求，但作用于模型层而非代码文本层）。
  - 规范驱动代码生成：规则即规范，可生成代码/模型；定位偏模型变换引擎而非直接"Spec→代码"生成器。
- **活跃度/维护状态**：活跃。最近提交 2026-06-17，18 issue、22 名贡献者，需 Eclipse 2026-03 / JDK 21+。
- **评分**：**A**
- **一句话理由**：基于 TGG 的**真正的**双向变换引擎，增量式同步与"变更触发再同步"语义最贴合子问题，且持续活跃。

---

## 4. Eclipse Epsilon

- **名称**：Eclipse Epsilon
- **作者/组织**：Eclipse 基金会（Eclipse 官方项目；核心作者 Dimitrios Kolovos 等，约克大学系）
- **年份**：2008 年前后开始，持续维护（6108 次提交）
- **技术栈/功能**：Eclipse 插件 + 多种脚本语言：EGL（代码生成）、ETL（模型到模型变换）、EVL（校验）、ECL（比较）、EML（合并）、EPL（模式匹配）、Epsilon Flock（模型迁移）；可作 Java 库、Ant 任务、Maven/Gradle 集成；适配 EMF/UML/Simulink/XML 等。
- **关键能力**：
  - 规范驱动代码生成：EGL 是成熟、广泛使用的模板式代码生成器（Spec/模型 → 代码）。
  - 双向同步/round-trip：**无原生双向同步**。ETL 是单向的；双向主要靠 ECL 比较 + EVL 校验 + EML 合并来"人工拼出"同步流程，而非形式化双向变换；Flock 面向 schema/模型迁移而非代码回流。
  - 追踪性：无内置的 spec↔代码元素级追踪。
- **活跃度/维护状态**：高度活跃。最近提交 2026-07-22，20 名贡献者，社区/文档/VS Code 支持完善。
- **评分**：**B**
- **一句话理由**：活跃度高、代码生成能力强，但缺少原生双向同步机制，双向需靠"比较+校验+合并"工具链人工拼装。

---

## 5. Eclipse Henshin

- **名称**：Eclipse Henshin（org.eclipse.emf.henshin）
- **作者/组织**：Eclipse 基金会（EMFT 项目下）
- **年份**：2010 年前后开始，持续到 2025（2711 次提交）
- **技术栈/功能**：基于 EMF 的就地（in-place）图变换语言与工具；规则/单元控制流、图形与文本语法、解释器（带调试）、性能剖析器、冲突与依赖分析、状态空间/验证、规则变体、自动规则生成、OCL→应用条件；Xtext 适配、Apache Giraph 大规模并行执行。
- **关键能力**：
  - 内生（endogenous）就地变换为主；外生（exogenous）变换借助 trace 模型支持"源→目标实例生成"。
  - 双向同步/round-trip：**受限**。trace 模型提供一定可追踪性，可支撑部分往返，但非原生双向/同步引擎；无"Spec 变更→代码再生"的自动化同步链路。
  - 规范驱动代码生成：可作为模型变换/规则引擎驱动生成，但非专用代码生成器。
- **活跃度/维护状态**：中等偏低。最近提交 2025-06-26，7 个 issue，维护主要靠社区少数人。
- **评分**：**B**
- **一句话理由**：成熟的图变换引擎与外生 trace 支持，但双向/同步能力受限、近一年活跃下降。

---

## 6. Eclipse ATL

- **名称**：Eclipse ATL（ATL Transformation Language）
- **作者/组织**：Eclipse 基金会（MMT 项目，原 INRIA/Nantes 团队）
- **年份**：2000s 中后期，长期维护（官方仓库 eclipse-atl/atl 2026-07 仍有更新）
- **技术栈/功能**：声明式+命令式混合的模型到模型（M2M）变换语言与工具包；规则匹配/导航/创建目标元素；Eclipse ATL IDE（语法高亮、调试器）；ATL Transformations Zoo 用例库。
- **关键能力**：
  - 规范驱动生成：成熟的单向前向 M2M 变换（源模型 → 目标模型），可支撑 PIM→PSM→代码的 MDA 链路。
  - 双向同步/round-trip：**原生单向**。ATL 本身不提供双向；双向需借助外部工具（如 Echo 把 ATL 解释为双向）或 A2M 等，无内置同步原子操作。
  - 追踪性：无内置 spec↔代码追踪。
- **活跃度/维护状态**：中等偏稳定。官方仓库 2026-07 更新，14 star、生态/论坛仍在，但整体趋缓。
- **评分**：**B**
- **一句话理由**：经典且稳定的单向 M2M 变换标准，规范驱动可行，但无原生双向同步，需外部工具补充。

---

## 7. Echo（HASLab）

- **名称**：Echo
- **作者/组织**：HASLab（葡萄牙米尼奥大学 High-Assurance Software Laboratory）——Nuno Macedo、Alcino Cunha、Tiago Guimarães
- **年份**：2013 年前后，2018 年发布 0.3.1 后基本停更
- **技术栈/功能**：Eclipse/EMF 插件 + Alloy 模型查找器；OCL 注解约束；接受 QVT-R 与 ATL 规范变换；模型可视化（Alloy visualizer）、模型生成、一致性检查、模型修复、批式变换，全部基于最小化修复语义。
- **关键能力**：
  - 双向/多向同步：**强**。把 QVT-R/ATL 变换解释为**双向/多向**变换，对不一致模型做**最小修复**以恢复一致性；批式变换从既有模型生成最小一致模型；提供全部合法解供选择；距离度量支持图编辑距离或操作式距离。
  - 与"Spec 变更自动再生/标记待更新"的契合度：语义上接近（变更→最小修复/再生成），但作用于模型层、非代码文本层，且非增量式（每次全量 Alloy 求解）。
- **活跃度/维护状态**：**停更**。最近提交 2018-10-05，v0.3.1，4 个 release，15 issue。
- **评分**：**B**
- **一句话理由**：在"QVT-R/ATL 双向一致性与最小修复"上学术价值极高、能力名副其实，但项目已停更且依赖旧版 Eclipse。

---

## 8. Boomerang

- **名称**：Boomerang
- **作者/组织**：boomerang-lang（Nate Foster 等，源自 Cornell/Penn 的 lens 双向编程研究）
- **年份**：2010s 研究项目，2016 迁到 GitHub，2018 后基本停更
- **技术栈/功能**：OCaml 实现的**双向编程语言**，基于 lens 理论（get/put 组织）；面向字符串等数据结构，提供 stdlib、lenses、synthesis（从示例合成）、unittests、docs；配套 Optician 等工具。
- **关键能力**：
  - 双向同步：**纯正双向**（get/put lens），在"字符串/数据"层面完美满足 round-trip 的公理（PutGet/GetPut）。
  - 与 Spec→代码范式契合度：**低**。面向字符串/文本的双向变换，不直接面向"Spec 结构→代码结构"的软件工程级追踪；无代码生成/再生与待更新标记。
- **活跃度/维护状态**：**基本停更**。最近提交 2023-03-16（文档性 PR），仅 28 次提交、2 issue、0 release。
- **评分**：**C**
- **一句话理由**：双向语义（lens）最严谨，但面向字符串而非 Spec→代码、且已长期停更，属于研究样本。

---

## 9. FunnyQT

- **名称**：FunnyQT
- **作者/组织**：JGraLab（Universität Koblenz-Landau），作者 Tassilo Horn
- **年份**：2012 年启动，2019 年 v1.1.6 后基本停更
- **技术栈/功能**：Clojure 实现的模型查询与变换库，支持 EMF 与 JGraLab(TGraph)；含查询 API、正则路径表达式、模式匹配（pmatch）、就地变换、外延式/规则式变换、core.logic 关系查询、双向变换（funnyqt.bidi）、图同演化变换（coevo）、EDN 持久化、GraphViz 可视化。
- **关键能力**：
  - 双向同步：提供专门的 **funnyqt.bidi 双向变换 API**，用左右模型间的关系/对应规范来生成/同步任一方向——**支持双向生成与双向同步**。
  - 规范驱动代码生成：非专用代码生成器；面向模型查询/变换，可用以驱动模型层生成。
- **活跃度/维护状态**：**停更**。最近提交 2019-01-05，253 个 tag 但实质停在 1.1.6，单一作者。
- **评分**：**C**
- **一句话理由**：自带真正的双向变换 API，但定位模型查询/变换而非 Spec→代码，且自 2019 年起停更、单作者维护。

---

## 汇总对比表

| # | 项目 | 组织/作者 | 技术栈 | 双向同步 | 规范驱动代码生成/再生 | 活跃度 | 评分 |
|---|------|-----------|--------|----------|------------------------|--------|------|
| 1 | GitHub Spec Kit | GitHub | Python CLI + AI Agent | Agent 驱动（converge/analyze 闭环） | 是（核心范式） | 极高（2026-08） | **A** |
| 2 | OpenAPI Generator | OpenAPITools | Java | 无原生（全量覆盖再生） | 是（行业标准） | 极高（2026-08） | **A** |
| 3 | eMoflon::IBeX | TU Darmstadt | Java/Xtend + TGG | 是（TGG 前向/后向，增量解释） | 是（模型/规则级） | 高（2026-06） | **A** |
| 4 | Eclipse Epsilon | Eclipse | Java + EGL/ETL 等脚本 | 无原生（ECL+EVL+EML 拼装） | 是（EGL） | 高（2026-07） | **B** |
| 5 | Eclipse Henshin | Eclipse | Java/EMF 就地图变换 | 受限（外生 trace） | 部分（变换驱动） | 中（2025-06） | **B** |
| 6 | Eclipse ATL | Eclipse (MMT) | Java 声明式 M2M | 无原生（需外部工具） | 是（单向 M2M→代码） | 中（2026-07） | **B** |
| 7 | Echo | HASLab/米尼奥大学 | Java + Alloy + QVT-R/ATL | 强（双向/多向最小修复） | 部分（模型级批式生成） | 停更（2018） | **B** |
| 8 | Boomerang | boomerang-lang | OCaml（lens） | 强（字符串级 get/put） | 否 | 停更（2023） | **C** |
| 9 | FunnyQT | JGraLab/科布伦茨大学 | Clojure | 有（funnyqt.bidi 双向） | 否（模型查询/变换） | 停更（2019） | **C** |

---

## 结论与洞察

1. **与"Spec-as-Source + 代码生成"范式最契合且活跃的项目**：GitHub Spec Kit 与 OpenAPI Generator。前者是 Agent 驱动、提供"Spec 变更 → converge 补任务 → 再实现"的闭环，最贴近"标记待更新/自动再生成"的子问题；后者是确定性模板生成的事实标准，但纯单向。
2. **在"双向同步原子操作"上形式化能力最强**：eMoflon::IBeX（TGG 增量双向）、Echo（QVT-R/ATL 最小修复双向）、Boomerang（lens get/put）、FunnyQT（bidi）。但它们多数停在模型/字符串层，不直接做"Spec→代码文本"的往返。
3. **评分逻辑**：A 类（Spec Kit / OpenAPI Generator / eMoflon::IBeX）在该研究问题下要么"范式契合且活跃"、要么"具备真正的双向同步且活跃"；B 类是有价值但缺原生双向或活跃度下滑；C 类是停更或与 Spec→代码范式偏差较大的研究样本。
4. **空白点**：目前没有一个项目同时满足"①确定性的 Spec→代码双向同步（含 round-trip 与待更新标记）②直接面向代码文本 ③活跃维护"。这正是指向新实现/研究课题的空白。