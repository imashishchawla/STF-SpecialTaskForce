"""
config.py — Environment-variable configuration for the Terraform Support A2A server.

All secrets and runtime settings are loaded from environment variables.
Use .env.example as a template; copy to .env and fill in values before running.
Never hardcode credentials here.
"""
from __future__ import annotations

import os


# ── LLM provider ──────────────────────────────────────────────────────────────

LLM_PROVIDER: str = os.environ.get("LLM_PROVIDER", "watsonx")

# WatsonX
WATSONX_URL: str = os.environ.get("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
WATSONX_APIKEY: str = os.environ.get("WATSONX_APIKEY", "")
WATSONX_PROJECT_ID: str = os.environ.get("WATSONX_PROJECT_ID", "")
WATSONX_MODEL_ID: str = os.environ.get(
    "WATSONX_MODEL_ID", "meta-llama/llama-3-3-70b-instruct"
)

# Ollama
OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "llama3.3")

# ── A2A server ─────────────────────────────────────────────────────────────────

HOST: str = os.environ.get("HOST", "127.0.0.1")
PORT: int = int(os.environ.get("PORT", "8080"))

# ── Auth (disabled by default for Phase 3b local use) ─────────────────────────

ENABLE_CLIENT_AUTH: bool = os.environ.get("ENABLE_CLIENT_AUTH", "false").lower() == "true"
ENABLE_USER_AUTH: bool = os.environ.get("ENABLE_USER_AUTH", "false").lower() == "true"

# ── MCP tool servers (none wired in Phase 3b — Phase 4 only) ──────────────────

MCP_TERRAFORM_URL: str = os.environ.get("MCP_TERRAFORM_URL", "")

# ── AgentOps (optional) ────────────────────────────────────────────────────────

AGENTOPS_API_KEY: str = os.environ.get("AGENTOPS_API_KEY", "")
