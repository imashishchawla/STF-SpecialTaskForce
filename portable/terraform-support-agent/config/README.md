# config/ — Runtime configuration

This directory holds **non-secret** runtime settings for the Terraform Support Agent. These files are safe to commit because they contain no credentials, tokens, or customer-identifying data.

## Files

| File | Purpose |
|---|---|
| `runtime.yaml` | Token budgets, tool permissions, retry limits, confidence thresholds |

## What belongs here

- Token budget limits per coordinator pass
- Maximum retry counts for tools
- Confidence thresholds that control when the coordinator escalates vs proceeds
- Tool permission allowlist overrides (Phase 4+)
- Feature flags for capabilities gated behind a phase

## What does NOT belong here

- API keys, tokens, or credentials → use `.env` (gitignored) or the OS keychain
- Customer data or case-specific settings → use `checkpoints/`
- Operator personal preferences (signature, tone) → use `memory/preferences.md`

## Editing

Changes to `runtime.yaml` take effect on the next coordinator invocation. The coordinator reads this file at session start. If the file is absent or malformed, the coordinator uses built-in defaults and logs a warning.

All changes should be proposed by the agent and approved by the operator before committing. Do not commit values that differ materially from the documented defaults without recording an ADR in `.memory/decisions.md`.
