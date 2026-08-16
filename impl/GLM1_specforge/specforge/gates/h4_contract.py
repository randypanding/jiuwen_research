"""H4: contract surface + breaking-change detection gate (D4)."""
from __future__ import annotations

from typing import Any, Optional

from ..contracts.diff import ContractDelta, diff_surfaces
from ..contracts.extractor import extract
from ..contracts.surface import SurfaceSnapshot
from ..spec.semver import SemVer, check_bump
from .base import GateContext, GateResult, GateVerdict


class H4ContractGate:
    gate_id = "h4"
    description = "contract surface extraction + BC/NBC + version bump consistency"
    hard = True

    def __init__(self, deprecated_state: Optional[dict[str, str]] = None):
        self.deprecated_state = deprecated_state or {}

    def applicable(self, ctx: GateContext) -> bool:
        unit = ctx.spec_unit
        return bool(unit and unit.artifacts)

    def run(self, ctx: GateContext) -> GateResult:
        unit = ctx.spec_unit
        old_snap: SurfaceSnapshot = ctx.surface_old  # may be None (new unit)
        new_snap: SurfaceSnapshot = ctx.surface_new
        if new_snap is None:
            new_snap = self._extract_instance(ctx)
        evidence: dict[str, Any] = {
            "old_hash": old_snap.hash() if old_snap else None,
            "new_hash": new_snap.hash(),
        }
        delta = diff_surfaces(old_snap, new_snap) if old_snap else ContractDelta(
            old_hash="", new_hash=new_snap.hash())
        from ..contracts.diff import explain

        evidence["changes"] = [c.to_dict() for c in delta.changes]
        evidence["has_breaking"] = delta.has_breaking

        if old_snap is not None:
            old_present = (set(old_snap.functions) | set(old_snap.classes) | set(old_snap.constants))
            new_present = (set(new_snap.functions) | set(new_snap.classes) | set(new_snap.constants))
            from ..spec.semver import classify_deprecation

            deprec_violations = classify_deprecation(old_present, new_present, self.deprecated_state)
            if deprec_violations:
                return GateResult(self.gate_id, GateVerdict.FAIL,
                                  reason="; ".join(deprec_violations), evidence=evidence,
                                  constitution_ref="#11 不可再生制品只允许前向演进")

        # version bump consistency
        delta_unit = ctx.spec_delta
        old_ver = delta_unit.old_version if delta_unit else unit.version
        bump = check_bump(SemVer.parse(old_ver), SemVer.parse(unit.version),
                          has_breaking=delta.has_breaking, has_feature=delta.has_additive)
        evidence["bump"] = {"required": bump.required, "ok": bump.ok, "reason": bump.reason}
        if not bump.ok:
            return GateResult(self.gate_id, GateVerdict.FAIL, reason=bump.reason, evidence=evidence,
                              constitution_ref="#11 版本号必须编码兼容性语义")

        # R2/R3 artifacts: any contract change escalates to human (INCONCLUSIVE)
        r = ctx.config.get("r_level") or (unit.r_level if unit else "R0")
        if r in ("R2", "R3") and delta.changes:
            return GateResult(self.gate_id, GateVerdict.INCONCLUSIVE,
                              reason=f"{r} artifact contract change requires human approval",
                              evidence=evidence,
                              constitution_ref="#11 契约制品破坏性变更须显式版本化并经人类批准")

        if delta.has_breaking and not bump.ok:
            return GateResult(self.gate_id, GateVerdict.FAIL, reason=explain(delta), evidence=evidence)

        return GateResult(self.gate_id, GateVerdict.PASS,
                          reason=explain(delta), evidence=evidence)

    def _extract_instance(self, ctx: GateContext) -> SurfaceSnapshot:
        paths = []
        for pattern in ctx.spec_unit.artifacts:
            from pathlib import Path

            root = Path(ctx.instance_path)
            p = root / pattern
            if p.is_dir():
                paths.append(p)
            elif p.suffix == ".py" and p.exists():
                paths.append(p)
            else:
                paths.extend(root.glob(pattern.rstrip("/") + "/*.py"))
        if not paths:
            paths = [ctx.instance_path]
        merged = SurfaceSnapshot(module=ctx.spec_unit.spec_id)
        for p in paths:
            snap = extract(p)
            for k, v in snap.functions.items():
                merged.functions[k] = v
            for k, v in snap.classes.items():
                merged.classes[k] = v
            for k, v in snap.constants.items():
                merged.constants[k] = v
            merged.dunder_exports = snap.dunder_exports or merged.dunder_exports
        return merged
