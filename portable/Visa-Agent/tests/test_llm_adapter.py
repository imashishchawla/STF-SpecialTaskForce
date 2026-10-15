"""Automated test suite for the Universal LLM Adapter, self-healing parser, and reflection loop."""

import json
import unittest

from runtime.contracts import ContractError
from runtime.llm import (
    normalize_agent_id,
    repair_and_parse_json,
    format_reflection_prompt,
    build_specialist_prompt,
    execute_model_turn,
)


class TestLLMAdapter(unittest.TestCase):
    def test_normalize_agent_id(self):
        self.assertEqual(normalize_agent_id("gsm"), "agent_pr_gsm_specialist")
        self.assertEqual(normalize_agent_id("pr"), "agent_pr_gsm_specialist")
        self.assertEqual(normalize_agent_id("acs"), "agent_acs_evidence_auditor")
        self.assertEqual(normalize_agent_id("coordinator"), "master_migration_coordinator")
        self.assertEqual(normalize_agent_id("agent_visitor_visa_specialist"), "agent_visitor_visa_specialist")

        with self.assertRaises(ContractError):
            normalize_agent_id("non_existent_specialist")

    def test_repair_and_parse_json_variations(self):
        # 1. Standard clean JSON
        clean = '{"status": "ok", "value": 42}'
        self.assertEqual(repair_and_parse_json(clean), {"status": "ok", "value": 42})

        # 2. Wrapped in markdown codeblock
        markdown = '```json\n{"status": "ok", "points": 85}\n```'
        self.assertEqual(repair_and_parse_json(markdown), {"status": "ok", "points": 85})

        # 3. Conversational preamble and trailing explanation (common in Llama/Claude)
        conversational = (
            "Here is the evaluation envelope requested:\n\n"
            "```json\n"
            '{\n  "status": "ready",\n  "subclass": "189"\n}\n'
            "```\n"
            "Let me know if you need any adjustments!"
        )
        self.assertEqual(repair_and_parse_json(conversational), {"status": "ready", "subclass": "189"})

        # 4. Trailing commas
        trailing_comma = '{"items": [1, 2, 3,], "active": true,}'
        self.assertEqual(repair_and_parse_json(trailing_comma), {"items": [1, 2, 3], "active": True})

        # 5. Invalid JSON
        with self.assertRaises(ContractError):
            repair_and_parse_json("Not a json at all")

    def test_build_specialist_prompt(self):
        facts = [{"id": "fact_01", "name": "age", "value": "37"}]
        with self.assertRaises(ContractError):
            build_specialist_prompt(
                agent_id="gsm",
                case_id="case_abc123",
                candidate_alias="XCVBH-TEST-0001",
                task_description="Evaluate points for 189",
                sanitized_facts=facts,
            )

    def test_execute_model_turn_never_calls_model(self):
        vault = {"XCVBH-1234-0001": "Asha Example"}
        call_count = 0

        def mock_model(prompt):
            nonlocal call_count
            call_count += 1
            return "{}"

        safe_prompt = "Evaluate points for candidate XCVBH-1234-0001"
        with self.assertRaises(ContractError):
            execute_model_turn(
                prompt=safe_prompt,
                vault_mapping=vault,
                model_caller_fn=mock_model,
                max_retries=2,
            )
        self.assertEqual(call_count, 0)

    def test_execute_model_turn_blocks_egress_pii(self):
        vault = {"XCVBH-1234-0001": "Asha Example"}
        leaky_prompt = "Evaluate points for Asha Example under 189"

        with self.assertRaises(ContractError):
            execute_model_turn(
                prompt=leaky_prompt,
                vault_mapping=vault,
                model_caller_fn=lambda p: "{}",
            )

    def test_public_mcp_is_disabled(self):
        from runtime.llm import query_anzsco_public_tool
        with self.assertRaises(ContractError):
            query_anzsco_public_tool("search_occupations", {"query": "software engineer"})

    def test_mcp_cannot_expose_vault(self):
        from mcp_server import TOOLS_MANIFEST, handle_request
        self.assertNotIn("decrypt_client_vault", [tool["name"] for tool in TOOLS_MANIFEST])
        response = handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                   "params": {"name": "decrypt_client_vault", "arguments": {"profile_folder": "synthetic"}}})
        self.assertEqual(response["error"]["code"], -32601)


if __name__ == "__main__":
    unittest.main()
