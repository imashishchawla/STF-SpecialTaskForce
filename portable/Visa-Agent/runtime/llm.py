"""Legacy model parsing helpers; all model and public MCP calls fail closed."""

import json
import re
from typing import Callable

from .contracts import ContractError
from .registry import is_valid_agent

# Fuzzy alias map to resolve common short names used by LLMs
AGENT_ALIASES = {
    "gsm": "agent_pr_gsm_specialist",
    "pr": "agent_pr_gsm_specialist",
    "pr_gsm": "agent_pr_gsm_specialist",
    "acs": "agent_acs_evidence_auditor",
    "auditor": "agent_acs_evidence_auditor",
    "acs_auditor": "agent_acs_evidence_auditor",
    "partner": "agent_partner_family_specialist",
    "family": "agent_partner_family_specialist",
    "employer": "agent_employer_sponsorship_specialist",
    "sponsorship": "agent_employer_sponsorship_specialist",
    "student": "agent_student_visa_specialist",
    "visitor": "agent_visitor_visa_specialist",
    "coordinator": "master_migration_coordinator",
    "master": "master_migration_coordinator",
}


def normalize_agent_id(name: str) -> str:
    """Normalize fuzzy agent names to canonical registered IDs."""
    if not name or not isinstance(name, str):
        raise ContractError("Agent ID must be a non-empty string")
    clean = name.strip().lower()
    if is_valid_agent(clean):
        return clean
    if clean in AGENT_ALIASES:
        return AGENT_ALIASES[clean]
    # Check prefix matching
    for alias, canonical in AGENT_ALIASES.items():
        if clean.startswith(alias) or alias in clean:
            return canonical
    raise ContractError(f"Cannot resolve agent identity: '{name}'")


def repair_and_parse_json(raw_text: str) -> dict:
    """Extract, clean, and parse JSON from any LLM output.

    Handles markdown fences (```json), conversational preamble/postamble,
    and trailing commas.
    """
    if not raw_text or not isinstance(raw_text, str):
        raise ContractError("Model output was empty or not a string")

    cleaned = raw_text.strip()

    # 1. Strip markdown fences: ```json ... ``` or ``` ... ```
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"```\s*$", "", cleaned, flags=re.MULTILINE).strip()

    # 2. Extract balanced outer JSON object {...}
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ContractError("No valid JSON object structure found in response")
    cleaned = cleaned[start : end + 1]

    # 3. Fix trailing commas: {"key": "val",} -> {"key": "val"}
    cleaned = re.sub(r",\s*([\}\]])", r"\1", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ContractError(f"Malformed JSON in response: {exc}") from exc


def format_reflection_prompt(original_prompt: str, error_message: str) -> str:
    """Disabled because errors and original prompts can contain private values."""
    raise ContractError("Free-form model reflection prompts are disabled")


def build_specialist_prompt(
    agent_id: str,
    case_id: str,
    candidate_alias: str,
    task_description: str,
    sanitized_facts: list[dict],
    document_references: list[dict] = None,
    vault_ref: str = "local_vault",
) -> str:
    """Case-scoped prompts are disabled pending a verifiable local-only model."""
    raise ContractError("Case-scoped specialist prompts are local-only; external model use is disabled")


def execute_model_turn(
    prompt: str,
    vault_mapping: dict,
    model_caller_fn: Callable[[str], str],
    expected_recipient: str = "master_migration_coordinator",
    max_retries: int = 2,
) -> dict:
    """Fail closed: a vault lookup cannot establish that free-form text is safe."""
    raise ContractError("External model calls are disabled for Visa Agent case work")


def query_anzsco_public_tool(tool_name: str, arguments: dict = None) -> dict:
    """Fail closed: public MCP traffic is disabled until generic-only routing exists."""
    raise ContractError("External MCP calls are disabled for Visa Agent case work")
