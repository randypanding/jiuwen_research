from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class ApprovalRequired(Exception):
    pass


class GoldenManifest(BaseModel):
    spec_hash: str
    seed: str
    lock_hash: str
    approved_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class GoldenVerdict(BaseModel):
    match: bool
    reason: str


class GoldenStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _paths(self, artifact_id: str) -> tuple[Path, Path]:
        return self.root / f"{artifact_id}.golden", self.root / f"{artifact_id}.manifest.json"

    def save(self, artifact_id: str, content: str, manifest: GoldenManifest) -> None:
        if "/" in artifact_id:
            raise ValueError(f"artifact_id must not contain '/': {artifact_id}")
        if not manifest.approved_by:
            # PDR-001：黄金输出锁定须人类批准，CI 永不自动写黄金
            raise ApprovalRequired(f"golden snapshot for {artifact_id} requires human approval")
        content_path, manifest_path = self._paths(artifact_id)
        content_path.write_text(content, encoding="utf-8")
        manifest_path.write_text(manifest.model_dump_json(), encoding="utf-8")

    def load(self, artifact_id: str) -> tuple[str, GoldenManifest]:
        content_path, manifest_path = self._paths(artifact_id)
        if not content_path.exists() or not manifest_path.exists():
            raise KeyError(artifact_id)
        manifest = GoldenManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        return content_path.read_text(encoding="utf-8"), manifest

    def compare(self, artifact_id: str, content: str) -> GoldenVerdict:
        try:
            stored, _ = self.load(artifact_id)
        except KeyError:
            return GoldenVerdict(match=False, reason="missing_snapshot")
        if stored != content:
            return GoldenVerdict(match=False, reason="content_mismatch")
        return GoldenVerdict(match=True, reason="match")
