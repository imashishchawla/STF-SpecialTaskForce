# memory/

This directory holds all persistent agent knowledge. **No agent writes here directly.** The Memory Curator proposes; the operator approves before any file is created or modified.

## Areas

| Sub-directory | Contents | Write authority |
|---|---|---|
| `patterns/` | Sanitized issue patterns (error fingerprint, cause, remedy, confidence) | Human-approved only |
| `ops/` | Internal process references (registry routing, entitlement conditions, escalation paths) | Human-approved only |
| `corrections/` | Accepted corrections with provenance — supersede prior hypotheses | Human-approved only |
| `preferences.md` | Operator style, signature, diagnostic habits | Human-approved only |

## Rules

- Never add customer names, org/workspace/run IDs, tokens, raw logs, or raw state to any file here.
- All memory entries carry a `confidence` field: `candidate | validated | outdated | rejected`.
- The coordinator checks `corrections/` before finalising any hypothesis on a case with prior history.
- The Memory Curator checks `patterns/` for duplicates before proposing a new entry.
