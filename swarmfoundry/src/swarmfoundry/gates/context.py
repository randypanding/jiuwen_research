from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from swarmfoundry.schema.receipt import CostRecord
from swarmfoundry.schema.judge import JudgeVerdict
from swarmfoundry.specrepo.loader import SpecRepo


@dataclasses.dataclass
class GateContext:
    """Everything a gate may look at. Note the asymmetry discipline: the context
    handed to a *builder* never contains holdout_dirs/judge rubrics; only the
    verifier receives this full context (enforced by comm layer + harness)."""

    instance_dir: Path
    instance_id: str
    spec_repo: SpecRepo | None = None
    config: dict = dataclasses.field(default_factory=dict)
    r_level: str = "R0"
    baseline_surface_path: Path | None = None
    holdout_dirs: tuple[Path, ...] = ()
    diff_suite_dir: Path | None = None
    sibling_instances: tuple[Path, ...] = ()
    judge_verdicts: tuple[JudgeVerdict, ...] = ()
    builder_model_family: str = ""
    costs: CostRecord = dataclasses.field(default_factory=CostRecord)
    golden_checks: tuple[dict, ...] = ()
    receipts_dir: Path | None = None

    def gate_config(self, gate_id: str) -> dict:
        return (self.config.get("gates", {}) or {}).get(gate_id, {}) or {}


def load_config(path: Path) -> dict:
    import tomllib

    return tomllib.loads(Path(path).read_text(encoding="utf-8"))
