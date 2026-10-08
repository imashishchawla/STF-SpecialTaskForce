---
pattern_id: P007
title: Variable set not applied — workspace variable overrides variable set silently
status: active
confidence: high
created: 2026-10-02
last_verified: 2026-10-02
source_verified: false
affects:
  - product: Terraform Cloud / HCP Terraform
  - feature: Variable sets, workspace variables
---

# P007 — Variable set not applied — workspace variable overrides variable set silently

## Symptom

Customer reports: a variable set is assigned to a workspace (or globally), but the Terraform run uses the wrong value — specifically, the old value rather than the one set in the variable set. No error is raised. The customer confirms the variable set is attached to the workspace in the UI.

Alternatively: the customer updated a variable's value in a variable set and expects all attached workspaces to pick it up, but runs continue to use the previous value.

## Root cause

Terraform Cloud applies a **precedence hierarchy** for variables. A workspace-level variable of the same name and category (`terraform` or `env`) **silently overrides** a variable set value. The variable set is technically active, but its value is masked.

Precedence order (highest wins):
1. Workspace-specific variable (UI or API)
2. Variable set — ordered by priority if multiple sets define the same variable
3. Default value in the Terraform configuration (`default` block in `variables.tf`)

There is no warning when a workspace variable shadows a variable set entry.

## Discriminating checks

1. **Check for a workspace-level variable of the same name** — in the workspace settings → Variables tab, look for a variable with the same key as the one in the variable set. If it exists, it is the active value regardless of the variable set.
2. **Check variable category** — a `terraform` category variable set entry does not override an `env` category workspace variable and vice versa. Confirm both category and key match.
3. **Check variable set priority** — if multiple variable sets define the same key, confirm which set has higher priority in the organisation variable set list.
4. **Check variable set scope** — confirm the variable set is assigned to this specific workspace (not just a different workspace or project within the same org).

## Next actions

| Scenario | Recommended action |
|---|---|
| Workspace variable shadows variable set | Delete or rename the workspace-specific variable if the variable set value is intended to be canonical. If both are needed, document which takes precedence. |
| Multiple variable sets define the same key | Adjust priority order in the organisation variable sets list, or consolidate conflicting sets. |
| Variable set recently updated but not picking up | Force a new run (changes to variable set values do not trigger runs automatically). Confirm the new value is visible in the workspace's effective variables view. |
| Variable set is scoped to a project but workspace is not in that project | Re-assign the variable set or move the workspace into the appropriate project. |

## References

- Terraform Cloud docs — Variable precedence: `https://developer.hashicorp.com/terraform/cloud-docs/workspaces/variables#precedence` ⚠️ URL not verified in this session
- Terraform Cloud docs — Variable sets: `https://developer.hashicorp.com/terraform/cloud-docs/workspaces/variables/managing-variables#variable-sets` ⚠️ URL not verified in this session

## Memory curator notes

- This pattern is frequently misreported as a "variable set not working" bug. The root cause is almost always silent workspace-level override.
- Update `last_verified` and `source_verified` after confirming against current Terraform Cloud documentation.
