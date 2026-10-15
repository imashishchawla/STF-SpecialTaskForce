# Visa Agent

This workspace contains the [Visa Agent role](./.agents/visa-agent.md), specialist instructions in `.agents/`, an AES-256 encrypted vault, and a local SQLite profile workflow. The legacy model and MCP paths are disabled; a purpose-limited model packet builder is available without a configured provider.

## Strict Case Storage Rule (MANDATORY)

**Never keep client checklists, fee schedules, roadmaps, CVs, or personal files in the agent root directory (`portable/Visa-Agent/`).**  
All client cases, databases, roadmaps, and documents are stored exclusively in the git-ignored private directory:
```
.profile/<client-name>/
├── profile.json       # Case metadata (0600)
├── state.sqlite3      # Local SQLite database (0600)
├── .vault.key         # AES-256 encryption key (0600)
├── vault.enc          # Encrypted token-to-PII vault (0600)
├── documents/         # Uploaded client documents (0600)
└── roadmaps/          # Case roadmaps, fee schedules, and master checklists
```

## Quick Start & Profile Commands

To manage profiles locally:
```sh
# List all active profiles
python3 profile.py list

# Inspect profile metadata and database state
python3 profile.py show Asha_Example

# Check local encrypted vault availability without printing values
python3 decrypt_vault.py Asha_Example
```

## Local salary slip validation

Run `python3 audit_salary_slips.py` to scan private profile PDFs with local `pdftotext`. It prints aggregate counts only: candidates, text extraction failures, file permission failures, and presence of financial or contact fields. It does not print names, paths, amounts, or document text. Classification is based on filenames and text markers; it does not authenticate employer records or validate figures. The local CLI and `runtime.tools` calculations remain available for manual use. `mcp.json` contains no active servers, and `mcp_server.py` exposes no tools; the vault decryption CLI is for direct local terminal use only.

## Purpose-limited model packets

`runtime/safe_egress.py` provides `prepare_packet(profile_dir, task, selected_facts)` and `send_prepared_packet(packet, model_caller)`. The caller selects only the task's fixed fields after local document validation. `salary_evidence` sends a month, currency, payment mode, and locally computed booleans; it never sends amounts or document text. Employer and employee names and IDs become random `XCVBH` tokens. `identity_check` can tokenize a name, phone, email, passport number, or employee ID. The mapping is encrypted in that profile's `llm-vault.enc`; the key is stored in `.llm-vault.key`, both mode `0600`. Profile and vault CLIs omit names and decrypted values by default. No model provider is configured. See [privacy egress workflow](./PRIVACY_EGRESS.md) before adding one.

## Client Profiles

Client profiles reside exclusively in the local `.profile/` directory (git-ignored, `0700`/`0600` permissions) created via `python3 profile.py create`. Real client case data, CVs, and documents never enter repository tracking.
