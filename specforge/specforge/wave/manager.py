"""Wave transaction manager: begin/register/admit/rollback with frontier lock.

ACID-lite on a single machine (decision D5):
  Atomicity  : admission is one commit + one receipt append; failure => discard
  Consistency: admission algebra must say ADMIT before commit
  Isolation  : frontier lock serializes admissions to the world (TTL + heartbeat)
  Durability : receipt ledger (hash chain) + wave state files on disk
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ..gates.base import AdmissionDecision, GateResult, decide_admission
from ..receipt.schema import EvidenceReceipt, ReceiptLedger
from .instance import InstancePort, InstanceRecord


class WaveError(RuntimeError):
    pass


class FrontierLock:
    """Single-flight admission lock with TTL (crashed holders expire)."""

    def __init__(self, path: str, ttl_s: float = 600.0):
        self.path = Path(path)
        self.ttl_s = ttl_s
        self._held = False

    def acquire(self) -> None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                ttl = float(data.get("ttl", self.ttl_s))  # holder's ttl wins
                age = time.time() - float(data.get("at", 0))
                if age < ttl:
                    raise WaveError(
                        f"frontier locked by {data.get('holder')} since {age:.0f}s ago (ttl={ttl}s)")
            except json.JSONDecodeError:
                pass  # corrupt lock: expire immediately
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"holder": os.getpid(), "at": time.time(), "ttl": self.ttl_s}),
            encoding="utf-8")
        self._held = True

    def heartbeat(self) -> None:
        if self._held and self.path.exists():
            self.path.write_text(
                json.dumps({"holder": os.getpid(), "at": time.time(), "ttl": self.ttl_s}),
                encoding="utf-8")

    def release(self) -> None:
        if self._held and self.path.exists():
            self.path.unlink()
        self._held = False


@dataclass
class WaveRecord:
    wave_id: str
    spec_delta: dict[str, Any]
    state: str = "OPEN"  # OPEN | COMMITTED | ABORTED | ROLLED_BACK
    instances: list[InstanceRecord] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    admitted_instance: Optional[str] = None
    commit_id: Optional[str] = None
    receipt_id: Optional[str] = None
    pipeline: str = "A"   # A=delivery, B=calibration

    def to_dict(self) -> dict[str, Any]:
        return {
            "wave_id": self.wave_id, "spec_delta": self.spec_delta, "state": self.state,
            "instances": [i.to_dict() for i in self.instances],
            "created_at": self.created_at, "admitted_instance": self.admitted_instance,
            "commit_id": self.commit_id, "receipt_id": self.receipt_id, "pipeline": self.pipeline,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "WaveRecord":
        return cls(
            wave_id=d["wave_id"], spec_delta=d.get("spec_delta", {}), state=d.get("state", "OPEN"),
            instances=[InstanceRecord(**{k: i.get(k) for k in
                                         ("instance_id", "wave_id", "source", "path", "status", "created_at")})
                       for i in d.get("instances", [])],
            created_at=d.get("created_at", 0.0), admitted_instance=d.get("admitted_instance"),
            commit_id=d.get("commit_id"), receipt_id=d.get("receipt_id"),
            pipeline=d.get("pipeline", "A"),
        )


class WaveManager:
    def __init__(self, root: str, port: InstancePort, world_ref: str = "main",
                 ledger_path: Optional[str] = None):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.port = port
        self.world_ref = world_ref
        self.ledger = ReceiptLedger(ledger_path or str(self.root / "receipts.jsonl"))
        self.lock = FrontierLock(str(self.root / "frontier.lock"))

    # ---- lifecycle ------------------------------------------------------------

    def begin(self, spec_delta: Any, pipeline: str = "A") -> WaveRecord:
        wave_id = f"wave-{uuid.uuid4().hex[:8]}"
        rec = WaveRecord(wave_id=wave_id,
                         spec_delta=spec_delta.to_dict() if hasattr(spec_delta, "to_dict") else dict(spec_delta),
                         pipeline=pipeline)
        self._save(rec)
        return rec

    def register_instance(self, wave_id: str, source: str, instance_id: Optional[str] = None) -> InstanceRecord:
        rec = self.load(wave_id)
        if rec.state != "OPEN":
            raise WaveError(f"wave {wave_id} is {rec.state}, cannot register")
        instance_id = instance_id or f"inst-{uuid.uuid4().hex[:6]}"
        path = self.port.materialize(wave_id, instance_id, source)
        ir = InstanceRecord(instance_id=instance_id, wave_id=wave_id, source=source,
                            path=path, status="MATERIALIZED")
        rec.instances.append(ir)
        self._save(rec)
        return ir

    # ---- admission ------------------------------------------------------------

    def admit(
        self,
        wave_id: str,
        instance_id: str,
        hard_results: list[GateResult],
        soft_results: Optional[list[GateResult]] = None,
        measurement: Optional[dict[str, Any]] = None,
        cost_usd: float = 0.0,
        wall_s: float = 0.0,
    ) -> tuple[AdmissionDecision, Optional[EvidenceReceipt]]:
        rec = self.load(wave_id)
        if rec.state != "OPEN":
            raise WaveError(f"wave {wave_id} is {rec.state}, cannot admit")
        decision = decide_admission(hard_results, soft_results or [])
        inst = next((i for i in rec.instances if i.instance_id == instance_id), None)
        if inst is None:
            raise WaveError(f"instance {instance_id} not registered in {wave_id}")

        if not decision.admitted:
            self.port.discard(wave_id, instance_id)
            inst.status = "DISCARDED"
            self._save(rec)
            return decision, None

        self.lock.acquire()
        try:
            commit_id = self.port.commit(wave_id, instance_id, self.world_ref)
            receipt = EvidenceReceipt(
                receipt_id=f"rcpt-{uuid.uuid4().hex[:8]}",
                spec_id=rec.spec_delta.get("spec_id", ""),
                spec_delta=rec.spec_delta,
                instance_id=instance_id,
                r_level=rec.spec_delta.get("r_level", "R0"),
                hard_gates=[r.to_dict() for r in hard_results],
                soft_gates=[r.to_dict() for r in (soft_results or [])],
                measurement=measurement,
                cost_usd=cost_usd, wall_s=wall_s,
            )
            self.ledger.append(receipt)
            rec.state = "COMMITTED"
            rec.admitted_instance = instance_id
            rec.commit_id = commit_id
            rec.receipt_id = receipt.receipt_id
            inst.status = "ADMITTED"
            # discard sibling instances (their measurement value is already captured)
            for other in rec.instances:
                if other.instance_id != instance_id and other.status == "MATERIALIZED":
                    self.port.discard(wave_id, other.instance_id)
                    other.status = "DISCARDED"
            self._save(rec)
            return decision, receipt
        except Exception:
            # atomicity: commit failed -> nothing entered the world
            rec.state = "ABORTED"
            self._save(rec)
            raise
        finally:
            self.lock.release()

    def rollback(self, wave_id: str, reason: str) -> str:
        rec = self.load(wave_id)
        if rec.state != "COMMITTED" or not rec.commit_id:
            raise WaveError(f"wave {wave_id} not committed, nothing to rollback")
        self.lock.acquire()
        try:
            new_head = self.port.rollback(rec.commit_id, self.world_ref)
            rec.state = "ROLLED_BACK"
            self._save(rec)

            def mark(r: EvidenceReceipt) -> None:
                if r.receipt_id == rec.receipt_id:
                    r.reverted = True
                    r.revert_reason = reason

            self.ledger.update_last(mark)
            return new_head
        finally:
            self.lock.release()

    # ---- persistence ----------------------------------------------------------

    def _save(self, rec: WaveRecord) -> None:
        d = self.root / "waves" / rec.wave_id
        d.mkdir(parents=True, exist_ok=True)
        (d / "wave.json").write_text(json.dumps(rec.to_dict(), ensure_ascii=False, indent=1),
                                     encoding="utf-8")

    def load(self, wave_id: str) -> WaveRecord:
        p = self.root / "waves" / wave_id / "wave.json"
        if not p.exists():
            raise WaveError(f"unknown wave {wave_id}")
        return WaveRecord.from_dict(json.loads(p.read_text(encoding="utf-8")))

    def frontier_status(self) -> dict[str, Any]:
        lock_path = self.root / "frontier.lock"
        info: dict[str, Any] = {"locked": lock_path.exists()}
        if lock_path.exists():
            try:
                data = json.loads(lock_path.read_text(encoding="utf-8"))
                info.update(data)
                info["age_s"] = round(time.time() - float(data.get("at", 0)), 1)
            except json.JSONDecodeError:
                info["corrupt"] = True
        info["chain_errors"] = self.ledger.verify_chain()
        return info
