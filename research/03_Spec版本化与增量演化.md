# 03 Spec 版本化与增量演化 — 审查版（2026-08-15）

> 主题：管理 Spec 变更历史、保证向后兼容性，尤其针对 R2/R3 级制品（形式化规格、API/契约规范、模型/元模型、特性模型等）。
> 审查标准：**近期性**（2026-05-15 之后近 3 个月内发表/更新）或 **重大意义**（奠基性、高影响、领域必读）。已剔除停更、弱相关、来源不可靠的条目。
> 分级标记：`[近3月]`=近三个月内；`[重大]`=奠基/高影响；`[2026]`=2026 年但早于近三月窗口；`[参考]`=背景资料；`[剔除]`=已移除。

## 一、论文（Papers）

### A. API / 契约版本化与向后兼容（OpenAPI / AsyncAPI / SemVer）

1. **[重大] How Many Web APIs Evolve Following Semantic Versioning?**
   - 作者：Souhaila Serbout, Cesare Pautasso（USI Lugano）
   - 年份/会议：2024, ICWE
   - URL：http://pautasso.org/biblio-pdf/apiace-icwe2024.pdf
   - 简介：对 3,075 个 Web API 的演化历史做实证分析，评估其版本号是否真正遵循 SemVer 规则（最坏情形仅 25% 合规）。**"SemVer 在现实中大多不被遵守"是本子问题的关键实证。**

2. **[重大] A First Look at the Deprecation of RESTful APIs: An Empirical Study**
   - 作者：Jerin Yasmin, Yuan Tian, Jinqiu Yang
   - 年份：2020（arXiv:2008.12808）
   - URL：https://arxiv.org/abs/2008.12808
   - 简介：提出 RADA 框架，从 OpenAPI 规格自动识别 deprecated 元素，实证研究 REST API 的 deprecated-removed 协议执行情况。**deprecation 机制研究的代表性工作。**

3. **[参考] To deprecate or to simply drop operations? An empirical study on the evolution of a large OpenAPI collection**
   - 作者：Serbout & Pautasso 团队
   - 年份/会议：2022, ECSA
   - URL：http://pautasso.org/biblio-pdf/apiace-ecsa2022-deprecate.pdf
   - 简介：基于百万级 OpenAPI/Swagger 操作，研究 API 演化中 operation 删除造成的 breaking changes 及 deprecation 的使用程度。

4. **[参考] How Composable is the Web? An Empirical Study on OpenAPI Data model Compatibility**
   - 年份：2022, IEEE
   - URL：https://xplorestaging.ieee.org/document/9885779
   - 简介：对 20,587 个公开 Web API 的 schema 兼容性做实证研究，定义三级数据模型元素兼容性。

5. **[参考] A Formal Study on Backward Compatible Dynamic Software Updates**
   - 年份：2015（arXiv:1503.07235）
   - URL：https://arxiv.org/pdf/1503.07235v1
   - 简介：形式化研究动态软件更新的向后兼容性，用"混合执行满足规格 Σ"刻画兼容条件。

### B. 形式化规格演化与细化（TLA+ / Event-B / B 方法）

6. **[重大] Specification and Verification With the TLA+ Trifecta: TLC, Apalache, and TLAPS**
   - 年份：2022（arXiv:2211.07216）
   - URL：https://arxiv.org/pdf/2211.07216v1
   - 简介：TLA+ 三件套（TLC/Apalache/TLAPS）综述，强调 TLA+ 中 refinement 即蕴含（Spec ⇒ TD!Spec），可直接用于规格演化验证。**refinement 作为规格演化验证机制的核心论述。**

7. **[重大] Leveraging TLA+ Specifications to Improve the Reliability of the ZooKeeper Coordination Service**
   - 年份：2023（arXiv:2302.02703）
   - URL：https://arxiv.org/pdf/2302.02703v1.pdf
   - 简介：用 TLA+ 分层规格（系统规格→测试规格）支撑 ZooKeeper 开发，展示规格作为 "super-doc" 的演化与复用。**规格在真实系统（ZooKeeper）中演化的工业案例。**

8. **[参考] Consistency-preserving refactoring of refinement structures in Event-B models**
   - 年份/会议：2019, Formal Aspects of Computing（DOI 10.1007/s00165-019-00478-z）
   - URL：https://dl.acm.org/doi/pdf/10.1007/s00165-019-00478-z
   - 简介：提出保持一致性的事件 B 细化结构重构方法，提升既有模型的维护性与可复用性。

### C. 模型 / 元模型版本化与共演化（MDE）

9. **[重大] Approaches to Co-Evolution of Metamodels and Models: A Survey**
   - 作者：Regina Hebig, Djamel Eddine Khelladi, Reda Bendraou
   - 年份/会议：2017, IEEE Transactions on Software Engineering 43(5):396-414
   - URL：https://xplorestaging.ieee.org/document/7569018
   - 简介：综述 31 种元模型-模型共演化方法，给出解决方案技术分类学与决策支持。**MDE 共演化方向的权威综述。**

10. **[参考] COPE: Coupled Evolution of Metamodels and Models for the Eclipse Modeling Framework**
    - 作者：Herrmannsdörfer 等
    - 年份/会议：2008, Eclipse Symposium
    - URL：https://wwwbroy.in.tum.de/publ/papers/2008_eclipsesymposium_cope.pdf
    - 简介：提出 COPE 语言，用可复用的耦合演化操作描述元模型与模型的同步演化。

11. **[2024] "Don't Touch my Model!" Towards Managing Model History and Versions during Metamodel Evolution**
    - 年份/会议：2024, ICSE NIER
    - URL：https://www.computer.org/csdl/proceedings-article/icse-nier/2024/050000a077/21r85Opmd7W
    - 简介：记录元模型历史版本并维护各版本模型，支持模型在不同时间点按需共演化。

### D. 特性模型 / 产品线演化（Feature Model / SPL）

12. **[参考] Multi-Version Decision Propagation for Configuring Feature Models in Space and Time**
    - 年份/会议：2024, ACM（SPLC，DOI 10.1145/3646548.3676550）
    - URL：https://dl.acm.org/doi/fullHtml/10.1145/3646548.3676550
    - 简介：提出多版本决策传播，支持跨多个特性模型版本同时进行配置。

13. **[2025] Modular Soundness Checking of Feature Model Evolution Plans**
    - 年份/会议：2025, Theoretical Computer Science（期刊）
    - URL：https://violet.foldr.org/publication/fmep-tcs25/
    - 简介：对特性模型演化计划（FMEP）做模块化健全性检查，验证各时间点模型计算的正确性。

### E. 语言 / 规范版本化标准与草案（W3C / IETF / FHIR / OpenAPI / AsyncAPI）— 更新至 2026 状态

14. **[重大] OpenAPI Specification 版本化（3.2.0 稳定 / 3.3.0 开发中 / 4.0 未落地）**
    - 状态：OpenAPI 3.2.0 为当前稳定版（2025-09 发布）；实际开发重心在 3.3.0（v3.3-dev 分支，2026-06/07 仍有 PR）；**OpenAPI 4.0（Moonwalk）截至 2026 尚不存在，仍处设计阶段**。
    - URL：https://swagger.org.cn/specification/v3/ ；Moonwalk SIG：https://github.com/OAI/sig-moonwalk/
    - 简介：OAS 采用 SemVer 2.0.0 版本化，major.minor 指定功能集。**规划 Spec 版本化时需注意：主流 API 规范仍在 3.x 轨道演进，4.0 短期不会落地。**

15. **[重大] AsyncAPI 版本与迁移（3.1.0 于 2026-01-31 发布）**
    - URL：https://github.com/asyncapi/spec/releases ；发布说明：https://www.asyncapi.com/blog/release-notes-3.1.0
    - 简介：v3 之后首个新版本，minor 发布、无破坏性变更，标志 AsyncAPI 走出 v3 后的长期停滞期；v3 将 operations/channels/messages 解耦是最大 breaking change。**事件驱动契约版本化的活跃参考。**

16. **[重大] YANG Module Versioning**（IETF draft-ietf-netmod-yang-module-versioning-15）
    - URL：https://www.ietf.org/archive/id/draft-ietf-netmod-yang-module-versioning-15.txt
    - 简介：允许 YANG 模块非线性多版本演化，用 revision date 唯一标识版本。

17. **[重大] YANG Semver**（IETF draft-ietf-netmod-yang-semver-27）
    - URL：https://www.ietf.org/archive/id/draft-ietf-netmod-yang-semver-27.txt
    - 简介：为 YANG 制品引入 SemVer 风格版本号，标注向后兼容(BC)/不兼容(NBC)变更。**"版本号编码兼容性语义"的成熟标准做法。**

18. **[重大] FHIR Versions**（HL7 FHIR）
    - URL：https://build.fhir.org/versions
    - 简介：定义 FHIR 制品达到 Normative 状态后的前后向兼容规则，保证跨版本数据交换安全。**医疗领域规格版本化的严格兼容治理案例。**

19. **[参考] Extending and Versioning Languages Part 1**（W3C TAG 编辑草案）
    - URL：https://www.w3.org/2001/tag/doc/versioning.html
    - 简介：定义语言可扩展性、向后/向前兼容性的语义，为语言规范版本化提供概念框架。

### F. 新增（2026 年）— LLM 与 API/契约演化的交叉

20. **[2026] When LLMs Lag Behind: Knowledge Conflicts from Evolving APIs in Code Generation**
    - 年份：2026（arXiv:2604.09515）
    - URL：https://arxiv.org/pdf/2604.09515v1
    - 简介：系统实证研究 LLM 在 API 演化（弃用/修改/新增）下的代码生成，"上下文-记忆冲突"问题。**与 API 契约演化直接相关：LLM 训练数据中的旧契约会与最新规格冲突。**

21. **[2026] KCoEvo: A Knowledge Graph Augmented Framework for Evolutionary Code Generation**
    - 年份：2026（arXiv:2603.07581）
    - URL：https://arxiv.org/pdf/2603.07581v1
    - 简介：构建 API 演化知识图谱辅助 LLM 生成跨版本一致代码，处理版本化约束。

22. **[参考] APIMig: A Project-Level Cross-Multi-Version API Migration Framework Based on Evolution Knowledge Graph**
    - 年份：2025（IJCAI 2025）
    - URL：https://ijcai-preprints.s3.us-west-1.amazonaws.com/2025/4624.pdf
    - 简介：基于演化知识图谱的跨多版本 API 迁移框架，提取 add/remove/update 演化实体。

23. **[近3月] When Retrieval Hurts Code Completion: A Diagnostic Study of Stale Repository Context**
    - 年份：2026（arXiv:2605.14478）
    - URL：https://arxiv.org/html/2605.14478v1
    - 简介：检索到的过期仓库上下文对代码生成的负面影响，与"陈旧规范/契约"主题相关。

## 二、开源项目（活跃度核实至 2026-08-15）

### 活跃 / 高价值

1. **oasdiff** — 高度活跃（v1.24.0 于 2026-07-21 发布；2026-02 起支持 OpenAPI 3.1）
   - URL：https://github.com/oasdiff/oasdiff/
   - 简介：Go 编写的 OpenAPI diff 与 breaking change 检测 CLI（覆盖 509 种变更），支持本地、CI 与 PR review。
   - 相关性：高。**当前 OpenAPI 破坏性变更检测的事实标准工具。**

2. **Azure/openapi-diff (oad)** — 活跃（2026-02 仍有 PR；被 azure-rest-api-specs 内部调用）
   - URL：https://github.com/Azure/openapi-diff/
   - 简介：npm 包，Azure REST API Specs 的 "Breaking change detector"，每个 PR 强制执行。
   - 相关性：高。

3. **Pact（Pact 家族）** — 高度活跃（pact-js-core v20.1.0 于 2026-08-05 发布）
   - URL：https://github.com/pact-foundation/pact-net
   - 简介：消费者驱动契约测试，Pact Broker 用 consumer version selectors 管理契约版本匹配。
   - 相关性：高。**契约测试生态的事实标准。**

4. **AsyncAPI（规范+生态）** — 活跃（3.1.0 于 2026-01-31 发布；社区月度更新持续）
   - URL：https://www.asyncapi.com/docs/migration/migrating-to-v3
   - 简介：事件驱动 API 规范，含版本迁移与变更治理。
   - 相关性：高。

5. **OpenAPI Specification** — 活跃（3.3.0-dev 分支 2026-06/07 有 PR/issue）
   - URL：https://swagger.org.cn/specification/v3/
   - 简介：OAS 3.2.0 稳定，3.3.0 开发中，4.0（Moonwalk）设计阶段。
   - 相关性：高。

6. **api-changelog（lxgicstudios）** — 新增（近期项目）
   - URL：https://github.com/lxgicstudios/api-changelog
   - 简介：对比两个 OpenAPI/Swagger 文件生成人类可读 changelog，零外部依赖，检测新增/删除端点、必填字段、弃用等。
   - 相关性：中高。

### 停更 / 已剔除

7. **[剔除] Optic** — 已归档死亡（仓库于 2026-01-12 归档只读，useoptic.com 域名失效；最后发布 v1.0.9 于 2025-08-11）
   - URL：https://github.com/opticdev/optic/
   - 说明：曾是 OpenAPI 生态重要工具，2026 年 1 月归档，社区已迁移至 oasdiff/APInotes 等替代。**本子方向近期最大变动。**

8. **[剔除] elibracha/openapi-diff** — 停更（最后发布 v2.3.2，2020-04-19，已 6 年无更新）
   - URL：https://github.com/elibracha/openapi-diff
   - 说明：已移除。

9. **[剔除] api-specs-comparator（egoettelmann）** — 停更（最后版本 0.2.0，2020-02-14）
   - URL：https://github.com/egoettelmann/api-specs-comparator
   - 说明：已移除。

10. **[剔除] Weopt/open-api-diff** — 低价值重复工具，已移除。

## 三、审查结论

- **核心机制**：TLA+ refinement（Spec ⇒ TD!Spec）+ SemVer/YANG SemVer（版本号编码兼容性）+ deprecation 协议（RADA），构成"规格演化+向后兼容"的三大机制支柱。
- **2026 新动向**：① OpenAPI 4.0 短期不会落地，实际演进在 3.2.0→3.3.0 轨道；② Optic 归档是本方向近期最大变动，oasdiff 成为事实标准；③ 研究热点从"规范 diff 工具"转向"LLM 与 API 演化知识的冲突/同步"（arXiv 2604.09515、2603.07581）。
- **工具生态**：oasdiff + Azure/openapi-diff + Pact 是当前活跃组合；Optic/elibracha/api-specs-comparator 已停更。
