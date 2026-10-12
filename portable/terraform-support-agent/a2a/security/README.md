# A2A Security Package

**Status: Implemented (Phase 3b — Priority P2 Complete).**  
This package provides security boundaries, PII redaction, cryptographic local storage, wire format verification, and network exposure protection for the Terraform Support Agent A2A server.

---

## 1. Modules Overview

| Module | Purpose | Governing Spec |
|---|---|---|
| `vault.py` | Manages per-session AES-256-GCM encrypted vaults (`vault/<session_ulid>.jsonl`). Stores encrypted token mappings with 32-byte session salts. Provides display-time detokenization for operators. | [Design Doc 08](../../docs/design/08-pii-protection-and-encryption.md) |
| `redactor.py` | Two-tier scanner (unstructured text regex + dictionary keys) substituting sensitive values with non-guessable `XCVBH-<8char>-<counter>` tokens before prompt assembly or LLM invocation. | [Design Doc 08](../../docs/design/08-pii-protection-and-encryption.md) |
| `wire_validator.py` | Validates incoming messages wrapped in `SignedEnvelope` contracts: schema conformance, message size bounds, TTL freshness, and SHA-256 canonical payload hash integrity. | [Design Doc 09](../../docs/design/09-inter-agent-wire-format.md) |
| `bind_guard.py` | Enforces fail-closed network host binding rules. Fails server startup immediately if configured to bind to `0.0.0.0` or non-loopback interfaces without client/user authentication enabled. | [Portability Plan](../../plan/portability-readiness-plan.md) §4 |

---

## 2. Security Boundaries & Guardrails

1. **Model Context Protection:** Sensitive raw customer data (emails, IPs, tokens, AWS keys, ARNs, passwords) is never passed into the LLM context. Only synthetic `XCVBH-*` tokens are sent.
2. **Key Storage:** The master vault key lives in `vault/.key` (chmod 600) or `STF_VAULT_KEY` environment variable. The `vault/` directory is strictly ignored by version control.
3. **Loopback by Default:** The A2A server defaults to `127.0.0.1`. Remote network binding requires explicit activation of client authentication (`ENABLE_CLIENT_AUTH=true`) or user authentication (`ENABLE_USER_AUTH=true`).
4. **Wire Format Integrity:** Payloads crossing the agent boundary must match their declared canonical payload hash and be within their time-to-live (`ttl_ms`) budget.
5. **No Live Side Effects:** MCP connectors remain disabled (`enabled: false`) until Phase 4 allowlist reviews.

---

## 3. Testing & Verification

Comprehensive offline unit tests are located in `a2a/tests/security/`:
- `test_redactor.py`: Token format, session determinism, cross-session salt isolation, idempotency, credential detection, and detokenization.
- `test_wire_validator.py`: Envelope schema checks, TTL expiration rejection, canonical hash verification, and message size limits.
- `test_bind_guard.py`: Loopback verification and fail-closed rejection of unauthenticated non-loopback bindings.

Run the test suite:
```bash
cd portable/terraform-support-agent/a2a
PYTHONPATH=. python3 -m unittest discover -s tests -t . -v
```
