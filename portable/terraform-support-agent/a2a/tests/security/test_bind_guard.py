"""
test_bind_guard.py — Unit tests for network host binding verification.
"""
from __future__ import annotations

import unittest

from security.bind_guard import (
    SecurityConfigurationError,
    is_loopback_address,
    verify_bind_address_or_fail,
)


class TestBindGuard(unittest.TestCase):

    def test_loopback_detection(self) -> None:
        """Loopback identifiers must be recognized."""
        self.assertTrue(is_loopback_address("127.0.0.1"))
        self.assertTrue(is_loopback_address("localhost"))
        self.assertTrue(is_loopback_address("::1"))
        self.assertFalse(is_loopback_address("0.0.0.0"))
        self.assertFalse(is_loopback_address("192.168.1.50"))
        self.assertFalse(is_loopback_address("10.0.0.1"))

    def test_localhost_binding_allowed_without_auth(self) -> None:
        """Binding to loopback without auth is safe and allowed."""
        ok, msg = verify_bind_address_or_fail("127.0.0.1", enable_client_auth=False, enable_user_auth=False)
        self.assertTrue(ok)
        self.assertIn("loopback", msg)

        ok, msg = verify_bind_address_or_fail("localhost")
        self.assertTrue(ok)

    def test_unauthenticated_exposure_rejected(self) -> None:
        """Binding to 0.0.0.0 without authentication must raise SecurityConfigurationError."""
        with self.assertRaises(SecurityConfigurationError) as ctx:
            verify_bind_address_or_fail("0.0.0.0", enable_client_auth=False, enable_user_auth=False)
        self.assertIn("SECURITY ERROR", str(ctx.exception))
        self.assertIn("0.0.0.0", str(ctx.exception))

    def test_external_ip_rejected_without_auth(self) -> None:
        """Binding to a LAN IP without auth must fail closed."""
        with self.assertRaises(SecurityConfigurationError):
            verify_bind_address_or_fail("192.168.1.100", enable_client_auth=False, enable_user_auth=False)

    def test_authenticated_external_binding_allowed(self) -> None:
        """Binding to external IP with auth enabled is permitted."""
        ok, msg = verify_bind_address_or_fail("0.0.0.0", enable_client_auth=True, enable_user_auth=False)
        self.assertTrue(ok)
        self.assertIn("authentication enabled", msg)


if __name__ == "__main__":
    unittest.main()
