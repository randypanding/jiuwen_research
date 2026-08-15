# Spec 形式化语言研究 — 资料搜集索引（审查版 2026-08-15）

> 研究问题：如何设计一种既能被人类精确表达意图，又能被机器可执行验证的 Spec 形式化语言？
> 本目录已完成**第二轮审查**：按"近 3 个月更新（2026-05-15 之后）或重大意义"标准对全部条目分级，剔除停更/弱相关条目，并补充 2026 年新成果。

## 目录结构

| 文件 | 对应子问题 | 审查后内容概要 |
| --- | --- | --- |
| `01_自然语言与形式化契约融合.md` | 自然语言与形式化契约的融合机制（L1→L2） | 22 篇论文 + 8 个项目：TLA+ 评测三件套（近3月）、nl2spec/nl2postcond、fm-universe 生态、DbC/Pacti、Event-B Agent、Daikon |
| `02_DontCare区与未定义自由.md` | Don't-Care 区的显式声明与验证 | 32 篇论文 + 9 个项目：CASL 宽松语义、TLA+、Interface Automata、未定义行为形式化、2026 欠规格化新作（Relaxed NFL/VERIMED/SpecRL） |
| `03_Spec版本化与增量演化.md` | Spec 版本化与增量演化（向后兼容） | 23 篇论文/标准 + 10 个项目：TLA+ refinement、SemVer/YANG SemVer/FHIR、OpenAPI 3.2/3.3/4.0 状态、AsyncAPI 3.1、oasdiff/Pact |

## 分级统计

| 分级 | 01 | 02 | 03 | 说明 |
| --- | --- | --- | --- | --- |
| `[近3月]` | 5 | 5 | 1 | 2026-05-15 之后发表/更新 |
| `[重大]` | 9 | 10 | 10 | 奠基性/高影响/领域必读 |
| `[2026]` | 2 | 6 | 2 | 2026 年但早于近三月窗口 |
| `[参考]` | 6 | 11 | 10 | 背景资料 |
| `[剔除]` | 1 | 0 | 4 | 停更/弱相关/来源不可靠 |

## 关键审查发现

1. **NL→可验证规格**：多篇独立研究一致表明 LLM 生成规格"语义正确率远低于句法正确率"，必须依赖模型检验器（TLC/NuSMV/SANY）闭环验证——直接支撑"机器可执行验证"诉求。
2. **未定义即自由**：CASL 宽松语义（一个规格=一族模型）+ TLA+（规格=允许行为集合）+ Alpern-Schneider 分类学是三大理论支柱；2026 年出现 Relaxed NFL、VERIMED、SpecRL 等直接处理欠规格化的新工具。
3. **版本化**：OpenAPI 4.0 短期不会落地（仍在 3.2→3.3 轨道）；Optic 已于 2026-01 归档，oasdiff 成为事实标准；研究热点转向"LLM 与 API 演化知识的冲突"。
4. **工具活跃度**：活跃=Daikon、tlaplus、Maude、Why3、ASMETA、oasdiff、Pact、fm-universe、AsyncAPI；停更=nl2spec、pyeb、Hets、CafeOBJ、CH2O、K-c-semantics、Optic、elibracha、api-specs-comparator。

## 下一步建议（待分析）

1. 基于审查后的核心条目（[重大]+[近3月]），对三个子问题分别提炼"机制/语义/演化"三条主线。
2. 交叉对比各语言（TLA+、Alloy、Event-B、CASL、契约语言）在"人类可表达 + 机器可验证"双目标下的取舍。
3. 评估活跃开源项目（fm-universe、TLAForge、Pacti、oasdiff、Daikon）是否可作为 Spec 语言原型的直接基础。
