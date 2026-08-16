from __future__ import annotations

from swarmfoundry.schema.gates import GATE_S, GateResult, STATUS_FAIL, STATUS_PASS
from swarmfoundry.schema.judge import aggregate_panel
from swarmfoundry.gates.base import Gate
from swarmfoundry.gates.context import GateContext


class SJudgeGate(Gate):
    """S: soft gate — LLM-as-judge panel executed by the verifier following a
    frozen rubric. Judges may only veto, never rescue; abstain is allowed;
    self-review is invalidated; insufficient valid verdicts fail closed."""

    gate_id = GATE_S

    def run(self, ctx: GateContext) -> GateResult:
        cfg = ctx.gate_config(self.gate_id)
        min_valid = int(cfg.get("min_valid_verdicts", 2))
        if not ctx.judge_verdicts:
            return GateResult(
                gate_id=self.gate_id,
                status=STATUS_FAIL,
                evidence=["no judge verdicts recorded; soft gate cannot testify"],
            )
        decision = aggregate_panel(list(ctx.judge_verdicts), ctx.builder_model_family, min_valid=min_valid)
        status = STATUS_FAIL if decision.vetoed else STATUS_PASS
        return GateResult(
            gate_id=self.gate_id,
            status=status,
            evidence=tuple(decision.reasons),
            details=decision.to_dict(),
        )
