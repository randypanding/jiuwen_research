from __future__ import annotations

import dataclasses

from swarmfoundry.schema import SCHEMA_VERSION
from swarmfoundry.schema.base import (
    SchemaError,
    check_id,
    check_schema_version,
    require,
    require_list,
)
from swarmfoundry.schema.spec import R_LEVELS

TASK_PENDING = "pending"
TASK_ASSIGNED = "assigned"
TASK_INSTANCES_READY = "instances_ready"
TASK_VERIFYING = "verifying"
TASK_ADMITTED = "admitted"
TASK_REJECTED = "rejected"
TASK_ESCALATED = "escalated"
TASK_STATUSES = (
    TASK_PENDING,
    TASK_ASSIGNED,
    TASK_INSTANCES_READY,
    TASK_VERIFYING,
    TASK_ADMITTED,
    TASK_REJECTED,
    TASK_ESCALATED,
)

MAX_FANOUT = 8


@dataclasses.dataclass(frozen=True)
class WaveTask:
    task_id: str
    spec_delta_id: str
    r_level: str
    n_fanout: int
    depends_on: tuple[str, ...] = ()
    status: str = TASK_PENDING
    assigned_instances: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "spec_delta_id": self.spec_delta_id,
            "r_level": self.r_level,
            "n_fanout": self.n_fanout,
            "depends_on": list(self.depends_on),
            "status": self.status,
            "assigned_instances": list(self.assigned_instances),
        }

    @classmethod
    def from_dict(cls, data: dict, where: str) -> "WaveTask":
        r_level = require(data, "r_level", str, where)
        if r_level not in R_LEVELS:
            raise SchemaError(f"{where}: r_level must be one of {R_LEVELS}")
        n = require(data, "n_fanout", int, where)
        if not 1 <= n <= MAX_FANOUT:
            raise SchemaError(f"{where}: n_fanout must be within [1, {MAX_FANOUT}]")
        status = data.get("status", TASK_PENDING)
        if status not in TASK_STATUSES:
            raise SchemaError(f"{where}: status must be one of {TASK_STATUSES}")
        return cls(
            task_id=check_id(require(data, "task_id", str, where), where),
            spec_delta_id=require(data, "spec_delta_id", str, where),
            r_level=r_level,
            n_fanout=n,
            depends_on=tuple(require_list(data, "depends_on", where)),
            status=status,
            assigned_instances=tuple(require_list(data, "assigned_instances", where)),
        )


@dataclasses.dataclass(frozen=True)
class WavePlan:
    wave_id: str
    interface_freeze: tuple[str, ...]
    tasks: tuple[WaveTask, ...]
    budget_units: float
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "wave_id": self.wave_id,
            "interface_freeze": list(self.interface_freeze),
            "budget_units": self.budget_units,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WavePlan":
        where = "WavePlan"
        check_schema_version(data, where)
        tasks = tuple(
            WaveTask.from_dict(t, f"{where}.tasks[{i}]") for i, t in enumerate(require_list(data, "tasks", where))
        )
        plan = cls(
            wave_id=check_id(require(data, "wave_id", str, where), where),
            interface_freeze=tuple(require_list(data, "interface_freeze", where)),
            tasks=tasks,
            budget_units=float(require(data, "budget_units", float, where)),
        )
        plan.validate()
        return plan

    def validate(self) -> None:
        ids = [t.task_id for t in self.tasks]
        if len(ids) != len(set(ids)):
            raise SchemaError(f"WavePlan {self.wave_id}: duplicate task ids")
        known = set(ids)
        for t in self.tasks:
            for dep in t.depends_on:
                if dep not in known:
                    raise SchemaError(f"WavePlan {self.wave_id}: task {t.task_id} depends on unknown {dep}")
        if _has_cycle(self.tasks):
            raise SchemaError(f"WavePlan {self.wave_id}: dependency cycle detected")

    def ready_tasks(self) -> list[WaveTask]:
        done = {t.task_id for t in self.tasks if t.status in (TASK_ADMITTED, TASK_REJECTED)}
        return [
            t
            for t in self.tasks
            if t.status == TASK_PENDING and all(d in done for d in t.depends_on)
        ]


def _has_cycle(tasks: tuple[WaveTask, ...]) -> bool:
    graph = {t.task_id: set(t.depends_on) for t in tasks}
    state: dict[str, int] = {}

    def visit(node: str) -> bool:
        if state.get(node) == 1:
            return True
        if state.get(node) == 2:
            return False
        state[node] = 1
        for dep in graph.get(node, ()):
            if visit(dep):
                return True
        state[node] = 2
        return False

    return any(visit(n) for n in graph)
