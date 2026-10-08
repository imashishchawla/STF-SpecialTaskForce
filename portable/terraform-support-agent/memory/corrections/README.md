# memory/corrections/

Accepted corrections — operator-approved updates that supersede prior hypotheses or conclusions on a specific topic.

## When a correction is recorded

1. The operator explicitly corrects a finding ("That's wrong — the actual cause was X").
2. Engineering confirms a different root cause than the coordinator proposed.
3. A new release or doc update contradicts a conclusion in an existing pattern.

## Schema (YAML front matter)

```yaml
---
correction_id: <slug>
schema_version: 1
topic: <short description of what is being corrected>
supersedes_pattern: <pattern_alias or null>
correction_date: "YYYY-MM-DD"
corrected_by: operator | engineering | source_update
source_ref:
  title: "<source>"
  url: "<full URL or internal reference>"
  retrieved: "YYYY-MM-DD"
---
```

## Rules

- A correction supersedes any earlier hypothesis or conclusion on the same topic.
- The coordinator always checks this directory before finalising a hypothesis on a case with prior history.
- Corrections are proposed by the Memory Curator and approved by the operator before writing.

## Empty — populated as corrections are accepted during real case work.
