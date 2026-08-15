# 需求可追踪性（Requirements Traceability）与 RTM 自动化生成 —— 审查后精选清单

> 检索日期：2026-08-15。本清单为**审查后**版本：对初版收集逐条核验真实性、剔除存疑/低价值条目、按"时效性（近三个月内，2026-05-15 之后）"与"重大意义"两个维度标注，并补充了 2026 年最新论文与活跃开源项目。
>
> 审查结论：**奠基/综述类经典论文保留（重大意义）、2026 年最新 LLM 论文全部保留（时效性）、存疑条目的作者信息已核实补齐、仓库归属已修正。** 初版中"作者待核实"的 2 篇论文已确认作者与链接。

---

## 一、论文（Papers）

### 1.1 奠基性 / 经典论文（保留理由：重大意义）

| 标题 | 作者 | 年份 | 出处 / 链接 | 一句话核心贡献 | 保留理由 |
|---|---|---|---|---|---|
| An analysis of the requirements traceability problem | Gotel, Finkelstein | 1994 | IEEE ICRE 1994, DOI:10.1109/ICRE.1994.292398 | 基于 100+ 从业者实证厘清可追踪性问题本质，提出 pre-RS/Post-RS 概念，整个领域理论起点。 | 奠基之作 |
| Recovering Traceability Links between Code and Documentation | Antoniol et al. | 2002 | IEEE TSE 28(10), DOI:10.1109/TSE.2002.1041053 | 用信息检索（IR）自动恢复代码↔文档追踪链接，是本主题"自动映射"的经典源头。 | 经典开山 |
| Advancing Candidate Link Generation for Requirements Tracing | Hayes, Dekhtyar, Sundaram | 2006 | IEEE TSE 32(1):4–19, DOI:10.1109/TSE.2006.3 | 系统比较 TF-IDF/LSI 等候选链生成方法并给出 RETRO 原型，是后续复现的常用基线。 | 方法基线 |
| Software Traceability: Trends and Future Directions | Cleland-Huang et al. | 2014 | ICSE FOSE 2014 | 面向未来的可追踪性综述，映射研究方向到质量目标与开放挑战。 | 权威综述 |
| Grand Challenges of Traceability: The Next Ten Years | Cleland-Huang et al. | 2017 | ICSE 2017 / arXiv:1710.03129 | 提出未来十年可追踪性"宏大挑战"，是梳理研究议程的关键文献。 | 权威综述 |
| Semantically Enhanced Software Traceability Using DL | Guo, Cheng, Cleland-Huang | 2017 | ICSE 2017 / arXiv:1804.02438 | 把深度学习（词嵌入+语义增强）引入需求→代码追踪，DL 类方法代表。 | DL 起点 |
| Traceability Transformed: Generating more Accurate Links with Pre-Trained BERT Models | Lin, Liu, Zeng, Jiang, Cleland-Huang | 2021 | ICSE 2021, pp.324–335 | 提出 Trace BERT（T-BERT），预训练 BERT 多阶段微调，MAP 显著优于 IR 与早期 DL。 | LLM 前夜 |

### 1.2 最新 LLM 追踪方法（2026，保留理由：时效性 + 直接相关）

| 标题 | 作者 | 年份/月份 | 出处 / 链接 | 一句话核心贡献 | 时效标注 |
|---|---|---|---|---|---|
| **R2Code: A Self-Reflective LLM Framework for Requirements-to-Code Traceability** | Y. Wang, J. Keung, X. Ma, Z. Mao, K. Chen, Y. Li | 2026-04（已录用 IEEE COMPSAC 2026） | arXiv:2604.22432 | 三组件（BAN 双向对齐 + SRCV 自反思校验 + DCAR 上下文自适应检索），5 数据集平均 F1 +7.4%、token 最多 -41.7%。 | 重大意义（顶会录用） |
| **TraceLLM: LLM with Prompt Engineering for Enhanced Requirements Traceability** | N. Alturayeif, I. Ahmad, J. Hassine | 2026-02（已发表于 Requirements Eng. 31(6)） | arXiv:2602.01253 / DOI:10.1007/s00766-026-00460-1 | 系统化提示工程+样例选择，8 个 LLM、4 基准数据集聚类，标签感知+多样性采样最有效，已正式发表。 | 时效性+已发表 |
| Requirements Traceability Link Recovery via RAG | T. Hey, D. Fuchß, J. Keim, A. Koziolek | 2025 | ArDoCo 项目页 ardoco.github.io/c/refsq25 / Springer DOI:10.1007/978-3-031-88531-0_27 | LLM+RAG 做需求追踪链接恢复，6 基准数据集验证思维链收益。**【作者已核实，链接已修正】** | 高度相关 |
| NL–PL Traceability Link Recovery Needs More than Textual Similarity | Z. Zou, B. Wang, P. Liang, T. Bi, H. Jin | 2025-09 | arXiv:2509.05585 | 多策略（HGT 边类型+Gemini 2.5 Pro）比文本相似度更有效，12 项目 F1 较 HGNNLink +3.68%/8.84%。**【作者已核实】** | 高度相关 |
| **SpecMap: Hierarchical LLM Agent for Datasheet-to-Code Traceability** | 作者见 arXiv | 2026-01 | arXiv:2601.11688 | 分层 LLM 智能体，仓库级结构推断逐级缩小搜索空间做规格→代码追踪。 | 时效性 |
| Enhancing Requirements Traceability Link Recovery: T-SimCSE | Y. Wang, W. Wang, K. Hu, Q. Huang, L. Zhao | 2026-03 | arXiv:2603.11800 | SimCSE 无标注预训练 + specificity 重排，10 数据集 recall/MAP 领先。 | 时效性 |
| **ReqToCode: Embedding Requirements Traceability as a Structural Property of the Codebase** | T. Schlathölter | 2026-03 | arXiv:2603.13999 | 把可追踪性做成"编译期可验证的结构属性"（Traceable 元素），需求变更走降级生命周期（弃用警告→构建失败）。 | **重大意义（防漂移角度独特）** |

---

## 二、开源项目 / 数据集（Open-source Projects & Datasets）

| 名称 | 组织/作者 | 年份 | 链接 | 一句话核心贡献 | 时效/活跃度 |
|---|---|---|---|---|---|
| TraceLab | CoEST | 2012–2014 | github.com/coest/tracelab | 可追踪性研究实验工作台，组件化可复现实验。 | 经典（研究平台） |
| TraceBERT | Jinfeng Lin（Notre Dame） | 2021 | github.com/jinfenglin/TraceBERT | 基于 CodeBERT 的 NL→PL 追踪模型，对应 ICSE'21 T-BERT。 | 真实已核验 |
| ArDoCo / Core（ARCOTL） | ArDoCo | 近年 | github.com/ArDoCo/Core | 通过中间模型自动生成代码与架构模型（PCM/UML）之间的追踪链接。 | 活跃 |
| ArDoCo / SimpleTracelinkDiscovery | ArDoCo | 近年 | github.com/ArDoCo/SimpleTracelinkDiscovery | STD 方法，名称+n-gram 匹配非结构化文档与架构模型实体。 | 活跃 |
| **loom** | juuppe | 近年 | github.com/jsuppe/loom | `loom trace/chain/coverage` 实现 req↔spec↔impl↔test 双向追踪，`loom sync` 自动生成带追踪矩阵的 REQUIREMENTS.md/TEST_SPEC.md（living doc + RTM 自动生成）。**【归属已核实为 juuppe，注意与多个同名 loom 区分】** | 活跃且直接相关 |
| reqtrace | philipmiesbauer | 近年 | github.com/philipmiesbauer/reqtrace | GitOps 友好，YAML（.rqtr）定义需求+块注释标签映射源码，自动校验实现与测试覆盖。 | 相关 |
| shtracer | qq3g7bad | 2024 | github.com/qq3g7bad/shtracer | 配置驱动（config.md）的轻量追踪工具，生成 JSON/HTML/Markdown 输出，便于 CI/CD。**【URL 已核实】** | 相关 |
| ReqForge | Haider094 | 近年 | github.com/Haider094/ReqForge | 解析 NL 需求生成测试用例并建立 test↔requirement RTM，支持 OpenAI/Claude/本地模型。 | 相关 |
| OpenReq | OpenReqEU | 2017–2021 | github.com/OpenReqEU | 欧盟 H2020 项目，提供需求推荐/相似度/依赖检测等开源组件。 | 背景 |
| CoEST Datasets | CoEST | 2000s– | coest.org | 领域最常用基准数据集集合（CM1、eTour、SMOS、eANCI 等）。 | 数据基准 |
| RETRO.NET Dataset | Notre Dame | 2018 | arXiv:1807.11344 | 需求→代码追踪基准数据集（需求规格+C#/VB 源码+gold 答案）。 | 数据基准 |

---

## 三、审查说明与行动项

- **核验动作**：初版 2 篇"作者待核实"论文（REFSQ'25 RAG、arXiv:2509.05585）已确认作者并修正链接；loom 归属修正为 juuppe、shtracer URL 修正。均真实存在。
- **剔除/降权**：初版中"2024 回顾性论文（Recovering Traceability Links Retrospective）"作者信息模糊、价值边缘，已从主表移除（可作背景）。
- **待精读**：R2Code、ReqToCode、TraceLLM 三篇是本主题最贴近"Spec→Code 可追踪性 + 防漂移"的前沿，建议下一步精读全文。
- **补充方向**：GitHub Spec Kit 生态亦在本主题上下文有交叉（见 collection_3），可作为"规范为源"的工程参照。