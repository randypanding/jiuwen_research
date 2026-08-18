# 03｜主要 AI 供应商 ToS/AUP 对第三方工具与额度使用的条款比对

- **任务包**：4｜R4.1 条款合规（ToS 比对）
- **调研方法**：对每家先 WebSearch 官方 ToS/Usage Policy/Terms 页，再逐一打开原文核对引用；**未抓到原文/仅靠转载的字段标注「待核验」**。
- **性质**：检索宽判（forward-looking directional review），**非法律意见**。
- **抓取日期**：2026-08-18
- **置信度说明**：`O`=官方原文直接引用；`C`=可追溯到官方/权威二手(原文完整可比对)；`S`=待进一步核验。

> 说明：本表聚焦“**能否把订阅/消费额度通过第三方工具（CLI/脚本/agent）自动调用、能否读取用量数据、能否多账号/共享、能否跑基准、能否拿输出做训练/再工程**”。多数供应商对 **自建 API**（按量付费/开发态）与 **消费者订阅** 采用两套条款，已尽量区分。

---

## 1. Anthropic（Claude.ai / Claude Pro / API）

**适用文档**：Consumer Terms（2025-10-08）、Commercial Terms（2025-06-17）、Usage Policy/AUP（2025-09-15）。
**官方入口**：https://www.anthropic.com/legal/terms ｜ https://www.anthropic.com/legal/commercial-terms ｜ https://www.anthropic.com/legal/aup

| 条款 | 原文引用（≤60字） | 来源 URL | 抓取日 | 置信 |
|---|---|---|---|---|
| F1 第三方工具读本地用量/日志 | 无直接条款。Consumer Terms 仅限“个人使用”；未禁止读取本地日志。Commercial 提供 API/日志，但明确禁止“从服务抓取/采掘数据”。 | https://www.anthropic.com/legal/terms | 2026-08-18 | S |
| F2 自动化/非交互使用订阅额度（headless/agent） | 消费者条款未明文禁止脚本调用订阅；但 D.4(Commercial)禁止“反向工程或复制服务”。自建 API 支持程序化调用（限流由账户定）。 | https://www.anthropic.com/legal/commercial-terms | 2026-08-18 | O |
| F3 多账号/账号共享 | Consumer：账号凭证不得共享 —“You may not share your Account login…with anyone else…may not make your Account available to anyone else.” | https://www.anthropic.com/legal/terms | 2026-08-18 | O |
| F4 发布基准/性能/容量对比 | 未发现禁止基准的条款；Anthropic 对外部评测持开放态度（应附可复现条件）。⚠️ 若用 API 输出跑对比须看用例合规。 | https://www.anthropic.com/legal/aup | 2026-08-18 | C |
| F5 用产出构建竞争性数据/训练/反工程 | ✅明确禁止 —Consumer §3(2)：不得用以“开发竞争产品…或训练任何 AI/ML 算法或模型”；Commercial D.4(a)：不得训练竞争模型；AUP 禁“model scraping/distillation”。 | https://www.anthropic.com/legal/commercial-terms ；/legal/aup | 2026-08-18 | O |
| F6 反规避/反抓取 | ✅明确禁止 —Consumer §3(4)：不得“crawl, scrape, or otherwise harvest data”；AUP 禁 jailbreak/prompt injection（未经授权）；违者限流/冻结/终止。 | https://www.anthropic.com/legal/terms ;/legal/aup | 2026-08-18 | O |
| F7 账号共享定义与处罚 | Consumer：禁止共享凭证/账号，用户对账户下一切行为负责；违规可被终止（Safeguards 监控，见 AUP）。 | https://www.anthropic.com/legal/terms | 2026-08-18 | O |

> **要点**：Claude.ai/Pro 订阅⸺共享明确禁止、训练/抓取/再工程明确禁止；用第三方工具脚本调用**订阅**额度处于灰区（服务条款未明文，但 AUP 禁自动大规模调用）。自建 API 程序化调用合规（属正常开发者用途）；禁止用其做模型蒸馏/竞争模型（Anthropic 已公开起诉滥用蒸馏案）。

---

## 2. OpenAI（ChatGPT / API）

**适用文档**：ChatGPT 用户协议 ToU（ROW，2026-01-01）、Service Terms（2026-06-12）、Usage Policies（2025-10-29）、Sharing & Publication Policy（2022-11-14）。
**官方入口**：https://openai.com/policies/terms-of-use/ ｜ /service-terms/ ｜ /usage-policies/ ｜ /sharing-publication-policy/

| 条款 | 原文引用（≤60字） | 来源 URL | 抓取日 | 置信 |
|---|---|---|---|---|
| F1 第三方工具读本地用量/日志 | 未规定读取“本地日志”的权限。ChatGPT 不提供开放 API 读取订阅用量日志（仅 Enterprise 管理员可查用户日志）。 | https://openai.com/policies/service-terms/ | 2026-08-18 | C |
| F2 自动化/非交互使用订阅额度（headless/agent） | ToU 明文禁止“自动或程序化提取数据或输出”及“规避任何速率限制/安全防护”。agent 自动调用订阅额度属高风险/含糊。 | https://openai.com/policies/terms-of-use/ | 2026-08-18 | O |
| F3 多账号/账号共享 | ToU：“You cannot share your credentials or make your account available to others”。未明文禁止多账号，但规避额度、被风控视为滥用。 | https://openai.com/policies/terms-of-use/ | 2026-08-18 | O |
| F4 发布基准/性能/容量对比 | Sharing&Publication 欢迎研究/评测类公开成果；未禁止基准。规避安全防护式评测被禁止。 | https://openai.com/policies/sharing-publication-policy/ | 2026-08-18 | C |
| F5 用产出构建竞争性数据集/训练/反工程 | ✅明确禁止 —ToU：不得“反编译/还原源码或底层组件(含模型/算法)”；不得“使用输出开发与 OpenAI 竞争的模型”。 | https://openai.com/policies/terms-of-use/ | 2026-08-18 | O |
| F6 反规避/反抓取 | ✅明确禁止 —ToU：“自动或程序化提取数据或输出”“绕过速率限制或安全防护”，与 Usage Policies“circumventing our safeguards”一致。 | https://openai.com/policies/terms-of-use/ ;/usage-policies/ | 2026-08-18 | O |
| F7 账号共享定义与处罚 | ToU：禁止共享凭证/把账号给他人；用户对账户全部活动负责；“破坏/规避规则或防护可能会失去访问权限”。 | https://openai.com/policies/terms-of-use/ | 2026-08-18 | O |

> **要点**：ChatGPT 订阅对“程序化/自动提取 & 绕过速率限制”态度明确禁止；用脚本/agent 批量调用订阅额度风险高。**训练竞争模型、逆向模型**同为明禁。培养/评测公开对比未禁止。认识上注意“to人为声称 AI 输出是人类生成”亦被禁止（影响某些代理署名场景）。

---

## 3. Google（Gemini API / Google AI Studio / Gemini 消费端）

**适用文档**：Gemini API 附加服务条款（2026-03-23 生效）、Google API 服务条款、Google ToS（2026-07-30 新版，于 2026-07-08 核对），Gemini Code Assist / Dev ToS（as via Gemini CLI）。
**官方入口**：https://ai.google.dev/gemini-api/terms ｜ https://developers.google.com/terms ｜ https://policies.google.com/terms

| 条款 | 原文引用（≤60字） | 来源 URL | 抓取日 | 置信 |
|---|---|---|---|---|
| F1 第三方工具读本地用量/日志 | Gemini API 不开放读取本地日志。API 有官方用量面板；Dev ToS 未禁止本地读取。⚠️ 使用第三方工具“直接访问”Code Assist 服务被明确列为违规（见 F6）。 | https://github.com/google-gemini/gemini-cli (tos-privacy.md) | 2026-08-18 | C |
| F2 自动化/非交互使用订阅额度（headless/agent） | 官方 Gemini CLI（headless）可合规使用 OAuth/API；但“用第三方工具直接访问服务（如用第三方以 Gemini CLI OAuth 封装）违反条款，可致封号”。 | https://github.com/google-gemini/gemini-cli (tos-privacy.md) | 2026-08-18 | C |
| F3 多账号/账号共享 | 未查到消费端明确“禁多账号”条款（待核验）。ConductAtlas 未标出 Google 多账号禁令；共享凭证被一般条款禁止。 | https://conductatlas.com/platform/github/…（google 属三方分析） | 2026-08-18 | S |
| F4 发布基准/性能/容量对比 | 未发现禁止基准条款；Google 传统上欢迎第三方评测。⚠️ 新版 Google ToS 增禁“jailbreaking/adversarial prompting/prompt injection”(用于评测的安全绕过除外)。 | https://terms.law/ToS-Watchdog/ai-services/gemini/ ；policies.google.com/terms/update | 2026-08-18 | C |
| F5 用产出构建竞争性数据集/训练/反工程 | ✅明确禁止 —Gemini API附加条款：不得“开发与这些服务竞争的模型”，不得“逆向工程/提取/复制任何组件(含参数权重)”；新版 ToS：不得“使用 AI 生成内容开发 ML 模型”。 | https://ai.google.dev/gemini-api/terms ；policies.google.com/terms/update | 2026-08-18 | O |
| F6 反规避/反抓取 | ✅明确禁止 —新版 ToS：不得“reverse engineering…extract trade secrets”，自动访问须遵守 robots.txt；“jailbreak/adversarial prompting/prompt injection”除安全测试外被禁。 | https://terms.law/ToS-Watchdog/ai-services/gemini/ | 2026-08-18 | C |
| F7 账号共享定义与处罚 | Google 一般条款禁止共享凭证；违规可致“暂停/终止访问”。 | policies.google.com/terms | 2026-08-18 | C |

> **要点**：Gemini 是最依赖“官方 CLI + OAuth”的供应商，明文禁止“用第三方工具直接访问服务”，但对官方 CLI 的 headless/agent 使用是合规主张。对“用 Gemini 输出训练 ML 模型”“逆向/提取权重/抓取”为明禁。基准对外评测未见禁止。

---

## 4. Microsoft / GitHub（Copilot 消费端 & GitHub Copilot）

**适用文档**：Microsoft Copilot Terms of Use（2026-06-12）、GitHub Copilot Product Specific Terms（已过时，2026-03-05 起改用 GitHub Generative AI Services Terms）、Microsoft Services Agreement。
**官方入口**：https://www.microsoft.com/…copilot/termsofuse ｜ https://github.com/customer-terms/github-copilot-product-specific-terms

| 条款 | 原文引用（≤60字） | 来源 URL | 抓取日 | 置信 |
|---|---|---|---|---|
| F1 第三方工具读本地用量/日志 | Copilot 消费端不开放日志；GitHub Copilot User sampling/telemetry 受条款约束（B/数据节）。本地读取未被直接禁止。 | https://github.com/customer-terms/github-copilot-product-specific-terms | 2026-08-18 | C |
| F2 自动化/非交互使用订阅额度（headless/agent） | Copilot 消费端明禁“Don’t use tools or computer programs (like bots or scrapers) to access Copilot.” 且“only…for your own personal use.” GitHub Copilot（开发向）官方支持 agent/CLI。 | https://www.microsoft.com/…copilot/termsofuse | 2026-08-18 | O |
| F3 多账号/账号共享 | Copilot 消费端限制个人使用，未明示多账号；共享凭据被 MS Services Agreement 禁止。GitHub 企业条款按 seat 授权，禁止超额共享。 | https://go.microsoft.com/fwlink/?LinkID=530144 | 2026-08-18 | C |
| F4 发布基准/性能/容量对比 | 未见 Copilot 明禁基准条款。开发向 Copilot（Business/Enterprise）支持大量 agent/usage-based workflows，通常可测。 | https://github.com/features/copilot/plans | 2026-08-18 | C |
| F5 用产出构建竞争性数据集/训练/反工程 | ✅明确禁止 —“使用本服务/输出开发或训练与竞争…模型”为通用条款禁止；Copilot PST 未转授版权于 GitHub（“GitHub does not own Suggestions”），再工程受 Microsoft 服务协议限制。 | https://github.com/customer-terms/github-copilot-product-specific-terms | 2026-08-18 | C |
| F6 反规避/反抓取 | ✅明确禁止 —Microsoft Services Agreement 禁“用 bots/scrapers 访问”；Copilot 消费端“Don’t use tools or computer programs…to access”。 | https://www.microsoft.com/…copilot/termsofuse | 2026-08-18 | O |
| F7 账号共享定义与处罚 | Copilot 消费端：个人使用；共享账号违 MS 服务协议，可致暂停/终止。GitHub 按 seat 授权、禁共享超额。 | https://go.microsoft.com/fwlink/?LinkID=530144 | 2026-08-18 | C |

> **要点**：与 Anthropic/Anthropic 类似，Copilot **消费端**明确禁止用 bots/scrapers/工具访问，并限“个人使用”；开发向 GitHub Copilot（Pro/Pro+/Max）官方支持 agent/CLI/usage 信用额度，reverse/训练竞争模型仍禁。两者商业模式差异显著，影响“额度管理工具”落地方式。

---

## 5. Cursor（Anysphere, Inc.）

**适用文档**：Cursor Terms of Service（2026-08-13）、Acceptable Use Policy。
**官方入口**：https://www.cursor.com/terms-of-service ｜ /acceptable-use-policy

| 条款 | 原文引用（≤60字） | 来源 URL | 抓取日 | 置信 |
|---|---|---|---|---|
| F1 第三方工具读本地用量/日志 | 无明禁本地读取。Privacy 收集“Usage Data（技术日志/交互数据，不含内容）”供内部业务；聚合/去标识后可披露第三方。 | https://www.cursor.com/privacy | 2026-08-18 | C |
| F2 自动化/非交互使用订阅额度（headless/agent） | ToS 未明文禁 headless/agent；Cursor 官方有 CLI/API。⚠️ “1.5 使用限制(vi) probe/scan/penetrate服务”会限制主动探测。未提自动调用订阅额度规则。 | https://www.cursor.com/terms-of-service | 2026-08-18 | O |
| F3 多账号/账号共享 | 未直接禁多账号（待核验）。ToS 一般禁止将账号用于非授权第三方；AUP 禁绕过付费墙。 | https://www.cursor.com/terms-of-service | 2026-08-18 | S |
| F4 发布基准/性能/容量对比 | ✅条件允许 —“不得向第三方提供…基准测试结果，除非包含足以让他人复现该测试的所有必要信息”。即可复现的评测可发表。 | https://www.cursor.com/terms-of-service | 2026-08-18 | O |
| F5 用产出构建竞争性数据集/训练/反工程 | ✅明确禁止 —1.5(v)：“使用本服务或任何建议开发/训练与本服务竞争…的模型，或从事模型提取/窃取”。1.5(i)禁即改/反工程。 | https://www.cursor.com/terms-of-service | 2026-08-18 | O |
| F6 反规避/反抓取 | ✅明确禁止 —1.5(vi)禁“probe/scan/penetrate服务”；1.5(viii)禁“harvest/scrape/extract data”。 | https://www.cursor.com/terms-of-service | 2026-08-18 | O |
| F7 账号共享定义与处罚 | ToS 对订阅自动续费、付款失败可删账号；账号删除以“超一年不活动/卡失效”为触发；未明示共享处罚（待核验）。 | https://www.cursor.com/terms-of-service | 2026-08-18 | S |

> **要点**：Cursor 条款对“再工程、竞争模型训练、抓取、探测”均明禁；**基准测试要求“可复现即可发表”**（对容量/性能对比是最友好措辞之一）。多账号、自动化订阅调用未见明文，属灰区，需询问官方。注意 1.3“未明确同意则不用于模型训练”为较友好条款。

---

## 6. Mistral AI（Le Chat / Vibe / La Plateforme / API）

**适用文档**：ROW Consumer Terms（2026-08-05）、EEA Consumer Terms、Commercial/Additional Product Terms、Usage Policy（2026-06-11）。注：2026-08-08 起 Mistral AI Studio 与 API 仅限商业客户。
**官方入口**：https://legal.mistral.ai/terms/row-consumer-terms ｜ /usage-policy ｜ /commercial-terms-of-service

| 条款 | 原文引用（≤60字） | 来源 URL | 抓取日 | 置信 |
|---|---|---|---|---|
| F1 第三方工具读本地用量/日志 | 未直接规定。Additional Product Terms：Mistral 可用 Usage Data 做“research, improve products…”。本地日志读取未被禁止。 | https://conductatlas.com/platform/mistral-ai/mistral-ai-additional-product-terms/ | 2026-08-18 | C |
| F2 自动化/非交互使用订阅额度（headless/agent） | Consumer/Usage Policy 未明禁 headless；API 面向商业且支持程序化。Usage Policy 禁“circumvent security/安全过滤”。批量自动化订阅消费处于灰区。 | https://legal.mistral.ai/terms/usage-policy | 2026-08-18 | O |
| F3 多账号/账号共享 | ✅明确禁止多账号 —“The creation or use of multiple Mistral AI accounts by a single individual is strictly prohibited, including to bypass rate limits or any other restrictions.” | https://legal.mistral.ai/terms/row-consumer-terms ；conductatlas 引用 | 2026-08-18 | C |
| F4 发布基准/性能/容量对比 | Usage Policy 未明确禁基准；Mistral 官方对外开源/公开评测较开放（自建 API）。规避安全测试式评测被禁。 | https://legal.mistral.ai/terms/usage-policy | 2026-08-18 | C |
| F5 用产出构建竞争性数据集/训练/反工程 | ✅明确禁止 —Commercial Terms（d/e）禁“reverse engineer/decompile…或使用 Output 反工程 Mistral AI 产品”。“Customer will not…use the Output…to reverse engineer”。 | https://conductatlas.com/platform/mistral-ai/mistral-ai-commercial-terms/ | 2026-08-18 | C |
| F6 反规避/反抓取 | ✅明确禁止 —Commercial Terms（f）禁“干扰/规避/绕过安全或审核机制”；Usage Policy 禁绕过安全过滤与 AI 安全 filter；违规可暂停/终止账号。 | https://legal.mistral.ai/terms/usage-policy | 2026-08-18 | O |
| F7 账号共享定义与处罚 | Additional Terms：不得将 End User Account“sharing/selling/licensing…outside of your entity”。ROW Consumer：禁多账号/假账号；违规可终止。 | https://legal.mistral.ai/terms/row-consumer-terms ；conductatlas | 2026-08-18 | C |

> **要点**：Mistral 在多账号上**用语最明确**（“multiple accounts…strictly prohibited”）；Studio/API 自 2026-08 起转向“仅商业客户”。再工程、绕过安全过滤为明禁。对外评测/基准未见禁止。Note：Consumer 条款（Vibe 等）与 Commercial/API 分离，影响工具化落地时的适用文档选择。

---

## A）能力 × 厂商 宽判表（红/黄/绿）

> 🟢=明确允许；🟡=含糊/灰区（需官方澄清或取决于支付方/账号类型）；🔴=明确禁止（对该能力构成障碍）。
> “能力”从“我们能否合法行使该行为”角度判定（抓取/训练/共享/绕过均属我方受限能力，故多数标🔴；基准/本地读取多为🟢/🟡）。

| 焦点能力 \ 厂商 | Anthropic | OpenAI | Google Gemini | MS/GitHub Copilot | Cursor | Mistral |
|---|---|---|---|---|---|---|
| **F1** 三方工具读本地用量/日志 | 🟡（消费端无开放读取；未禁本地读取） | 🟡（仅 Enterprise 有日志；未禁本地） | 🟡（官方面板；第三方“直接访问服务”被禁用） | 🟡（消费端无；开发向有 telemetry） | 🟢/🟡（Usage Data 内部用，未禁本地读） | 🟡（Usage Data 归其研究；未禁本地） |
| **F2** 自动化/非交互用订阅额度 | 🟡（API🟢；订阅脚本调用灰区+限流） | 🔴（明禁程序化提取/绕过速率限制） | 🟡（官方 CLI 合规；第三方封装违条款） | 🔴（消费端明禁 bots/scrapers；开发向🟢） | 🟡（CLI/API 有；服务条款未明文） | 🟡（API🟢；Consumer 批量消费灰区） |
| **F3** 多账号 / 账号共享 | 🔴（凭证共享明禁） | 🔴（凭证/账号共享明禁） | 🔴/🟡（共享禁止；多账号待核验） | 🔴（共享禁止；个人使用） | 🟡（未明文；灰区） | 🔴（多账号+共享均明禁） |
| **F4** 发布基准/性能/容量对比 | 🟢（未禁；外部评测开放） | 🟢（未禁；规避安全式评测除外） | 🟢（未禁基准；禁 jailbreak 评测绕过） | 🟢/🟡（开发向可测；消费端限制个人新） | 🟢（“可复现即可发表”明确） | 🟢（未禁；自建 API 开放） |
| **F5** 用产出构建竞争数据集/训练/反工程 | 🔴（模型训练/蒸馏/逆向明禁） | 🔴（输出训练竞争模型/逆向明禁） | 🔴（输出产 ML 模型/提取权重明禁） | 🔴（训练竞争模型/逆向明禁） | 🔴（训练竞争模型/提取明禁） | 🔴（逆向/用 Output 反工程明禁） |
| **F6** 反规避/反抓取条款强度 | 🔴（crawl/scrape/jailbreak 明禁） | 🔴（程序化提取/绕过防护明禁） | 🔴（reverse/robots.txt/jailbreak 明禁） | 🔴（bots/scrapers 明禁） | 🔴（probe/scrape/extract 明禁） | 🔴（绕过安全/审核过滤明禁） |
| **F7** 账号共享定义与处罚 | 🔴（凭证不共享；监控+可终止） | 🔴（禁止共享；违规可失访问） | 🟡/🔴（共享被一般条款禁） | 🔴（按 seat/共享即可终止） | 🟡（未明文处罚） | 🔴（共享/多账号明禁，可终止） |

**读表小结**
- **对“把订阅额度用第三方脚本/agent 自动拉满”最友好**：C（Cursor）、Mistral、Anthropic、Google（官方 CLI）跑官方/合规路径较可行；**OpenAI、微软 Copilot 消费端**措辞对自动/程序化调用最严（🔴）。
- **“拿输出做再工程/竞争模型/蒸馏”全行业红**，无一例外——任何基于“额度搬运”构建竞争性模型或大规模蒸馏的方案都应视为高风险/需豁免。
- **账号共享与多账号**在 Anthropic/OpenAI/Mistral/Microsoft 均明确禁止；Cursor/Google 措辞较含糊。
- **基准评测**普遍允许（对外发布差异在“可复现条件”“是否涉及安全绕过”）。

---

## B）需要律师确认的问题清单（≥8条）

1. 我司以“第三方/开发者工具”名义将 **Claude Pro / Cursor / Gemini Pro 等订阅额度**作为 headless/agent 批量调用，是否符合各厂商“个人使用、非商业、不得转售”认定的边界？何处需要签 MSA / 商业检测协议？
2. **“把自身服务额度作为编排中继层”**（聚合多家额度/密钥供终端用户）——是否落入各家“resell”“make the service available to others”“账号共享”条款（尤其 Anthropic D.4、OpenAI ToU、Mistral 共享禁令）？
3. Anthropic / OpenAI / Google 的 **“不得使用输出训练/改进竞争模型或做决策蒸馏”** 是否适用于“仅用于容量/性能基准测试而不用于训练”的中间结果？是否有豁免（研究型评测、可复现基准）？
4. Google 2026-07-30 新版 ToS **“禁止用 AI 生成内容开发 ML 模型/相关 AI 技术”** 与“官方 Gemini CLI 可合规 headless/agent”之间的边界如何界定？第三方工具“直接访问服务”哪一步算违规（OAuth 中继 vs 纯前端）？
5. 微软 **“Don’t use tools or computer programs…to access Copilot”** 是否当然延伸至 GitHub Copilot（开发向 agent/CLI），还是仅约束消费者聊天端？开发向额度（Copilot Pro/Max、AI Credits）是否有独立的自动/容量使用许可？
6. Cursor **“可复现即可发布的基准测试”** 是否覆盖容量/并发/吞吐类负载测试，还是仅指功能评测？对 Cursor API 的自动化调用是否同受该条约束？
7. 各家 **“多账号/多席位”** 政策：Mistral/Google 是否对“同一实体名下多个开发账号用于轮换额度”明确禁止；若分别以个人名义注册并各自付费，是否仍构成“规避 rate limit”？
8. 若我司在**中国大陆/无官方支持地区**通过代理/第三方通道使用上述服务，是否触及 Anthropic 的“Supported Regions”及各国出口管制条款？
9. OpenAI **“声称输出为人类生成”被禁** 是否限制我们产品在工具输出、基准报告署名上的表述方式；自动化流程产生的输出需满足何种披露标注？
10. 对使用 API（自建密钥）但**财务上由第三方实体付费/共享额度**的场景，是否构成“账号共享”“转售”或“提供未授权访问”，应由谁向哪一供应商承担合同责任？
11. **出口/管辖冲突**：美国的 ToS（如诉法/终止权）与欧盟（GDPR/消费者法）在本项目横跨地区时的优先级，以及供应商单方变更条款的效力窗口（Google 已承诺“重大不利变更提前通知”）。
12. **处罚与救济**：各供应商“暂停/终止/删号”约定的触发门槛与通知义务是否一致；若因第三方工具导致我方账号被封，对下游客户/承诺的赔偿与止损安排为何。

---

### 待核验 / 提示
- Google **消费端（Gemini App/Pro 订阅）多账号** 具体条款未抓到原文，仅凭三方分析，需进一步核验官方版。
- Cursor **多账号、账号共享处罚** 未抓到明条款，标 🟡/待核验。
- OpenAI **Business Terms（ChatGPT Enterprise / API 合同层）** 与本文消费者 ToU 有差异，若进入商业合作需另核。
- “F1 读取本地用量/日志”多数供应商条款**空白（未被禁止也未被明确授予）**，技术上属本地端行为，但需与 F6（不抓取服务端）交叉确认。