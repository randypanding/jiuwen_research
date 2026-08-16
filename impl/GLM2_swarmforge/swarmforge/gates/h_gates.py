"""H1-H8 硬门禁与 S 软门禁的具体实现。

每个门是纯决策逻辑：消费判别侧证据，产出 GateResult。
执行（构建/跑测/沙箱执行）由 verifier 的执行面产生证据，本模块不执行进程——
这保证门禁可离线测试、可重放、可在最简环境机械运行。

证据 kind 契约（verifier 执行面必须产出的形态）：
  build_report      H1  {compile_ok, type_errors[], lint_errors[], tool_versions{}}
  test_report       H2  {total, passed, failed, errors, skipped, property_failures[]}
  scenario_results  H3  {results: [ScenarioResult.to_dict()...], fail_to_pass[], pass_to_pass[]}
  contract_diff     H4  {removed_symbols[], changed_signatures[], added_symbols[], breaking[]}
  diff_report       H5  DifferentialReport.to_dict()
  golden_result     H5  {verdict: pass|fail|inconclusive, detail}
  guard_report      H6  {path_violations[], forbidden_deps[], license_violations[], secret_findings[]}
  drift_report      H7  {orphans[], missing_anchors[], bypasses[], stale_clauses[]}
  budget_report     H8  {tokens_used, token_cap, wallclock_used_s, wallclock_cap_s, per_role{}}
"""
from __future__ import annotations

import fnmatch
from typing import Optional

from ..oracle.schema import DiffConclusion
from ..specrepo.rregistry import RLevel
from .algebra import GateContext, GateResult, Verdict


class H1BuildGate:
    """H1 构建/类型/静态分析：语法与结构底线。"""
    gate_id = "H1"
    description = "build / typecheck / static analysis"

    def evaluate(self, ctx: GateContext) -> GateResult:
        rep = ctx.verified_evidence("build_report")
        problems = []
        if not rep.get("compile_ok", False):
            problems.append("compile failed")
        problems += [f"type: {e}" for e in rep.get("type_errors", [])]
        problems += [f"lint: {e}" for e in rep.get("lint_errors", [])]
        if problems:
            return GateResult(self.gate_id, Verdict.FAIL, True,
                              "; ".join(problems[:5]), {"problem_count": len(problems)})
        return GateResult(self.gate_id, Verdict.PASS, True, "clean build")


class H2TestGate:
    """H2 单元与属性测试：局部行为。属性失败按阻断处理。"""
    gate_id = "H2"
    description = "unit & property tests"

    def evaluate(self, ctx: GateContext) -> GateResult:
        rep = ctx.verified_evidence("test_report")
        failed = rep.get("failed", 0) + rep.get("errors", 0)
        prop_fail = rep.get("property_failures", [])
        if failed > 0 or prop_fail:
            return GateResult(
                self.gate_id, Verdict.FAIL, True,
                f"{failed} failing, {len(prop_fail)} property failures",
                {"failed": failed, "property_failures": prop_fail[:5]},
            )
        return GateResult(self.gate_id, Verdict.PASS, True,
                          f"{rep.get('passed', 0)}/{rep.get('total', 0)} passed")


class H3HoldoutGate:
    """H3 场景 holdout：oracle 主体，守护 L1 意图。

    FAIL_TO_PASS：本波次目标场景必须通过；
    PASS_TO_PASS：回归检查不得破坏（regression 崩 = FAIL）。
    """
    gate_id = "H3"
    description = "scenario holdout suite (L1 oracle)"

    def evaluate(self, ctx: GateContext) -> GateResult:
        rep = ctx.verified_evidence("scenario_results")
        results = {r["scenario_id"]: r["outcome"] for r in rep.get("results", [])}
        f2p = rep.get("fail_to_pass", [])
        p2p = rep.get("pass_to_pass", [])
        unmet = [s for s in f2p if results.get(s) != "pass"]
        regressed = [s for s in p2p if results.get(s, "pass") not in ("pass", "skip")]
        missing = [s for s in f2p + p2p if s not in results]
        if unmet or regressed or missing:
            return GateResult(
                self.gate_id, Verdict.FAIL, True,
                f"fail_to_pass unmet={unmet} regressed={regressed} missing={missing}",
                {"unmet": unmet, "regressed": regressed, "missing": missing},
            )
        return GateResult(self.gate_id, Verdict.PASS, True,
                          f"{len(f2p)} f2p + {len(p2p)} p2p green")


class H4ContractGate:
    """H4 契约面提取 + 破坏性变更检测：L2 的机械见证（R1/R2 兼容性）。"""
    gate_id = "H4"
    description = "contract face & breaking change detection"

    def evaluate(self, ctx: GateContext) -> GateResult:
        rep = ctx.verified_evidence("contract_diff")
        breaking = rep.get("breaking", [])
        # breaking 变更只有在显式声明主版本升级时才可放行（由 verifier 在证据里声明）
        if breaking and not rep.get("major_bump_declared", False):
            return GateResult(
                self.gate_id, Verdict.FAIL, True,
                f"breaking changes without major bump: {breaking[:5]}",
                {"breaking": breaking[:10]},
            )
        return GateResult(self.gate_id, Verdict.PASS, True,
                          f"contract intact; breaking={len(breaking)} "
                          f"(declared={rep.get('major_bump_declared', False)})")


class H5DifferentialGate:
    """H5 差分测试 / 黄金输出：spec 沉默检测 + R3 逐行语义。

    - 多实例：DIFFERENCE_FOUND → FAIL（spec 沉默须先由 moderator 收敛）；
      INCONCLUSIVE → FAIL 并升级统计通道。
    - R3 黄金锁定制品：golden verdict 必须 pass；inconclusive（manifest 不一致）
      → 门禁 INCONCLUSIVE，不得据此放行。
    - 单实例 R0 常规路径：SKIP（差分不适用；抽样审计另行触发 N=3 校准）。
    """
    gate_id = "H5"
    description = "differential testing / golden outputs"

    def evaluate(self, ctx: GateContext) -> GateResult:
        if "diff_report" not in ctx.evidence and "golden_result" not in ctx.evidence:
            # 无差分证据：R0 单实例常规路径
            r0_only = ctx.config.get("r0_single_instance", True)
            if r0_only:
                return GateResult(self.gate_id, Verdict.SKIP, True,
                                  "N=1 R0 path; differential N/A (audit sampling covers)")
            return GateResult(self.gate_id, Verdict.INCONCLUSIVE, True,
                              "differential evidence missing")

        if "diff_report" in ctx.evidence:
            rep = ctx.verified_evidence("diff_report")
            conc = rep.get("conclusion")
            if conc == DiffConclusion.DIFFERENCE_FOUND.value:
                return GateResult(
                    self.gate_id, Verdict.FAIL, True,
                    f"spec silence detected: divergent_inputs={rep.get('divergent_inputs')}",
                    {"conclusion": conc, "detail": rep.get("detail", "")},
                )
            if conc == DiffConclusion.INCONCLUSIVE.value:
                return GateResult(
                    self.gate_id, Verdict.FAIL, True,
                    "nondeterminism unresolved; statistical channel required",
                    {"conclusion": conc, "suspects": rep.get("nondet_suspects", [])},
                )

        if "golden_result" in ctx.evidence:
            gold = ctx.verified_evidence("golden_result")
            verdict = gold.get("verdict")
            if verdict == "fail":
                return GateResult(self.gate_id, Verdict.FAIL, True,
                                  f"golden mismatch: {gold.get('detail', '')}")
            if verdict == "inconclusive":
                return GateResult(self.gate_id, Verdict.INCONCLUSIVE, True,
                                  f"golden manifest invalid: {gold.get('detail', '')}")

        return GateResult(self.gate_id, Verdict.PASS, True, "differential/green")


class H6GuardGate:
    """H6 不变量与运行时护栏：宪法的可机械化部分。

    路径越界 / 违禁依赖 / 许可冲突 / 秘密泄漏，任一命中即 FAIL。
    """
    gate_id = "H6"
    description = "invariants & runtime guardrails"

    FORBIDDEN_DEP_PATTERNS = [
        # 示例策略：telnet/ftp 等明文协议库禁入；具体清单由 config 提供
        "telnetlib*", "ftplib*",
    ]

    def evaluate(self, ctx: GateContext) -> GateResult:
        rep = ctx.verified_evidence("guard_report")
        violations = []
        violations += [f"path: {p}" for p in rep.get("path_violations", [])]
        deps = rep.get("forbidden_deps", []) or self._scan_deps(ctx, rep)
        violations += [f"dep: {d}" for d in deps]
        violations += [f"license: {l}" for l in rep.get("license_violations", [])]
        violations += [f"secret: {s}" for s in rep.get("secret_findings", [])]
        if violations:
            return GateResult(self.gate_id, Verdict.FAIL, True,
                              "; ".join(violations[:5]), {"count": len(violations)})
        return GateResult(self.gate_id, Verdict.PASS, True, "guardrails intact")

    def _scan_deps(self, ctx: GateContext, rep: dict) -> list[str]:
        """证据未声明违禁依赖时，对声明的依赖清单做模式匹配兜底。"""
        declared = rep.get("declared_deps", [])
        extra_forbidden = ctx.config.get("forbidden_dep_patterns", [])
        patterns = self.FORBIDDEN_DEP_PATTERNS + list(extra_forbidden)
        return [d for d in declared for p in patterns if fnmatch.fnmatch(d, p)]


class H7DriftGate:
    """H7 spec↔code 漂移检测：真值一致性（reconciler 的机械部分）。

    四类硬错误（无良性解释空间，直接阻断）：
      orphans          代码标注引用了不存在的条款（孤儿注解）
      missing_anchors  bound 条款声明了锚点但代码中无任何覆盖
      bypasses         依赖了未在 spec 声明的契约面（R1/R2）
      stale_clauses    行为契约哈希变化但代码未跟（收割期）
    R3 冻结制品显式豁免 missing_anchors（前向追加语义）。
    """
    gate_id = "H7"
    description = "spec<->code drift detection"

    def evaluate(self, ctx: GateContext) -> GateResult:
        rep = ctx.verified_evidence("drift_report")
        orphans = rep.get("orphans", [])
        missing = rep.get("missing_anchors", [])
        bypasses = rep.get("bypasses", [])
        stale = rep.get("stale_clauses", [])
        problems = []
        if orphans:
            problems.append(f"orphan annotations: {orphans[:5]}")
        if missing:
            problems.append(f"bound clauses without code coverage: {missing[:5]}")
        if bypasses:
            problems.append(f"undeclared contract dependencies: {bypasses[:5]}")
        if stale:
            problems.append(f"stale clauses: {stale[:5]}")
        if problems:
            return GateResult(self.gate_id, Verdict.FAIL, True,
                              "; ".join(problems), {
                                  "orphans": len(orphans), "missing": len(missing),
                                  "bypasses": len(bypasses), "stale": len(stale),
                              })
        return GateResult(self.gate_id, Verdict.PASS, True, "no drift")


class H8BudgetGate:
    """H8 成本/资源/性能预算：经济与非功能约束（合取否决型）。"""
    gate_id = "H8"
    description = "cost / resource / performance budget"

    def evaluate(self, ctx: GateContext) -> GateResult:
        rep = ctx.verified_evidence("budget_report")
        token_cap = rep.get("token_cap", ctx.config.get("token_cap", 0)) or 0
        tokens = rep.get("tokens_used", 0)
        wall_cap = rep.get("wallclock_cap_s", ctx.config.get("wallclock_cap_s", 0)) or 0
        wall = rep.get("wallclock_used_s", 0.0)
        breaches = []
        if token_cap and tokens > token_cap:
            breaches.append(f"tokens {tokens} > cap {token_cap}")
        if wall_cap and wall > wall_cap:
            breaches.append(f"wallclock {wall:.1f}s > cap {wall_cap}s")
        if breaches:
            return GateResult(self.gate_id, Verdict.FAIL, True,
                              "; ".join(breaches),
                              {"tokens_used": tokens, "token_cap": token_cap,
                               "wallclock_used_s": wall, "wallclock_cap_s": wall_cap})
        return GateResult(self.gate_id, Verdict.PASS, True,
                          f"tokens={tokens}/{token_cap or '∞'} wall={wall:.1f}s/{wall_cap or '∞'}")


class SoftJudgeGate:
    """S 软门禁：LLM-as-judge 的判词代数。

    输入 evidence "judge_outputs": [JudgeOutput.to_dict()...]
    采样集成规则（k 次采样多数决）：
      veto 票数 > k/2 → veto（阻断）
      abstain 票数 > 0 且无多数 veto → abstain（升级，永不默认通过）
      否则 no_veto
    """
    gate_id = "S"
    description = "LLM-as-judge soft gate (veto-only)"

    def evaluate(self, ctx: GateContext) -> GateResult:
        outs = ctx.verified_evidence("judge_outputs")
        if not outs:
            return GateResult(self.gate_id, Verdict.NOT_CONFIGURED, False,
                              "no judge outputs; S not configured")
        vetoes = [o for o in outs if o.get("verdict") == "veto"]
        abstains = [o for o in outs if o.get("verdict") == "abstain"]
        k = len(outs)
        if len(vetoes) * 2 > k:
            return GateResult(self.gate_id, Verdict.FAIL, True,
                              f"judge veto majority ({len(vetoes)}/{k})",
                              {"reasons": [r for o in vetoes for r in o.get("reasons", [])][:5]})
        if abstains:
            return GateResult(self.gate_id, Verdict.INCONCLUSIVE, True,
                              f"judge abstained ({len(abstains)}/{k}); human review required")
        return GateResult(self.gate_id, Verdict.PASS, True,
                          f"no veto ({k} samples)")


#: 全部门禁注册表（按 成本升序 fail-fast 排列：机械静态 → 执行 → 差分）
ALL_GATES: list = [
    H1BuildGate(),     # 秒级
    H6GuardGate(),     # 秒级（策略匹配）
    H8BudgetGate(),    # 秒级（账目比对）
    H7DriftGate(),     # 静态扫描级
    H2TestGate(),      # 执行级
    H4ContractGate(),  # 提取比对级
    H3HoldoutGate(),   # 端到端执行级
    H5DifferentialGate(),  # 最昂贵：多实例差分/黄金重放
    SoftJudgeGate(),   # S：LLM 采样
]

GATE_BY_ID = {g.gate_id: g for g in ALL_GATES}


def gates_for_r_level(r: RLevel) -> list:
    """按制品 R 级给出必须启用的门（REQUIRED_GATES 的物理投影）。"""
    from ..specrepo.rregistry import REQUIRED_GATES
    required = REQUIRED_GATES[r]
    return [g for g in ALL_GATES if g.gate_id in required]
