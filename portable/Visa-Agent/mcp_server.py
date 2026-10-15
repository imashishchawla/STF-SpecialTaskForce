#!/usr/bin/env python3
"""Disabled MCP surface. Private case tools run through the local CLI only."""

import json
import sys

TOOLS_MANIFEST = []


def handle_request(req: dict) -> dict:
    req_id = req.get("id")
    method = req.get("method")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "visa-agent-mcp", "version": "1.0.0"},
            "capabilities": {"tools": {}}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS_MANIFEST}}
    return {"jsonrpc": "2.0", "id": req_id,
            "error": {"code": -32601, "message": "MCP tools are disabled; use local CLI validation"}}


def main():
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = handle_request(request)
        except (ValueError, TypeError):
            response = {"jsonrpc": "2.0", "id": None,
                        "error": {"code": -32700, "message": "Invalid JSON-RPC request"}}
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
