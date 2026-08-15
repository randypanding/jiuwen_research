"""证据收据（EvidenceReceipt）与哈希链账本。

PR 的重定义：不是评审请求，而是准入事务 + 证据收据。
收据包含 spec-delta 引用、R 级、被选/被弃实例、H1-H8 结果、S 判词、
差分结论、漂移检查、成本。哈希链使账本防篡改（改任何一张收据即断链）。
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class EvidenceReceipt:
    receipt_id: str
    wave_id: str
    domain: str
    spec_delta_id: str
    spec_version_after: str = ""            # 准入后的契约哈希
    instance_id: str = ""                   # 被选择准入的实例（"" = 无一准入）
    discarded_instances: list[str] = field(default_factory=list)
    r_levels_touched: list[str] = field(default_factory=list)
    gate_run: dict = field(default_factory=dict)        # GateRunOutcome.to_dict()
    differential: dict = field(default_factory=dict)    # DifferentialReport.to_dict()
    measurement_class: str = ""             # 六格判定类别
    cost: dict = field(default_factory=dict)
    decided_by: str = "leader"
    human_involved: bool = False            # R2/R3 或 L2 变更时必须 True
    ts: float = field(default_factory=time.time)
    prev_receipt_hash: str = ""
    self_hash: str = ""                     # 内容哈希（不含 self_hash 自身）

    def content(self) -> dict:
        d = asdict(self)
        d.pop("self_hash")
        return d

    def compute_hash(self) -> str:
        blob = json.dumps(self.content(), ensure_ascii=False, sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "EvidenceReceipt":
        return cls(**d)


GENESIS = "0" * 64


class ReceiptLedger:
    """收据账本：append-only + 哈希链。

    verify_chain() 重算全链；任何历史收据被改动即验出断点位置。
    """

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def append(self, receipt: EvidenceReceipt) -> str:
        prev = self.tail_hash()
        receipt.prev_receipt_hash = prev
        receipt.self_hash = receipt.compute_hash()
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(receipt.to_dict(), ensure_ascii=False) + "\n")
        return receipt.self_hash

    def all(self) -> list[EvidenceReceipt]:
        if not os.path.exists(self.path):
            return []
        out = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    out.append(EvidenceReceipt.from_dict(json.loads(line)))
        return out

    def tail_hash(self) -> str:
        receipts = self.all()
        return receipts[-1].self_hash if receipts else GENESIS

    def verify_chain(self) -> Optional[int]:
        """返回首个断点索引（None = 完整）。检查：重算哈希 + prev 链接。"""
        prev = GENESIS
        for i, r in enumerate(self.all()):
            if r.prev_receipt_hash != prev:
                return i
            if r.compute_hash() != r.self_hash:
                return i
            prev = r.self_hash
        return None
