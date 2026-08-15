"""BusPort：总线端口抽象 + openjiuwen TeamRuntime 适配器。

契约层只依赖 BusPort 协议；InProcessBus 用于单机/测试，
OpenJiuwenBusAdapter 把权限矩阵强制桥接到 openjiuwen 的
core/multi_agent/team_runtime（跨进程经 agent_teams messager pyzmq）。
"""
from __future__ import annotations

from typing import Callable, Optional, Protocol

from .bus import Envelope, InProcessBus, validate_wiring  # noqa: F401 re-export


class BusPort(Protocol):
    def publish(self, env: Envelope) -> int: ...
    def subscribe(self, role: str, topic_pattern: str,
                  handler: Callable[[Envelope], None]) -> str: ...
    def unsubscribe(self, sub_id: str) -> None: ...


class OpenJiuwenBusAdapter:
    """把 InProcessBus 的权限/审计语义桥接到 openjiuwen TeamRuntime。

    openjiuwen 侧：每个 swarmforge 角色注册为一个 CommunicableAgent
    （TeamRuntime.register_agent），订阅模式直接复用其 fnmatch
    subscription_manager。权限矩阵在适配层前置强制——TeamRuntime 本身
    无权限概念，不能裸用（否则 builder 可直接订阅 gate.*）。

    需要 openjiuwen 可安装（可选依赖 [openjiuwen]）；未安装时抛
    ImportError——契约层测试不依赖它。
    """

    def __init__(self, team_id: str = "swarmforge"):
        try:
            from openjiuwen.core.multi_agent.team_runtime.team_runtime import (
                RuntimeConfig, TeamRuntime,
            )
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "openjiuwen is required for OpenJiuwenBusAdapter; "
                "pip install swarmforge[openjiuwen]"
            ) from exc
        from .bus import PUBLISH_MATRIX, SUBSCRIBE_MATRIX, BusPermissionError, _matches

        self._rt = TeamRuntime(RuntimeConfig(team_id=team_id))
        self._publish_matrix = PUBLISH_MATRIX
        self._subscribe_matrix = SUBSCRIBE_MATRIX
        self._BusPermissionError = BusPermissionError
        self._matches = staticmethod(_matches)

    async def start(self) -> None:
        await self._rt.start()

    async def stop(self) -> None:
        await self._rt.stop()
