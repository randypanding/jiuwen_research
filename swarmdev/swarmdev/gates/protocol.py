from __future__ import annotations

from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from swarmdev.contracts import GateOutcome, OracleBundle, RLevel, SpecDoc

VALID_GATE_IDS: tuple[str, ...] = ("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8")


class GateContext(BaseModel):
    workspace: Path
    spec: SpecDoc
    instance_id: str
    instance_dir: Path
    r_level: RLevel
    bundle: Optional[OracleBundle] = None
    surface_snapshot: Optional[dict] = None
    cost_record: Optional[dict] = None
    extra: dict = Field(default_factory=dict)


@runtime_checkable
class Gate(Protocol):
    gate_id: str

    def run(self, ctx: GateContext) -> GateOutcome: ...
