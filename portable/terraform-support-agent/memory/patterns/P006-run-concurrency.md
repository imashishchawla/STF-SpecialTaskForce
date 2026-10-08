---
pattern_id: P006
title: Concurrent Terraform runs fail with state lock error
status: active
confidence: high
created: 2026-10-02
last_verified: 2026-10-02
source_verified: false
affects:
  - product: Terraform Cloud / HCP Terraform
  - feature: Remote state backend, run queue
---

# P006 — Concurrent Terraform runs fail with state lock error

## Symptom

Customer reports: two `terraform plan` or `terraform apply` runs triggered at almost the same time (CI pipeline + manual run, or two pipeline branches) and one fails immediately with a state lock error such as:

```
Error: Error locking state: Error acquiring the state lock:
  ConflictException: 429: run is already in progress
```

or

```
Error: error locking state: resource locked (run run-xxxxxxxxxxxxxxxx is holding the state lock)
```

## Root cause

Terraform requires an exclusive write lock on the state file for any operation that may change state. When two runs target the same workspace simultaneously, the second run cannot acquire the lock held by the first and fails immediately. This is expected protective behaviour, not a defect.

**Common triggers:**
- CI pipeline automatically queues a plan on push while an engineer manually triggers a run in the UI
- Two branches merge to the same protected branch within seconds of each other
- Scheduled destroy + scheduled plan overlap in the same workspace

## Discriminating checks

1. **Confirm this is a lock conflict** — error message contains `ConflictException`, `state lock`, or `resource locked`, **not** a permissions error or a state migration error.
2. **Identify the holding run** — the error message includes the holding run ID (`run-xxxxxxxxxxxxxxxx`). Look it up in the workspace run list to confirm it is still active or has just finished.
3. **Check if concurrency is intentional or accidental** — review the CI trigger configuration and compare timestamps of both runs.

## Next actions

| Scenario | Recommended action |
|---|---|
| Both runs are legitimate but overlapping | Enable run queue (Terraform Cloud queues runs automatically; the second run waits rather than failing). Verify `execution_mode` is not set to `local` which bypasses the queue. |
| One run is a stale/hung run holding the lock | Use the Terraform Cloud UI or API to force-cancel the stuck run, then re-trigger. Never use `terraform force-unlock` on remote state unless Engineering confirms it is safe. |
| CI and manual runs collide regularly | Enforce a single-trigger policy: disable manual runs in the workspace while CI is the source of truth, or use workspace tags to route CI vs manual to separate workspaces. |
| Lock error appears on a fresh workspace with no active runs | Check for orphaned locks from a previous interrupted run. Escalate to Engineering if the workspace shows no active run but the lock persists. |

## References

- Terraform Cloud docs — Run states and stages: `https://developer.hashicorp.com/terraform/cloud-docs/run/states` ⚠️ URL not verified in this session
- Terraform Cloud docs — Concurrency model: `https://developer.hashicorp.com/terraform/cloud-docs/workspaces/concurrency` ⚠️ URL not verified in this session

## Memory curator notes

- Do not conflate with P004 (state lock from `terraform apply` interruption on a local backend). P006 is specific to remote/cloud backends where the queue mechanism is available.
- Update `last_verified` and `source_verified` after confirming against current Terraform Cloud documentation.
