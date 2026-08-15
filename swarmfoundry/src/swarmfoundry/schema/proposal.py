from __future__ import annotations

import dataclasses

from swarmfoundry.schema import SCHEMA_VERSION
from swarmfoundry.schema.base import (
    SchemaError,
    check_id,
    check_schema_version,
    require,
)

KIND_MODEL_TIER = "model_tier"
KIND_R_LEVEL_CHANGE = "r_level_change"
KIND_RULE_CHANGE = "rule_change"
KIND_HARNESS_OPTIMIZATION = "harness_optimization"
PROPOSAL_KINDS = (KIND_MODEL_TIER, KIND_R_LEVEL_CHANGE, KIND_RULE_CHANGE, KIND_HARNESS_OPTIMIZATION)

STATUS_DRAFT = "draft"
STATUS_SUBMITTED = "submitted"
STATUS_HUMAN_APPROVED = "human_approved"
STATUS_REJECTED = "rejected"
PROPOSAL_STATUSES = (STATUS_DRAFT, STATUS_SUBMITTED, STATUS_HUMAN_APPROVED, STATUS_REJECTED)


@dataclasses.dataclass(frozen=True)
class RuleProposal:
    """Contract C13: deep-agent proposal channel. Proposals never take effect
    within the current session; effect requires human approval + next session."""

    proposal_id: str
    kind: str
    content: str
    rationale: str
    status: str = STATUS_DRAFT
    effective_session: str = ""
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "proposal_id": self.proposal_id,
            "kind": self.kind,
            "content": self.content,
            "rationale": self.rationale,
            "status": self.status,
            "effective_session": self.effective_session,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RuleProposal":
        where = "RuleProposal"
        check_schema_version(data, where)
        kind = require(data, "kind", str, where)
        if kind not in PROPOSAL_KINDS:
            raise SchemaError(f"{where}: kind must be one of {PROPOSAL_KINDS}")
        status = data.get("status", STATUS_DRAFT)
        if status not in PROPOSAL_STATUSES:
            raise SchemaError(f"{where}: status must be one of {PROPOSAL_STATUSES}")
        return cls(
            proposal_id=check_id(require(data, "proposal_id", str, where), where),
            kind=kind,
            content=require(data, "content", str, where),
            rationale=require(data, "rationale", str, where),
            status=status,
            effective_session=data.get("effective_session", ""),
        )

    def may_apply(self, current_session: str) -> bool:
        return self.status == STATUS_HUMAN_APPROVED and self.effective_session == current_session
