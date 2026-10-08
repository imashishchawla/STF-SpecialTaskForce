---
skill_id: terraform-communication
version: "0.1.0-draft"
status: draft
source: portable/terraform-support-agent/export/skills/communication.md
canonical: true
bob_generated: false
phase: 3
---

# Skill: communication
> **Status**: Draft skeleton — not yet validated or active.
> Full specification: `docs/design/03-skills-and-templates.md §7`
> Template catalog: `export/templates/` (Phase 3 implementation)

## Purpose
Produce stage-appropriate communication drafts in the operator's established style, using only **reviewed and validated findings**.
The style rules and signature are loaded from `memory/preferences.md` at output-generation time.

## Style rules (authoritative source: plan §10)
```
Tone:     Short, direct, polite, practical
Avoid:    "sorry", "apologize", unsupported promises
Links:    Full URLs only — no shortened links, no internal tracker links in customer drafts
Paths:    Precise UI paths and commands when validated
Language: Match customer's language if supplied and if translation is approved
Pronouns: Use supplied pronouns; do not guess personal details
Internal: Never expose Jira details, entitlement info, or operational instructions in customer drafts
```

## Signature (resolved from `memory/preferences.md` at output-generation time)
```
Regards,
{{operator_name}} | {{operator_title}}
Available {{operator_availability}}
Thank you for choosing IBM Support.
```
> Never hard-code a name here. If `preferences.md` is unpopulated, the intake onboarding check
> will have halted the session before this skill is reached.

## Closure survey line (exact — fill in real ticket number)
```
Please take a moment to complete our customer satisfaction survey:
https://www.ibm.com/mysupport/s/case/<REAL_TICKET_NUMBER>/survey
```
> Block closure drafts without a real ticket number.

## Templates (✅ complete — all 9 files in export/templates/)
| File | Classification | Content |
|---|---|---|
| `customer-reply.md` | CUSTOMER-VISIBLE | Standard customer reply with signature |
| `customer-reply-initial.md` | CUSTOMER-VISIBLE | First-response acknowledgment |
| `handoff.md` | INTERNAL ONLY | Shift handoff with all required fields |
| `closure.md` | CUSTOMER-VISIBLE | Customer closure with survey URL |
| `internal-update.md` | INTERNAL ONLY | IBM internal case notes |
| `can-report.md` | INTERNAL ONLY | Customer Advocacy Notification |
| `rca.md` | INTERNAL ONLY | Root cause analysis |
| `kb-draft.md` | CUSTOMER-VISIBLE | Customer-facing KB article |
| `registry-routing-internal.md` | INTERNAL ONLY | Internal Jira collaboration steps (restricted) |

## Email copy-paste format (C002)
All drafted emails must be wrapped in:
```
─────────────────────────────────────────────
COPY FROM HERE
─────────────────────────────────────────────
Subject: Re: [Case #XXXXX] — <issue title>

Hi <Name>,

<body>

Regards,
{{operator_name}} | {{operator_title}}
Available {{operator_availability}}
Thank you for choosing IBM Support.
─────────────────────────────────────────────
END COPY
─────────────────────────────────────────────
```
- Subject line always included
- Signature tokens resolve from `memory/preferences.md`; if unset use `[NAME]`, `[TITLE]`, `[AVAILABILITY]`
- Block contains only what the operator sends — no rules, no internal notes

## Preconditions
- Must only use findings that have been reviewed by the Validation Reviewer
- Must not present unconfirmed hypotheses as conclusions in customer drafts
- Must not be invoked before the coordinator's review step is complete
