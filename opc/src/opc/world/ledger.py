from __future__ import annotations

import json
from pathlib import Path

from opc.schemas.common import sha256_hex
from opc.schemas.evidence import EvidenceReceipt, LedgerEntry


class AdmissionLedger:
    """Append-only hash-chained ledger of admission receipts.

    Every entry commits to the previous entry's chain digest; any silent
    edit, re-ordering or deletion of history breaks verify(). Rollback is
    expressed as a compensating entry, never as deletion.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _entries(self) -> list[LedgerEntry]:
        if not self.path.exists():
            return []
        entries = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entries.append(LedgerEntry.model_validate_json(line))
        return entries

    def head(self) -> LedgerEntry | None:
        entries = self._entries()
        return entries[-1] if entries else None

    def append(self, receipt: EvidenceReceipt) -> LedgerEntry:
        entries = self._entries()
        prev_digest = entries[-1].chain_digest if entries else LedgerEntry.genesis()
        seq = len(entries)
        receipt_digest = receipt.digest()
        chain_digest = sha256_hex(f"{seq}|{receipt_digest}|{prev_digest}".encode("utf-8"))
        entry = LedgerEntry(seq=seq, receipt_digest=receipt_digest, prev_digest=prev_digest, chain_digest=chain_digest)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")
        return entry

    def verify(self) -> tuple[bool, list[str]]:
        entries = self._entries()
        problems: list[str] = []
        prev_digest = LedgerEntry.genesis()
        for index, entry in enumerate(entries):
            if entry.seq != index:
                problems.append(f"seq gap at position {index}: found {entry.seq}")
            if entry.prev_digest != prev_digest:
                problems.append(f"broken link at seq {entry.seq}: prev_digest mismatch")
            expected = sha256_hex(f"{entry.seq}|{entry.receipt_digest}|{entry.prev_digest}".encode("utf-8"))
            if entry.chain_digest != expected:
                problems.append(f"tampered entry at seq {entry.seq}: chain_digest mismatch")
            prev_digest = entry.chain_digest
        return (not problems, problems)

    def receipts_count(self) -> int:
        return len(self._entries())

    def to_json(self) -> str:
        return json.dumps([e.model_dump(mode="json") for e in self._entries()], ensure_ascii=False)
