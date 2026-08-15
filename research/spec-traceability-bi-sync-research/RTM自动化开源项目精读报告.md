# 需求可追踪性 / RTM 自动化开源项目精读报告

> 研究总问题：**Spec-as-Source 范式下从 Spec 到代码的可追踪性(Traceability)与双向同步**。
> 评分维度：对总问题及子问题（需求追踪矩阵RTM自动生成、Spec↔Code漂移检测、双向同步）的解决程度、采用价值、与该范式的适应程度、项目活跃度。
> 评分：A（高相关+高活跃或高完成度）/ B（部分相关或有明显短板）/ C（低相关或已停滞）。
> 说明：所有信息均来自对 GitHub 仓库页/README/arXiv 的一手抓取，未抓取到内容的已明确标注；未编造任何数据。

---

## 1. TraceLab · CoEST

- **名称**：TraceLab（Software Traceability Instrument）
- **作者/组织**：CoEST（Center of Excellence for Software & Systems Traceability）；仓库 `github.com/CoEST/TraceLab`（注意：题目写的 coest/tracelab，实际组织为 `CoEST`）
- **年份**：2014–2018（首个提交 2014-04，最后发布 v1.8 于 2018-05）
- **技术栈/功能**：C#（95%）/.NET 桌面应用；为"可追踪性研究"设计的工作台(workbench)，面向研究者搭建、组合、评估追踪链接恢复(TLR)实验；含组件/插件体系、实验流程编排、评估指标计算；需 Visual Studio 2010 编译。
- **关键能力**：
  - RTM 自动生成：**不直接提供**。它是研究实验平台，而非面向生产的 RTM 生成器；可运行 TLR 算法并比较其生成链接的效果。
  - 追踪链接：支持（TLR 算法组件化执行）。
  - 双向同步：**不支持**。
  - 漂移检测：**不支持**。
- **活跃度/维护状态**：已停滞。仓库最后提交 2016-10，最后 release v1.8 为 2018-05，仅 13 commits、6 tags。
- **评分：C** —— 学术 TLR 实验工作台，理念开创但已停止维护，且与现代 Spec-as-Source 的"代码式/自动同步"需求几乎无适配。

---

## 2. TraceBERT

- **名称**：TraceBERT（BERT-based software traceability）
- **作者/组织**：Jinfeng Lin（jinfenglin）；合作者 Ting Zhang；论文作者含 Cleland-Huang 等（ICSE 2021）
- **年份**：2021（ICSE 2021 论文；仓库最后提交 2021-11）
- **技术栈/功能**：Python（80%）+ Shell；基于微软 CodeBERT 的预训练模型；两阶段训练（① Code Search 大规模函数↔文档对，② Issue-Commit 追踪精调）；提供 Siamese / Single / Twin 三种架构；用于在 NL 工件与 PL 代码工件之间恢复追踪链接。
- **关键能力**：
  - RTM 自动生成：间接支持。本质是"追踪链接恢复"模型，可把 NL 需求/Issue 链接到代码工件，从而支撑 RTM；但仓库仅提供训练与评估脚本，**未提供生产级预测脚本**（README 明确说明）。
  - 追踪链接：**是核心能力**（NL→PL 链接恢复）。
  - 双向同步：**不支持**。
  - 漂移检测：**不支持**。
- **活跃度/维护状态**：研究型复制(replication)仓库，已不再活跃（最后提交 2021-11，无 release）。
- **评分：B** —— 在"从 Spec/需求到代码的链接恢复"上技术贡献显著（可作 RTM 自动生成的模型底座），但仅研究代码、无产品化、无双向同步与漂移，活跃度低。

---

## 3. ArDoCo / Core（ARCOTL）

- **名称**：ArDoCo Core Framework（ARchitecture Documentation Consistency）
- **作者/组织**：KIT KASTEL MCSE 组（德国）；仓库 `github.com/ArDoCo/Core`（题目写 ArDoCo/Core，实际用户为 `ardoco`）
- **年份**：2021 至今（活跃；最新提交 2026-07，v1.0.0 release 2024-03）
- **技术栈/功能**：Java（98.7%）；为 TLR（Traceability Link Recovery）与**不一致检测(inconsistency detection)** 定义核心框架元素；NLP/NLU 处理非结构化架构文档，与架构模型（PCM/UML）建立链接。
- **关键能力**：
  - RTM 自动生成：间接支持（TLR 引擎产出文档↔模型链接，可构成追踪矩阵）。
  - 追踪链接：有（文档↔PCM/UML 模型链接恢复）。
  - 漂移检测：**有**（核心目标之一即"不一致/一致性检测"，即规格与实现漂移的检测）。
  - 双向同步：部分相关（检测不一致，但写回/自动双向同步并非主卖点）。
- **活跃度/维护状态**：**非常活跃**（2026 年仍有合并提交，2,464 commits、55 releases、12 贡献者，MIT 许可）。
- **评分：A** —— 直接命中"Spec↔Model 可追踪性 + 漂移/不一致检测"，且活跃度高、工程化完整，是本批次与总问题匹配度最高的研究级框架之一。

---

## 4. ArDoCo / SimpleTracelinkDiscovery（STD）

- **名称**：SimpleTracelinkDiscovery（STD）
- **作者/组织**：ArDoCo 团队（`github.com/ArDoCo/SimpleTracelinkDiscovery`，实际用户 `ardoco`）
- **年份**：2022–2023（最后提交 2023-06，70 commits）
- **技术栈/功能**：Java（99.4%）；极简的 TLR 基线方法：将非正式文本架构文档与软件架构模型(PCM)链接；通过匹配模型实体名及其 n-gram 与文档中的词/n-gram，用归一化 Levenshtein 或 Jaro-Winkler 相似度判定链接。
- **关键能力**：
  - RTM 自动生成：部分支持（文档↔模型链接恢复，作为基线）。
  - 追踪链接：有（简单字符串/相似度匹配）。
  - 双向同步：**不支持**。
  - 漂移检测：**不支持**（仅静态链接恢复）。
- **活跃度/维护状态**：已归档（GitHub 标记 Public archive），不再开发。
- **评分：C** —— 仅是一个轻量 TLR 基线算法，无同步/漂移能力，且已归档，适配 Spec-as-Source 的价值有限。

---

## 5. Loom（jsuppe/loom）

- **名称**：Loom（📿 Weaving requirements through code）
- **作者/组织**：jsuppe（题目写 juuppe，实际仓库为 `github.com/jsuppe/loom`）
- **年份**：2026（初始 release 2026-02，最新提交 2026-06，242 commits）
- **技术栈/功能**：Python 包 + SQLite 本地存储 + MCP server + 本地 Web UI；面向 AI 辅助开发的**语义化需求可追踪性系统**。核心命令：`loom extract`（从对话/自然语言提取需求）、`loom spec`（展开为规格）、`loom link`（链接代码并用内容哈希检测漂移）、`loom sync`（生成 REQUIREMENTS.md/TEST_SPEC.md 等活文档**并含追踪矩阵**）、`loom decompose`/`loom_exec`（把规格拆为原子任务交给本地小模型执行）、`loom verify`（推进需求生命周期 pending→in_progress→implemented→verified）、`loom check`/`loom context`（漂移告警）。
- **关键能力**：
  - RTM 自动生成：**有**（`loom sync` 自动生成追踪矩阵 + 活文档）。
  - 追踪链接：**有**（`loom link`，含内容哈希）。
  - 双向同步：**部分**（需求生命周期自动推进、活文档再生成，属强"文档=源"闭环；Spec→代码执行）。
  - 漂移检测：**有**（内容哈希 + Driftgraph 声明图 + 三层漂移告警通道，scope 限定后 recall 100% / FPR 12%，实证 ~1,050 次试验）。
- **活跃度/维护状态**：**非常活跃**（2026 年仍在持续迭代，MIT 许可，含实证评估）。注意：仓库含大量个人/Claude 协作痕迹，需自行评估工程成熟度。
- **评分：A** —— 几乎逐点命中总问题（RTM 自动生成、Spec↔Code 漂移检测、双向活文档同步），且针对 AI/Spec-as-Source 场景设计、活跃度极高，是本批次与本范式最契合的项目。

---

## 6. reqtrace

- **名称**：reqtrace
- **作者/组织**：philipmiesbauer（`github.com/philipmiesbauer/reqtrace`）
- **年份**：2026（初始提交 2026-02，最后提交 2026-03，35 commits）
- **技术栈/功能**：纯 Python（100%）；GitOps / Docs-as-Code 需求追踪工具。用 `.rqtr`（YAML）定义需求，通过块注释标签（`@trace-start`/`@trace-end`）把实现映射到需求；DAG 父级依赖（`derived_from`）；支持部分实现百分比；**ReqIF 导入/导出**；schema 校验；交互式 HTML 报告。CLI 工具含 `reqtrace` / `reqtrace-validate` / `reqtrace-exchange`。
- **关键能力**：
  - RTM 自动生成：**有**（`reqtrace --reqs/--src/--html` 生成追踪矩阵与覆盖率报告）。
  - 追踪链接：**有**（代码标签↔需求）。
  - 双向同步：**部分**（Docs-as-Code，但以扫描/报告为主，未见自动双向写回）。
  - 漂移检测：**弱/无**（未实现自动漂移检测；后续计划含"测试验证扫描器"）。
- **活跃度/维护状态**：活跃（2026 年仍在提交，13 tags，GPL-3.0），但单作者、早期阶段。
- **评分：B** —— 直接面向"需求即代码 + RTM 自动生成 + ReqIF"且活跃，命中范式；但缺漂移检测与真正双向同步，规模尚小。

---

## 7. shtracer

- **名称**：shtracer
- **作者/组织**：qq3g7bad（`github.com/qq3g7bad/shtracer`）
- **年份**：2024–2026（首个样本 2024-11，最新 release v0.1.6 于 2026-05，301 commits）
- **技术栈/功能**：纯 POSIX Shell（76.5%）+ JavaScript/CSS（HTML 报告）；零依赖、CI/CD 原生。用 Markdown 注释标签（如 `<!-- @REQ-001@ -->`）在需求→架构→实现→测试各层做标记，生成结构化 JSON 追踪矩阵、HTML/Markdown 报告；支持 `-c` change 模式（全局重命名标签）、`-v` verify 模式（检测孤立/重复标签、悬空 FROM 引用）、多种退出码供 CI 判定。
- **关键能力**：
  - RTM 自动生成：**有**（JSON 追踪矩阵 + HTML/Markdown 报告，含各层覆盖率/upstream/downstream）。
  - 追踪链接：**有**（层间 `FROM:` 链，REQ→ARCH→IMPL→TEST）。
  - 双向同步：**无**（只读检测/报告）。
  - 漂移检测：**部分**（verify 模式检测孤立/重复/悬空标签，接近漂移/一致性检查，但非语义漂移）。
- **活跃度/维护状态**：**活跃**（2026 年迭代中，MIT，2 贡献者，含 66 单测 + 32 集成测试）。
- **评分：B** —— 轻量、零依赖、CI 友好，能自动生成 RTM 并做标签级一致性检查，贴近胶水式工作流；但无真正的 Spec↔Code 语义漂移检测与双向同步。

---

## 8. ReqForge

- **名称**：ReqForge
- **作者/组织**：Haider094（Wajahat Haider，`github.com/Haider094/ReqForge`）
- **年份**：2026（last commit 2026-04，仅 6 commits）
- **技术栈/功能**：Python（96.8%）+ FastAPI + LangChain；LLM（OpenAI / Anthropic Claude / 本地模型）把自然语言需求转成功能/边界/负向测试用例，并**生成测试↔需求的追踪矩阵**；CLI、REST API、Python SDK；导出 JSON/Markdown/CSV；提供 Docker。
- **关键能力**：
  - RTM 自动生成：**有**（自动生成 test↔requirement 追踪矩阵，但针对"需求→测试"而非"Spec→代码"）。
  - 追踪链接：有（测试用例↔源需求）。
  - 双向同步：**无**。
  - 漂移检测：**无**。
- **活跃度/维护状态**：早期/个人项目（6 commits、单作者、无 release）。
- **评分：C** —— 用 LLM 做需求→测试并顺带产 RTM，思路契合范式但仅覆盖"需求↔测试"一环、无代码追踪/同步/漂移，工程极早期。

---

## 9. OpenReq（OpenReqEU）

- **名称**：OpenReq（H2020 项目生态）
- **作者/组织**：OpenReq 联盟（`github.com/OpenReqEU`，Horizon 2020 资助 #732463；含 HITeC、TU Graz、SIEMENS、University of Helsinki、Qt 等）
- **年份**：2017–2020（项目周期；多数仓库最后更新 2020–2024，个别 2026）
- **技术栈/功能**：52 个仓库，Java/Python/Go/JS 微服务生态，面向**社区驱动需求工程**：需求抽取/分类、重复检测、相似需求推荐、依赖检测、优先级排序、群体决策、DOORS 集成、Qthulhu/Issue-Link-Map 可视化、Milla/KeljuCaaS/Mulperi 推理与编排等。
- **关键能力**：
  - RTM 自动生成：**不直接**（生态偏需求管理与推荐，而非 Spec↔Code 追踪矩阵）。
  - 追踪链接：**部分**（依赖检测、跨引用检测、相似性检测，属需求间链接而非需求↔代码）。
  - 双向同步：**无**（虽有 DOORS 集成脚本，但非 Spec↔Code 双向同步）。
  - 漂移检测：**无**。
- **活跃度/维护状态**：项目已结束，多数微服务停滞（2020–2024 后基本不更新）。
- **评分：C** —— 是大型 RE 工具生态，但时间已过、基本停滞，且不聚焦 Spec↔Code 双向追踪/漂移，与总问题的直接适配最弱。

---

## 10. CoEST Datasets

- **名称**：CoEST Datasets（Center of Excellence for Software & Systems Traceability 数据集）
- **作者/组织**：CoEST（coest.org；主办 NASA/NSF 资助的可追踪性卓越中心）
- **年份**：约 2010 年代起持续维护（官方网站 coest.org）
- **技术栈/功能**：数据/基准集（非工具）。收录常见 TLR/RM 基准：iTrust、eTour、EBT、RETRO.NET、CM1-NASA、GANTT、MODIS、WARC、CCHIT-WorldVista、Dronology、EasyClinic、eAnci 等，含 NL 需求 ↔ 代码/工件/低层需求的标注链接（gold standard）。
- **关键能力**：
  - RTM 自动生成：**否**（是可用于评估 RTM 自动生成/链接恢复算法的**基准数据**）。
  - 追踪链接：提供标注好的 ground-truth 链接供评测。
  - 双向同步 / 漂移检测：**无关**。
- **活跃度/维护状态**：官网 coest.org 页面在多数抓取中返回 robots disallow/空内容，**未能直接抓取到数据集清单页面**（依据第三方论文与 TraceLab README 引用确认其存在与内容）；数据本身仍被 2025 年研究引用。
- **评分：B** —— 作为 RTM/TLR 研究的行业标准评测数据非常宝贵，但它是数据而非工具，不提供任何自动生成/同步/漂移能力。

---

## 11. RETRO.NET Dataset

- **名称**：RETRO.NET（REquirements TRacing On target .NET Dataset）
- **作者/组织**：Jane Huffman Hayes、Jared Payne、Alex Dekhtyar（arXiv:1807.11344，IEEE RE 2018）
- **年份**：2018
- **技术栈/功能**：数据集（C# / Visual Basic 源代码）+ 需求规格 + 用于互相追踪的 gold standard/答案集 + 解析需求规格的脚本（retro.net 格式）。
- **关键能力**：为需求↔代码追踪提供带真值标注的评测语料；**可用于评估 RTM 自动生成与链接恢复质量**；本身不提供自动生成、双向同步或漂移检测。
- **活跃度/维护状态**：静态数据集（2018 发布）；仍被 2025 年研究作为基准引用。
- **评分：B** —— 质量高的"需求↔代码"追踪评测基准，适合验证 Spec-as-Source 可行性与 RTM 自动生成精度，但属数据而非可用工具。

---

## 总览对比表

| # | 项目 | 活跃度 | RTM自动生成 | 追踪链接 | 双向同步 | 漂移检测 | 评分 |
|---|------|--------|:---:|:---:|:---:|:---:|:---:|
| 1 | TraceLab (CoEST) | 停滞(2018) | 否 | 有(实验) | 否 | 否 | **C** |
| 2 | TraceBERT | 停滞(2021) | 间接(模型) | 有 | 否 | 否 | **B** |
| 3 | ArDoCo/Core | **高(2026)** | 间接 | 有 | 部分(检测) | **有** | **A** |
| 4 | ArDoCo/STD | 归档(2023) | 部分 | 有(基线) | 否 | 否 | **C** |
| 5 | Loom (jsuppe) | **高(2026)** | **有** | **有** | **部分** | **有** | **A** |
| 6 | reqtrace | 高(2026) | **有** | 有 | 部分 | 弱 | **B** |
| 7 | shtracer | **高(2026)** | **有** | 有 | 否 | 部分(标签级) | **B** |
| 8 | ReqForge | 早期(2026) | 有(需求↔测试) | 有 | 否 | 否 | **C** |
| 9 | OpenReqEU | 停滞(2020-24) | 否 | 部分(需求间) | 否 | 否 | **C** |
| 10 | CoEST Datasets | 静态 | 数据 | 数据 | — | — | **B** |
| 11 | RETRO.NET | 静态 | 数据 | 数据 | — | — | **B** |

## 关键结论（针对总问题）

1. **最契合 Spec-as-Source 范式的两个项目是 Loom 与 ArDoCo/Core**：Loom 同时覆盖 RTM 自动生成、Spec↔Code 漂移检测与双向活文档闭环，且专为 AI 辅助/文档即源场景设计；ArDoCo 提供研究级的文档↔模型可追踪性与不一致（漂移）检测，二者均保持高活跃度，值得重点借鉴。
2. **RTM 自动生成**在实用工具侧主要由轻量派（reqtrace、shtracer）以"标签+矩阵报告"实现，研究侧由 TraceBERT/ArDoCo 以链接恢复模型实现；Loom 则把矩阵作为活文档自动产出。
3. **双向同步与语义漂移检测在全批次中最薄弱**：纯工具（reqtrace/shtracer/ReqForge/C TraceLab）基本只做"读+报告"，无自动写回；具备漂移概念的仅 Loom（内容哈希+声明图）与 ArDoCo（不一致检测）。
4. **数据集（CoEST、RETRO.NET）** 是评估任何 RTM 自动生成方案精度的基准，适合作为验证 Spec-as-Source 落地效果的地基。