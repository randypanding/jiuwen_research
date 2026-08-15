"""H7: spec<->code drift detection.

Three funnels (spec-traceability research, simplified for M0/M1):
  1. trace anchor coverage: `spec:<CLAUSE_ID>` comments in code must cover
     all machine clauses (threshold), and no orphan anchors.
  2. contract hash: spec.contract block hash vs extracted surface hash of
     the declared contract (when spec declares expected surface hash).
  3. artifact existence: declared artifacts must exist.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .base import GateContext, GateResult, GateVerdict

_ANCHOR = re.compile(r"spec:([A-Za-z0-9_\-]+)")


class H7DriftGate:
    gate_id = "h7"
    description = "spec<->code drift: trace anchors, contract hash, artifact existence"
    hard = True

    def __init__(self, min_coverage: float = 0.8):
        self.min_coverage = min_coverage

    def applicable(self, ctx: GateContext) -> bool:
        return ctx.spec_unit is not None and bool(ctx.spec_unit.artifacts)

    def run(self, ctx: GateContext) -> GateResult:
        unit = ctx.spec_unit
        root = Path(ctx.instance_path)
        evidence: dict[str, Any] = {}

        # 1. artifact existence
        missing = []
        for pattern in unit.artifacts:
            p = root / pattern
            if not p.exists() and not list(root.glob(pattern)):
                missing.append(pattern)
        evidence["missing_artifacts"] = missing
        if missing:
            return GateResult(self.gate_id, GateVerdict.FAIL,
                              reason=f"spec artifacts missing from code: {missing}",
                              evidence=evidence,
                              constitution_ref="#10 spec 与代码不一致默认判缺陷并阻断")

        # 2. trace anchors
        anchors: set[str] = set()
        anchor_hits: list[str] = []
        for pattern in unit.artifacts:
            p = root / pattern
            candidates = [p] if p.is_file() else sorted(root.glob(pattern.rstrip("/") + "/**/*.py"))
            if p.is_file() and p.suffix != ".py":
                candidates = [p]
            for f in candidates:
                try:
                    text = f.read_text(encoding="utf-8")
                except OSError:
                    continue
                for m in _ANCHOR.finditer(text):
                    anchors.add(m.group(1))
                    anchor_hits.append(f"{f.relative_to(root)}:{m.group(1)}")
        clause_ids = {c.clause_id for c in unit.machine_clauses()}
        covered = clause_ids & anchors
        orphans = anchors - clause_ids
        coverage = len(covered) / len(clause_ids) if clause_ids else 1.0
        evidence["anchors"] = sorted(anchors)
        evidence["coverage"] = coverage
        evidence["orphans"] = sorted(orphans)

        if orphans:
            return GateResult(self.gate_id, GateVerdict.FAIL,
                              reason=f"orphan trace anchors (code claims clauses that spec does not define): "
                                     f"{sorted(orphans)}",
                              evidence=evidence,
                              constitution_ref="#1 spec 是唯一真值")
        if coverage < self.min_coverage:
            return GateResult(self.gate_id, GateVerdict.INCONCLUSIVE,
                              reason=f"trace coverage {coverage:.2f} < {self.min_coverage}: "
                                     "code-clause traceability incomplete",
                              evidence=evidence,
                              constitution_ref="#12 准入必须附带完整证据收据")

        # 3. contract hash check (when spec declares it)
        declared_hash = unit.contract.get("surface_hash") if isinstance(unit.contract, dict) else None
        if declared_hash and ctx.surface_new is not None:
            actual = ctx.surface_new.hash()
            evidence["contract_hash"] = {"declared": declared_hash, "actual": actual}
            if declared_hash != actual:
                return GateResult(self.gate_id, GateVerdict.FAIL,
                                  reason="declared contract surface_hash drifted from extracted surface",
                                  evidence=evidence,
                                  constitution_ref="#10 spec 与代码不一致默认判缺陷并阻断")
        elif declared_hash and ctx.surface_new is None and "surface_snapshot" in (unit.contract or {}):
            snap_dict = unit.contract.get("surface_snapshot")
            actual = hashlib.sha256(
                json.dumps(snap_dict, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            evidence["contract_hash"] = {"declared": declared_hash, "actual": actual}
            if declared_hash != actual:
                return GateResult(self.gate_id, GateVerdict.FAIL,
                                  reason="declared contract surface_hash drifted from spec snapshot",
                                  evidence=evidence,
                                  constitution_ref="#10")

        return GateResult(self.gate_id, GateVerdict.PASS,
                          reason=f"trace coverage {coverage:.2f}, no orphans, contract consistent",
                          evidence=evidence)
