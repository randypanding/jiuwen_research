from __future__ import annotations

from typing import Any

from pydantic import Field

from opc.schemas.common import BaseSchema, Verdict


class InstanceRun(BaseSchema):
    instance_id: str
    input_id: str
    status: Verdict
    output_hash: str = ""
    normalized_output: dict[str, Any] = Field(default_factory=dict)
    exit_code: int | None = None
    timed_out: bool = False
    duration_s: float = 0.0


class Divergence(BaseSchema):
    input_id: str
    instance_a: str
    instance_b: str
    field_path: str = ""
    value_a: str = ""
    value_b: str = ""
    in_dont_care_scope: bool = False


class DiffReport(BaseSchema):
    """Result of H5: instance-to-instance behavioural differential.

    verdict semantics:
      PASS          - no divergence outside registered don't-care scopes
      FAIL          - divergence found in a constrained region (spec silence
                      candidate -> spec moderator must rule)
      INCONCLUSIVE  - runs incomplete (timeout/crash) or sample count < 3
                      after failures (information-insufficient rule)
    """

    instance_ids: list[str]
    corpus_id: str = ""
    runs: list[InstanceRun] = Field(default_factory=list)
    divergences: list[Divergence] = Field(default_factory=list)
    verdict: Verdict = Verdict.INCONCLUSIVE
    all_pass_and_empty_diff: bool = False
    dont_care_divergences: int = 0
    note: str = ""
