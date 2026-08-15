# 建议文档（子问题三）：Spec 版本化与增量演化

> 面向总问题：设计一种既能被人类精确表达意图、又能被机器可执行验证的 Spec 形式化语言。本文聚焦 R2/R3 级制品的变更历史管理与向后兼容保证。

## 一、核心结论（基于证据）

1. **向后兼容不能靠自律，必须机器化验证**。对 3,075 个 Web API 的实证显示 SemVer 合规率最坏仅 25%（Serbout & Pautasso, ICWE 2024），版本号语义与实际破坏性变更严重脱节。兼容性必须由可执行检查保证。
2. **"refinement 即蕴含"是兼容性验证的形式化内核**。TLA+ Trifecta（arXiv:2211.07216，A 档）确立：新版本规格蕴含旧规格（Spec ⇒ TD!Spec）时，向后兼容成为可经 TLC/Apalache/TLAPS 机器验证的定理，把兼容问题从约定问题转化为证明问题。
3. **版本号可编码兼容性语义**。YANG Semver（draft-27，A 档）用 BC/NBC 标注使版本号携带机器可读的兼容信息；oasdiff v1.27.0（2026-07-30 核实）进一步新增 versioning policy 检查（`api-version-not-bumped` 等），自动报告"发生了破坏性变更但版本号未升 major"，实现了版本号与变更严重度的一致性闭环。
4. **R3 级（元模型）演化需共演化机制而非线性迁移**。共演化综述（Hebig 等, TSE 2017，A 档）给出 31 种方法的分类学与决策支持；"Don't Touch my Model!"（ICSE NIER 2024）主张多版本并存、按需迁移，优于强制一次性升级。
5. **生态现状**：OpenAPI 3.2.0 稳定、3.3.0 开发中，4.0（Moonwalk）截至 2026-08 仍停留在 ADR/讨论阶段（无正式规范、无发布，已核实），其"机械升级（3.x→4.0 自动迁移）"原则值得借鉴；Optic 已于 2026-01 归档，oasdiff 成为破坏性变更检测的事实标准。

## 二、对 Spec 语言设计的具体建议

**版本模型**
- 建议 1：采用 SemVer 风格版本号 + 语言级 BC/NBC 兼容性标注，并在工具中强制"版本号与变更严重度一致"检查。依据：YANG Semver（draft-27）、oasdiff v1.27.0 versioning policy、OpenAPI 3.x 的 SemVer 2.0.0 实践。
- 建议 2：对 R3 制品支持非线性多版本并存，以 revision 标识（时间戳/内容哈希）版本，消费方按版本选择匹配。依据：YANG Module Versioning（draft-15）、"Don't Touch my Model!"、Pact consumer version selectors。
- 建议 3：按制品等级/成熟度分级施加兼容义务——等级越高（R3 元模型）义务越严。依据：FHIR Versions 的 Normative 分级治理，与我们的 R2/R3 分级天然呼应。

**兼容性验证机制**
- 建议 4：双层验证。语义层用 refinement-as-implication（新 Spec ⇒ 旧 Spec）经模型检查/证明器判定；结构层用变更分类规则（新增/删除/收紧/放宽）做快速机器判定，两层结论合并产出 BC/NBC 判定。依据：TLA+ Trifecta（A）、oasdiff 的 509 类变更分类（A）。
- 建议 5：把 deprecation 建模为语言一等概念，"deprecated → removed"需经状态机并预留至少一个 minor 版本的缓冲期。依据：RADA（arXiv:2008.12808）及弃用协议实证。

**演化工作流**
- 建议 6：将破坏性变更检测嵌入 PR/CI 强制门禁，未过检不得合并；同时自动生成人类可读 changelog，兼顾"机器可验证 + 人类可读"。依据：Azure/openapi-diff 在 azure-rest-api-specs 的逐 PR 强制实践（A）、api-changelog。
- 建议 7：R3 制品每次变更须附带共演化策略（迁移操作/变换规则），并将变更历史组织为可查询的演化图谱（add/remove/update 实体与版本间关系），供下游 R2 制品增量迁移。依据：共演化综述（A）、COPE 的可复用演化操作思想、KCoEvo 演化知识图谱。
- 建议 8：规格作为"super-doc"随系统持续演化并分层（系统规格 → 测试/消费规格），保持长期可维护性。依据：ZooKeeper TLA+ 工业案例（arXiv:2302.02703）。

## 三、工具采用建议

- **采用**：oasdiff（事实标准、高度活跃，v1.27.0 于 2026-07-30 发布，兼具 diff/破坏性判定/版本策略检查，可作兼容性检查器原型基础）；Azure/openapi-diff 的 CI 门禁模式；Pact 的消费方版本匹配机制作设计参考。
- **关注不依赖**：OpenAPI 4.0/Moonwalk——尚无正式规范，不应以其为设计基线，按 3.x 轨道对齐，仅吸收其"机械升级"原则。
- **不采用**：Optic（2026-01 归档只读）、elibracha/openapi-diff（6 年未更新）、api-specs-comparator（停更）——均已死亡，作为依赖有断供风险。api-changelog 可借鉴思路但成熟度有限，不宜直接依赖。

## 四、风险与开放问题

1. **refinement 蕴含判定的可扩展性**：时序逻辑蕴含在复杂规格下可能不可判定，需有界模型检查或证明辅助，验证成本与自动化程度如何平衡是开放问题。
2. **语法兼容 ≠ 语义兼容**：结构 diff 只能覆盖句法层，行为层兼容需另靠模型检查；两层结论冲突时的裁决规则待定义。
3. **豁免机制**：现实演化中"确需破坏性变更"不可避免，需设计显式豁免/降级流程（如 oasdiff 的 severity-levels），否则门禁会被绕过，重蹈 SemVer 失守覆辙。
4. **LLM 交互风险**：LLM 训练语料含过期契约，参与 Spec 生成/迁移时会产生跨版本知识冲突（arXiv:2604.09515），必须以最新版 Spec 为强制上下文约束。
5. **多版本并存的维护成本**：保留全部历史版本的兼容义务可能无限累积，需定义各版本的支持窗口与退役（EOL）策略。
