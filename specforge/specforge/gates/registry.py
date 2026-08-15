"""Gate registry: H1..H8 + default suite assembly."""
from __future__ import annotations

from .base import Gate, GateContext, SuiteResult, run_suite
from .h1_build import H1BuildGate
from .h2_tests import H2TestsGate
from .h3_holdout import H3HoldoutGate
from .h4_contract import H4ContractGate
from .h5_difftest import H5DifftestGate
from .h6_guardrail import H6GuardrailGate
from .h7_drift import H7DriftGate
from .h8_budget import H8BudgetGate


def default_hard_gates(**cfg) -> list[Gate]:
    return [
        H1BuildGate(commands=cfg.get("h1_commands")),
        H2TestsGate(
            mutation_score_threshold=cfg.get("mutation_threshold", 0.7),
            enable_mutation=cfg.get("enable_mutation", True),
            max_mutants=cfg.get("max_mutants", 6),
        ),
        H3HoldoutGate(score_threshold=cfg.get("h3_threshold", 0.8),
                      min_scenarios=cfg.get("h3_min", 5)),
        H4ContractGate(),
        H5DifftestGate(),
        H6GuardrailGate(dependency_allowlist=cfg.get("dependency_allowlist")),
        H7DriftGate(min_coverage=cfg.get("h7_coverage", 0.8)),
        H8BudgetGate(),
    ]


GATE_IDS = ["h1", "h2", "h3", "h4", "h5", "h6", "h7", "h8"]


def run_hard_suite(ctx: GateContext, cfg: dict | None = None, fail_fast: bool = False) -> SuiteResult:
    return run_suite(ctx, default_hard_gates(**(cfg or {})), fail_fast=fail_fast)


__all__ = [
    "Gate", "GateContext", "SuiteResult", "run_suite", "run_hard_suite",
    "default_hard_gates", "GATE_IDS",
    "H1BuildGate", "H2TestsGate", "H3HoldoutGate", "H4ContractGate",
    "H5DifftestGate", "H6GuardrailGate", "H7DriftGate", "H8BudgetGate",
]
