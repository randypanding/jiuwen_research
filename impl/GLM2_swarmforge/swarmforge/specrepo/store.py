"""SpecStore：文件型 spec 仓。

目录布局（零依赖 JSON，机械可判等、diff 友好）：
    specs/
      domains/<domain>.spec.json      # SpecDocument（L1 摘要+条款三层+don't-care）
      registry.json                   # R 级注册表（全局）
      versions.jsonl                  # 版本链（append-only，一 delta 一行）
      locks/<wave>.json               # 波次接口锁（接口冻结窗口）

写路径全部原子（tmp + os.replace）；版本链只追加；
真值 = 文件内容，内存对象只是投影。
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import dataclass, asdict
from typing import Optional

from .rregistry import RRegistry
from .schema import SpecDocument, SpecDelta


class SpecConflictError(Exception):
    """spec-delta 的 base_version 与当前契约哈希不符（乐观并发冲突）。"""


@dataclass
class VersionRecord:
    version: str          # 本版本契约哈希
    delta_id: str
    wave_id: str
    ts: float
    actor: str            # 提交者角色（spec_moderator / human / harvest_bot）

    def to_dict(self) -> dict:
        return asdict(self)


class InterfaceLock:
    """波次接口锁：接口冻结窗口的物理实现。

    锁的是 L2 契约面（条款 id 集合），不是文件——多个波次可并行，
    只要它们冻结的条款集不相交（spec-concurrency 研究的接口级锁结论）。
    """

    def __init__(self, wave_id: str, clause_ids: list[str], ttl_seconds: float = 3600.0):
        self.wave_id = wave_id
        self.clause_ids = frozenset(clause_ids)
        self.ttl = ttl_seconds
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl_seconds

    def expired(self, now: Optional[float] = None) -> bool:
        return (now if now is not None else time.time()) > self.expires_at

    def overlaps(self, other: "InterfaceLock") -> bool:
        return bool(self.clause_ids & other.clause_ids)


class SpecStore:
    """spec 仓的机械操作面。所有写操作走 apply_delta（版本链一致性）。"""

    def __init__(self, root: str):
        self.root = root
        self.domains_dir = os.path.join(root, "domains")
        self.registry_path = os.path.join(root, "registry.json")
        self.versions_path = os.path.join(root, "versions.jsonl")
        self.locks_dir = os.path.join(root, "locks")
        os.makedirs(self.domains_dir, exist_ok=True)
        os.makedirs(self.locks_dir, exist_ok=True)

    # ---------- 原子写 ----------
    @staticmethod
    def _atomic_write(path: str, payload: dict) -> None:
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    # ---------- 读 ----------
    def load_domain(self, domain: str) -> Optional[SpecDocument]:
        path = os.path.join(self.domains_dir, f"{domain}.spec.json")
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as f:
            return SpecDocument.from_dict(json.load(f))

    def load_registry(self) -> RRegistry:
        if not os.path.exists(self.registry_path):
            return RRegistry()
        with open(self.registry_path, encoding="utf-8") as f:
            return RRegistry.from_dict(json.load(f))

    def version_chain(self) -> list[VersionRecord]:
        if not os.path.exists(self.versions_path):
            return []
        out = []
        with open(self.versions_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(VersionRecord(**json.loads(line)))
        return out

    # ---------- 写 ----------
    def init_domain(self, doc: SpecDocument, actor: str = "human") -> str:
        path = os.path.join(self.domains_dir, f"{doc.domain}.spec.json")
        self._atomic_write(path, doc.to_dict())
        return doc.contract_hash()

    def write_registry(self, registry: RRegistry) -> None:
        self._atomic_write(self.registry_path, registry.to_dict())

    def acquire_lock(self, lock: InterfaceLock) -> None:
        """获取波次接口锁：与任何未过期锁的条款集相交即拒绝。"""
        for existing in self.active_locks():
            if not existing.expired() and existing.overlaps(lock):
                raise SpecConflictError(
                    f"interface lock conflict: wave {lock.wave_id} overlaps "
                    f"clause set of wave {existing.wave_id} "
                    f"({sorted(lock.clause_ids & existing.clause_ids)})"
                )
        self._atomic_write(
            os.path.join(self.locks_dir, f"{lock.wave_id}.json"),
            {
                "wave_id": lock.wave_id,
                "clause_ids": sorted(lock.clause_ids),
                "created_at": lock.created_at,
                "expires_at": lock.expires_at,
            },
        )

    def release_lock(self, wave_id: str) -> None:
        path = os.path.join(self.locks_dir, f"{wave_id}.json")
        if os.path.exists(path):
            os.unlink(path)

    def active_locks(self) -> list[InterfaceLock]:
        out: list[InterfaceLock] = []
        if not os.path.isdir(self.locks_dir):
            return out
        for name in os.listdir(self.locks_dir):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(self.locks_dir, name), encoding="utf-8") as f:
                d = json.load(f)
            lock = InterfaceLock(d["wave_id"], d["clause_ids"])
            lock.created_at = d["created_at"]
            lock.expires_at = d["expires_at"]
            out.append(lock)
        return out

    def apply_delta(self, domain: str, delta: SpecDelta, actor: str = "spec_moderator") -> str:
        """原子应用 spec-delta：乐观并发检查 → 变更 → 版本链追加。

        准入事务的 COMMIT 阶段调用；失败抛 SpecConflictError，不改任何文件。
        """
        doc = self.load_domain(domain)
        if doc is None:
            raise FileNotFoundError(f"unknown domain {domain}")
        current = doc.contract_hash()
        if delta.base_version != current:
            raise SpecConflictError(
                f"stale delta: base={delta.base_version[:12]} current={current[:12]}"
            )
        removed = set(delta.clauses_removed)
        doc.clauses = [c for c in doc.clauses if c.clause_id not in removed]
        by_id = {c.clause_id: c for c in doc.clauses}
        for c in delta.clauses_added + delta.clauses_modified:
            by_id[c.clause_id] = c
        doc.clauses = list(by_id.values())
        existing_dc = {d.entry_id for d in doc.dont_cares}
        for d in delta.dont_cares_added:
            if d.entry_id not in existing_dc:
                doc.dont_cares.append(d)
        new_version = doc.contract_hash()
        self._atomic_write(
            os.path.join(self.domains_dir, f"{domain}.spec.json"), doc.to_dict()
        )
        rec = VersionRecord(
            version=new_version, delta_id=delta.delta_id, wave_id=delta.wave_id,
            ts=time.time(), actor=actor,
        )
        with open(self.versions_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return new_version
