"""
test_client.py — Local smoke-test client for the Terraform Support A2A server.

Sends a single streaming message to the running A2A server and prints the response.

Usage (server must be running first):
    python main.py &
    python test_client.py

Do NOT call .stream() or .invoke() directly on A2AClient.
Use run_streaming_test() from aicoe_agent_utils.a2a.client_utils.
"""
from __future__ import annotations

import asyncio

from dotenv import load_dotenv

load_dotenv()

import config  # noqa: E402
from aicoe_agent_utils.a2a.client_utils import run_streaming_test

# A minimal test message — uses a synthetic sanitized prompt (no real case data).
_TEST_MESSAGE = (
    "Hello. I have a case where a customer reports that `terraform plan` hangs "
    "indefinitely after a recent HCP Terraform workspace migration. "
    "No logs have been provided yet. What information do you need to begin diagnosis?"
)


async def main() -> None:
    server_url = f"http://{config.HOST}:{config.PORT}"
    print(f"Connecting to A2A server at {server_url} …\n")
    await run_streaming_test(
        server_url=server_url,
        message=_TEST_MESSAGE,
        enable_client_auth=config.ENABLE_CLIENT_AUTH,
    )


if __name__ == "__main__":
    asyncio.run(main())
