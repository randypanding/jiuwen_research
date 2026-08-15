"""Golden output store with manifest gate (WP5, D8).

Tracks:
  - golden/<unit>/golden.jsonl     expected outputs (normalized form)
  - golden/<unit>/manifest.json    .r3info-style manifest (env, deps, seeds, approvals)
Rules:
  - CI never auto-writes golden (approve_update is the only write path)
  - manifest mismatch -> INCONCLUSIVE (comparability premise broken)
  - updates archive the previous golden with reason label
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ..difftest.normalizer import NormalizeRules


@dataclass
class GoldenManifest:
    code_version: str = ""
    deps_hash: str = ""
    seed: int = 0
    model_version: str = ""
    python_version: str = field(default_factory=lambda: platform.python_version())
    platform: str = field(default_factory=lambda: f"{platform.system()}/{platform.machine()}")
    generated_by: str = ""
    approved_by: str = ""
    approval_reason: str = ""
    update_label: str = ""   # intent-change | refactor-equiv | bugfix | spec-upgrade
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code_version": self.code_version, "deps_hash": self.deps_hash, "seed": self.seed,
            "model_version": self.model_version, "python_version": self.python_version,
            "platform": self.platform, "generated_by": self.generated_by,
            "approved_by": self.approved_by, "approval_reason": self.approval_reason,
            "update_label": self.update_label, "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GoldenManifest":
        return cls(**{k: d.get(k, v) for k, v in cls().to_dict().items()})

    def fingerprint(self) -> str:
        payload = {k: v for k, v in self.to_dict().items()
                   if k not in ("approved_by", "approval_reason", "created_at", "update_label")}
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


@dataclass
class GoldenCompareResult:
    verdict: str   # MATCH | MISMATCH | INCONCLUSIVE | MISSING
    detail: str = ""
    diff_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"verdict": self.verdict, "detail": self.detail, "diff_paths": self.diff_paths}


def compute_deps_hash(requirements_txt: str = "") -> str:
    return hashlib.sha256(requirements_txt.encode()).hexdigest()[:16]


class GoldenStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _dir(self, unit_id: str) -> Path:
        d = self.root / unit_id.replace("/", "__")
        d.mkdir(parents=True, exist_ok=True)
        return d

    def manifest(self, unit_id: str) -> Optional[GoldenManifest]:
        p = self._dir(unit_id) / "manifest.json"
        if not p.exists():
            return None
        return GoldenManifest.from_dict(json.loads(p.read_text(encoding="utf-8")))

    def golden_records(self, unit_id: str) -> list[dict[str, Any]]:
        p = self._dir(unit_id) / "golden.jsonl"
        if not p.exists():
            return []
        return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]

    def compare(
        self,
        unit_id: str,
        records: Optional[list[dict[str, Any]]],
        *,
        expected_manifest: Optional[GoldenManifest] = None,
        rules: Optional[NormalizeRules] = None,
    ) -> GoldenCompareResult:
        rules = rules or NormalizeRules()
        man = self.manifest(unit_id)
        if man is None:
            return GoldenCompareResult("MISSING", f"no golden manifest for {unit_id}")
        if expected_manifest is not None and man.fingerprint() != expected_manifest.fingerprint():
            return GoldenCompareResult(
                "INCONCLUSIVE",
                "manifest mismatch: comparability premise broken "
                f"(stored={man.fingerprint()[:8]} expected={expected_manifest.fingerprint()[:8]})")
        if records is None:
            return GoldenCompareResult("INCONCLUSIVE", "no records provided for comparison")
        golden = self.golden_records(unit_id)
        if not golden:
            return GoldenCompareResult("MISSING", f"no golden records for {unit_id}")
        if len(golden) != len(records):
            return GoldenCompareResult("MISMATCH",
                                       f"record count {len(records)} != golden {len(golden)}")
        from ..difftest.comparator import compare_outputs

        for i, (g, r) in enumerate(zip(golden, records)):
            outcome = compare_outputs(g.get("output"), r.get("output"), rules)
            if outcome.verdict != "EQUAL":
                paths = [d.path for d in outcome.diffs][:5]
                return GoldenCompareResult(
                    "MISMATCH", f"record[{i}] differs at {paths}",
                    diff_paths=[d.path for d in outcome.diffs])
        return GoldenCompareResult("MATCH", f"{len(records)} records match golden (normalized)")

    def approve_update(
        self,
        unit_id: str,
        records: list[dict[str, Any]],
        manifest: GoldenManifest,
        *,
        approver: str,
        reason: str,
        update_label: str,
        allow_ci: bool = False,
    ) -> GoldenManifest:
        """The ONLY write path. Requires human approver identity + label."""
        if os.environ.get("CI") == "true" and not allow_ci:
            raise PermissionError("CI must never auto-write golden (constitution #12; r3 rule 1)")
        if not approver or not reason:
            raise ValueError("approver and reason are mandatory for golden updates")
        if update_label not in ("intent-change", "refactor-equiv", "bugfix", "spec-upgrade"):
            raise ValueError(f"update_label {update_label!r} invalid")
        d = self._dir(unit_id)
        # archive previous
        prev = d / "golden.jsonl"
        if prev.exists():
            ts = int(time.time())
            shutil.copy2(prev, d / f"golden.{ts}.jsonl")
        manifest.approved_by = approver
        manifest.approval_reason = reason
        manifest.update_label = update_label
        with open(prev, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        (d / "manifest.json").write_text(json.dumps(manifest.to_dict(), indent=1), encoding="utf-8")
        return manifest
