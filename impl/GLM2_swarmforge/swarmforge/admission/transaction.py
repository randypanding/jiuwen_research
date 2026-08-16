"""准入事务：两阶段（PREPARE=门禁与测量全完成，COMMIT=原子落账）。

原子性与可恢复性：
- WAL（write-ahead log）先行：BEGIN → (spec-delta 应用 + 收据落账 + 测量保留)
  → COMMIT / ROLLBACK。
- 崩溃恢复：加载时发现无终态记录的 BEGIN → 显式 ROLLBACK；
- 幂等键：spec-delta 按 delta_id、收据按 receipt_id 去重，部分完成的事务
  重放安全。

INV2：被丢弃实例的测量结论必须保留——rollback 只弃实例，测量入
measurement_ledger（永久）。
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Optional

from ..gates.registry import GateRunOutcome
from ..specrepo.schema import SpecDelta
from ..specrepo.store import SpecStore
from .receipt import EvidenceReceipt, ReceiptLedger


class TransactionStateError(Exception):
    pass


@dataclass
class MeasurementRecord:
    """测量结论（无论实例是否准入，永久保留——spec 熵与健康度的数据源）。"""
    wave_id: str
    spec_delta_id: str
    instance_id: str
    passed: bool
    diff_conclusion: str
    classification: str          # 六格判定类别
    detail: dict = field(default_factory=dict)
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "wave_id": self.wave_id, "spec_delta_id": self.spec_delta_id,
            "instance_id": self.instance_id, "passed": self.passed,
            "diff_conclusion": self.diff_conclusion, "classification": self.classification,
            "detail": self.detail, "ts": self.ts,
        }


class MeasurementLedger:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def append(self, rec: MeasurementRecord) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")

    def all(self) -> list[MeasurementRecord]:
        if not os.path.exists(self.path):
            return []
        out = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    out.append(MeasurementRecord(**json.loads(line)))
        return out

    def for_wave(self, wave_id: str) -> list[MeasurementRecord]:
        return [m for m in self.all() if m.wave_id == wave_id]


class AdmissionTransaction:
    """单次准入的事务对象。begin → commit / rollback。"""

    def __init__(self, txn_root: str, store: SpecStore, ledger: ReceiptLedger,
                 measurement_ledger: MeasurementLedger):
        self.txn_root = txn_root
        os.makedirs(txn_root, exist_ok=True)
        self.store = store
        self.ledger = ledger
        self.measurements = measurement_ledger
        self._begin_record: Optional[dict] = None
        self._finished = False

    # ---------- WAL ----------
    def _wal_path(self, txn_id: str) -> str:
        return os.path.join(self.txn_root, f"{txn_id}.wal")

    def _wal_append(self, txn_id: str, record: dict) -> None:
        record = dict(record)
        record["ts"] = time.time()
        with open(self._wal_path(txn_id), "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # ---------- 生命周期 ----------
    @property
    def txn_id(self) -> str:
        if self._begin_record is None:
            raise TransactionStateError("transaction not begun")
        return self._begin_record["txn_id"]

    def begin(self, wave_id: str, domain: str, instance_id: str,
              gate_outcome: GateRunOutcome,
              spec_delta: SpecDelta,
              differential: dict,
              measurement_class: str,
              discarded_instances: Optional[list[str]] = None,
              r_levels_touched: Optional[list[str]] = None,
              cost: Optional[dict] = None,
              human_involved: bool = False) -> str:
        if self._begin_record is not None:
            raise TransactionStateError("already begun")
        txn_id = f"TXN-{wave_id}-{instance_id[:8]}-{int(time.time())}"
        self._begin_record = {
            "txn_id": txn_id, "state": "BEGIN", "wave_id": wave_id,
            "domain": domain, "instance_id": instance_id,
            "gate_decision": gate_outcome.decision.value,
            "gate_run": gate_outcome.to_dict(),
            "spec_delta": spec_delta.to_dict(),
            "differential": differential,
            "measurement_class": measurement_class,
            "discarded_instances": discarded_instances or [],
            "r_levels_touched": r_levels_touched or [],
            "cost": cost or {},
            "human_involved": human_involved,
        }
        self._wal_append(txn_id, self._begin_record)
        return txn_id

    def commit(self) -> str:
        """COMMIT：spec-delta 应用 → 收据落账 → 测量保留 → WAL COMMIT。

        任何一步失败 → 自动 rollback 并抛出原异常（事务不留中间态）。
        """
        if self._begin_record is None:
            raise TransactionStateError("not begun")
        if self._finished:
            raise TransactionStateError("already finished")
        rec = self._begin_record
        delta = SpecDelta(
            delta_id=rec["spec_delta"]["delta_id"],
            wave_id=rec["spec_delta"]["wave_id"],
            base_version=rec["spec_delta"]["base_version"],
            clauses_added=[], clauses_modified=[], clauses_removed=[],
            dont_cares_added=[], motivation="",
        )
        # 用完整 delta 重建（from_dict 语义）
        delta = _delta_from_dict(rec["spec_delta"])
        try:
            spec_version = self._apply_delta_idempotent(rec["domain"], delta)
            receipt_hash = self._append_receipt_idempotent(rec, spec_version)
            self._keep_measurements(rec, passed=True)
            self._wal_append(rec["txn_id"], {"state": "COMMIT",
                                             "receipt_hash": receipt_hash})
            self._finished = True
            return receipt_hash
        except Exception:
            self.rollback("commit failed; auto-rollback")
            raise

    def rollback(self, reason: str) -> None:
        """ROLLBACK：丢弃实例、保留测量结论（INV2）、WAL ROLLBACK。"""
        if self._begin_record is None:
            raise TransactionStateError("not begun")
        if self._finished:
            raise TransactionStateError("already finished")
        rec = self._begin_record
        self._keep_measurements(rec, passed=False)
        self._wal_append(rec["txn_id"], {"state": "ROLLBACK", "reason": reason})
        self._finished = True

    # ---------- 幂等步骤 ----------
    def _apply_delta_idempotent(self, domain: str, delta: SpecDelta) -> str:
        applied = any(v.delta_id == delta.delta_id for v in self.store.version_chain())
        if applied:
            doc = self.store.load_domain(domain)
            return doc.contract_hash() if doc else ""
        return self.store.apply_delta(domain, delta)

    def _append_receipt_idempotent(self, rec: dict, spec_version: str) -> str:
        if any(r.receipt_id == rec["txn_id"] for r in self.ledger.all()):
            return self.ledger.tail_hash()
        receipt = EvidenceReceipt(
            receipt_id=rec["txn_id"], wave_id=rec["wave_id"], domain=rec["domain"],
            spec_delta_id=rec["spec_delta"]["delta_id"],
            spec_version_after=spec_version, instance_id=rec["instance_id"],
            discarded_instances=rec["discarded_instances"],
            r_levels_touched=rec["r_levels_touched"],
            gate_run=rec["gate_run"], differential=rec["differential"],
            measurement_class=rec["measurement_class"], cost=rec["cost"],
            decided_by="leader", human_involved=rec["human_involved"],
        )
        return self.ledger.append(receipt)

    def _keep_measurements(self, rec: dict, passed: bool) -> None:
        for iid in [rec["instance_id"]] + list(rec["discarded_instances"]):
            self.measurements.append(MeasurementRecord(
                wave_id=rec["wave_id"],
                spec_delta_id=rec["spec_delta"]["delta_id"],
                instance_id=iid, passed=passed and iid == rec["instance_id"],
                diff_conclusion=(rec["differential"] or {}).get("conclusion", ""),
                classification=rec["measurement_class"],
                detail={"gate_decision": rec["gate_decision"]},
            ))

    # ---------- 崩溃恢复 ----------
    @classmethod
    def recover(cls, txn_root: str, store: SpecStore, ledger: ReceiptLedger,
                measurement_ledger: MeasurementLedger) -> list[str]:
        """加载 txn_root：无终态的 BEGIN 显式 ROLLBACK，返回恢复的 txn_id 列表。"""
        recovered: list[str] = []
        for name in sorted(os.listdir(txn_root)):
            if not name.endswith(".wal"):
                continue
            txn_id = name[:-4]
            path = os.path.join(txn_root, name)
            states: list[dict] = []
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        states.append(json.loads(line))
            if not states or states[-1].get("state") in ("COMMIT", "ROLLBACK"):
                continue
            begin = next(s for s in states if s.get("state") == "BEGIN")
            txn = cls.__new__(cls)
            txn.txn_root = txn_root
            txn.store = store
            txn.ledger = ledger
            txn.measurements = measurement_ledger
            txn._begin_record = begin
            txn._finished = False
            txn.rollback("recovered after crash")
            recovered.append(txn_id)
        return recovered


def _delta_from_dict(d: dict) -> SpecDelta:
    from ..specrepo.schema import ClauseLayer, DontCareEntry, SpecClause, WitnessRef
    def clause(c):
        return SpecClause(
            clause_id=c["clause_id"], layer=ClauseLayer(c["layer"]), text=c["text"],
            witnesses=[WitnessRef.from_dict(w) for w in c.get("witnesses", [])],
            anchors=list(c.get("anchors", [])),
            supersedes=c.get("supersedes"), rationale=c.get("rationale", ""))
    return SpecDelta(
        delta_id=d["delta_id"], wave_id=d["wave_id"], base_version=d["base_version"],
        clauses_added=[clause(c) for c in d.get("clauses_added", [])],
        clauses_modified=[clause(c) for c in d.get("clauses_modified", [])],
        clauses_removed=list(d.get("clauses_removed", [])),
        dont_cares_added=[DontCareEntry.from_dict(x) for x in d.get("dont_cares_added", [])],
        motivation=d.get("motivation", ""),
    )
