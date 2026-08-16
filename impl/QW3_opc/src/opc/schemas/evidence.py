from __future__ import annotations

from datetime import datetime, timezone

from pydantic import Field, field_validator

from opc.schemas.common import BaseSchema, RLevel, Verdict, content_hash


class EvidenceReceipt(BaseSchema):
    """The admission evidence receipt: the PR of this paradigm.

    It is NOT a review request. It is an atomic, auditable record that a
    single instance crossed the admit() boundary, carrying the full proof
    chain: which spec-delta, which R-level, which instance was selected,
    which were discarded and why, and the hash of every gate report.
    """

    receipt_id: str
    wave_id: str
    spec_delta_ref: str = Field(description="git commit sha or spec version the instance was derived from")
    r_level: RLevel
    selected_instance: str
    discarded_instances: list[str] = Field(default_factory=list)
    gate_report_hashes: dict[str, str] = Field(default_factory=dict)
    judge_verdict: Verdict = Verdict.INCONCLUSIVE
    diff_verdict: Verdict = Verdict.INCONCLUSIVE
    drift_clean: bool = False
    admitted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("receipt_id")
    @classmethod
    def _rid(cls, v: str) -> str:
        if not v.startswith("RCPT-"):
            raise ValueError("receipt_id must start with 'RCPT-'")
        return v

    def digest(self) -> str:
        return content_hash(self)


class LedgerEntry(BaseSchema):
    """A single hash-chained entry in the admission ledger.

    Each entry commits to the previous entry's digest, forming a tamper-
    evident chain. Any silent edit of history breaks verification.
    """

    seq: int
    receipt_digest: str
    prev_digest: str
    chain_digest: str = ""

    @classmethod
    def genesis(cls) -> str:
        return "sha256:" + "0" * 64
