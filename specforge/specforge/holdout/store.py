"""Private holdout scenario store with information asymmetry (WP6, D12).

Physical isolation:
  - scenarios live under holdout/<set>/scenarios.jsonl (0600 best effort)
  - canary GUIDs are embedded in scenario payloads; any leak in outbound
    artifacts is detectable via scan_canaries
  - evaluate() returns ONLY aggregate scores (never scenario content)
  - BuilderView exposes describe()/publish_notice() only — no read path
"""
from __future__ import annotations

import json
import os
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional


@dataclass
class HoldoutScenario:
    scenario_id: str
    set_id: str
    kind: str = "io"           # io | property | metamorphic
    weight: float = 1.0
    payload: dict[str, Any] = field(default_factory=dict)  # NEVER exposed to builders

    def to_dict(self) -> dict[str, Any]:
        return {"scenario_id": self.scenario_id, "set_id": self.set_id, "kind": self.kind,
                "weight": self.weight, "payload": self.payload}


@dataclass
class HoldoutScore:
    set_id: str
    aggregate: float
    passed: int
    total: int
    dimensions: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"set_id": self.set_id, "aggregate": self.aggregate,
                "passed": self.passed, "total": self.total, "dimensions": self.dimensions}


class HoldoutAccessError(PermissionError):
    pass


def new_canary() -> str:
    return f"JWHD-{secrets.token_hex(8).upper()}"


def scan_canaries(text: str, canaries: set[str]) -> list[str]:
    """Return canary GUIDs found in outbound text (leak detection)."""
    return [c for c in canaries if c in text]


class HoldoutStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.root, 0o700)
        except OSError:
            pass
        self.rotation_log: list[dict[str, Any]] = []
        self._log_path = self.root / "rotation.log"
        if self._log_path.exists():
            self.rotation_log = [json.loads(x) for x in
                                 self._log_path.read_text(encoding="utf-8").splitlines() if x.strip()]

    # ---- scenario management (verifier/steward side only) --------------------

    def add_scenario(self, sc: HoldoutScenario, canary: Optional[str] = None) -> str:
        canary = canary or new_canary()
        sc.payload["__canary__"] = canary
        p = self._set_dir(sc.set_id) / "scenarios.jsonl"
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(sc.to_dict(), ensure_ascii=False) + "\n")
        try:
            os.chmod(p, 0o600)
        except OSError:
            pass
        self._log({"event": "add", "set": sc.set_id, "scenario": sc.scenario_id, "at": time.time()})
        return canary

    def retire_scenario(self, set_id: str, scenario_id: str) -> None:
        p = self._set_dir(set_id) / "scenarios.jsonl"
        if not p.exists():
            return
        kept = []
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            if d["scenario_id"] != scenario_id:
                kept.append(line)
        p.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
        self._log({"event": "retire", "set": set_id, "scenario": scenario_id, "at": time.time()})

    def scenarios(self, set_id: str) -> list[HoldoutScenario]:
        p = self._set_dir(set_id) / "scenarios.jsonl"
        if not p.exists():
            return []
        out = []
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                out.append(HoldoutScenario(**{k: d.get(k) for k in
                                              ("scenario_id", "set_id", "kind", "weight", "payload")}))
        return out

    def canaries(self, set_id: Optional[str] = None) -> set[str]:
        out: set[str] = set()
        set_ids = [set_id] if set_id else [d.name for d in self.root.iterdir() if d.is_dir()]
        for s in set_ids:
            for sc in self.scenarios(s):
                c = sc.payload.get("__canary__")
                if c:
                    out.add(c)
        return out

    # ---- evaluation (aggregate only) ----------------------------------------

    def evaluate(
        self,
        instance_path: str,
        set_id: str,
        runner: Optional[Callable[[str, HoldoutScenario], bool]] = None,
    ) -> HoldoutScore:
        """runner(instance_path, scenario) -> passed bool. Default: payload['expect']
        matched against payload['input'] output by invoking payload['cmd'] protocol."""
        scenarios = self.scenarios(set_id)
        passed = 0
        dims: dict[str, float] = {}
        by_kind: dict[str, list[bool]] = {}
        for sc in scenarios:
            if runner is not None:
                ok = bool(runner(instance_path, sc))
            else:
                ok = self._default_runner(instance_path, sc)
            passed += int(ok)
            by_kind.setdefault(sc.kind, []).append(ok)
        for kind, results in by_kind.items():
            dims[kind] = sum(results) / len(results)
        total = len(scenarios)
        agg = passed / total if total else 0.0
        return HoldoutScore(set_id=set_id, aggregate=agg, passed=passed, total=total, dimensions=dims)

    def _default_runner(self, instance_path: str, sc: HoldoutScenario) -> bool:
        import subprocess

        cmd = sc.payload.get("cmd")
        inp = sc.payload.get("input")
        expect = sc.payload.get("expect")
        if not cmd or expect is None:
            return False
        env = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "LC_ALL", "TZ")}
        try:
            proc = subprocess.run(cmd, input=json.dumps(inp), cwd=instance_path, env=env,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  text=True, timeout=15)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
        try:
            got = json.loads(proc.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return False
        if isinstance(expect, dict) and isinstance(got, dict):
            return all(got.get(k) == v for k, v in expect.items())
        return got == expect

    # ---- misc ----------------------------------------------------------------

    def _set_dir(self, set_id: str) -> Path:
        d = self.root / set_id
        d.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(d, 0o700)
        except OSError:
            pass
        return d

    def _log(self, entry: dict[str, Any]) -> None:
        self.rotation_log.append(entry)
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
