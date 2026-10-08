---
eval_id: E03
scenario: conflicting-sources
phase: 3
status: ready
created: "2026-10-02"
---

# E03 — Conflicting Sources

## Scenario

The Source Researcher finds two official HashiCorp documents that give different behavior for the same configuration in the same Terraform version range. The coordinator must resolve the conflict explicitly — not pick the majority, not average them, not ignore one silently.

---

## Input (paste this into coordinator)

```
Product: HCP Terraform
Terraform version: 1.6.x
Issue: Customer is using a dynamic provider block inside a module. The workspace runs
successfully on the first apply but fails on subsequent applies with:
"Error: Provider configuration not present"

Evidence supplied:
- Run log excerpt showing "Provider configuration not present" on second apply
- HCL: module uses dynamic provider blocks with `for_each` on the calling module
- Provider version: hashicorp/aws 5.31.0

Research question: Is `for_each` on `provider` blocks inside modules supported in Terraform 1.6.x?
```

*(Two source findings should be returned — the feature docs say "supported in 1.x" but the upgrade guide for 1.6 notes a known issue with stateful provider meta-arguments in `for_each` modules.)*

---

## Expected output — key assertions

| # | Assertion | Pass condition |
|---|---|---|
| A1 | Source Researcher returns BOTH findings with full URLs and version applicability | Two separate entries in findings, each with a URL |
| A2 | Coordinator explicitly names the conflict | States that the two sources give different guidance |
| A3 | Coordinator does NOT resolve by majority (1 vs 1 = no majority) | No claim that "most sources say X" |
| A4 | Coordinator identifies the more specific source as the tiebreaker | Upgrade guide / release notes for exact version > general feature doc |
| A5 | Coordinator proposes one discriminating check | Specific check that would confirm which source applies to this case |
| A6 | Coordinator does NOT present a confirmed cause | Labeled as hypothesis until discriminating check result is available |
| A7 | Coordinator states which source is authoritative for which aspect | Version-specific release notes > general docs for behavior-change questions |

### The correct resolution logic (A4)

- Version-specific release notes and upgrade guides are more authoritative than general feature documentation for behavior-change questions in a specific version.
- The coordinator should note: "The general docs confirm `for_each` provider support, but the 1.6.x upgrade notes indicate a known issue with stateful meta-arguments in for_each module providers — this is more specific to the version in scope."
- Discriminating check: ask the customer whether the state file shows the provider as a module-level or root-level provider after the first successful apply.

---

## Acceptance criteria

| Criterion | Pass | Fail |
|---|---|---|
| Both findings present | two source entries | one source entry |
| Conflict explicitly named | yes | silently picks one |
| Version-specific source preferred | yes | general docs treated as equal |
| Discriminating check proposed | one specific check | no check / generic advice |
| Hypothesis labeled correctly | hypothesis or "possible" | stated as confirmed |

---

## Evaluator notes

This tests the source authority hierarchy. The most common failure is the coordinator picking the source that confirms the hypothesis it is already leaning toward. The correct behavior is to name the conflict and defer to the more specific (version-targeted) source for a tiebreak — with a discriminating check to confirm.

A secondary failure mode: returning the conflict but then saying "I cannot determine the answer" without proposing a discriminating check. That is not acceptable — the coordinator must always return a next action.
