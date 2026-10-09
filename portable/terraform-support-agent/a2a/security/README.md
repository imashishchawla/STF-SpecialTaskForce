# A2A security module

**Status: design only.** This directory has no enforcement code yet. The current A2A scaffold must not receive real customer cases or be exposed beyond an isolated test. The [active plan](../../plan/portability-readiness-plan.md) makes this module a required gate before A2A startup.

## Required boundary

- Validate the request identity, schema, size, and correlation before passing content to the coordinator.
- Detect and replace sensitive strings before any LLM call using the XCVBH scheme in [design 08](../../docs/design/08-pii-protection-and-encryption.md). Store mappings only in a local encrypted vault outside the exported bundle; never put vault values in model context or messages.
- Bridge A2A messages to the repository's separate SignedEnvelope contract only after its [design 09](../../docs/design/09-inter-agent-wire-format.md) checks pass. A2A transport does not itself enforce STF policy.
- Bind to `127.0.0.1` by default. Reject non-loopback startup unless authentication, transport protection, and network policy are explicitly configured and reviewed.
- Keep MCP, case writes, external messages, Terraform execution, and memory promotion disabled until their separate gates pass.

The planned package should contain focused redaction/vault, inbound-validation, and bind/auth modules with tests in `a2a/tests/security/`. Startup must fail closed when a required check is missing. Do not claim that the current `main.py` or installer already provides these controls.
