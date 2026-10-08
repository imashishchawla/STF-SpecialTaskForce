---
pattern_alias: P002-ado-webhook-missed
schema_version: 1
status: candidate
category: vcs
product_scope: hcp_terraform
affected_versions: "all"
last_reviewed: "2026-10-02"
---

# Pattern P002 — Azure DevOps Webhook Missed Events

## Error fingerprint
- Workspace connected to Azure DevOps does not trigger a run on push
- No run appears in the HCP Terraform Runs tab after a commit
- No error — just silence

## Trigger conditions
- Azure DevOps push event format differs from expected webhook payload
- Branch filter in workspace settings does not match the pushed branch (e.g. `main` vs `refs/heads/main`)
- Service hook in Azure DevOps was deleted or expired
- ADO project or repo was renamed — webhook URL became stale

## Supporting observations
- Azure DevOps Service Hooks delivery logs show no delivery, or show a failed delivery
- Other VCS providers (GitHub, GitLab) on the same HCP TF org trigger runs normally
- Issue is branch-specific (only some branches miss triggers)

## Conflicting evidence
- If ADO delivers the webhook but HCP TF still doesn't queue a run → check workspace trigger settings and run triggers filter
- If all pushes work except from one user → check ADO user permissions on the repo

## Discriminating check
Ask: "Can you check Azure DevOps → Project Settings → Service Hooks → find the HCP Terraform hook → view Recent Deliveries? What does the last delivery attempt show?"

## Confirmed cause status: unconfirmed (candidate)

## Remedy (if confirmed)
1. Re-create the service hook in Azure DevOps with the correct HCP Terraform webhook URL
2. Verify the branch filter matches exactly (include `refs/heads/` prefix if required by ADO)
3. Test with a manual push to the configured branch
4. Rollback: no state changes — safe

## Source references
- Ref: https://developer.hashicorp.com/terraform/cloud-docs/vcs/azure-devops-services
- Ref: https://learn.microsoft.com/en-us/azure/devops/service-hooks/services/webhooks

## Confidence explanation
Candidate only. ADO webhook behaviour varies by project configuration. Requires delivery log inspection to confirm.
