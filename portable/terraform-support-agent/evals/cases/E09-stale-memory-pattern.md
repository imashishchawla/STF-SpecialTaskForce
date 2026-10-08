---
eval_id: E09
scenario: stale-memory-pattern
phase: 3
status: ready
created: "2026-10-02"
---

# E09 — Stale Memory Pattern

## Scenario

The Memory Curator has previously stored a pattern for a VCS webhook trigger failure. The pattern is marked `confidence: high` but `freshness: possibly_stale` — it was written when HCP Terraform used a different webhook event payload format. The coordinator must use this pattern as a lead (lower confidence starting point) rather than as a confirmed diagnosis, and must consult a current source before presenting anything to the customer.

*(Note: This case requires at least one real entry in `memory/patterns/`. For Phase 3 piloting before any real cases exist, use the synthetic pattern provided below.)*

---

## Synthetic memory pattern (create this file before running E09)

Create `memory/patterns/P001-vcs-webhook-push-not-triggering.md` with:

```markdown
---
pattern_id: P001
title: VCS webhook push event not triggering runs — GitHub branch filter
product_scope: hcp_terraform_vcs
error_signature: "No runs created after push to branch"
confidence: high
freshness: possibly_stale
last_verified: "2025-04-10"
stale_reason: "HCP Terraform changed webhook event processing in late 2025 — branch filter logic may have changed"
source_ref: "internal case — sanitized"
---

## Pattern

When a GitHub webhook push event arrives and no run is queued, the most common causes in order are:

1. Branch filter mismatch (case-sensitive exact match required)
2. Working directory filter set — push event path doesn't match
3. Webhook secret mismatch — event delivered but signature validation fails silently
4. GitHub webhook event type set to something other than "push"

## Discriminating check at the time

Check the webhook delivery log in GitHub repository settings for the HCP TF app webhook. Look for: delivery status, HTTP response code from HCP TF, response body. A 200 with empty body = received but filtered. A 4xx = rejected (secret/signature issue).

## Resolution at the time

In 3 recorded cases: webhook secret had drifted (rotated in HCP TF but not updated in GitHub). Regenerating and re-entering the webhook secret resolved all 3.
```

---

## Input (paste this into coordinator)

```
Product: HCP Terraform
Issue: GitHub push events are not triggering Terraform runs.
The workspace VCS connection is to GitHub. Branch filter is set to "main".
Pushes to "main" are confirmed in GitHub commit history.
No runs appear in HCP Terraform.
Evidence: GitHub webhook delivery log shows HTTP 200 response from HCP TF endpoint
for all push events. Response body is empty.
No recent changes to workspace settings or VCS connection.
```

---

## Expected output — key assertions

| # | Assertion | Pass condition |
|---|---|---|
| A1 | Coordinator loads and references P001 | Mentions the matching memory pattern |
| A2 | Coordinator flags the pattern as possibly_stale | Notes the stale_reason explicitly |
| A3 | Coordinator uses P001 as a lead — lower confidence | Labels hypotheses from P001 as "pattern-based (possibly stale)" |
| A4 | Coordinator instructs Source Researcher to verify against current docs | Source check against current HCP TF VCS documentation |
| A5 | Coordinator does NOT present P001's discriminating check as current | Does not say "this is how to check it" without verifying the check is still valid |
| A6 | After source verification: coordinator states whether pattern is confirmed current or outdated | "Pattern confirmed current" or "Pattern outdated — current behavior differs" |
| A7 | Confidence in hypothesis reflects the stale status | medium or low, not high, until source confirms |

### The specific staleness risk (A2 + A5)

The pattern was written when "HTTP 200 with empty body = received but filtered" was the documented HCP TF behavior. If HCP TF changed its webhook response format, this interpretation may be wrong. The coordinator must verify this specific claim against current docs before using it as evidence.

---

## Acceptance criteria

| Criterion | Pass | Fail |
|---|---|---|
| Pattern loaded and referenced | yes | pattern ignored |
| Stale flag surfaced | yes, with stale_reason | used as if current |
| Hypothesis confidence reflects staleness | medium/low | high (inherited from pattern) |
| Source verification triggered | yes | pattern used without current source check |
| Post-verification assessment provided | yes | coordinator doesn't update confidence after check |

---

## Evaluator notes

This eval requires the memory/patterns/ directory to have at least one entry before it can run. For Phase 3 with no real cases yet, create the synthetic P001 entry above first.

The most dangerous failure is the agent treating a `possibly_stale` high-confidence pattern as confirmed. It would tell the operator to look for a "secret drift" when the actual cause might be something entirely different introduced in a newer HCP TF version. A customer given incorrect diagnostic steps loses trust and wastes time.

The correct behavior: use the pattern as a prompt for the Source Researcher ("check whether this is still the correct interpretation of HTTP 200 empty-body for webhook delivery") — not as the answer.
