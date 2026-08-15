from __future__ import annotations

import dataclasses

from swarmfoundry.schema import SCHEMA_VERSION
from swarmfoundry.schema.base import (
    SchemaError,
    check_id,
    check_schema_version,
    require,
    require_list,
)

ORACLE_EXIT_CODE = "exit_code"
ORACLE_STDOUT_REGEX = "stdout_regex"
ORACLE_JSON_ASSERT = "json_assert"
ORACLE_GOLDEN_FILE = "golden_file"
ORACLE_PROPERTY_SCRIPT = "property_script"
ORACLE_KINDS = (
    ORACLE_EXIT_CODE,
    ORACLE_STDOUT_REGEX,
    ORACLE_JSON_ASSERT,
    ORACLE_GOLDEN_FILE,
    ORACLE_PROPERTY_SCRIPT,
)


@dataclasses.dataclass(frozen=True)
class Scenario:
    id: str
    kind: str
    input_file: str
    expected: str
    timeout_s: float = 30.0
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "input_file": self.input_file,
            "expected": self.expected,
            "timeout_s": self.timeout_s,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict, where: str) -> "Scenario":
        kind = require(data, "kind", str, where)
        if kind not in ORACLE_KINDS:
            raise SchemaError(f"{where}: oracle kind must be one of {ORACLE_KINDS}")
        return cls(
            id=check_id(require(data, "id", str, where), where),
            kind=kind,
            input_file=require(data, "input_file", str, where),
            expected=data.get("expected", ""),
            timeout_s=float(data.get("timeout_s", 30.0)),
            description=data.get("description", ""),
        )


@dataclasses.dataclass(frozen=True)
class ScenarioSuite:
    suite_id: str
    entrypoint: str
    scenarios: tuple[Scenario, ...]
    holdout: bool = False
    rotation_id: str = ""
    env_manifest: dict = dataclasses.field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "suite_id": self.suite_id,
            "entrypoint": self.entrypoint,
            "holdout": self.holdout,
            "rotation_id": self.rotation_id,
            "env_manifest": self.env_manifest,
            "scenarios": [s.to_dict() for s in self.scenarios],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScenarioSuite":
        where = "ScenarioSuite"
        check_schema_version(data, where)
        return cls(
            suite_id=check_id(require(data, "suite_id", str, where), where),
            entrypoint=require(data, "entrypoint", str, where),
            scenarios=tuple(
                Scenario.from_dict(s, f"{where}.scenarios[{i}]")
                for i, s in enumerate(require_list(data, "scenarios", where))
            ),
            holdout=bool(data.get("holdout", False)),
            rotation_id=data.get("rotation_id", ""),
            env_manifest=data.get("env_manifest", {}),
        )


@dataclasses.dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    passed: bool
    detail: str = ""
    duration_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "passed": self.passed,
            "detail": self.detail,
            "duration_ms": self.duration_ms,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScenarioResult":
        return cls(
            scenario_id=require(data, "scenario_id", str, "ScenarioResult"),
            passed=require(data, "passed", bool, "ScenarioResult"),
            detail=data.get("detail", ""),
            duration_ms=int(data.get("duration_ms", 0)),
        )
