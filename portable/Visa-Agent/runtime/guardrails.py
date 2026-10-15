"""Outbound egress guardrails and exception traceback scrubbers.

Enforces zero-PII-leakage before any external network or model call.
"""

import json
import re
from typing import Any, Union
from .contracts import ContractError
from .redactor import PIILeakageError


def _extract_all_strings(data: Any) -> list[str]:
    """Recursively collect all string values from a nested dict/list/string."""
    collected = []
    if isinstance(data, str):
        collected.append(data)
    elif isinstance(data, dict):
        for k, v in data.items():
            if isinstance(k, str):
                collected.append(k)
            collected.extend(_extract_all_strings(v))
    elif isinstance(data, list):
        for item in data:
            collected.extend(_extract_all_strings(item))
    return collected


def check_egress_safety(payload: Union[str, dict, list], vault_mapping: dict) -> bool:
    """Pre-flight check: verify NO real sensitive values from vault appear in outbound payload.

    Raises PIILeakageError if an un-redacted value is detected.
    """
    if not vault_mapping:
        return True

    all_strings = " \n ".join(_extract_all_strings(payload))

    for token, real_val in vault_mapping.items():
        if not real_val or len(str(real_val).strip()) < 2:
            continue
        val_str = str(real_val).strip()
        # Word-boundary check for names/strings
        pattern = re.compile(rf"\b{re.escape(val_str)}\b", re.IGNORECASE)
        if pattern.search(all_strings):
            raise PIILeakageError(
                f"Egress blocked: un-redacted PII detected for token '{token}'. Real value was not masked before external call."
            )

    return True


def scrub_traceback(traceback_text: str, vault_mapping: dict) -> str:
    """Scrub real sensitive values from Python exception tracebacks before logging."""
    if not traceback_text or not vault_mapping:
        return traceback_text

    scrubbed = traceback_text
    for token, real_val in vault_mapping.items():
        if not real_val or len(str(real_val).strip()) < 2:
            continue
        val_str = str(real_val).strip()
        scrubbed = re.sub(rf"\b{re.escape(val_str)}\b", token, scrubbed, flags=re.IGNORECASE)

    return scrubbed
