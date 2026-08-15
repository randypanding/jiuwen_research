# 02 Don't-Care 区与未定义自由 — 审查版（2026-08-15）

> 主题：Spec 如何表达"未定义即自由"、避免规格无限膨胀。
> 审查标准：**近期性**（2026-05-15 之后近 3 个月内发表/更新）或 **重大意义**（奠基性、高影响、领域必读）。已剔除停更、弱相关、来源不可靠的条目。
> 分级标记：`[近3月]`=近三个月内；`[重大]`=奠基/高影响；`[2026]`=2026 年但早于近三月窗口；`[参考]`=背景资料；`[剔除]`=已移除。

## 一、论文

### A. 代数规范与宽松语义（Loose Semantics / Underspecification）— 理论根基

1. **[重大] CASL — The Common Algebraic Specification Language: Semantics and Proof Theory**
   - 作者：T. Mossakowski, A. Haxthausen, D. Sannella, A. Tarlecki
   - URL：https://homepages.inf.ed.ac.uk/dts/pub/cai.pdf
   - 简介：CASL 采用"宽松（loose）语义"，一个规格对应一族模型，是"未定义即自由"在代数规范中的标准表达。**"一个规格=一族模型"是本子问题最核心的语义模型。**

2. **[重大] Foundations of Algebraic Specification and Formal Software Development**
   - 作者：D. Sannella, A. Tarlecki
   - 年份：2012 — Springer 专著
   - URL：https://www.springer.com/us/book/9783642173356
   - 简介：代数规格理论集大成之作，模型类语义与精化理论是"未定义即自由"的理论基础。

3. **[参考] On the role of nondeterminism and refinement in model-driven top-down development of software systems**
   - 基尔大学（Kiel）博士论文
   - URL：https://macau.uni-kiel.de/receive/diss_mods_00004303?lang=de
   - 简介：区分"固有非确定性"与"欠规格化（underspecification）"两类非确定性，并讨论其在逐步精化中的角色。

### B. 抽象状态机（Abstract State Machine / Evolving Algebras）

4. **[重大] Evolving Algebras: An Attempt to Discover Semantics**
   - 作者：Yuri Gurevich
   - 年份：1992 — Bulletin of EATCS（ASM 奠基论文）
   - URL：https://web.eecs.umich.edu/~gurevich/Opera/92.pdf
   - 简介：提出演化代数（ASM），用"抽象状态+状态转换"在任意抽象层次建模，天然支持未指定即自由。

5. **[参考] The Abstract State Machines Method**
   - ACM 文章（DOI: 10.1145/3811032，近期综述）
   - URL：https://dl.acm.org/doi/pdf/10.1145/3811032
   - 简介：ASM 方法综述，涵盖 Gurevich 新论题到行为理论的发展，说明 ASM 如何在任意抽象层次描述算法。

### C. 未定义行为的形式化（Undefined Behavior Formalization）— "未定义"的显式建模

6. **[重大] Defining the Undefinedness of C**
   - 作者：C. Hathhorn, C. Ellison, G. Rosu
   - 年份：2015 — PLDI
   - URL：https://fsl.cs.illinois.edu/publications/hathhorn-ellison-rosu-2015-pldi.pdf
   - 简介：用 K 框架给出可执行 C 语义，能捕获 77 种核心未定义行为，把"未定义"显式建模为语义卡死。**"未定义即自由"在主流语言中的权威形式化。**

7. **[参考] Educational Undefined Behavior Technical Report**
   - ISO/IEC WG14（C 标准委员会）
   - 年份：2022 — WG14 文档 n3308
   - URL：https://open-std.org/JTC1/SC22/WG14/www/docs/n3308.pdf
   - 简介：C 标准对 UB 的权威解释——"标准对该构造不施加任何要求"，即未定义即自由的官方定义。

8. **[参考] A Typed C11 Semantics for Interactive Theorem Proving**
   - 作者：R. Krebbers, J. Wiedijk
   - 年份：2015 — CPP
   - URL：https://robbertkrebbers.nl/research/ch2o/（CH2O 项目页）
   - 简介：在 Coq 中形式化 C11，把未定义/未指定行为建模为卡死或任意选择。

### D. Assume-Guarantee / 契约式设计 — "把未定义留给环境"

9. **[重大] Interface Automata**
   - 作者：L. de Alfaro, T. Henzinger
   - 年份：2001 — FSE
   - URL：https://luca.dealfaro.com/papers/01/FSE01.pdf
   - 简介：用"输入假设/输出保证"刻画组件交互，采用乐观组合与交替式精化，把环境行为留给假设而非规格。**A/G 契约的奠基性理论。**

10. **[重大] Specification and Design of (Parallel) Programs**
    - 作者：C.B. Jones
    - 年份：1983 — IFIP Congress
    - URL：https://www.vldb.org/dblp/db/indices/a-tree/j/Jones:Cliff_B=.html（dblp 索引）
    - 简介：rely/guarantee 方法奠基之作，用"依赖条件"描述环境干扰，是 assume-guarantee 思想的源头。

11. **[参考] Assume-Guarantee Verification for Interface Automata**
    - 作者：M. Emmi, D. Giannakopoulou, C. Pasareanu
    - 年份：2008 — FM
    - URL：https://raw.githubusercontent.com/michael-emmi/research-papers/master/conf-fm-EmmiGP08.pdf
    - 简介：给出接口自动机首个可靠且完备的 assume-guarantee 推理规则（兼容性/安全/精化）。

12. **[2024] Composition and Merging of Assume-Guarantee Contracts Are Tensor Products**
    - 年份：2024 — arXiv:2405.06052
    - URL：https://arxiv.org/html/2405.06052
    - 简介：用张量积刻画 A/G 契约的组合与合并，契约的"环境假设"正是把未定义部分留给环境。

13. **[参考] Assume/Guarantee Contracts for Dynamical Systems: Theory and Computational Tools**
    - 年份：2020 — arXiv:2012.12657
    - URL：https://arxiv.org/pdf/2012.12657v1
    - 简介：把 A/G 契约推广到动力系统，假设-保证分离使规格不必定义环境行为。

### E. 部分函数与未定义项的逻辑（Partial Functions / Free Logic / LPF）

14. **[参考] Free Logic**
    - Stanford Encyclopedia of Philosophy
    - URL：https://plato.stanford.edu/archives/sum2026/entries/logic-free/
    - 简介：自由逻辑允许非指称项，是"未定义项"的形式逻辑基础。

15. **[参考] A Semantic Analysis of Logics that Cope with Partial Terms**
    - 作者：C.B. Jones, D. Lover, P. Steggles
    - URL：https://scispace.com:443/pdf/a-semantic-analysis-of-logics-that-cope-with-partial-terms-2z79wctpkp.pdf
    - 简介：LPF（部分函数逻辑）把未定义处理为"空洞"（absence of value）而非具体错误值。

### F. Z 与部分规格 / 精化（Partial Specification in Z / Refinement）

16. **[参考] Consistency and refinement for partial specification in Z**
    - 作者：E. Boiten, J. Derrick, H. Bowman, M. Steen
    - 年份：1996 — FME'96
    - URL：https://kar.kent.ac.uk/21388/1/fme.pdf
    - 简介：用"最小公共精化（unification）"检查多视角部分规格的一致性，部分规格允许省略不关心的行为。

17. **[参考] Guards, Preconditions, and Refinement in Z**
    - 作者：R. Miarka, E. Boiten, J. Derrick
    - 年份：2000 — ZB 2000
    - URL：https://www.cs.kent.ac.uk/pubs/2000/1130/index.html
    - 简介：把 Z 操作在前置条件域外的行为建模为"任意结果"或"阻塞"，统一表达拒绝与欠规格化。

### G. Liveness vs Safety — "规格该约束什么"

18. **[重大] Defining Liveness**
    - 作者：B. Alpern, F.B. Schneider
    - 年份：1985 — Information Processing Letters 21(4):181-185（DOI: 10.1016/0020-0190(85)90056-0）
    - URL：https://lclem.github.io/bibliographer/articles/10.1016/0020-0190(85)90056-0/
    - 简介：给出 safety/liveness 的形式定义并证明任何性质=安全∩活性，为"规格该约束什么"提供分类学。**"避免无限膨胀"的分类学基础。**

### H. 时序逻辑与"不要过度约束"（TLA+）

19. **[重大] Specifying Systems: The TLA+ Language and Tools for Hardware and Software Engineers**
    - 作者：L. Lamport
    - 年份：2002 — 专著（Microsoft Research 全文 PDF）
    - URL：https://www.microsoft.com/en-us/research/wp-content/uploads/2018/05/book-02-08-08.pdf
    - 简介：TLA+ 权威著作，规格即"允许行为集合"，未约束的即自由。**"规格=允许行为集合"是本子问题最直接的工程化表达。**

### I. 非确定性与语义（Nondeterminism / Omnisemantics）

20. **[重大] Omnisemantics: Smooth Handling of Nondeterminism**
    - 作者：A. Erbsen, S. Gruetter, 等
    - 年份：2021 — PACMPL（ICFP）
    - URL：https://inria.hal.science/hal-03255472v3
    - 简介：用"起始状态→结果集合"的 omni 风格判断优雅处理操作语义中的非确定性。**处理非确定性的现代语义框架。**

21. **[参考] Refining UML Interactions with Underspecification and Nondeterminism**
    - 作者：Ø. Haugen, K.E. Husa, R.K. Runde, K. Stølen
    - 年份：2005 — Nordic Journal of Computing
    - URL：https://www.breibakk.no/kst/Articles/2005.NORDIC-JOURNAL.pdf
    - 简介：区分欠规格化（实现只需满足一个备选行为）与固有非确定性，并定义相应精化。

### J. Don't-Care 条件（硬件/逻辑综合）— 概念源头

22. **[重大] Don't Care Set Specifications in Combinational and Synchronous Logic Circuits**
    - 作者：M. Damiani, G. De Micheli
    - 年份：1993 — IEEE TCAD 12(3):365-388
    - URL：https://dl.acm.org/doi/10.1109/43.215001
    - 简介：组合与时序逻辑中 don't-care 条件规格与计算的统一框架，don't-care 即优化自由度。**"Don't-Care"术语的权威定义来源。**

### K. 未指定项语义（ACSL / 规格语言）

23. **[2024] A Semantics of Structures, Unions, and Underspecified Terms for Formal Specification**
    - 年份：2024 — ACM（DOI: 10.1145/3644033.3644380）
    - URL：https://dl.acm.org/doi/pdf/10.1145/3644033.3644380
    - 简介：给 ACSL 中未指定（underspecified）项以"良定义但欠规格"的语义，基于 Krebbers 的 C 语义。

### L. 新增（2026 年，近三月为主）— 欠规格化与精化的最新进展

24. **[近3月] Verifiable Auto-Formalization of Mathematics Using a Relaxed Natural Formal Language**
    - 作者：Zhicheng Hui, Lihan Xie, Xingzhi Qi, Zhehao Li, Yingjun Lan, Qinxiang Cao
    - 年份：2026（arXiv:2606.24443，2026-06-23）
    - URL：https://arxiv.org/abs/2606.24443
    - 简介：提出"宽松自然形式语言（Relaxed NFL）"作为自动形式化中间层，明确允许"部分指定的表达式与命题"（partial specification），把歧义/隐含解析推迟到后续 elaboration 阶段。**与本子问题直接相关：如何显式声明"未定义即自由"。**

25. **[近3月] Combining Axiomatic Models for Refinement Proofs**
    - 作者：Suha Orhun Mutluergil, Alperen Dogan
    - 年份：2026（arXiv:2606.27916，2026-06-26）
    - URL：https://arxiv.org/abs/2606.27916
    - 简介：统一 Hoare / Incorrectness / Lisbon / Necessary-Preconditions 四种公理逻辑，用 forward/backward simulation 刻画并传递 refinement proof 中的安全性质。**与 refinement freedom 直接相关。**

26. **[近3月] Neurosymbolic Auditing of Natural-Language Software Requirements（VERIMED）**
    - 作者：Bethel Hall, William Eiers
    - 年份：2026（arXiv:2605.13817，2026-05-13）
    - URL：https://arxiv.org/abs/2605.13817
    - 简介：LLM+SMT 审计自然语言需求的歧义、不一致、vacuousness 与 underspecification，用随机形式化差异作为歧义信号。**"未定义即自由"的审计/检测工具思路。**

27. **[2026] SpecRL: Reinforcement Learning with Test-Based Completeness Rewards for Formal Specification Synthesis**
    - 年份：2026（arXiv:2604.05820）
    - URL：https://arxiv.org/abs/2604.05820v2
    - 简介：针对"弱规格如 ensures true 过于宽松"（即 don't-care/loose semantics 问题），用负测试完备性奖励在 Dafny 中排序规格候选。**直接回应"避免规格无限膨胀/过度宽松"。**

28. **[2026] Intent-aligned Formal Specification Synthesis via Traceable Refinement（VeriSpecGen）**
    - 年份：2026（arXiv:2604.10392）
    - URL：https://arxiv.org/html/2604.10392v1
    - 简介：在 Lean 中通过需求级归因与局部修复做可追溯 refinement 的规格合成（Verina SpecGen 上 86.6%）。

29. **[2026] What Prompts Don't Say: Understanding and Managing Underspecification in LLM Prompts**
    - 年份：2026（ACL 2026 Findings）
    - URL：https://aclanthology.org/2026.findings-acl.441.pdf
    - 简介：系统分析 LLM 提示词 underspecification：未指定需求常被默认推断（41.1%）但脆弱，跨模型/提示词变化时回归率 2 倍。**underspecification 的实证研究。**

30. **[2026] Lenses for Partially-Specified States (Extended Version)**
    - 作者：Kazutaka Matsuda, Minh Nguyen, Meng Wang
    - 年份：2026（ESOP 2026，arXiv:2601.04573）
    - URL：https://arxiv.org/abs/2601.04573
    - 简介：提出 partial-state lenses，允许源/视图状态部分指定，用偏序合并多视图更新意图，形式化"部分指定感知的良行为性"。

31. **[近3月] ConVer: Using Contracts and Loop Invariant Synthesis for Scalable Formal Software Verification**
    - 年份：2026（arXiv:2605.27051）
    - URL：https://arxiv.org/html/2605.27051v1
    - 简介：LLM 从系统性质合成函数契约，CEGAR-CEGIS 循环中经 SMART ICE 细化契约，做大规模 C 程序形式验证。

32. **[2026] SpecSyn: LLM-based Synthesis and Refinement of Formal Specifications for Real-world Program Verification**
    - 年份：2026（arXiv:2604.21570）
    - URL：https://arxiv.org/html/2604.21570v1
    - 简介：面向真实程序验证的形式规格（如 ACSL）合成与细化框架。

## 二、开源项目（活跃度核实至 2026-08-15）

### 活跃 / 高价值

1. **TLA+（tlaplus）** — 活跃（2026-07-16 提交，含 CVE-2025-7962 修复；稳定版 v1.7.4）
   - URL：https://github.com/tlaplus/tlaplus
   - 简介：TLC 模型检查器 + TLA+ Toolbox IDE（含 TLAPS 证明系统、SANY 解析器、PlusCal 翻译器）。注意：Toolbox GUI 已弃用，官方推荐 VS Code 扩展。
   - 相关性：TLA+"规格不约束即自由"理念的官方工具链。

2. **Maude** — 活跃（2026-07-24 提交，alpha165 发布）
   - URL：https://github.com/maude-lang/Maude
   - 简介：基于重写逻辑的规格/编程语言。
   - 相关性：可执行代数规格，membership equational logic 支持部分性，重写逻辑天然表达非确定性。

3. **Why3** — 活跃（2026-07-21 提交；最新发布 1.8.2）
   - URL：https://github.com/AdaCore/why3（官方 GitLab: gitlab.inria.fr/why3/why3）
   - 简介：程序验证平台，WhyML 规格+编程语言，对接多个 SMT/证明器。
   - 相关性：前置/后置条件规格中未指定部分的验证（Frama-C、SPARK 的后端）。

4. **ASMETA（Asmeta）** — 活跃（2026-07-16 提交；2026-02 发布 26.02）
   - URL：https://github.com/asmeta/asmeta
   - 简介：ASM 工具集：AsmetaL 编辑器/编译器、模拟器 AsmetaS、基于 NuSMV 的模型检查器 AsmetaSMV、精化证明器 AsmRefProver 等。
   - 相关性：直接支持 ASM 的逐步精化与未指定建模，精化证明器可验证抽象→具体步骤。

5. **Pacti** — 新增（2025 ACM 论文配套工具）
   - URL：https://dl.acm.org/doi/pdf/10.1145/3704736
   - 简介：可扩展的契约式组合分析与设计工具，实现 assume-guarantee 契约的合并/组合/refinement 等操作。
   - 相关性：A/G 契约的现代计算工具。

### 低活跃 / 停更

6. **Hets（The Heterogeneous Tool Set）** — 低活跃（2026 年无提交，最近 2025-10-07）
   - URL：https://github.com/spechub/Hets/
   - 简介：异构规格工具集，支持 CASL/HetCASL 及多逻辑（Isabelle、Maude、OWL 等）。
   - 说明：CASL 宽松语义的主要工具实现，但近一年基本停滞。

7. **CafeOBJ** — 停更（最近提交 2024-11-19，1.6.2 发布）
   - URL：https://github.com/CafeOBJ/cafeobj
   - 说明：宽松语义与执行语义结合的代数规格语言，仓库约 1.5 年未动。

8. **CH2O** — 停更（最近提交 2022-01-26）
   - URL：https://github.com/robbertkrebbers/ch2o
   - 说明：Coq 中形式化的 ISO C11 语义，未定义/未指定行为形式化的基准项目，但已停滞。

9. **K framework c-semantics** — 停更（语义提交 2021 年）
   - URL：https://github.com/kframework/c-semantics
   - 说明：继任者为商业工具 RV-Match（runtimeverification.com/match），开源版已停滞。

## 三、审查结论

- **理论根基**：CASL 宽松语义（一个规格=一族模型）+ TLA+（规格=允许行为集合）+ Alpern-Schneider（safety/liveness 分类学）构成"未定义即自由"的三大理论支柱。
- **2026 新动向**：近三个月出现一批直接处理"欠规格化"的新工作——Relaxed NFL（部分指定中间层）、VERIMED（underspecification 审计）、SpecRL（用完备性奖励对抗过度宽松规格），说明"未定义即自由"正从理论走向 LLM 时代的工具化。
- **工具生态**：TLA+/Maude/Why3/ASMETA 仍活跃；Hets/CafeOBJ/CH2O/K-c-semantics 已停滞，不建议作为原型基础。
