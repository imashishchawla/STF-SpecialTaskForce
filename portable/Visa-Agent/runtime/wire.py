"""Local-only SignedEnvelope protocol; document paths must never reach a model."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import uuid

from .contracts import ContractError
from .registry import is_valid_agent, validate_route


def canonical_json(data: dict) -> str:
    """Format JSON with sorted keys and compact spacing for deterministic hashing."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_hash(data: dict) -> str:
    """Compute sha256 hex digest of canonical JSON payload."""
    serialized = canonical_json(data).encode("utf-8")
    return f"sha256:{hashlib.sha256(serialized).hexdigest()}"


def build_document_reference(doc_id: str, doc_type: str, file_path: Path, expected_root: Path = None) -> dict:
    """Construct and validate a local document reference.

    Enforces that the document exists, is not a symlink, and resides inside expected_root (.profile/).
    """
    file_path = Path(file_path).resolve()
    if file_path.is_symlink():
        raise ContractError("Document reference must not be a symlink")
    if not file_path.is_file():
        raise ContractError(f"Referenced document does not exist: {file_path}")

    if expected_root is not None:
        expected_root = Path(expected_root).resolve()
        if not str(file_path).startswith(str(expected_root)):
            raise ContractError("Document reference must reside inside the client profile boundary")

    file_bytes = file_path.read_bytes()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    return {
        "doc_id": doc_id,
        "doc_type": doc_type,
        "local_path": str(file_path),
        "sha256": file_hash,
    }


def build_envelope(
    from_agent: str,
    to_agent: str,
    msg_type: str,
    payload: dict,
    document_references: list = None,
    redaction_summary: dict = None,
    ttl_ms: int = 30000,
) -> dict:
    """Construct a SignedEnvelope JSON for inter-agent communication."""
    validate_route(from_agent, to_agent)
    if msg_type not in ("task", "result", "ack", "nack"):
        raise ContractError(f"Invalid msg_type: '{msg_type}'")
    if not isinstance(payload, dict):
        raise ContractError("Payload must be a dictionary")

    doc_refs = document_references or []
    redact_sum = redaction_summary or {
        "token_count": 0,
        "fields_redacted": [],
        "vault_ref": "none",
    }

    envelope = {
        "env_version": 1,
        "msg_id": f"msg_{uuid.uuid4().hex}",
        "from": from_agent,
        "to": to_agent,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "ttl_ms": ttl_ms,
        "msg_type": msg_type,
        "payload": payload,
        "document_references": doc_refs,
        "redaction_summary": redact_sum,
        "payload_hash": compute_hash(payload),
    }
    return envelope


def verify_envelope(envelope: dict, expected_recipient: str = None) -> bool:
    """Verify integrity, route validity, TTL, and payload hash of an envelope."""
    if not isinstance(envelope, dict):
        raise ContractError("Envelope must be an object")

    required_keys = {
        "env_version", "msg_id", "from", "to", "sent_at",
        "ttl_ms", "msg_type", "payload", "document_references",
        "redaction_summary", "payload_hash"
    }
    if not required_keys.issubset(set(envelope.keys())):
        raise ContractError("Envelope missing required fields")

    if envelope["env_version"] != 1:
        raise ContractError(f"Unsupported envelope version: {envelope['env_version']}")

    from_agent = envelope["from"]
    to_agent = envelope["to"]
    validate_route(from_agent, to_agent)

    if expected_recipient and to_agent != expected_recipient:
        raise ContractError(f"Envelope recipient mismatch: expected {expected_recipient}, got {to_agent}")

    # Check payload hash
    expected_hash = compute_hash(envelope["payload"])
    if envelope["payload_hash"] != expected_hash:
        raise ContractError("Payload hash mismatch; message corrupted or tampered")

    # Check TTL
    sent_time = datetime.fromisoformat(envelope["sent_at"])
    now_time = datetime.now(timezone.utc)
    elapsed_ms = (now_time - sent_time).total_seconds() * 1000.0
    if elapsed_ms > envelope["ttl_ms"]:
        raise ContractError(f"Envelope TTL expired ({elapsed_ms:.1f}ms > {envelope['ttl_ms']}ms)")

    # Validate document references if any
    for ref in envelope.get("document_references", []):
        ref_path = Path(ref["local_path"])
        if not ref_path.is_file():
            raise ContractError(f"Document reference path missing: {ref_path}")
        real_hash = hashlib.sha256(ref_path.read_bytes()).hexdigest()
        if real_hash != ref["sha256"]:
            raise ContractError(f"Document hash mismatch for {ref_path}")

    return True
