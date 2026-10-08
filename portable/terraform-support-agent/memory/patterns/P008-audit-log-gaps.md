---
pattern_id: P008
title: Audit log gaps — agent or run events missing from organisation audit trail
status: active
confidence: medium
created: 2026-10-02
last_verified: 2026-10-02
source_verified: false
affects:
  - product: Terraform Cloud / HCP Terraform (Plus/Enterprise tier)
  - feature: Audit logging
---

# P008 — Audit log gaps — agent or run events missing from organisation audit trail

## Symptom

Customer (typically a security team member or compliance engineer) reports that the Terraform Cloud audit log is missing expected events. Common examples:

- A workspace was deleted but there is no audit log entry for the deletion.
- A run was applied by a service account but the log shows a different actor or no actor.
- Agent pool events (e.g. agent registration, token revocation) are not appearing.
- The audit log export for a date range is incomplete compared to the run history.

## Root cause

Audit log gaps can have several distinct causes. Do not assume a single root cause without checking:

| Cause | Indicator |
|---|---|
| **Tier limitation** — audit logging is a Plus/Enterprise feature | Organisation is on Free or Plus (older) tier without the feature flag |
| **Streaming lag** — audit events are delivered with a delay to external SIEM or log destination | Gap is time-limited; events appear after a few minutes |
| **Export filter too narrow** — the export query excludes the event type or actor | Events exist in the audit trail but were filtered out during export |
| **Service account actor not matching expected identity** — team member ran action via Terraform CLI with cached token for a service account | Actor in log is the service account, not the human; both are correct |
| **Agent-initiated actions not attributed to run** — network agent applies a run; the log entry shows the agent token identity, not the workspace or user | Expected; agents act under agent pool token identity |
| **Event type not covered** — some platform events (e.g. internal infrastructure events) are not surfaced in the customer-visible audit log | Outside the audit log scope by design |

## Discriminating checks

1. **Confirm the organisation tier includes audit logging** — navigate to Organisation Settings → Plan & billing. Audit logging requires Plus or Enterprise (check current tier naming as HashiCorp has updated tiers). ⚠️ Verify current tier names from official docs before advising the customer.
2. **Check the time window** — confirm the customer is querying a window that has had time to flush (allow at least 5 minutes from event to availability).
3. **Re-run the export with broader filters** — remove any actor, workspace, or event-type filters and re-export to see if the event appears.
4. **Cross-reference run history with audit log** — look up the specific run ID in the workspace run list and check whether the same run ID appears in the audit log with a different actor.
5. **Check if the action was performed via agent** — if an agent pool is configured and runs use remote execution mode, agent actions appear under the agent token identity.

## Next actions

| Scenario | Recommended action |
|---|---|
| Tier does not include audit logging | Confirm tier requirements and advise customer on upgrade path. Do not promise that upgrading will backfill historical events. |
| Events appear after broadening the filter | Help customer adjust their export query or SIEM integration filter to capture all required event types. |
| Agent token is the actor, not expected user | Explain expected behaviour; recommend named agent tokens or agent pool naming conventions to improve traceability if required. |
| Gap is confirmed and reproducible with no filter issue | Escalate to Engineering with: org ID, affected workspace/run IDs, expected event type, time window, and export method used. |

## References

- Terraform Cloud docs — Audit logging: `https://developer.hashicorp.com/terraform/cloud-docs/api-docs/audit-trails` ⚠️ URL not verified in this session
- Terraform Cloud docs — Agents: `https://developer.hashicorp.com/terraform/cloud-docs/agents` ⚠️ URL not verified in this session

## Memory curator notes

- Confidence is `medium` because audit log behaviour changes with tier updates and HashiCorp platform changes; verify against current docs before advising.
- Update `last_verified` and `source_verified` after confirming against current Terraform Cloud documentation.
- This pattern is distinct from P003 (agent connectivity) which covers the agent failing to reach Terraform Cloud, not the audit log of agent actions.
