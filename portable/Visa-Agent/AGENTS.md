# Visa Agent workspace

The project agent is [Visa Agent](./.agents/visa-agent.md). Read that file, the [shared operating contract](./.agents/operating_contract.md), and the relevant specialist only when its subject is needed. The [master workflow](./MASTER_WORKFLOW_PROMPT.md) provides broader research guidance. Use the local [profile workflow](./PROFILE_WORKFLOW.md) to create and reopen client profiles.

## Strict Case Isolation & PII Boundaries (MANDATORY)

- **Never write case data to the root directory**: Checklists, roadmaps, fee schedules, CVs, and identity records must **NEVER** be stored in the agent root directory (`portable/Visa-Agent/`).
- **All case materials live in `.profile/<client-name>/`**: Each client has an isolated, git-ignored workspace with restrictive file permissions (`0700`/`0600`).
- **Encrypted local vaults**: Existing redaction mappings remain in `vault.enc`. Model-bound identity aliases use random `XCVBH` tokens and a separate AES-256-GCM `llm-vault.enc` inside the selected profile. Keys and mappings stay local.
- **Outbound egress**: Never put raw profile files, paths, document text, identifiers, or free-form case notes into a model prompt, tool result, public search, or MCP call. Select only fields permitted by `runtime/safe_egress.py`, then use `prepare_packet()` and `send_prepared_packet()`. Reject any unlisted field. Do not treat `check_egress_safety()` alone as proof of safety.

## Tools & Execution Infrastructure

- **MCP Server (`mcp_server.py`)**: Disabled for case work; `mcp.json` has no active servers. Use local Python tools directly.
- **Model gateway (`runtime/safe_egress.py`)**: Sends purpose-limited structured packets through a caller supplied model function. Legacy free-form model calls in `runtime/llm.py` remain disabled.
- **Inter-Agent Wire Protocol (`runtime/wire.py`)**: `SignedEnvelope` records and document pointers are local-only. Their `.profile/...` paths and hashes must never be copied into a model prompt or external message.
- **Profile and vault CLIs**: Default output omits names, paths, and decrypted values. `--reveal` requires a direct interactive terminal; agents must not run it or pass real profile folder names through tool calls.

