"""HoldoutStore：场景库与信息不对称的物理层。

open 场景与 holdout 场景分目录存放；holdout 读取需要 verifier 角色声明，
每次读取写审计日志（谁、何时、读了什么）。builder 拿不到 holdout 的内容
——这是消除 reward-hacking 信息前提的机械执行（INV5）。
"""
from __future__ import annotations

import json
import os
import time
from typing import Optional

from .schema import HoldoutScenario, ScenarioVisibility


class HoldoutAccessDenied(Exception):
    """非 verifier 角色尝试读取 holdout 场景（宪法 INV5 违例）。"""

    def __init__(self, role: str):
        self.role = role
        super().__init__(f"role '{role}' is not allowed to read holdout scenarios")


READER_ROLES = frozenset({"verifier", "architect", "human", "calibration_leader"})


class HoldoutStore:
    def __init__(self, root: str):
        self.root = root
        self.open_dir = os.path.join(root, "open")
        self.holdout_dir = os.path.join(root, "holdout")
        self.audit_path = os.path.join(root, "access_audit.jsonl")
        os.makedirs(self.open_dir, exist_ok=True)
        os.makedirs(self.holdout_dir, exist_ok=True)

    def _path(self, visibility: ScenarioVisibility, scenario_id: str) -> str:
        base = self.open_dir if visibility == ScenarioVisibility.OPEN else self.holdout_dir
        return os.path.join(base, f"{scenario_id}.json")

    def put(self, scenario: HoldoutScenario) -> None:
        path = self._path(scenario.visibility, scenario.scenario_id)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(scenario.to_dict(), f, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(tmp, path)

    def get(self, scenario_id: str, reader_role: str) -> HoldoutScenario:
        """按角色读取。holdout 场景仅 READER_ROLES 可读，且强制审计。"""
        for vis in (ScenarioVisibility.OPEN, ScenarioVisibility.HOLDOUT):
            path = self._path(vis, scenario_id)
            if os.path.exists(path):
                if vis == ScenarioVisibility.HOLDOUT and reader_role not in READER_ROLES:
                    # 审计拒绝尝试（信息不对称的取证面）
                    self._audit(reader_role, scenario_id, allowed=False)
                    raise HoldoutAccessDenied(reader_role)
                with open(path, encoding="utf-8") as f:
                    d = json.load(f)
                if d["visibility"] == ScenarioVisibility.HOLDOUT.value:
                    self._audit(reader_role, scenario_id, allowed=True)
                return HoldoutScenario.from_dict(d)
        raise FileNotFoundError(f"scenario {scenario_id} not found")

    def list_ids(self, visibility: ScenarioVisibility, reader_role: str) -> list[str]:
        base = self.open_dir if visibility == ScenarioVisibility.OPEN else self.holdout_dir
        if visibility == ScenarioVisibility.HOLDOUT and reader_role not in READER_ROLES:
            self._audit(reader_role, "__list_holdout__", allowed=False)
            raise HoldoutAccessDenied(reader_role)
        return sorted(
            name[:-5] for name in os.listdir(base) if name.endswith(".json")
        )

    def witnesses_for(self, clause_id: str, reader_role: str = "verifier") -> list[HoldoutScenario]:
        """列出为某条款提供见证的全部场景（含 holdout——仅判别侧可调用）。"""
        out = []
        for vis in (ScenarioVisibility.OPEN, ScenarioVisibility.HOLDOUT):
            for sid in self.list_ids(vis, reader_role):
                sc = self.get(sid, reader_role)
                if clause_id in sc.clause_ids:
                    out.append(sc)
        return out

    def _audit(self, role: str, scenario_id: str, allowed: bool) -> None:
        rec = {"ts": time.time(), "role": role, "scenario_id": scenario_id,
               "allowed": allowed}
        with open(self.audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def audit_tail(self, n: int = 50) -> list[dict]:
        if not os.path.exists(self.audit_path):
            return []
        with open(self.audit_path, encoding="utf-8") as f:
            lines = [ln for ln in f if ln.strip()]
        return [json.loads(ln) for ln in lines[-n:]]
