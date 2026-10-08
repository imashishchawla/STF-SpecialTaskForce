# Template: handoff.md — Shift Handoff
# Classification: INTERNAL ONLY — never send to customer
# Requires: All current investigation state, evidence refs, pending auth-required actions listed

---

─────────────────────────────────────────────
COPY FROM HERE  [INTERNAL — do not send to customer]
─────────────────────────────────────────────

## Handoff — [ISO date] from {{operator_name}}

**Case alias**: [alias — not the real ticket number in internal drafts]
**Ticket number**: [real ticket number — include for incoming engineer's reference]
**Stage**: [INTAKE / INVESTIGATING / AWAITING_CUSTOMER / AWAITING_ENGINEERING / VALIDATING / RESOLVED]
**Severity**: [current severity]
**Product scope**: [HCP TF / TFE / Public Registry / Private Registry / Terraform Core / Provider / CLI]
**Customer type**: [paying enterprise / self-managed / Free Tier / etc.]

---

### Summary (2–3 sentences)

[What the customer is experiencing, current investigation state, and what is needed next.]

---

### Evidence collected

| Ref | Item | Status |
|---|---|---|
| E1 | [evidence description — redacted] | reviewed |
| E2 | [evidence description — redacted] | pending |

---

### Investigation state

**Current ranked hypotheses**:
- H1 (confidence: medium): [one-line statement] — supporting: [E1] — conflicting: [E2]
- H2 (confidence: low): [one-line statement] — discriminating check still needed

**Discriminating check outstanding**:
[Describe the one check that would confirm or exclude the top hypothesis.]

---

### Outstanding items

| Item | Owner | Status |
|---|---|---|
| [specific missing evidence] | customer | awaiting |
| [Engineering query] | Engineering | escalated [date] |

---

### Immediate next action for incoming engineer

[Single, specific action — e.g. "Wait for customer response to Q about run logs, then run the E1 discriminating check."]

---

### Auth-required actions pending

[List any actions that require explicit per-action approval before execution.
If none: write "None".]

> **Note**: All auth-required actions must be re-approved by the incoming engineer before execution.
> Do not inherit approval from the outgoing shift.

---

─────────────────────────────────────────────
END COPY
─────────────────────────────────────────────

<!-- RULES (strip before sending) -->
<!-- ✅ Internal only — do not include in any customer-visible update -->
<!-- ✅ Signature token {{operator_name}} resolves from memory/preferences.md -->
<!-- ❌ Must not: expose this document to the customer -->
<!-- ❌ Must not: carry auth approvals across shifts — each action needs fresh approval -->
