"""
main.py — A2A server entry point for the Terraform Support Agent.

Starts the aicoe-agent-utils A2A server. This file is named main.py,
NOT __main__.py (which is a Python reserved name — do not rename it).

Usage:
    python main.py [--host HOST] [--port PORT]
    or simply:
    python main.py

Environment variables are loaded from .env (copy from .env.example).
"""
from __future__ import annotations

import asyncclick as click
from dotenv import load_dotenv

# Load .env before importing config so env vars are available.
load_dotenv()

import config  # noqa: E402  (after load_dotenv)
from a2a_factory import TerraformAgentFactory
from aicoe_agent_utils.a2a.server import start_a2a_server


@click.command()
@click.option("--host", default=None, help="Override HOST env var")
@click.option("--port", default=None, type=int, help="Override PORT env var")
async def main(host: str | None, port: int | None) -> None:
    """Start the Terraform Support A2A server."""
    resolved_host = host or config.HOST
    resolved_port = port or config.PORT

    factory = TerraformAgentFactory()
    agent = factory.make_agent()
    executor = factory.make_agent_executor(agent)

    await start_a2a_server(
        agent=agent,
        executor=executor,
        host=resolved_host,
        port=resolved_port,
        enable_client_auth=config.ENABLE_CLIENT_AUTH,
        enable_user_auth=config.ENABLE_USER_AUTH,
    )


if __name__ == "__main__":
    main()
