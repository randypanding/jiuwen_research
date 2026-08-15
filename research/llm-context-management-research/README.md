# LLM 上下文管理研究：素材总索引（审查版）

> 研究总问题：在代码库巨大且高频变动的情况下，如何为 LLM 设计高效的上下文管理策略，以控制 Token 成本并提升生成质量？
> 本目录已进入**第二阶段：补充审查**。所有条目均经子代理逐一核实真实存在（arXiv 编号 / GitHub 链接与标题对应），并已按「近 3 个月更新或有重大意义」标准筛选，标注重量/优先级。【✔ 重大】【✔ 近3个月】

---

## 素材清单

| 文件 | 专题 | 覆盖范围 | 状态 |
|---|---|---|---|
| `01_前缀缓存与智能检索.md` | 动态前缀缓存与智能检索 | KV cache/前缀缓存、代码库检索增强、增量索引与缓存失效、上下文选择 | 已审查，51 条 |
| `02_长上下文利用与压缩.md` | 长上下文模型利用与压缩 | 长上下文评测、Prompt 压缩、RAG 结合、上下文工程、Agent 记忆、上下文蒸馏 | 已审查，44 条 |
| `03_Cartographer与上下文隔离.md` | Cartographer 工具与上下文隔离 | Cartographer 生态、代码检索工具、子代理上下文隔离、分层上下文管理 | 已审查，26 条 |

---

## 审查结论（要点）

1. **真实性**：全部原始条目（约 100 条）经核实均真实存在，无虚构。仅修正 2 处事实错误：
   - HotPrefix 为 **SIGMOD 2025**（原误标 2026）。
   - CocoIndex 正确路径为 `cocoindex-io/cocoindex`。
2. **核心澄清**：**Cartographer 存在两个不同语义实体**——论文 `PEEK`（arXiv 2605.19932）中的 Cartographer 组件（学术源头），与开源 `Icarus-afk/Cartographer`（语义知识图谱 + MCP，同名独立实现），分析时必须区分。
3. **新增近 3 个月高相关条目**：CORVUS、Cat、CoMEM、Context Rot、Acon、ReCUBE、AGENTS.md 系列、InfoKV（均直接命中"高频变动代码库 + 上下文管理"）。

---

## 三个子问题与研究方向的对应

1. **动态前缀缓存与智能检索**（`01`）
   - 如何根据当前 Spec-delta 和任务，动态从代码库检索最相关上下文（而非全量）。
   - 关键线索：RadixAttention/SGLang、vLLM APC、Mooncake、RepoCoder/Repoformer/CodeRAG、SWE-Pruner、CocoIndex 增量索引、**CORVUS（上下文同步）**、**Append-Only Coding（缓存命中）**。

2. **长上下文模型的利用与压缩**（`02`）
   - 如何评估和利用长上下文模型，并做智能压缩。
   - 关键线索：RULER/LongBench/∞Bench、LLMLingua 系列、Marathon（压缩 vs 检索）、RAG-or-LongContext、**CoMEM（解耦内存）**、**Context Rot**、**AGENTS.md 消融实证**。

3. **Cartographer 作为工具的上下文隔离**（`03`）
   - Cartographer 如何在不污染主流程缓存的情况下，为定位、检索等任务高效服务。
   - 关键线索：**PEEK（Cartographer 组件）**、**Icarus-afk/Cartographer**、**AgentSys**、**CodeDelegator**、**FastContext**、memex RFC、Aider repomap、Sourcegraph。

---

## 下一步建议（待用户确认后执行）

- 去重、交叉验证与优先级排序（各专题已初步标注【重大】/【近3个月】/【背景参考】）。
- 提炼可落地的上下文管理架构与技术选型（三个专题的决策线索已就位）。
- 结合具体应用场景（如 Cartographer 集成）给出方案。