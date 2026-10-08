---
eval_id: E04
scenario: wrong-product-routing
phase: 3
status: ready
created: "2026-10-02"
---

# E04 — Wrong Product Routing (Terraform vs Azure DevOps)

## Scenario

Customer reports a "Terraform" issue that is actually caused by Azure DevOps — specifically the VCS webhook delivery mechanism. The intake classifier must catch that the true owner is the VCS integration layer, not a Terraform core or HCP Terraform defect, and state the correct ownership clearly.

---

## Input (paste this into coordinator)

```
Product: HCP Terraform (selected by customer)
Issue: Our Terraform runs are not triggering when we push to our Azure DevOps repository.
The workspace is connected to Azure DevOps via VCS integration. We've confirmed the 
branch filter matches our branch name. The webhook shows as "Active" in HCP Terraform
settings but no runs queue after commits.

Evidence:
- HCP Terraform workspace VCS settings screenshot: webhook status = Active, 
  trigger = push, branch filter = "main"
- Azure DevOps commit history confirms pushes to "main" on [dates]
- No runs appear in the HCP Terraform Runs tab for those commit times
- No error shown in HCP Terraform UI
```

---

## Expected output — key assertions

| # | Assertion | Pass condition |
|---|---|---|
| A1 | Scope classified correctly as VCS integration — NOT Terraform Core or HCP TF run issue | `product_scope: hcp_terraform_vcs` or `component: vcs_integration` |
| A2 | Coordinator identifies the investigation must start on the Azure DevOps side | States webhook *delivery* (ADO → HCP TF) must be checked, not HCP TF trigger config |
| A3 | Coordinator does NOT investigate run logs or provider errors | No request for run logs, provider versions, or HCL config |
| A4 | Correct diagnostic path stated | See diagnostic path below |
| A5 | Coordinator does NOT present Azure DevOps as a supported product | Clear statement that ADO itself is not supported; only the integration layer is |
| A6 | Customer-safe next action is a single targeted step | Ask for Azure DevOps webhook delivery log (not HCP TF data) |

### Correct diagnostic path (A4)

The issue is that commits are not triggering runs. Given:
- Webhook shows Active in HCP TF (rules out HCP TF not knowing about the webhook)
- Branch filter appears correct
- Commits confirmed in ADO
- No runs in HCP TF

The investigation must move to Azure DevOps webhook delivery:
1. Check ADO webhook delivery history: Project Settings → Service Connections → Webhooks → Recent Deliveries
2. Look for: delivery attempts, HTTP response codes from HCP Terraform, any 4xx/5xx from HCP TF endpoint
3. If no delivery attempts: the ADO push event type or filter is not firing — check event type config
4. If delivery attempts show 2xx but no run: HCP TF received but branch/working directory filter rejected it

The coordinator must ask for: **Azure DevOps webhook delivery log** — specifically the push event entries and their HTTP response codes.

---

## Acceptance criteria

| Criterion | Pass | Fail |
|---|---|---|
| Scope classified as VCS / webhook layer | yes | classified as run issue, provider issue, or TF Core |
| Investigation directed to ADO webhook delivery | yes | investigates HCP TF run config or provider |
| Single targeted question | ADO webhook delivery log | run logs, HCL, provider version |
| ADO not claimed as supported product | ADO is OOS; integration layer is in scope | treats ADO settings as IBM/HashiCorp supported |
| No hypothesis without evidence | labeled as hypothesis | states "the cause is ADO filter" without evidence |

---

## Evaluator notes

This is a high-frequency failure pattern: the customer selects "HCP Terraform" as the product because that is where they see the symptom (no runs). But the cause is outside HCP Terraform — the ADO push event is not delivering the webhook payload.

A common agent failure: requesting run logs. There are no run logs because no run was created. This eval specifically tests whether the agent understands that the absence of runs is the data point, not a run log to analyse.

The second failure: claiming ADO configuration is fully in scope. It is not — IBM Support supports the HCP Terraform side of the VCS integration; ADO-side configuration changes are guided but are the customer's responsibility.
