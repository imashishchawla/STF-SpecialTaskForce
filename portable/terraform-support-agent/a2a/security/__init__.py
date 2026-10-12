"""
A2A Security Package for Terraform Support Agent.

Implements:
- Design Doc 08: PII Protection, XCVBH tokenization, AES-256-GCM session vault.
- Design Doc 09: SignedEnvelope wire format validation, canonical hashing, TTL enforcement.
- Network Guard: Fail-closed localhost binding rules.
"""
from __future__ import annotations

from .bind_guard import (
    SecurityConfigurationError,
    is_loopback_address,
    verify_bind_address_or_fail,
)
from .redactor import RedactionPipeline, RedactionResult
from .vault import SessionVault, generate_ulid
from .wire_validator import (
    EnvelopeVerificationResult,
    SignedEnvelopeValidator,
    compute_canonical_payload_hash,
)

__all__ = [
    "SecurityConfigurationError",
    "is_loopback_address",
    "verify_bind_address_or_fail",
    "RedactionPipeline",
    "RedactionResult",
    "SessionVault",
    "generate_ulid",
    "EnvelopeVerificationResult",
    "SignedEnvelopeValidator",
    "compute_canonical_payload_hash",
]
