from __future__ import annotations


from opc.schemas.common import RLevel, Verdict
from opc.schemas.evidence import EvidenceReceipt
from opc.schemas.gates import AdmissionVerdict
from opc.schemas.wave import AdmissionTransaction, InstanceRecord, WaveManifest
from opc.world.ledger import AdmissionLedger


class AdmissionError(Exception):
    pass


class AdmissionController:
    """Wave transaction boundary: collect -> judge -> atomic commit/abort.

    Instances stay in the staging area (weights) until commit; after commit
    they are world state and can only evolve through spec-delta derivation.
    Rollback appends a compensating record; the ledger itself is immutable.
    """

    def __init__(self, ledger: AdmissionLedger):
        self.ledger = ledger
        self.waves: dict[str, WaveManifest] = {}
        self.staging: dict[str, list[InstanceRecord]] = {}
        self.transactions: dict[str, AdmissionTransaction] = {}
        self.wave_receipts: dict[str, list[str]] = {}

    def begin_wave(self, manifest: WaveManifest) -> None:
        if manifest.wave_id in self.waves:
            raise AdmissionError(f"wave {manifest.wave_id} already exists")
        self.waves[manifest.wave_id] = manifest
        self.staging[manifest.wave_id] = []

    def stage_instance(self, wave_id: str, record: InstanceRecord) -> None:
        wave = self._wave(wave_id)
        if wave.status != "collecting":
            raise AdmissionError(f"wave {wave_id} is {wave.status}; staging closed")
        self.staging[wave_id].append(record)

    def fanout_policy_violation(self, wave_id: str, contract_id: str, fanout_n: int) -> str | None:
        wave = self._wave(wave_id)
        r_level = wave.r_levels.get(contract_id)
        if r_level in (RLevel.R2, RLevel.R3) and fanout_n > 1:
            return f"{contract_id} is {r_level.value}: fan-out regeneration forbidden"
        return None

    def admit(
        self,
        wave_id: str,
        verdict: AdmissionVerdict,
        selected: str,
        discarded: dict[str, str],
        gate_hashes: dict[str, str],
        spec_delta_ref: str,
        r_level: RLevel,
    ) -> EvidenceReceipt:
        self._wave(wave_id)
        if not verdict.admitted:
            raise AdmissionError(f"refusing admit: blocking gates {verdict.blocking_gates}")
        for record in self.staging[wave_id]:
            if record.instance_id == selected:
                record.status = "selected"
            elif record.instance_id in discarded:
                record.status = "discarded"
                record.measurement_note = discarded[record.instance_id]
                if not record.measurement_note.strip():
                    raise AdmissionError(
                        f"discarded instance {record.instance_id} without measurement note: "
                        "every discard must leave a conclusion about the spec"
                    )
        receipt = EvidenceReceipt(
            receipt_id=f"RCPT-{wave_id}-{selected}",
            wave_id=wave_id,
            spec_delta_ref=spec_delta_ref,
            r_level=r_level,
            selected_instance=selected,
            discarded_instances=sorted(discarded),
            gate_report_hashes=gate_hashes,
            judge_verdict=verdict.soft_verdict,
            drift_clean=verdict.hard_verdicts.get("H7") is Verdict.PASS,
            admitted=True,
        )
        self.ledger.append(receipt)
        self.wave_receipts.setdefault(wave_id, []).append(receipt.receipt_id)
        return receipt

    def commit(self, wave_id: str, commit_hash: str) -> AdmissionTransaction:
        wave = self._wave(wave_id)
        transaction = AdmissionTransaction(
            wave_id=wave_id,
            receipts=list(self.wave_receipts.get(wave_id, [])),
            committed=True,
            commit_hash=commit_hash,
        )
        wave.status = "committed"
        self.transactions[wave_id] = transaction
        return transaction

    def abort(self, wave_id: str, reason: str) -> AdmissionTransaction:
        wave = self._wave(wave_id)
        wave.status = "aborted"
        transaction = AdmissionTransaction(wave_id=wave_id, committed=False, compensated=True, rollback_reason=reason)
        self.transactions[wave_id] = transaction
        return transaction

    def _wave(self, wave_id: str) -> WaveManifest:
        if wave_id not in self.waves:
            raise AdmissionError(f"unknown wave {wave_id}")
        return self.waves[wave_id]
