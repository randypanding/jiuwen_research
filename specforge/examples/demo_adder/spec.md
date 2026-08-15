---
spec_id: units.demo.adder
version: 1.0.0
r_level: R0
depends: []
artifacts: ["demo_adder/good.py", "demo_adder/broken.py"]
---

## L1 意图

为计算器应用提供整数加法。用户输入两个整数，得到它们的和。
成功标准：任意 int 输入下结果正确且不崩溃。

```clause
id: REQ-ADDER-L1-1
level: L1
text: 对任意两个 int 输入，add 必须返回它们的数学和。
witness: holdout:adder-basic
```

## L2 契约

```clause
id: REQ-ADDER-L2-1
level: L2
text: add(a, b) 接受两个 int 参数，返回 int；对域内输入不抛异常。
witness: gate:h2
```

```clause
id: REQ-ADDER-L2-2
level: L2
text: 交换律必须成立。
witness: gate:h2
```

```invariant
expr: add(a, b) == add(b, a)
scope: h2
```

## L3 实现说明

实现为纯函数；性能无关紧要。

## DONT-CARE

```dontcare
- id: DC-ADDER-1
  kind: unspecified
  region: debug_log
```
