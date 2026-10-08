---
eval_id: E02
scenario: missing-log-evidence
phase: 3
status: ready
created: "2026-10-02"
---

# E02 — Missing Log Evidence

## Scenario

Customer reports a Terraform run failure but provides only the error message text with no run logs, no version information, and no HCL. The intake skill must request exactly the missing pieces that would change the next diagnostic step — nothing more.

---

## Input (paste this into coordinator)

```
Product: HCP Terraform
Report: Our runs are failing with "Error: No valid credential sources found for AWS Provider."
We've used this workspace for months and nothing changed on our end.
```

*(No logs attached. No version info. No run ID. No recent change context.)*

---

## Expected output — key assertions

| # | Assertion | Pass condition |
|---|---|---|
| A1 | Intake does NOT halt with a redaction block | No secret pattern detected in this input |
| A2 | Product scope classified as HCP Terraform | `product_scope: hcp_terraform` or equivalent |
| A3 | Error type classified as authentication/authorization | `error_category: auth_credential` |
| A4 | Coordinator asks for EXACTLY the items that change the next diagnostic step | See required items list below |
| A5 | Coordinator does NOT ask for items that wouldn't change the diagnostic | No request for policy sets, VCS details, cost estimation config |
| A6 | Coordinator does NOT present a hypothesis as confirmed | No statement of cause without evidence |
| A7 | Single clarifying block — not a long checklist | ≤3 targeted questions in the reply |

### Required items the coordinator must request (A4)

At minimum, the coordinator must ask for:
1. The Terraform AWS provider version (determines which credential chain is in effect)
2. The execution mode (remote / agent / local CLI — determines where credentials are sourced)
3. Whether this is a new workspace or one that was previously working — and if working before, what recently changed (narrows to regression vs misconfiguration)

### Items the coordinator must NOT ask for (A5)

- Run task or policy configuration (not relevant until auth is resolved)
- VCS details (not relevant — this is a credential error, not a trigger error)
- Full HCL config (not needed to diagnose credential chain)

---

## Acceptance criteria

| Criterion | Pass | Fail |
|---|---|---|
| Product scope correct | hcp_terraform | any other scope |
| Error category correct | auth / credential | networking, provider, other |
| Questions count | ≤3 focused questions | >5 questions or a numbered checklist |
| No hypothesis stated as confirmed | hypothesis labeled as such or absent | "The issue is X" without evidence |
| No unnecessary fields requested | not asked | asks for VCS, policies, HCL upfront |

---

## Evaluator notes

This is the **most common real-world pattern**: customer pastes an error with zero supporting evidence. The intake skill's value is in knowing what to ask — not asking everything. A failure here means the agent will annoy customers with data dumps on every case.

The correct next action is a short, numbered ask for provider version + execution mode + change history. That is the minimum that changes the next diagnostic step for `NoCredentialSources`.
