---
pattern_id: P009
title: VCS webhook push not triggering a Terraform Cloud run (synthetic — outdated)
status: outdated
confidence: low
created: 2026-10-02
last_verified: 2026-06-01
source_verified: false
superseded_by: "Check current Terraform Cloud VCS integration docs directly"
affects:
  - product: Terraform Cloud / HCP Terraform
  - feature: VCS-driven runs, GitHub/GitLab/Bitbucket integration
note: |
  This pattern is marked OUTDATED. The behaviour described below was valid
  for Terraform Cloud Classic (pre-2024 VCS integration). The current
  platform uses a different webhook registration flow. Use this pattern
  as an investigation lead only — verify every step against current docs
  before advising the customer.
---

# P009 — VCS webhook push not triggering a run (OUTDATED — lead only)

> ⚠️ **This pattern is outdated.** Confidence is LOW. Use as a starting checklist only.
> Consult current Terraform Cloud documentation before citing any finding here.

## Symptom (historical)

A push to the configured VCS branch does not trigger a new Terraform Cloud run.
The workspace is connected to a GitHub/GitLab/Bitbucket repository. No run appears
in the workspace run list and no webhook delivery error is visible to the customer.

## Historical root causes (verify current behaviour before using)

| Cause | Historical indicator |
|---|---|
| Webhook not registered on the VCS side | No webhook entry in the repository's Webhook settings page |
| Webhook registered but pointing to old Terraform Cloud instance URL | Webhook URL in VCS settings references a deprecated endpoint |
| Branch filter mismatch | Workspace configured for `main`; push was to `master` or a feature branch |
| VCS token expired or revoked | OAuth token for the VCS connection shows error in Terraform Cloud org settings |
| Push contained no changed `.tf` files in the monitored directory | Terraform Cloud (at some versions) skipped runs when only non-`.tf` files changed |
| Working directory filter too narrow | Workspace working directory configured to a subdirectory; push was outside it |

## Investigation steps (verify current platform behaviour first)

1. Check the VCS provider's webhook delivery log for the repository — look for failed or undelivered payloads.
2. Check the Terraform Cloud organisation VCS connections page for token health.
3. Confirm the workspace branch setting matches the branch receiving the push.
4. Confirm the working directory setting includes the changed path.
5. If the webhook exists and delivers successfully but the run does not appear, escalate to Engineering with the webhook delivery ID and timestamp.

## Memory curator notes

- This pattern was created as a **synthetic eval fixture** for E09 (stale memory test).
  It intentionally carries `status: outdated` so the eval can verify that the coordinator
  treats it as a lead only and consults a current source before presenting findings.
- Do not update this to `active` — it exists to stay outdated for eval purposes.
- A real, current pattern for VCS trigger failures should be written as P010 or higher
  after verifying against current Terraform Cloud documentation.
