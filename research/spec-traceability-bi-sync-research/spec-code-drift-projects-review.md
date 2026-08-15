# Spec↔Code 漂移检测 / 架构一致性 —— 开源项目精读与 ABC 评分

> 研究问题：Spec-as-Source 范式下从 Spec 到代码的可追踪性（Traceability）与双向同步。
> 评分维度：对子问题 H7（Spec↔Code 漂移检测，区分"合规性偏离 Compliance Violation"与"良性演进 Benign Evolution"）的解决程度、采用价值、与 Spec-as-Source 范式的适应程度、项目活跃度。
>
> 数据来源：逐一抓取各仓库 GitHub/Bitbucket 主页、README、Release 与活跃度信息（2026-08 抓取）。

---

## 1. ArchUnit

- 作者/组织：TNG Technology Consulting（Peter Gafert 主导）
- 年份：2014 年启动，持续维护至今
- 技术栈/功能：Java 库，通过 ASM 分析字节码并导入 Java 代码结构（类、包、依赖、层、切片），用纯 Java 单测框架（JUnit 等）自动校验架构与编码规则。
- 关键能力：
  - 依赖/包/层/切片关系检查、循环依赖检测、类成员规则；
  - 规则以"代码内手写即"ArchRule""表述，作为单测在 CI 中运行；
  - 侧重"合规检查"（对已声明的结构性规则做一致性校验），**不直接做 Spec 文本↔代码的文档化漂移检测**，也不区分"合规偏离 vs 良性演进"（规则是既定且二元的）。
- 活跃度/维护状态：极高。v1.5.0（2026-08-04），2,717 commits，95 contributors，2.3K+ 依赖方，Apache-2.0。
- 评分：**A**
- 一句话理由：生态级、最活跃、最广泛采用的 Java 架构合规测试库，但属"代码内规则→代码"的结构合规范式，并非 Spec 文本↔代码漂移检测，对 H7 的核心区分力有限。

---

## 2. ArchUnitNET

- 作者/组织：TNG（ArchUnit 的 C# 版）
- 年份：约 2017 年启动，持续维护
- 技术栈/功能：C#/Mono.Cecil 分析程序集，导入 C# 代码结构，检查类/成员/接口依赖与命名规则；提供 xUnit、NUnit、MSTest、TUnit、xUnitV3 等扩展。
- 关键能力：与 ArchUnit 能力对齐，全部为"代码内规则→代码"的结构合规测试；接口画出 C# 代码结构以支持 Debug 下运行。无 Spec 文档↔代码漂移检测。
- 活跃度/维护状态：活跃。v0.13.3（2026-03-05），1,166 commits，35 contributors，Apache-2.0。
- 评分：**B**
- 一句话理由：是 ArchUnit 的 C# 全功能移植、活跃稳定，但生态/体量小于 Java 版，且同为规则式合规检查，对 H7 的 Spec 漂移与良性演进区分贡献有限。

---

## 3. jQAssistant

- 作者/组织：jQAssistant 社区（BUSHIDO 组织发起，Dirk Mahler 等）
- 年份：2016 年开源，持续维护
- 技术栈/功能：Java；把源码/制品扫描进 Neo4j 图数据库，用 Cypher 书写"概念（concepts）"与"约束（constraints）"规则，执行后生成违规报告；插件化 scanner/rule 生态（Java、Maven、Git、Asciidoc 等）。
- 关键能力：
  - 强大的关系图建模 + 可编程校验规则，可表达复杂架构约束与合规校验；
  - 能"对比实现 vs 意图"（通过约束查询），具备架构一致性检查能力；
  - 但规则由人手工编写，**非 Spec 文本驱动、无自动漂移/良性演进区分语义**。
- 活跃度/维护状态：很高。v2.9.1（2026-02-17），11,536 commits，31 contributors，GPL-3.0。
- 评分：**A**
- 一句话理由：基于图数据库的成熟规则/合规引擎，灵活且极活跃，可作为架构一致性后端，但漂移检测依赖手写 Cypher 规则，不天然支持 Spec↔Code 文本漂移与良性演进判定。

---

## 4. DCL2Check

- 作者/组织：ASERG / UFMG（巴西米纳斯联邦大学）
- 年份：约 2016 年（仓库快照 2016-12）
- 技术栈/功能：Java 开发的 Eclipse 插件；基于 DCL 2.0（Dependency Constraint Language）进行架构"规范+一致性"检查。
- 关键能力：以 DCL 2.0 规范文件声明依赖约束，对项目做架构一致性（conformance）校验并报告违规——理念上属于"Spec(规范)→代码"合规检查，是这 11 个项目中最接近"规范驱动合规"的一类。
- 活跃度/维护状态：基本停更。1 star、0 forks、4 commits、无 Release、需手动安装 Xtext 与 jar 到 Eclipse；最后活动约 2016 年，MIT。
- 评分：**C**
- 一句话理由：理念契合（规范驱动的架构一致性检查），但为单作者消亡的 Eclipse 插件、2016 年后停更、几乎无使用，无漂移检测与活跃度支撑分级。

---

## 5. HUSACCT

- 作者/组织：HU University of Applied Sciences Utrecht（无单一作者，学术项目）
- 年份：2011 年启动，v1.0 于 2012-12，v5.5 于 2023-01
- 技术栈/功能：Java 写就，支持 Java + C#；提供"软件架构合规检查（SACC）"与"架构恢复（SAR）"。
- 关键能力：明确支持"实现架构（源码）vs 意图架构（设计 Spec）"的一致性监控；支持语义丰富模块化架构（SRMA：子系统/层/组件等模块 + 多种规则类型），静态分析并报告违规；附带可视化/浏览/报告。
- 活跃度/维护状态：停滞。v5.5（2023-01-25），最后 commit 2023-09，4,292 commits、65 contributors；Eclipse/Maven 插件为 2012 年遗留且不再维护。
- 评分：**B**
- 一句话理由：在"意图架构 vs 实现"合规检查上最直白贴合 Spec↔Code 思想且支持语义化模块规则，但时隔已停更、仅 Java/C#、无连续漂移与良性演进识别能力。

---

## 6. ARCADE

- 作者/组织：Joshua Garcia & Nenad Medvidović（USC/UCI）
- 年份：约 2012 年启动，Bitbucket 仓库最后更新 2022-05
- 技术栈/功能：Java 为主（arcadepy 伴生 Python 部分）；"架构恢复、变更与衰变评估器（Architecture Recovery, Change, And Decay Evaluator）"。
- 关键能力：8 种架构恢复技术、架构坏味目录与检测算法、架构变更/衰变度量（decay metrics）、主题模型等；用于研究"变更与衰变"，**关注恢复与度量，而非 Spec↔Code 文档化漂移检测**。
- 活跃度/维护状态：停滞。Bitbucket 仓库最后更新 2022-05，1 watcher、0 forks、无 CI 构建；请用户回访以争取经费。
- 评分：**C**
- 一句话理由：是架构恢复/演化/坏味的研究型工作台，测"衰变"而非规范↔代码追踪漂移，托管于 Bitbucket、2022 后基本停更，与 Spec-as-Source 适配度低。

---

## 7. ArchGuard

- 作者/组织：Tgenz1213（个人/小组）
- 年份：2026-01 初始提交（新项目，迭代极快）
- 技术栈/功能：Go 编写 CLI；LLM（Ollama 默认本地、OpenAI、Gemini）+ 向量检索（本地 index 或 Postgres/pgvector，HNSW）+ ADR 解析。
- 关键能力：
  - 核心定位"架构漂移检测器"：用 LLM 语义比对代码变更与 ADR（架构决策记录）规则，判断是否违反 ADR；
  - 输出 [VIOLATION] + 推理理由，可区分"是否符合既定 ADR 决策"，直接命中"合规性偏离"检测这一面；
  - 支持 delta 索引、智能截断、缓存、CI 退出码、archguard-ignore 抑制（具"人工确认后免检"机制，接近良性演进处理）；
  - Confluence 集成拉取 ADR，GitHub Actions 市场。
- 活跃度/维护状态：极活跃。51 commits、14 releases（v1.5.0，2026-08-05），6 contributors，MIT。
- 评分：**A**
- 一句话理由：用 LLM 语义逻辑把"ADR 规范↔代码"漂移检测做成 CI 门禁并给出可解释违规推理，最贴合合规偏离判定，活跃度极高；弱点是 ADR 粒度为"决策级"而非"逐条需求/验收标准级"，良性演进大多靠人工 ignore。

---

## 8. SpecSeal

- 作者/组织：xantus-ai（Brandon "onamfc" Estrella）
- 年份：2026-05 初始提交（pre-1.0，v0.1）
- 技术栈/功能：TypeScript CLI（npm 包），Markdown spec 解析 + 哈希绑定注解扫描器。
- 关键能力：
  - 专为"Spec-as-Source"设计：spec 用稳定 ID 的 Markdown 写，代码用 `// @spec REQ-ID #hash` 注解引用；
  - 哈希只覆盖行为契约段（Acceptance/Non-functional），**spec 文案的润色改动不触发漂移，只有行为契约变化才标记 stale**——本质上就是"区分合规性偏离 vs 良性演进"的哈希版本；
  - 检测 stale 注解、孤儿注解、未实现需求；提供 `check/coverage/map/sync/init` 命令与 JSON 输出，可做 CI 质量闸门；
  - 定位为 Spec Kit / Cursor / Claude Code 等生成工具之上的"覆盖+漂移"层。
- 活跃度/维护状态：早期但活跃。7 commits、1 contributor、无正式 Release，MIT。
- 评分：**A**
- 一句话理由：在这 11 个项目中与 H7 及 Spec-as-Source 范式契合度最高——用"行为契约哈希"天然把文本性编辑与行为性偏离区分开，可落 CI 度量覆盖；但尚处 v0.1、仅 TS/JS 扫描器、单作者，成熟度待验证。

---

## 9. DocChecker

- 作者/组织：FSoft-AI4Code（FPT AI Center，Dau Thi Van Anh 等）；论文 EACL 2024 Demo
- 年份：2023-05 开源，2024-01 后停更
- 技术栈/功能：Python/PyTorch；基于 encoder-decoder 的代码-文本预训练模型，三目标联合预训练（code-text 对比学习、二分类、文本生成）。
- 关键能力：检测"代码↔注释/文档不一致"，判断 pair 为 Consistent / Inconsistent，并为不一致 pair 生成推荐 docstring；支持 10 种语言；在 Just-In-Time 数据集上 fine-tune 验证。
- 活跃度/维护状态：停更。25 commits、1 contributor、无 Release，最后 commit 2024-01-23，Apache-2.0。
- 评分：**C**
- 一句话理由：面向"代码-注释不一致"的深度学习检测器，范围是函数级注释而非需求 Spec↔代码、且已停更，对 H7 规范漂移与正常演进区分帮助有限。

---

## 10. deep-jit-inconsistency-detection

- 作者/组织：panthap2（Sheena Panthaplackel 等，UT Austin）；论文 AAAI-2021
- 年份：2020-12 开源，研究代码/数据集
- 技术栈/功能：Python/PyTorch；序列（双向 LSTM）与图（GGNN/gated graph neural network）编码器 + 特征，检测与更新注释。
- 关键能力：Just-In-Time 检测"代码变更后注释是否失同步"，含三种检测模型（SEQ/GRAPH/HYBRID）与"检测+更新"联合/分离训练；提供 AST diff 流程与数据集。
- 活跃度/维护状态：基本停更的研究产物。11 commits、1 contributor、无 Release，最后 commit 2025-07（README 更新），MIT。
- 评分：**C**
- 一句话理由：是有价值的评论-代码 JIT 一致性研究代码与数据集，但面向注释漂移而非需求 Spec↔代码追踪，且为无维护的学术复现物件，与 Spec-as-Source 适配度低。

---

## 11. DriftBench

- 作者/组织：rigour-labs（Rigour，erashu212 等）
- 年份：2026-01 初始提交（v0.1，迭代中）
- 技术栈/功能：Python 基准 + Rigour CLI（drift 检测引擎，本地 Qwen 模型 + LLM 教师）；含 `datasets/`（lodash、flask、django、fastapi、shadcn、tanstack）、`runner/`（harness/engine）、`rlaif/` 训练管线、`api/` 排行榜。
- 关键能力：
  - 提出"全频谱 PR 漂移与意图保持基准"：7 类漂移（Staleness、Security、Architecture、Pattern、Logic、Standard、Agent Team Drift），用于评测 AI 编码工具是否"语法正确但违反设计模式/安全/隐式业务逻辑"；
  - 用 golden_patch + drift_candidates 构造任务，golden 应无漂移、含缺陷补丁应触发漂移，产出 Pass Rate / DDR / Accuracy 指标与排行榜；
  - 本身是"评测基准 + 漂移检测引擎"，漂移分类学（含 Architecture Drift）与 H7 概念高度相关。
- 活跃度/维护状态：活跃。95 commits（2026-03-09），多模块持续迭代，MIT。
- 评分：**B**
- 一句话理由：提供了直接可用的"漂移"分类学与可复现基准来度量代码漂移（含架构漂移），与 H7 问题框架高度吻合，但定位是评测 AI 编码产物而非 Spec↔Code 同步工具，且依赖 Rigour 商业化引擎。

---

## 汇总表

| # | 项目 | 组织 | 栈 | 漂移检测 | 架构一致性 | Spec↔代码对比 | 合规偏离识别 | 活跃度 | 评分 |
|---|------|------|----|---------|-----------|--------------|-------------|--------|------|
| 1 | ArchUnit | TNG | Java | 部分(规则) | ✔ | ✘(代码内规则) | 部分(二元) | ★★★★★ | **A** |
| 2 | ArchUnitNET | TNG | C# | 部分(规则) | ✔ | ✘ | 部分(二元) | ★★★★ | **B** |
| 3 | jQAssistant | jQAssistant | Java+Neo4j | 部分(手写规则) | ✔ | ✘ | 部分(约束) | ★★★★★ | **A** |
| 4 | DCL2Check | ASERG-UFMG | Java/Eclipse | ✘ | ✔(规范驱动) | ✔(DCL规范) | 部分 | ✗(停更) | **C** |
| 5 | HUSACCT | HU Utrecht | Java/C# | ✘ | ✔(SACC) | ✔(意图vs实现) | ✔ | ✗(停滞) | **B** |
| 6 | ARCADE | Garcia(UCI) | Java | ✘(衰变度量) | 恢复/度量 | ✘ | ✗ | ✗(停滞) | **C** |
| 7 | ArchGuard | Tgenz1213 | Go+LLM | ✔(ADR vs 代码) | ✔ | ✔(ADR) | ✔(可解释) | ★★★★★(新且快) | **A** |
| 8 | SpecSeal | xantus-ai | TypeScript | ✔(哈希契约) | 部分 | ✔(spec↔code) | ✔(直观) | ★★★(早期) | **A** |
| 9 | DocChecker | FSoft-AI4Code | Python/ML | 注释↔代码 | ✘ | ✘ | ✘ | ✗(停更) | **C** |
| 10 | deep-jit | panthap2 | Python/ML | 注释↔代码(JIT) | ✘ | ✘ | ✘ | ✗(研究物) | **C** |
| 11 | DriftBench | rigour-labs | Python | ✔(7类分类学) | ✔(Arch Drift) | 部分 | ✔(基准) | ★★★★ | **B** |

---

## 结论要点

- **最贴合 H7 与 Spec-as-Source 的两个**：**SpecSeal**（用"行为契约哈希"把文案性编辑与行为性偏离天然区分，输出可测的 spec 覆盖率与漂移，可直接作为 CI 门禁）与 **ArchGuard**（用 LLM 语义比对 ADR↔代码，输出可解释的违规推理，落地 CI）。
- **最成熟、可作合规后端的**：ArchUnit / jQAssistant——架构合规检查与规则引擎很强、生态活跃，但漂移检测依赖手工规则，无"良性演进 vs 合规偏离"的自动区分。
- **"规范驱动合规"的历史先驱**：DCL2Check、HUSACCT 理念契合（规范/意图架构 vs 实现），但均已停更或停滞，工程化与活跃度不足。
- **与研究问题相关但侧重不同**：DriftBench 提供漂移分类学与评测基准；DocChecker、deep-jit 聚焦"注释↔代码"不一致而非需求 Spec↔代码。
- **建议采纳组合**：以 **SpecSeal 式"哈希化契约注解 + 覆盖率/漂移/孤儿检测"** 作为 Spec-as-Source 的双向同步与追踪核心，叠加 **ArchGuard 式 LLM 语义合规判定** 以处理"良性演进"的模糊边界，并以 **DriftBench 的 7 类漂移分类学** 作为区分合规偏离与良性演进的判据框架。