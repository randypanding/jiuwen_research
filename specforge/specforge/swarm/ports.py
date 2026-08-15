"""Swarm ports: the ONLY coupling between orchestration and openJiuwen.

The orchestrator (and its tests) depend on these Protocols. The real
OpenJiuwenAdapter (openjiuwen_adapter.py) implements them on top of
agent-core APIs; fakes implement them for tests. Contract communication
tests lock these interfaces.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Protocol, runtime_checkable


@dataclass
class SpawnOrder:
    spec_delta: dict[str, Any]
    seed: int                    # platform-injected PRNG seed (constitution #17)
    instance_id: str
    builder_tier: str = "RU-M"
    tools_allowlist: list[str] = field(default_factory=list)
    context_id: str = ""         # isolated context (information asymmetry)


@dataclass
class InstanceOutput:
    instance_id: str
    source: str                  # path/branch/commit identifying the produced tree
    oracle_passed: bool = True   # builder-side self-check result (NOT authoritative)
    cost_usd: float = 0.0
    wall_s: float = 0.0
    notes: str = ""


@runtime_checkable
class BuilderPort(Protocol):
    tier: str

    def spawn(self, order: SpawnOrder) -> InstanceOutput: ...


@dataclass
class GateRunOrder:
    instance_source: str
    spec_unit: dict[str, Any]
    spec_delta: dict[str, Any]
    config: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class VerifierPort(Protocol):
    def run_hard_gates(self, order: GateRunOrder) -> dict[str, Any]: ...
    def run_differential(self, sources: list[str], spec_unit: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class ModerationDecision:
    route: str            # admit-best-instance | register-freedom | spec-delta | spec-clarify | escalate | more-instances
    don_t_care_regions: list[str] = field(default_factory=list)
    spec_delta_draft: Optional[dict[str, Any]] = None
    rationale: str = ""


@runtime_checkable
class ModeratorPort(Protocol):
    def route(self, measurement: dict[str, Any]) -> ModerationDecision: ...


@dataclass
class SwarmEvent:
    kind: str   # wave-begin | spawn | gates | admit | measurement | moderation | degrade
    payload: dict[str, Any] = field(default_factory=dict)
    at: float = 0.0


@runtime_checkable
class MessengerPort(Protocol):
    def publish(self, event: SwarmEvent) -> None: ...
    def history(self) -> list[SwarmEvent]: ...
