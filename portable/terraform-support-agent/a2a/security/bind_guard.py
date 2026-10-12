"""
bind_guard.py — Network exposure and host binding verification.

Implements network safety rules from the Portability Readiness Plan (§4).
Fails startup closed if the A2A server is configured to bind to a non-loopback
address (e.g. 0.0.0.0 or a public interface) without explicit authentication
and deployment controls enabled.
"""
from __future__ import annotations

import ipaddress
from typing import Tuple


LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


class SecurityConfigurationError(Exception):
    """Raised when server network binding or authentication rules are violated."""
    pass


def is_loopback_address(host: str) -> bool:
    """Check if the given host string is strictly a local loopback interface."""
    host_clean = host.strip().lower()
    if host_clean in LOOPBACK_HOSTS:
        return True
    try:
        ip = ipaddress.ip_address(host_clean)
        return ip.is_loopback
    except ValueError:
        return False


def verify_bind_address_or_fail(
    host: str,
    enable_client_auth: bool = False,
    enable_user_auth: bool = False,
) -> Tuple[bool, str]:
    """
    Verify that host binding meets safety guardrails.

    Rules:
    1. Loopback addresses (127.0.0.1, localhost, ::1) are always allowed.
    2. Non-loopback addresses (e.g. 0.0.0.0, LAN IP, public IP) REQUIRE:
       - Both or at least one authentication mechanism enabled (enable_client_auth or enable_user_auth).
       - If neither is enabled, raises SecurityConfigurationError and aborts.
    """
    if is_loopback_address(host):
        return True, "Bound to local loopback interface (secure)"

    # Non-loopback requested:
    if not enable_client_auth and not enable_user_auth:
        msg = (
            f"SECURITY ERROR: Attempted to bind A2A server to non-loopback address '{host}' "
            "with ENABLE_CLIENT_AUTH=false and ENABLE_USER_AUTH=false. "
            "Exposing the A2A server without authentication is strictly prohibited. "
            "To fix: Bind to 127.0.0.1 (default) or enable authentication in .env."
        )
        raise SecurityConfigurationError(msg)

    return True, f"Bound to external interface '{host}' with authentication enabled"
