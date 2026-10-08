---
correction_id: C001-yaml-comment-inference
schema_version: 1
topic: Agent must not infer operator_name from YAML front matter comments
supersedes_pattern: null
correction_date: "2026-10-02"
corrected_by: operator
source_ref:
  title: "Session observation — operator caught incorrect name inference"
  url: "local/session"
  retrieved: "2026-10-02"
---

# Correction C001 — YAML Comment Inference Bug

## What was wrong

On session initialisation, the agent read `memory/preferences.md` and found:

```yaml
operator_name: ""  # Populated by onboarding.sh — full name (e.g. "Ashish Chawla")
```

The agent incorrectly extracted `"Ashish Chawla"` from the **comment text** and used it as the
operator name in the greeting response. The field value was an empty string `""`.

## Correct behaviour

- `operator_name` must only be resolved from the **YAML field value** (the string after the colon).
- If the field value is empty string `""` or missing, the agent must treat it as **unset**.
- Comments (text after `#`) are documentation only — never parsed as values.
- When `operator_name` is unset, the intake skill onboarding check must trigger:
  > "What is your full name? (This will be used in all communication drafts.)"

## Rule added

> **RULE C001**: Before using `operator_name` (or any preferences field) in any output,
> assert `field_value != ""` AND `field_value != null`. If either condition fails, treat as
> unset and trigger the intake onboarding check. Never read values from YAML comments.

## Scope

Applies to: all front matter fields in `memory/preferences.md` —
`operator_name`, `operator_title`, `operator_availability`, `agent_repo_path`, and all others.
