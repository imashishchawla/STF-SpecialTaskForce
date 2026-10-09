# Template catalog
> **Status**: Nine draft templates are present; pilot use and validation remain pending.
> Full specification: `docs/design/03-skills-and-templates.md §8`

These templates are referenced by the `communication` skill. Placeholder fields are intentional and must be resolved from validated case evidence or local operator preferences before use.
All templates require: validated findings from Validation Reviewer before use.

---

## customer-reply.md — Standard customer reply

```markdown
Hi [Customer name or team],

[Body — validated findings only, no unconfirmed hypotheses presented as conclusions]

[Validated next steps or requested information]

Regards,
{{operator_name}} | {{operator_title}}
Available {{operator_availability}}
Thank you for choosing IBM Support.
```
> Signature tokens are resolved from `memory/preferences.md` at generation time.

**Required fields**: customer name/team, validated body, next steps
**Must not**: Include internal Jira details, entitlement info, routing steps, or unvalidated claims

---

## customer-reply-initial.md — First-response acknowledgment

```markdown
Hi [Customer name or team],

Thank you for reaching out to IBM Support.

I've received your case and am investigating [describe known scope — no hypotheses].

I'll follow up with [expected output] by [timeframe if confirmed].

Regards,
{{operator_name}} | {{operator_title}}
Available {{operator_availability}}
Thank you for choosing IBM Support.
```

**May be sent** before full investigation is complete, using only confirmed facts.

---

## internal-update.md — IBM internal case note

```markdown
## Internal update — [ISO date]

**Status**: [INVESTIGATING / AWAITING CUSTOMER / AWAITING ENGINEERING / VALIDATING]

**Summary**: [One-sentence summary of current state]

**Evidence reviewed**: [list with refs]

**Current hypothesis**: [ranked list — label as hypothesis, not confirmed cause]

**Next action**: [specific, one item]

**Blockers**: [if any]
```

**Must not** appear in customer-visible updates.

---

## handoff.md — Shift handoff

```markdown
## Handoff — [ISO date] from {{operator_name}}

**Case**: [alias / ticket number]
**Stage**: [current stage]
**Severity**: [current severity]
**Product scope**: [HCP TF / TFE / etc.]

**Summary**: [2–3 sentences]

**Evidence collected**:
- [list]

**Investigation state**: [current hypothesis and status]

**Outstanding**: [what is missing or blocked]

**Immediate next action for incoming engineer**: [one specific action]

**Auth-required actions pending**: [list if any — must not be executed without fresh approval]
```

---

## closure.md — Customer closure (REQUIRES real ticket number)

```markdown
Hi [Customer name or team],

[Resolution summary — confirmed cause and remedy, or confirmed no-issue finding]

[Any follow-up steps or documentation the customer should keep]

Please take a moment to complete our customer satisfaction survey:
https://www.ibm.com/mysupport/s/case/<REAL_TICKET_NUMBER>/survey

Regards,
{{operator_name}} | {{operator_title}}
Available {{operator_availability}}
Thank you for choosing IBM Support.
```

> **Block this template** if `<REAL_TICKET_NUMBER>` is not a verified case ticket number.

---

## Additional draft templates
- `can-report.md` — Customer Advocacy Notification
- `rca.md` — Root cause analysis (confirmed vs investigation update variants)
- `kb-draft.md` — Customer-facing knowledge base article
- `registry-routing-internal.md` — Internal Jira collaboration steps (restricted, internal only)
