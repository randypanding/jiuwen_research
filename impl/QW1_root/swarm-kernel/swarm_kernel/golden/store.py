from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from swarm_kernel.contracts.base import utc_now_iso


class GoldenManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = 1
    artifact_id: str
    seed: int
    generator_config_sha256: str
    content_sha256: str
    created_by: str
    approved_by: str = ""
    created_at: str = Field(default_factory=utc_now_iso)

    @property
    def approved(self) -> bool:
        return bool(self.approved_by)


class GoldenPolicyError(Exception):
    pass


class GoldenStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _paths(self, artifact_id: str) -> tuple[Path, Path]:
        return self.root / f"{artifact_id}.golden", self.root / f"{artifact_id}.manifest.json"

    def write(self, artifact_id: str, content: str, seed: int, generator_config_sha256: str, created_by: str, approved_by: str = "", ci_mode: Optional[bool] = None) -> GoldenManifest:
        ci = os.environ.get("CI", "").lower() in ("1", "true", "yes") if ci_mode is None else ci_mode
        if ci:
            raise GoldenPolicyError("CI must never auto-write golden outputs; updates require human review + track-B evidence")
        content_path, manifest_path = self._paths(artifact_id)
        content_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        content_path.write_text(content, encoding="utf-8")
        manifest = GoldenManifest(
            artifact_id=artifact_id,
            seed=seed,
            generator_config_sha256=generator_config_sha256,
            content_sha256=content_sha,
            created_by=created_by,
            approved_by=approved_by,
        )
        manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2, ensure_ascii=False), encoding="utf-8")
        return manifest

    def load(self, artifact_id: str) -> tuple[str, GoldenManifest]:
        content_path, manifest_path = self._paths(artifact_id)
        if not content_path.exists() or not manifest_path.exists():
            raise GoldenPolicyError(f"missing golden artifact {artifact_id}: fail-closed")
        manifest = GoldenManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
        content = content_path.read_text(encoding="utf-8")
        if hashlib.sha256(content.encode("utf-8")).hexdigest() != manifest.content_sha256:
            raise GoldenPolicyError(f"golden artifact {artifact_id} corrupted: manifest mismatch")
        return content, manifest

    def compare(self, artifact_id: str, actual: str) -> tuple[bool, list[str], Optional[GoldenManifest]]:
        try:
            expected, manifest = self.load(artifact_id)
        except GoldenPolicyError as e:
            return False, [str(e)], None
        if actual == expected:
            return True, [], manifest
        exp_lines = expected.splitlines()
        act_lines = actual.splitlines()
        mismatches = []
        for i in range(max(len(exp_lines), len(act_lines))):
            e = exp_lines[i] if i < len(exp_lines) else "<missing>"
            a = act_lines[i] if i < len(act_lines) else "<missing>"
            if e != a:
                mismatches.append(f"line {i + 1}: expected {e!r} got {a!r}")
                if len(mismatches) >= 20:
                    mismatches.append("... truncated")
                    break
        return False, mismatches, manifest
