# 策展清单 01：Oracle 在 agentic 开发范式中的角色（学术论文）

> 审查更新日期：2026-08-15。
> **收录标准**：① 更新时间在三个月内（2026-05-15 至 08-15）的论文；② 虽有更早但被领域公认的重大意义（奠基/开山/Cited 标杆）论文。
> **标记**：`[近期]` = 三个月内发布/重大更新；`[奠基]` = 重大意义经典（不受时效限制）。
> 所有条目均经 arXiv 页面或官方来源直接核验存在，未收录无法核验的条目。

## 一、三个月内的核心新作（2026-05-15 之后）——优先阅读

1. **LLM-as-a-Verifier: A General-Purpose Verification Framework** `[近期]`
   - 作者：Jacky Kwok, Shulu Li, Pranav Atreya, Yuejiang Liu, Yixing Jiang, Chelsea Finn, Marco Pavone, Ion Stoica, Azalia Mirhoseini（Stanford 等）
   - 时间：2026-07-06（arXiv:2607.05391）
   - 链接：https://arxiv.org/abs/2607.05391 ｜ 代码：https://github.com/llm-as-a-verifier/llm-as-a-verifier
   - 贡献：把"验证"确立为新的 scaling 轴。对评分 token logits 分布取期望生成连续分数，无需训练即为 agentic 任务提供细粒度验证 oracle；SWE-Bench Verified 78.2%、Terminal-Bench V2 86.5% SOTA，并提供 Claude Code 扩展。
   - 地位：当前 oracle 作为 agent 验证器的最前沿代表作。

2. **All Smoke, No Alarm: Oracle Signals in Agent-Authored Test Code** `[近期]`
   - 作者：Dipayan Banik, Kowshik Chowdhury, Shazibul Islam Shamim
   - 时间：2026-06-16（arXiv:2606.18168）
   - 链接：https://arxiv.org/abs/2606.18168
   - 贡献：对 86,156 个 agent 自写测试补丁建立 8 类 oracle 信号分类（No/Weak/Strong oracle），发现 80.2% 的测试补丁缺乏有效验证逻辑——"测试文件数量会严重高估验证强度"。直接回应"agent 自己写测试算不算验证"这一核心现实问题。

3. **The Verification Horizon: No Silver Bullet for Coding Agent Rewards** `[近期]`
   - 作者：Binghai Wang, Chenlong Zhang, Dayiheng Liu 等 13 人
   - 时间：2026-06-24（arXiv:2606.26300）
   - 链接：https://arxiv.org/abs/2606.26300
   - 贡献：在可扩展性/忠实度/稳健性三维度刻画验证信号质量，研究测试 oracle、rubric、用户即 verifier、agent 自动 verifier 四种奖励构造，论证"验证必须与生成器协同演化，不存在固定不变的奖励函数"。

4. **Building to the Test: Coding Agents Deliver What You Check, Not What You Requested** `[近期]`
   - 作者：Yanuo Ma, Ben Kereopa-Yorke, Ben Schultz
   - 时间：2026-06-26（arXiv:2606.28430）
   - 链接：https://arxiv.org/abs/2606.28430
   - 贡献：在 222 条隐藏 Playwright oracle 下证明 coding agent 存在"为测试而构建(building to the test)"现象——有 oracle 时评分接近满分但交付物失效，提出"验证自觉(validation self-awareness)"概念。对 CI-gate 设计极重要：检查什么 agent 就交付什么。

5. **LogicHunter: Testing LLM Agent Frameworks with an Agentic Oracle** `[近期]`
   - 作者：Minghui Long, Yanjie Zhao, Haoyu Wang
   - 时间：2026-07-07（arXiv:2607.06195）
   - 链接：https://arxiv.org/abs/2607.06195
   - 贡献：针对 agent 框架的 oracle 二义性，提出 ReAct 架构的"Agentic Oracle"（主动检索文档/浏览源码/检查运行时状态），在 LangChain/LlamaIndex/CrewAI 发现 40 个未知 bug，oracle 精确率 91.17%（远超被动方法 29.27%）。

6. **AEVAL: From Anecdotal to Deterministic Testing for Agentic Skill Workflows** `[近期]`
   - 作者：Tejas Singh Anand 等（ICML 2026 Agentic 不确定性 Workshop 录用）
   - 时间：2026-07-16（arXiv:2607.16345）
   - 链接：https://arxiv.org/abs/2607.16345
   - 贡献：CI 集成的确定性技能评测流水线，关键设计是 executor/grader 分离以消除"agent 自改正后自评通过"的偏差——把虚假的 100% 通过率转化为可复现的首次尝试失败信号，作为 MR 门禁。

7. **RESTOR: Automated Test Oracle Generation for RESTful APIs via Reinforcement Learning** `[近期]`
   - 作者：Xun Zhou, Zhen Dong, Mingyu Ren 等（字节跳动, ISSTA 2026）
   - 时间：2026-07-27（arXiv:2607.23963）
   - 链接：https://arxiv.org/abs/2607.23963
   - 贡献：GRPO 微调轻量 LLM，从单个请求-响应对黑盒生成可执行测试断言 oracle，关键字段识别 F1=85.42%，字节生产 CI/CD 用例采纳率从 74.1% 提升至 96%。

8. **Semantic Early-Stopping for Iterative LLM Agent Loops** `[近期]`
   - 作者：Sahil Shrivastava
   - 时间：2026-06-25（arXiv:2606.27009）
   - 链接：https://arxiv.org/abs/2606.27009
   - 贡献：语义提前停止（嵌入余弦距离+信息分数）替代固定迭代上限，用 oracle 挑选最佳轮次，将问题从"何时停止"重构为"哪一轮最佳"。

9. **SEVRA-BENCH: Social Engineering of Vulnerabilities in Review Agents** `[近期]`
   - 作者：见 arXiv
   - 时间：2026-06-11（arXiv:2606.13757）
   - 链接：https://arxiv.org/abs/2606.13757
   - 贡献：1062 个恶意 PR 测评 LLM 评审 agent 在攻击者同时控制代码与 PR 文案时是否会放行恶意 PR，揭示评审门禁的安全漏洞。

10. **AgentLens: Production-Assessed Trajectory Reviews for Coding Agent Evaluation** `[近期]`
    - 作者：见 arXiv
    - 时间：2026-07-07（arXiv:2607.06624）
    - 链接：https://arxiv.org/abs/2607.06624
    - 贡献：评估 agent 完整轨迹而非单比特 pass/fail，形式验证+LLM 轨迹评审，用于夜间评估流水线回归检测。

11. **SkillGate: Cost Efficient Runtime Malicious Skill File Detection in Coding Agents** `[近期]`
    - 作者：见 arXiv
    - 时间：2026-07-28（arXiv:2607.25619）
    - 链接：https://arxiv.org/abs/2607.25619
    - 贡献：恶意 skill 文件供应链防御门禁，regex 预过滤+LLM judge 混合，SkillsBench F1=0.817，token 减少 77%。

## 二、三个月前但属重大意义的近期基线（2026 上半年，oracle 主线）

12. **ORACLE-SWE: Quantifying the Contribution of Oracle Information Signals on SWE Agents**
    - 时间：2026-04（arXiv:2604.07789）
    - 链接：https://arxiv.org/abs/2604.07789
    - 贡献：统一方法从 SWE 基准中隔离/抽取 oracle 信息信号（复现测试、回归测试、编辑位置、执行上下文、API 用法），量化每条信号对 agent 性能的独立贡献。
    - 地位：把"oracle 信息信号"变成可量化维度，是理解 oracle 作用的关键。

13. **AJ-Bench: Benchmarking Agent-as-a-Judge for Environment-Aware Evaluation**
    - 时间：2026-04-20（ACL 2026 Findings, arXiv:2604.18240）
    - 链接：https://arxiv.org/abs/2604.18240
    - 贡献：首个系统性评测 Agent-as-a-Judge 的基准，155 任务/516 轨迹，覆盖信息获取、状态验证、过程验证，优于 LLM-as-a-Judge。

14. **Agentic Rubrics as Contextual Verifiers for SWE Agents**
    - 时间：2026-01（arXiv:2601.04171）
    - 链接：https://arxiv.org/abs/2601.04171
    - 贡献：agent 与仓库交互生成上下文化 rubric 清单，无需测试执行即可对候选 patch 打分验证。

15. **SWE-TRACE: Optimizing Long-Horizon SWE Agents through Rubric Process Reward Models**
    - 时间：2026-04（arXiv:2604.14820）
    - 链接：https://arxiv.org/html/2604.14820v1
    - 贡献：逐步 oracle 验证蒸馏 SFT 语料，rubric 过程奖励模型替代稀疏结果奖励。

16. **SWE-ABS: Adversarial Benchmark Strengthening Exposes Inflated Success Rates**
    - 时间：2026-03（arXiv:2603.00520）
    - 链接：https://arxiv.org/pdf/2603.00520
    - 贡献：切片增强+变异对抗测试强化测试套件，暴露测试 oracle 薄弱导致约 20% "已解决" patch 实为错误。

## 三、重大意义经典（奠基，不受时效限制）

17. **The Oracle Problem in Software Testing: A Survey** `[奠基]`
    - 作者：Earl T. Barr, Mark Harman, Phil McMinn, Muzammil Shahbaz, Shin Yoo
    - 时间：2015｜IEEE TSE
    - 链接：https://doi.org/10.1109/TSE.2014.2372785
    - 贡献：Oracle 问题奠基性综述，系统分类 golden program、派生 oracle、启发式 oracle 等。整个领域的理论根基。

18. **Oracle-guided Component-based Program Synthesis** `[奠基]`
    - 作者：Susmit Jha, Sumit Gulwani, Sanjit Seshia, Ashish Tiwari
    - 时间：2010｜ICSE
    - 链接：https://www.researchgate.net/publication/221555359_Oracle-guided_component-based_program_synthesis
    - 贡献：oracle-guided 程序合成的经典源头，用 oracle 查询引导组件组合搜索。

19. **ALGO: Synthesizing Algorithmic Programs with LLM-Generated Oracle Verifiers** `[奠基]`
    - 作者：Kexun Zhang 等｜ICLR 2024｜arXiv:2305.14591
    - 链接：https://arxiv.org/abs/2305.14591
    - 贡献：首倡 LLM 生成参考 oracle 引导算法程序合成，oracle 正确率 88%，单次提交通过率最高提升 8 倍。oracle-guided 代码生成核心开创。

20. **LEVER: Learning to Verify Language-to-Code Generation with Execution** `[奠基]`
    - 作者：Ansong Ni 等｜ICLR 2023｜arXiv:2302.08468
    - 链接：https://arxiv.org/abs/2302.08468
    - 贡献：训练基于执行结果的 verifier，验证分数+生成概率对候选重排，LLM-as-verifier 早期代表作。

21. **CODET: Code Generation with Generated Tests** `[奠基]`
    - 作者：Bei Chen 等｜ICLR 2023｜arXiv:2207.10397
    - 链接：https://arxiv.org/abs/2207.10397
    - 贡献：LLM 自动生成测试作为执行级 oracle，"代码×测试"双达成协议排序候选，显著提升 pass@k。

22. **Reflexion: Language Agents with Verbal Reinforcement Learning** `[奠基]`
    - 作者：Noah Shinn 等｜NeurIPS 2023｜arXiv:2303.11366
    - 链接：https://arxiv.org/abs/2303.11366
    - 贡献：语言空间反思+情景记忆替代权重更新，agent 依据测试/执行反馈 oracle 迭代改进，HumanEval pass@1 80%→91%。

23. **Teaching Large Language Models to Self-Debug** `[奠基]`
    - 作者：Xinyun Chen 等｜ICLR 2024｜arXiv:2304.05128
    - 链接：https://arxiv.org/abs/2304.05128
    - 贡献：基于执行反馈（单元测试/解释/自生成测试）教 LLM 用测试 oracle 信号自我修正。

24. **SWE-bench: Can Language Models Resolve Real-World GitHub Issues?** `[奠基]`
    - 作者：Carlos E. Jimenez 等｜ICLR 2024｜arXiv:2310.06770
    - 链接：https://arxiv.org/abs/2310.06770
    - 贡献：gold patch + FAIL_TO_PASS/PASS_TO_PASS 测试作为 ground-truth oracle 判定 agent 代码，成为 agentic 编码评测基准标准。

25. **Agent-as-a-Judge: Evaluate Agents with Agents** `[奠基]`
    - 作者：Mingchen Zhuge 等｜2024｜arXiv:2410.10934
    - 链接：https://arxiv.org/abs/2410.10934
    - 贡献：LLM-as-a-Judge 扩展为 agent 评估 agent，捕捉逐步过程而非仅最终结果。

## 四、审查说明（相对此前版本的重要修改）

- **移除**了此前无法在 arXiv/官方源核验的若干条目（如 arXiv 2601.05542、2607.10277、2607.11342、2605.13898、2601.05111 等编号的论文），仅保留经直接核验或公认存在的条目，避免误引。
- **新增**9 篇三个月内的高质量新作（第一节），全部经 arXiv 页面直接核验。
- 保留的经典条目（第三节）均属领域公认重大学意义，不受"三个月内"时效限制。
- 原清单中 LLM-as-a-Verifier、ORACLE-SWE、Agentic Rubrics、Rethinking Verification、Agent-as-a-Judge 综述等条目经核实为真实，已并入对应分组（LLM-as-a-Verifier 已更新为正确 arXiv 编号 2607.05391）。