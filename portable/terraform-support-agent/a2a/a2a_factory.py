"""
a2a_factory.py — A2A agent factory for the Terraform Support Agent.

Extends A2AAgentFactory from aicoe-agent-utils.

RULES (see docs/design/07-implementation-plan.md §2.3.4):
  - Do NOT call build_graph() — the framework handles it.
  - MCP tools are NOT wired in Phase 3b; override get_mcp_tools() in Phase 4.
"""
from __future__ import annotations

from typing import Any

from aicoe_agent_utils.a2a.agent_factory import A2AAgentFactory

import config
from terraform_agent import TerraformSupportAgent


class TerraformAgentFactory(A2AAgentFactory):
    """
    Factory that constructs the TerraformSupportAgent and its executor.

    Phase 3b: no MCP tools wired.
    Phase 4: override get_mcp_tools() once terraform-mcp.yaml is enabled.
    """

    def make_agent(self) -> TerraformSupportAgent:
        """Instantiate the coordinator agent with the configured LLM."""
        return TerraformSupportAgent(
            llm_provider=config.LLM_PROVIDER,
            # WatsonX kwargs — ignored when provider is ollama
            watsonx_url=config.WATSONX_URL,
            watsonx_apikey=config.WATSONX_APIKEY,
            watsonx_project_id=config.WATSONX_PROJECT_ID,
            watsonx_model_id=config.WATSONX_MODEL_ID,
            # Ollama kwargs — ignored when provider is watsonx
            ollama_base_url=config.OLLAMA_BASE_URL,
            ollama_model=config.OLLAMA_MODEL,
        )

    def make_agent_executor(self, agent: TerraformSupportAgent) -> Any:
        """
        Build the AgentExecutor.

        Phase 3b: no MCP tools; passes empty tool list.
        Phase 4: call self.get_mcp_tools() here after terraform-mcp.yaml is enabled.
        """
        return agent.create_executor(tools=[])
