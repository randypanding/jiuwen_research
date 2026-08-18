# Anthropic Claude 订阅档位权益「地面真相」研究报告

> 调研日期：2026-08-18　|　方法：官方页面逐条 WebFetch/WebSearch 核验 + 社区/逆向实测交叉
> 置信度标注：**O**=官方一手；**A**=官方文档派生的可靠推断；**C**=跨源一致（≥2 独立来源）但非官方逐字；**S**=单源/社区实测，待核验
> 半衰期：**短**=<1季度（价格/倍率/额度整数）；**中**=1–2季度（周额度结构）；**长**=≥1年（架构/API 设计语义）

---

## 0. 核心方法论与免责声明

- Anthropic **不在任何单一页面发布「今天此套餐=多少条消息/几小时」的完整权威数字**。官方只有：①价格页列的相对倍率（5x/20x）；②帮助中心个别档位给的「approx/approximately」数字；③`claude.ai` Settings>Usage 与 Claude Code `/usage` 的**实时账户级读数**（每个账户所见即当前真相）。
- 因此本报告区分「**官方冻结数字**」（O/A，可信）与「**社区/逆向实测数字**」（C/S，随时间漂移大）。**数字以抓取日为准，落笔处一律标注"截至2026-08官方/社区显示"，因为 Anthropic 已多次午夜改档（如 2025-08 周额上线、2026-03 高峰期倍率、2026-05-06 Claude Code 5 小时额度翻倍并取消高峰限速）。**
- 关键结构结论先行：**订阅侧与 API 侧是两套完全独立的计量系统**，表头、重置语义、计费、可编程性全部不同。

---

## 1. R3.1 档位 × meter 权益矩阵

### 1.1 官方定价基线（截至 2026-08-18 抓取 anthropic.com/pricing）

| 档位 | 官方价格 | 账期 | 关键权益主线 |
|---|---|---|---|
| **Free** | $0 | — | 网页/桌面/移动端对话、代码生成、联网搜索、记忆、扩展思考；**无 Claude Code** |
| **Pro** | $17/月（年付，一次 $200）或 $20/月 | 月/年 | 更多用量\*、Claude Code、Claude Cowork、无限 Project、Research、更多模型、M365/Outlook |
| **Max 5x** | 从 $100/月 | 月/年 | Pro 全部 + 5x 用量、更高输出上限、早期功能、高峰优先 |
| **Max 20x** | 从 $200/月 | 月/年 | 20x 用量（相对 Pro） |
| **Team 标准座** | $20/座·月（年付）/ $25 月付 | 月/年 | 比 Pro 更多用量\*、集中计费、SSO、企业级部署、默认不训练模型 |
| **Team 高级座(Premium)** | $100/座·月（年付）/ $125 月付 | 月/年 | 标准座的 5x 用量\* |
| **Enterprise** | 定价需联系销售 | 定制 | 大规模运营，多种子混合、单点登录、审计日志、用量分析、合规/HIPAA、SCIM 等（特性表见官网） |
| **API（Console 预付费）** | 按 token 计费（见 §1.8） | 预付款 | 按用量付费、usage tier、RPM/TPM |

- 注意官方原文：Max/Team 均标注"**Usage limits apply**"，且价格页本身**不公布硬性消息数/小时数**——只有相对倍率与帮助中心近似值。
- 来源：https://www.anthropic.com/pricing（抓取 2026-08-18）　置信 **O**　半衰期 **短**（价格/倍率）

### 1.2 Free

| meter/维度 | 地面真相 | 来源/置信/半衰期 |
|---|---|---|
| 价格 | $0，无需开动 | pricing，O/H 短 |
| 模型可用 | 主力 Sonnet（社区称 Sonnet 5 系）；Opus 额度极低（社区：约 Free 档每周 Opus/Fable 配额约为其他档的 ~50%） | 社区 C 短 |
| 5h 窗口 | 社区实测：每日 ~15–40 条短消息（多数落在 Sonnet、非 Claude.ai 的 codew/cap 无条款） | writingmate/truefoundry C 短 |
| Claude Code | **官方明确不提供**（免费档无 Claude Code 访问） | explainx/truefoundry C 短 |
| 重置语义 | 社区称每日重置 + 高峰缩减；官方不承认固定数字 | S 短 |
| 超额行为 | 峰值时段降级/减少；**无优先队列**；等窗口 / 不自动转 API | C 短 |

### 1.3 Pro（$17年付/$20月付）

| meter/维度 | 地面真相 | 来源/置信/半衰期 |
|---|---|---|
| 模型可用 | **Sonnet 全功能**；**Opus 在 Claude Code 不可用**；网页端参与独立 Opus 池 | 官方帮助中心 O 中 |
| 5h 窗口（官方冻结） | **≈45 条消息/5h**，或 **≈10–40 次 Claude Code prompt/5h**（"average users, vary by 消息/上下文/附件长度"） | support.anthropic.com O 中-短 |
| 5h 窗口（2026-05 翻倍后，社区） | 翻倍后常见 ~90 条（官方未更新 45 为 90，数字存在官方/社区歧义） | writingmate S 短 |
| 周额（官方，2025-08 上线） | Sonnet ≈40–80 小时/周；**不入 Opus 周池**（Opus 需要 Max） | support/explainx O 中 |
| 窗口类型 | 5 小时**滚动**（非整点）+ 7 天周额（固定日重置） | 社区跨源 C 长 |
| 并发/速率 | 无公开固定数字；并行多实例会更快撞限 | 帮助中心 O 中 |
| 超额行为 | `You've hit your session limit · resets X`；`/model` 切 Sonnet 不恢复访问（额度共享池）；等重置或启用 usage credits；**不自动转 API** | ssdnodes C 中 |
| 商用/fair-use | 面向个体的非商用强度；周额即为防「inference whale」滥用；默认无模型训练，但 **Offers training opt-out 为 Pro 也可选**（pricing 特性表） | pricing O 中 |

*注：Pro 官方帮助中心还注明 "Pro plan subscribers can access Sonnet 4, but won't be able to use Opus 4 with Claude Code"。*

### 1.4 Max 5x（$100/月）

| meter/维度 | 地面真相 | 来源/置信/半衰期 |
|---|---|---|
| 模型可用 | **Sonnet + Opus** 均可（Claude Code 可切换）；Max 特有 **Opus 独立周池** | 帮助中心/cc-hub O 中 |
| 5h 窗口（官方近似） | **≈225 消息/5h**，或 **≈50–200 Claude Code prompt/5h** | support.anthropic.com O 中-短 |
| 周额（官方近似） | Sonnet ≈140–280 小时/周；**Opus ≈15–35 小时/周** | 支持中心/explainx O 中 |
| 超额行为 | 撞限可 `Usage credits` 续用；排队优先权更高；高峰优先；**Opus 周池与 5h/周全模型池分开计量，先耗尽那个更早到** | C/cc-hub 中 |
| 并发/速率 | 帮助中心：大代码库/多实例并行会更快撞限 | O 中 |

### 1.5 Max 20x（$200/月）

| meter/维度 | 地面真相 | 来源/置信/半衰期 |
|---|---|---|
| 5h 窗口（官方近似） | **≈900 消息/5h**，或 **≈200–800 Claude Code prompt/5h** | support.anthropic.com O 中-短 |
| 周额（官方近似） | Sonnet ≈240–480 小时/周；**Opus ≈24–40 小时/周** | 支持中心/explainx O 中 |
| 模型 | Sonnet + Opus；Opus 独立周池最大 | O 中 |
| 商用量级判例 | 2025-08 曾有 $200/用户数周消耗 ≈$3.5 万美元推理成本 → 促成周额出台；已被多方解读为**订阅非商用无限**的信号 | TechCrunch/BusinessInsider C 中 |

### 1.6 Team（标准座 $20/$25 · 高级座 $100/$125，5–150 座）

| meter/维度 | 地面真相 | 来源/置信/半衰期 |
|---|---|---|
| 计量单位 | **按座（per-seat）** 的额度，非组织池；座级决定额度大小（Premium=标准 5x） | pricing/ssdnodes O 中 |
| 结算/管理 | 集中计费、SSO、管理员控制连接器、企业级桌面部署、企业内搜索、**默认不训练内容** | pricing O 中 |
| 模型 | Sonnet + Opus（按座）；Premium 座含 Opus 更多 | 社区 C 中 |
| 重置 | 每座滚动 5h + 周额；**与 claude.ai/Chat 及 Cowork 共享同一池**（官方帮助中心明示用 Claude for Work 组织侧同款：额度按座、跨 Claude.cowork/chat 共享） | ssdnodes/帮助中心 C 中 |
| Claude Code 访问 | **Claude for Work（Team/Enterprise）不可用订阅内访问 Claude Code** — 官方帮助中心：Team/Enterprise 用户需另开 **API Console PAYG** 账号按量付费 | support.anthropic.com O 中 |
| API 独立性 | 组织侧与 Console API **独立**：Team/Enterprise 的组织额度不计入/prevoid API 预付费；code 访问走 PAYG | O 中 |

### 1.7 Enterprise

| meter/维度 | 地面真相 | 来源/置信/半衰期 |
|---|---|---|
| 定价 | 未公开，联系销售；最高权限 | pricing O 长 |
| 计量 | 按座、多子混合；滚动 5h + 周额（同 Team 结构）；**配额可在组织/座级配置** | ssdnodes/pricing C 中 |
| 治理 | SSO/SCIM/审计日志/用量分析/RBAC/合规 API/HIPAA/自定义数据留存，**组织级技能部署**、数据目录 | pricing O 长 |
| 数据 | 默认不训练内容（对 Team/Enterprise 为默认，非 opt-in） | pricing O 长 |
| 可编程 | 走 Analytics API（详见 §R3.2）；Admin/Usage API 对纯 Enterprise 有差异 | usage-cost-api O 中 |
| API 独立性 | 与 Console/API 独立计费；Enterprise 成本须经 Analytics API 获取 | O 中 |

### 1.8 API（Console 预付费，usage-tier 制）

| meter/维度 | 地面真相 | 来源/置信/半衰期 |
|---|---|---|
| 计费 | 按 token：社区/官方镜像常引 Sonnet 类 ≈$3/M in、$15/M out；Opus 类更高（社区表差异大：$15/$75 与 $5/$25 并存）——**请以 docs.anthropic.com 当季 models/pricing 为准，未逐字数锁定，标注待核验** | 混合 C->S 短 |
| 限流维度 | **RPM / ITPM / OTPM**，按模型族、per-usage-tier | rate-limits 文档 O 短(数字)/长(语义) |
| usage tier | 按累计充值自动升档：Tier1 起（$500上限）→Tier4（$200,000）→Monthly Invoicing（无上限） | rate-limits O 中 |
| 算法 | **Token bucket 连续补充**，非固定窗重置 | rate-limits O 长 |
| 超额 | HTTP `429` + `retry-after`；`rate_limit_error`；超支则暂停到下月 | O 长 |
| 模型可用性 | 全部模型全部区域，响应头 `anthropic-organization-id` | api/overview O 长 |
| 订阅 vs API | **完全独立**：订阅额度不计入 API 预付费；API key 与订阅账户是两套凭证 | 官方多处 O 长 |

### 1.9 A/B 测试 / 异质性（官方未披露项）

- **官方从未公开 A/B 或使用异质性**。社区观测到：同一套餐不同账号 `/usage` 显示的 5h 基数与周额常有差异（属「容量管理」动态调额，非固定公式）。官方帮助中心措辞为「usage varies based on …」（把差异归责于消息长度/上下文/附件/模型/工具），并明言**每个账户实时读数才是准确信息**。
- 已知结构异质：Pro 单周池（跨模型）、Max 双周池（全模型 + Sonnet 专池；另有 Opus 专池）、Enterprise 可组织级配置。
- 置信 S（官方缺口），半衰期 中。

---

## 2. R3.2 官方可编程数据源

### 2.1 Usage & Cost API 是否覆盖订阅侧？

**结论：API 侧（Console/Claude Platform）有，订阅侧（claude.ai Pro/Max/Team/Enterprise 的 5h/周额）没有。**
- **Console/API 侧**：`Usage & Cost Admin API`（`/v1/organizations/usage_report/messages`、`.../cost_report`），返回**历史逐日 token 用量与成本**，粒度 bucket_width、报表类，**非实时窗口态**。
  - 认证：Admin API Key（`sk-ant-admin01-`）于 `x-api-key`；或 **OAuth bearer `org:admin` scope**（仅 admin/owner/primary owner 可拿）。Enterprise(claude.ai) 组织则用 **Analytics API key** 走另一套 `/api/admin/analytics`。
  - wells：是**组织级 API 消耗**（RPM/TPM/cost），**不含订阅的 5h/周额消耗**。
- 字段示例：`given-name` 不适用；返回含 `total_input_tokens`/`total_output_tokens`/按模型按日分桶，非订阅 meter。
- 来源：Usage & Cost API 文档（EN 与 PT-BR 镜像一致）　置信 **O**　半衰期 **中**

### 2.2 API 侧限流响应头（订阅 vs API 两套）

**两套 header 体系，因认证方式而异（官方文档只公开 API key 那套）：**

**Set A — SDK/API key（官方文档化）**
```
retry-after                                   # 429 时等待秒数
anthropic-ratelimit-requests-{limit,remaining,reset}   # RPM：(上限/剩余/RFC3339补满时刻)
anthropic-ratelimit-tokens-{limit,remaining,reset}     # 合并token桶
anthropic-ratelimit-input-tokens-{limit,remaining,reset}  # ITPM
anthropic-ratelimit-output-tokens-{limit,remaining,reset} # OTPM
anthropic-priority-{input,output}-tokens-{limit,remaining,reset}  # 仅 Priority Tier
anthropic-fast-*                                 # 仅 Fast mode
```
- `reset` 为 **RFC 3339 全桶补满时刻**；`remaining` token 四舍五入到最近千位；`cache_read_input_tokens` 除 Haiku3.5 外**不计 ITPM**。来源：平台 rate-limits 文档（多语言一致）　置信 **O**　半衰期 中(数字)/长(语义)

**Set B — OAuth/订阅（Pro/Max，官方未公开，社区逆向实测）**
```
anthropic-ratelimit-unified-status                          # allowed|allowed_warning|rejected
anthropic-ratelimit-unified-reset                           # 代表窗口重置(unix s)
anthropic-ratelimit-unified-representative-claim            # 绑定窗口:five_hour|seven_day|seven_day_opus|seven_day_sonnet
anthropic-ratelimit-unified-5h-{utilization,reset,supass...} # 0..1 用量分数 + 重置
anthropic-ratelimit-unified-7d-{utilization,reset,supass...}
anthropic-ratelimit-unified-fallback[-percentage]           # 降级(Sonnet)可用性
anthropic-ratelimit-unified-overage-status                  # 超用状态
```
- 语义：订阅用量以 **utilization 分数(0~1)** 而非剩余计数表达；**任何响应**都带（非仅 429）；`five_hour`/`seven_day`/`seven_day_opus`|`seven_day_sonnet` 为当前绑定窗口。来源：claude-pulse RATE_LIMITS.md（逆向，2026-05-30）　置信 **S**（官方无文档）　半衰期 中

### 2.3 响应体 usage 字段（Messages API，官方文档化）

```
usage:
  input_tokens                       # 最后一个 cache breakpoint 之后的输入
  cache_creation_input_tokens        # 首次写入缓存的 input
  cache_read_input_tokens            # 命中缓存读取的 input
  output_tokens
```
- 缓存读取 10% 单价；`max_tokens` 不预占 OTPM（按实际产出计）。来源：Messages API + cache-aware ITPM 说明　置信 **O**　半衰期 长

### 2.4 `claude` CLI：`/usage` 与 statusline `rate_limits`

- **`/usage`**（CLI 内命令）：展示**当前可用/已用**的 5h（session）与周（weekly）额度及重置时刻；另有 **Opus 专属额度**栏（Max）。是订阅侧 meter 最可靠的手动来源。来源：Claude Code 帮助 / ssdnodes / claude-code-hub　置信 **C**　半衰期 中
- **statusline `rate_limits` 字段**（v2.1.80+）：statusline 输出可展示 `rate_limits`（包含 `usages` 数组：`window:{5h|7d|...}`、`active`、`surpassed_threshold` 等），可实时看到 5h/周窗口用量 % 与重置时刻。
  - 配置于 `~/.claude/settings.json` 的 `statusLine`；社区工具（claude-statusline 等）解析该字段。
  - 来源：claudelab（statusline 教程）/ cc-statusline　置信 **C**　半衰期 中

### 2.5 本地日志与凭证路径

| 路径 | 内容 | 来源/置信/半衰期 |
|---|---|---|
| `~/.claude/` | 会话 JSONL 落在 **`~/.claude/projects/…/`**（`.jsonl` 含消息+token 快照）；`settings.json` 用户设置；旧版 `~/.config/claude/` 为 v1 遗留 | claude-statusline(读 session timestamps)/社区 C 中 |
| `~/.config/claude/` | 旧版(<=1.x)配置/日志，读取旧 `/usage` 产物；新版迁移到 `~/.claude/` | 社区 C 中 |
| credential store | OAuth 在 Keychain/`libsecret`；statusline 工具需读取以获得 token→但**不可用于持久轮询**（token 短期有效） | claude-statusline C 短 |
| 结构化会话 | 每条 message 是 JSON，内含 `message.usage`（同 §2.3） | 本地实测/社区 C 中 |

- **结论：订阅侧 5h/周/Opus meter 只能靠本地+后台（CLI `/usage`/statusline/本地 JSONL）获得** — 官方对订阅侧**无任何公开 API** 返回窗口态。

### 2.6 哪些 meter 只能靠探针（probe）获得

| meter | 是否可官方程序化取 | 可行渠道 |
|---|---|---|
| API 用量/成本(历史) | ✅ Usage & Cost Admin API / Console CSV | Admin Key / org:admin / Analytics Key |
| API 实时 RPM/TPM | ⚠️ 半（仅响应头, 被动） | 请求响应头 Set A |
| **订阅 5h 窗口用量/重置** | ❌ 无公开 API | CLI `/usage` / statusline / OAuth 响应头 Set B（未文档）/ 本地 JSONL |
| **订阅周额** | ❌ 无公开 API | 同上前两者 |
| **订阅 Opus 专池** | ❌ 无公开 API | `representative-claim=seven_day_opus` 出现时 / `/usage` |
| 免费档额度 | ❌ 无 | 无（爬 claude.ai 协议违反 ToS） |

---

## 3. 附录

### A) Anthropic entitlements_v0 矩阵（截至 2026-08-18）

| 档位 | 价格 | 模型 | 5h 窗口(官方近似) | 周额(官方近似) | 窗口类型 | 超额行为 | 订阅内 Claude Code |
|---|---|---|---|---|---|---|---|
| Free | $0 | Sonnet(主力)/Opus极低 | ~15–40 msg/日(社区) | 无官方 | 逐日(社区) | 降级等待,不转API | ❌ |
| Pro | $17年/$20月 | Sonnet；Code无Opus | ≈45 msg='10–40 prompt | Sonnet 40–80h | 5h滚动+周额(固定日) | 等重置/usage credits | ✅ |
| Max 5x | $100 | Sonnet+Opus | ≈225 msg='50–200 prompt | Son160–280h/Opus15–35h | 5h滚动+周(全模型+Sonnet专+Opus专)并存 | 等待/credits/优先 | ✅ |
| Max 20x | $200 | Sonnet+Opus | ≈900 msg='200–800 prompt | Son240–480h/Opus24–40h | 同上 | 同上 | ✅ |
| Team 标准座 | $20/$25/座 | Sonnet(座) | 按座>Pro | 按座组织级 | Per-seat rolling+weekly | 组织治理 | ❌(需另开API PAYG) |
| Team 高级座 | $100/$125/座 | +Opus更多 | 标准座5x | 更大 | 同上 | 同上 | ❌(同上) |
| Enterprise | 定制 | 全 | 按座可配置 | 组织配置 | 同上 | 合规流程 | ❌(API PAYG) |
| API | token计费 | 全 | 无会话窗→RPM/ITPM/OTPM+token bucket | 无 | 连续补充 | 429/超支暂停 | PAYG |

*注：5h/周/Opus 池 **多窗口并存、先耗尽最晚到者为准**；额度与 claude.ai 网页/Chat/Cowork **完全共享同一池**；API 与订阅独立。*

### B) datasource_capability 要点

- **官方节流只暴露 API 侧**（Usage & Cost Admin API、set-A header、usage 字段、Console CSV）；对订阅 5h/周/Opus meter **零公开 API**。
- 认证：org admin（admin/owner/primary owner）→ Admin Key 或 `org:admin` OAuth；Enterprise→Analytics Key。
- 唯一「官方认可」的订阅读数入口 = 界面（claude.ai Settings>Usage / CLI `/usage`）+ 逆向 header Set B + 本地 JSONL。

### C) 订阅侧可观测性缺口图

```
                    ┌──────────────────────────────────────────────┐
 官方可程序化          │ 订阅(5h/周/Opus)窗口态:    ❌ 无公开 API        │
 (Usage&Cost API,    │  API 实时 RATE header:    ⚠️ SetB 未文档化      │
  SetA headers)  ──► ┤  CLI /usage/statusline:    ✅ 手动(非API)        │
                    │  本地 ~/.claude/**/*.jsonl: ✅ 本地(听后台)        │
                    │  claude.ai Settings>Usage:  ✅ 界面                │
                    └──────────────────────────────────────────────┘
  缺口: 订阅侧不存在(无认证 token 可轮询的)程序化 meter 端点。
  探针必要范围 = 5h覆盖/周额覆盖/Opus专池覆盖 → 只能本地+后台抓取。
```

### D)「官方未公开字段」待核验清单

1. **订阅 Set B header 完整 schema**（`unified-*`，尤其 `overage-status` 取值与 `-surpassed-threshold` 触发阈值比分）——逆向自 claude-pulse，最新为 2026-05-30，**待重抓现行 CLI 版本验证**。
2. **Max Opus 周池与其他池的扣减优先级/比例**（fallback-percentage 观测为 const 0.5）——未见官方确认。
3. **Pro 5h「45→90」翻倍**——官方帮助中心仍写 45；社区称 2026-05-06 Claude Code 5h 永久翻倍并存。**两套数字并存待核验**。
4. **各模型 API 单价当季冻结值**（Sonnet 类 $3/$15；Opus 类 $15/$75 vs $5/$25 社区不一致）——**需 docs.anthropic.com 当季 models/pricing 逐字锁定**。
5. Free 档「每日 15–40」为准静态数字，官方从不承认 —— 视为**观测性缺口**而非官方字段。
6. Team/Enterprise 组织级配额是否可经企业侧 config 输出到日志/审计——未证，待核验。

---

### 主要来源 URL（抓取日 2026-08-18）
- https://www.anthropic.com/pricing（档位/价格/倍率/能力表）
- https://docs.anthropic.com/en/api/rate-limits · https://platform.claude.com/docs/en/api/rate-limits（API 限流两面、spend tier、headers、usage tier）
- https://docs.anthropic.com/en/manage-claude/usage-cost-api · …/admin-api（Usage&Cdec 认证 Admin/org:admin + Enterprise Analytics）
- https://support.anthropic.com/en/articles/9797557-usage-limit-best-practices（用量机制与缓存）
- https://support.anthropic.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan（Pro/Max 与 Claude Code：45/225/900、周额小时数、Opus 访问差异、Team/Enterprise 需 API PAYG）
- https://github.com/qalarc/claude-pulse/blob/main/docs/RATE_LIMITS.md（Set B 逆向；2026-05-30）
- 交叉社区核对：writingmate.ai（2026 用量）、explainx.ai（改动时间线，2026-07/08）、hypereal.tech（档位明细）、truefoundry.com（Claude Code 限量，2026-07）、claudelab.net / github cc-statusline（statusline rate_limits）、ssdnodes.com（`/usage` 与封禁/削额信号语义）、claude-code-hub.org（windows 结构与 `/usage`）