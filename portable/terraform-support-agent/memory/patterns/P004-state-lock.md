---
pattern_alias: P004-state-lock
schema_version: 1
status: candidate
category: state_and_locks
product_scope: hcp_terraform
affected_versions: "all"
last_reviewed: "2026-10-02"
---

# Pattern P004 — State Lock / Pending State Upload

## Error fingerprint
- Run fails with: `Error acquiring the state lock`, `state is locked`, or `pending state upload`
- A previous run appears stuck in `applying` state in the Runs tab
- New runs cannot queue or immediately fail

## Trigger conditions
- A previous run was interrupted mid-apply (network drop, timeout, agent restart)
- State upload to HCP TF backend failed — lock was not released
- A manual `terraform apply` run outside HCP TF left a local lock file in the remote backend
- Two runs were triggered simultaneously on a workspace without run queue

## Supporting observations
- HCP TF Runs tab shows a run stuck in `applying` for longer than expected
- State version in the workspace is not advancing
- Customer reports the workspace was working and then "froze"

## Conflicting evidence
- If the workspace has never been applied — state lock cannot exist (check workspace config instead)
- If the error is `state version conflict` (not `locked`) → different issue: concurrent run or version mismatch

## Discriminating check
Ask: "In HCP Terraform → Workspace → Runs, is there a run currently in 'Applying' or 'Pending' state? If so, what is the Run ID and when did it start?"

## Confirmed cause status: unconfirmed (candidate)

## Remedy (if confirmed — requires care)
⚠️ Force-unlock is potentially destructive. Confirm the stuck run is truly orphaned before unlocking.

1. Attempt to discard the stuck run from the HCP TF UI first (safest)
2. If the run cannot be discarded: take a state backup first
   - HCP TF → Workspace → States → download the current state version
3. Force-unlock: `terraform force-unlock <LOCK_ID>` from CLI with appropriate credentials
4. Verify the workspace state is consistent after unlock: `terraform state list`
5. Rollback: restore state from the backup downloaded in step 2 if needed

## Source references
- Ref: https://developer.hashicorp.com/terraform/cloud-docs/workspaces/state
- Ref: https://developer.hashicorp.com/terraform/cli/commands/force-unlock

## Confidence explanation
Candidate only. Force-unlock is high-risk — must confirm the stuck run is genuinely orphaned and not still executing before proceeding.
