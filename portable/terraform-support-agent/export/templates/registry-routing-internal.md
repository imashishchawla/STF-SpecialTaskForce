# Template: registry-routing-internal.md — Internal Jira Collaboration Draft
# Classification: INTERNAL ONLY — never expose content to customer
# Requires: registry-routing skill has confirmed applicability
# Source: Interim process — verify current status in memory/ops/registry-routing.md before use

---

─────────────────────────────────────────────
COPY FROM HERE  [INTERNAL — do not send to customer]
─────────────────────────────────────────────

## ⚠️ INTERNAL ONLY — do not include in customer communication

---

## Registry Collaboration Case Draft

**Case alias**: [alias]
**Ticket number**: [real ticket number]
**Severity**: [Sev 1 / Sev 2 / Sev 3 / Sev 4]
**Customer type**: [paying HCP TF enterprise / self-managed]
**Entitlement status**: Public registry entitlement — [OFF in CSP (verified) / OFF in CSP (pending verification)]
**Process status**: INTERIM — verify current applicability with team before use

> Check `memory/ops/registry-routing.md` for whether Phase II has started. If Phase II is active, this process may be superseded.

---

### For Sev 2 / 3 / 4 — Jira Collaboration Case

**Path in CSP**:
1. Open the customer's case in CSP
2. Navigate to the case left panel
3. Click the dropdown → select "New Collaboration"
4. Set Remote Repository to: `Terraform - JIRA - Terraform Public Registry`
5. Fill in Subject (→ becomes Jira title)
6. Fill in Description (→ carries customer information)
7. Support Mission: defaults to `HashiCorp`

**Proposed Jira case content**:

**Subject (→ Jira title)**:
```
[One-sentence description of the registry issue — sanitized, no customer identifiers]
```

**Description (→ carries customer information)**:
```
Product: Terraform Public Registry
Issue: [Sanitized summary — what the customer is experiencing, affected registry item
        (module/provider name only — no customer org names or IDs), error observed, impact]
Severity: [current severity]
Customer tier: [enterprise / self-managed — no customer name]
```

**Support Mission**: HashiCorp

---

### For Sev 1 — PagerDuty Engagement

> ⚠️ PagerDuty engagement path requires current process verification.
> The exact steps must be confirmed with the team before use — see `memory/ops/registry-routing.md`.

Pending Phase 3 verification:
- [ ] Confirm current PagerDuty path for Sev 1 registry cases with team/manager
- [ ] Update `memory/ops/registry-routing.md` with verified steps
- [ ] Manager notification is required immediately for Sev 1

---

### For Out-of-Scope Customers (Free Tier / Partner / Community Edition)

Route to: `terraform-registry@hashicorp.com`

**Customer-appropriate draft wording** (do not reference internal routing):
```
This issue involves the Terraform Public Registry. I am escalating it to the appropriate team
who will follow up with you.
```

---

### Tracking checklist

- [ ] CSP collaboration case created (ID: _________)
- [ ] Jira case received (ID: _________)
- [ ] Engineering updated on case status
- [ ] Customer update sent (customer-appropriate wording only)
- [ ] SLA delay risk assessed — manager notified if delay anticipated
- [ ] Customer update sent after Engineering response

─────────────────────────────────────────────
END COPY
─────────────────────────────────────────────
