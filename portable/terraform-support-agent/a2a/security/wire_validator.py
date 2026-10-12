"""
wire_validator.py — SignedEnvelope validation and A2A wire format verification.

Implements Design Doc 09 (Inter-Agent Wire Format) for the STF
Terraform Support Agent.

Validates that messages arriving at the A2A server boundary:
1. Comply with the SignedEnvelope schema.
2. Are not stale (TTL enforcement).
3. Have matching payload integrity hashes (payload_hash).
4. Do not exceed message size bounds.
5. Contain valid redaction summaries.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


# Maximum message size (5 MB) to prevent DOS / buffer exhaustion
MAX_MESSAGE_SIZE_BYTES = 5 * 1024 * 1024

# Allowed message types per Doc 09 §2
ALLOWED_MSG_TYPES = {"task", "result", "ack", "nack", "heartbeat"}


@dataclass
class EnvelopeVerificationResult:
    """Outcome of a SignedEnvelope inspection."""
    valid: bool
    error: Optional[str] = None
    envelope: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None


def compute_canonical_payload_hash(payload: Dict[str, Any]) -> str:
    """Compute sha256:<hex> over the canonical, deterministic JSON of the payload."""
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


class SignedEnvelopeValidator:
    """Validates inbound SignedEnvelope dictionaries against Doc 09 rules."""

    def __init__(self, max_ttl_ms: int = 300_000, enforce_ttl: bool = True) -> None:
        self.max_ttl_ms = max_ttl_ms
        self.enforce_ttl = enforce_ttl

    def validate(self, envelope: Dict[str, Any], raw_size_bytes: Optional[int] = None) -> EnvelopeVerificationResult:
        """Validate envelope structure, TTL, payload hash, and bounds."""
        # 1. Size Check
        if raw_size_bytes is not None and raw_size_bytes > MAX_MESSAGE_SIZE_BYTES:
            return EnvelopeVerificationResult(
                valid=False,
                error=f"Message size ({raw_size_bytes} bytes) exceeds limit ({MAX_MESSAGE_SIZE_BYTES} bytes)",
            )

        # 2. Structural fields check
        required_fields = ["env_version", "msg_id", "sent_at_ms", "ttl_ms", "from", "to", "msg_type"]
        for field in required_fields:
            if field not in envelope:
                return EnvelopeVerificationResult(valid=False, error=f"Missing required envelope field: {field}")

        if envelope["env_version"] != 1:
            return EnvelopeVerificationResult(
                valid=False,
                error=f"Unsupported env_version: {envelope['env_version']} (expected 1)",
            )

        msg_type = envelope["msg_type"]
        if msg_type not in ALLOWED_MSG_TYPES:
            return EnvelopeVerificationResult(valid=False, error=f"Invalid msg_type: {msg_type}")

        msg_id = str(envelope["msg_id"])
        if not msg_id.startswith("msg_"):
            return EnvelopeVerificationResult(valid=False, error=f"msg_id must start with 'msg_', got: {msg_id}")

        # 3. TTL enforcement
        now_ms = int(time.time() * 1000)
        sent_at_ms = int(envelope["sent_at_ms"])
        ttl_ms = int(envelope["ttl_ms"])

        if self.enforce_ttl:
            age_ms = now_ms - sent_at_ms
            if age_ms < 0 and abs(age_ms) > 5000:
                return EnvelopeVerificationResult(valid=False, error="Message timestamp is in the future")
            if age_ms > ttl_ms:
                return EnvelopeVerificationResult(
                    valid=False,
                    error=f"Message TTL expired: age {age_ms}ms exceeds ttl_ms {ttl_ms}ms",
                )

        # 4. Payload extraction and hash verification
        payload: Optional[Dict[str, Any]] = None
        if msg_type in ("task", "result"):
            has_task = "task" in envelope and envelope["task"] is not None
            has_result = "result" in envelope and envelope["result"] is not None

            if has_task and has_result:
                return EnvelopeVerificationResult(valid=False, error="Cannot have both 'task' and 'result' payloads")
            if not has_task and not has_result:
                return EnvelopeVerificationResult(valid=False, error=f"Message type '{msg_type}' requires a payload")

            payload = envelope.get("task") if has_task else envelope.get("result")
            if not isinstance(payload, dict):
                return EnvelopeVerificationResult(valid=False, error="Payload must be a JSON object")

            # Verify payload_hash if provided
            declared_hash = envelope.get("payload_hash")
            if declared_hash:
                computed_hash = compute_canonical_payload_hash(payload)
                if declared_hash != computed_hash:
                    return EnvelopeVerificationResult(
                        valid=False,
                        error=f"payload_hash mismatch: expected {declared_hash}, computed {computed_hash}",
                    )

        # 5. Redaction Summary Check
        if "redaction_summary" in envelope:
            summary = envelope["redaction_summary"]
            if not isinstance(summary, dict) or "vault_ref" not in summary:
                return EnvelopeVerificationResult(
                    valid=False,
                    error="redaction_summary must be an object containing 'vault_ref'",
                )

        return EnvelopeVerificationResult(valid=True, envelope=envelope, payload=payload)
