# Design 04 — Memory and Evidence Schemas

> **Status**: Draft — awaiting operator review.  
> **Prepared**: 2 October 2026.  
> **Scope**: Design phase only. No memory files, indexes, or stores are created here.

---

## 1. Memory areas overview

| Area | Path | Persistence | Write authority | Contains |
|---|---|---|---|---|
| Working context | Session memory (not persisted) | Session-bound | Coordinator (auto) | Redacted excerpts, temporary analysis for current investigation |
| Case checkpoints | `checkpoints/<case_alias>-pass-<n>.md` | Per-case | Human-approved | Sanitized timeline, facts, hypotheses, decisions, next action |
| Issue patterns | `memory/patterns/<slug>.md` | Permanent (versioned) | Human-approved only | Sanitized error patterns, causes, remedies, references |
| Preferences | `memory/preferences.md` | Permanent (versioned) | Human-approved only | Response style, templates, signature, diagnostic habits |
| Operational knowledge | `memory/ops/<topic>.md` | Permanent (restricted) | Human-approved only | Internal process references, entitlement/routing conditions |
| Correction history | `memory/corrections/<slug>.md` | Permanent (versioned) | Human-approved only | Accepted corrections with provenance |

> **Memory write rule**: No agent writes to `memory/` or `checkpoints/` directly. The Memory Curator **proposes** entries; the operator approves before any persistent write. The coordinator may write a draft checkpoint to a staging area (`checkpoints/draft/`) during a pass, but the draft requires promotion approval.

---

## 2. Separation from STF `.memory/`

The STF repository has its own `.memory/` directory (`/.memory/decisions.md`, `/.memory/lessons.md`). These are STF project governance records and must not be modified by the terraform agent.

The terraform agent uses `memory/` (no leading dot) inside its own dedicated repository (not inside STF). The paths are completely separate. During the design phase, no `memory/` directory exists anywhere — it is created during Phase 3 implementation in the terraform agent's own repo.

---

## 3. Issue pattern schema

A single pattern entry is a Markdown file with a YAML front matter block followed by a prose section.

**File**: `memory/patterns/<slug>.md`  
**Naming**: `<category>-<short-description>.md` — e.g., `vcs-azdevops-webhook-missed-events.md`

```yaml
---
pattern_alias: vcs-azdevops-webhook-missed-events
schema_version: 1
category: vcs_webhook
sub_category: azure_devops
affected_products:
  - hcp_terraform
  - terraform_enterprise
affected_versions: ">=1.5.0"          # version range where this has been observed
confidence: candidate                  # candidate | validated | outdated | rejected
last_reviewed: "2026-10-02"
superseded_by: null                    # or pattern_alias of newer entry
source_refs:
  - title: "HashiCorp Docs — VCS Integration"
    url: "https://developer.hashicorp.com/terraform/cloud-docs/vcs"
    retrieved: "2026-10-02"
    version_applicability: "HCP TF current"
    publication_status: released
    visibility: public
---

## Error fingerprint

```
Error: Webhook event not received for push to branch <branch>
Run not triggered after commit <sha>
```

## Trigger conditions

[Sanitized description of conditions under which this pattern occurs — no customer identifiers]

## Discriminating check

[The one specific check that confirms this pattern vs similar-looking issues]

## Confirmed cause

[null if not yet confirmed | one sentence if confirmed by Engineering or reproducible evidence]

## Supported observations

[Sanitized list of observations that support this pattern]

## Competing causes

[Other hypotheses that were considered and excluded, with reason for exclusion]

## Remedy

[Validated remedy or workaround]

## Validation result

[customer_confirmed_improvement | engineering_confirmed | analyst_validated | unvalidated]

## Notes

[Any important caveats, version-specific behavior, or known limitations]
```

---

## 4. Confidence lifecycle

```
CANDIDATE   ──► VALIDATED     when: discriminating check confirmed + remedy validated by customer or Engineering
     │
     └──────► REJECTED        when: subsequent evidence contradicts the pattern at the same version range

VALIDATED   ──► OUTDATED      when: a product update changes the behavior; validated entry kept for history
OUTDATED    ──► superseded_by → new pattern_alias
```

> **A customer-confirmed improvement validates the remedy's outcome only** — it does not confirm the root cause unless Engineering or a reproducible test establishes it. The `confidence` field must reflect this distinction.

---

## 5. Case checkpoint schema

**File**: `checkpoints/<case_alias>-pass-<n>.md`  
**Naming**: `CASE-2026-001-pass-1.md`

> The case alias must never be the real ticket/case number in persistent storage. The operator maps aliases in a separate restricted record outside this repository.

```yaml
---
case_alias: CASE-2026-001
schema_version: 1
pass_number: 1
pass_timestamp: "2026-10-02T14:30:00+05:30"
product_scope:
  primary: hcp_terraform
  provider_name: null
  product_version: "202407.1"
  cli_version: "1.9.5"
case_stage: investigating
investigation_state: blocked             # investigating | blocked | awaiting_customer | awaiting_engineering | resolved
result_status: blocked                   # from STF result envelope
blocker: "Awaiting redacted API audit log from customer"
next_action: "Request the last 72 hours of audit log export from HCP Terraform settings"
---

## Timeline

[Sanitized timeline with timestamps and timezone as supplied — not normalized]

## Established facts

[What is confirmed — distinguishing from hypothesis]

## Current hypotheses (ranked)

| Rank | Hypothesis | Supporting evidence | Conflicting evidence | Discriminating check |
|---|---|---|---|---|
| 1 | ... | ... | ... | ... |

## Rejected hypotheses

[With reason for rejection]

## Actions taken

[What was tried and what was confirmed or excluded as a result]

## Outstanding questions

[Exactly what is unknown and why it matters]

## Evidence references

[Sources consulted with full citations]

## Approved actions

[Any auth-required actions that were explicitly approved — with authorization record]

## Next action

[One specific next action — same as `next_action` in front matter]
```

---

## 6. Preferences schema

**File**: `memory/preferences.md`

```yaml
---
schema_version: 1
last_reviewed: "2026-10-02"
---

## Response style

- Tone: short, direct, polite, practical
- Avoid: "sorry", "apologize", unsupported promises
- Links: full URLs only
- Commands: precise with exact syntax when supported by source
- Pronouns: use supplied; never guess
- Language: English unless customer's language and translation are approved

## Signature (resolved from `memory/preferences.md`)

Regards,
{{operator_name}} | {{operator_title}}
Available {{operator_availability}}
Thank you for choosing IBM Support.

## Closure survey URL pattern (exact)

https://www.ibm.com/mysupport/s/case/<REAL_TICKET_NUMBER>/survey

## Handoff fields (exact)

Issue:
Impact:
Diagnosis / Actions taken:
Next Steps:
Originating Region:
Destination Region:

## CAN fields (exact)

Problem statement:
Technical impact:
Business impact:
Actions taken:
Needs:

## Diagnostic habits

[the operator's known diagnostic preferences — to be populated from real usage; empty initially]
```

---

## 7. Evidence reference schema

Used in result envelopes, checkpoints, and memory entries:

```typescript
interface EvidenceRef {
  ref_id: string;                      // unique within result or checkpoint
  title: string;
  source_type: "public_docs" | "release_notes" | "github_issue" | "status_page"
             | "internal_process" | "memory_pattern" | "supplied_evidence";
  url?: string;                        // full URL — omit for supplied evidence
  internal_ref?: string;               // for internal process docs
  retrieved_date: string;              // ISO date
  version_applicability: string;
  publication_status: "released" | "beta" | "open_issue" | "unconfirmed_comment";
  visibility: "public" | "internal_session_only";
  excerpt?: string;                    // verbatim or paraphrased (label which)
}
```

---

## 8. Operational knowledge schema

**Files**: `memory/ops/<topic>.md` — e.g., `memory/ops/registry-routing.md`

```yaml
---
schema_version: 1
topic: registry-routing
classification: internal_restricted     # never exposed in customer-visible output
source_ref: "plan/01-TCPR-Terraform-Public-Registry_-Case-Handling-in-CSP-270426-034252.pdf"
source_status: interim
review_date: "2026-10-02"
verification_required: true             # must verify with team before operational use
---

[Sanitized internal process description — no customer data]
[Applicability conditions]
[Routing steps — internal only]
[Verification notes]
```

> Operational knowledge files are **session-scoped by default** — the coordinator reads them for a session but does not embed their content in checkpoint files, memory patterns, or any customer-visible output.

---

## 9. Correction history schema

**File**: `memory/corrections/<slug>.md`

```yaml
---
schema_version: 1
correction_alias: corr-2026-001
correction_type: source_error          # source_error | style | workflow | hypothesis | remedy
target_ref: memory/patterns/vcs-azdevops-webhook-missed-events.md
correction_date: "2026-10-02"
correction_by: ashish_chawla
---

## What was wrong

[The incorrect claim, style element, or workflow step]

## What is correct

[The accepted correction]

## Provenance

[How the error was discovered — e.g., Engineering feedback, updated docs]

## Applied to

[Which memory entries or templates were updated as a result]
```

---

## 10. Sanitization checklist (applied before any persistent write)

Memory Curator must verify all items before proposing any write:

- [ ] No customer names or display names
- [ ] No customer email addresses
- [ ] No organization names or slugs
- [ ] No workspace names or IDs (`ws-*`)
- [ ] No run IDs (`run-*`), task IDs, plan IDs, apply IDs
- [ ] No account IDs, subscription IDs, tenant IDs
- [ ] No authentication tokens, API keys, PATs, secrets of any kind
- [ ] No raw state file content (summaries of state structure are OK if no sensitive values)
- [ ] No full plan JSON
- [ ] No raw log content (sanitized error patterns are OK)
- [ ] No URLs containing customer identifiers
- [ ] No IP addresses (unless generic documentation example)
- [ ] Free-text descriptions reviewed for indirect identifiers

---

## 11. Retention and deletion

| Area | Retention policy |
|---|---|
| Working context (session) | Cleared at session end — no recovery |
| Draft checkpoints | Promoted or deleted within 7 days (proposed) |
| Approved checkpoints | Retained until case is closed + 90 days (proposed) |
| Issue patterns (validated) | Permanent with version history; superseded entries kept |
| Issue patterns (rejected) | Kept 30 days then eligible for deletion (proposed) |
| Preferences | Permanent; versioned |
| Operational knowledge | Permanent while process is current; dated with `review_date` |
| Correction history | Permanent |

> Retention periods are proposals. The operator must confirm before they govern any actual deletion.

---

## 12. Unresolved design questions

| # | Question | Impact |
|---|---|---|
| MQ-01 | How should alias-to-ticket mapping be stored securely outside the agent repo? | Affects checkpoint traceability to live support records |
| MQ-02 | Should draft checkpoints go in `checkpoints/draft/` or be in-session only? | Affects resumption after an interrupted session |
| MQ-03 | What is the right granularity for operational knowledge files — one file per process vs one file per routing scenario? | Affects maintainability |
| MQ-04 | Should correction history reference the specific model output that was incorrect, or just the conclusion? | Affects auditability |
| MQ-05 | Is YAML front matter the right format, or should a pure JSON schema be used for machine processing later? | Affects future tool integration |

---

*Previous: [`03-skills-and-templates.md`](03-skills-and-templates.md) | Next: [`05-runtime-and-integration.md`](05-runtime-and-integration.md)*
