from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from pydantic import BaseModel, Field


class RunOutput(BaseModel):
    exit_code: int
    stdout: str = ""
    stderr: str = ""


class Divergence(BaseModel):
    input_repr: str
    outputs: dict[str, str]


class DifferentialReport(BaseModel):
    passed: bool
    divergences: list[Divergence] = Field(default_factory=list)
    inputs_run: int = 0


def default_normalize(output: RunOutput) -> str:
    return json.dumps(
        {"exit": output.exit_code, "stdout": output.stdout, "stderr": output.stderr},
        sort_keys=True,
    )


class DifferentialEngine:
    def __init__(self, runner: Callable[[Path, str], RunOutput]):
        self.runner = runner

    def compare_instances(
        self,
        instance_dirs: dict[str, Path],
        inputs: list[str],
        normalizer: Callable[[RunOutput], str] | None = None,
    ) -> DifferentialReport:
        normalize = normalizer or default_normalize
        divergences: list[Divergence] = []
        for inp in inputs:
            outputs: dict[str, str] = {}
            for instance_id in sorted(instance_dirs):
                outputs[instance_id] = normalize(self.runner(instance_dirs[instance_id], inp))
            if len(set(outputs.values())) > 1:
                divergences.append(Divergence(input_repr=inp, outputs=outputs))
        return DifferentialReport(
            passed=not divergences,
            divergences=divergences,
            inputs_run=len(inputs),
        )
