---
schema_version: 1
process_status: current
last_verified: "2026-10-02"
owner: support-engineer
visibility: internal-only
---

# memory/ops/escalation-paths.md

> **Internal only.** Nothing from this document may appear in customer-visible drafts.
> Verify `last_verified` date before operational use. Re-verify after any IBM/HashiCorp process change.

---

## Purpose

When and how to escalate a Terraform support case — covering severity upgrades, PagerDuty engagement, manager notification, and Engineering escalation.

---

## Escalation decision tree

```
Is the customer fully blocked (no workaround) AND business-impacting?
 └─ Yes → Is this production with financial / compliance impact?
       ├─ Yes → Consider Sev 1 / Sev 2 upgrade + PagerDuty (see §2)
       └─ No  → Sev 3 standard path, engineer-led
 └─ No → Continue standard investigation
```

> **Rule**: The agent proposes an escalation path — the operator executes it after reviewing. The agent never pages PagerDuty or updates severity independently.

---

## §1 — Severity upgrade

### Criteria

| Severity | Criteria |
|---|---|
| Sev 1 | Production system fully down, no workaround, active customer impact |
| Sev 2 | Significant functionality impaired, workaround exists but unacceptable for production |
| Sev 3 | Non-critical impairment or limited impact |
| Sev 4 | General questions, low-priority improvements |

### How to upgrade severity

1. In CSP: open the case → **Edit** → update **Severity** field
2. This is an `approval_class: severity_change` action — requires explicit per-action approval before the agent proposes the step
3. After upgrade: notify direct manager (see §3)

---

## §2 — PagerDuty engagement (Sev 1 only)

> PagerDuty engagement is an `approval_class: pagerduty_engagement` action.
> The agent produces a draft engagement summary — the operator executes the page.

### When to page

- Sev 1 confirmed AND no Engineering response within SLA
- Sev 1 confirmed AND customer has a time-critical external dependency (release, compliance deadline)

### Steps (operator executes — agent produces draft only)

1. Confirm current on-call Engineering contact via the IBM/HashiCorp internal PagerDuty schedule
2. Create a PagerDuty incident with:
   - **Title**: `[Sev 1] <brief issue summary> — Case #<ticket_number>`
   - **Body**: product scope, customer type, exact error, steps taken so far, customer impact statement
   - **Service**: route to the correct HashiCorp Engineering service for the product scope
3. Add the PagerDuty incident link to the CSP case internal note
4. Notify direct manager (see §3)
5. Inform customer of escalation using customer-safe wording only:
   > "We have escalated this to our Engineering team for urgent review. We will update you as soon as we have more information."

### What the agent produces

An internal draft containing:
- Suggested PagerDuty title and body (customer-identifiers replaced with case alias)
- Customer-safe update text for the case
- Manager notification draft

---

## §3 — Manager notification triggers

Notify your direct manager when **any** of the following occur:

| Trigger | When |
|---|---|
| Sev 1 case opened or upgraded | Immediately |
| Sev 2 case approaching SLA breach | At 75% of SLA elapsed |
| PagerDuty page sent | Immediately after page |
| Customer escalation request (customer asks for manager) | Immediately |
| Engineering investigation stalled > 5 business days | Flag proactively |
| Case requires urgent registry routing (Sev 1 Public Registry) | Before routing |
| Anticipated SLA delay due to Engineering dependency | As soon as identified |

### Notification method

- Slack DM to direct manager (preferred for Sev 1 / urgent)
- Email for non-urgent flags
- Include: case alias, ticket number, severity, customer impact, current status, and your proposed next action

---

## §4 — Engineering escalation (non-Sev-1)

When an investigation reaches a confirmed product bug or regression with no customer workaround:

1. Open a **Jira collaboration case** (see `registry-routing.md` for registry-specific path; for core/provider bugs, use the standard Engineering collaboration queue)
2. Include: reproducible steps, exact versions, error output, discriminating check result, customer impact
3. Link the Jira collaboration case to the CSP case
4. Update the CSP case stage to `AWAITING_ENGINEERING`
5. Set a follow-up reminder for the next SLA checkpoint
6. Customer update: use `internal-update.md` template for internal tracking, `customer-reply.md` for customer communication — separate drafts, never mixed

---

## §5 — SLA reference (general guidance — verify current SLA in CSP)

| Severity | First Response | Subsequent Updates |
|---|---|---|
| Sev 1 | 1 hour | Every 2 hours until resolved |
| Sev 2 | 4 business hours | Every 8 business hours |
| Sev 3 | 1 business day | Every 2 business days |
| Sev 4 | 2 business days | Every 5 business days |

> Verify exact SLA values in the customer's contract or CSP — these are illustrative, not contractual.

---

## §6 — MCP tool integration (Phase 4+)

When Jira and CSP MCP connectors are active (Phase 4), the coordinator will be able to:
- Query current SLA elapsed time from CSP via read-only API
- Draft Jira collaboration cases with pre-populated fields
- Check Engineering case status without manual navigation

Until then, all steps above are manual and require operator execution after agent draft review.

> **Phase 4 note**: Update this document with specific MCP query patterns once the Jira and CSP connectors are allowlisted and enabled.

---

## Related

- [`entitlement-checks.md`](entitlement-checks.md) — entitlement verification before routing
- [`registry-routing.md`](registry-routing.md) — registry-specific routing process
- [`docs/design/06-registry-routing.md`](../../docs/design/06-registry-routing.md) — full routing design
- [`export/templates/internal-update.md`](../../export/templates/internal-update.md) — internal case note template
- [`export/templates/can-report.md`](../../export/templates/can-report.md) — Customer Advocacy Notification
