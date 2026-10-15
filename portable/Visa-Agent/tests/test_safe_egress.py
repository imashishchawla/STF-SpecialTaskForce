"""Synthetic behavioral checks for the only enabled model callback."""

import json
from pathlib import Path
import tempfile
import unittest

from runtime.contracts import ContractError
from runtime.redactor import decrypt_vault_mapping
from runtime.safe_egress import PreparedPacket, prepare_packet, send_prepared_packet


class SafeEgressTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.profile = Path(self.temp.name) / ".profile" / "Synthetic_Client"
        self.profile.mkdir(parents=True, mode=0o700)
        self.profile.parent.chmod(0o700)

    def tearDown(self):
        self.temp.cleanup()

    def test_identity_values_are_random_tokens_and_vault_is_local(self):
        facts = {"employer_name": "Example Employer", "employee_name": "Asha Example",
                 "employee_id": "EMP-12345", "pay_period": "2026-09", "currency": "INR",
                 "payment_mode": "bank_transfer", "gross_ge_net": True,
                 "bank_credit_present": True, "slip_count": 2}
        packet = prepare_packet(self.profile, "salary_evidence", facts)
        payload = json.loads(packet.wire_json)
        for field in ("employer_name", "employee_name", "employee_id"):
            self.assertRegex(payload["facts"][field], r"^XCVBH-[A-F0-9]{24}$")
            self.assertNotIn(facts[field], packet.wire_json)
        self.assertEqual(payload["facts"]["pay_period"], "2026-09")
        seen = []
        self.assertEqual(send_prepared_packet(packet, lambda wire: seen.append(wire) or "ok"), "ok")
        self.assertEqual(seen, [packet.wire_json])
        key_path = self.profile / ".llm-vault.key"
        vault_path = self.profile / "llm-vault.enc"
        self.assertEqual(key_path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(vault_path.stat().st_mode & 0o777, 0o600)
        self.assertNotIn(b"Asha Example", vault_path.read_bytes())
        mapping = decrypt_vault_mapping(key_path.read_bytes(), vault_path)
        self.assertIn("Asha Example", mapping.values())
        repeated = prepare_packet(self.profile, "salary_evidence", facts)
        self.assertEqual(repeated.wire_json, packet.wire_json)

    def test_identity_check_masks_phone_email_and_passport(self):
        facts = {"person_name": "Asha Example", "phone": "+91 9876543210",
                 "email": "asha@example.invalid", "passport_number": "P1234567",
                 "same_identity": True}
        packet = prepare_packet(self.profile, "identity_check", facts)
        for value in facts.values():
            if isinstance(value, str):
                self.assertNotIn(value, packet.wire_json)
        self.assertEqual(json.loads(packet.wire_json)["facts"]["same_identity"], True)

    def test_rejects_document_text_paths_and_unapproved_facts(self):
        for facts in ({"document_path": "/private/client/pay.pdf"},
                      {"gross_pay": "123456.00"},
                      {"employee_name": "Asha Example", "note": "full salary slip"},
                      {"pay_period": "September 2026"}):
            with self.subTest(facts=list(facts)):
                with self.assertRaises(ContractError):
                    prepare_packet(self.profile, "salary_evidence", facts)
        self.assertFalse((self.profile / ".llm-vault.key").exists())

    def test_forged_or_modified_packet_never_calls_model(self):
        called = []
        forged = PreparedPacket('{"schema":1,"task":"identity_check","facts":{"phone":"123456"}}', b"bad")
        with self.assertRaises(ContractError):
            send_prepared_packet(forged, lambda wire: called.append(wire))
        self.assertEqual(called, [])

    def test_tokens_differ_between_profiles(self):
        other = self.profile.parent / "Other_Synthetic_Client"
        other.mkdir(mode=0o700)
        first = prepare_packet(self.profile, "identity_check", {"person_name": "Asha Example"})
        second = prepare_packet(other, "identity_check", {"person_name": "Asha Example"})
        self.assertNotEqual(first.wire_json, second.wire_json)


if __name__ == "__main__":
    unittest.main()
