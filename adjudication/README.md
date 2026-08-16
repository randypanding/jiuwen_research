# 裁决与复现说明(jiuwen_research 七方案对比)

本目录包含对 randypanding/jiuwen_research 七份工程方案(GLM1/GLM2/K3/QW1/QW2/QW3/PR3)之间
"可用代码客观裁决"分歧点的判定实验。`test_adjudication.py` 共 15 个测试,全部通过。

## 一、复现环境

```bash
git clone https://github.com/randypanding/jiuwen_research.git && cd jiuwen_research
git fetch origin 'refs/pull/*/head:refs/remotes/pr/*'   # PR3 = refs/pull/3/head = copilot/create-engineering-plan
python3.12 -m venv venv && venv/bin/pip install pytest pydantic pyyaml hypothesis
```

注意:PR3/GLM2 声明 `python>=3.11,<3.14`,请用 3.12(实测 3.14 上 pydantic 可装但版本钉不符)。
各方案的实现目录:GLM1→`specforge/`、GLM2→`swarmforge/`、K3→`swarmdev/`、QW1→`swarm-kernel/`、
QW2→`swarmfoundry/`、QW3→`opc/`、PR3→`kernel/`。

## 二、七家实现测试复现矩阵(已实测)

```bash
# 以 GLM1 为例,其余类推
git archive origin/GLM1 specforge | tar -x -C /tmp && cd /tmp/specforge
/path/to/venv/bin/pip install -e . -q && /path/to/venv/bin/python -m pytest -q
```

| 分支 | 实现包 | 方案声称 | 实测结果 | 耗时 |
|---|---|---|---|---|
| GLM1 | specforge | "28 个测试文件 ✅" | **197 passed, 12 skipped**(skip=agent-core submodule 未检出,设计如此) | 2m03s |
| GLM2 | swarmforge | 134 项全绿 | **134 passed**(精确一致) | 0.63s |
| K3 | swarmdev | 139 项全绿 | **139 passed**(精确一致) | 14s |
| QW1 | swarm-kernel | 86 用例全绿 | **86 passed**(精确一致);`ci/run_all_gates.sh` → ALL GATES: PASS(必须从仓根目录运行,脚本用相对路径 `swarm-kernel/fixtures/...`) | 17s |
| QW2 | swarmfoundry | 66 pytest + selftest 13/13 | **66 passed** + **selftest 13/13**(均精确一致) | 79s |
| QW3 | opc | 64 例全绿 | **64 passed**(精确一致) | 11s |
| PR3 | swarmkernel | (未给总数) | **466 passed**(283 个测试函数经参数化展开) | 0.78s |

结论:七家"测试全绿"声称全部属实。

## 三、语义裁决实验(test_adjudication.py,15 个测试全过)

```bash
# 需要先 pip install -e GLM1 的 specforge 与 PR3 的 swarmkernel(裁决 1/4 复用其实现做交叉验证)
/path/to/venv/bin/python -m pytest adjudication/test_adjudication.py -v
```

1. **裁决 1(PR3 内部矛盾)**:契约层 `JudgeProtocol.aggregation` 默认 `majority_veto`,引擎层
   `SoftGateEngine.evaluate` 默认 `any_veto`;同一组样本(1 veto + 2 no_veto)在两默认值下
   分别得到 NO_VETO 与 VETO。→ 应统一为 `any_veto`(与其余五家"可信 veto 即否决"共识一致)。
2. **裁决 2(弃权语义,三方互斥)**:枚举全部 27 种判词组合 × 4 条公开宣称的不变量:
   "弃权不阻断"(PR3/QW1)违反 I4(静默时自动放行);"弃权转人工"(K3/GLM2)与"弃权即否决"(QW3)
   违反 I3(无信号时制造阻断)。唯一同时满足四条不变量的是复合规则:
   **quorum≥2 份有效判词 + any_veto + 弃权不计入分母;不足 quorum → ESCALATE**。
3. **裁决 3(浮点比对)**:严格相等(QW2 默认)对同一数学和的两种结合顺序
   ((0.1+0.2)+0.3 vs 0.1+(0.2+0.3))判 DIFF —— 假阳性实证;声明式容差(1e-9,GLM1 默认)
   吸收重序噪声且仍检出 1% 真实回归。→ 默认容差,exact 逐通道 opt-in。
4. **裁决 4(QW1 Wilson 阈值标定)**:跨实现复算(与 GLM1 `wilson_lower` 逐点一致,误差<1e-12)。
   QW1 规则(lower≥0.4→pass,upper≤0.6→fail)的真实语义 = **3 连胜才过、0/3 才败、其余全部
   转人工**(2/2 也是 inconclusive)。采用前必须明知这一点。
5. **裁决 5(fan-out 公式)**:多数派公式(0.4r+0.3n+0.3k→{1,3,6})与 PR3 公式(六信号→{1,3,5,7})
   均满足三条共识不变量(N≤8、R3⇒N=1、对不确定度单调);分歧点位已固化在测试中,待真实波次数据标定。
6. **裁决 6(PR3 脚手架缺口)**:`swarmkernel.cli` 入口点声明但模块不存在(ModuleNotFoundError);
   hypothesis/jsonschema 声明为测试依赖但无任何测试 import;governance 三契约无测试。

## 四、已知文档级不一致(非代码可裁决,需作者确认)

- GLM1:CI "三 job"(WP0)vs 四项硬门禁(§10);holdout 权限 0600(D12)vs "0700/0600"(WP6)。
- GLM2:降级阈值 escape>5%(§7)与 P3 进阶"逃逸缺陷率<5%"语义不同(一为降级线一为进阶线),建议统一为 2% 以对齐其余五家。
