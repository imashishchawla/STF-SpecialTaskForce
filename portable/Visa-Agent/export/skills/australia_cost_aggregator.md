---
skill_id: australia_cost_aggregator
version: 1.0.0
status: draft
canonical: true
source: portable/Visa-Agent/export/skills/australia_cost_aggregator.md
bob_generated: false
phase: 1
---

# Australian visa cost aggregator skill

## When to use this skill

When a client or consultant needs to understand the cost components of applying for an Australian skilled migration visa. Use this skill to:

- Provide a transparent cost breakdown by visa subclass
- Estimate total out-of-pocket costs for visa application, assessment, health, and police
- Identify state-specific costs for state-nominated visas (190, 491)
- Clarify who bears which costs (applicant vs. employer)
- Set realistic expectations before application begins

**Activate only for visa subclasses 189, 190, 491, 482, 186, 600.**

Do not use this skill for:
- Legal advice on visa eligibility
- Negotiation of employer sponsorship terms
- Final cost quotes (all outputs are estimates for planning)
- Calculating points or ranking chances

## How the coordinator calls this skill

The master coordinator routes cost queries to this skill with:

```
task: cost_aggregator
visa_subclass: "189" | "190" | "491" | "482" | "186" | "600"
candidate_circumstances: "brief description" (occupation, qualification level, state if known)
output_format: "json" (default) or "text" (human-readable summary)
```

Example: 
```
visa_subclass: "190"
candidate_circumstances: "Software engineer, Bachelor in Computer Science, nominated for NSW"
output_format: "json"
```

The coordinator does **not** pass:
- Full names or personal identifiers
- Dates of birth or passport details
- Complete family composition
- Raw documents or lengthy case text

## What this skill outputs to the coordinator

A structured packet containing:

1. **Visa fee** — Application fee from Home Affairs for subclass (per main applicant and dependants)
2. **Assessment fee** — Skills assessment cost by occupation and assessing authority (range and note on variations)
3. **Health examination** — Estimate with location sensitivity
4. **Police clearance** — State-specific cost estimate and provider
5. **State nomination** (if applicable) — State-specific sponsorship fee
6. **Employer costs** (if applicable) — Note on employer responsibility; applicant does not pay visa fees for 482/186
7. **Totals** — Minimum and maximum estimated total cost (AUD)
8. **Cost breakdown summary** — Itemized text for client presentation
9. **Next steps** — How to verify each component (official URLs, contact details)
10. **Verification status** — All marked as "provisional" and flagged for official confirmation
11. **Assumptions** — Single applicant, no dependants, unless stated (no PII stored)

## Skill context and constraints

- **Data source**: `knowledge/australia/visa_costs.json` (version 1.0.0, status: draft)
- **Access date**: 2026-11-15 (requires periodic verification against Home Affairs)
- **Accuracy**: Draft status. All estimates require official confirmation before application.
- **Currency**: Australian Dollars (AUD)
- **Indexation**: Home Affairs indexes fees 1 July annually; estimates may change

## How clients use this skill's output

The cost breakdown is presented via the master coordinator:
- As a transparent cost estimate table for client decision-making
- Embedded in visa pathway summaries (showing visa, assessment, and total costs side-by-side)
- In client roadmap timelines (noting when costs are due)
- In fee comparison documents (comparing routes 189 vs. 190 vs. 491)

Clients should always:
1. Verify current fees on Home Affairs website before submitting applications
2. Contact their assessing authority (ACS, Engineers Australia, etc.) for exact assessment fees
3. Check state portals for current sponsorship fees
4. Get quotes from local health providers and police services

## Skill limitations and handoff

- **Cannot calculate grant probability or visa strength** — that requires a separate eligibility assessment
- **Cannot advise on visa strategy** — cost alone does not determine the best route (speed, points, spouse points, etc. also matter)
- **Cannot provide payment arrangement advice** — that requires legal/financial consultation
- **Cannot process live or sensitive data** — all input is summarized; no PII stored or transmitted

If a client's circumstances change (partner, children, different state nomination), re-run the skill with updated parameters. Each calculation is independent.

## Skill validation checklist

Before using this skill in production:

- [ ] Verify all visa fees against current https://immi.homeaffairs.gov.au/visas/getting-a-visa/fees-and-charges
- [ ] Confirm ACS, Engineers Australia, VETASSESS, and TIA assessment fees against official sites
- [ ] Check all state nomination fees against state portals (NSW, VIC, QLD, SA, WA, TAS, NT, ACT)
- [ ] Verify AFP police clearance costs and state-specific variations
- [ ] Update `knowledge/australia/visa_costs.json` with any changes
- [ ] Test output formatting with at least one client scenario (e.g., ICT/189, Engineer/190-NSW, Nurse/491-QLD)
- [ ] Document any discrepancies found during verification
- [ ] Mark skill status as "active" once all checks pass

## Handoff to human review

This skill is marked `status: draft` until human verification is complete. Do not advertise to clients or reference in formal advice until production-ready.

---

**Canonical source**: `portable/Visa-Agent/export/skills/australia_cost_aggregator.md`  
**Data file**: `portable/Visa-Agent/knowledge/australia/visa_costs.json`  
**Agent reference**: `.agents/agent_cost_aggregator.md`  
**Last reviewed**: 2026-11-15  
**Next review**: 2027-02-15 (or after any Home Affairs fee announcement, whichever comes first)
