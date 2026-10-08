---
schema_version: 1
last_updated: "2026-10-02"
maintainer: operator
---

# Time Estimate Calibration

Tracks operator-corrected time estimates for recurring task types.
The agent reads this file before producing any time estimate and recalibrates accordingly.

Rules:
- `agent_estimate` = what the agent initially estimated
- `operator_actual` = what the operator said the actual time was (correction)
- When `operator_actual` is set, use it as the calibrated value for future estimates of that `task_type`
- Entries with no `operator_actual` are agent defaults only — treat as rough guides

---

## Estimates

### Email Drafting

| task_type | description | agent_estimate | operator_actual | notes |
|---|---|---|---|---|
| `draft-initial-reply` | First customer reply — acknowledgment, clarifying question | 10m | — | |
| `draft-investigation-update` | Mid-case customer reply with findings | 15m | — | |
| `draft-closure` | Closure email with survey line | 10m | — | |
| `draft-handoff` | Internal shift handoff | 15m | — | |
| `draft-rca` | Root cause analysis document | 30m | — | |
| `draft-can` | Customer Advocacy Notification | 20m | — | |
| `draft-kb` | Customer-facing KB article | 45m | — | |

### Configuration & Reproduction

| task_type | description | agent_estimate | operator_actual | notes |
|---|---|---|---|---|
| `write-tf-config` | Write a minimal Terraform config for reproduction | 30m | — | |
| `write-provider-config` | Write provider config block with auth | 20m | — | |
| `reproduce-issue` | End-to-end reproduction in isolated workspace | 45m | — | |
| `test-fix` | Apply and verify a suggested fix | 30m | — | |

### Research & Diagnosis

| task_type | description | agent_estimate | operator_actual | notes |
|---|---|---|---|---|
| `source-check` | Verify one claim against official docs | 10m | — | |
| `log-analysis` | Analyse run logs and produce ranked hypotheses | 20m | — | |
| `full-case-diagnosis` | Complete first-pass diagnosis from intake to hypotheses | 45m | — | |

---

## How to record a correction

When the operator says "that took X minutes, not Y":

1. Locate the matching `task_type` row above.
2. Fill in `operator_actual` with the corrected value.
3. Add a note explaining the context (e.g. "simple case with full logs provided").

The agent will use `operator_actual` as the calibrated estimate on the next occurrence of that task type.
Entries accumulate over time — do not delete old rows; add new rows for different conditions.
