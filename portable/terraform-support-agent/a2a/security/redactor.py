"""
redactor.py — PII and Credential Redaction Pipeline.

Implements Design Doc 08 (PII Protection and Encryption) for the STF
Terraform Support Agent.

Ensures sensitive strings never appear in plaintext in LLM context windows,
version-controlled checkpoints, or public traces.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from .vault import SessionVault


# Regex pattern matching any existing XCVBH token: XCVBH-<8hexchars>-<4digits>
XCVBH_PATTERN = re.compile(r"\bXCVBH-[a-f0-9]{8}-\d{4}\b")

# Credential patterns (Tier: Encrypted)
RE_AWS_KEY = re.compile(r"\b(AKIA|ASIA|ABIA|ACCA)[A-Z0-9]{16}\b")
RE_GITHUB_PAT = re.compile(r"\b(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})\b")
RE_TFC_TOKEN = re.compile(r"\batlasv1\.[a-zA-Z0-9_-]{40,}\b")
RE_PEM_PRIVATE_KEY = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----")

# PII / Infrastructure patterns (Tier: Redacted)
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
RE_IPV4 = re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b")
RE_AWS_ARN = re.compile(r"\barn:aws[a-zA-Z-]*:[a-zA-Z0-9-]*:[a-zA-Z0-9-]*:[0-9]{12}:[a-zA-Z0-9-_/:.]+\b")
RE_UUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")

# Sensitive dictionary keys to redact automatically
SENSITIVE_FIELD_NAMES = {
    "customer_name", "customer_email", "customer_id",
    "account_name", "account_id", "organization_name", "org_name",
    "api_key", "apikey", "secret", "password", "token",
    "bearer", "private_key", "access_key", "secret_key",
}


@dataclass
class RedactionResult:
    """Outcome of a redaction pass."""
    sanitized_text: str
    token_count: int
    fields_redacted: List[str]
    vault_ref: str
    credential_warnings: List[str] = field(default_factory=list)

    def summary(self) -> Dict[str, Any]:
        """Return redaction_summary formatted for SignedEnvelope (Doc 09)."""
        return {
            "token_count": self.token_count,
            "fields_redacted": self.fields_redacted,
            "vault_ref": self.vault_ref,
        }


class RedactionPipeline:
    """
    Two-tier redaction pipeline:
    1. Pattern Scanner (identifies PII & credentials in unstructured text).
    2. Field-Name Allowlist/Denylist (identifies sensitive keys in structured payloads).
    """

    def __init__(self, vault: Optional[SessionVault] = None) -> None:
        self.vault: SessionVault = vault or SessionVault()

    def _generate_token(self, raw_value: str, tier: str) -> str:
        """
        Generate deterministic, non-guessable XCVBH token:
        XCVBH-<8-char-prefix>-<4-digit-counter>
        where prefix = sha256(session_salt + raw_value)[:8]
        """
        existing = self.vault.get_token_for_value(raw_value)
        if existing:
            return existing

        digest = hashlib.sha256(self.vault.session_salt + raw_value.encode("utf-8")).hexdigest()
        prefix = digest[:8]
        counter = self.vault.next_counter()
        token = f"XCVBH-{prefix}-{counter:04d}"

        self.vault.store_token(token, raw_value, tier=tier)
        return token

    def redact_text(self, text: str) -> RedactionResult:
        """
        Scan unstructured text, replace sensitive values with XCVBH tokens,
        and record in vault. Idempotent on already tokenized spans.
        """
        if not text:
            return RedactionResult(
                sanitized_text="",
                token_count=0,
                fields_redacted=[],
                vault_ref=self.vault.session_id,
            )

        sanitized = text
        redacted_fields: List[str] = []
        credential_warnings: List[str] = []
        token_count = 0

        # Step 1: Scan for high-severity credentials (Tier: Encrypted)
        cred_scans: List[Tuple[re.Pattern, str]] = [
            (RE_PEM_PRIVATE_KEY, "private_key"),
            (RE_AWS_KEY, "aws_access_key"),
            (RE_GITHUB_PAT, "github_pat"),
            (RE_TFC_TOKEN, "tfc_token"),
        ]

        for pattern, label in cred_scans:
            for match in pattern.finditer(sanitized):
                val = match.group(0)
                if XCVBH_PATTERN.fullmatch(val):
                    continue  # already tokenized
                token = self._generate_token(val, tier="encrypted")
                sanitized = sanitized.replace(val, token)
                token_count += 1
                if label not in redacted_fields:
                    redacted_fields.append(label)
                credential_warnings.append(f"Detected and encrypted {label} (redacted as {token})")

        # Step 2: Scan for PII & Infrastructure identifiers (Tier: Redacted)
        pii_scans: List[Tuple[re.Pattern, str]] = [
            (RE_EMAIL, "email"),
            (RE_AWS_ARN, "aws_arn"),
            (RE_IPV4, "ip_address"),
            (RE_UUID, "uuid"),
        ]

        for pattern, label in pii_scans:
            for match in pattern.finditer(sanitized):
                val = match.group(0)
                if XCVBH_PATTERN.fullmatch(val):
                    continue
                token = self._generate_token(val, tier="redacted")
                sanitized = sanitized.replace(val, token)
                token_count += 1
                if label not in redacted_fields:
                    redacted_fields.append(label)

        return RedactionResult(
            sanitized_text=sanitized,
            token_count=token_count,
            fields_redacted=redacted_fields,
            vault_ref=self.vault.session_id,
            credential_warnings=credential_warnings,
        )

    def redact_data(self, data: Any, path: str = "") -> Tuple[Any, List[str], int, List[str]]:
        """
        Recursively redact a dict or list structure.
        Returns (sanitized_data, fields_redacted, token_count, credential_warnings).
        """
        fields_redacted: List[str] = []
        credential_warnings: List[str] = []
        total_tokens = 0

        if isinstance(data, dict):
            new_dict: Dict[str, Any] = {}
            for k, v in data.items():
                current_path = f"{path}.{k}" if path else k
                # If key name is explicitly sensitive, redact the value regardless of regex
                if any(sens in k.lower() for sens in SENSITIVE_FIELD_NAMES) and isinstance(v, str):
                    if not XCVBH_PATTERN.fullmatch(v):
                        tier = "encrypted" if any(sec in k.lower() for sec in ("key", "secret", "password", "token")) else "redacted"
                        tok = self._generate_token(v, tier=tier)
                        new_dict[k] = tok
                        fields_redacted.append(current_path)
                        total_tokens += 1
                        if tier == "encrypted":
                            credential_warnings.append(f"Redacted sensitive field {current_path}")
                        continue

                rec_v, rec_f, rec_c, rec_w = self.redact_data(v, current_path)
                new_dict[k] = rec_v
                fields_redacted.extend(rec_f)
                total_tokens += rec_c
                credential_warnings.extend(rec_w)
            return new_dict, fields_redacted, total_tokens, credential_warnings

        elif isinstance(data, list):
            new_list = []
            for idx, item in enumerate(data):
                current_path = f"{path}[{idx}]"
                rec_v, rec_f, rec_c, rec_w = self.redact_data(item, current_path)
                new_list.append(rec_v)
                fields_redacted.extend(rec_f)
                total_tokens += rec_c
                credential_warnings.extend(rec_w)
            return new_list, fields_redacted, total_tokens, credential_warnings

        elif isinstance(data, str):
            res = self.redact_text(data)
            if res.token_count > 0:
                fields_redacted.append(path or "text")
            return res.sanitized_text, fields_redacted, res.token_count, res.credential_warnings

        return data, fields_redacted, total_tokens, credential_warnings
