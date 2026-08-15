# 子问题二建议：Don't-Care 区的显式声明与验证

## 一、核心结论（基于证据）

1. **"未定义即自由"已有成熟的数学刻画，且两条主流路线收敛于同一思想**：CASL 宽松语义"一个规格 = 一族模型"（Mossakowski 等），与 TLA+ "规格 = 允许行为集合、未约束即自由"（Lamport《Specifying Systems》）。验证语义随之确定：性质成立当且仅当在该规格的所有模型/所有允许行为上成立。
2. **约束范围有上界定理**：Alpern-Schneider《Defining Liveness》证明任何时序性质 = 安全 ∩ 活性。规格只需声明这两类性质，其余一律默认 don't-care——这是"避免无限膨胀"的分类学基础。
3. **"未定义"必须显式声明而非隐式推断**：C 标准的官方立场是"对该构造不施加任何要求"（WG14 n3308），而《Defining the Undefinedness of C》用可执行语义把 77 种 UB 建模为 stuck，证明 don't-care 边界可被机器执行。实证方面，《What Prompts Don't Say》显示隐式默认推断脆弱（跨模型回归率翻倍），支持显式标注。
4. **必须区分不同种类的"自由"**：固有非确定性 vs 欠规格化（基尔博士论文、UML 精化论文）；未定义=卡死（禁止） vs 未指定=任意选择（自由）（CH2O/Krebbers）。混为一谈会导致语义污染。
5. **膨胀控制的三条工程路径**：分类学限域（safety/liveness）、委托给环境（Interface Automata / rely-guarantee 的假设-保证分离）、部分指定+延迟解析（Relaxed NFL，已核实其 elaboration 阶段将宽松表达转为语义确定的 Core NFL 并保持每步可验证）。

## 二、对 Spec 语言设计的具体建议

**don't-care 语法**：
- 提供一等公民的显式 don't-care 标注，并区分三类：输出自由（欠规格）、不可达状态、可忽略输出——映射 Damiani & De Micheli 的 SDC/ODC 分类（《Don't Care Set Specifications》）。
- 双轨语义标注：`undefined`（越界即 stuck/报错）与 `unspecified`（任选其一皆合法），依据 CH2O 与 K 框架 C 语义的卡死/任意选择建模。
- 允许部分指定的表达式，配套 elaboration 阶段延迟解析，依据 Relaxed NFL。

**语义模型选择**：
- 内核采用宽松语义（一族模型）+ 允许行为集合（依据 CASL、TLA+ 专著）；验证即"对所有模型全称量化"，与 Why3 VCGen 的验证模式契合。
- 接口层用 assume-guarantee 契约把环境行为的 don't-care 委托给假设，规格本体不定义环境（依据 Interface Automata、Jones rely/guarantee、Pacti）。
- 表达式级未定义项采用 LPF"空洞"语义，避免未定义值污染整个表达式（依据 Jones/Lover/Steggles）。
- 前置条件域外提供"自由"与"阻塞"两种显式模式供编写者选择（依据 Z 中 guards/preconditions 研究）。

**膨胀控制机制**：
- 语言层仅接受 safety 与 liveness 性质声明，其余自动为 don't-care（依据 Defining Liveness）。
- 引入完备性度量对抗"过度宽松"（如 ensures true 型空规格）：借鉴 SpecRL 的负测试完备性奖励作为质量分；借鉴 VERIMED 的随机形式化差异审计欠规格化，作为编辑器实时提示。
- 用 refinement 逐步消解欠规格化自由度（refinement-as-implication，与子问题三衔接）。

## 三、工具采用建议

- **采用**：TLA+ 工具链（TLC，活跃至 2026-07）作为行为集语义与模型检查的参照；Why3（活跃，VCGen+多 SMT 后端）作为验证后端架构样板；Pacti 作为 A/G 契约运算的参考实现。
- **仅借鉴不采用**：Maude、ASMETA（重写逻辑/ASM 精化思想有价值但范式偏重）；Hets/CafeOBJ/CH2O/K-c-semantics——CASL 语义的主要实现均已停滞，理论需自研落地，不可作为原型基础。

## 四、风险与开放问题

1. **标注负担与隐式默认的平衡**：强制显式 don't-care 标注增加编写成本，过松则退化为隐式推断；需要审计工具（VERIMED 式）辅助决定何时必须标注。
2. **自由与空洞验证的矛盾**：规格过宽导致验证 vacuous，过窄导致膨胀，完备性度量尚无公认标准（SpecRL 仅为排序启发）。
3. **状态爆炸**：允许行为集合的模型检查受限于有限实例，需符号后端（Apalache 类）支撑。
4. **多视角 don't-care 的一致性**：最小公共精化（Z unification）与 partial-state lenses 仍是研究阶段方法，工程化程度低。
