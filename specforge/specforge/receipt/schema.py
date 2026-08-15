"""Evidence receipt schema + hash chain (WP8).

A receipt is the admission transaction record (PR redefined): spec-delta ref,
R level, selected instance, discarded instances' measurement, H results,
S verdicts, differential conclusion, drift check, cost, hash chain links.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional

RECEIPT_VERSION = 1


def _sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False,
                                     default=str).encode()).hexdigest()


@dataclass
class EvidenceReceipt:
    receipt_id: str
    spec_id: str
    spec_delta: dict[str, Any]
    instance_id: str
    r_level: str = "R0"
    hard_gates: list[dict[str, Any]] = field(default_factory=list)
    soft_gates: list[dict[str, Any]] = field(default_factory=list)
    measurement: Optional[dict[str, Any]] = None
    drift_check: str = "PASS"
    cost_usd: float = 0.0
    wall_s: float = 0.0
    admitted_at: float = field(default_factory=time.time)
    prev_hash: str = ""
    receipt_hash: str = ""
    reverted: bool = False
    revert_reason: str = ""

    def body_hash(self) -> str:
        body = {
            "receipt_id": self.receipt_id,
            "spec_id": self.spec_id,
            "spec_delta": self.spec_delta,
            "instance_id": self.instance_id,
            "r_level": self.r_level,
            "hard_gates": self.hard_gates,
            "soft_gates": self.soft_gates,
            "measurement": self.measurement,
            "drift_check": self.drift_check,
            "cost_usd": self.cost_usd,
            "wall_s": self.wall_s,
            "admitted_at": self.admitted_at,
            "prev_hash": self.prev_hash,
            "reverted": self.reverted,
            "revert_reason": self.revert_reason,
        }
        return _sha(body)

    def seal(self) -> "EvidenceReceipt":
        self.receipt_hash = self.body_hash()
        return self

    def verify(self) -> bool:
        return self.receipt_hash == self.body_hash()

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_version": RECEIPT_VERSION,
            **{
                "receipt_id": self.receipt_id, "spec_id": self.spec_id,
                "spec_delta": self.spec_delta, "instance_id": self.instance_id,
                "r_level": self.r_level, "hard_gates": self.hard_gates,
                "soft_gates": self.soft_gates, "measurement": self.measurement,
                "drift_check": self.drift_check, "cost_usd": self.cost_usd,
                "wall_s": self.wall_s, "admitted_at": self.admitted_at,
                "prev_hash": self.prev_hash, "receipt_hash": self.receipt_hash,
                "reverted": self.reverted, "revert_reason": self.revert_reason,
            },
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EvidenceReceipt":
        return cls(
            receipt_id=d["receipt_id"], spec_id=d["spec_id"], spec_delta=d.get("spec_delta", {}),
            instance_id=d.get("instance_id", ""), r_level=d.get("r_level", "R0"),
            hard_gates=d.get("hard_gates", []), soft_gates=d.get("soft_gates", []),
            measurement=d.get("measurement"), drift_check=d.get("drift_check", "PASS"),
            cost_usd=d.get("cost_usd", 0.0), wall_s=d.get("wall_s", 0.0),
            admitted_at=d.get("admitted_at", 0.0), prev_hash=d.get("prev_hash", ""),
            receipt_hash=d.get("receipt_hash", ""), reverted=d.get("reverted", False),
            revert_reason=d.get("revert_reason", ""),
        )


class ReceiptLedger:
    """Append-only ledger on disk; verifies the hash chain."""

    def __init__(self, path: str):
        self.path = path
        import os
        from pathlib import Path

        self._dir = Path(path).parent
        self._dir.mkdir(parents=True, exist_ok=True)
        if not Path(path).exists():
            Path(path).write_text("", encoding="utf-8")
            try:
                os.chmod(path, 0o644)
            except OSError:
                pass

    def append(self, receipt: EvidenceReceipt) -> EvidenceReceipt:
        prev = self.tail()
        receipt.prev_hash = prev.receipt_hash if prev else ""
        receipt.seal()
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(receipt.to_dict(), ensure_ascii=False) + "\n")
        return receipt

    def all(self) -> list[EvidenceReceipt]:
        out: list[EvidenceReceipt] = []
        for line in open(self.path, encoding="utf-8").read().splitlines():
            if line.strip():
                out.append(EvidenceReceipt.from_dict(json.loads(line)))
        return out

    def tail(self) -> Optional[EvidenceReceipt]:
        receipts = self.all()
        return receipts[-1] if receipts else None

    def verify_chain(self) -> list[str]:
        errors: list[str] = []
        prev_hash = ""
        for r in self.all():
            if not r.verify():
                errors.append(f"{r.receipt_id}: body hash mismatch (tampered?)")
            if r.prev_hash != prev_hash:
                errors.append(f"{r.receipt_id}: broken chain link (prev={r.prev_hash[:8]} expected={prev_hash[:8]})")
            prev_hash = r.receipt_hash
        return errors

    def update_last(self, mutate) -> None:
        """Atomically rewrite ledger applying `mutate` to the last receipt (used by rollback)."""
        receipts = self.all()
        if not receipts:
            raise IndexError("empty ledger")
        mutate(receipts[-1])
        receipts[-1].seal()
        with open(self.path, "w", encoding="utf-8") as f:
            for r in receipts:
                f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
