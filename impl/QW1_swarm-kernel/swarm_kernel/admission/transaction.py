from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Optional

from swarm_kernel.contracts.admission import AdmissionDecision, LedgerEntry
from swarm_kernel.contracts.base import Verdict
from swarm_kernel.contracts.gates import GateSuiteResult
from swarm_kernel.contracts.oracle import JudgeVerdict, JudgeVerdictKind
from swarm_kernel.contracts.admission import EvidenceReceipt


class AdmissionError(Exception):
    pass


class AdmissionTransaction:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.world = self.root / "world"
        self.staging = self.root / "staging"
        self.preimages = self.root / "preimages"
        self.ledger_dir = self.root / "ledger"
        for d in (self.world, self.staging, self.preimages, self.ledger_dir):
            d.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.ledger_dir / "ledger.jsonl"
        self._lock_path = self.root / ".lock"

    def _acquire(self, timeout_s: float = 10.0) -> None:
        deadline = time.time() + timeout_s
        while True:
            try:
                fd = os.open(self._lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return
            except FileExistsError:
                if time.time() > deadline:
                    raise AdmissionError("lock timeout")
                time.sleep(0.05)

    def _release(self) -> None:
        try:
            self._lock_path.unlink()
        except FileNotFoundError:
            pass

    def _last_entry(self) -> Optional[LedgerEntry]:
        if not self.ledger_path.exists():
            return None
        lines = [l for l in self.ledger_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        if not lines:
            return None
        return LedgerEntry.model_validate(json.loads(lines[-1]))

    def verify_receipt(self, receipt: EvidenceReceipt) -> list[str]:
        problems: list[str] = []
        suite = receipt.gate_suite
        if not suite.hard_pass:
            problems.append(f"hard gates not all passed: {[g.value for g in suite.blocking_gates()]}")
        if receipt.judge_verdict is not None and receipt.judge_verdict.kind == JudgeVerdictKind.VETO:
            problems.append("soft gate vetoed")
        if not receipt.drift_check.clean:
            problems.append("drift check not clean")
        if not receipt.chosen_instance_id:
            problems.append("no chosen instance")
        return problems

    def admit(self, receipt: EvidenceReceipt) -> AdmissionDecision:
        problems = self.verify_receipt(receipt)
        if problems:
            return AdmissionDecision(admit=False, receipt_id=receipt.receipt_id, reasons=problems)
        return self._commit(receipt)

    def _commit(self, receipt: EvidenceReceipt) -> AdmissionDecision:
        self._acquire()
        try:
            source = self.staging / receipt.chosen_instance_id
            if not source.exists():
                return AdmissionDecision(admit=False, receipt_id=receipt.receipt_id, reasons=[f"staging missing {receipt.chosen_instance_id}"])
            target = self.world / receipt.chosen_instance_id
            tx_id = f"tx-{receipt.receipt_id}"
            preimage_dir = self.preimages / tx_id
            preimage_dir.mkdir(parents=True, exist_ok=True)
            if target.exists():
                shutil.copytree(target, preimage_dir / target.name, dirs_exist_ok=True)
            else:
                (preimage_dir / "__absent__").write_text("", encoding="utf-8")
            tmp_target = self.world / f".{receipt.chosen_instance_id}.incoming"
            if tmp_target.exists():
                shutil.rmtree(tmp_target)
            shutil.copytree(source, tmp_target)
            (tmp_target / "EVIDENCE.json").write_text(receipt.model_dump_json(indent=2), encoding="utf-8")
            if target.exists():
                shutil.rmtree(target)
            os.replace(tmp_target, target)
            prior = self._last_entry()
            entry = LedgerEntry(
                transaction_id=tx_id,
                receipt_sha256=receipt.receipt_hash(),
                instance_id=receipt.chosen_instance_id,
                target_path=str(target),
                op="commit",
            ).seal(prior.entry_sha256 if prior else "")
            with self.ledger_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry.model_dump(mode="json"), ensure_ascii=False) + "\n")
            return AdmissionDecision(admit=True, receipt_id=receipt.receipt_id, reasons=["H1-H8 pass", "S pass"], rollback_handle=tx_id, transaction_id=tx_id)
        finally:
            self._release()

    def verify_ledger_chain(self) -> tuple[bool, str]:
        if not self.ledger_path.exists():
            return True, ""
        prior_sha = ""
        for line in self.ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = LedgerEntry.model_validate(json.loads(line))
            recorded = entry.entry_sha256
            entry.entry_sha256 = ""
            recomputed = entry.sha256()
            if entry.prior_entry_sha256 != prior_sha or recomputed != recorded:
                return False, entry.transaction_id
            prior_sha = recorded
        return True, ""

    def rollback(self, transaction_id: str) -> AdmissionDecision:
        self._acquire()
        try:
            entries = []
            if self.ledger_path.exists():
                entries = [LedgerEntry.model_validate(json.loads(l)) for l in self.ledger_path.read_text(encoding="utf-8").splitlines() if l.strip()]
            target_entry = next((e for e in entries if e.transaction_id == transaction_id), None)
            if target_entry is None:
                return AdmissionDecision(admit=False, receipt_id="", reasons=[f"unknown transaction {transaction_id}"])
            preimage_dir = self.preimages / transaction_id
            world_target = self.world / target_entry.instance_id
            if not preimage_dir.exists():
                return AdmissionDecision(admit=False, receipt_id="", reasons=["preimage missing; manual recovery required"])
            if world_target.exists():
                shutil.rmtree(world_target)
            restored = list(preimage_dir.iterdir())
            if restored and restored[0].name != "__absent__":
                shutil.copytree(restored[0], world_target)
            prior = entries[-2] if len(entries) >= 2 else None
            entry = LedgerEntry(
                transaction_id=f"{transaction_id}-rollback",
                receipt_sha256=target_entry.receipt_sha256,
                instance_id=target_entry.instance_id,
                target_path=str(world_target),
                op="rollback",
            ).seal(entries[-1].entry_sha256 if entries else "")
            with self.ledger_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry.model_dump(mode="json"), ensure_ascii=False) + "\n")
            return AdmissionDecision(admit=True, receipt_id=target_entry.receipt_sha256, reasons=["rolled back"], rollback_handle=transaction_id, transaction_id=entry.transaction_id)
        finally:
            self._release()
