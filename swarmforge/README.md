# SwarmForge

Spec-as-Source 开发 agent swarm 的契约内核（基于 openJiuwen，范式见 `/workspace/structure.md`，工程计划见 `/workspace/ENGINEERING_PLAN.md`）。

零三方依赖（仅标准库）——CI 门禁必须能在最简环境机械执行。

## 模块

| 模块 | 职责 |
|---|---|
| `constitution` | 15 条范式不变量 + 违例异常 |
| `specrepo` | spec 三层条款/见证绑定/don't-care/R 级注册表/接口锁/版本链 |
| `oracle` | holdout 场景库（隔离+审计）/ 差分引擎 / 黄金门 / judge 协议 |
| `gates` | 门禁代数（H1–H8 + S）/ 证据来源链 / fail-fast 编排 |
| `admission` | 波次状态机 / 准入事务(2PC+WAL+崩溃恢复) / 哈希链收据 |
| `bus` | 事件总线 / 权限矩阵（信息不对称物理层）/ 连线检查 / openjiuwen 适配 |
| `measurement` | 自适应 fan-out / 六格判定 / 健康度 / 降级触发 |
| `harness` | 角色装配（宪法校验）/ 模型档位 / 规则变更提案 |
| `reconciler` | spec↔code 漂移扫描（H7 证据生产） |

## 测试

```bash
pip install -e .[test]  # 或直接 pytest
python3 -m pytest tests/ # 134 passed
```

覆盖：门禁拦截性、准入代数真值表、防绕过（证据伪造/总线越权/holdout 访问）、
事务原子性与崩溃恢复、收据防篡改、契约间通信与端到端波次流转、宪法投影。
