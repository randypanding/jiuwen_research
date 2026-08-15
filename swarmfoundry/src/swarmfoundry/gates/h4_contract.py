from __future__ import annotations

from swarmfoundry.schema.gates import GATE_H4, GateResult, STATUS_FAIL, STATUS_PASS
from swarmfoundry.contracts.compat import diff_surfaces
from swarmfoundry.contracts.extract import extract_surface, load_surface
from swarmfoundry.gates.base import Gate
from swarmfoundry.gates.context import GateContext


class H4ContractGate(Gate):
    """H4: contract-surface extraction + breaking-change detection.
    R0 without baseline: not applicable (pass, recorded).
    R1/R2/R3: baseline mandatory; any breaking change fails unless an explicit
    human-approved waiver ref is present in gate config."""

    gate_id = GATE_H4

    def run(self, ctx: GateContext) -> GateResult:
        if ctx.baseline_surface_path is None:
            if ctx.r_level == "R0":
                return GateResult(
                    gate_id=self.gate_id,
                    status=STATUS_PASS,
                    evidence=["R0 artifact without consumers: no baseline contract required"],
                    details={"not_applicable": True},
                )
            return GateResult(
                gate_id=self.gate_id,
                status=STATUS_FAIL,
                evidence=[f"{ctx.r_level} artifact requires a frozen baseline contract surface"],
            )
        baseline = load_surface(ctx.baseline_surface_path)
        current = extract_surface(ctx.instance_dir, module=baseline.module)
        diff = diff_surfaces(baseline, current)
        breaking = diff.breaking()
        evidence = [f"surface symbols: baseline={len(baseline.symbols)} current={len(current.symbols)}", f"changes={len(diff.changes)} breaking={len(breaking)}"]
        for c in diff.changes:
            evidence.append(f"  {c.severity.upper()} {c.change} {c.kind} {c.name}: {c.detail}")
        if breaking:
            cfg = ctx.gate_config(self.gate_id)
            waiver = cfg.get("waiver")
            if isinstance(waiver, dict) and waiver.get("human_approval_ref"):
                evidence.append(f"breaking changes covered by explicit waiver {waiver['human_approval_ref']}")
                return GateResult(self.gate_id, STATUS_PASS, tuple(evidence), {"waived": True})
            return GateResult(self.gate_id, STATUS_FAIL, tuple(evidence), {"breaking": [c.to_dict() for c in breaking]})
        return GateResult(self.gate_id, STATUS_PASS, tuple(evidence))
