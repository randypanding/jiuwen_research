from __future__ import annotations

import hashlib
from typing import Optional

from pydantic import Field, model_validator

from .base import ContractModel, RLevel, new_id, utc_now_iso
from .fanout import DiscardedInstance
from .gates import GateSuiteResult
from .oracle import JudgeVerdict


class DriftCheckSummary(ContractModel):
    contract_name: str = "DriftCheckSummary"
    stale: int = 0
    orphan: int = 0
    unimplemented: int = 0
    ok: int = 0

    @property
    def clean(self) -> bool:
        return self.stale == 0 and self.orphan == 0 and self.unimplemented == 0


class EvidenceReceipt(ContractModel):
    contract_name: str = "EvidenceReceipt"
    receipt_id: str = Field(default_factory=lambda: new_id("er"))
    wave_id: str
    delta_id: str
    r_level: RLevel
    chosen_instance_id: str
    discarded: list[DiscardedInstance] = Field(default_factory=list)
    gate_suite: GateSuiteResult
    judge_verdict: Optional[JudgeVerdict] = None
    diff_conclusion: str = ""
    drift_check: DriftCheckSummary = Field(default_factory=DriftCheckSummary)
    measurement_conclusion: str = ""
    prior_receipt_sha256: str = ""
    ts: str = Field(default_factory=utc_now_iso)

    def receipt_hash(self) -> str:
        return self.sha256()

    @property
    def complete(self) -> bool:
        return self.gate_suite.hard_pass and self.drift_check.clean


class AdmissionDecision(ContractModel):
    contract_name: str = "AdmissionDecision"
    transaction_id: str = Field(default_factory=lambda: new_id("tx"))
    admit: bool
    receipt_id: str
    reasons: list[str] = Field(default_factory=list)
    rollback_handle: str = ""
    ts: str = Field(default_factory=utc_now_iso)

    @model_validator(mode="after")
    def admission_algebra(self) -> "AdmissionDecision":
        return self


class LedgerEntry(ContractModel):
    contract_name: str = "LedgerEntry"
    transaction_id: str
    receipt_sha256: str
    instance_id: str
    target_path: str
    prior_entry_sha256: str = ""
    op: str = "commit"
    entry_sha256: str = ""
    ts: str = Field(default_factory=utc_now_iso)

    def seal(self, prior: str = "") -> "LedgerEntry":
        self.prior_entry_sha256 = prior
        self.entry_sha256 = ""
        self.entry_sha256 = self.sha256()
        return self
