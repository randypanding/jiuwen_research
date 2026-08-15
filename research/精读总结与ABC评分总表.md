# LLM 生成代码差分测试引擎：文献与开源项目精读总结及 ABC 评分总表

> 生成时间：2026-08-15
> 覆盖范围：工作区 `differential-testing-research/` 下 6 个方向文件中的全部论文与开源项目（6 个子 agent 分两批并行精读）
> 本文件为最终交付物，包含：评分标准、评分汇总表、逐条目精读总结。

## 研究问题

如何为 LLM 生成的代码实例构建高效、高覆盖率的差分测试（Differential Testing）引擎？

三个子问题：
1. **行为等价性的自动判据**：如何定义和自动化判断两个代码实例在功能上等价（而非仅仅输出相同）？
2. **测试输入的智能生成**：如何利用 LLM 或 fuzzing 技术，自动生成能暴露行为差异的测试用例？
3. **差分测试与属性测试的融合**：如何将差分测试与基于属性的测试（如 H2）结合，形成更完整的验证闭环？

## 评分标准

| 等级 | 含义 |
| --- | --- |
| **A** | 采用价值高：直接回答研究问题（一个或多个子问题），方法成熟、适应性强，可直接借鉴或集成到差分测试引擎设计 |
| **B** | 有参考价值：部分回答研究问题，或需改造/适配后才能采用 |
| **C** | 相关性弱：仅作背景参考，或与研究问题关联度低 |

## 评分汇总表

### 方向 1：针对 LLM 生成代码的差分测试与评测

| 条目 | 类型 | 等级 |
| --- | --- | --- |
| CodeT: Code Generation with Generated Tests | 论文 | A |
| SelfEvolve（IBM 差分测试版） | 论文 | B |
| Self-Debugging | 论文 | B |
| Coder-Reviewer Reranking | 论文 | B |
| LEVER | 论文 | A |
| MBR-Exec | 论文 | A |
| CodeRanker (Fault-Aware Neural Code Rankers) | 论文 | B |
| RankEF (Sifting through the Chaff) | 论文 | B |
| Revisit Self-Debugging with Self-Generated Tests | 论文 | B |
| ACE (Adversarial Unit Test Generation) | 论文 | A |
| TitanFuzz | 论文 | B |
| DLLens | 论文 | B |
| DiffSpec | 论文 | A |
| LWDIFF | 论文 | B |
| RustAssure | 论文 | A |
| Syzygy | 论文 | B |
| Kaizen | 论文 | A |
| tHinter | 论文 | A |
| Fuzpiler | 论文 | B |
| EvalPlus | 论文 | A |
| LiveCodeBench | 论文 | B |
| BigCodeBench | 论文 | B |
| TestEval | 论文 | B |
| RepoExec | 论文 | B |
| microsoft/CodeT | 开源项目 | A |
| evalplus/evalplus | 开源项目 | A |
| bigcode-evaluation-harness | 开源项目 | B |
| LiveCodeBench | 开源项目 | B |
| bigcodebench | 开源项目 | B |
| TitanFuzz | 开源项目 | B |
| DLLens | 开源项目 | B |
| mbr-exec | 开源项目 | A |
| coder_reviewer_reranking | 开源项目 | B |
| lever | 开源项目 | B |
| cruxeval | 开源项目 | B |
| SWE-bench | 开源项目 | B |
| DS-1000 | 开源项目 | B |
| human-eval | 开源项目 | B |

### 方向 2：程序行为/语义等价性的自动判据

| 条目 | 类型 | 等级 |
| --- | --- | --- |
| Semantic Program Alignment for Equivalence Checking | 论文 | A |
| Relational verification using product programs | 论文 | A |
| A Monadic Framework for Relational Verification | 论文 | B |
| Exploiting Synchrony and Symmetry in Relational Verification | 论文 | B |
| An Algebra of Alignment for Relational Verification | 论文 | B |
| A language-independent proof system for full program equivalence | 论文 | B |
| Checking equivalence in a non-strict language (NEBULA) | 论文 | B |
| HEC (Equality Saturation) | 论文 | A |
| Alive2 | 论文 | A |
| Regression Verification | 论文 | A |
| Differential Symbolic Execution | 论文 | A |
| Partition-Based Regression Verification | 论文 | B |
| Csmith | 论文 | A |
| Semantic Code Search via Equational Reasoning (Yogo) | 论文 | B |
| Program Synthesis with Equivalence Reduction | 论文 | B |
| code2vec | 论文 | B |
| code2seq | 论文 | B |
| CodeBERT | 论文 | B |
| GraphCodeBERT | 论文 | B |
| ASTNN | 论文 | B |
| CCLearner | 论文 | B |
| EquiBench | 论文 | A |
| Disproving Program Equivalence with LLMs (ProbeGen) | 论文 | A |
| On Neural Network Equivalence Checking using SMT | 论文 | C |
| Emerge | 论文 | A |
| code2vec | 开源项目 | B |
| code2seq | 开源项目 | B |
| ASTNN | 开源项目 | B |
| CCLearner | 开源项目 | B |
| CodeBERT | 开源项目 | B |
| SymDiff | 开源项目 | A |
| Alive2 | 开源项目 | A |
| Csmith | 开源项目 | A |
| KLEE | 开源项目 | A |
| Yogo | 开源项目 | B |
| roojs/semantic-code-search | 开源项目 | B |
| sturdy-dev/semantic-code-search | 开源项目 | B |

### 方向 3：测试输入智能生成 + 差分测试与属性测试融合

| 条目 | 类型 | 等级 |
| --- | --- | --- |
| TitanFuzz | 论文 | A |
| WhiteFox | 论文 | A |
| FuzzGPT | 论文 | B |
| ChatFuzz | 论文 | B |
| CodaMosa | 论文 | B |
| TestPilot | 论文 | B |
| ChatUniTest | 论文 | B |
| CoverUp | 论文 | A |
| ELFuzz | 论文 | B |
| Mokav | 论文 | A |
| DiffSpec | 论文 | A |
| MutGen | 论文 | B |
| CodeGraphGPT (CKGFuzzer) | 论文 | B |
| PromeFuzz | 论文 | B |
| SAFuzz | 论文 | B |
| Kaizen | 论文 | A |
| NEZHA | 论文 | A |
| DLFuzz | 论文 | B |
| Evolutionary Generative Fuzzing for Kotlin Compiler | 论文 | B |
| Towards Translating Real-World Code with LLMs (FLOURINE) | 论文 | A |
| Differential Fuzzing-Based Evaluation of Functional Equivalence | 论文 | A |
| LLMs in the Heart of Differential Testing (LLMeDiff) | 论文 | B |
| 基于大语言模型的模糊测试研究综述 | 论文 | B |
| A Review of LLMs for Automated Test Case Generation | 论文 | B |
| On the Challenges of Fuzzing via LLMs | 论文 | C |
| QuickCheck | 论文 | A |
| To Kill a Mockingbird | 论文 | A |
| Mica | 论文 | A |
| Property-Based Testing in Practice | 论文 | B |
| Empirical Evaluation of PBT in Python | 论文 | B |
| PBT Across Four Environments | 论文 | B |
| How Developers Implement PBT | 论文 | C |
| PBT-Bench | 论文 | A |
| Agentic Property-Based Testing | 论文 | A |
| PropTest | 论文 | B |
| METAL | 论文 | B |
| MetaFOE | 论文 | A |
| Towards Generating Executable Metamorphic Relations | 论文 | B |
| Variable Discovery with LLMs for MT | 论文 | B |
| Bidirectional Empowerment of MT and LLMs (survey) | 论文 | B |
| Drowzee | 论文 | C |
| From Prompts to Properties | 论文 | B |
| Testing Noninterference, Quickly | 论文 | C |
| Hypothesis | 开源项目 | A |
| QuickCheck (Haskell) | 开源项目 | A |
| proptest | 开源项目 | A |
| quickcheck (Rust) | 开源项目 | B |
| jqwik | 开源项目 | B |
| AFL++ | 开源项目 | A |
| libFuzzer | 开源项目 | A |
| EvoSuite | 开源项目 | B |
| Randoop | 开源项目 | B |
| KLEE | 开源项目 | B |
| WhiteFox | 开源项目 | A |
| TitanFuzz | 开源项目 | A |
| FuzzGPT | 开源项目 | B |
| CodaMosa | 开源项目 | B |
| Cryptofuzz | 开源项目 | A |

### 方向 4：经典差分测试基础 + 编译器/解释器差分测试

| 条目 | 类型 | 等级 |
| --- | --- | --- |
| Differential Testing for Software (McKeeman) | 论文 | A |
| Translation Validation | 论文 | B |
| The Oracle Problem in Software Testing (survey) | 论文 | A |
| A Survey on Metamorphic Testing | 论文 | A |
| Finding and Understanding Bugs in C Compilers (Csmith) | 论文 | A |
| Taming Compiler Fuzzers | 论文 | B |
| Compiler Validation via Equivalence Modulo Inputs (EMI) | 论文 | A |
| Many-core Compiler Fuzzing | 论文 | B |
| Finding Deep Compiler Bugs via Guided Mutation (Athena) | 论文 | A |
| Toward Understanding Compiler Bugs in GCC and LLVM | 论文 | B |
| Random Testing with YARPGen | 论文 | A |
| A Survey of Compiler Testing | 论文 | A |
| Fuzzing with Code Fragments (LangFuzz) | 论文 | A |
| Test Transplantation and Differential Testing (JS) | 论文 | A |
| COMFORT | 论文 | A |
| JIT-PICKING | 论文 | A |
| FuzzJIT | 论文 | A |
| DUMPLING | 论文 | A |
| Coverage-Directed Differential Testing of JVM (classfuzz) | 论文 | A |
| Deep Differential Testing of JVM (classming) | 论文 | A |
| Csmith | 开源项目 | A |
| YARPGen | 开源项目 | A |
| AFL | 开源项目 | B |
| AFL++ | 开源项目 | B |
| libFuzzer | 开源项目 | B |
| KLEE | 开源项目 | B |
| Fuzzilli | 开源项目 | A |
| Nautilus | 开源项目 | A |
| Grammarinator | 开源项目 | A |
| JQF | 开源项目 | A |
| jsfunfuzz / funfuzz | 开源项目 | B |
| GraphicsFuzz (GLF) | 开源项目 | B |

### 方向 5：LLM 代码自我修复 / 自调试 / 执行反馈

| 条目 | 类型 | 等级 |
| --- | --- | --- |
| LDB (Debug like a Human) | 论文 | A |
| LeDex | 论文 | B |
| RLEF | 论文 | B |
| PerfCodeGen | 论文 | A |
| FixAudit | 论文 | A |
| AgentForge | 论文 | B |
| CYCLE | 论文 | B |
| SelfEvolve | 论文 | B |
| Self-Edit | 论文 | A |
| CodeChain | 论文 | B |
| MBR-Exec | 论文 | A |
| CodeRanker | 论文 | B |
| RankEF | 论文 | B |
| Top Pass | 论文 | B |
| RepairAgent | 论文 | B |
| Agentic Program Repair from Test Failures | 论文 | B |
| RLTF | 论文 | B |
| CodeRL | 论文 | B |
| StepCoder | 论文 | B |
| InterCode | 论文 | B |
| SWE-agent | 开源项目 | A |
| OpenHands | 开源项目 | A |
| Aider | 开源项目 | B |
| AutoCodeRover | 开源项目 | A |
| Agentless | 开源项目 | A |
| RepairAgent | 开源项目 | B |
| PerfCodeGen | 开源项目 | A |
| InterCode | 开源项目 | B |
| Web-Based Multi-Round Dialogue Code Repair Agent | 开源项目 | C |
| Agentic Code Fixer | 开源项目 | B |

### 方向 6：程序合成验证 + 形式化方法用于 LLM 代码

| 条目 | 类型 | 等级 |
| --- | --- | --- |
| SymDiff | 论文 | A |
| Relational Verification Using Product Programs | 论文 | A |
| Thirty-seven Years of Relational Hoare Logic | 论文 | B |
| A Relational Program Logic with Data Abstraction | 论文 | B |
| S4Eq | 论文 | B |
| KLEE | 论文 | A |
| LLM Powered Symbolic Execution (AutoBug) | 论文 | A |
| Cottontail | 论文 | A |
| Hybrid Concolic Testing with LLMs | 论文 | B |
| Inference-Time Code Selection via SEP | 论文 | A |
| SpecGen | 论文 | B |
| DafnyBench | 论文 | B |
| VerifyThisBench | 论文 | B |
| CLEVER | 论文 | B |
| VERINA | 论文 | A |
| VeriContest | 论文 | B |
| ATLAS | 论文 | B |
| AlphaVerus | 论文 | B |
| Program Semantic Inequivalence Game (SInQ) | 论文 | A |
| Towards Verified Code Reasoning by LLMs | 论文 | A |
| Clover | 论文 | A |
| KLEE | 开源项目 | A |
| Z3 | 开源项目 | A |
| CBMC | 开源项目 | A |
| SeaHorn | 开源项目 | B |
| Why3 | 开源项目 | B |
| Boogie | 开源项目 | B |
| SymDiff | 开源项目 | A |
| angr | 开源项目 | B |
| Rosette | 开源项目 | B |
| ConcoLLMic | 开源项目 | A |
| congruent-eq | 开源项目 | A |
| Dafny | 开源项目 | B |

## 统计

- 论文合计：约 151 篇（含跨方向重复条目，如 TitanFuzz、DiffSpec、Kaizen、SymDiff、KLEE、MBR-Exec、CodeRanker、RankEF 等）
- 开源项目合计：约 75 个（含跨方向重复）
- A 级：约 60+ 项；B 级：约 100+ 项；C 级：约 8 项

---

# 详细精读总结与评分

### 方向 1：针对 LLM 生成代码的差分测试与评测

#### 论文（24 篇）

##### [A] CodeT: Code Generation with Generated Tests
- 类型：论文
- 链接：https://arxiv.org/abs/2207.10397
- 总结：微软研究院提出的奠基性工作，用同一 LLM 同时生成代码与测试用例，通过"代码-测试双一致"（dual execution agreement）筛选出正确代码。该方法将生成测试作为验证 LLM 代码正确性的核心手段，无需额外标注数据。实验在 HumanEval、MBPP 等基准上显著提升 pass@k。其"用生成测试验证生成代码"的思路正是差分测试引擎中行为判据的直接来源。
- 评分理由：直接回答子问题 1（行为等价判据）与子问题 2（测试输入生成），方法成熟、可复现，官方实现可用，A 级。

##### [B] SelfEvolve（IBM 差分测试版）
- 类型：论文
- 链接：https://arxiv.org/abs/2306.02907
- 总结：IBM 提出的代码演化方法，针对 LLM 代码翻译场景，用 LLM 生成测试用例对翻译后的代码做差分测试，并迭代修复发现的翻译错误。它把差分测试作为翻译正确性的判据，与本方向最直接相关。但工作聚焦翻译场景，通用性有限，且未提供官方开源实现。
- 评分理由：部分回答子问题 1 与 2，思路可直接借鉴，但需改造适配到通用代码生成场景，B 级。

##### [B] Self-Debugging: Teaching Large Language Models to Self-Debug
- 类型：论文
- 链接：https://arxiv.org/abs/2304.05128
- 总结：Google 提出的自调试框架，让 LLM 执行自己生成的代码，基于执行结果（如单元测试反馈）生成解释并迭代修复。它展示了执行反馈对提升代码正确性的关键作用。其"执行-反馈-修复"闭环与差分测试引擎的迭代验证思路互补。
- 评分理由：部分回答子问题 1，提供执行反馈范式参考，但与差分测试的直接关联较弱，需结合使用，B 级。

##### [B] Coder-Reviewer Reranking for Code Generation
- 类型：论文
- 链接：https://arxiv.org/abs/2211.16490
- 总结：CMU/Google 提出的代码生成器+评审器双模型架构，评审器对候选代码打分重排，并结合可执行性过滤。通过执行结果筛选可运行候选，提升最终代码质量。为"生成-筛选-重排"流水线提供了参考。
- 评分理由：部分回答子问题 1，重排思路可借鉴，但依赖额外评审模型训练，适配成本较高，B 级。

##### [A] LEVER: Learning to Verify Language-to-Code Generation with Execution
- 类型：论文
- 链接：https://arxiv.org/abs/2302.08468
- 总结：Yale/Google 提出训练验证器（verifier）基于程序执行结果判断代码正确性并重排候选。验证器融合了程序特征与执行结果特征，显著提升代码生成准确率。其"执行感知验证"是差分测试引擎中行为判据的机器学习实现路径。
- 评分理由：直接回答子问题 1，方法成熟、效果显著，可集成到引擎作为可学习判据，A 级。

##### [A] MBR-Exec: Natural Language to Code Translation with Execution
- 类型：论文
- 链接：https://arxiv.org/abs/2206.07581
- 总结：FAIR 提出用执行结果做最小贝叶斯风险（MBR）解码，从候选代码中选择通过测试的代码。它将执行反馈融入解码过程，显著提升代码翻译正确性。官方实现可用，是"执行选择"范式的经典代表。
- 评分理由：直接回答子问题 1，方法简洁有效、可复现，官方实现可用，可直接借鉴为引擎的候选选择模块，A 级。

##### [B] Fault-Aware Neural Code Rankers (CodeRanker)
- 类型：论文
- 链接：https://arxiv.org/abs/2211.09427
- 总结：微软研究院提出训练神经排序器预测代码正确性，并预测错误类型（fault-aware），无需执行即可筛选代码。它在多个代码生成基准上优于执行无关基线。为"无执行判据"提供了思路。
- 评分理由：部分回答子问题 1，无需执行的排序器可作为执行判据的补充，但精度有限，需结合执行，B 级。

##### [B] RankEF (Sifting through the Chaff)
- 类型：论文
- 链接：https://dl.acm.org/doi/10.1145/3691620.3695000
- 总结：ASE 2024 工作，利用执行反馈做多任务学习改进代码候选排序，从大量候选中筛选正确代码。它强调执行反馈信息对排序的增益。可作为候选重排模块的参考。
- 评分理由：部分回答子问题 1，执行反馈排序思路可借鉴，但依赖特定训练流程，B 级。

##### [B] Revisit Self-Debugging with Self-Generated Tests for Code Generation
- 类型：论文
- 链接：https://arxiv.org/abs/2501.12793
- 总结：系统研究"自生成测试+执行反馈"用于代码自调试的两种范式，分析其适用条件与失效场景。它为自调试与测试生成结合提供了实证分析。对引擎设计中的反馈回路有参考价值。
- 评分理由：部分回答子问题 1 与 2，实证分析有价值，但未提出新方法，B 级。

##### [A] ACE: Self-Evolving LLM Coding Framework via Adversarial Unit Test Generation and Preference Optimization
- 类型：论文
- 链接：https://arxiv.org/abs/2605.16299
- 总结：2026 年提出的自进化编码框架，采用求解器-对抗器架构，用对抗性单元测试发现执行级失败并驱动模型自进化，结合偏好优化。对抗测试生成能暴露更多行为差异，与差分测试目标高度契合。
- 评分理由：直接回答子问题 2，对抗式测试生成方法新颖、针对性强，A 级。

##### [B] TitanFuzz: Large Language Models Are Zero-Shot Fuzzers
- 类型：论文
- 链接：https://arxiv.org/abs/2305.12445
- 总结：UIUC 提出用 LLM 作为零样本模糊器，为深度学习库生成输入程序做差分/模糊测试，发现 65 个真实 bug。它展示了 LLM 生成测试输入的能力。其测试输入生成思路可用于引擎。
- 评分理由：部分回答子问题 2，LLM 生成测试输入方法可借鉴，但面向 DL 库场景，需适配，B 级。

##### [B] DLLens: Enhancing Differential Testing With LLMs For Testing Deep Learning Libraries
- 类型：论文
- 链接：https://arxiv.org/abs/2406.07944
- 总结：UIUC 提出用 LLM 合成跨库 API 对应（counterpart）做差分测试，增强对深度学习库的差分测试能力。核心是自动发现 API 对应关系。其"自动建立对应关系"思路对差分测试引擎有价值。
- 评分理由：部分回答子问题 2，对应关系合成方法可借鉴，但场景特定，B 级。

##### [A] DiffSpec: Differential Testing with LLMs using Natural Language Specifications and Code Artifacts
- 类型：论文
- 链接：https://arxiv.org/abs/2410.04249
- 总结：用自然语言规范+代码工件引导 LLM 生成差分测试，应用于 eBPF 与 Wasm 验证器。它将规范知识注入测试生成，提升差分测试的有效性。为引擎提供了"规范引导测试生成"的范式。
- 评分理由：直接回答子问题 2，方法通用、可迁移到代码生成场景，A 级。

##### [B] LWDIFF: An LLM-Assisted Differential Testing Framework for WebAssembly Runtimes
- 类型：论文
- 链接：https://www.computer.org/csdl/proceedings-article/icse/2025/056900a769/251mHCEMl6U
- 总结：ICSE 2025 工作，用 LLM 从 Wasm 规范提取知识、生成多阶段差分测试，测试 WebAssembly 运行时。它展示了 LLM 理解规范并生成差分测试的流程。为规范驱动的差分测试提供参考。
- 评分理由：部分回答子问题 2，规范提取思路可借鉴，但面向 Wasm 场景，B 级。

##### [A] RustAssure: Differential Symbolic Testing for LLM-Transpiled C-to-Rust Code
- 类型：论文
- 链接：https://www.semanticscholar.org/paper/b1de38975f0ab5e25f9dcea99572326aefaa15a2
- 总结：对 LLM 转译的 C→Rust 代码做差分符号测试，验证翻译等价性。它将差分测试与符号执行结合，能系统发现翻译引入的行为差异。为"LLM 翻译代码等价性验证"提供了强方法。
- 评分理由：直接回答子问题 1 与 3，差分+符号执行融合方法成熟，A 级。

##### [B] Syzygy: Dual Code-Test C to (safe) Rust Translation using LLMs and Dynamic Analysis
- 类型：论文
- 链接：https://www.semanticscholar.org/paper/b1de38975f0ab5e25f9dcea99572326aefaa15a2
- 总结：UC Berkeley 提出联合翻译代码与测试，用动态分析信息验证 C→Rust 翻译等价性。它强调测试与代码协同翻译。为翻译等价性验证提供动态分析路径。
- 评分理由：部分回答子问题 1，动态分析思路可借鉴，但依赖联合翻译流程，B 级。

##### [A] Kaizen: Metamorphic Fuzzing and Differential Testing for LLM-Translated HPC Applications
- 类型：论文
- 链接：https://arxiv.org/abs/2607.04058
- 总结：2026 年提出对 LLM 翻译的 CUDA→OpenMP 代码做变形模糊+差分测试，验证并行代码翻译等价性。它融合变形测试与差分测试，覆盖 HPC 场景。为高性能代码差分测试提供范式。
- 评分理由：直接回答子问题 1、2、3，变形+差分融合方法全面，A 级。

##### [A] tHinter: Guided Debugging of Auto-Translated Code Using Differential Testing
- 类型：论文
- 链接：https://arxiv.org/abs/2501.09475
- 总结：用 AFL++ 生成测试并对自动翻译代码做差分，定位导致输出差异的错误行，辅助调试翻译错误。它将差分测试与模糊测试结合，并输出可操作的调试提示。为引擎提供"定位差异根源"的能力。
- 评分理由：直接回答子问题 2 与 3，差分+模糊+定位一体化，实用性强，A 级。

##### [B] Fuzpiler: 基于 LLM 翻译与差分测试的跨语言编译器模糊测试
- 类型：论文
- 链接：http://netinfo-security.org/CN/10.3969/j.issn.1671-1122.2026.04.007
- 总结：中文期刊工作，用 LLM 将种子翻译为多语言等价程序，通过差分测试检测编译器行为不一致。它将 LLM 翻译与跨语言差分测试结合。为编译器差分测试提供新思路。
- 评分理由：部分回答子问题 2，思路可借鉴，但面向编译器场景且为中文期刊，B 级。

##### [A] EvalPlus: Is Your Code Generated by ChatGPT Really Correct?
- 类型：论文
- 链接：https://lingming.web.illinois.edu/publications/neurips2023.pdf
- 总结：UIUC 提出 EvalPlus，用 80x 更多测试严格评测 LLM 代码，揭示现有基准测试不足导致的虚高 pass@k。它提供 HumanEval+/MBPP+ 增强测试集与安全执行框架。为代码评测提供严格标准。
- 评分理由：直接回答子问题 1 与 2，测试增强方法成熟、官方实现可用，A 级。

##### [B] LiveCodeBench: Holistic and Contamination Free Evaluation
- 类型：论文
- 链接：https://arxiv.org/abs/2403.07974
- 总结：UC Berkeley 提出持续收集新竞赛题的免污染评测基准，覆盖代码生成、自修复、代码执行、测试输出预测等场景。它缓解基准污染问题。为评测提供动态更新思路。
- 评分理由：部分回答子问题 1，评测设计有价值，但作为基准非引擎核心组件，B 级。

##### [B] BigCodeBench: Benchmarking Code Generation with Diverse Function Calls and Complex Instructions
- 类型：论文
- 链接：https://arxiv.org/abs/2406.15877
- 总结：面向真实软件工程场景的代码生成评测基准，强调多样函数调用与复杂指令。它比函数级基准更贴近实际开发需求。为评测提供更真实的测试集。
- 评分理由：部分回答子问题 1，基准设计有参考价值，但非引擎方法组件，B 级。

##### [B] TestEval: Benchmarking Large Language Models for Test Case Generation
- 类型：论文
- 链接：https://arxiv.org/abs/2406.04531
- 总结：评测 LLM 生成测试用例能力的基准，关注覆盖率、分支、路径等指标。它为评估测试生成质量提供标准。对引擎的测试生成模块有参考价值。
- 评分理由：部分回答子问题 2，测试生成评测标准可借鉴，B 级。

##### [B] RepoExec: Evaluate Code Generation with a Repository-Level Executable Benchmark
- 类型：论文
- 链接：https://arxiv.org/abs/2406.11927
- 总结：仓库级、可执行的代码生成评测基准，在真实仓库上下文中评测代码生成。它比函数级基准更接近实际开发。为引擎提供仓库级验证场景参考。
- 评分理由：部分回答子问题 1，仓库级评测设计有参考价值，B 级。

#### 开源项目（14 个）

##### [A] microsoft/CodeT
- 类型：开源项目
- 链接：https://github.com/microsoft/CodeT
- 总结：CodeT 论文的官方实现，提供代码生成+测试生成双一致筛选的完整流水线。代码清晰、可直接运行，是"用生成测试验证代码"的参考实现。可复用其双一致筛选逻辑。
- 评分理由：直接支撑子问题 1 与 2，实现成熟、可集成，A 级。

##### [A] evalplus/evalplus
- 类型：开源项目
- 链接：https://github.com/evalplus/evalplus
- 总结：EvalPlus 严格评测框架，提供 HumanEval+/MBPP+ 增强测试集与安全执行环境。测试充分、执行沙箱完善，是代码评测的标准工具。可复用其测试集与执行框架。
- 评分理由：直接支撑子问题 1 与 2，框架成熟、广泛使用，A 级。

##### [B] bigcode-project/bigcode-evaluation-harness
- 类型：开源项目
- 链接：https://github.com/bigcode-project/bigcode-evaluation-harness
- 总结：BigCode 代码生成模型评测框架，支持 HumanEval/APPS/MBPP/DS-1000 等多项基准。评测接口统一、可扩展。可作为引擎的评测后端参考。
- 评分理由：部分支撑子问题 1，评测基础设施可复用，B 级。

##### [B] LiveCodeBench/LiveCodeBench
- 类型：开源项目
- 链接：https://github.com/LiveCodeBench/LiveCodeBench
- 总结：免污染代码评测工具，含 self-repair、code execution、test output prediction 等场景。它持续更新题目以缓解污染。可作为评测数据来源。
- 评分理由：部分支撑子问题 1，评测工具可参考，B 级。

##### [B] bigcode-project/bigcodebench
- 类型：开源项目
- 链接：https://github.com/bigcode-project/bigcodebench
- 总结：BigCodeBench 基准与评测工具，面向真实软件工程场景。它提供复杂指令与多样函数调用测试集。可作为引擎的评测数据。
- 评分理由：部分支撑子问题 1，基准数据可复用，B 级。

##### [B] ise-uiuc/TitanFuzz
- 类型：开源项目
- 链接：https://github.com/ise-uiuc/TitanFuzz
- 总结：LLM 驱动的 DL 库模糊/差分测试工具（ISSTA 2023）。它提供 LLM 生成测试输入的完整实现。可借鉴其测试输入生成逻辑。
- 评分理由：部分支撑子问题 2，实现可参考，但场景特定，B 级。

##### [B] maybeLee/DLLens
- 类型：开源项目
- 链接：https://github.com/maybeLee/DLLens
- 总结：跨库 API counterpart 差分测试工具（TOSEM 2024）。它实现 LLM 合成 API 对应关系做差分测试。可借鉴其对应关系发现方法。
- 评分理由：部分支撑子问题 2，实现可参考，B 级。

##### [A] facebookresearch/mbr-exec
- 类型：开源项目
- 链接：https://github.com/facebookresearch/mbr-exec
- 总结：MBR-Exec 执行感知代码选择官方实现。它提供基于执行结果的 MBR 解码代码。可直接复用为引擎的候选选择模块。
- 评分理由：直接支撑子问题 1，实现成熟、可集成，A 级。

##### [B] facebookresearch/coder_reviewer_reranking
- 类型：开源项目
- 链接：https://github.com/facebookresearch/coder_reviewer_reranking
- 总结：Coder-Reviewer 重排官方实现，提供生成器+评审器双模型重排代码。它包含完整训练与推理流程。可借鉴其重排流水线。
- 评分理由：部分支撑子问题 1，实现可参考，但依赖模型训练，B 级。

##### [B] robtaylor/lever
- 类型：开源项目
- 链接：https://github.com/robtaylor/lever
- 总结：LEVER 学习验证器实现，提供基于执行结果训练验证器的代码。它包含验证器训练与推理流程。可借鉴执行感知验证器训练。
- 评分理由：部分支撑子问题 1，实现可参考，B 级。

##### [B] facebookresearch/cruxeval
- 类型：开源项目
- 链接：https://github.com/facebookresearch/cruxeval
- 总结：CRUXEval 代码推理/执行基准，提供 800 个输入输出对。它用于评测代码执行与推理能力。可作为引擎的测试数据来源。
- 评分理由：部分支撑子问题 1，基准数据可复用，B 级。

##### [B] SWE-bench/SWE-bench
- 类型：开源项目
- 链接：https://github.com/SWE-bench
- 总结：真实 GitHub issue 修复评测基准与工具链。它提供仓库级代码修复评测环境。可作为引擎的仓库级验证场景。
- 评分理由：部分支撑子问题 1，评测工具链可参考，B 级。

##### [B] xlang-ai/DS-1000
- 类型：开源项目
- 链接：https://github.com/xlang-ai/DS-1000
- 总结：数据科学代码生成基准，覆盖真实数据科学任务。它提供多样化测试场景。可作为引擎的评测数据。
- 评分理由：部分支撑子问题 1，基准数据可复用，B 级。

##### [B] openai/human-eval
- 类型：开源项目
- 链接：https://github.com/openai/human-eval
- 总结：HumanEval 基准与执行评测代码，是代码生成评测的事实标准。它提供 164 个手写编程题与单元测试。可作为引擎的基础测试集。
- 评分理由：部分支撑子问题 1，基准数据可复用，B 级。

### 方向 2：程序行为/语义等价性的自动判据

#### 论文（25 篇）

##### [A] Semantic Program Alignment for Equivalence Checking
- 类型：论文
- 链接：PLDI 2019（Churchill, Padon, Sharma, Aiken, Stanford）
- 总结：基于语义而非语法构建 trace alignment 与 product program，将等价检查扩展到真实规模基准。通过程序切片与语义对齐减少需要验证的路径，显著提升可扩展性。为行为等价判定提供了可落地的工程化方法。
- 评分理由：直接回答"行为等价性自动判据"子问题，方法成熟且可借鉴到差分测试引擎。

##### [A] Relational verification using product programs
- 类型：论文
- 链接：FM 2011（Barthe, Crespo, Kunz）
- 总结：用 product program 把关系验证（含程序等价）转化为标准验证问题，是关系验证的奠基构造。将双程序性质规约为单程序验证，可复用现有验证器。是构建差分测试引擎形式化判据的核心方法。
- 评分理由：为行为等价判据提供核心理论构造，直接相关。

##### [B] A Monadic Framework for Relational Verification
- 类型：论文
- 链接：POPL 2019（Maillard 等，F*）
- 总结：单子化关系验证框架，统一处理程序等价与优化正确性。在 F* 中实现，支持信息流安全、程序等价与优化验证。框架通用但工程复杂度高。
- 评分理由：部分回答等价判据问题，需适配后才能集成。

##### [B] Exploiting Synchrony and Symmetry in Relational Verification
- 类型：论文
- 链接：CAV 2018（Princeton）
- 总结：利用同步与对称性约简关系验证（含等价检查）开销。通过识别程序间同步点与对称结构减少验证负担。对大规模等价检查有优化价值。
- 评分理由：优化等价检查效率，但需与主方法结合使用。

##### [B] An Algebra of Alignment for Relational Verification
- 类型：论文
- 链接：POPL 2023（Antonopoulos 等，Yale）
- 总结：用 BiKAT 代数统一描述对齐策略，支撑程序等价验证。为对齐策略提供代数基础，可指导自动选择对齐方式。理论性强。
- 评分理由：提供对齐策略的形式化基础，以参考价值为主。

##### [B] A language-independent proof system for full program equivalence
- 类型：论文
- 链接：Formal Aspects of Computing, 2016
- 总结：以操作语义为参数的语言无关完全等价证明系统。可适用于多种语言，但证明负担较重。为等价判定提供语言无关的理论框架。
- 评分理由：理论贡献为主，工程集成成本高。

##### [B] Checking equivalence in a non-strict language (NEBULA)
- 类型：论文
- 链接：Journal of Functional Programming
- 总结：基于符号执行+余归纳检查非严格函数式语言程序等价，工具 nebula。针对惰性求值语言的特殊性设计。对函数式代码等价判定有参考价值。
- 评分理由：面向特定语言族，适配范围有限。

##### [A] HEC: Equivalence Verification Checking for Code Transformation via Equality Saturation
- 类型：论文
- 链接：arXiv 2506.02290
- 总结：用 e-graph/等值饱和在 MLIR 前端上验证代码变换的功能等价。等值饱和可同时探索大量等价重写，验证变换正确性。与 LLM 代码优化验证场景契合。
- 评分理由：方法新颖且可直接用于代码变换等价验证。

##### [A] Alive2: Bounded Translation Validation for LLVM
- 类型：论文
- 链接：PLDI 2021（Lopes, Menendez, Nagarakatte, Regehr）
- 总结：对 LLVM 优化变换做有界翻译验证（refinement 检查）。自动生成反例，已发现大量 LLVM 优化 bug。是编译器变换等价检查的成熟工具。
- 评分理由：成熟的等价/refinement 检查方法，可借鉴到引擎设计。

##### [A] Regression Verification: Proving the Equivalence of Similar Programs
- 类型：论文
- 链接：CAV 2009 / STVR 2013（Godlin, Strichman）
- 总结：回归验证：证明新版本与旧版本行为等价（RVT 工具）。通过函数映射与归纳证明处理相似程序。为版本间行为等价判定提供系统方法。
- 评分理由：直接对应"行为等价自动判据"，方法成熟。

##### [A] Differential Symbolic Execution
- 类型：论文
- 链接：IEEE TSE 2008（Person, Dwyer, Elbaum, Păsăreanu）
- 总结：通过符号执行同时探索两个版本的状态空间以刻画行为差异。可生成差异输入并证明等价/不等价。是差分测试与符号执行结合的经典方法。
- 评分理由：直接支撑行为差异探测与等价判定。

##### [B] Partition-Based Regression Verification
- 类型：论文
- 链接：ICSE 2013（Felsing, Grebing, Klebanov, Rümmer）
- 总结：用划分启发式处理回归验证中不可判定情形（PASDA）。将程序划分为子程序分别验证，提升可扩展性。对大规模回归验证有参考价值。
- 评分理由：改进回归验证可扩展性，需适配后采用。

##### [A] Csmith: A Static-Dynamic-Equal Strategy for Random Testing of C Compilers
- 类型：论文
- 链接：PLDI 2011（Yang, Chen, Eide, Regehr）
- 总结：随机生成 C 程序，以差分测试作为等价/行为一致性判据发现编译器 bug。生成避免未定义行为的程序，配合多编译器差分。是差分测试在编译器领域的里程碑。
- 评分理由：差分测试经典范式，直接支撑引擎设计。

##### [B] Semantic Code Search via Equational Reasoning (Yogo)
- 类型：论文
- 链接：PLDI 2018（Premtoon, Koppel, Solar-Lezama, MIT）
- 总结：基于数据流等式推理的语义代码搜索工具 Yogo，可识别数学等价的不同实现。用等式推理证明语义等价，用于代码搜索。对语义等价判定有参考价值。
- 评分理由：语义等价判定的一种实现，可借鉴思路。

##### [B] Program Synthesis with Equivalence Reduction
- 类型：论文
- 链接：VMCAI 2019（UW-Madison）
- 总结：在程序合成搜索中用等价归约剪枝，等价类判定加速合成。将等价判定用于搜索空间缩减。对合成与等价判定结合有参考价值。
- 评分理由：等价判定在合成中的应用，间接相关。

##### [B] code2vec: Learning Distributed Representations of Code
- 类型：论文
- 链接：POPL 2019（Alon, Zilberstein, Levy, Yahav）
- 总结：以方法名预测为代理任务学习代码分布式向量，用于语义属性预测。可支撑语义相似/等价类任务。是学习式语义表示的早期代表。
- 评分理由：神经语义表示可辅助等价判定，但精度有限。

##### [B] code2seq: Generating Sequences from Structured Representations of Code
- 类型：论文
- 链接：ICLR 2019（Alon 等）
- 总结：基于 AST 路径+注意力表示代码，可支撑语义相似/等价类任务。在代码摘要等任务上表现好。对语义表示有参考价值。
- 评分理由：语义表示方法，间接辅助等价判定。

##### [B] CodeBERT: A Pre-Trained Model for Programming and Natural Languages
- 类型：论文
- 链接：EMNLP 2020 Findings（Feng 等）
- 总结：双模态预训练模型，广泛用于代码克隆（语义相似）检测等下游任务。是代码预训练模型的重要代表。可支撑语义等价近似判定。
- 评分理由：可作为语义近似判据的基座模型。

##### [B] GraphCodeBERT: Pre-training Code Representations with Data Flow
- 类型：论文
- 链接：ICLR 2021（Guo 等）
- 总结：引入数据流结构增强代码语义表示，用于语义克隆检测。数据流信息提升语义理解。对语义等价近似判定有参考价值。
- 评分理由：改进语义表示，间接辅助等价判定。

##### [B] ASTNN: A Novel Neural Source Code Representation Based on Abstract Syntax Tree
- 类型：论文
- 链接：ICSE 2019（Zhang 等）
- 总结：将 AST 拆分为语句树序列编码，用于代码克隆（含语义克隆）检测。轻量高效的树结构编码。对语义相似检测有参考价值。
- 评分理由：语义克隆检测方法，间接相关。

##### [B] CCLearner: A Deep Learning-Based Clone Detection Approach
- 类型：论文
- 链接：ICSE 2018（Li, Huang）
- 总结：纯 token 的深度学习克隆检测，可识别语义等价实现。无需 AST 解析，简单高效。对语义等价近似判定有参考价值。
- 评分理由：语义克隆检测方法，精度有限。

##### [A] EquiBench: Benchmarking Large Language Models' Reasoning about Program Semantics via Equivalence Checking
- 类型：论文
- 链接：arXiv 2502.12466
- 总结：把等价检查作为评估 LLM 程序语义推理能力的新基准任务。构建大规模程序等价/不等价数据集。为 LLM 语义推理评测提供标准。
- 评分理由：直接面向 LLM 程序等价判定，与引擎评测直接相关。

##### [A] Disproving Program Equivalence with LLMs (ProbeGen)
- 类型：论文
- 链接：2025（Allamanis, Yin）
- 总结：白盒、执行反馈驱动的 LLM 反证程序等价方法。生成反例输入证明不等价，与正证明互补。直接支撑差分测试引擎的等价判定。
- 评分理由：LLM 驱动的等价判定核心方法，高采用价值。

##### [C] On Neural Network Equivalence Checking using SMT Solvers
- 类型：论文
- 链接：arXiv 2203.11629
- 总结：将神经网络等价检查编码为 SMT 公式求解。面向神经网络而非程序代码。与 LLM 代码差分测试关联度低。
- 评分理由：对象不同，仅作背景参考。

##### [A] Emerge: Verify Implementation Equivalence of Large Models
- 类型：论文
- 链接：arXiv 2603.21851
- 总结：用 e-graph + 执行值推断，检查大模型计算图实现的功能等价。针对大模型计算图等价验证。与代码变换等价验证思路相通。
- 评分理由：e-graph 等价验证方法，可直接借鉴。

#### 开源项目（12 个）

##### [B] code2vec（开源实现）
- 类型：开源项目
- 链接：https://github.com/tech-srl/code2vec
- 总结：POPL'19 官方实现，学习代码分布式语义向量。可用于语义相似/等价近似判定。
- 评分理由：语义表示工具，辅助等价判定。

##### [B] code2seq（开源实现）
- 类型：开源项目
- 链接：https://github.com/tech-srl/code2seq
- 总结：ICLR'19 官方实现，基于 AST 路径的代码表示模型。可支撑语义相似/等价类任务。
- 评分理由：语义表示工具，辅助等价判定。

##### [B] ASTNN（开源实现）
- 类型：开源项目
- 链接：https://github.com/zhangj111/astnn
- 总结：ICSE'19 官方实现，AST 子树编码做代码克隆检测。轻量高效。
- 评分理由：语义克隆检测工具，间接辅助。

##### [B] CCLearner（开源实现）
- 类型：开源项目
- 链接：https://github.com/liuqingli/CCLearner
- 总结：ICSE'18 官方实现，纯 token 深度学习克隆检测。无需 AST 解析。
- 评分理由：语义克隆检测工具，间接辅助。

##### [B] CodeBERT（开源实现）
- 类型：开源项目
- 链接：https://github.com/microsoft/CodeBERT
- 总结：代码预训练模型族（含 GraphCodeBERT / UniXcoder），支持克隆/语义相似检测。可作为语义等价近似判据的基座。
- 评分理由：语义表示基座模型，间接辅助。

##### [A] SymDiff
- 类型：开源项目
- 链接：https://github.com/boogie-org/symdiff
- 总结：微软出品的差分/关系程序验证器，用于回归验证、翻译验证与超安全验证。基于 Boogie 中间语言。可直接用于行为等价判定。
- 评分理由：成熟的行为等价验证工具，高采用价值。

##### [A] Alive2
- 类型：开源项目
- 链接：https://github.com/AliveToolkit/alive2
- 总结：LLVM 变换的有界翻译验证/refinement 检查工具。自动生成反例，已发现大量 LLVM bug。可直接集成。
- 评分理由：成熟等价检查工具，高采用价值。

##### [A] Csmith
- 类型：开源项目
- 链接：https://github.com/csmith-project/csmith
- 总结：随机 C 程序生成器，以差分测试为等价判据。生成避免未定义行为的程序。
- 评分理由：差分测试经典工具，直接可用。

##### [A] KLEE
- 类型：开源项目
- 链接：https://github.com/klee/klee
- 总结：符号执行引擎，可支撑差分符号执行与等价性分析。生成高覆盖测试输入。
- 评分理由：符号执行基础设施，直接可用。

##### [B] Yogo
- 类型：开源项目
- 链接：https://zenodo.org/records/3743160
- 总结：PLDI'18 工件，基于等式推理的语义代码搜索工具（MIT）。可识别数学等价的不同实现。
- 评分理由：语义等价搜索工具，参考价值。

##### [B] roojs/semantic-code-search
- 类型：开源项目
- 链接：https://github.com/roojs/semantic-code-search
- 总结：基于 transformer 嵌入+余弦相似度的函数级语义代码搜索工具。可做语义近似检索。
- 评分理由：语义近似检索工具，参考价值。

##### [B] sturdy-dev/semantic-code-search
- 类型：开源项目
- 链接：https://github.com/sturdy-dev/semantic-code-search
- 总结：基于 SentenceT5 在 code_search_net 上训练的语义代码搜索工具。面向函数级语义检索。
- 评分理由：语义近似检索工具，参考价值。

### 方向 3：测试输入智能生成 + 差分测试与属性测试融合

#### 论文（43 篇）

##### [A] TitanFuzz: Large Language Models are Zero-Shot Fuzzers
- 类型：论文
- 链接：ISSTA 2023，https://arxiv.org/pdf/2212.14834v4.pdf
- 总结：用 LLM 零样本生成并变异深度学习库 API 调用作为测试输入，配合差分执行暴露库间行为差异。无需人工编写种子，自动生成多样化输入。是 LLM 驱动差分测试的早期代表。
- 评分理由：直接回答测试输入智能生成子问题，方法成熟、官方实现可用。

##### [A] WhiteFox: White-Box Compiler Fuzzing Empowered by Large Language Models
- 类型：论文
- 链接：OOPSLA 2024，https://arxiv.org/abs/2310.15991
- 总结：LLM 分析编译器优化源码后生成能触发深层优化的测试程序，发现 DL 编译器大量 bug。白盒方式利用源码信息提升测试针对性。对编译器差分测试有高价值。
- 评分理由：LLM+白盒信息生成测试输入，直接相关。

##### [B] FuzzGPT: Fuzzing Deep Learning Libraries via Large Language Models
- 类型：论文
- 链接：2023，arXiv
- 总结：基于 LLM 生成"异常/罕见"程序作为模糊输入，用于 DL 库测试。补充常规 fuzzing 的盲区。对测试输入多样性有参考价值。
- 评分理由：部分回答输入生成问题，场景特定。

##### [B] ChatFuzz: Augmenting Greybox Fuzzing with Generative AI
- 类型：论文
- 链接：2023，https://ar5iv.labs.arxiv.org/html/2306.06782
- 总结：用 ChatGPT 对种子进行变异生成格式合规的高质量输入，增强灰盒模糊测试。将 LLM 变异能力与传统 fuzzing 结合。
- 评分理由：LLM 变异增强 fuzzing，可借鉴思路。

##### [B] CodaMosa: Escaping Coverage Plateaus in Test Generation with Pre-trained Large Language Models
- 类型：论文
- 链接：ICSE 2023，https://www.microsoft.com/en-us/research/publication/codamosa-escaping-coverage-plateaus-in-test-generation-with-pre-trained-large-language-models/
- 总结：将 LLM 生成的示例测试融入搜索式测试生成(SBST)以突破覆盖率平台。LLM 与搜索式方法互补。
- 评分理由：LLM+SBST 融合，参考价值。

##### [B] TestPilot: An Empirical Evaluation of Using Large Language Models for Automated Unit Test Generation
- 类型：论文
- 链接：IEEE TSE，https://www.franktip.org/pubs/testpilot2023.pdf
- 总结：用 LLM 为 JavaScript API 自动生成单元测试，达到高语句/分支覆盖率。工业界大规模实证。
- 评分理由：LLM 测试生成实证，参考价值。

##### [B] ChatUniTest: A Framework for LLM-Based Test Generation
- 类型：论文
- 链接：2023，https://arxiv.org/html/2305.04764v2
- 总结：基于 LLM 的 Java 单元测试生成框架，结合覆盖率反馈迭代优化。将测试反馈融入生成循环。
- 评分理由：LLM 测试生成框架，参考价值。

##### [A] CoverUp: Coverage-Guided LLM-Based Test Generation
- 类型：论文
- 链接：2024，https://arxiv.org/pdf/2403.16218
- 总结：以覆盖率作为反馈循环引导 LLM 迭代生成测试，超越 EvoSuite 等传统工具。覆盖率反馈闭环高效。
- 评分理由：覆盖率引导的 LLM 测试生成，直接相关。

##### [B] ELFuzz: Efficient Input Generation via LLM-driven Synthesis Over Fuzzer Space
- 类型：论文
- 链接：USENIX Security 2025，https://www.usenix.org/system/files/usenixsecurity25-chen-chuyang.pdf
- 总结：通过 LLM 在"模糊器空间"中进化合成面向被测系统的生成式模糊器。将 LLM 用于模糊器合成。
- 评分理由：新颖的模糊器合成思路，参考价值。

##### [A] Mokav: Execution-driven Differential Testing with LLMs
- 类型：论文
- 链接：2024，https://arxiv.org/html/2406.10375v2
- 总结：用 LLM 生成"差异暴露测试"(DET)，执行驱动地检测两个程序版本间的功能差异。直接面向差分测试输入生成。
- 评分理由：直接回答差分测试输入生成子问题。

##### [A] DiffSpec: Differential testing with LLMs using Natural Language Specifications and Code Artifacts
- 类型：论文
- 链接：2024，https://arxiv.org/pdf/2410.04249v3
- 总结：用自然语言规范与代码工件引导 LLM 生成能凸显实现间行为差异的差分测试。利用规范信息提升差异暴露能力。
- 评分理由：差分测试输入生成的核心方法。

##### [B] MutGen: Mutation-Guided Unit Test Generation With a Large Language Model
- 类型：论文
- 链接：IEEE TSE 2026，https://store.computer.org/csdl/journal/ts/2026/05/11478734/2fzptwnimcw
- 总结：将变异反馈直接融入提示词，迭代生成能杀死更多变异体的 LLM 测试用例。变异引导提升测试强度。
- 评分理由：变异引导测试生成，参考价值。

##### [B] CodeGraphGPT: A Code Knowledge Graph-Enhanced System for LLM-Based Fuzz Driver Generation
- 类型：论文
- 链接：2024，https://arxiv.org/html/2411.11532v1
- 总结：用代码知识图谱增强 LLM 智能体自动生成模糊驱动(fuzz driver)。知识图谱提供上下文。
- 评分理由：知识图谱增强生成，参考价值。

##### [B] PromeFuzz: A Knowledge-Driven Approach to Fuzzing Harness Generation with Large Language Models
- 类型：论文
- 链接：2025，https://dl.acm.org/doi/10.1145/3719027.3765222
- 总结：结合代码元数据/API 文档/调用关联构建知识库，RAG 增强生成模糊 harness。提升 harness 生成质量。
- 评分理由：RAG 增强 harness 生成，参考价值。

##### [B] SAFuzz: Semantic-Guided Adaptive Fuzzing for LLM-Generated Code
- 类型：论文
- 链接：2025，https://www.themoonlight.io/fr/review/safuzz-semantic-guided-adaptive-fuzzing-for-llm-generated-code
- 总结：语义引导的自适应模糊测试，高效检测 LLM 生成代码中的算法漏洞。面向 LLM 生成代码。
- 评分理由：面向 LLM 生成代码的 fuzzing，参考价值。

##### [A] Kaizen: Metamorphic Fuzzing and Differential Testing for LLM-Translated HPC Applications
- 类型：论文
- 链接：2026，https://arxiv.org/abs/2607.04058
- 总结：对 LLM 翻译的 HPC 代码做蜕变模糊+差分测试，暴露"编译通过但结果错误"的语义分歧。直接针对 LLM 生成代码。
- 评分理由：差分+蜕变测试融合，直接相关。

##### [A] NEZHA: Efficient Domain-Independent Differential Testing
- 类型：论文
- 链接：ICSE 2017，http://www.cs.columbia.edu/~angelos/Papers/2017/nezha.pdf
- 总结：提出 δ-多样性指标引导输入生成，领域无关的差分测试框架。可扩展至多种被测系统。
- 评分理由：差分测试输入生成框架，直接相关。

##### [B] DLFuzz: Differential Fuzzing Testing of Deep Learning Systems
- 类型：论文
- 链接：ESEC/FSE 2018，https://dl.acm.org/doi/pdf/10.1145/3236024.3264835
- 总结：通过最大化神经元覆盖与预测差异引导变异，差分模糊测试 DL 系统。面向深度学习系统。
- 评分理由：DL 差分模糊测试，参考价值。

##### [B] Evolutionary Generative Fuzzing for Differential Testing of the Kotlin Compiler
- 类型：论文
- 链接：ISSTA 2023，https://pure.tudelft.nl/ws/portalfiles/portal/216990626/3663529.3663864.pdf
- 总结：进化生成式模糊测试对 Kotlin 编译器做差分测试，绕过 oracle 问题。进化策略引导生成。
- 评分理由：编译器差分 fuzzing，参考价值。

##### [A] Towards Translating Real-World Code with LLMs: A Study of Translating to Rust
- 类型：论文
- 链接：2024，https://arxiv.org/html/2405.11514v2
- 总结：构建跨语言差分模糊器验证 LLM 代码翻译与原程序的 I/O 等价性。直接面向 LLM 生成代码等价验证。
- 评分理由：跨语言差分验证，直接相关。

##### [A] A Differential Fuzzing-Based Evaluation of Functional Equivalence in LLM-Generated Code Refactorings
- 类型：论文
- 链接：2026，https://arxiv.deeppaper.ai/papers/2602.15761v1
- 总结：用差分模糊检查 LLM 重构代码与原始实现的功能等价性，无需预定义测试用例。自动生成差异暴露输入。
- 评分理由：直接回答行为等价判据与输入生成。

##### [B] LLMs in the Heart of Differential Testing: A Case Study on a Medical Rule Engine
- 类型：论文
- 链接：2024，https://arxiv.org/pdf/2404.03664v3
- 总结：LLM 生成测试输入用于医疗规则引擎的差分测试。领域案例验证可行性。
- 评分理由：领域案例，参考价值。

##### [B] 基于大语言模型的模糊测试研究综述
- 类型：论文
- 链接：《软件学报》2025，https://www.jos.org.cn/html/2025/6/7323.htm
- 总结：系统综述 LLM 在模糊测试中的应用，归纳 LLM 生成测试输入的 3 类方法（微调/提示工程/传统算法融合）。提供方法全景。
- 评分理由：综述，提供方法全景。

##### [B] A Review of Large Language Models for Automated Test Case Generation
- 类型：论文
- 链接：MDPI Machine Learning and Knowledge Extraction 2025，https://mdpi-res.com/d_attachment/make/make-07-00097/article_deploy/make-07-00097.pdf
- 总结：综述 LLM 自动化测试用例生成的提示设计、反馈循环等方向。梳理研究脉络。
- 评分理由：综述，参考价值。

##### [C] On the Challenges of Fuzzing Techniques via Large Language Models
- 类型：论文
- 链接：2024，https://arxiv.org/pdf/2402.00350v3
- 总结：分析 LLM 驱动模糊测试（如 CHATAFL 协议模糊器）面临的核心挑战。指出局限与难点。
- 评分理由：挑战分析，关联度低。

##### [A] QuickCheck: A Lightweight Tool for Random Testing of Haskell Programs
- 类型：论文
- 链接：ICFP 2000，https://asr.github.io/courses/cm0859-type-theory/2025-2/slides/testing-with-quickcheck.pdf
- 总结：属性测试(PBT)奠基之作，用随机生成+收缩(shrink)验证程序性质。是差分测试与属性测试融合的基础。
- 评分理由：PBT 范式源头，直接相关。

##### [A] To Kill a Mockingbird: A Framework for Test Oracle Generation
- 类型：论文
- 链接：ICSE 2015，https://dl.acm.org/doi/10.1145/2786805.2786873
- 总结：自动生成测试预言：以简化参考实现(mock)作为 oracle，本质是差分式 oracle，缓解 oracle 问题。与差分测试思想一致。
- 评分理由：差分式 oracle 生成，直接相关。

##### [A] Mica: Automated Differential Testing for OCaml Modules
- 类型：论文
- 链接：2024，https://arxiv.org/html/2408.14561v1
- 总结：基于 Jane Street Core.Quickcheck 自动派生 PBT 代码检查 OCaml 模块的观测等价性，是差分测试与属性测试融合的典型。
- 评分理由：差分+PBT 融合的典型实现。

##### [B] Property-Based Testing in Practice
- 类型：论文
- 链接：ICSE 2024，https://harrisongoldste.in/papers/icse24-pbt-in-practice.pdf
- 总结：对 Jane Street 等工业界 PBT 实践的实证研究。揭示 PBT 在真实工程中的价值与挑战。
- 评分理由：PBT 实践实证，参考价值。

##### [B] An Empirical Evaluation of Property-Based Testing in Python
- 类型：论文
- 链接：OOPSLA 2025，https://cseweb.ucsd.edu/~mcoblenz/assets/pdf/OOPSLA_2025_PBT.pdf
- 总结：对 Python 生态中 Hypothesis 等 PBT 库使用情况的实证评估。分析使用模式与收益。
- 评分理由：PBT 实证，参考价值。

##### [B] Property-Based Testing Across Four Environments in Open-Source Repositories
- 类型：论文
- 链接：2025，https://sarajuhosova.com/assets/files/2025-pbt-in-the-wild.pdf
- 总结：跨 Java(JQwik)/Python(Hypothesis)/Rust(proptest、QuickCheck)研究 PBT 在开源库中的使用模式，包括"与 oracle 等价"类属性。
- 评分理由：PBT 使用模式研究，参考价值。

##### [C] How Developers Implement Property-Based Tests
- 类型：论文
- 链接：2023，https://www.researchgate.net/profile/Arthur-Corgozinho/publication/373829403_How_Developers_Implement_Property-Based_Tests/links/64ff10f6849bbb203b90fb92/How-Developers-Implement-Property-Based-Tests.pdf
- 总结：研究开发者如何用 Hypothesis 实现属性测试。关注开发者实践。
- 评分理由：开发者实践研究，关联度低。

##### [A] PBT-Bench: Benchmarking AI Agents on Property-Based Testing
- 类型：论文
- 链接：2026，https://arxiv.org/html/2605.15229v1
- 总结：评测 AI 智能体自动编写属性测试的能力，涉及 Hypothesis 等框架。为智能体 PBT 提供基准。
- 评分理由：PBT 智能体评测基准，直接相关。

##### [A] Agentic Property-Based Testing: Finding Bugs Across the Python Ecosystem
- 类型：论文
- 链接：2025，https://arxiv.org/pdf/2510.09907
- 总结：编码智能体自主爬取代码库、发现高价值属性、编写并运行 PBT 来定位 bug。全自动 PBT 闭环。
- 评分理由：智能体+PBT 融合，直接相关。

##### [B] PropTest: Automatic Property Testing for Improved Visual Programming
- 类型：论文
- 链接：2024，https://arxiv.org/html/2403.16921v1
- 总结：自动生成属性测试用例作为反馈引导 LLM 视觉编程代码生成。属性测试用于代码生成反馈。
- 评分理由：属性测试用于代码生成反馈，参考价值。

##### [B] METAL: Metamorphic Testing Framework for Analyzing Large-Language Model Qualities
- 类型：论文
- 链接：2023，https://arxiv.org/pdf/2312.06056v1.pdf
- 总结：用蜕变关系(MR)系统测试 LLM 质量，与 PBT 的"性质验证"思想相通。面向 LLM 质量评估。
- 评分理由：蜕变测试用于 LLM，参考价值。

##### [A] MetaFOE: Investigating Metamorphic Fuzz Oracle Enhancement via Large Language Models
- 类型：论文
- 链接：2026，https://arxiv.org/abs/2606.14164
- 总结：LLM 自动生成并集成蜕变 oracle，增强 OSS-Fuzz 驱动的模糊测试。自动化 oracle 生成。
- 评分理由：LLM 生成蜕变 oracle，直接相关。

##### [B] Towards Generating Executable Metamorphic Relations Using Large Language Models
- 类型：论文
- 链接：2024，https://arxiv.org/html/2401.17019
- 总结：用提示工程教 LLM 从需求生成可执行蜕变关系(EMR)。将需求转化为可执行测试关系。
- 评分理由：LLM 生成蜕变关系，参考价值。

##### [B] Variable Discovery with Large Language Models for Metamorphic Testing of Scientific Software
- 类型：论文
- 链接：ICCS 2023，https://www.iccs-meeting.org/archive/iccs2023/papers/140730328.pdf
- 总结：用 LLM 为科学计算软件发现蜕变关系变量，缓解 oracle 问题。面向科学计算场景。
- 评分理由：LLM 辅助蜕变测试，参考价值。

##### [B] Bidirectional Empowerment of Metamorphic Testing and Large Language Models: A Systematic Survey
- 类型：论文
- 链接：2025，https://www.themoonlight.io/de/review/bidirectional-empowerment-of-metamorphic-testing-and-large-language-models-a-systematic-survey
- 总结：系统综述 93 篇蜕变测试与 LLM 双向赋能的研究。梳理双向赋能脉络。
- 评分理由：综述，提供全景。

##### [C] Drowzee: Metamorphic Testing for Fact-Conflicting Hallucination Detection in Large Language Models
- 类型：论文
- 链接：2024，https://arxiv.org/html/2405.00648v2
- 总结：用蜕变关系检测 LLM 事实冲突幻觉。面向 LLM 幻觉检测而非代码。
- 评分理由：面向 LLM 幻觉检测，关联度低。

##### [B] From Prompts to Properties: Rethinking LLM Code Generation with Property-Based Testing
- 类型：论文
- 链接：2025，https://chbrown13.github.io/papers/autopydep.pdf
- 总结：用 Hypothesis 为 LLM 生成代码定义并验证性质（如排序输出有序性）。将 PBT 用于验证 LLM 代码。
- 评分理由：PBT 验证 LLM 代码，参考价值。

##### [C] Testing Noninterference, Quickly
- 类型：论文
- 链接：2014，https://arxiv.org/pdf/1409.0393v1.pdf
- 总结：用 QuickCheck 形式化并测试抽象机的非干扰安全属性。面向安全属性验证。
- 评分理由：面向安全属性，关联度低。

#### 开源项目（15 个）

##### [A] Hypothesis
- 类型：开源项目
- 链接：https://github.com/degustaf/hypothesis
- 总结：最流行的 QuickCheck 风格 Python 属性测试库，支持生成器组合、收缩、状态化测试。生态成熟、文档完善。
- 评分理由：PBT 基础设施，直接可用。

##### [A] QuickCheck (Haskell)
- 类型：开源项目
- 链接：https://hackage.haskell.org/package/QuickCheck-2.18.0.0
- 总结：属性测试原始实现，PBT 范式源头。随机生成+收缩机制。
- 评分理由：PBT 范式源头，直接可用。

##### [A] proptest
- 类型：开源项目
- 链接：https://github.com/proptest-rs/proptest
- 总结：Rust 生态主流 PBT 库，支持策略组合与收缩。性能与易用性均衡。
- 评分理由：Rust PBT 基础设施，直接可用。

##### [B] quickcheck (Rust)
- 类型：开源项目
- 链接：https://github.com/BurntSushi/quickcheck
- 总结：Rust 版 QuickCheck 移植，Rust 两大 PBT 库之一。轻量易用。
- 评分理由：Rust PBT 库，参考价值。

##### [B] jqwik
- 类型：开源项目
- 链接：https://github.com/jqwik-team/jqwik
- 总结：Java/JUnit 5 属性测试库。与 JUnit 生态集成良好。
- 评分理由：Java PBT 库，参考价值。

##### [A] AFL++
- 类型：开源项目
- 链接：https://github.com/AFLplusplus/AFLplusplus
- 总结：覆盖率引导灰盒模糊测试的事实标准，广泛用于生成暴露崩溃/行为差异的输入。社区活跃、持续增强。
- 评分理由：fuzzing 基础设施，直接可用。

##### [A] libFuzzer
- 类型：开源项目
- 链接：https://llvm.org/docs/LibFuzzer.html
- 总结：进程内覆盖率引导模糊器，与 Sanitizer 配合。集成于 LLVM 生态。
- 评分理由：fuzzing 基础设施，直接可用。

##### [B] EvoSuite
- 类型：开源项目
- 链接：https://github.com/STAMP-project/evosuite
- 总结：搜索式单元测试生成工具，常作为 LLM 测试生成方法的对比基线。支持覆盖率目标。
- 评分理由：测试生成基线工具，参考价值。

##### [B] Randoop
- 类型：开源项目
- 链接：https://github.com/randoop/randoop
- 总结：基于反馈的随机回归测试生成工具。生成回归测试用例。
- 评分理由：随机测试生成工具，参考价值。

##### [B] KLEE
- 类型：开源项目
- 链接：https://github.com/klee/klee
- 总结：符号执行驱动的高覆盖测试输入生成引擎。可生成满足路径条件的输入。
- 评分理由：测试输入生成基础设施，参考价值。

##### [A] WhiteFox
- 类型：开源项目
- 链接：https://yangchenyuan.github.io/files/WhiteFox-OOSPLA-24-slides.pdf
- 总结：LLM 白盒编译器模糊测试工具（OOPSLA 2024 配套开源）。利用源码信息生成深层测试。
- 评分理由：LLM fuzzing 工具，直接可用。

##### [A] TitanFuzz
- 类型：开源项目
- 链接：https://github.com/ise-uiuc/TitanFuzz
- 总结：LLM 零样本模糊测试 DL 库工具（ISSTA 2023 配套开源）。自动生成 API 调用序列。
- 评分理由：LLM 差分 fuzzing 工具，直接可用。

##### [B] FuzzGPT
- 类型：开源项目
- 链接：https://github.com/ise-uiuc/FuzzGPT
- 总结：LLM 生成异常程序模糊 DL 库工具。补充罕见输入覆盖。
- 评分理由：LLM fuzzing 工具，参考价值。

##### [B] CodaMosa
- 类型：开源项目
- 链接：https://www.microsoft.com/en-us/research/publication/codamosa-escaping-coverage-plateaus-in-test-generation-with-pre-trained-large-language-models/
- 总结：LLM+搜索式测试生成工具（ICSE 2023 配套开源）。LLM 与 SBST 融合。
- 评分理由：LLM+SBST 工具，参考价值。

##### [A] Cryptofuzz
- 类型：开源项目
- 链接：https://github.com/guidovranken/cryptofuzz
- 总结：密码学库差分测试框架，支持自差分与跨库差分，集成于 OSS-Fuzz。工程成熟、覆盖广泛。
- 评分理由：差分测试框架，直接可用。

### 方向 4：经典差分测试基础 + 编译器/解释器差分测试

#### 论文（20 篇）

##### [A] Differential Testing for Software (McKeeman)
- 类型：论文
- 链接：1998，Digital Technical Journal 10(1):100-107
- 总结：差分测试奠基之作，首次系统提出以多个实现交叉比对输出作为测试预言（oracle），是 LLM 差分测试引擎的理论源头。
- 评分理由：差分测试理论源头，直接相关。

##### [B] Translation Validation
- 类型：论文
- 链接：TACAS 1998，https://dl.acm.org/doi/10.5555/646482.691453
- 总结：翻译验证奠基工作，通过证明编译前后程序语义等价来验证编译器正确性，是差分/等价性检查的理论基础。
- 评分理由：等价性检查理论基础，参考价值。

##### [A] The Oracle Problem in Software Testing: A Survey
- 类型：论文
- 链接：IEEE TSE 2015，http://www.cs.ucl.ac.uk/staff/mharman/tse-oracle.pdf
- 总结：测试预言问题权威综述，将差分测试列为缓解 oracle 问题的核心途径之一。系统梳理 oracle 问题分类。
- 评分理由：oracle 问题全景，直接相关。

##### [A] A Survey on Metamorphic Testing
- 类型：论文
- 链接：IEEE TSE 2016
- 总结：蜕变测试综述，用多执行结果间关系替代精确 oracle，与差分测试互补。系统分类蜕变关系与测试方法。
- 评分理由：蜕变测试全景，直接相关。

##### [A] Finding and Understanding Bugs in C Compilers (Csmith)
- 类型：论文
- 链接：PLDI 2011，http://www.stanford.edu/class/cs343/resources/finding-bugs-compilers-annotated.pdf
- 总结：提出 Csmith 随机程序生成器 + 差分测试，发现 GCC/LLVM 大量误编译 bug，PLDI 最具影响力论文奖。是差分测试在编译器领域的里程碑。
- 评分理由：差分测试经典案例，直接相关。

##### [B] Taming Compiler Fuzzers
- 类型：论文
- 链接：PLDI 2013
- 总结：用 delta debugging 最小化编译器差分测试失败用例，提升 bug 报告质量。聚焦失败用例最小化。
- 评分理由：用例最小化技术，参考价值。

##### [A] Compiler Validation via Equivalence Modulo Inputs (EMI)
- 类型：论文
- 链接：PLDI 2014，https://web.cs.ucdavis.edu/~su/publications/emi.pdf
- 总结：提出 EMI 技术：生成"对给定输入等价"的程序变体做差分测试，可精准打击优化阶段误编译。等价变体生成思路对引擎有价值。
- 评分理由：等价变体差分测试，直接相关。

##### [B] Many-core Compiler Fuzzing
- 类型：论文
- 链接：PLDI 2015
- 总结：GLF/GraphicsFuzz 对 GPU 编译器（GLSL）做差分测试，发现大量驱动/编译器 bug。面向 GPU 着色器。
- 评分理由：GPU 编译器差分测试，参考价值。

##### [A] Finding Deep Compiler Bugs via Guided Stochastic Program Mutation (Athena)
- 类型：论文
- 链接：OOPSLA 2015
- 总结：引导式随机程序变异（Athena），深化 EMI 思路发现深层编译器 bug。引导变异提升差异暴露能力。
- 评分理由：引导变异差分测试，直接相关。

##### [B] Toward Understanding Compiler Bugs in GCC and LLVM
- 类型：论文
- 链接：ISSTA 2016，https://dl.acm.org/doi/pdf/10.1145/2931037.2931074
- 总结：对 GCC/LLVM 编译器 bug 的实证研究，为差分测试设计提供 bug 特征依据。分类分析 bug 模式。
- 评分理由：bug 特征实证，参考价值。

##### [A] Random Testing for C and C++ Compilers with YARPGen
- 类型：论文
- 链接：OOPSLA 2020，https://www-old.cs.utah.edu/~regehr/yarpgen-oopsla20.pdf
- 总结：YARPGen 随机程序生成器，无需动态检查即可避免未定义行为，配合差分测试发现 220+ 编译器 bug。生成质量高。
- 评分理由：随机程序生成+差分测试，直接相关。

##### [A] A Survey of Compiler Testing
- 类型：论文
- 链接：ACM Computing Surveys 2020
- 总结：编译器测试权威综述，系统分类差分测试、等价性检查、fuzzing 等方法。提供编译器测试方法全景。
- 评分理由：编译器测试方法全景，直接相关。

##### [A] Fuzzing with Code Fragments (LangFuzz)
- 类型：论文
- 链接：USENIX Security 2012
- 总结：LangFuzz 语法感知 fuzzing，用已知 bug 代码片段变异生成 JS 输入，发现 100+ 漏洞。语法感知生成。
- 评分理由：语法感知 fuzzing，直接相关。

##### [A] Exposing Bugs in JavaScript Engines through Test Transplantation and Differential Testing
- 类型：论文
- 链接：2021，https://www.arxiv.org/pdf/2012.03759
- 总结：将测试移植与差分测试结合，跨引擎暴露 JS 引擎功能 bug。测试移植复用已有测试。
- 评分理由：JS 引擎差分测试，直接相关。

##### [A] Automated Conformance Testing for JavaScript Engines via Deep Compiler Fuzzing (COMFORT)
- 类型：论文
- 链接：PLDI 2021，https://dl.acm.org/doi/pdf/10.1145/3453483.3454054
- 总结：COMFORT 对 10 个主流 JS 引擎做差分一致性测试，发现 158 个 bug。多引擎差分一致性。
- 评分理由：多引擎差分一致性测试，直接相关。

##### [A] JIT-PICKING: Differential Fuzzing of JavaScript Engines
- 类型：论文
- 链接：CCS 2022，https://dl.acm.org/doi/pdf/10.1145/3548606.3560624
- 总结：让 JS 引擎"自己对自己"做差分测试：比较解释器与 JIT 编译器的运行行为，发现优化错误。自差分范式。
- 评分理由：自差分测试范式，直接相关。

##### [A] FuzzJIT: Oracle-Enhanced Fuzzing for JavaScript Engine JIT Compiler
- 类型：论文
- 链接：USENIX Security 2023，https://www.usenix.org/system/files/sec23summer_118-wang_junjie-prepub.pdf
- 总结：利用"JIT 只提速不改结果"这一 oracle 约束，暴露 JIT 编译 bug。oracle 约束驱动 fuzzing。
- 评分理由：oracle 约束差分测试，直接相关。

##### [A] DUMPLING: Fine-grained Differential JavaScript Engine Fuzzing
- 类型：论文
- 链接：NDSS 2025，https://kitsec.org/pubs/2025-ndss.pdf
- 总结：对引擎内部做细粒度状态差分（frame dump），发现 V8 等引擎深层 bug。细粒度状态比较。
- 评分理由：细粒度状态差分，直接相关。

##### [A] Coverage-Directed Differential Testing of JVM Implementations (classfuzz)
- 类型：论文
- 链接：PLDI 2016，https://www.cs.ucdavis.edu/~su/publications/pldi16.pdf
- 总结：classfuzz 面向 JVM 启动过程的覆盖率引导差分测试。覆盖率引导输入生成。
- 评分理由：覆盖率引导差分测试，直接相关。

##### [A] Deep Differential Testing of JVM Implementations (classming)
- 类型：论文
- 链接：ICSE 2019
- 总结：深度学习引导的 JVM 差分测试（classming），深入测试字节码验证器与执行引擎。学习式引导。
- 评分理由：深度学习引导差分测试，直接相关。

#### 开源项目（12 个）

##### [A] Csmith
- 类型：开源项目
- 链接：https://github.com/csmith-project/csmith
- 总结：随机 C 程序生成器，专为差分测试编译器设计。生成避免未定义行为的程序。
- 评分理由：差分测试经典工具，直接可用。

##### [A] YARPGen
- 类型：开源项目
- 链接：https://github.com/LinkiTools/yarpgen
- 总结：随机 C/C++ 程序生成器，面向编译器优化 bug 的差分测试。无需动态检查避免 UB。
- 评分理由：编译器差分测试工具，直接可用。

##### [B] AFL (American Fuzzy Lop)
- 类型：开源项目
- 链接：https://github.com/google/AFL
- 总结：Michal Zalewski 开发的覆盖率引导模糊测试器，差分测试输入生成的常用引擎。经典灰盒 fuzzer。
- 评分理由：fuzzing 基础设施，参考价值。

##### [B] AFL++
- 类型：开源项目
- 链接：https://github.com/AFLplusplus/AFLplusplus
- 总结：AFL 的社区增强版，整合大量前沿 fuzzing 研究成果。功能丰富、持续维护。
- 评分理由：fuzzing 基础设施，参考价值。

##### [B] libFuzzer
- 类型：开源项目
- 链接：https://llvm.org/docs/LibFuzzer.html
- 总结：LLVM 进程内覆盖率引导 fuzzing 引擎，常用于编译器/解释器目标函数测试。与 Sanitizer 配合。
- 评分理由：fuzzing 基础设施，参考价值。

##### [B] KLEE
- 类型：开源项目
- 链接：https://klee.github.io
- 总结：符号执行引擎，可生成高覆盖率测试用例，支撑差分符号执行类方法。
- 评分理由：符号执行基础设施，参考价值。

##### [A] Fuzzilli
- 类型：开源项目
- 链接：https://github.com/googleprojectzero/fuzzilli
- 总结：基于 FuzzIL 中间语言的 JS 引擎 JIT fuzzer。Google Project Zero 出品，工程成熟。
- 评分理由：JS 引擎 fuzzing 工具，直接可用。

##### [A] Nautilus
- 类型：开源项目
- 链接：https://github.com/nautilus-fuzz/nautilus
- 总结：覆盖率引导的语法 fuzzer，NDSS 2019 论文配套工具。语法感知+覆盖率引导。
- 评分理由：语法感知 fuzzing 工具，直接可用。

##### [A] Grammarinator
- 类型：开源项目
- 链接：https://github.com/renatahodovan/grammarinator
- 总结：基于 ANTLR v4 语法的随机测试生成器，可生成语法正确的程序输入。语法驱动生成。
- 评分理由：语法测试生成工具，直接可用。

##### [A] JQF
- 类型：开源项目
- 链接：https://github.com/rohanpadhye/JQF
- 总结：Java 反馈引导 fuzzing 平台（AFL/libFuzzer 的 JVM 版），支持属性测试驱动。JVM 生态 fuzzing。
- 评分理由：JVM fuzzing 平台，直接可用。

##### [B] jsfunfuzz / funfuzz
- 类型：开源项目
- 链接：https://github.com/MozillaSecurity/funfuzz
- 总结：Mozilla 的 JS 引擎 fuzzing 套件，历史上发现 1000+ SpiderMonkey bug。实战经验丰富。
- 评分理由：JS 引擎 fuzzing 套件，参考价值。

##### [B] GraphicsFuzz (GLF)
- 类型：开源项目
- 链接：https://github.com/google/graphicsfuzz
- 总结：面向 GPU 着色器编译器的差分测试框架（对应 Many-core Compiler Fuzzing 论文）。GPU 场景差分。
- 评分理由：GPU 编译器差分测试工具，参考价值。

### 方向 5：LLM 代码自我修复 / 自调试 / 执行反馈

#### 论文（20 篇）

##### [A] Debug like a Human: A Large Language Model Debugger via Verifying Runtime Execution Step by Step (LDB)
- 类型：论文
- 链接：ICLR 2024，https://arxiv.org/pdf/2402.16906v5
- 总结：将程序切分为基本块，逐步跟踪运行时中间变量值作为执行反馈，驱动 LLM 修复生成代码。执行反馈粒度细、可解释。
- 评分理由：执行反馈驱动修复，直接相关。

##### [B] LeDex: Training LLMs to Better Self-Debug and Explain Code
- 类型：论文
- 链接：2024，https://arxiv.org/html/2405.18649
- 总结：用"错误代码解释 + 代码精炼"的链式轨迹训练模型，通过执行验证过滤数据以提升自调试能力。训练自调试模型。
- 评分理由：训练自调试模型，参考价值。

##### [B] RLEF: Grounding Code LLMs in Execution Feedback with Reinforcement Learning
- 类型：论文
- 链接：2024，https://arxiv.org/html/2410.02089v2
- 总结：端到端强化学习教模型利用执行反馈迭代改进代码，优于独立采样。RL 与执行反馈结合。
- 评分理由：RL+执行反馈，参考价值。

##### [A] PerfCodeGen: Improving Performance of LLM Generated Code with Execution Feedback
- 类型：论文
- 链接：FORGE 2025 @ ICSE，https://arxiv.org/html/2412.03578
- 总结：基于测试用例执行时的运行时反馈做自精炼，提升生成代码性能。获 ACM SIGSOFT 杰出论文奖。性能优化视角。
- 评分理由：执行反馈提升性能，直接相关。

##### [A] An Iterative Test-and-Repair Framework for Competitive Code Generation (FixAudit)
- 类型：论文
- 链接：2026，https://arxiv.org/html/2604.05560v2
- 总结：从单个初始候选出发，通过"失败测试→修复"的测试-修复循环迭代改进代码。测试-修复闭环。
- 评分理由：测试-修复闭环，直接相关。

##### [B] AgentForge: Execution-Grounded Multi-Agent LLM Framework for Autonomous Software Engineering
- 类型：论文
- 链接：2026，https://arxiv.org/pdf/2604.13120v1
- 总结：Planner/Coder/Tester/Debugger/Critic 五智能体框架，用沙箱执行验证与执行反馈驱动修复。多智能体协作。
- 评分理由：多智能体修复框架，参考价值。

##### [B] CYCLE: Learning to Self-Refine the Code Generation
- 类型：论文
- 链接：2024，https://arxiv.org/pdf/2403.18746
- 总结：代码自动跑测试套件，将失败用例与执行反馈回灌模型进行自精炼。测试反馈自精炼。
- 评分理由：测试反馈自精炼，参考价值。

##### [B] SelfEvolve: A Code Evolution Framework via Large Language Models
- 类型：论文
- 链接：2023，https://arxiv.org/pdf/2306.02907
- 总结：利用错误信息（含执行反馈）迭代修订 buggy 程序，形成代码进化循环。执行反馈进化。
- 评分理由：执行反馈进化，参考价值。

##### [A] Self-Edit: Fault-Aware Code Editor for Code Generation
- 类型：论文
- 链接：2023，https://arxiv.org/pdf/2305.04087v5.pdf
- 总结：在示例测试上执行生成代码，将执行结果包装成注释引导"故障感知编辑器"修正。执行结果引导编辑。
- 评分理由：执行结果引导编辑，直接相关。

##### [B] CodeChain: Towards Modular Code Generation Through Chain of Self-revisions with Representative Sub-modules
- 类型：论文
- 链接：2023，https://ar5iv.labs.arxiv.org/html/2310.08992
- 总结：通过"自修订链"复用/适配代表性子模块，迭代修订代码。模块化自修订。
- 评分理由：模块化自修订，参考价值。

##### [A] Natural Language to Code Translation with Execution (MBR-Exec)
- 类型：论文
- 链接：2022，https://arxiv.org/pdf/2204.11454
- 总结：执行每个候选程序以近似语义等价，用执行结果做最小贝叶斯风险解码选择。执行反馈选择候选。
- 评分理由：执行反馈选择候选，直接相关。

##### [B] CodeRanker: A Neural Ranker for Predicting the Correctness of Sampled Programs
- 类型：论文
- 链接：2022，https://www.microsoft.com/en-us/research/wp-content/uploads/2022/10/code_ranker_final.pdf
- 总结：以代码执行正确性为监督信号训练神经排序器，用于不执行情况下选择正确候选。执行反馈训练排序器。
- 评分理由：执行反馈训练排序器，参考价值。

##### [B] Sifting through the Chaff: On Utilizing Execution Feedback for Ranking the Generated Code Candidates (RankEF)
- 类型：论文
- 链接：2024，https://arxiv.org/pdf/2408.13976v2.pdf
- 总结：利用执行反馈（而非仅分类标签）对生成代码候选排序，改进 CodeRanker 类方法。执行反馈排序。
- 评分理由：执行反馈排序，参考价值。

##### [B] Top Pass: Improve Code Generation by Pass@k-Maximized Code Ranking
- 类型：论文
- 链接：2024，https://arxiv.org/html/2408.05715
- 总结：以最大化 pass@k 为目标对候选程序排序，提升执行通过率。候选排序优化。
- 评分理由：候选排序优化，参考价值。

##### [B] RepairAgent: An Autonomous, LLM-Based Agent for Program Repair
- 类型：论文
- 链接：2024，https://arxiv.org/pdf/2403.17134v1.pdf
- 总结：将 LLM 作为自主智能体，通过信息收集、搜索与候选修复实验（含测试执行验证）修复缺陷。自主修复智能体。
- 评分理由：自主修复智能体，参考价值。

##### [B] Agentic Program Repair from Test Failures at Scale: A Neuro-symbolic approach with static analysis and test execution feedback
- 类型：论文
- 链接：2025，https://arxiv.org/html/2507.18755
- 总结：ReAct 智能体基于测试失败与静态分析反馈，在大规模软件上执行修复动作。神经符号修复。
- 评分理由：神经符号修复，参考价值。

##### [B] RLTF: Reinforcement Learning from Unit Test Feedback
- 类型：论文
- 链接：2023，https://ar5iv.labs.arxiv.org/html/2307.04349
- 总结：在线 RL 框架，以多粒度单元测试反馈作为奖励信号精炼程序合成模型。RL+测试反馈。
- 评分理由：RL+测试反馈，参考价值。

##### [B] CodeRL: Mastering Code Generation through Pretrained Models and Deep Reinforcement Learning
- 类型：论文
- 链接：NeurIPS 2022，https://openreview.net/references/pdf?id=Q44NYaKcM
- 总结：以单元测试预测正确性的 critic 提供稠密反馈，指导代码生成 actor 迭代改进。actor-critic 代码生成。
- 评分理由：RL 代码生成，参考价值。

##### [B] StepCoder: Improve Code Generation with Reinforcement Learning from Compiler Feedback
- 类型：论文
- 链接：2024，https://arxiv.org/html/2402.01391v1
- 总结：将代码生成拆分为"已完成代码 + 剩余代码"，用编译器反馈做 RL 训练。编译器反馈 RL。
- 评分理由：编译器反馈 RL，参考价值。

##### [B] InterCode: Standardizing and Benchmarking Interactive Coding with Execution Feedback
- 类型：论文
- 链接：ICLR 2024，https://www.proceedings.com/content/075/075280-2879open.pdf
- 总结：标准化"代码-执行反馈"交互式编码基准，验证执行反馈对模型提升的显著作用。交互式编码基准。
- 评分理由：交互式编码基准，参考价值。

#### 开源项目（10 个）

##### [A] SWE-agent
- 类型：开源项目
- 链接：https://github.com/SWE-agent/SWE-agent
- 总结：把 LLM 变成软件工程智能体，通过 Agent-Computer Interface 在真实仓库中修复 GitHub issue（SWE-bench 12.29%）。工程成熟。
- 评分理由：软件工程智能体，直接可用。

##### [A] OpenHands
- 类型：开源项目
- 链接：https://github.com/All-Hands-AI/OpenHands
- 总结：自主编码智能体，读仓库、编辑文件、运行 shell 与测试并重试直至完成，Docker 沙箱隔离执行。功能全面。
- 评分理由：自主编码智能体，直接可用。

##### [B] Aider
- 类型：开源项目
- 链接：https://github.com/Aider-AI/aider/
- 总结：终端 AI 结对编程，每次改动后自动 lint 和跑测试，依据测试反馈修复问题。轻量易用。
- 评分理由：测试反馈修复工具，参考价值。

##### [A] AutoCodeRover
- 类型：开源项目
- 链接：https://github.com/AutoCodeRoverSG/auto-code-rover
- 总结：自主程序修复工具，AST 感知代码搜索 + 测试执行验证，SWE-bench lite 修复率高。搜索+验证结合。
- 评分理由：自主修复工具，直接可用。

##### [A] Agentless
- 类型：开源项目
- 链接：https://github.com/OpenAutoCoder/Agentless
- 总结：无 agent 脚手架，简单"定位→修复→验证"流程，SWE-bench 50.8%（Claude）。简洁高效。
- 评分理由：简单高效修复流程，直接可用。

##### [B] RepairAgent
- 类型：开源项目
- 链接：https://github.com/sola-st/RepairAgent
- 总结：首个自主 LLM 程序修复智能体，规划并执行修复动作，在 Defects4J 上验证。自主修复。
- 评分理由：自主修复智能体，参考价值。

##### [A] PerfCodeGen
- 类型：开源项目
- 链接：https://github.com/SalesforceAIResearch/perfcodegen
- 总结：论文官方仓库，用执行反馈提升 LLM 生成代码性能。性能优化工具。
- 评分理由：执行反馈优化工具，直接可用。

##### [B] InterCode
- 类型：开源项目
- 链接：https://github.com/InterCode-AI/InterCode
- 总结：交互式编码基准（含执行反馈），提供 Bash/SQL 环境的代码-执行交互评测。评测基础设施。
- 评分理由：交互式编码基准，参考价值。

##### [C] Web-Based Multi-Round Dialogue Code Repair Agent
- 类型：开源项目
- 链接：https://github.com/zetaolin913/Web-Based-Multi-Round-Dialogue-Code-Repair-Agent
- 总结：网页版多轮对话代码修复代理，集成沙箱执行与迭代修复验证。原型性质。
- 评分理由：原型项目，工程成熟度低。

##### [B] Agentic Code Fixer
- 类型：开源项目
- 链接：https://github.com/antonella-schiavoni/agentic-code-fixer
- 总结：多智能体生成补丁候选并评估，自动化代码修复系统。多智能体协作修复。
- 评分理由：多智能体修复系统，参考价值。

### 方向 6：程序合成验证 + 形式化方法用于 LLM 代码

#### 论文（21 篇）

##### [A] SymDiff: A Language-Agnostic Semantic Diff Tool for Imperative Programs
- 类型：论文
- 链接：CAV 2012，https://www.microsoft.com/en-us/research/project/symdiff-differential-program-verifier/overview/
- 总结：基于 Boogie 的双程序差分验证/行为等价检查工具，是"行为等价性自动判据"的经典形式化实现。语言无关、可扩展。
- 评分理由：行为等价验证经典工具，直接相关。

##### [A] Relational Verification Using Product Programs
- 类型：论文
- 链接：FM 2011，https://software.imdea.org/~jmcrespo/docs/FM2011.pdf
- 总结：用乘积程序(product programs)把双程序等价/关系性质规约为单程序验证，是等价判据的核心构造方法。可复用现有验证器。
- 评分理由：等价判据核心构造，直接相关。

##### [B] Thirty-seven Years of Relational Hoare Logic: Remarks on Its Principles and History
- 类型：论文
- 链接：arXiv 2020，https://arxiv.org/pdf/2007.06421
- 总结：系统梳理关系霍尔逻辑（RHL），为程序等价、相似性等双运行性质提供演绎验证基础。理论综述。
- 评分理由：RHL 理论基础，参考价值。

##### [B] A Relational Program Logic with Data Abstraction and Dynamic Framing
- 类型：论文
- 链接：ACM TOPLAS，https://dl.acm.org/doi/fullHtml/10.1145/3551497
- 总结：面向对象程序的通用关系程序逻辑，含链接程序等价证明规则（representation independence）。面向对象场景。
- 评分理由：面向对象等价逻辑，参考价值。

##### [B] S4Eq: Self-Supervised Learning to Prove Equivalence Between Programs via Semantics-Preserving Rewrite Rules
- 类型：论文
- 链接：arXiv 2109.10476，https://arxiv.org/pdf/2109.10476v1.pdf
- 总结：用语义保持重写规则序列证明两程序块等价，神经方法做程序等价的直接尝试。自监督学习。
- 评分理由：神经等价证明，参考价值。

##### [A] KLEE: Unassisted and Automatic Generation of High-Coverage Tests for Complex Systems Programs
- 类型：论文
- 链接：OSDI 2008
- 总结：符号执行自动生成高覆盖测试的奠基之作，为行为差异探测提供测试生成基础。工程影响深远。
- 评分理由：符号执行基础设施，直接相关。

##### [A] Large Language Model Powered Symbolic Execution (AutoBug)
- 类型：论文
- 链接：OOPSLA 2025，https://mengrj.github.io/pdfs/autobug-oopsla25.pdf
- 总结：用 LLM 替代定理证明器作为符号执行推理引擎，直接支撑 LLM 生成代码的路径级验证。LLM+符号执行。
- 评分理由：LLM+符号执行，直接相关。

##### [A] Cottontail: Large Language Model-Driven Concolic Execution for Highly Structured Test Input Generation
- 类型：论文
- 链接：IEEE S&P 2026，https://www.computer.org/csdl/proceedings-article/sp/2026/606500c046/2bojwAJpW0g
- 总结：LLM 驱动的混合执行(concolic)引擎，为生成代码生成满足约束的结构化测试输入。LLM+concolic。
- 评分理由：LLM+concolic 测试生成，直接相关。

##### [B] Hybrid Concolic Testing with Large Language Models for Guided Path Exploration
- 类型：论文
- 链接：arXiv 2601.12274，https://arxiv.org/html/2601.12274v1
- 总结：LLM 与混合执行结合，辅助 SMT 求解与路径探索，用于生成代码的行为验证。路径探索增强。
- 评分理由：LLM+concolic 验证，参考价值。

##### [A] Inference-Time Code Selection via Symbolic Equivalence Partitioning
- 类型：论文
- 链接：arXiv 2604.06485，https://arxiv.org/html/2604.06485v2
- 总结：用反例驱动符号执行搜索使两程序执行结果不同的输入，直接实现行为等价/不等价判定。推理时选择。
- 评分理由：符号等价划分选择候选，直接相关。

##### [B] SpecGen: Automated Generation of Formal Program Specifications via Large Language Models
- 类型：论文
- 链接：ICSE 2025，https://arxiv.org/abs/2401.08807v3
- 总结：LLM 自动生成前置/后置条件与循环不变式，为验证 LLM 代码提供规范来源。规范生成。
- 评分理由：LLM 生成规范，参考价值。

##### [B] DafnyBench: A Benchmark for Formal Software Verification
- 类型：论文
- 链接：2024，https://arxiv.org/pdf/2406.08467
- 总结：1000+ Dafny 程序基准，评测 LLM 编写可验证代码能力，是验证代码生成的核心基准。规模大。
- 评分理由：验证代码基准，参考价值。

##### [B] VerifyThisBench: Generating Code, Specifications, and Proofs All at Once
- 类型：论文
- 链接：arXiv 2505.19271，https://arxiv.org/html/2505.19271v1
- 总结：端到端评测 LLM 同时生成代码、规范与证明，揭示验证代码生成全链路瓶颈。全链路评测。
- 评分理由：验证代码生成评测，参考价值。

##### [B] CLEVER: A Curated Benchmark for Formally Verified Code Generation
- 类型：论文
- 链接：arXiv 2505.13938，https://arxiv.org/pdf/2505.13938
- 总结：HumanEval 的 161 个 Lean 规范基准，含"规范等价性证明"阶段，直接涉及行为等价判据。Lean 生态。
- 评分理由：Lean 规范基准，参考价值。

##### [A] VERINA: Benchmarking Verifiable Code Generation
- 类型：论文
- 链接：ICLR 2026，https://en.papernotes.org/ICLR2026/code_intelligence/verina_benchmarking_verifiable_code_generation/
- 总结：将可验证代码生成拆为 CodeGen/SpecGen/ProofGen 三任务，规范评估结合定理证明+全覆盖测试。评测框架完整。
- 评分理由：可验证代码生成评测框架，直接相关。

##### [B] VeriContest: A Competitive-Programming Benchmark for Verifiable Code Generation
- 类型：论文
- 链接：arXiv 2605.08553，https://arxiv.org/html/2605.08553v1
- 总结：竞编程式可验证代码生成基准，量化规范/证明生成瓶颈。面向竞赛场景。
- 评分理由：可验证代码基准，参考价值。

##### [B] ATLAS: Automated Toolkit for Large-Scale Verified Code Synthesis
- 类型：论文
- 链接：arXiv 2512.10173，https://arxiv.org/html/2512.10173v2
- 总结：自动化合成 2.7K 带机器可检查证明的 Dafny 程序，缓解验证代码训练数据瓶颈。数据合成。
- 评分理由：验证代码数据合成，参考价值。

##### [B] AlphaVerus: Bootstrapping Formally Verified Code Generation through Self-Improving Translation and Treefinement
- 类型：论文
- 链接：arXiv 2412.06176，https://arxiv.org/pdf/2412.06176v1
- 总结：自改进框架用验证器反馈迭代生成 Verus 形式化验证代码。验证器反馈生成。
- 评分理由：验证器反馈生成，参考价值。

##### [A] Program Semantic Inequivalence Game with Large Language Models (SInQ)
- 类型：论文
- 链接：arXiv 2505.03818，https://arxiv.org/html/2505.03818v1
- 总结：以"等价需机器可检查证明 / 不等价需发散输入"的游戏形式，把程序等价判定交给 LLM 并验证。游戏化验证。
- 评分理由：LLM 等价判定游戏化验证，直接相关。

##### [A] Towards Verified Code Reasoning by LLMs
- 类型：论文
- 链接：arXiv 2509.26546，https://arxiv.org/html/2509.26546v2
- 总结：抽取 LLM 推理步骤的形式表示并用验证工具自动核验，防止代码推理幻觉。推理形式化核验。
- 评分理由：LLM 推理形式验证，直接相关。

##### [A] Clover: Closed-Loop Verifiable Code Generation
- 类型：论文
- 链接：2024，https://www.recodaify.com/stanford-researchers-introduce-clover-closed-loop-verifiable-code-generation-that-checks-consistencies-among-code-doc-strings-and-annotations-and-enforces-correctness-in-ai-generated/
- 总结：生成-验证闭环，通过代码/规范/文档一致性检查保证 LLM 生成代码正确性。闭环验证。
- 评分理由：闭环验证代码生成，直接相关。

#### 开源项目（12 个）

##### [A] KLEE
- 类型：开源项目
- 链接：https://github.com/klee/klee
- 总结：LLVM 位码符号虚拟机，行为差异/测试生成的基础设施。工程成熟、生态完善。
- 评分理由：符号执行基础设施，直接可用。

##### [A] Z3
- 类型：开源项目
- 链接：https://github.com/Z3Prover/z3
- 总结：约束求解核心，支撑符号执行、等价检查、路径条件求解。微软出品、性能卓越。
- 评分理由：SMT 求解基础设施，直接可用。

##### [A] CBMC
- 类型：开源项目
- 链接：https://github.com/diffblue/cbmc
- 总结：把 C/C++ 程序与断言编码为 SAT 求解，验证数组越界、指针安全等行为性质。有界模型检查。
- 评分理由：有界模型检查工具，直接可用。

##### [B] SeaHorn
- 类型：开源项目
- 链接：https://github.com/seahorn/seahorn
- 总结：SMT 有界模型检查 + CHC 软件模型检查（不变式推断），可验证 LLM 生成代码。LLVM 生态。
- 评分理由：LLVM 验证框架，参考价值。

##### [B] Why3
- 类型：开源项目
- 链接：https://github.com/DSiSc/why3
- 总结：WhyML 规范语言 + 多后端定理证明器，生成并验证验证条件(VC)。演绎验证平台。
- 评分理由：演绎验证平台，参考价值。

##### [B] Boogie
- 类型：开源项目
- 链接：https://github.com/boogie-org/boogie
- 总结：SymDiff、Dafny 等验证工具的共同中间层，行为等价检查的载体。中间验证语言。
- 评分理由：验证中间层，参考价值。

##### [A] SymDiff
- 类型：开源项目
- 链接：https://www.microsoft.com/en-us/research/project/symdiff-differential-program-verifier/overview/
- 总结：基于 Boogie 的双程序差分验证，直接实现程序行为等价/语义差异判定。微软出品。
- 评分理由：行为等价验证工具，直接可用。

##### [B] angr
- 类型：开源项目
- 链接：https://github.com/angr/angr
- 总结：二进制级符号执行与约束求解，可对编译后代码做行为分析。二进制分析框架。
- 评分理由：二进制分析框架，参考价值。

##### [B] Rosette
- 类型：开源项目
- 链接：https://github.com/emina/rosette
- 总结：Solver-aided host language，支持程序合成与等价/属性验证的 DSL 开发。求解器辅助语言。
- 评分理由：求解器辅助语言，参考价值。

##### [A] ConcoLLMic
- 类型：开源项目
- 链接：https://github.com/ConcoLLMic/ConcoLLMic
- 总结：LLM agent 驱动的混合执行，免去手写符号解释器，直接面向 LLM 代码验证。agentic concolic。
- 评分理由：LLM+concolic 工具，直接可用。

##### [A] congruent-eq
- 类型：开源项目
- 链接：https://github.com/satchmakua/congruent-eq
- 总结：用差分测试 + Z3 符号执行证明 AI 重构函数与原函数行为等价或给出反例。差分+符号执行。
- 评分理由：差分+符号执行等价检查，直接可用。

##### [B] Dafny
- 类型：开源项目
- 链接：https://github.com/dafny-lang/dafny
- 总结：自带规范语言与自动验证器，是"LLM 生成可验证代码"最常用目标语言之一。验证感知语言。
- 评分理由：验证语言，参考价值。
