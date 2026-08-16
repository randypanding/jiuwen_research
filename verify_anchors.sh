#!/usr/bin/env bash
# Verify plan-cited openJiuwen anchors against pinned submodule commits via raw.githubusercontent.com
AC=73cfc3bc8b74386c5d91c6d1ff11f50e6df510df
JS=fc110aafb954aa6d99c886dc8f4e4fdf71973885
ACB="https://raw.githubusercontent.com/openJiuwen-ai/agent-core/$AC"
JSURL=$(cd /workspace/jiuwen_research && git config -f .gitmodules submodule.jiuwenswarm.url)
JSB="https://raw.githubusercontent.com/${JSURL#https://github.com/}/$JS"

check() { # repo_base file lineno label
  local base=$1 file=$2 ln=$3 label=$4
  local out
  out=$(timeout 15 curl -s "$base/$file" | sed -n "${ln}p")
  if [ -z "$out" ]; then echo "[$label] $file:$ln => <EMPTY/404>"; else
    echo "[$label] $file:$ln => $(echo "$out" | sed 's/^ *//' | cut -c1-90)"
  fi
}

echo "== agent-core @ $AC =="
check $ACB openjiuwen/core/multi_agent/team_runtime/team_runtime.py 55 K3-register
check $ACB openjiuwen/core/multi_agent/team_runtime/team_runtime.py 163 K3-send
check $ACB openjiuwen/harness/factory.py 454 GLM1/QW2/QW3-create_deep_agent
check $ACB openjiuwen/core/workflow/workflow.py 98 GLM1/K3-Workflow
check $ACB openjiuwen/agent_teams/runtime/manager.py 115 GLM1-TeamRuntimeManager
check $ACB openjiuwen/agent_teams/schema/blueprint.py 209 GLM2-TeamAgentSpec
check $ACB openjiuwen/agent_teams/schema/blueprint.py 198 QW3-TeamAgentSpec
check $ACB openjiuwen/core/session/checkpointer/checkpointer.py 60 K3-CheckpointerFactory
check $ACB openjiuwen/core/single_agent/rail/base.py 672 K3-AgentRail-hooks
check $ACB openjiuwen/core/security/guardrail/guardrail.py 377 K3-guardrail
check $ACB openjiuwen/agent_teams/memory/extractor.py 48 K3/QW2-extractor
check $ACB openjiuwen/core/context_engine/schema/config.py 60 K3/QW3-ContextEngineConfig
check $ACB openjiuwen/core/foundation/llm/model_clients/intelli_router_model_client.py 96 K3-IntelliRouter
check $ACB openjiuwen/harness/rails/evolution/skill_evolution_rail.py 141 K3-SkillEvolutionRail
check $ACB openjiuwen/agent_teams/tools/tool_task.py 225 K3-task-tools
check $ACB openjiuwen/core/application/workflow_agent/workflow_agent.py 11 K3-WorkflowAgent

echo; echo "== jiuwenswarm @ $JS ($JSB) =="
check "$JSB" jiuwenswarm/agents/harness/team/config_loader.py 550 QW2-config_loader
check "$JSB" jiuwenswarm/agents/harness/team/team_manager.py 1124 QW3-team_manager
check "$JSB" jiuwenswarm/agents/swarm/providers/evolution_rails.py 1 GLM2-evolution_rails
