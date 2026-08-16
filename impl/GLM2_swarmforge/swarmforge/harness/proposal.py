"""规则变更提案通道（deep agent → 人类批准 → 新 session 生效）。

INV6/INV8：判别侧与判据 session 内冻结；例外与演进只能走提案。
提案在当前 session 内 pending，不生效；effective_from_session 必须晚于
提交 session —— 机械校验。
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Optional

from ..constitution import ConstitutionViolation


class ProposalError(Exception):
    pass


@dataclass
class RuleChangeProposal:
    proposal_id: str
    kind: str                 # tier_policy | gate_threshold | rubric | constitution | harness
    summary: str
    rationale: str = ""
    evidence_refs: list[str] = field(default_factory=list)  # 案例/测量结论引用
    submitted_in_session: str = ""
    effective_from_session: str = ""   # 必须是后续 session
    status: str = "pending"            # pending | approved | rejected | expired
    decided_by: str = ""               # human
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "RuleChangeProposal":
        return cls(**d)


class ProposalBook:
    """提案登记簿：append-only；批准不等于生效——生效在新 session 装载时。"""

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def submit(self, p: RuleChangeProposal, current_session: str) -> str:
        p.submitted_in_session = current_session
        if p.effective_from_session and p.effective_from_session <= current_session:
            raise ConstitutionViolation(
                "INV6",
                f"proposal {p.proposal_id} attempts to take effect within session "
                f"'{current_session}' (effective_from={p.effective_from_session})",
            )
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(p.to_dict(), ensure_ascii=False) + "\n")
        return p.proposal_id

    def all(self) -> list[RuleChangeProposal]:
        if not os.path.exists(self.path):
            return []
        out = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    out.append(RuleChangeProposal.from_dict(json.loads(line)))
        return out

    def decide(self, proposal_id: str, approved: bool, decided_by: str = "human") -> None:
        """批准/否决：重写登记簿对应条目（人类动作，留 decided_by）。"""
        props = self.all()
        found = False
        for p in props:
            if p.proposal_id == proposal_id:
                p.status = "approved" if approved else "rejected"
                p.decided_by = decided_by
                found = True
        if not found:
            raise ProposalError(f"unknown proposal {proposal_id}")
        with open(self.path, "w", encoding="utf-8") as f:
            for p in props:
                f.write(json.dumps(p.to_dict(), ensure_ascii=False) + "\n")

    def effective_for(self, session_id: str) -> list[RuleChangeProposal]:
        """给定 session 应装载的已批准提案（生效条件满足）。"""
        return [
            p for p in self.all()
            if p.status == "approved" and p.effective_from_session
            and p.effective_from_session <= session_id
            and session_id > p.submitted_in_session
        ]
