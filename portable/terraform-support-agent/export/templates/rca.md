# Template: rca.md — Root Cause Analysis
# Classification: Two variants — INVESTIGATION UPDATE (unconfirmed) and CONFIRMED RCA
# Choose the correct variant based on validation status.
# Requires: Validated findings from Validation Reviewer

---

## VARIANT A: Investigation Update (use when root cause is NOT yet confirmed)

─────────────────────────────────────────────
COPY FROM HERE
─────────────────────────────────────────────
**Subject**: [Ticket number] — Investigation Update

Hi [Customer name or team],

I wanted to share an update on the investigation for this case.

**Current status**: We are actively investigating the reported issue.

**What we know so far**:
- [Confirmed fact 1 — what is verified from evidence]
- [Confirmed fact 2]

**What we are checking next**:
- [Next diagnostic step or information needed from Engineering / customer]

**What we need from you** (if applicable):
- [Specific item — e.g. "Can you confirm whether the issue also occurs in workspace X?"]

I will follow up by [realistic date if one can be confirmed — do not promise a date without basis].

Regards,
{{operator_name}} | {{operator_title}}
Available {{operator_availability}}
Thank you for choosing IBM Support.
─────────────────────────────────────────────
END COPY  [Variant A]
─────────────────────────────────────────────

---

## VARIANT B: Confirmed Root Cause Analysis (use only when cause is confirmed by evidence or Engineering)

─────────────────────────────────────────────
COPY FROM HERE
─────────────────────────────────────────────
**Subject**: [Ticket number] — Root Cause Analysis

Hi [Customer name or team],

Following our investigation, I can now share the root cause and resolution for this case.

**Timeline**:
| Date/Time | Event |
|---|---|
| [timestamp] | [event] |
| [timestamp] | [first failure point] |
| [timestamp] | [resolution or mitigation] |

> Timestamps preserved as reported. All customer identifiers redacted.

**Confirmed root cause**:
[One clear sentence — confirmed by [customer confirmation / Engineering confirmation / reproducible evidence]. Do not use "likely" or "probably" in this section.]

**Evidence**:
- [evidence item 1 — ref + source]
- [evidence item 2]

**Validated remedy**:
[Step-by-step remediation — customer-safe, with exact UI paths or commands, risk notes, and rollback steps if applicable.]

**Prevention**:
[Optional — only if a preventive measure is validated and customer-appropriate.]

**References**:
- [Full URL 1]
- [Full URL 2]

Regards,
{{operator_name}} | {{operator_title}}
Available {{operator_availability}}
Thank you for choosing IBM Support.
─────────────────────────────────────────────
END COPY  [Variant B]
─────────────────────────────────────────────

---

> **Agent rule**: Use Variant A when the validation reviewer returned `verdict: conditional` or cause is pending Engineering confirmation.
> Use Variant B only when `verdict: validated` and cause is confirmed. Never label Variant A as an RCA.
