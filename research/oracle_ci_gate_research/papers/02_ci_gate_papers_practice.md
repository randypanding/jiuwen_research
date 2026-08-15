# 策展清单 02：CI-gate 在 agentic 开发范式中的应用（论文 + 权威实践）

> 审查更新日期：2026-08-15。
> **收录标准**：① 更新时间在三个月内（2026-05-15 至 08-15）的论文/权威实践；② 有重大意义的先行工作。
> **标记**：`[近期]` = 三个月内；`[重大]` = 重大意义先行工作。来源类型：论文 / 官博 / 博客 / 工程指南。

## 一、三个月内（2026-05-15 之后）——优先阅读

1. **The Specification as Quality Gate: Three Hypotheses on AI-Assisted Code Review** `[重大]`（2026-03-26，arXiv:2603.25773）
   - 链接：https://arxiv.org/abs/2603.25773
   - 贡献：论证没有可执行规格时，生成 agent 与评审 agent 推理自同一工件、错误相关，AI 评审"循环论证"（用 AI 审 AI 造的问题审不出来）。主张"规格优先+确定性验证流水线+AI 评审仅处理残差"的架构。这是理解 CI-gate 与 oracle 关系的关键理论。
   - 说明：发布于 3 个月前略早，但因对 CI-gate 主题具重大意义而收录。

2. **SWE-CI: Evaluating Agent Capabilities in Maintaining Codebases via Continuous Integration**（2026-03-04，arXiv:2603.03823）
   - 链接：https://arxiv.org/abs/2603.03823
   - 贡献：首个基于 CI 循环的仓库级基准，从静态功能正确性转向长期可维护性评测。说明：3 个月前略早，重大意义先行工作。

3. **AEVAL: From Anecdotal to Deterministic Testing for Agentic Skill Workflows** `[近期]`（2026-07-16，arXiv:2607.16345）
   - 链接：https://arxiv.org/abs/2607.16345
   - 贡献：CI 集成的确定性技能评测流水线，executor/grader 分离消除"自改正自评分"偏差，作为 MR 门禁。已在 Oracle 文件中收录，本处从 CI-gate 视角引用。

4. **SEVRA-BENCH: Social Engineering of Vulnerabilities in Review Agents** `[近期]`（2026-06-11，arXiv:2606.13757）
   - 链接：https://arxiv.org/abs/2606.13757
   - 贡献：1062 个恶意 PR 测评评审 agent 是否会放行恶意 PR，揭示评审门禁存在社会工程安全漏洞。

5. **SkillGate: Cost Efficient Runtime Malicious Skill File Detection in Coding Agents** `[近期]`（2026-07-28，arXiv:2607.25619）
   - 链接：https://arxiv.org/abs/2607.25619
   - 贡献：恶意 skill 文件供应链防御门禁，regex 预过滤+LLM judge 混合。

6. **AgentLens: Production-Assessed Trajectory Reviews for Coding Agent Evaluation** `[近期]`（2026-07-07，arXiv:2607.06624）
   - 链接：https://arxiv.org/abs/2607.06624
   - 贡献：评估完整轨迹而非单比特 pass/fail，用于夜间评估流水线回归检测。

7. **AWS — Balancing speed and safety: A control framework for AI coding agents** `[近期]`（AWS Security Blog）
   - 链接：https://aws.amazon.com/blogs/security/balancing-speed-and-safety-a-control-framework-for-ai-coding-agents/
   - 贡献：为 AI coding agent 建分层 AppSec 控制框架，CI 中按序执行 secrets/SAST/SCA/IaC 扫描并"critical finding 即 fail build"作为硬性门禁；含分支保护、规格即范围边界、hook。
   - 更正：此前版本误标为 2025，实际发布于 2026-07-30。

8. **AWS — Evaluating AI Agents: A production blueprint with Strands and AgentCore** `[近期]`（AWS ML Blog，与 Motorway 合著）
   - 链接：https://aws.amazon.com/blogs/machine-learning/evaluating-ai-agents-a-production-blueprint-with-strands-and-agentcore/
   - 贡献：两阶段评估策略、三层评估框架（工具/推理/输出质量阈值 95/85/90%）、五阶段部署流水线质量门禁、pass^k 一致性度量。

9. **AWS — The Agentic AI Security Scoping Matrix** `[近期]`（AWS Security Blog）
   - 链接：https://aws.amazon.com/blogs/security/the-agentic-ai-security-scoping-matrix-a-framework-for-securing-autonomous-ai-systems/
   - 贡献：按自主度四级（无/指定/受监督/完全自主）映射安全控制，是 agent gate 设计的分类学基础。

10. **AWS — Amazon Bedrock AgentCore now supports Bedrock Guardrails in policy** `[近期]`（官方 What's New, 2026-06 GA）
    - 链接：https://aws.amazon.com/about-aws/whats-new/2026/06/amazon-bedrock-agentcore-policy-guardrails-generally-available/
    - 贡献：AgentCore 网关层策略门禁，在 agent 代码之外拦截 prompt 注入/有害内容/敏感数据暴露。

11. **Galileo — How to bring CI/CD rigor to the agent development lifecycle** `[近期]`（Galileo Blog）
    - 链接：https://galileo.ai/blog/agent-cicd-development-lifecycle
    - 贡献：agent CI/CD 统计质量门禁（Wilson 置信区间三判定 gate）、分层评估流水线、分阶段发布与自动回滚。

12. **Galileo — Building Continuous Agent Evaluation Pipelines for Production** `[近期]`（Galileo Blog）
    - 链接：https://galileo.ai/blog/building-continuous-agent-evaluation-pipelines
    - 贡献：连续 agent 评估流水线，CI/CD 质量门禁（pre-commit 单测、PR 集成测试、pre-deploy 基准显著性检验）。

13. **Codex CLI — Verification Patterns: Seven Strategies for Ensuring Agent-Generated Code Actually Works** `[近期]`（danielvaughan, 2026-06-09）
    - 链接：https://codex.danielvaughan.com/2026/06/09/codex-cli-verification-patterns-ensuring-agent-generated-code-correctness-hooks-review-testing/
    - 贡献：含 Pattern 7 "CI 验证流水线——trust nothing, verify everything"，在 agent 影响范围之外的 CI 中做独立评审门禁。

14. **Codex — The Post-Merge Fate of Agentic Code** `[近期]`（danielvaughan, 2026-07-14）
    - 链接：https://codex.danielvaughan.com/2026/07/14/post-merge-fate-agentic-code-corrective-maintenance-security-codex-cli-guardian-review-posttooluse-defence/
    - 贡献：合并后 AI 贡献需多 49% 纠正性维护，主张 Guardian Auto-Review 作为 pre-merge gate。

## 二、重大意义先行工作（2025 及更早，实质支撑 CI-gate 落地）

15. **Rethinking Verification for LLM Code Generation: From Generation to Testing**（2025-07，arXiv:2507.06920）
    - 链接：https://arxiv.org/abs/2507.06920
    - 贡献：把 LLM 代码验证范式从"生成质量"转向"测试驱动"(TCG)，用测试充分性/多样性评估作为代码验证关卡；提出 SAGA 人机协作方法与 TCGBench。

16. **AI-Augmented CI/CD Pipelines: From Code Commit to Production with Autonomous Decisions**（2025，arXiv:2508.11867）
    - 链接：https://arxiv.org/abs/2508.11867
    - 贡献：LLM/自主体作为"策略受限的 co-pilot 并渐进成为决策者"参与 flaky test 判定、回滚、canary 提升等 CI/CD 决策点。

17. **On the Use of Agentic Coding: An Empirical Study of Pull Requests on GitHub**（2025）
    - 链接：https://www.researchgate.net/publication/395649563_On_the_Use_of_Agentic_Coding_An_Empirical_Study_of_Pull_Requests_on_GitHub
    - 贡献：实证 567 个 Claude Code 生成的 PR（157 项目），83.8% 被接受，揭示合并门禁对 agent 代码的实际约束与接受度。

18. **Does AI Code Review Lead to Code Changes? A Case Study of GitHub Actions**（2025，arXiv:2508.18771）
    - 链接：https://arxiv.org/abs/2508.18771
    - 贡献：人工评审 60% 带来代码改动，而 AI 评审仅 0.9%，说明纯 AI 评审作为合并门禁的采纳率严重不足。

19. **GitHub's Copilot Code Review: Can AI Spot Security Flaws Before You Commit?**（2025，arXiv:2509.13650）
    - 链接：https://arxiv.org/abs/2509.13650
    - 贡献：Copilot Code Review 对已知 CWE 漏洞检出低效、不一致，安全门禁不能依赖 AI 评审。

20. **Automated Code Review Using Large Language Models at Ericsson: An Experience Report**（ICSME 2025, arXiv:2507.19115）
    - 链接：https://arxiv.org/abs/2507.19115
    - 贡献：爱立信用 LLM+静态分析构建轻量评审工具，经验表明可辅助但需人工把关。

21. **Claude Code: Best practices for agentic coding**（Anthropic 官方实践）
    - 链接：https://blog.csdn.net/SDFsoul/article/details/149221981
    - 贡献：TDD 工作流——先写测试并确认"如预期失败"→提交→让 agent 持续迭代直到通过，作为 agent 输出验证关卡。

22. **Hitchhiker's Guide to AI-Native Engineering — Verification**（GitHub steveash, 2026）
    - 链接：https://github.com/steveash/hitchhikers-guide-to-ai-native-engineering/blob/main/guide/03-verification.md
    - 贡献：被剖析的 6 个仓库中 5 个对 PR 强制 CI 门禁；CI 在干净环境跑全量测试，能捕获本地钩子遗漏的问题。

## 三、审查说明（相对此前版本的重要修改）

- **新增**多篇三个月内的高质量论文与厂商实践（第一节），全部经 arXiv 页面或官方来源直接核验。
- **更正**：AWS control framework 发布日期由 2025 订正为 2026-07-30；补入其姊妹篇（Security Scoping Matrix、Bedrock AgentCore、Strands/AgentCore）。
- **移除**了此前清单中偏向低价值/难以核验的若干 CSDN 转载与重复条目，精简为"重大意义先行工作"。
- 保留了"AI 评审作为门禁"的实证研究（GitHub Actions、Copilot Code Review、Ericsson），因为它们直接回答"CI-gate 能否依赖 AI 评审照看"这一关键问题。
- 多处工具类条目（nullius、skillgate、spec-agent、right-hooks、agent-guardrails、CI-Copilot）已并入开源项目清单（03）统一管理，避免重复。