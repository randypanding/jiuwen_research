"""事件总线：契约间通信 + 信息不对称的物理强制层。

- Topic 命名规范：`<域>.<对象>.<动作>`，支持 fnmatch 通配（与 openjiuwen
  TeamRuntime 的 subscription_manager 同语义：`*`/`?`）。
- 权限矩阵：deny-by-default。角色只能 publish/subscribe 矩阵声明的 topic。
  builder 永远拿不到 holdout.*/gate.*——这是 INV5 的机械执行，不是礼仪。
- 连线完整性检查：声明的 provides/consumes 必须闭合（悬空订阅/死信发布
  在装配期报错，不在运行期静默丢失）。
"""
from __future__ import annotations

import fnmatch
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

from ..constitution import ConstitutionViolation


# ---------------- Topic 命名规范 ----------------
# wave.*      波次生命周期（leader 发布）
# build.*     实例生成（builder 发布）
# verify.*    验证执行（verifier 发布）
# gate.*      门禁结果（verifier 发布）
# spec.*      spec 变更提案/落地（spec_moderator / spec_steward）
# measurement.* 测量结论（verifier/calibration 发布）
# admit.*     准入事务（leader 执行、全订阅）
# drift.*     漂移事件（reconciler 发布）
# oracle.*    判据补强提案（critic 发布）
# proposal.*  规则变更提案（deep_agent 发布，仅提案不生效）
# report.*    人类报告面（只含 L1/L2 事项与健康度）
# holdout.*   holdout 场景内容（仅判别侧；builder 不可见）

#: 角色 → 允许 publish 的 topic 模式列表
PUBLISH_MATRIX: dict[str, list[str]] = {
    "leader": ["wave.*", "admit.*", "report.*"],
    "architect": ["wave.plan", "rubric.*", "oracle.scenario.proposed"],
    "builder": ["build.*", "build.instance.*"],
    "verifier": ["verify.*", "gate.*", "measurement.diff.*", "measurement.scenario.*",
                 "measurement.*.classified", "measurement.classified"],
    "spec_moderator": ["spec.delta.proposed", "spec.dontcare.*", "report.*"],
    "spec_steward": ["spec.version.*", "report.*"],
    "reconciler": ["drift.*"],
    "cartographer": ["map.*"],
    "critic": ["oracle.*"],
    "refactor": ["refactor.*"],
    "moderator": ["wiki.*"],
    "deep_agent": ["proposal.*"],
    "calibration_leader": ["calibration.*", "measurement.*"],
    "human": ["approve.*", "constitution.*"],
    "ci": ["ci.*"],
}

#: 角色 → 允许 subscribe 的 topic 模式列表（信息不对称核心）
SUBSCRIBE_MATRIX: dict[str, list[str]] = {
    "leader": ["build.completed", "gate.*", "measurement.classified",
               "admit.*", "drift.*", "anomaly.*", "proposal.*"],
    "architect": ["spec.delta.proposed", "measurement.classified", "drift.*"],
    "builder": ["wave.assign.*", "spec.snapshot.*", "scenario.open.*"],
    "verifier": ["build.completed", "build.instance.*", "wave.sealed", "spec.snapshot.*"],
    "spec_moderator": ["measurement.classified", "gate.completed", "drift.*"],
    "spec_steward": ["spec.*", "drift.*"],
    "reconciler": ["world.*", "admit.committed", "spec.version.*"],
    "cartographer": ["ci.failure.*", "map.request.*"],
    "critic": ["admit.committed", "gate.completed", "spec.snapshot.*"],
    "refactor": ["admit.committed", "refactor.request.*"],
    "moderator": ["admit.committed"],
    "deep_agent": ["measurement.*", "drift.*", "anomaly.*", "report.*"],
    "calibration_leader": ["calibration.*", "spec.snapshot.*", "measurement.*"],
    "human": ["report.*", "proposal.*", "approve.request.*"],
    "ci": ["admit.requested"],
}

#: 判别侧专用 topic（builder 绝不可见：INV5）
VERIFIER_ONLY_TOPICS = ("holdout.*", "gate.*", "verify.*", "measurement.*", "rubric.*")


@dataclass
class Envelope:
    """总线消息信封。payload 必须可 JSON 序列化（跨进程兼容的物理基础）。"""
    topic: str
    type: str                     # 事件类型，如 wave.sealed / gate.completed
    sender_role: str
    payload: dict = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    ts: float = field(default_factory=time.time)
    wave_id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Envelope":
        return cls(**d)


def _matches(patterns: list[str], topic: str) -> bool:
    return any(fnmatch.fnmatch(topic, p) for p in patterns)


class BusPermissionError(ConstitutionViolation):
    """违反信息不对称协议（INV5）。"""

    def __init__(self, role: str, action: str, topic: str):
        self.role, self.action, self.topic = role, action, topic
        super().__init__(
            "INV5",
            f"role '{role}' is not permitted to {action} topic '{topic}'",
        )


# ---------------- 连线完整性 ----------------
@dataclass
class ContractDecl:
    """契约模块的总线声明：提供什么事件、消费什么事件。"""
    contract: str          # 模块名，如 "admission", "measurement"
    role: str              # 以什么角色上线
    provides: list[str]    # 发布的 topic（可含通配）
    consumes: list[str]    # 订阅的 topic（可含通配）


@dataclass
class WiringIssue:
    kind: str    # dangling_subscription | dead_letter | undeclared_role
    detail: str


def validate_wiring(decls: list[ContractDecl],
                    publish_matrix: Optional[dict] = None,
                    subscribe_matrix: Optional[dict] = None) -> list[WiringIssue]:
    """装配期连线检查：
    1. 每个被消费的 topic 至少有一个契约提供（否则订阅永远收不到——断链）
    2. 每个提供的 topic 至少被消费或属于显式白名单（否则死信）
    3. 声明的 role 必须在权限矩阵中
    """
    pub_m = publish_matrix or PUBLISH_MATRIX
    sub_m = subscribe_matrix or SUBSCRIBE_MATRIX
    issues: list[WiringIssue] = []

    for d in decls:
        if d.role not in pub_m:
            issues.append(WiringIssue("undeclared_role",
                                      f"contract {d.contract} uses unknown role {d.role}"))
            continue
        for t in d.provides:
            if not _matches(pub_m[d.role], t):
                issues.append(WiringIssue(
                    "permission_mismatch",
                    f"contract {d.contract} provides '{t}' beyond role {d.role} publish grants"))
        for t in d.consumes:
            if not _matches(sub_m.get(d.role, []), t):
                issues.append(WiringIssue(
                    "permission_mismatch",
                    f"contract {d.contract} consumes '{t}' beyond role {d.role} subscribe grants"))

    provided: set[str] = set()
    for d in decls:
        provided.update(d.provides)
    for d in decls:
        for t in d.consumes:
            if not any(fnmatch.fnmatch(p, t) for p in provided):
                issues.append(WiringIssue(
                    "dangling_subscription",
                    f"contract {d.contract} consumes '{t}' but no contract provides it"))
    return issues


# ---------------- InProcessBus ----------------
class InProcessBus:
    """进程内总线：权限强制 + 通配订阅 + 审计日志。

    与 openjiuwen core/multi_agent TeamRuntime 同构（fnmatch topic），
    bus/bridge.py 提供跨进程适配。deny-by-default。
    """

    def __init__(self, publish_matrix: Optional[dict] = None,
                 subscribe_matrix: Optional[dict] = None,
                 audit_path: Optional[str] = None):
        self.publish_matrix = publish_matrix or PUBLISH_MATRIX
        self.subscribe_matrix = subscribe_matrix or SUBSCRIBE_MATRIX
        self.audit_path = audit_path
        self._subs: dict[str, dict[str, Callable[[Envelope], None]]] = {}
        self._log: list[Envelope] = []

    def publish(self, env: Envelope) -> int:
        """发布。返回投递数。非法发布抛 BusPermissionError（INV5）。"""
        grants = self.publish_matrix.get(env.sender_role)
        if grants is None or not _matches(grants, env.topic):
            raise BusPermissionError(env.sender_role, "publish", env.topic)
        json.dumps(env.payload)  # payload 必须 JSON 可序列化
        self._log.append(env)
        delivered = 0
        for pattern, handlers in self._subs.items():
            if fnmatch.fnmatch(env.topic, pattern):
                for handler in list(handlers.values()):
                    handler(env)
                    delivered += 1
        self._audit(env, delivered)
        return delivered

    def subscribe(self, role: str, topic_pattern: str,
                  handler: Callable[[Envelope], None]) -> str:
        """订阅。非法订阅抛 BusPermissionError——builder 订阅 holdout.* 在此被物理拒绝。"""
        grants = self.subscribe_matrix.get(role)
        if grants is None or not _matches(grants, topic_pattern):
            raise BusPermissionError(role, "subscribe", topic_pattern)
        sub_id = uuid.uuid4().hex
        self._subs.setdefault(topic_pattern, {})[sub_id] = handler
        return sub_id

    def unsubscribe(self, sub_id: str) -> None:
        for pattern in list(self._subs):
            self._subs[pattern].pop(sub_id, None)
            if not self._subs[pattern]:
                del self._subs[pattern]

    def history(self, topic_pattern: str = "*") -> list[Envelope]:
        return [e for e in self._log if fnmatch.fnmatch(e.topic, topic_pattern)]

    def _audit(self, env: Envelope, delivered: int) -> None:
        if self.audit_path is None:
            return
        rec = {"event_id": env.event_id, "topic": env.topic, "type": env.type,
               "sender_role": env.sender_role, "delivered": delivered, "ts": env.ts}
        with open(self.audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
