"""swarmforge: Spec-as-Source 开发 agent swarm 的契约层。

范式见 /workspace/structure.md (PDR-001)。本包实现其中必须自建的范式件：
spec 仓、R 级注册表、oracle/holdout、门禁代数 H1-H8、准入事务与证据收据、
事件总线与信息不对称协议、测量（fan-out/六格判定/健康度）、角色装配。

零三方依赖（仅标准库）：CI 门禁必须能在最简环境机械执行。
"""

__version__ = "0.1.0"
