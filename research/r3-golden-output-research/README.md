# R3 级制品黄金输出与验证机制 · 资料搜集索引（审查版）

> 研究问题：如何为不可再生或逐行语义敏感的 R3 级制品（如加密、金额计算）设计黄金输出（Golden Output）与验证机制？
>
> 本目录为**第一步：广泛搜集 + 第二步：补充审查**的成果。审查版已按"近三个月（2026-05-15 之后）有更新/发表，或具有重大意义"的标准筛选，并修正链接与出处、剔除弱条目、补充 2026 年最新内容。**分析/综述留待下一步。**

## 子问题与对应文件

| 子问题 | 文件 | 条目数 |
| --- | --- | --- |
| 黄金输出的生成与维护：如何生成可信黄金输出并管理其演化 | [01-golden-output.md](01-golden-output.md) | 26 |
| 非确定性的容忍与检测：区分代码再生的非确定性（随机性、并发时序、LLM 采样）与真正行为偏差 | [02-nondeterminism.md](02-nondeterminism.md) | 28 |
| 差分测试在 R3 级制品上的轻量化应用：无 fan-out 下的有限差分验证（历史实例、变异分析等） | [03-differential-testing.md](03-differential-testing.md) | 34 |

## 审查动作摘要（2026-08-15）

- **修正链接**：insta → `mitsuhiko/insta`；NonDex/iDFlakies/IDoFT → 迁移后仓库；Cryptofuzz → `MozillaSecurity/cryptofuzz`；ApprovalTests.Python → `approvals` 组织；pytest-approval → `GIScience`。
- **更正出处**：Fujita 快照实证为 ICSME 2023（非期刊）；Lam flaky 纵向研究为 OOPSLA 2020（非 ISSTA）；《Automated Oracle Creation Support》为 ICSE 2012 的 Staats/Gay/Heimdahl（非 Fraser & Zeller）。
- **剔除弱条目**：停更多年的项目（kotlarmilos/flaky-tests、conan-deterministic-examples、nondex-rs、Cryptofuzz++）、非权威来源（GitHub Gist、HashHackers 博客、51Testing）、无法正规核验的条目（sci-hub 链接）、相关性弱的硬件重放论文（BugNet、SReplay）。
- **新增近三月/重大意义条目**（约 20 条）：TestEvo-Bench、LLMShot、LLM 非确定性归因（温度/随机性）、AI 代码可复现性实证、在线 SMC 置信序列、AI 智能体确定性重放（agrepl/rewind/Reprise）、Debian 14 强制可复现构建、DDYF、Stripe Spark 历史回放、Eq@DFuzz/Kaizen/Beyond BLEU、MIST-RL/AdverTest、PBT-Bench/PROGRESS、LLM4FP/TAO 等。
- **时效标注**：每条标注【近三月】【重大意义】【经典】【活跃】/【低活跃】。

## 与 R3 级制品最直接相关的近期证据（建议优先阅读）

1. **Stripe Spark 历史回放**（方向三 #26）：历史请求回放 + 当前 vs 候选实现差分，直接以金额计算为例，与本研究背景几乎同题。
2. **LLM 非确定性归因**（方向二 #13-14）：温度=0 仍不可复现的实证边界，是"区分随机性与真行为偏差"的直接依据。
3. **DDYF**（方向三 #6）：差分 oracle + 密码协议差分模糊，2026-05。
4. **TestEvo-Bench**（方向一 #4）：测试-代码共演化基准，2026-07。
5. **LLMShot**（方向一 #3）：LLM 辅助快照维护，ICSME 2025。

## 下一步建议

1. 按子问题对条目做质量分级（P0 权威论文 / 直接相关工具 / 背景参考）。
2. 提取各方向的代表性方法与机制，交叉对比。
3. 针对缺口定向补充检索（如"golden output cryptography / financial computation regression"、金额计算十进制验证论文）。
