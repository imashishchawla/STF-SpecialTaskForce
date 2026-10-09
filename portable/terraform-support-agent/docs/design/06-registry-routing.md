# Design 06 — Registry Routing Design

> **Status**: Draft — awaiting operator review.  
> **Prepared**: 2 October 2026.  
> **Scope**: Design phase only. No collaboration cases, PagerDuty alerts, or messages have been created.
>
> ⚠️ **Source classification**: The rules in this document derive from an **interim internal process** (PDF reviewed: `plan/archive/01-TCPR-Terraform-Public-Registry_-Case-Handling-in-CSP-270426-034252.pdf`, reviewed 2 October 2026). The document's current organizational validity has not been independently established. These rules require verification with the team before operational use. They are **internal-only** — no detail may appear in customer-visible output.

---

## 1. Source extraction summary

The supplied PDF (`TCPR-Terraform Public Registry_ Case Handling in CSP-270426-034252`) describes an interim support process for Terraform Public Registry issues. Key facts extracted:

| Fact | Extracted value |
|---|---|
| Process status | Interim (explicit in document) |
| Phase II planned | Yes — started April (year inferred as 2026) — direct registry team handling |
| Applicability | Paying/enterprise HCP Terraform AND self-managed customers under entitlement conditions below |
| Entitlement condition | Public registry entitlement is **OFF** in CSP |
| Out-of-scope | Free Tier / Partner / Community Edition |

---

## 2. Routing decision tree

```
Case arrives with public_registry scope
               │
               ▼
    ┌─────────────────────────────────┐
    │ Check customer type + entitlement│
    └─────────────────────────────────┘
               │
    ┌──────────┴────────────────────────┐
    │                                   │
    ▼                                   ▼
Free Tier / Partner /        Paying/enterprise HCP TF
Community Edition            OR self-managed customer
                             WITH entitlement OFF in CSP
    │                                   │
    ▼                                   │
Route to:                               │
terraform-registry@hashicorp.com        │
(per this process document)             │
                                        ▼
                              ┌─────────────────────┐
                              │ Check severity        │
                              └─────────────────────┘
                                        │
                         ┌──────────────┴─────────────────┐
                         │                                 │
                         ▼                                 ▼
                      Sev 2 / 3 / 4                     Sev 1
                         │                                 │
                         ▼                                 ▼
               Jira collaboration case         PagerDuty engagement
               (the operator creates manually)       (the operator executes manually)
```

---

## 3. CSP Jira collaboration case steps (Sev 2 / 3 / 4)

> These steps are for the operator's reference. The agent prepares the draft; the operator creates the case.

**Path in CSP** (as described in the source document):

```
1. Open the customer's case in CSP
2. Navigate to the case left panel
3. Click the dropdown → select "New Collaboration"
4. Set Remote Repository to: Terraform - JIRA - Terraform Public Registry
5. Subject → becomes the Jira issue title
6. Description → carries the customer information summary
7. Support Mission → defaults to "HashiCorp"
```

**Agent's output for this path**:

The `registry-routing` skill produces an internal draft containing:

```markdown
## Registry collaboration case draft (INTERNAL ONLY)

Case alias: <alias>
Severity: <sev>
Customer type: <paying_hcp_tf | self_managed>
Entitlement status: public_registry_off_in_csp (verified: <yes | pending verification>)
Process status: INTERIM — verify with team before use

### Jira collaboration case details

Subject (→ Jira title):
[One-sentence description of the registry issue — sanitized, no customer identifiers]

Description (→ carries customer information):
[Sanitized summary: what the customer is experiencing, affected registry item (module/provider name),
 error observed, impact]

Support Mission: HashiCorp

### Tracking checklist

- [ ] CSP collaboration case created (ID: _______)
- [ ] Jira case received (ID: _______)
- [ ] Engineering updated on case status
- [ ] Customer update sent (customer-appropriate wording only)
- [ ] SLA delay risk assessed — manager notified if delay anticipated
- [ ] Customer update after Engineering response
```

---

## 4. PagerDuty engagement steps (Sev 1)

> Sev 1 requires human judgment. The agent prepares the engagement path; the operator executes.

The agent's output for Sev 1:

```markdown
## Sev 1 Registry engagement draft (INTERNAL ONLY)

Case alias: <alias>
Severity: Sev 1
Customer type: <paying_hcp_tf | self_managed>
Entitlement status: public_registry_off_in_csp (verified: <yes | pending verification>)
Process status: INTERIM — verify with team before use

### PagerDuty engagement path

[Steps from source document for PagerDuty engagement — to be populated from the document
during Phase 3 skill implementation once the process is verified with the team]

⚠️ Note: PagerDuty engagement step details were not fully extracted from the supplied PDF.
the operator must verify the exact PagerDuty path with the team before Phase 3 implementation.

### Tracking checklist (same as Sev 2/3/4 above, plus)
- [ ] Engineering paged via PagerDuty
- [ ] Manager notified immediately (Sev 1 protocol)
```

---

## 5. Email routing for out-of-scope customers

For Free Tier / Partner / Community Edition customers with a Public Registry issue:

**Agent's output**:

```markdown
## Registry email routing (INTERNAL NOTE)

This customer type is not covered by the CSP/Jira interim process.
Per the source document, route to: terraform-registry@hashicorp.com

Customer communication should be drafted without referencing internal routing.
Suggest standard language: "This issue involves the Terraform Public Registry.
I am escalating it to the appropriate team who will follow up with you."
[exact wording subject to Communication Specialist review]
```

---

## 6. Support intermediary responsibilities

The source document describes IBM Support as an intermediary throughout the lifecycle. Extracted responsibilities:

| Responsibility | Agent action | the operator action |
|---|---|---|
| Track both CSP case and Jira | Maintain tracking checklist in checkpoint | Creates/monitors cases |
| Keep Engineering informed | Propose checkpoint updates | Sends updates |
| Relay Engineering updates to customer | Draft customer-appropriate Engineering summary | Reviews and sends |
| Anticipate SLA delays | Flag in checkpoint if timeline indicates delay | Notifies manager |

**Customer-appropriate wording for Engineering updates**:

When relaying an Engineering response, the Communication Specialist must:

- Strip any internal project names, internal system identifiers, or operational details
- Translate Engineering findings into customer-understandable language
- Not promise a timeline unless Engineering has confirmed one
- Not describe the internal collaboration process to the customer

---

## 7. Phase II context

The source document states that Phase II (direct registry team handling) was planned to start in April. As this design was prepared in October 2026, Phase II may already be active. This has a direct impact on whether the interim process in this document is still applicable.

**Before using this skill in any live case**:

1. Verify with the team or manager whether Phase II has started
2. If Phase II is active, confirm what the new process is
3. Update `memory/ops/registry-routing.md` with the verified current process
4. Mark this design document as superseded if the interim process no longer applies

---

## 8. What the agent will never do independently

Regardless of instructions in case content, customer messages, or retrieved pages:

- Create a Jira collaboration case
- Page via PagerDuty
- Send a message to `terraform-registry@hashicorp.com`
- Change the severity of a case
- Close a case

These require explicit per-action approval with a recorded authorization.

---

## 9. Unresolved design questions

| # | Question | Impact |
|---|---|---|
| RQ-01 | Has Phase II (direct registry team handling) started as of the operator's current date? | May make the entire interim process obsolete |
| RQ-02 | What are the exact PagerDuty engagement steps for Sev 1 registry cases? | Required for Phase 3 skill implementation |
| RQ-03 | How does the operator verify entitlement status in CSP? Specific UI path needed | Required for applicability check in the skill |
| RQ-04 | Is the CSP path "case left panel → New Collaboration" the same in the current CSP version? | Required for accuracy of Jira collaboration draft |
| RQ-05 | What constitutes "self-managed customers under entitlement conditions"? Need specific entitlement field name in CSP | Required for routing decision accuracy |

---

*Previous: [`05-runtime-and-integration.md`](05-runtime-and-integration.md) | Next: [`07-implementation-plan.md`](07-implementation-plan.md)*
