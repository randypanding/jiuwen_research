# Oracle 与 CI-gate 在 agentic 开发范式下的最佳实践 —— 研究素材库

> 状态：已完成首轮采集与**补充审查**（审查更新日期 2026-08-15）。本目录为策展后的研究素材库，供下一步分析使用。

## 收录标准（审查后）
- Oracle / CI-gate 主题下，**更新时间在三个月内（2026-05-15 至 2026-08-15）**的高质量论文、权威实践、活跃开源项目；
- 或**具重大意义**（奠基/事实标准/标杆），不受时效限制的先行工作（明确标注 `[奠基]`/`[重大]`）。
- 所有指向外部链接的条目均经 arXiv 页面或官方来源直接核验，未核验项已明确标注。

## 目录结构
```
oracle_ci_gate_research/
├── README.md
├── papers/
│   ├── 01_oracle_papers.md              # Oracle 学术论文（策展后 25 条）
│   └── 02_ci_gate_papers_practice.md    # CI-gate 论文+权威实践（策展后 22 条）
└── projects/
    └── 03_open_source_projects.md       # Oracle / CI-gate 开源项目（策展后 30+ 项）
```

## 各文件内容概览
- 01：三个月内核心新作（LLM-as-a-Verifier、All Smoke No Alarm、Verification Horizon、Building to the Test、LogicHunter、AEVAL、RESTOR、SEVRA-BENCH 等）+ 2026 上半年 oracle 基线（ORACLE-SWE、AJ-Bench、Agentic Rubrics 等）+ 重大意义经典（Oracle Problem、ALGO、LEVER、CODET、Reflexion、SWE-bench 等）。
- 02：三个月内 CI-gate 论文与厂商实践（Specification as Quality Gate、SWE-CI、AWS 系列、Galileo、Codex CLI 等）+ 重大意义先行工作（Rethinking Verification、AI 评审实证研究等）。
- 03：agent 验证/评估框架（oracle 核心）、CI 门禁/AI 评审、oracle/validator/流程门禁工具、开源 coding agent 四大类的核验后清单，标注活跃度与近三月状态。

## 审查要点（相对首轮版本）
- 移除无法核验的存疑 arXiv 条目与低价值重复项。
- 订正多处事实错误：AWS 发布时间、Harbor 指向、SWE-bench 归属、PR-Agent 仓库、agentevals 归属、Roo Code 停摆。
- 大量补充三个月内（2026-05 后）的最新高质量论文、厂商实践与开源项目。

## 下一步建议（待用户指示）
- 交叉分析 oracle 与 CI-gate 两类机制的内在关系（如 Building to the Test 对 CI-gate 设计的启示、oracle 信号强度与合并门禁的相关性）。
- 提炼 agentic 开发范式下的端到端 best-practices 流程。
- 按成熟度/维护状态对开源项目做落地选型评估。
- 产出研究报告或实践指南。