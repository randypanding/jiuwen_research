# 标准落点调研：FOCUS（R5.1）+ OpenTelemetry GenAI（R5.2）

> **调研日期**：2026-08-18
> **方法**：先 WebSearch 官方来源，再 WebFetch 抓原文核验。来源标注为 `官方`（org/官档）或`一手仓库`（GitHub issue/PR）。未抓到或无法核验的记为「待核验」。口径标注：`置信度 A/C/O`（O=官方原文直接佐证，C=多来源交叉一致，A=单方/二手来源）、`半衰期 短/中/长`。
> **范围**：为“AI 消费/用量/订阅权益（entitlement 窗口、重置、节流）”寻找可落地的官方标准锚点。

---

## R5.1 FOCUS（FinOps Open Cost & Usage Specification）

### 5.1.1 当前版本与发布时间线

| 版本 | 关键事实 | 出处 |
|---|---|---|
| **v1.4（当前最新）** | FOCUS Steering Committee 于 **2026-06-04** 正式 ratify（批准发布）；PDF 出版物显示 `publication version 1.4`；新增 2 数据集、47 列、6 属性、17 术语、2 支持特性 | 官方 focus.finops.org PDF；官方 finops.org/insights/introducing-focus-1-4 |
| **v1.3** | 2025-12-05 ratify（2025-12-11 官方新闻稿发布）；首个引入 Contract Commitment 数据集 | 官方 linuxfoundation.org 新闻稿；官方 focus.finops.org v1-3 |
| **v1.2** | 引入 `CommitmentDiscountCategory` 等承诺折扣列 | 官方 learn.microsoft（FOCUS 1.2 conformance 提及 CDC），交叉佐证 |
| 发布节奏 | 约**每半年一个版本**（v1.3≈2025-12，v1.4≈2026-06），进入 `v1.5` 开发里程碑 | 官方 ins/focus-1-4；GitHub milestone `v1.5` |

> 关键引句（官方 ins/focus-1-4，抓取 2026-08-18）：“Together … 1.4 lays the groundwork for **FOCUS 1.5**, which will bring **unit and token economics** into view by introducing the **Price Sheet** and tracking **inference value** at the AI frontier.” —— 即 v1.5 官方已公开承诺面向“token/推理价值”的扩展。

### 5.1.2 Contract Commitment 语义核验

- **结论：已含「Contract Commitment」语义**。v1.3 首次新增独立的 **Contract Commitment 数据集**，与 Cost and Usage 数据集解耦可独立授权；v1.4 将其从 **13 列扩充到 30 列**（含支付模型、生命周期状态、折扣逻辑、eligibility）。
- Cost and Usage 数据集内用 JSON 对象列 **`ContractApplied`** 把每条 charge 关联到一个或多个 contract commitment（内部元素：`ContractId`、`ContractCommitmentId`、`ContractCommitmentAppliedCost/Quantity`）。
- **CommitmentDiscount 系列列**（v1.2 起，用于折扣侧）：`CommitmentDiscountId`、`CommitmentDiscountName`、`CommitmentDiscountType`、`CommitmentDiscountQuantity`、`CommitmentDiscountUnit`、`CommitmentDiscountStatus`、`CommitmentDiscountCategory`（按 Usage / 按 Cost 分类）。*注意 CommitmentDiscount 与 ContractCommitment 是两套并列概念，前者描述“折扣”，后者描述“合约条款/承诺量”。*

**Contract Commitment 数据集列清单（v1.4，官方一手 raw 抓取，共 30 列，未逐条核验定义）**：
`BillingCurrency, ContractCommitmentApplicability(JSON), ContractCommitmentBenefitCategory, ContractCommitmentCategory, ContractCommitmentCost, ContractCommitmentCreated, ContractCommitmentDescription, ContractCommitmentDiscountPercentage, ContractCommitmentDurationType, ContractCommitmentFulfillmentInterval, ContractCommitmentId, ContractCommitmentLastUpdated, ContractCommitmentLifecycleStatus, ContractCommitmentModel, ContractCommitmentOfferCategory, ContractCommitmentPaymentInterval, ContractCommitmentPaymentModel, ContractCommitmentPaymentUpfrontPercentage, ContractCommitmentPeriodStart, ContractCommitmentPeriodEnd, ContractCommitmentQuantity, ContractCommitmentType, ContractCommitmentUnit, ContractId, ContractPeriodStart, ContractPeriodEnd, InvoiceIssuerName, PricingCurrency, PricingCurrencyContractCommitmentCost, ServiceProviderName`
（来源：`github.com/FinOps-Open-Cost-and-Usage-Spec/FOCUS_Spec/blob/working_draft/specification/datasets/contract_commitment/columns/columns.mdpp`）

> 与本项目“订阅权益窗口”最相关的既有字段：`ContractCommitmentPeriodStart/End`（窗口）、`ContractCommitmentQuantity` + `ContractCommitmentUnit`（额度量/单位）、`ContractCommitmentBenefitCategory`/`OfferCategory`（权益类型）、`ContractCommitmentLifecycleStatus`（生命周期）。**没有**“重置周期/reset、节流/throttle、速率/rate limit”的语义字段。

### 5.1.3 “订阅权益窗口 / 重置 / 节流”能否表达

- **可以表达窗口与额度**：用 Contract Commitment 数据集（PeriodStart/End + Quantity/Unit）承载“权益窗口+剩余额度”，贴近既有 FOCUS 语义。
- **不能原生表达“重置(reset)/节流(throttle)/速率(rate)”**：FOCUS 目前是“账单事实（billed/technical facts）”标准，粒度是 charge/contract 层，不覆盖配额重置周期、限速策略。这些属于新概念 = **需要新 schema 或在新数据集/新列中扩展**，而非现有 Profile 可套。
- **FOCUS 没有独立的“Profile/扩展规格”机制**：扩展载体只有两条路——
  1. **非规范私有列**：数据生成方可用 `x_` 前缀的自定义列承载（官方 `x_` 表示 external / non-FOCUS 列，见 microsoft finops-toolkit 数据字典）；
  2. **正式入规**：以 GitHub Feature Request（issue type：Standardization / Enhancement / Net New / Enablement）→ 排入里程碑 → 随版本发布。没有类似 CloudEvents “documented extension” 或 OTel “profile” 的独立扩展命名空间。

### 5.1.4 扩展 / 提案流程、WG 节奏、门槛与成本

来源：官方 focus.finops.org about-focus / faqs / working-group-faq；一手 `foundation/operating_procedures.md`。

- **提案流程（正式 Contributor 路径）**：组织签 **CLA（FOCUS Series Membership Agreement）** 成为 Contributing Member → 在 FOCUS_Spec 仓库提 issue / PR → 进 FOCUS WG / Task Force → Steering Committee 审批 ratify。**无需成为 FinOps Foundation 会员，贡献 FOCUS 无成本**（官方 FAQ 明示：“there is no cost to contribute to FOCUS”）。
- **治理**：JDF（Linux Foundation 系）项目；Steering Committee 任命自上属 Governing Board；Working Group（FG）处理 Work Package；用 **Task Force**（如 TF-2）推进具体行动项（可见于 #2405 的 `Task Force: TF-2` 标注）。
- **节奏**：规范约半年一版；FOCUS Working Group 以 sprint 制运行（官方 WG FAQ 描述 6-8 周 sprint，具体开会频率、周例会安排未在抓取页面量化 → **待核验**）。
- **成本**：贡献 FOCUS=0 成本（签 CLA 即可）。若要申请 **FOCUS Conformant 认证**（v1.3 认证已开放；Validator 对 1.4 的支持预计 2026 Q3 后）则要求组织为 FinOps Foundation + Linux Foundation 会员，需采购成本 → 非“提标准”所必需。

### 5.1.5 是否已有类似“权益/额度”提案（finops-hub / FOCUS_Spec issues）

- **是，已在 AI/token 方向积压**（一手 GitHub 核验）：
  - **#2018** `[FR] Surface AI model identity and token consumption in FOCUS` —— 父级主题。
  - **#2405** `[AI] Enumerate all possible AI data elements for FOCUS roadmap`（milestone `v1.5`，`Task Force: TF-2`）——内含提案 **“AI Inference Workload Alignment for FOCUS 1.5”**，核心哲学为 **“No AI Exceptionalism”**：token 计数、缓存折扣尽量复用既有 `ConsumedQuantity/PricingQuantity/ContractedUnitPrice` 数学列，而非新增大量 schema。
- **外部重要动向**：Linux Foundation 于 **2026-06-03 宣布筹建 “Tokenomics Foundation”**（`tokeneconomics.com`），目标是“为 AI 成本管理建立开放标准”，与本课题高相关（官方 PRNewswire + finops.org ins/token-economics）。
- **finops-hub**：该仓库为 adoption/工具生态目录，未抓到含“权益/额度/entitlement”专项提案的上游讨论 → **待核验**（finops-hub 更多是落地工具/转换器聚合，标准提案集中在 FOCUS_Spec issues）。

> 官方 ins/focus-1-4 引句（抓取 2026-08-18）：“This is the first FOCUS release that lets FinOps teams interface with AP … Together … groundwork for FOCUS 1.5 … unit and token economics.”

### 5.1.6 FOCUS for AI 进展

- 官方页面 **FOCUS for AI**（focus.finops.org/technology-categories/focus-for-ai/）已上线：给出映射示意 —— `1,000,000 input tokens → ConsumedQuantity+ConsumedUnit`；`model & price → SkuId/SkuPriceId/PublisherName`；`AI 服务 → ServiceCategory: AI and ML`；`学分/token 计费 → PricingCurrency→BilledCost`；`预留吞吐 → CommitmentDiscount 列`。
- 采用者示例：Nebius（AI 服务商）已提供 FOCUS 格式用量数据。
- **最快官方落点 = FOCUS v1.5**：官方在 v1.4 发布稿里明确 1.5 引入 **Price Sheet** 并“tracking inference value at the AI frontier”。按 v1.3→v1.4 约半年节奏，v1.5 大概率落在 **≈2026 Q4–2027 Q1**（基于已发布版本的半周期外推，非官方承诺 → 置信度 C、半衰期中）。

### 5.1.7 FOCUS 小结表

| 维度 | 结论 |
|---|---|
| 当前版本 | v1.4（2026-06-04 ratify） |
| 承诺语义 | ✅ v1.3 引入 Contract Commitment 数据集；v1.4 扩到 30 列；CommitmentDiscount 系列列自 v1.2 |
| 权益窗口/额度 | ✅ 可用 ContractCommitmentPeriodStart/End + Quantity/Unit + BenefitCategory |
| 重置/节流/速率 | ❌ 无字段，需新 schema/新列 |
| Profile/扩展机制 | ❌ 无；只有 `x_` 私有列 + FR→里程碑 两条路 |
| 提案入口 | 签 CLA（0 成本）→ GitHub FR/PR → WG/Task Force(TF-2) → SC ratify |
| 最快落点 | v1.5（≈2026 Q4–2027 Q1，含 Price Sheet + token/inference 价值）|
| 相关在途提案 | #2018/#2405（“No AI Exceptionalism”）；Tokenomics Foundation（2026-06 筹建）|

---

## R5.2 OpenTelemetry（OTel）GenAI 语义约定

### 5.2.1 状态核验：是否迁独立仓库 / 是否 Stable / 当前版本

- **已迁独立仓库**：2026-05-05 起，主仓 `semantic-conventions` 通过 **PR #3696** 将 GenAI 语义迁移到 **`open-telemetry/semantic-conventions-genai`**（该 repo 自身 README、以及主仓 “Moved” 页 + opentelemetry-js #6783、semantic-conventions release note 交叉确认）。“下一个 semconv release 将不再包含 GenAI 语义约定”（一手 source：追踪 issue #233 + release note）。
- **仍是 Development（非 stable）**：所有 `gen_ai.*` 文档标注 `Status: Development`（原 experimental）；近五次小版本中 v1.37/v1.40/v1.41 出现**破坏性属性改名**（`gen_ai.system`→`gen_ai.provider.name`、`prompt_tokens`→`input_tokens`、`completion_tokens`→`output_tokens`、删 `gen_ai.prompt/completion` 改 `gen_ai.input/output.messages`）。
- **主仓（core semconv）当前版本**：**v1.44.0**（官方 releases，2026-08-04 发布；opentelemetry.io docs 侧边栏 “Semantic conventions 1.44.0”）。主仓内最后 GenAI 实质新增在 v1.41.0。
- **GenAI 独立仓版本化**：独立仓允许“不同版本化方案 + 更快迭代”（why 迁移），但 **README 中 Schema URL 仍是 `TODO`**（未正式给出 schema URL）；各语言 SDK 将按 **独立包 + 独立版本号** 暴露 GenAI 常量（推荐 `@opentelemetry/semantic-conventions-genai` 独立包，见 opentelemetry-js #6783 共识），截至抓取**独立包尚未正式发布（release expected soon）** → 因此“声明遵循哪个 semconv 版本”尚无规范 schemaUrl 可钉。
  - 现状最佳做法：钉 **core semconv v1.44.0 + semantic-conventions-genai 仓库 `main` 快照（2026-08-11 最近提交）**，并在数据中记录该版本。

### 5.2.2 gen_ai.* 相关属性现状（官方 registry / 一手 docs）

Span 层（gen-ai-spans / openai.md 一手核验）：
- `gen_ai.operation.name`（Required，如 `chat`/`embeddings`/`execute_tool`/`invoke_agent`/`invoke_workflow`/`retrieval`/`create_agent`）
- `gen_ai.request.model`（Required / Conditionally）
- `gen_ai.provider.name`（Required，取代并 deprecate `gen_ai.system`，v1.37 起）
- `gen_ai.response.model`、`gen_ai.response.id`、`gen_ai.response.finish_reasons`
- `gen_ai.conversation.id`、`gen_ai.output.type`、`gen_ai.prompt.name`
- **用量**：`gen_ai.usage.input_tokens`、`gen_ai.usage.output_tokens`（v1.41 主编入的拆分族：`gen_ai.usage.cache_read/cache_write.input_tokens`、`gen_ai.usage.reasoning.output_tokens`、`gen_ai.usage.{text,image,audio,video}.{input,output}_tokens`；另在建 voice-agent PR #390 增加 `gen_ai.usage.input_audio_tokens/output_audio_tokens`）

Metric 层（一手）：
- `gen_ai.client.token.usage`、`gen_ai.client.operation.duration`；在建 PR #197（modality/cache/phase 拆分）与 PR #390（voice）会重构/新增。

> 结论：**`gen_ai.*` 目前没有任何 `quota`/`rate`/`limit`/`entitlement` 属性**——用量只有 `input/output/cache/reasoning/modality tokens` 计数。与腾讯课题最接近但**不等于**权益/额度的是流控相关在途提案（见下）。

### 5.2.3 是否有 quota/rate/limit/entitlement？（大概率没有 → 已核验）

- **确认为“没有”**：遍历官方 registry + 一手 openai.md span/metric 表（至 2026-08-11 快照），`gen_ai.*` 命名空间内无 quota/rate/limit/entitlement 属性。
- **最接近的在途工作（issue #101，一手，Open）**：“Propose a complete, stable gen_ai client metric set”，其中明确列出缺口与新增项：
  - `gen_ai.usage.cost`（Counter, `usd`，New）
  - `gen_ai.client.error_rate`、`gen_ai.client.retry_count`
  - **`gen_ai.client.rate_limit.events`（Counter, `{event}`，New）** —— 目前唯一与“限流信号”相关的官方级动议，但它描述的是“客户端收到的 429/限流事件计数”，**不是订阅权益/配额/剩余额度语义**。
- **评估是否值得提案**：值得。独立仓强调“更快迭代 + 接受新动议”，且已存在 rate_limit metric 的讨论基础；但这类业务（entitlement/quota 窗口、额度、重置）更多是 **计量/账单层** 概念，OTel 定位为“运行时可观测性线协议”，把要素建模成 span attribute 或独立 metric 均可。可先行在本仓 issue 以 `gen_ai.entitlement.*` / `gen_ai.quota.*`（例如 `gen_ai.entitlement.id`, `gen_ai.entitlement.remaining_units`, `gen_ai.entitlement.reset_period`）提出，作为对 #101 的补充。

### 5.2.4 如何声明“遵循哪个 semconv 版本”

来源：官方 opentelemetry.io/docs/specs/semconv/configuration/version-selection/（Development）。

- **声明式版本选择（推荐）**：配置键 `.instrumentation/development.general.<domain>.semconv`（`<domain>`= `gen_ai` 等），属性 `version`（int，目标版本，如 `1`）、`experimental`（bool，是否纳入 development 约定）、`dual_emit`（bool，是否同时发旧主版本做双发迁移）。
- **环境变量**：`OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`（逗号可分 `http/dup,gen_ai_latest_experimental`）；未设置时 SDK 默认继续发 v1.36 之前的“冻结旧形”。
- **多版本输出建议**：可用 `dual_emit=true` 双发新旧版本（target + previous），消费方按需取；核心版本锚点建议落后于上游稳定若干步、记录 `schemaUrl`（待 GenAI 仓发布后补其独立 schemaUrl），当前用“core v1.44.0 + genai 仓版本/commit 哈希”钉版本。

### 5.2.5 OTel GenAI 小结表

| 维度 | 结论 |
|---|---|
| 独立仓库 | ✅ `open-telemetry/semantic-conventions-genai`（2026-05-05 分家，主仓不再包含）|
| Stabiity | ❌ 仍 Development/experimental；近半年多次破坏性改名 |
| 主仓版本 | v1.44.0（2026-08-04）；GenAI 实质新增停在 v1.41.0 |
| gen_ai.* 用量 | `usage.input/output_tokens`（+cache/reasoning/modality/audio 族）|
| quota/rate/limit/entitlement | ❌ 无；仅 #101 提案 `gen_ai.client.rate_limit.events` 指标最接近 |
| 版本声明 | declarative `.instrumentation/...gen_ai.semconv.version` + `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`；Schema URL 仍 TODO |
| 独立包 | 各语言 SDK 视做独立包/独立版本（JS 提案 `@opentelemetry/semantic-conventions-genai`），未发布 |

---

## 结论区

### A) 字段级映射表（“AI 消费/订阅权益” → FOCUS）

| 语义 | FOCUS 落点 | 现成程度 | 备注 |
|---|---|---|---|
| 权益窗口起止 | `ContractCommitmentPeriodStart/End`、`ContractPeriodStart/End` | 现成 | 用于订阅/承诺窗口 |
| 权益额度/数 | `ContractCommitmentQuantity`+`ContractCommitmentUnit` | 现成 | 承诺量与单位 |
| 权益类型 | `ContractCommitmentBenefitCategory`/`OfferCategory`/`Category`/`Type` | 现成 | v1.4 扩展 |
| 生命周期/状态 | `ContractCommitmentLifecycleStatus`/`Model`/`PaymentModel`/`DurationType` | 现成 | v1.4 扩展 |
| 单条 charge 关联承诺 | `ContractApplied`（JSON: ContractId+ContractCommitmentId+AppliedCost/Quantity） | 现成 | Cost and Usage 内 |
| 折扣侧 | `CommitmentDiscountId/Name/Type/Quantity/Unit/Status/Category` | 现成 | v1.2 起 |
| token 用量计数 | `ConsumedQuantity`+`ConsumedUnit`（token），模型= `SkuId/SkuPriceId/PublisherName`，`ServiceCategory: AI and ML` | 现成/官方映射 | FOCUS for AI 页面示意 |
| Price Sheet/单价 | **v1.5 引入 Price Sheet**（“unit & token economics”） | 在途 | 官方承诺 |
| 推理价值/成本 | **v1.5 “inference value at the AI frontier”** | 在途 | 官方承诺 |
| 配额重置周期(reset) | 无字段 → `x_` 私有列 / 待 v1.5+ 新列 | 缺口 | 需提案 |
| 节流/rate/限流 | 无字段 → `x_` 私有列 / 新 schema | 缺口 | 需提案 |

### B) FOCUS 提案路线 / 门槛

1. 组织签 **CLA（FOCUS Series Membership Agreement）** → 成为 Contributing Member（**0 成本，无需 FinOps Foundation 会员**）。
2. 提交 GitHub **Feature Request**（类型填 Standardization / Enhancement / Net New；可关联父级 #2018、参与 #2405 的 Task Force TF-2）。
3. 参与 FOCUS WG / Task Force 会议推进 → 进 milestone（当前 v1.5 正好容纳“token/推理价值/Price Sheet”）→ SC ratify。
4. 认证（如需）：FinOps Certified FOCUS Conformant（v1.3 已开放；Validator 1.4 预计 2026 Q3 后）要求 FinOps Foundation + LF 会员（有成本）→ 提标准阶段不必做。
   **时间估计**：以 v1.5 为目标，若本季度内提交、随半年一版节奏，最快 ≈ **2026 Q4–2027 Q1** 进发布；纯提案→ratify 的绝对时长依社区排程无法精确承诺（待核验）。

### C) OTel GenAI 映射表（钉版本）+ 多版本输出建议

- 钉版本方式：**core semconv `v1.44.0`**（2026-08-04）+ **semantic-conventions-genai `main` 快照（2026-08-11）/ 独立仓 tag**；GenAI 独立 schemaUrl 发布后切换为 schemaUrl 声明。
- 若你的产物既要“稳定给消费方”又要“跟上新拆分语义”，建议：内部按 **`gen_ai.usage.input/output_tokens` + 新拆分族（cache/reasoning/modality）** 双记录；对外默认发稳定的 input/output 计数（缺省即 v1.36 前旧形），另以 `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental` 或 `dual_emit` 双发新模式，避免 renaming 破坏下游。
- 重塑字段需自行映射：`gen_ai.system`→`gen_ai.provider.name`；`prompt_tokens`→`input_tokens`；`completion_tokens`→`output_tokens`；`gen_ai.prompt/completion`→`gen_ai.input/output.messages`（opt-in）。

### D) “配额/权益属性”提案草稿要点（OTel GenAI）

- **问题**：`gen_ai.*` 无 `quota/rate/limit/entitlement`；消费方需自行归一化配额/权益/限流信号（对照：阿里云 AI 网关已在 FinOps 侧引入“消费者配额/周期重置/余量”，反映真实需求）。
- **主张**：新增一组 span 属性 + 指标，建议命名空间：
  - 属性：`gen_ai.entitlement.id`, `gen_ai.entitlement.tier`, `gen_ai.entitlement.remaining_units`, `gen_ai.entitlement.reset_period`, `gen_ai.quota.limit`, `gen_ai.quota.remaining`（单位随 `gen_ai.token.type`/modality）。
  - 指标：在 #101 基础上补充 `gen_ai.client.entitlement_remaining`（Gauge）等，与 `gen_ai.client.rate_limit.events` 配套。
- **理由/可行性**：独立仓“更快迭代、接受新动议”；请求/响应往往由 provider 回传 `usage` 之余的 meta（如 Anthropic `rate limits` 头、OpenAI `organization quota`）可标准化接入；Phase 与 modality 拆分先例（#197/#390）为同类结构性扩展树立范式。建议先在该仓提 issue，并将 FOCUS ContractCommitment 的窗口/额度语义作对账参考（计量侧对齐）。

---

## 附：核心来源清单

| # | 用途 | URL | 引用要点 | 置信度/半衰期 |
|---|---|---|---|---|
| 1 | FOCUS v1.4 官方发布 | finops.org/insights/introducing-focus-1-4/ | 2026-06-04 ratify；2 数据集/47 列；1.5 引入 Price Sheet+token economics | O / 中 |
| 2 | FOCUS v1.3 新闻稿 | linuxfoundation.org/press/…focus-1.3 | 2025-12-11；Contract Commitment 首出现 | O / 长 |
| 3 | ContractCommitmentId 定义 | github.com/FinOps-…/contractcommitmentid.md | 唯一标识，v1.3 引入 | O / 长 |
| 4 | ContractApplied 定义 | github.com/FinOps-…/contractapplied.md | JSON 关联 charge↔commitment | O / 长 |
| 5 | CC 30 列清单 | raw …/contract_commitment/columns/columns.mdpp | v1.4 列全集 | O / 长 |
| 6 | FOCUS for AI | focus.finops.org/technology-categories/focus-for-ai/ | token→ConsumedQuantity 等映射；Nebius | O / 中 |
| 7 | AI 提案 #2018/#2405 | github.com/…/FOCUS_Spec/issues/2405 | v1.5、TF-2、“No AI Exceptionalism” | C / 中 |
| 8 | FOCUS 贡献/成本 | focus.finops.org/faqs/ 、about-focus | 签 CLA、0 成本、无需 FFO 会员 | O / 长 |
| 9 | WG 流程 | foundation/operating_procedures.md；finops.org/working-group-faq | FG/Task Force、sprint、SC ratify | O / 中 |
| 10 | OTel GenAI 独立仓 | github.com/open-telemetry/semantic-conventions-genai | 独立仓、Schema URL=TODO、Development | O / 中 |
| 11 | 分家 #3696/#233/#6783 | semantic-conventions releases；opentelemetry-js #6783 | 主仓不再含 GenAI；独立包建议 | C / 中 |
| 12 | gencai rate-limit #101 | github.com/open-telemetry/semantic-conventions-genai/issues/101 | 无 quota 属性；`gen_ai.client.rate_limit.events` 在途 | C / 中 |
| 13 | 版本选择机制 | opentelemetry.io/docs/specs/semconv/configuration/version-selection/ | declarative `.semconv.version`+`dual_emit` | O / 中 |
| 14 | semconv v1.44.0 | github.com/open-telemetry/semantic-conventions/releases | 2026-08-04 发布 | O / 短 |
| 15 | Tokenomics Foundation | prnewswire + finops.org/insights/token-economics | LF 2026-06-03 筹建 AI 成本开放标准 | C / 中 |

> 待核验项：FOCUS WG 具体周会时间/频次量化；finops-hub 内专项“权益/额度”提案；GenAI 独立仓首版正式发布号与独立 schemaUrl；FOCUS v1.5 精确发布日期（仅按半周期外推）。