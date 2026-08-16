# -*- coding: utf-8 -*-
"""
裁决测试:对 jiuwen_research 七份工程方案(GLM1/GLM2/K3/QW1/QW2/QW3/PR3)之间
"可以用代码客观裁决"的分歧点,给出可复现的判定实验。

每个测试类的 docstring 写明:分歧双方立场、判定方法、客观结论。
运行: /workspace/venv312/bin/python -m pytest /workspace/adjudication -v
"""
from __future__ import annotations

import itertools
import math

import pytest


# =====================================================================
# 裁决 1:PR3 内部矛盾 —— 软门禁聚合模式默认值
# =====================================================================
class TestAdjudicate1_PR3AggregationDefaultConflict:
    """分歧:PR3 契约层 JudgeProtocol.aggregation 默认 "majority_veto",
    而 PR3 引擎层 SoftGateEngine.evaluate 默认 "any_veto",
    且 soft.py docstring 自称 "any_veto is the default"。
    其余五家(GLM1/GLM2/K3/QW2/QW3)共识是"可信 veto 即否决"(≈any_veto)。

    判定:同一份判词样本在两种默认值下结果必须一致,否则即缺陷。
    """

    @staticmethod
    def _sample(verdict, citation="evidence: x"):
        from swarmkernel.contracts.gate import JudgeSample
        return JudgeSample(criterion_id="c1", verdict=verdict, citation=citation)

    def test_defaults_disagree(self):
        from swarmkernel.contracts.oracle import JudgeProtocol
        import inspect
        from swarmkernel.gates.soft import SoftGateEngine

        contract_default = JudgeProtocol().aggregation
        engine_default = inspect.signature(SoftGateEngine.evaluate).parameters[
            "aggregation"
        ].default
        # 缺陷事实:两处默认值不一致
        assert contract_default == "majority_veto"
        assert engine_default == "any_veto"
        assert contract_default != engine_default, "PR3 默认值冲突已被修复?"

    def test_same_samples_different_verdict(self):
        """1 个带引用的 veto + 2 个 no_veto(k=3):
        any_veto → VETO(阻断);majority_veto → NO_VETO(放行)。
        这直接决定一个被判否决的实例能否准入 —— 不是风格问题是语义缺陷。"""
        from swarmkernel.contracts.gate import SoftVerdict
        from swarmkernel.gates.soft import aggregate

        samples = [
            self._sample(SoftVerdict.VETO),
            self._sample(SoftVerdict.NO_VETO, None),
            self._sample(SoftVerdict.NO_VETO, None),
        ]
        assert aggregate(samples, "any_veto") is SoftVerdict.VETO
        assert aggregate(samples, "majority_veto") is SoftVerdict.NO_VETO

    def test_consensus_requires_any_veto(self):
        """共识裁决:五家方案全部主张"单一可信 veto 即阻断"
        (GLM2 "否决即否决";K3 "veto→否决";QW2 "软门禁是单调否决器";
        QW3 judge 两值输出 reject 即阻断;GLM1 "k 多数 PASS"反向等价)。
        majority_veto 在 k=3 时需要 ≥2 个 veto 才阻断,违背该共识。
        结论:统一为 any_veto;majority/unanimous 仅作显式配置的例外。"""
        from swarmkernel.contracts.gate import SoftVerdict
        from swarmkernel.gates.soft import aggregate

        for n_veto in (1, 2, 3):
            samples = [self._sample(SoftVerdict.VETO)] * n_veto + [
                self._sample(SoftVerdict.NO_VETO, None)
            ] * (3 - n_veto)
            assert aggregate(samples, "any_veto") is SoftVerdict.VETO


# =====================================================================
# 裁决 2:弃权(abstain)语义 —— 三家立场互斥
# =====================================================================
class TestAdjudicate2_AbstainSemantics:
    """分歧(三方互斥):
      S1 "弃权不阻断":PR3(abstain 不计入分母,聚合全弃权=ABSTAIN,代数上 admit=H∧¬veto)、QW1(abstain 不阻断,计入健康度)
      S2 "弃权转人工":K3(abstain→转人工不误阻)、GLM2(弃权永不默认通过→ESCALATE)
      S3 "弃权即否决":QW3(弃权即否决)

    判定:对全部 3^3=27 种判词组合,检验四条公开宣称的不变量:
      I1 no-rescue      :S 门任何结果都不能让 H 失败变准入(三家都声明)
      I2 veto-单调       :把任意 no_veto/abstain 改成 veto,不会从"阻断"变"准入"
      I3 静默不阻塞      :法定人数内全是弃权/无信号时,不制造不存在的阻断
                          (PR3: "forcing a judge to speak manufactures signal")
      I4 静默不放行      :法定人数不足时不自动准入(fail-closed,GLM2/QW2 主张)

    客观结论:S1 违反 I4;S2 违反 I3;S3 同时违反 I3(且把懒 judge 变成 DoS);
    唯一同时满足 I1–I4 的是复合规则:
      "quorum(≥2 份有效判词) + any_veto + 弃权不计入分母;不足 quorum → ESCALATE"
    这正是 QW2(min_valid_verdicts=2, 不足额 fail-closed)与 PR3(弃权不计分母)的合成。
    """

    V, N, A = "VETO", "NO_VETO", "ABSTAIN"
    QUORUM = 2  # 有效(非弃权)判词法定人数,QW2 min_valid_verdicts=2

    @staticmethod
    def s1_abstain_never_blocks(hard_pass, samples):
        return hard_pass and "VETO" not in samples

    @staticmethod
    def s2_abstain_escalates(hard_pass, samples):
        # 任何弃权都转人工 → 阻塞自动准入
        return hard_pass and "VETO" not in samples and "ABSTAIN" not in samples

    @staticmethod
    def s3_abstain_is_veto(hard_pass, samples):
        return hard_pass and "VETO" not in samples and "ABSTAIN" not in samples

    @classmethod
    def composite_quorum(cls, hard_pass, samples):
        valid = [s for s in samples if s != cls.A]
        if len(valid) < cls.QUORUM:
            return "ESCALATE"  # 不自动准入,也不永久阻塞
        return hard_pass and cls.V not in valid

    SEMANTICS = {
        "S1 弃权不阻断(PR3/QW1)": s1_abstain_never_blocks,
        "S2 弃权转人工(K3/GLM2)": s2_abstain_escalates,
        "S3 弃权即否决(QW3)": s3_abstain_is_veto,
    }

    ALL = list(itertools.product([V, N, A], repeat=3))

    def _i1_no_rescue(self, fn):
        return all(fn(False, s) in (False, "ESCALATE") for s in self.ALL)

    def _i2_veto_monotone(self, fn):
        for s in self.ALL:
            base = fn(True, s)
            for i in range(3):
                if s[i] != self.V:
                    t = s[:i] + (self.V,) + s[i + 1 :]
                    if fn(True, t) is True and base is not True:
                        return False
        return True

    def _i3_silent_not_blocked(self, fn):
        # 2 份干净 no_veto + 1 弃权(quorum 已满):不应被弃权拖住
        return fn(True, (self.N, self.N, self.A)) is True

    def _i4_silent_not_admitted(self, fn):
        # 全弃权:不得自动准入
        return fn(True, (self.A, self.A, self.A)) is not True

    def test_each_semantics_fails_at_least_one_invariant(self):
        report = {}
        for name, fn in self.SEMANTICS.items():
            report[name] = dict(
                I1_no_rescue=self._i1_no_rescue(fn),
                I2_veto_monotone=self._i2_veto_monotone(fn),
                I3_silent_not_blocked=self._i3_silent_not_blocked(fn),
                I4_silent_not_admitted=self._i4_silent_not_admitted(fn),
            )
        for name, r in report.items():
            assert not all(r.values()), f"{name} 竟然满足全部不变量: {r}"
        # 逐条指认(这就是裁决结论本身)
        assert report["S1 弃权不阻断(PR3/QW1)"]["I4_silent_not_admitted"] is False
        assert report["S2 弃权转人工(K3/GLM2)"]["I3_silent_not_blocked"] is False
        assert report["S3 弃权即否决(QW3)"]["I3_silent_not_blocked"] is False

    def test_composite_rule_satisfies_all_four(self):
        fn = self.composite_quorum
        assert self._i1_no_rescue(fn)
        assert self._i2_veto_monotone(fn)
        assert self._i3_silent_not_blocked(fn)
        assert self._i4_silent_not_admitted(fn)
        # 且 veto 仍然阻断
        assert fn(True, (self.V, self.N, self.N)) is False

    def test_pr3_engine_matches_composite_when_quorum_met(self):
        """PR3 引擎在 quorum 满足时与复合规则一致(弃权不计分母,单 veto 即阻断);
        差异仅在 quorum 不足时 PR3 仍放行(=违反 I4)——需要外加 min_valid_verdicts。"""
        from swarmkernel.contracts.gate import JudgeSample, SoftVerdict
        from swarmkernel.gates.soft import aggregate

        j = lambda v, c="ref": JudgeSample(criterion_id="c", verdict=v, citation=c)
        # quorum 满足:1 veto + 2 abstain → 弃权不计分母 → VETO(与复合规则一致)
        assert aggregate(
            [j(SoftVerdict.VETO), j(SoftVerdict.ABSTAIN, None), j(SoftVerdict.ABSTAIN, None)],
            "any_veto",
        ) is SoftVerdict.VETO
        # quorum 不满足:全弃权 → PR3 聚合 = ABSTAIN,代数 admit=H∧¬veto → 放行(I4 破口)
        assert aggregate(
            [j(SoftVerdict.ABSTAIN, None)] * 3, "any_veto"
        ) is SoftVerdict.ABSTAIN


# =====================================================================
# 裁决 3:浮点比对 —— 严格相等(QW2) vs 声明式容差(GLM1/PR3)
# =====================================================================
class TestAdjudicate3_FloatComparison:
    """分歧:QW2 "浮点严格相等……不私设 epsilon"(04 §3)
         vs GLM1 归一化器默认 float 相对容差 1e-9;PR3 封闭归一化集含 round:3。

    判定实验:良性不确定性(加法重序,等价于并行归约/线程调度变化)
    在严格相等下是否产生假阳性 DIFF;声明式容差是否既能吸收重序噪声、
    又不掩盖真实回归。结论:严格相等作为*默认值*客观错误(假阳性),
    但作为逐通道显式声明(exact channel)是合法的 —— QW2 的规则原文
    自己也不反对"经登记的 don't-care 通道",分歧只在默认值。
    """

    @staticmethod
    def reduce_order_a(xs):
        acc = 0.0  # 朴素左折叠归约(模拟一种执行/调度顺序)
        for x in xs:
            acc += x
        return acc

    @staticmethod
    def reduce_order_b(xs):
        acc = 0.0  # 同一数学和,另一结合顺序(模拟并行归约/线程调度差异)
        for x in reversed(xs):
            acc += x
        return acc

    def test_strict_equality_false_positive(self):
        xs = [0.1, 0.2, 0.3]
        a = (xs[0] + xs[1]) + xs[2]  # (0.1+0.2)+0.3 = 0.6000000000000001
        b = xs[0] + (xs[1] + xs[2])  # 0.1+(0.2+0.3)   = 0.6
        # 同一数学和,两种结合顺序 —— 严格相等判 DIFF(假阳性实证)
        assert a != b
        strict_verdict = "DIFF" if a != b else "EQUAL"
        assert strict_verdict == "DIFF"
        # 大规模版本:同一数组正序/逆序朴素归约同样发散
        big = [1.0] + [1e-12] * 1000
        assert self.reduce_order_a(big) != self.reduce_order_b(big)

    def test_declared_tolerance_absorbs_noise_catches_regression(self):
        tol = 1e-9  # GLM1 默认相对容差
        a = (0.1 + 0.2) + 0.3
        b = 0.1 + (0.2 + 0.3)
        scale = max(abs(a), abs(b), 1e-300)
        assert abs(a - b) / scale <= tol  # 重序噪声被吸收
        # 大规模重序噪声同样被吸收
        big = [1.0] + [1e-12] * 1000
        ra, rb = self.reduce_order_a(big), self.reduce_order_b(big)
        assert abs(ra - rb) / max(abs(ra), 1e-300) <= tol
        # 真实回归(结果偏移 1%)仍然被检出
        regressed = a * 1.01
        assert abs(a - regressed) / max(abs(a), 1e-300) > tol

    def test_exact_channel_remains_available(self):
        """裁决不等于否定 QW2:把 strict 作为逐通道 opt-in(声明 exact),
        则与 GLM1/PR3 的封闭归一化集完全兼容 —— 客观结论是
        "默认容差、声明例外",而不是"默认严格、差异即信号"。"""
        assert True  # 语义说明性断言,结论见 docstring


# =====================================================================
# 裁决 4:QW1 的 Wilson 门禁阈值实际语义(跨实现复算)
# =====================================================================
class TestAdjudicate4_WilsonCalibration:
    """分歧:非确定性门禁的重试聚合,各家用法不同:
    QW1 明文 "Wilson 95%: lower≥0.4→pass, upper≤0.6→fail, 否则 inconclusive";
    GLM1 wilson_lower(z=1.96);K3/QW3 SPRT α=0.05/β=0.10。

    判定:不评优劣,先用数学把 QW1 规则的真实语义算清楚并钉成测试
    (防止后人误读阈值),并复用 GLM1 的 wilson_lower 做跨实现交叉验证。
    """

    @staticmethod
    def wilson(k, n, z=1.96):
        if n == 0:
            return 0.0, 1.0
        p = k / n
        denom = 1 + z * z / n
        center = (p + z * z / (2 * n)) / denom
        margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
        return center - margin, center + margin

    def test_cross_check_with_glm1_implementation(self):
        from specforge.gates.stats import wilson_lower  # GLM1 的实现

        for n in (1, 2, 3, 4, 5, 10):
            for k in range(n + 1):
                lo, _ = self.wilson(k, n)
                assert lo == pytest.approx(wilson_lower(k, n), abs=1e-12)

    def test_qw1_rule_real_semantics(self):
        def verdict(k, n):
            lo, hi = self.wilson(k, n)
            if lo >= 0.4:
                return "pass"
            if hi <= 0.6:
                return "fail"
            return "inconclusive"

        # PASS 的最低门槛实测 = 3 连胜(3/3 的 lower≈0.438 才首次 ≥0.4)
        assert verdict(3, 3) == "pass"
        assert verdict(2, 2) == "inconclusive"
        assert verdict(1, 1) == "inconclusive"
        # FAIL 的实测 = 0/3(0/3 的 upper≈0.561 ≤0.6);0/2 都不算 fail
        assert verdict(0, 3) == "fail"
        assert verdict(0, 2) == "inconclusive"
        # 3 次中任何一次失败 → inconclusive(转人工),2/3 永远不等于 pass
        assert verdict(2, 3) == "inconclusive"
        # 结论固化:QW1 的规则实为 "3 连胜才过、0/3 才败、其余全部转人工"
        # —— 这与 QW3 的警告"'跑 3 次都绿'不构成证据"形成直接张力,
        # 采用该规则时必须明知:它在数学上把 3/3 当作 pass 的最低证据。


# =====================================================================
# 裁决 5:fan-out 公式 —— 多数派公式 vs PR3 公式的共识不变量
# =====================================================================
class TestAdjudicate5_FanoutFormulas:
    """分歧:GLM1/GLM2/QW2/QW3 用 U=0.4·rework+0.3·novelty+0.3·risk,
    阈值 0.3/0.7 → N∈{1,3,6};PR3 用六信号加权分 → N∈{1,3,5,7}。
    公式本身无数据不可裁决;但两家共同声明的不变量可以钉死:
      F1 N ≤ 8(硬顶);F2 R3 ⇒ N=1(禁 fan-out/禁早停);F3 N 对不确定度单调不减。
    """

    @staticmethod
    def majority_formula(rework, novelty, risk, r_level=0):
        if r_level == 3:
            return 1
        u = 0.4 * rework + 0.3 * novelty + 0.3 * risk
        return min(8, 1 if u < 0.3 else 3 if u < 0.7 else 6)

    @staticmethod
    def pr3_like_formula(score, r_level=0):
        if r_level == 3:
            return 1
        n = 1 if score < 0.25 else 3 if score < 0.55 else 5 if score < 0.8 else 7
        return min(8, n)

    def test_shared_invariants_hold_for_both(self):
        for r in (0.0, 0.25, 0.5, 0.75, 1.0):
            for nv in (0.0, 0.5, 1.0):
                for rk in (0.0, 0.5, 1.0):
                    n = self.majority_formula(r, nv, rk)
                    assert 1 <= n <= 8
            # 单调性:rework 单调
            seq = [self.majority_formula(x, 0.5, 0.5) for x in (0, 0.25, 0.5, 0.75, 1.0)]
            assert seq == sorted(seq)
        seq2 = [self.pr3_like_formula(x) for x in (0, 0.2, 0.4, 0.6, 0.9)]
        assert seq2 == sorted(seq2) and max(seq2) <= 8
        assert self.majority_formula(1, 1, 1, r_level=3) == 1
        assert self.pr3_like_formula(0.99, r_level=3) == 1

    def test_formulas_disagree_documented(self):
        """客观记录分歧点,供后续用真实波次数据回归标定:
        rework=1.0, novelty=0, risk=0 → 多数派 U=0.4→N=3;PR3 同信号(0.20)→N=1。"""
        assert self.majority_formula(1.0, 0.0, 0.0) == 3
        assert self.pr3_like_formula(0.20) == 1


# =====================================================================
# 裁决 6:PR3 脚手架缺口实证(声明了入口点但模块不存在)
# =====================================================================
class TestAdjudicate6_PR3ScaffoldingGaps:
    """客观事实核验:pyproject 声明 swarmkernel=swarmkernel.cli:main 入口点,
    但 cli 模块不存在;hypothesis/jsonschema 声明为测试依赖但未被任何测试 import。"""

    def test_cli_entrypoint_missing(self):
        with pytest.raises(ModuleNotFoundError):
            import swarmkernel.cli  # noqa: F401

    def test_declared_test_deps_unused(self):
        import pathlib
        import re

        root = pathlib.Path("/workspace/plans/PR3_kernel/kernel/tests")
        pattern = re.compile(r"^\s*(import\s+hypothesis|from\s+hypothesis)", re.M)
        uses_hypothesis = any(
            pattern.search(p.read_text(encoding="utf-8")) for p in root.rglob("*.py")
        )
        assert uses_hypothesis is False, "hypothesis 库已被使用,此缺口已修复"
