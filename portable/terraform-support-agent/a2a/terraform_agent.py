"""
terraform_agent.py — Terraform Support Agent implementation.

Extends BaseLangGraphAgent from aicoe-agent-utils.

RULES (see docs/design/07-implementation-plan.md §2.3.4):
  - Do NOT call build_graph() — the framework handles graph construction.
  - The coordinator system prompt is loaded from
    ../export/agents/coordinator.md at import time.
"""
from __future__ import annotations

import os
import pathlib
import re

from aicoe_agent_utils.agents.base_langgraph_agent import BaseLangGraphAgent


# ---------------------------------------------------------------------------
# Coordinator prompt — loaded once from the canonical agent definition file.
# YAML front matter (--- ... ---) is stripped before use.
# ---------------------------------------------------------------------------

_AGENT_DIR = pathlib.Path(__file__).parent.parent  # portable/terraform-support-agent/
_COORDINATOR_MD = _AGENT_DIR / "export" / "agents" / "coordinator.md"


def _load_coordinator_prompt() -> str:
    """Read coordinator.md and strip YAML front matter."""
    text = _COORDINATOR_MD.read_text(encoding="utf-8")
    # Strip --- ... --- front matter block if present
    stripped = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)
    return stripped.strip()


_COORDINATOR_PROMPT: str = _load_coordinator_prompt()


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class TerraformSupportAgent(BaseLangGraphAgent):
    """
    Terraform support case coordinator.

    Wraps the coordinator skill set defined in export/agents/coordinator.md
    and exposes it as an A2A-compatible LangGraph agent.
    """

    def get_prompt(self) -> str:
        """Return the coordinator system prompt."""
        return _COORDINATOR_PROMPT

    def get_agent_card(self) -> dict:
        """Return the A2A agent card metadata."""
        return {
            "name": "terraform-support-agent",
            "description": (
                "Terraform Cloud / HCP Terraform / TFE support case coordinator. "
                "Accepts case evidence, classifies scope, investigates using approved "
                "sources, and drafts operator-ready responses. "
                "All external actions require explicit operator approval."
            ),
            "skills": [
                "case-intake",
                "redaction",
                "scope-classification",
                "log-diagnosis",
                "hcl-analysis",
                "source-check",
                "communication-draft",
                "registry-routing",
                "reproduction-planning",
                "memory-curation",
            ],
            "version": "0.1.0-draft",
            "phase": "3b",
        }

    def get_looking_up_info_msg(self) -> str:
        return "Reviewing case evidence and approved sources…"

    def get_processing_info_msg(self) -> str:
        return "Analyzing and preparing coordinator output…"
