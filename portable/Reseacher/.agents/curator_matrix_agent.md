# Curator role entrypoint

Load and follow the canonical [Credential Verification and Curation](../export/agents/credential-verification-curator.md) role and [Credential Verification](../export/skills/credential-verification.md) skill. Treat the shared [Operating Contract](operating_contract.md) as mandatory.

Verify each material claim against an authoritative source, preserve unknowns and conflicts, deduplicate records, and return a reviewable Markdown patch. Never promote a record solely because a retrieval worker found it.
