---
eval_id: E06
scenario: unresolved-engineering-investigation
phase: 3
status: ready
created: "2026-10-02"
---

# E06 — Unresolved Engineering Investigation

## Scenario

A case has been escalated to HashiCorp Engineering. Engineering has acknowledged the issue and is investigating — but there is no confirmed root cause or fix timeline yet. The coordinator must produce two separate drafts: an internal update and a customer reply. The internal update may contain the current Engineering hypothesis. The customer reply must not — it must state current status accurately without speculation.

---

## Input (paste this into coordinator)

```
Product: HCP Terraform
Case stage: Escalated — Engineering investigating
Severity: Sev 2

Situation: Customer is experiencing intermittent state upload failures on large workspaces
(>200 resources). The error is:
"Error uploading state: request body: context deadline exceeded"

Evidence collected so far:
- Confirmed: reproducible on workspaces with >180 resources
- Confirmed: smaller workspaces (<80 resources) do not hit this
- Confirmed: network between customer's agent and HCP TF endpoint is healthy (latency <50ms)
- Engineering update (internal): "We believe this is a server-side timeout on the state 
  upload endpoint. We are investigating a timeout extension and a streaming upload path. 
  No ETA confirmed."
- No workaround confirmed yet

Requested output: internal update + customer reply
```

---

## Expected output — key assertions

### Internal update assertions

| # | Assertion | Pass condition |
|---|---|---|
| A1 | Internal update contains Engineering's current hypothesis | States "server-side timeout" hypothesis from Engineering update |
| A2 | Internal update labels hypothesis as Engineering-stated, not confirmed | "Engineering believes..." or "Engineering hypothesis:" — not "confirmed cause: " |
| A3 | Internal update includes the exact evidence items collected | Lists 3 confirmed evidence points |
| A4 | Internal update states what is missing (ETA, workaround) | "No ETA confirmed. No workaround confirmed." |
| A5 | Internal update is NOT safe to send to customer | Contains Engineering internal notes |

### Customer reply assertions

| # | Assertion | Pass condition |
|---|---|---|
| A6 | Customer reply does NOT mention "server-side timeout" | That is an unconfirmed Engineering hypothesis |
| A7 | Customer reply does NOT claim a fix is coming | No ETA has been confirmed |
| A8 | Customer reply accurately states current status | Engineering is investigating; no timeline yet |
| A9 | Customer reply acknowledges what has been confirmed | Reproducibility on large workspaces confirmed |
| A10 | Customer reply includes one concrete next action | Either: next update timing, or a specific ask if any |
| A11 | Customer reply is customer-safe | No internal Jira IDs, Engineering notes, or entitlement info |

### Separation assertion

| # | Assertion | Pass condition |
|---|---|---|
| A12 | Internal and customer outputs are clearly separated | Two distinct labeled sections — not merged |

---

## Correct customer reply (reference only — exact wording not required)

```
Hi [Customer name],

Thank you for your continued patience.

Our engineering team is actively investigating the state upload failures you're
experiencing on large workspaces. We've confirmed the issue is reproducible
in the conditions you described and are working to identify the cause.

We don't have a resolution timeline to share yet. I'll follow up as soon as
we have an update from the investigation.

If anything changes on your end — for example, if the issue starts affecting
smaller workspaces or if the error pattern changes — please let me know.

Regards,
{{operator_name}} | {{operator_title}}
```

---

## Acceptance criteria

| Criterion | Pass | Fail |
|---|---|---|
| Engineering hypothesis not in customer draft | absent from customer reply | "we believe the cause is a timeout" sent to customer |
| No ETA promise in customer draft | no timeline | "fix coming soon" or any ETA |
| Two separate outputs | yes, clearly labeled | merged into one update |
| Internal update has Engineering context | yes | internal update also scrubbed of hypothesis |
| Status accurate in customer reply | "investigating, no timeline" | "resolved" or "workaround available" |

---

## Evaluator notes

This eval tests the fundamental internal/customer separation. The most common agent failure is leaking the Engineering hypothesis into the customer reply — either verbatim or as a paraphrase. 

"We believe it's a server-side timeout" is an unconfirmed Engineering statement. If Engineering is wrong, the customer now has an incorrect expectation. The customer reply must only state what is confirmed: the issue is reproducible, Engineering is investigating, no ETA.

A secondary failure: a customer reply that says nothing useful (just "we're working on it"). That is not acceptable either — the reply must confirm what has been established (reproducibility on large workspaces) and state the one next action (update when investigation progresses).
