"""Automated unit tests for deterministic migration tools and MCP server."""

import json
from pathlib import Path
import unittest

from runtime.tools import (
    calculate_gsm_points,
    audit_acs_employment_episode,
    calculate_acs_skill_met_date,
)
from mcp_server import handle_request


class TestMigrationTools(unittest.TestCase):
    def test_calculate_gsm_points_candidate_scenario(self):
        res = calculate_gsm_points(
            age=37,
            english_level="superior",
            overseas_exp_years=8.5,
            education_level="bachelor_or_master",
            partner_status="partner_skilled_english",
        )
        self.assertEqual(res["subclass_189_points"], 85)
        self.assertEqual(res["subclass_190_points"], 90)
        self.assertEqual(res["subclass_491_points"], 100)
        self.assertTrue(res["meets_minimum_pass_mark"])
        self.assertEqual(res["breakdown"]["age"]["points"], 25)
        self.assertEqual(res["breakdown"]["english"]["points"], 20)
        self.assertEqual(res["breakdown"]["overseas_experience"]["points"], 15)
        self.assertEqual(res["breakdown"]["education"]["points"], 15)
        self.assertEqual(res["breakdown"]["partner"]["points"], 10)

    def test_calculate_gsm_points_ineligible_age(self):
        res = calculate_gsm_points(
            age=46,
            english_level="superior",
            overseas_exp_years=10.0,
            education_level="bachelor",
            partner_status="single",
        )
        self.assertEqual(res["breakdown"]["age"]["points"], 0)
        self.assertFalse(res["breakdown"]["age"]["eligible"])

    def test_audit_acs_employment_cash_rejected(self):
        res = audit_acs_employment_episode(
            employer="Cash Only Services Ltd",
            months_duration=21,
            payment_mode="cash",
            has_bank_credits=False,
            has_tax_or_pf=False,
            has_detailed_roles_letter=True,
        )
        self.assertEqual(res["acs_compliance_status"], "rejected")
        self.assertEqual(res["recommendation"], "Exclude from ACS claim")
        self.assertTrue(any("Cash payments are strictly not accepted" in f for f in res["findings"]))

    def test_audit_acs_employment_bank_transfer_eligible(self):
        res = audit_acs_employment_episode(
            employer="Global Tech Corp",
            months_duration=14,
            payment_mode="bank_transfer",
            has_bank_credits=True,
            has_tax_or_pf=True,
            has_detailed_roles_letter=True,
        )
        self.assertEqual(res["acs_compliance_status"], "eligible")
        self.assertEqual(res["recommendation"], "Include in ACS claim")
        self.assertEqual(len(res["findings"]), 0)

    def test_calculate_acs_skill_met_date_btech(self):
        episodes = [
            {"employer": "Alpha Software", "months": 42, "eligible": True},
            {"employer": "Beta Systems", "months": 106, "eligible": True},
        ]
        res = calculate_acs_skill_met_date("btech_ict_major", episodes)
        self.assertEqual(res["acs_deduction_years"], 2.0)
        self.assertGreaterEqual(res["post_skill_met_years"], 8.0)
        self.assertEqual(res["overseas_points_bracket"], 15)
        self.assertTrue(res["max_points_achieved"])


class TestMCPServer(unittest.TestCase):
    def test_mcp_initialize(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        res = handle_request(req)
        self.assertEqual(res["result"]["serverInfo"]["name"], "visa-agent-mcp")
        self.assertEqual(res["result"]["protocolVersion"], "2024-11-05")

    def test_mcp_tools_list(self):
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        res = handle_request(req)
        self.assertEqual(res["result"]["tools"], [])

    def test_mcp_tools_call(self):
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "calculate_gsm_points",
                "arguments": {
                    "age": 32,
                    "english_level": "superior",
                    "overseas_exp_years": 10.0,
                    "education_level": "bachelor_or_master",
                    "partner_status": "partner_skilled_english",
                },
            },
        }
        res = handle_request(req)
        self.assertEqual(res["error"]["code"], -32601)


if __name__ == "__main__":
    unittest.main()
