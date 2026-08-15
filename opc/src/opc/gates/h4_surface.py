from __future__ import annotations

import time

from opc.gates.base import Gate, GateContext, check, worst
from opc.gates.surface import extract_surface, surface_breaking
from opc.schemas.common import RLevel
from opc.schemas.gates import CheckResult, GateReport


class H4ContractSurfaceGate(Gate):
    """H4: contract-surface extraction + breaking-change detection.

    The mechanical witness of L2 interface contracts and of R1/R2
    compatibility obligations:
      * every symbol declared in the contract's interface_surface must exist
        in the instance;
      * against the world baseline, removed or signature-changed public
        symbols are breaking (scope widens with the R-level).
    """

    gate_id = "H4"

    def run(self, ctx: GateContext) -> GateReport:
        started = time.monotonic()
        checks: list[CheckResult] = []
        contract = ctx.contract()

        candidate_surface = extract_surface(ctx.instance_dir)
        candidate_suffixes = {symbol.rsplit(".", 1)[-1]: symbol for symbol in candidate_surface}

        if contract is not None:
            missing = []
            for item in contract.interface_surface:
                if item.symbol not in candidate_suffixes:
                    missing.append(item.symbol)
            checks.append(
                check(
                    "h4.contract_symbols",
                    not missing,
                    f"contract symbols absent from instance: {missing}" if missing else "all contract symbols present",
                )
            )
        else:
            checks.append(check("h4.contract_symbols", False, "no contract bound to this admission"))

        if ctx.baseline_dir is not None:
            baseline_surface = extract_surface(ctx.baseline_dir)
            r_level = ctx.r_level() or RLevel.R0
            if r_level is RLevel.R0 and contract is not None:
                scope = {
                    candidate_suffixes[item.symbol]
                    for item in contract.interface_surface
                    if item.symbol in candidate_suffixes
                } | {
                    symbol
                    for symbol in baseline_surface
                    if symbol.rsplit(".", 1)[-1] in {i.symbol for i in contract.interface_surface}
                }
                baseline_scope = {s: v for s, v in baseline_surface.items() if s in scope}
                breaking = surface_breaking(baseline_scope, candidate_surface)
            else:
                breaking = surface_breaking(baseline_surface, candidate_surface)
            checks.append(
                check(
                    "h4.breaking",
                    not breaking,
                    f"breaking changes vs world baseline: {breaking[:8]}" if breaking else "no breaking changes",
                )
            )
        else:
            checks.append(
                check("h4.breaking", True, "no world baseline yet (first admission of this contract)")
            )

        return self.report(ctx, worst([c.status for c in checks]), checks, started)
