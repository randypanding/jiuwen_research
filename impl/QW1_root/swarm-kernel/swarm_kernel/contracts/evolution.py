from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from .base import ContractModel, Role, new_id, utc_now_iso


class ProposalStatus(str, Enum):
    DRAFT = "draft"
    HUMAN_APPROVED = "human_approved"
    EFFECTIVE_NEXT_SESSION = "effective_next_session"
    REJECTED = "rejected"


class RuleProposal(ContractModel):
    contract_name: str = "RuleProposal"
    proposal_id: str = Field(default_factory=lambda: new_id("rp"))
    case_refs: list[str] = Field(default_factory=list)
    rule_text: str
    scope: str = "constitution"
    proposer: Role = Role.DEEP_AGENT
    status: ProposalStatus = ProposalStatus.DRAFT
    effective_session: str = ""
    ts: str = Field(default_factory=utc_now_iso)

    @model_validator(mode="after")
    def no_immediate_effect(self) -> "RuleProposal":
        if self.status == ProposalStatus.EFFECTIVE_NEXT_SESSION and not self.effective_session:
            raise ValueError("effective_session required when proposal takes effect")
        return self

    @property
    def may_apply_current_session(self) -> bool:
        return False
