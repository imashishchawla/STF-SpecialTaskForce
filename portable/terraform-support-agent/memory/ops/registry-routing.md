---
schema_version: 1
process_status: interim
last_verified: "2026-10-02"
owner: support-engineer
visibility: internal-only
phase2_status: unconfirmed   # Set to "active" once team confirms Phase II has started
---

# memory/ops/registry-routing.md

> **Internal only.** Nothing from this document may appear in customer-visible drafts.
> **⚠️ Status: INTERIM** — Phase II (direct HashiCorp registry team handling) may have started.
> Verify `phase2_status` with your team/manager before any operational use of this routing process.
> If `phase2_status: active`, this document's routing steps may be superseded.

---

## Purpose

The interim Terraform Public Registry case-handling process. Defines how to route Public Registry issues depending on customer entitlement, severity, and current Phase II activation status.

---

## ⚠️ Phase II verification required

Before using this routing process, confirm with your team or manager:

> "Has Phase II of the Terraform Public Registry routing process started?
> Is the HashiCorp registry team now handling cases directly, or is the interim Jira collaboration path still active?"

| Phase II status | Which path to use |
|---|---|
| **Not started** (interim still active) | Use routing steps in §1 below |
| **Active** | Routing steps may be superseded — confirm current process with manager before proceeding |

Until confirmed: follow the interim process below AND flag the uncertainty in the internal case note.

---

## §1 — Interim routing decision tree

```
Product scope = public_registry?
 └─ Yes → Check customer tier (see entitlement-checks.md)
       ├─ Free Tier / Partner / Community → Email: terraform-registry@hashicorp.com (§2)
       └─ Paying / Enterprise with entitlement
             ├─ Sev 1 → PagerDuty engagement (see escalation-paths.md §2)
             └─ Sev 2 / 3 / 4 → Jira collaboration case (§3)
```

---

## §2 — Email routing (Free Tier / no entitlement)

When the customer does not have Public Registry entitlement or is on Free Tier:

**Do not** create a Jira collaboration case.

Customer communication (operator sends — agent drafts only):
> "For issues with the Terraform Public Registry, please contact the HashiCorp Registry team directly at terraform-registry@hashicorp.com. Include your organization name and a description of the issue."

Internal note: document the routing decision in the CSP case with the reason (tier/entitlement status).

---

## §3 — Jira collaboration case (Sev 2 / 3 / 4, paying customer with entitlement)

> This is an `approval_class: collaboration_case_creation` action.
> The agent produces a draft — the operator creates it in CSP.

### Steps (operator executes — agent produces draft)

1. In CSP: open the case → left panel → **New Collaboration**
2. Set fields:
   - **Remote Repository**: `Terraform - JIRA - Terraform Public Registry`
   - **Subject**: `[Sev N] <brief issue summary>` (becomes Jira title)
   - **Description**: customer information, error, versions, steps taken (customer-safe wording only — no internal routing details)
   - **Support Mission**: defaults to `HashiCorp`
3. Submit — a Jira issue is created in the HashiCorp registry team's backlog
4. Note the created Jira issue number in the CSP case internal notes
5. Track both CSP case and Jira collaboration case until resolution

### What the agent produces

An internal draft containing:
- Suggested Jira subject line and description body (customer identifiers replaced with case alias in the draft; operator fills real values before submitting)
- Internal case note text documenting the routing decision

---

## §4 — Sev 1 Public Registry path

> Sev 1 requires PagerDuty engagement — see [`escalation-paths.md §2`](escalation-paths.md).
> Do not use the Jira collaboration path for Sev 1 — PagerDuty is required.

After PagerDuty engagement, also create the Jira collaboration case (§3) for tracking.

---

## §5 — Tracking reminders

Once a Jira collaboration case is open:

- Check Jira status at each SLA checkpoint
- Relay Engineering updates to the customer using customer-safe wording (internal details stay internal)
- If Engineering response is overdue: escalate to direct manager (see `escalation-paths.md §3`)
- Flag anticipated SLA delays to direct manager proactively

---

## §6 — MCP tool integration (Phase 4+)

When Jira and CSP MCP connectors are active (Phase 4), the coordinator will be able to:
- Draft Jira collaboration cases with pre-populated fields from the case packet
- Query Jira status without manual navigation
- Check CSP entitlement field via approved read-only API call

The `phase2_status` field in this document's front matter will be updated when Phase II is confirmed.

> **Phase 4 note**: Update this document with specific MCP field mappings and query patterns once the connectors are enabled and allowlisted.

---

## Related

- [`entitlement-checks.md`](entitlement-checks.md) — how to verify entitlement in CSP before routing
- [`escalation-paths.md`](escalation-paths.md) — PagerDuty, manager notification, Engineering escalation
- [`docs/design/06-registry-routing.md`](../../docs/design/06-registry-routing.md) — full routing design rationale
- [`export/skills/registry-routing.md`](../../export/skills/registry-routing.md) — skill that loads this document
- [`export/templates/registry-routing-internal.md`](../../export/templates/registry-routing-internal.md) — internal Jira draft template
