# Dogfood 示范域：demo_adder

一个最小的"整数加法器"单元，用于端到端验证 SpecForge 全链路：
spec 解析 → lint → 契约提取 → 差分测量 → 门禁 → 准入 → 收据。

## 文件

- `spec.md` — 三层规范 + don't-care（含 clause/invariant/dontcare 块）
- `good.py` — 正确实现（sum 保持符号语义，超界饱和）
- `broken.py` — 缺陷实现（对负数取绝对值：会在差分与 holdout 上分歧）
- `tests/` — 强断言测试（杀死变异）
- `holdout/` — 私有场景集（由 verifier 侧注入，builder 不可见）

## 运行

```
python -m pytest tests/ -q                 # 单元测试
python -m specforge.cli validate-spec examples/demo_adder/spec.md
python -m specforge.cli demo               # 端到端（在 specforge/ 目录下）
```
