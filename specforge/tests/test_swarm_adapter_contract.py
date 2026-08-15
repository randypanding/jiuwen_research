"""WP14 contract: WIRING_NOTES map must hold against the pinned agent-core tree.

The adapter is the ONLY place where specforge touches openjiuwen APIs. These
tests lock that mapping to the actual submodule code so a submodule bump that
breaks the wiring fails CI here (contract-communication test, not a unit test).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from specforge.swarm.openjiuwen_adapter import WIRING_NOTES, OpenJiuwenAdapter

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_CORE = REPO_ROOT / "agent-core" / "openjiuwen"

pytestmark = pytest.mark.skipif(
    not AGENT_CORE.exists(), reason="agent-core submodule not checked out")


def classes_in(rel: str) -> set[str]:
    """Top-level + nested class names declared in a module file."""
    tree = ast.parse((AGENT_CORE / rel).read_text(encoding="utf-8"))
    return {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}


def functions_in(rel: str) -> set[str]:
    tree = ast.parse((AGENT_CORE / rel).read_text(encoding="utf-8"))
    return {n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def source_of(rel: str) -> str:
    return (AGENT_CORE / rel).read_text(encoding="utf-8")


# ---- BuilderPort.spawn wiring ----------------------------------------------

def test_team_agent_spec_exists_with_lifecycle_default():
    src = source_of("agent_teams/schema/blueprint.py")
    assert "class TeamAgentSpec" in src
    # WIRING_NOTES: lifecycle="temporary" is the default (blueprint.py:209)
    assert 'lifecycle: str = TeamLifecycle.TEMPORARY' in src
    # dispatch_mode="autonomous" default (shared board claiming)
    assert 'dispatch_mode: Literal["autonomous", "scheduled"] = "autonomous"' in src


def test_team_runtime_manager_activate_finalize():
    fns = functions_in("agent_teams/runtime/manager.py")
    assert {"activate", "finalize"} <= fns, "activate/finalize are the wave lifecycle hooks"


def test_deep_agent_spec_and_tier_config():
    names = classes_in("harness/schema/deep_agent_spec.py")
    assert {"DeepAgentSpec", "TeamModelConfig", "SubAgentSpec"} <= names


def test_member_memory_toolkit_readonly_flag():
    src = source_of("agent_teams/memory/member_memory_toolkit.py")
    assert "class MemberMemoryToolkit" in src
    assert "read_only" in src, "builder memory must be mountable read-only"


# ---- VerifierPort wiring -----------------------------------------------------

def test_workflow_engine_exists():
    names = classes_in("core/workflow/workflow.py")
    assert "Workflow" in names
    src = source_of("core/workflow/workflow.py")
    for method in ("set_start_comp", "add_workflow_comp", "add_connection", "set_end_comp"):
        assert method in src, f"Workflow.{method} required by verifier fan-in graph"


# ---- ModeratorPort wiring ----------------------------------------------------

def test_context_engine_isolation_surface():
    names = classes_in("core/context_engine/context_engine.py")
    assert "ContextEngine" in names, "moderator context isolation depends on ContextEngine"


# ---- MessengerPort wiring ----------------------------------------------------

def test_team_topic_event_schema():
    src = source_of("agent_teams/schema/events.py")
    assert "class TeamTopic" in src
    for t in ("TASK", "MESSAGE"):
        assert t in src, f"TeamTopic.{t} required for wave message bus"


# ---- Rails wiring -------------------------------------------------------------

def test_subagent_rail_priority_for_cartographer():
    src = source_of("harness/rails/subagent/subagent_rail.py")
    assert "class SubagentRail" in src
    assert "priority = 95" in src


def test_base_security_rail_priority():
    src = source_of("harness/rails/security/base_security_rail.py")
    assert "class BaseSecurityRail" in src
    assert "priority: int = 90" in src


def test_agent_card_for_subagent_spec():
    names = classes_in("core/single_agent/schema/agent_card.py")
    assert "AgentCard" in names


# ---- adapter behaviour --------------------------------------------------------

def test_adapter_refuses_without_openjiuwen(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def no_oj(name, *a, **kw):
        if name.startswith("openjiuwen"):
            raise ImportError(name)
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", no_oj)
    with pytest.raises(ImportError):
        OpenJiuwenAdapter()


def test_wiring_notes_are_substantive():
    for anchor in ("TeamRuntimeManager.activate", "TeamTopic", "SubagentRail",
                   "BaseSecurityRail", "MemberMemoryToolkit", "ContextEngine"):
        assert anchor in WIRING_NOTES
