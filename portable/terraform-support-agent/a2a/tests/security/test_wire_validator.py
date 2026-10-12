"""
test_wire_validator.py — Unit tests for SignedEnvelope wire format validation.
"""
from __future__ import annotations

import time
import unittest

from security.wire_validator import (
    MAX_MESSAGE_SIZE_BYTES,
    SignedEnvelopeValidator,
    compute_canonical_payload_hash,
)


class TestSignedEnvelopeValidator(unittest.TestCase):

    def setUp(self) -> None:
        self.validator = SignedEnvelopeValidator()
        self.now_ms = int(time.time() * 1000)
        self.valid_task = {
            "task_id": "task_01J1TEST",
            "action": "diagnose_log",
            "evidence": "XCVBH-3f9a1b2c-0001 failed with status 500",
        }
        self.payload_hash = compute_canonical_payload_hash(self.valid_task)

    def test_valid_envelope(self) -> None:
        """A properly formed envelope must validate successfully."""
        env = {
            "env_version": 1,
            "msg_id": "msg_01J1ABCDEF000000000001",
            "sent_at_ms": self.now_ms,
            "ttl_ms": 30000,
            "from": "coordinator",
            "to": "specialist/diagnostics",
            "msg_type": "task",
            "task": self.valid_task,
            "payload_hash": self.payload_hash,
            "redaction_summary": {
                "token_count": 1,
                "fields_redacted": ["evidence"],
                "vault_ref": "session_01J1TEST",
            },
        }

        res = self.validator.validate(env)
        self.assertTrue(res.valid)
        self.assertIsNone(res.error)
        self.assertEqual(res.payload, self.valid_task)

    def test_missing_required_fields(self) -> None:
        """Missing structural fields must fail validation."""
        env = {
            "env_version": 1,
            "msg_id": "msg_123",
            # missing sent_at_ms, ttl_ms, from, to, msg_type
        }
        res = self.validator.validate(env)
        self.assertFalse(res.valid)
        self.assertIn("Missing required envelope field", res.error)

    def test_invalid_env_version(self) -> None:
        """Envelope version other than 1 must be rejected."""
        env = {
            "env_version": 2,
            "msg_id": "msg_123",
            "sent_at_ms": self.now_ms,
            "ttl_ms": 30000,
            "from": "coordinator",
            "to": "specialist",
            "msg_type": "task",
            "task": self.valid_task,
        }
        res = self.validator.validate(env)
        self.assertFalse(res.valid)
        self.assertIn("Unsupported env_version", res.error)

    def test_ttl_expiration(self) -> None:
        """Messages older than ttl_ms must be rejected."""
        old_time = self.now_ms - 45000  # 45 seconds ago
        env = {
            "env_version": 1,
            "msg_id": "msg_123",
            "sent_at_ms": old_time,
            "ttl_ms": 30000,  # 30 seconds TTL
            "from": "coordinator",
            "to": "specialist",
            "msg_type": "task",
            "task": self.valid_task,
        }
        res = self.validator.validate(env)
        self.assertFalse(res.valid)
        self.assertIn("Message TTL expired", res.error)

    def test_payload_hash_mismatch(self) -> None:
        """A tampered payload must fail payload_hash integrity check."""
        env = {
            "env_version": 1,
            "msg_id": "msg_123",
            "sent_at_ms": self.now_ms,
            "ttl_ms": 30000,
            "from": "coordinator",
            "to": "specialist",
            "msg_type": "task",
            "task": self.valid_task,
            "payload_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        }
        res = self.validator.validate(env)
        self.assertFalse(res.valid)
        self.assertIn("payload_hash mismatch", res.error)

    def test_size_limit_rejection(self) -> None:
        """Messages exceeding max size limit must be rejected."""
        env = {"env_version": 1}
        res = self.validator.validate(env, raw_size_bytes=MAX_MESSAGE_SIZE_BYTES + 1024)
        self.assertFalse(res.valid)
        self.assertIn("exceeds limit", res.error)


if __name__ == "__main__":
    unittest.main()
