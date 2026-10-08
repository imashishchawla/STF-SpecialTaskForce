# checkpoints/

Case-by-case sanitized investigation records. One checkpoint file per case per pass.

**Naming**: `<case_alias>-pass-<n>.md`  
**Example**: `case-2026-001-pass-1.md`

## What a checkpoint contains

- Sanitized case timeline
- Confirmed observations and ranked hypotheses (with confidence)
- Approved actions taken (with audit records)
- Current stage and next action
- Blockers (if any)
- Sub-agent task packets and outputs (sanitized)

## What a checkpoint must never contain

- Customer names, emails, or usernames
- Org names, workspace names, workspace IDs (`ws-*`)
- Run IDs (`run-*`), plan IDs, task IDs
- Authentication tokens, API keys, secrets of any kind
- Raw state file content or full plan JSON
- Raw log content (redacted summaries only)

## Write rules

- Draft checkpoints land in `draft/` during a coordinator pass.
- Promotion from `draft/` to `checkpoints/` requires operator approval.
- Only the coordinator proposes checkpoint writes. Sub-agents do not write here.

## Empty — populated as real cases are worked.
