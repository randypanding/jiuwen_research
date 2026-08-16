"""OpenJiuwen adapter: wiring map from ports to real agent-core APIs (WP14).

This module is import-guarded: openjiuwen is an optional heavy dependency.
The mapping below is normative (verified against pinned submodule commits,
see CAPABILITY_MAP.md and PLAN.md section 6). Execution teams implement
against these exact APIs; fakes in tests already lock the port contracts.
"""
from __future__ import annotations

from typing import Any

WIRING_NOTES = """
Port -> openJiuwen mapping (verified API surface):

BuilderPort.spawn
  - temporary team per wave: TeamAgentSpec(
        agents={"leader": DeepAgentSpec(...), "teammate": builder_spec},
        lifecycle="temporary",            # default; blueprint.py:209
        dispatch_mode="autonomous")       # members claim from shared board
  - activate: TeamRuntimeManager.activate(spec, session)  # runtime/manager.py:115
  - builder DeepAgentSpec: model=TeamModelConfig(RU-M tier),
        tools whitelist only (read/write/test/git), NO holdout/golden tools,
        memory read-only (MemberMemoryToolkit(read_only=True)),
        enable_skill_discovery=False, no evolution rails,
        context: session_id=wave, context_id=f"builder::{instance_id}"
  - seed: inject into spec_delta payload (builder has no RNG of its own)
  - finalize after round: TeamRuntimeManager.finalize()  # manager.py:176

VerifierPort.run_hard_gates / run_differential
  - deterministic Workflow (openjiuwen.core.workflow.Workflow):
        wf = Workflow()
        wf.set_start_comp("start", Start())
        for gate in H1..H8: wf.add_workflow_comp(gate, ToolComponent(cfg))
        wf.add_connection(["h1",...,"h8"], "join");  # fan-in
        wf.add_workflow_comp("join", Join, wait_for_all=True)
        wf.set_end_comp("end", End())
    each ToolComponent wraps `specforge gates run --json` via run_command
  - no LLM node on the hard path (D14: gates are never agent-discretionary)

ModeratorPort.route
  - persistent DeepAgent, context_id="spec_moderator" (ContextEngine isolation:
    openjiuwen.core.context_engine.context_engine.ContextEngine, context_engine.py:24)
  - session-frozen: attach no evolution rails

Judge (soft gates)
  - SubWorkflowComponent inside verifier workflow; model tier RU-H
  - independence & tier assertions: specforge.judge.assert_independence /
    assert_tier_ok executed at assembly time

MessengerPort
  - TeamTopic events: session:<sid>:team:<tname>:task|message (schema/events.py:24)
  - publish via messager.publish(topic_id=TeamTopic.TASK.build(...), ...)

Cartographer as tool
  - parent subagents=[SubAgentSpec(agent_card=AgentCard(name="cartographer"))]
    -> SubagentRail (priority 95) auto-mounts TaskTool (subagent_rail.py:28)

Constitution enforcement rails
  - BaseSecurityRail (priority 90) + AbortError for CRITICAL termination
  - H6 mapping: SecurityReject/AbortError, never prompt-level advice
"""


def _require_openjiuwen():
    try:
        import openjiuwen  # noqa: F401
    except ImportError as e:  # pragma: no cover - depends on env
        raise ImportError(
            "openjiuwen not installed; adapter requires agent-core. "
            "See WIRING_NOTES in this module and PLAN.md WP14."
        ) from e


class OpenJiuwenAdapter:
    """Production adapter (skeleton). Implement WP14 against WIRING_NOTES."""

    def __init__(self, *args: Any, **kw: Any):
        _require_openjiuwen()
        raise NotImplementedError(
            "WP14: implement per WIRING_NOTES; port contracts are locked by "
            "tests/test_swarm_orchestrator.py")
