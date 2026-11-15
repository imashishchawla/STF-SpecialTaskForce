# Searchable knowledge base

Markdown is the source of truth. Use host file search or `rg` to search by credential name, issuer, category, alias, skill, exam code, and version. Search the existing index and records before proposing a new one.

## Lifecycle and locations

- `index.md`: categories, historical leads, and links to accepted public records.
- `policies/`: source authority and record lifecycle rules.
- `updates/<task-id>/`: isolated proposals from a run or subagent. Workers never edit canonical records.
- Public accepted records: the Hugo website repository's approved credential section, one Markdown record per credential. Do not make a second canonical copy here.

Use `export/templates/credential-record.md` for each proposal and `export/templates/research-result.md` for run notes. Keep each update self-contained and link its evidence. The curator merges serially after independent review; keep a concise change note and do not discard prior evidence when a claim changes.

## Search/update protocol

1. Search IDs, names, aliases, issuers, exam codes, categories, and tags.
2. Compare stable identity and version; if duplicate, update or supersede the existing record instead of creating another.
3. Create a unique task folder and bounded worker assignments. Each worker uses a separate file; no simultaneous edits to the same record.
4. Review evidence and status transitions before merge. Preserve conflicts and provenance.
5. Keep user-specific recommendation data run-scoped unless the user explicitly requests storage.

Do not put secrets, private account data, raw prompts, or personal data in the catalog or run notes.
