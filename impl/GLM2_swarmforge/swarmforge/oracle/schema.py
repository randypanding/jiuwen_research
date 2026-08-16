"""Oracle 数据契约：holdout 场景、judge rubric、黄金输出 manifest、差分结论。

信息不对称（INV5）的物理基础：holdout 库只有 verifier 角色可读；
builder 只见 spec（L1/L2/L3）+ 接口面 + 本地可跑的自测（open 场景）。
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class ScenarioVisibility(str, Enum):
    OPEN = "open"        # builder 可见，用于自测
    HOLDOUT = "holdout"  # 仅 verifier 可见（场景集与 rubric 由 architect 持有）


@dataclass
class HoldoutScenario:
    """一个可执行验收场景（H3 的最小单元）。

    结构对齐 SWE-bench 双结构：failing_before（改造前应失败）与 passing_after
    （改造后应通过）共同构成 FAIL_TO_PASS 语义；regression_checks 构成
    PASS_TO_PASS 语义（不回归）。
    """
    scenario_id: str                  # SC-<domain>-<seq>
    domain: str
    visibility: ScenarioVisibility
    clause_ids: list[str]             # 该场景为哪些条款提供见证
    stimulus: dict                    # 输入（结构化，可序列化）
    expected: dict                    # 期望输出/后置条件（oracle 断言）
    regression_checks: list[str] = field(default_factory=list)  # 不得破坏的既有行为场景 id
    requires: str = "python>=3.11"    # 执行环境要求（M0 简化为标签）

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "HoldoutScenario":
        d = dict(d)
        d["visibility"] = ScenarioVisibility(d["visibility"])
        return cls(**d)

    def content_hash(self) -> str:
        blob = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()


@dataclass
class ScenarioResult:
    """单实例单场景的执行结果（verifier 产出，进入证据收据）。"""
    scenario_id: str
    instance_id: str
    outcome: str                       # pass | fail | error | timeout
    observed: dict = field(default_factory=dict)
    detail: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class JudgeRubric:
    """软门禁 S 的判据（architect 编写，verifier 以固定 workflow 执行）。

    judge 只输出 否决+理由 或 不否决，永不输出豁免硬门禁（INV4）。
    """
    rubric_id: str
    dimension: str                     # 单一维度（一个 rubric 只评一个维度）
    levels: dict[str, str]             # 档位 -> 可观察判别条件（如 veto/pass）
    evidence_required: bool = True     # 判词必须引用证据
    abstain_allowed: bool = True       # 允许弃权（三值判定）
    sample_count: int = 3              # 多次采样 + 多数决
    version: str = "1"                 # rubric 冻结版本（INV6：会话内不可变）

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "JudgeRubric":
        return cls(**d)


class JudgeVerdict(str, Enum):
    VETO = "veto"
    NO_VETO = "no_veto"
    ABSTAIN = "abstain"                # 弃权 → 升级人工/追加采样，永不默认通过


@dataclass
class JudgeOutput:
    """LLM-as-judge 的结构化输出协议。"""
    verdict: JudgeVerdict
    reasons: list[str] = field(default_factory=list)
    evidence_citations: list[str] = field(default_factory=list)  # 必须引用证据
    confidence: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "JudgeOutput":
        return cls(verdict=JudgeVerdict(d["verdict"]), reasons=list(d.get("reasons", [])),
                   evidence_citations=list(d.get("evidence_citations", [])),
                   confidence=float(d.get("confidence", 0.0)))


@dataclass
class GoldenManifest:
    """黄金输出锁定 manifest（R3 逐行敏感制品）。

    仿 Debian .buildinfo：完全决定再生物所需的全部环境指纹。
    CI 永不自动写黄金；更新只能人工触发并走评审（r3 研究结论）。
    """
    artifact_path: str
    code_hash: str
    deps_hash: str
    seed: int
    normalizer_config_hash: str
    golden_hash: str                    # 黄金输出文件自身的哈希
    approved_by: str = ""
    approval_reason: str = ""
    superseded: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "GoldenManifest":
        return cls(**d)


class DiffConclusion(str, Enum):
    """实例间差分的判定结论（H5 输出，六格判定的输入）。"""
    EQUIVALENT = "equivalent"            # 行为等价（在 oracle 与差分输入上）
    DIFFERENCE_FOUND = "difference_found"  # spec 沉默：未定义区被自由填充
    INCONCLUSIVE = "inconclusive"        # 非确定性未消除 → 统计通道/升级


@dataclass
class DifferentialReport:
    """一次差分测量的完整报告。"""
    wave_id: str
    spec_delta_id: str
    instance_ids: list[str]
    inputs_used: list[str] = field(default_factory=list)    # 差分输入 id
    fingerprints: dict[str, str] = field(default_factory=dict)  # instance_id -> 行为指纹
    conclusion: DiffConclusion = DiffConclusion.EQUIVALENT
    divergent_inputs: list[str] = field(default_factory=list)
    nondet_suspects: list[str] = field(default_factory=list)
    detail: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["conclusion"] = self.conclusion.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "DifferentialReport":
        d = dict(d)
        d["conclusion"] = DiffConclusion(d["conclusion"])
        return cls(**d)
