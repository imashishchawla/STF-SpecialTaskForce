---
eval_id: E01
scenario: happy-path
phase: 3
status: ready
created: "2026-10-02"
---

# Eval Case E01 — Happy Path: Complete Evidence, Confirmed Fix

## What this tests
- Coordinator produces the correct next action (apply the confirmed fix)
- Source Researcher cites the exact version-specific URL
- No unnecessary clarifying questions are asked
- Internal and customer outputs are correctly separated

---

## Input — Case packet (sanitized)

**Case alias**: eval-E01
**Product scope**: HCP Terraform
**Severity**: Sev 3

**Customer report**:
"Our Terraform runs started failing 3 days ago with the error:
`Error: Invalid provider configuration: Provider "registry.terraform.io/hashicorp/aws" requires explicit configuration.`
We haven't changed any provider configuration. We are on AWS provider v5.31.0 and Terraform Core 1.6.4.
The workspace uses remote execution. This was working fine last week."

**Supplied evidence**:
- Run log excerpt (redacted):
  ```
  Error: Invalid provider configuration
  Provider "registry.terraform.io/hashicorp/aws" requires explicit configuration.
  See the documentation for registry.terraform.io/hashicorp/aws.
  ```
- Terraform version: 1.6.4
- AWS provider version: 5.31.0
- Execution mode: Remote
- No recent code changes reported
- No VCS or policy changes reported

---

## Expected coordinator output

**Stage**: INVESTIGATING → VALIDATING

**Key assertions** (all must be present):

1. **Scope classification**: HCP Terraform, remote execution, AWS provider issue
2. **Hypothesis**: Provider configuration inheritance change in AWS provider v5.x (known breaking change in v5.0 — requires explicit `provider` block)
3. **Evidence citation**: AWS provider CHANGELOG citing v5.0.0 breaking changes (not a GitHub comment — release notes)
4. **Discriminating check**: "Does the customer's root module contain an explicit `provider` block for the AWS provider?"
5. **Next action**: Ask operator to request the customer share their root module `provider` block (if present) or confirm whether they rely on provider inheritance from a child module
6. **No premature RCA**: Hypothesis is stated as hypothesis, not confirmed cause

**Customer draft** (if generated):
- Must contain: one focused question — presence/content of `provider` block
- Must not contain: internal Jira IDs, entitlement info, routing details
- Must include: full URL to AWS provider upgrade guide

---

## Acceptance criteria

| Criterion | Pass condition |
|---|---|
| Scope classified correctly | `product_scope: hcp_terraform`, `execution_mode: remote` |
| Hypothesis ranked correctly | AWS provider v5 breaking change is H-1 or H-2 with `confidence: medium` or higher |
| Evidence cited with URL | Exact release notes URL, not a GitHub comment |
| One focused question | Asks about `provider` block — does not ask for all 14 intake checklist items |
| No confirmed RCA without discriminating check | `verdict` is `conditional` or hypothesis is labelled as unconfirmed |
| Internal and customer outputs separated | No internal routing details in customer draft |

---

## Evaluator notes

This is the baseline case. If the agent fails E01, it will fail all other cases.
The key failure mode to watch: asking unnecessary checklist questions when the evidence is sufficient to form a ranked hypothesis immediately.
