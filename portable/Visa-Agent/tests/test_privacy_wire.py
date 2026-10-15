"""Comprehensive automated tests for PII redaction, AES-256-GCM vault, registry, and wire protocol."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import time
import unittest

from runtime.contracts import ContractError
from runtime.redactor import (
    Redactor,
    PIILeakageError,
    encrypt_vault_mapping,
    decrypt_vault_mapping,
    get_or_create_vault_key,
)
from runtime.registry import (
    REGISTERED_AGENTS,
    get_agent,
    is_valid_agent,
    validate_route,
)
from runtime.wire import (
    build_envelope,
    verify_envelope,
    build_document_reference,
    compute_hash,
)
from runtime.guardrails import check_egress_safety, scrub_traceback


class TestPrivacyAndVault(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_aes_vault_encrypt_decrypt(self):
        key_path = self.dir_path / ".vault.key"
        enc_path = self.dir_path / "vault.enc"
        key = get_or_create_vault_key(key_path)
        self.assertEqual(len(key), 32)
        # Check permissions
        mode = key_path.stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)

        mapping = {
            "XCVBH-A1B2C3D4-0001": "Asha Example",
            "XCVBH-E5F6G7H8-0002": "1990-01-15",
            "XCVBH-J9K0L1M2-0003": "asha.example@example.com",
        }
        encrypt_vault_mapping(mapping, key, enc_path)
        self.assertTrue(enc_path.is_file())
        enc_mode = enc_path.stat().st_mode & 0o777
        self.assertEqual(enc_mode, 0o600)

        decrypted = decrypt_vault_mapping(key, enc_path)
        self.assertEqual(decrypted, mapping)

    def test_redactor_masks_pii_and_preserves_company_names(self):
        redactor = Redactor(session_salt=b"test_salt_1234567890123456789012")
        input_text = (
            "Candidate Asha Example (DOB: 15-01-1990), email ashatest@domain.com, "
            "phone +91-9876543210, worked at Acme Global and Beta Systems on Cloud Infrastructure."
        )
        known = ["Asha Example", "Asha", "Example"]
        redacted_text, count = redactor.redact_text(input_text, known_entities=known)

        # Names, email, DOB, phone must be masked
        self.assertNotIn("Asha Example", redacted_text)
        self.assertNotIn("15-01-1990", redacted_text)
        self.assertNotIn("ashatest@domain.com", redacted_text)
        self.assertNotIn("9876543210", redacted_text)

        # Company names MUST remain unmasked
        self.assertIn("Acme Global", redacted_text)
        self.assertIn("Beta Systems", redacted_text)
        self.assertIn("Cloud Infrastructure", redacted_text)

        # Tokens must have XCVBH sentinel format
        self.assertIn("XCVBH-", redacted_text)

        # Roundtrip detokenize restores original text
        restored = redactor.detokenize(redacted_text)
        self.assertEqual(restored, input_text)

    def test_redactor_export_vault(self):
        redactor = Redactor()
        redactor.redact_text("Alex Partner born 20-05-1992", known_entities=["Alex Partner"])
        meta = redactor.export_vault(self.dir_path)
        self.assertGreater(meta["tokens_count"], 0)
        self.assertTrue(Path(meta["vault_path"]).is_file())

        key = Path(meta["key_path"]).read_bytes()
        decrypted = decrypt_vault_mapping(key, Path(meta["vault_path"]))
        self.assertIn("Alex Partner", decrypted.values())


class TestAgentRegistry(unittest.TestCase):
    def test_registered_agents_exist(self):
        self.assertTrue(is_valid_agent("master_migration_coordinator"))
        self.assertTrue(is_valid_agent("agent_pr_gsm_specialist"))
        self.assertTrue(is_valid_agent("agent_acs_evidence_auditor"))
        self.assertFalse(is_valid_agent("rogue_agent"))

    def test_routing_validation(self):
        # Coordinator to specialist is allowed
        self.assertTrue(validate_route("master_migration_coordinator", "agent_pr_gsm_specialist"))
        # Specialist back to coordinator is allowed
        self.assertTrue(validate_route("agent_pr_gsm_specialist", "master_migration_coordinator"))
        # Direct specialist-to-specialist is disallowed (must route through coordinator)
        with self.assertRaises(ContractError):
            validate_route("agent_pr_gsm_specialist", "agent_visitor_visa_specialist")


class TestWireProtocol(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)
        # Create a mock document in profile
        self.doc_path = self.dir_path / "test_cv.pdf"
        self.doc_path.write_bytes(b"%PDF-1.4 mock cv content for testing")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_build_and_verify_valid_envelope(self):
        doc_ref = build_document_reference("doc_cv_1", "curriculum_vitae", self.doc_path, expected_root=self.dir_path)
        payload = {
            "case_id": "case_123",
            "candidate_alias": "XCVBH-A1B2-0001",
            "target_anzsco": "261313",
        }
        envelope = build_envelope(
            from_agent="master_migration_coordinator",
            to_agent="agent_pr_gsm_specialist",
            msg_type="task",
            payload=payload,
            document_references=[doc_ref],
            ttl_ms=5000,
        )
        self.assertTrue(verify_envelope(envelope, expected_recipient="agent_pr_gsm_specialist"))

    def test_tampered_payload_rejected(self):
        payload = {"data": "authentic"}
        envelope = build_envelope(
            from_agent="master_migration_coordinator",
            to_agent="agent_pr_gsm_specialist",
            msg_type="task",
            payload=payload,
        )
        envelope["payload"]["data"] = "tampered"
        with self.assertRaises(ContractError) as ctx:
            verify_envelope(envelope)
        self.assertIn("Payload hash mismatch", str(ctx.exception))

    def test_expired_ttl_rejected(self):
        payload = {"data": "test"}
        envelope = build_envelope(
            from_agent="master_migration_coordinator",
            to_agent="agent_pr_gsm_specialist",
            msg_type="task",
            payload=payload,
            ttl_ms=50,  # 50 ms
        )
        time.sleep(0.08)  # wait 80 ms
        with self.assertRaises(ContractError) as ctx:
            verify_envelope(envelope)
        self.assertIn("TTL expired", str(ctx.exception))


class TestEgressGuardrails(unittest.TestCase):
    def test_blocks_unredacted_pii(self):
        vault = {
            "XCVBH-1234-0001": "Asha Example",
            "XCVBH-1234-0002": "asha.example@example.com",
        }
        safe_payload = {
            "query": "Check points for candidate XCVBH-1234-0001 under ANZSCO 263111",
            "employer": "TechCorp Global",
        }
        # Safe payload passes
        self.assertTrue(check_egress_safety(safe_payload, vault))

        leaky_payload = {
            "query": "Check points for Asha Example under ANZSCO 263111",
        }
        # Leaky payload must raise PIILeakageError
        with self.assertRaises(PIILeakageError):
            check_egress_safety(leaky_payload, vault)

    def test_scrubs_traceback(self):
        vault = {"XCVBH-NAME-0001": "Alex Partner"}
        raw_traceback = "Traceback (most recent call last):\n  File 'app.py', line 12: user='Alex Partner'"
        clean_traceback = scrub_traceback(raw_traceback, vault)
        self.assertNotIn("Alex Partner", clean_traceback)
        self.assertIn("XCVBH-NAME-0001", clean_traceback)


if __name__ == "__main__":
    unittest.main()
