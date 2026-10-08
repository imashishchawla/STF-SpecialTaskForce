---
pattern_alias: P001-vcs-oauth-expiry
schema_version: 1
status: candidate
category: authentication_authorization
product_scope: hcp_terraform
affected_versions: "all"
last_reviewed: "2026-10-02"
---

# Pattern P001 — VCS OAuth Token Expiry

## Error fingerprint
- Run triggered from VCS returns: `could not clone repository` or `unauthorized` at plan queue
- VCS webhook delivers successfully (200 in webhook logs) but plan never starts or fails immediately
- No recent code changes — issue appeared suddenly

## Trigger conditions
- OAuth token used by HCP Terraform to access VCS provider has expired or been revoked
- User who authorized the OAuth connection left the org or had permissions changed
- VCS provider enforced a token rotation policy

## Supporting observations
- Run log shows authentication failure before any Terraform operation
- Webhook delivery logs in VCS show successful delivery
- Other workspaces on the same OAuth connection may also be affected

## Conflicting evidence
- If only one workspace fails while others on same OAuth connection succeed → not this pattern (check workspace-specific repo path or branch config instead)

## Discriminating check
Ask: "Can you check HCP Terraform → Settings → VCS Providers → [your VCS] → verify OAuth connection status? Has the authorizing user's account or org membership changed recently?"

## Confirmed cause status: unconfirmed (candidate — requires evidence match)

## Remedy (if confirmed)
1. Re-authorize the OAuth connection: HCP Terraform → Settings → VCS Providers → [provider] → Update OAuth Token
2. Or create a new machine/service account OAuth connection with long-lived credentials
3. Rollback: no state changes involved — safe to retry after re-auth

## Source references
- Ref: https://developer.hashicorp.com/terraform/cloud-docs/vcs
- Ref: https://developer.hashicorp.com/terraform/cloud-docs/vcs#updating-an-oauth-token

## Confidence explanation
Candidate only. Pattern matches common symptom cluster. Requires operator to verify OAuth connection status and confirm authorizing user is still active.
