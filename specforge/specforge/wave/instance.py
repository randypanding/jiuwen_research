"""InstancePort: materialize/commit/discard/rollback instances (wave physical layer).

GitInstancePort: git worktree/branch based (default). FakeInstancePort for tests.
Two-phase intent: prepare = gates already run on materialized instance dir;
commit = atomic merge into world ref; externalized side effects are deferred
to post-commit by the orchestrator (constitution #12).
"""
from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Protocol


class InstancePortError(RuntimeError):
    pass


class InstancePort(Protocol):
    def materialize(self, wave_id: str, instance_id: str, source: str) -> str: ...
    def commit(self, wave_id: str, instance_id: str, world_ref: str) -> str: ...
    def discard(self, wave_id: str, instance_id: str) -> None: ...
    def rollback(self, commit_id: str, world_ref: str) -> str: ...
    def instance_path(self, wave_id: str, instance_id: str) -> str: ...


@dataclass
class InstanceRecord:
    instance_id: str
    wave_id: str
    source: str
    path: str = ""
    status: str = "REGISTERED"   # REGISTERED | MATERIALIZED | ADMITTED | DISCARDED
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {"instance_id": self.instance_id, "wave_id": self.wave_id,
                "source": self.source, "path": self.path, "status": self.status,
                "created_at": self.created_at}


class GitInstancePort:
    """Default port: each instance is a git worktree on its own branch.

    repo: path to the world git repo. world_ref: branch to merge into (e.g. main).
    """

    def __init__(self, repo: str, workroot: str):
        self.repo = Path(repo)
        self.workroot = Path(workroot)
        self.workroot.mkdir(parents=True, exist_ok=True)

    def _git(self, *args: str, cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
        proc = subprocess.run(["git", *args], cwd=cwd or self.repo,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if check and proc.returncode != 0:
            raise InstancePortError(f"git {' '.join(args)} failed: {proc.stderr.strip()[:300]}")
        return proc

    def materialize(self, wave_id: str, instance_id: str, source: str) -> str:
        branch = f"sf/{wave_id}/{instance_id}"
        # source may be a commit/branch; create instance branch from it
        self._git("branch", "-f", branch, source)
        wt = self.workroot / wave_id / instance_id
        if wt.exists():
            shutil.rmtree(wt, ignore_errors=True)
        (self.workroot / wave_id).mkdir(parents=True, exist_ok=True)
        self._git("worktree", "add", "--detach", str(wt), branch)
        return str(wt)

    def instance_path(self, wave_id: str, instance_id: str) -> str:
        return str(self.workroot / wave_id / instance_id)

    def commit(self, wave_id: str, instance_id: str, world_ref: str) -> str:
        wt = Path(self.instance_path(wave_id, instance_id))
        branch = f"sf/{wave_id}/{instance_id}"
        self._git("add", "-A", cwd=wt)
        self._git("-c", "user.email=specforge@wave", "-c", "user.name=specforge",
                  "commit", "--allow-empty", "-m", f"admit {wave_id}/{instance_id}", cwd=wt)
        self._git("branch", "-f", branch, "HEAD", cwd=wt)
        # fast-forward-merge into world ref
        self._git("checkout", world_ref)
        proc = self._git("merge", "--no-ff", "--no-edit", branch, check=False)
        if proc.returncode != 0:
            self._git("merge", "--abort", check=False)
            raise InstancePortError(f"non-fast-forward conflict merging {branch} into {world_ref}")
        return self._git("rev-parse", "HEAD").stdout.strip()

    def discard(self, wave_id: str, instance_id: str) -> None:
        wt = Path(self.instance_path(wave_id, instance_id))
        if wt.exists():
            self._git("worktree", "remove", "--force", str(wt), check=False)
        self._git("branch", "-D", f"sf/{wave_id}/{instance_id}", check=False)

    def rollback(self, commit_id: str, world_ref: str) -> str:
        self._git("checkout", world_ref)
        self._git("-c", "user.email=specforge@wave", "-c", "user.name=specforge",
                  "revert", "--no-edit", commit_id)
        return self._git("rev-parse", "HEAD").stdout.strip()


class FakeInstancePort:
    """In-memory port for tests: copies source trees, tracks commit order."""

    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.commits: list[tuple[str, str]] = []   # (commit_id, instance_id)
        self.rollbacks: list[str] = []
        self._seq = 0
        self.fail_commit = False

    def materialize(self, wave_id: str, instance_id: str, source: str) -> str:
        dst = self.root / wave_id / instance_id
        dst.mkdir(parents=True, exist_ok=True)
        src = Path(source)
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        elif src.is_file():
            shutil.copy2(src, dst / src.name)
        else:
            (dst / "instance.txt").write_text(source, encoding="utf-8")
        return str(dst)

    def instance_path(self, wave_id: str, instance_id: str) -> str:
        return str(self.root / wave_id / instance_id)

    def commit(self, wave_id: str, instance_id: str, world_ref: str) -> str:
        if self.fail_commit:
            raise InstancePortError("simulated commit failure")
        self._seq += 1
        commit_id = f"fake-commit-{self._seq}"
        self.commits.append((commit_id, instance_id))
        return commit_id

    def discard(self, wave_id: str, instance_id: str) -> None:
        import shutil as _sh

        p = Path(self.instance_path(wave_id, instance_id))
        if p.exists():
            _sh.rmtree(p, ignore_errors=True)

    def rollback(self, commit_id: str, world_ref: str) -> str:
        self.rollbacks.append(commit_id)
        self._seq += 1
        return f"fake-revert-{self._seq}"
