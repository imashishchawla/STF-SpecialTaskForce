---
skill_id: terraform-registry-routing
version: "0.1.0-draft"
status: draft
source: portable/terraform-support-agent/export/skills/registry-routing.md
canonical: true
bob_generated: false
phase: 3
classification: internal-only
---

# Skill: registry-routing
> **Status**: Draft skeleton — not yet validated or active.
> Full specification: `docs/design/03-skills-and-templates.md §5`
> **⚠️ Internal only**: No detail from this skill may appear in customer-visible drafts.
> **⚠️ Verification required**: Process marked interim (review date: 2 October 2026). Verify current applicability before operational use.

## Purpose
Apply the interim Terraform Public Registry case-handling process when applicable.

## Applicability check (coordinator must verify all before invoking)
```
Required:
  - Product scope = public_registry
  - Customer type = paying/enterprise HCP Terraform OR self-managed under entitlement conditions
  - Entitlement condition = public registry entitlement is OFF in CSP

Route to terraform-registry@hashicorp.com instead if:
  - Customer type = Free Tier / Partner / Community Edition
```

## Steps when applicable (Sev 2 / 3 / 4)
1. Confirm entitlement status from coordinator's scope classification
2. Determine severity from current case severity field
3. Prepare Jira collaboration case request draft for coordinator's output:
   - Path: CSP case left panel → New Collaboration
   - Remote Repository: "Terraform - JIRA - Terraform Public Registry"
   - Subject: becomes Jira title
   - Description: carries customer information
   - Support Mission: defaults to "HashiCorp"
4. Output: internal collaboration case draft — **the operator creates it, the agent never creates it**

## Steps when applicable (Sev 1)
1. Prepare PagerDuty engagement path draft for coordinator's output
2. Output: internal engagement steps — **the operator executes, the agent never pages independently**

## Tracking reminders (internal)
- Track both CSP case and Jira collaboration case
- Keep Engineering informed per process
- Relay appropriate Engineering updates to customer (customer-safe wording only)
- Flag anticipated SLA delays to direct manager

## Output
Internal-only draft with the above steps. Never populate a customer reply with internal routing details.
