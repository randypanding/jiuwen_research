# 子问题一建议：自然语言与形式化契约的融合机制（L1→L2）

## 一、核心结论（基于证据）

多篇独立研究形成一致证据链：LLM 做 NL→形式化生成"语法易、语义难"。Can LLMs Write Correct TLA+（30 个 LLM、205 条规范，SANY+TLC 双验证）测得句法正确率最高 26.6%、语义正确率仅 8.6%，并归纳 5 类幻觉模式；NL2LTL-SecDev26 与 VLTL-Bench 结论相同。TLA+-Bench 进一步提出 correctness envelope：仅改变评分口径，同一批输出正确率在 10.0%~1.7% 间波动六倍，评测必须锚定"可执行验证"。TLA-Prover（已核实 arXiv:2606.06133）证明"验证器即奖励"有效：SFT+以 TLC 为奖励的修复式 GRPO，将语义通过率从 8.6% 提升至 30%。另一侧，nl2spec 证明"子公式↔自然语言片段"映射可交互式暴露并消解歧义；nl2postcond 证明后置条件断言能捕获 Defects4J 中 64 个真实 bug；Daikon 可从执行轨迹自动挖掘候选不变量。

结论：L1→L2 不能靠一次性直译，必须是"交互消歧 + 约束生成 + 验证器闭环修复 + 执行级评测"的管线；L2 契约形态以 pre/post/invariant 断言（Meyer DbC）为根基。

## 二、对 Spec 语言设计的具体建议

**语言机制**
1. 以 pre/post/invariant + assume-guarantee 为契约语义核心（Meyer DbC 1992；Pacti 提供契约组合/精化的参考实现）。
2. 每个 L2 子句可回溯到 L1 片段，内置"子公式↔NL"双向映射（nl2spec），这是"人类精确表达"与消歧的机制基础。
3. 轻量断言式契约作为 L2 最小落地单元，直接可执行检查（nl2postcond）。
4. 用文法归纳/约束解码约束生成输出空间，保证机器可解析（Doc2Spec；Grammar-Forced Translation, ICML 2025）。

**生成管线**
5. 以 fm-universe 7~8B 微调模型为底座（From Informal to Formal，18k 五语言指令数据），在自有 Spec 语料上续训，再做"验证器即奖励"GRPO，让模型自修复被拒规格（TLA-Prover）。
6. 采用"生成-验证-修复"智能体循环（Event-B Agent；LiveFMBench 证实 agentic 工作流有实质增益）。
7. 用 Daikon 从运行轨迹挖掘不变量，自底向上补充 L2 契约候选，与自顶向下的 L1 翻译互补。

**验证闭环**
8. 句法检查（SANY 类）+ 模型检查（TLC 类）作为强制关卡，反例回传生成端修复（TLA-Prover、Event-B Agent）。
9. 防真空检查：对性质做小幅变异，验证器必须能检出违例，否则判定契约恒真作废（TLA-Prover 的 Diamond 级变异测试）。
10. L1 与 L2 的一致性用 refinement-as-implication 交叉验证（TLA+ Trifecta，见 03 文件）。

**评测口径**
11. 执行级四档评分：Bronze（可解析）/Silver（无警告）/Gold（通过模型检查）/Diamond（通过变异测试），不用字符串匹配（TLA-Prover、TLA+-Bench）。
12. 显式声明并版本化 correctness envelope 评分口径（TLA+-Bench）；基准采取防数据污染设计（LiveFMBench）。

## 三、建议采用/不采用的工具

**采用**：fm-universe（活跃，模型底座+评测数据）；Daikon（活跃，2026-05 发布 v5.8.25，不变量候选源）；Pacti（活跃契约代数，A/G 语义参考实现）；TLAForge 的 LLM 会话式结构化构建模式（模式可借鉴）。

**不采用**：nl2spec 工具本体（2023-08 停更，仅采论文方法）；pyeb（停更）；AGREE（绑定 AADL 且 2025-12 后无提交，仅借鉴分层验证思路）；Rodin/Eclipse Event-B 工具链（重型、与路线不契合）；NL2Alloy 传统 NLP 链（已被 LLM 路线取代）。

## 四、风险与开放问题

1. 语义正确率绝对值仍低（8.6%~30%），L2 产物必须保留人工确认环节，需定义信任阈值与回退路径。
2. 评测口径敏感性高（六倍波动），评测协议须与语言版本绑定发布。
3. 交互消歧的用户成本与"低摩擦表达"目标冲突；可用 VERIMED 式"随机形式化差异"做自动歧义提示作为折中。
4. 5 类幻觉模式到自有错误分类的映射及各类型修复策略尚待设计。
5. Daikon 产物仅为"可能不变量"，需置信过滤，否则污染契约库。
6. 证据集中于 TLA+/ACSL/LTL，机制在业务域契约上的可迁移性待实证。
