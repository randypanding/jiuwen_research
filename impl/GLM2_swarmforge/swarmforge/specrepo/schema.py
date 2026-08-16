"""Spec 数据契约：条款、见证绑定、Don't-Care 区、SpecDelta。

范式约束（INV3）：每条 L1/L2 条款必须绑定 >=1 机械见证（gate 引用或 holdout 场景），
否则 status=unverifiable，只能作为 advisory 参与软门禁，不得作为放行依据。
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class ClauseLayer(str, Enum):
    L1 = "L1"  # 业务意图：人类定义、人类批准
    L2 = "L2"  # 开发契约：人类看 diff、可否决
    L3 = "L3"  # 实现说明：机器所有，人类不看不批


class WitnessKind(str, Enum):
    GATE = "gate"          # 硬门禁 H1-H8 中某门的机械见证
    HOLDOUT = "holdout"    # 场景 holdout 套件中的场景
    PROPERTY = "property"  # 属性/不变量测试（H2 的属性面）


@dataclass(frozen=True)
class WitnessRef:
    """条款到机械见证的绑定。没有见证的条款不得放行（INV3）。"""
    kind: WitnessKind
    ref: str  # gate id 如 "H2"、场景 id 如 "SC-pay-0007"、属性 id

    def to_dict(self) -> dict:
        return {"kind": self.kind.value, "ref": self.ref}

    @classmethod
    def from_dict(cls, d: dict) -> "WitnessRef":
        return cls(kind=WitnessKind(d["kind"]), ref=d["ref"])


class ClauseStatus(str, Enum):
    BOUND = "bound"              # 有机械见证，可参与放行
    UNVERIFIABLE = "unverifiable"  # 无机械见证，仅 advisory（只能否决）
    DEPRECATED = "deprecated"    # 已弃用（须给出后继条款）


@dataclass
class SpecClause:
    clause_id: str                 # 稳定 ID：REQ-*（L1）/ CON-*（L2）/ IMP-*（L3）
    layer: ClauseLayer
    text: str
    witnesses: list[WitnessRef] = field(default_factory=list)
    anchors: list[str] = field(default_factory=list)  # 声明覆盖的代码路径（glob），供 H7 漂移检测
    supersedes: Optional[str] = None                 # 被本条款取代的条款 id
    rationale: str = ""                              # 条款存在理由（回溯 L1 用）

    @property
    def status(self) -> ClauseStatus:
        if self.witnesses:
            return ClauseStatus.BOUND
        return ClauseStatus.UNVERIFIABLE

    def to_dict(self) -> dict:
        return {
            "clause_id": self.clause_id,
            "layer": self.layer.value,
            "text": self.text,
            "witnesses": [w.to_dict() for w in self.witnesses],
            "anchors": list(self.anchors),
            "supersedes": self.supersedes,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SpecClause":
        return cls(
            clause_id=d["clause_id"],
            layer=ClauseLayer(d["layer"]),
            text=d["text"],
            witnesses=[WitnessRef.from_dict(w) for w in d.get("witnesses", [])],
            anchors=list(d.get("anchors", [])),
            supersedes=d.get("supersedes"),
            rationale=d.get("rationale", ""),
        )


@dataclass
class DontCareEntry:
    """显式自由度登记：差异落在该区 = 合法非确定性，不算 spec 沉默缺陷（INV9）。"""
    entry_id: str
    clause_id: str                 # 所属条款
    dimension: str                 # 自由维度的可观察描述（如 "日志文案" / "内部迭代顺序"）
    origin: str = "measured"       # measured(差分测量登记) | harvested(收割登记) | designed(初始设计)
    evidence_ref: str = ""         # measured 时必填：测量事件 id
    recorded_by: str = "spec_moderator"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "DontCareEntry":
        return cls(**d)


@dataclass
class SpecDocument:
    """一个域的规范三层。真值唯一载体。"""
    domain: str                        # 域名，如 "payment"
    intent: str = ""                   # L1 摘要（全文在 L1.md，人类所有）
    clauses: list[SpecClause] = field(default_factory=list)
    dont_cares: list[DontCareEntry] = field(default_factory=list)

    def clause(self, clause_id: str) -> Optional[SpecClause]:
        for c in self.clauses:
            if c.clause_id == clause_id:
                return c
        return None

    def l2_clauses(self) -> list[SpecClause]:
        return [c for c in self.clauses if c.layer == ClauseLayer.L2]

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "intent": self.intent,
            "clauses": [c.to_dict() for c in self.clauses],
            "dont_cares": [d.to_dict() for d in self.dont_cares],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SpecDocument":
        return cls(
            domain=d["domain"],
            intent=d.get("intent", ""),
            clauses=[SpecClause.from_dict(c) for c in d.get("clauses", [])],
            dont_cares=[DontCareEntry.from_dict(x) for x in d.get("dont_cares", [])],
        )

    def contract_hash(self) -> str:
        """行为契约哈希（H7-J1）：仅 L2 bound 条款的规范化哈希。
        文案润色（L1/L3 变化）不触发；契约变化才标 stale。"""
        payload = sorted(
            (c.clause_id, c.text, tuple(sorted(w.to_dict()["ref"] for w in c.witnesses)))
            for c in self.l2_clauses()
        )
        blob = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def bound_clause_ratio(self) -> float:
        """判据覆盖率分子/分母：bound L1+L2 条款占比（健康度指标）。"""
        target = [c for c in self.clauses if c.layer in (ClauseLayer.L1, ClauseLayer.L2)]
        if not target:
            return 0.0
        bound = [c for c in target if c.status.value == "bound"]
        return len(bound) / len(target)


@dataclass
class SpecDelta:
    """一次波次要落地的规范变更割集。波次 = 接口冻结窗口 + spec-delta + 准入事务边界。"""
    delta_id: str
    wave_id: str
    base_version: str                       # 基于的 spec 版本（契约哈希）
    clauses_added: list[SpecClause] = field(default_factory=list)
    clauses_modified: list[SpecClause] = field(default_factory=list)
    clauses_removed: list[str] = field(default_factory=list)
    dont_cares_added: list[DontCareEntry] = field(default_factory=list)
    motivation: str = ""                    # 为何变更（回溯 L1）

    def to_dict(self) -> dict:
        return {
            "delta_id": self.delta_id,
            "wave_id": self.wave_id,
            "base_version": self.base_version,
            "clauses_added": [c.to_dict() for c in self.clauses_added],
            "clauses_modified": [c.to_dict() for c in self.clauses_modified],
            "clauses_removed": list(self.clauses_removed),
            "dont_cares_added": [d.to_dict() for d in self.dont_cares_added],
            "motivation": self.motivation,
        }


def validate_delta_solvency(delta: SpecDelta, doc: SpecDocument) -> list[str]:
    """校验 spec-delta 的条款可实现性约束（准入前的 spec 侧自检）。

    返回问题清单（空 = 通过）：
    - 新增/修改的 L1/L2 条款无见证 → 允许存在但标记 unverifiable（不阻断 spec 写入，
      阻断的是"以该条款为由的放行"——那由门禁代数在准入时检查）。
    - 移除 bound 条款但存在锚定它的 R1/R2 制品 → 必须给出演化策略（golden/adapt）。
    """
    problems: list[str] = []
    removed = set(delta.clauses_removed)
    for cid in removed:
        c = doc.clause(cid)
        if c is not None and c.layer == ClauseLayer.L2 and c.status.value == "bound":
            problems.append(
                f"removed bound L2 clause {cid}: requires evolution strategy for anchored artifacts"
            )
    for c in delta.clauses_added + delta.clauses_modified:
        if c.layer in (ClauseLayer.L1, ClauseLayer.L2) and not c.witnesses:
            problems.append(f"clause {c.clause_id} has no mechanical witness -> advisory only")
    return problems
