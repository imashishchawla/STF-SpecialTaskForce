---
schema_version: 1
process_status: current
last_verified: "2026-10-02"
owner: support-engineer
visibility: internal-only
---

# memory/ops/entitlement-checks.md

> **Internal only.** Nothing from this document may appear in customer-visible drafts.
> Verify `last_verified` date before operational use. Re-verify after any CSP or HashiCorp process change.

---

## Purpose

How to verify whether a customer's organization has **Terraform Public Registry entitlement** active in the Customer Support Portal (CSP). Required before invoking the `registry-routing` skill.

---

## When to check entitlement

The `registry-routing` skill requires the coordinator to confirm the customer's entitlement status before routing. Check entitlement when:

- Product scope is `public_registry`
- Customer reports an issue with modules or providers on `registry.terraform.io`
- You need to determine whether to route via Jira collaboration or `terraform-registry@hashicorp.com`

---

## How to check entitlement in CSP

1. Open the customer's case in the Customer Support Portal (CSP)
2. Navigate to the **Account** section on the case left panel
3. Look for the **Entitlements** or **Products** section
4. Locate the entry for **Terraform Public Registry**
5. Note the status: `active` / `inactive` / `not listed`

### Interpretation

| CSP Status | Meaning | Routing |
|---|---|---|
| `active` | Customer has Public Registry entitlement | → Jira collaboration (see `registry-routing.md`) |
| `inactive` | Entitlement exists but is off | → Email: `terraform-registry@hashicorp.com` |
| `not listed` | No Public Registry entitlement | → Email: `terraform-registry@hashicorp.com` |

---

## Customer tier mapping (when entitlement field is unclear)

| Customer tier | Entitlement assumption | Confirm in CSP |
|---|---|---|
| HCP Terraform Plus / Business | Likely active | Verify in CSP |
| HCP Terraform Free Tier | No entitlement | Route to email directly |
| Terraform Enterprise (self-managed) | Depends on contract — check CSP | Verify in CSP |
| Partner / NFR account | No entitlement | Route to email |

---

## If CSP entitlement field is missing or unclear

1. Do **not** assume entitlement
2. Escalate to your direct manager or senior support engineer for entitlement clarification
3. While clarifying, treat the case as **no entitlement** (email routing) — more conservative path
4. Document the ambiguity in the internal case note before routing

---

## MCP tool path (Phase 4+)

When the Terraform MCP connector is active (Phase 4), the coordinator will be able to query entitlement status directly via approved read-only API calls. Until then, use the CSP manual steps above.

> **Phase 4 note**: Update this document with the specific MCP query and field name once the allowlist review is complete and the connector is enabled.

---

## Related

- [`registry-routing.md`](registry-routing.md) — routing decision tree once entitlement is confirmed
- [`escalation-paths.md`](escalation-paths.md) — manager and PagerDuty paths
- [`docs/design/06-registry-routing.md`](../../docs/design/06-registry-routing.md) — full routing design
