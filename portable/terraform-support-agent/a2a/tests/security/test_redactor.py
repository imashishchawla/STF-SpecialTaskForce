"""
test_redactor.py — Unit tests for PII and credential redaction pipeline.
"""
from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from security.redactor import RedactionPipeline, XCVBH_PATTERN
from security.vault import SessionVault


class TestRedactionPipeline(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.vault = SessionVault(session_id="01J1TESTSESSION000000000001", vault_dir=Path(self.tmp_dir.name))
        self.pipeline = RedactionPipeline(vault=self.vault)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_token_format(self) -> None:
        """Tokens must match XCVBH-<8char-hex>-<4digit-counter>."""
        text = "Contact support at customer.alice@example.com for assistance."
        res = self.pipeline.redact_text(text)
        self.assertEqual(res.token_count, 1)
        matches = XCVBH_PATTERN.findall(res.sanitized_text)
        self.assertEqual(len(matches), 1)
        token = matches[0]
        self.assertTrue(token.startswith("XCVBH-"))
        self.assertTrue(token.endswith("-0001"))

    def test_determinism_within_session(self) -> None:
        """The same raw string must receive the exact same token in the same session."""
        text1 = "User alice@example.com reported an issue."
        text2 = "Follow-up email sent to alice@example.com yesterday."
        res1 = self.pipeline.redact_text(text1)
        res2 = self.pipeline.redact_text(text2)

        token1 = XCVBH_PATTERN.search(res1.sanitized_text).group(0)
        token2 = XCVBH_PATTERN.search(res2.sanitized_text).group(0)
        self.assertEqual(token1, token2)

    def test_different_sessions_different_tokens(self) -> None:
        """Different sessions must have different salts and thus different token prefixes."""
        with tempfile.TemporaryDirectory() as other_dir:
            other_vault = SessionVault(session_id="01J1TESTSESSION000000000002", vault_dir=Path(other_dir))
            other_pipeline = RedactionPipeline(vault=other_vault)

            raw = "corp.admin@acme-corp.com"
            res1 = self.pipeline.redact_text(raw)
            res2 = other_pipeline.redact_text(raw)

            tok1 = XCVBH_PATTERN.search(res1.sanitized_text).group(0)
            tok2 = XCVBH_PATTERN.search(res2.sanitized_text).group(0)
            self.assertNotEqual(tok1, tok2)

    def test_idempotency(self) -> None:
        """Applying the filter twice to already-tokenized text must be a no-op."""
        raw = "Server ip is 192.168.1.100 and admin is admin@example.com"
        res1 = self.pipeline.redact_text(raw)
        res2 = self.pipeline.redact_text(res1.sanitized_text)

        self.assertEqual(res1.sanitized_text, res2.sanitized_text)
        self.assertEqual(res2.token_count, 0)

    def test_credential_detection_and_warning(self) -> None:
        """Known credential formats must be masked and generate warnings."""
        secret_sample = "Found AWS key AKIAIOSFODNN7EXAMPLE in debug log"
        res = self.pipeline.redact_text(secret_sample)

        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", res.sanitized_text)
        self.assertIn("aws_access_key", res.fields_redacted)
        self.assertTrue(len(res.credential_warnings) > 0)
        self.assertIn("aws_access_key", res.credential_warnings[0])

    def test_detokenization(self) -> None:
        """De-tokenization at display time must restore the exact original plain text."""
        raw = "Cluster arn:aws:ecs:us-east-1:123456789012:cluster/prod-cluster has issue"
        res = self.pipeline.redact_text(raw)
        self.assertNotIn("arn:aws:ecs:us-east-1:123456789012", res.sanitized_text)

        restored = self.vault.detokenize_text(res.sanitized_text)
        self.assertEqual(restored, raw)

    def test_structured_data_redaction(self) -> None:
        """Sensitive field names in dictionaries must be redacted."""
        payload = {
            "task_id": "task_123",
            "customer_name": "Acme Widgets Inc",
            "account_id": "ACC-998877",
            "config": {
                "api_key": "supersecretpassword123",
                "region": "us-east-1",
            },
        }

        sanitized, fields_redacted, token_count, warnings = self.pipeline.redact_data(payload)
        self.assertEqual(sanitized["task_id"], "task_123")
        self.assertEqual(sanitized["config"]["region"], "us-east-1")
        self.assertTrue(sanitized["customer_name"].startswith("XCVBH-"))
        self.assertTrue(sanitized["account_id"].startswith("XCVBH-"))
        self.assertTrue(sanitized["config"]["api_key"].startswith("XCVBH-"))
        self.assertIn("customer_name", fields_redacted)
        self.assertIn("config.api_key", fields_redacted)


if __name__ == "__main__":
    unittest.main()
