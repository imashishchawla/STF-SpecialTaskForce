# Visa cost aggregator

Follow [operating_contract.md](./operating_contract.md). Activate only when the user needs a cost breakdown for a specific Australian skilled migration visa pathway. Do not present estimates as fixed quotes or final assessments.

## Purpose

Given a visa subclass (189, 190, 491, 482, 186, or 600), return a complete fee breakdown covering:
- Visa application fee (main applicant and dependants)
- Skills assessment fee (by occupation and assessing authority)
- Health examination cost estimate
- Police clearance cost estimate
- State nomination/sponsorship fee (if applicable)
- Employer sponsorship fee (if applicable)

## Input contract

Receive: visa subclass (e.g., 189), candidate circumstances (e.g., "ICT professional with Bachelor degree, single, from NSW").

Do not process:
- Specific names, dates of birth, or passport details
- Family composition or relationship status beyond "single", "with partner", "with N children"
- Raw employment history or salary records
- Immigration status or previous visa history

## Process

1. Verify the visa subclass against the canonical data file `knowledge/australia/visa_costs.json`. Confirm the visa stream (permanent/provisional/temporary) and primary visa fee.

2. For skills assessment: Identify the occupation and qualification level. Cross-reference the appropriate assessing authority (ACS, Engineers Australia, VETASSESS, TIA). Record the estimated assessment fee range and note that actual costs vary by submission type.

3. For health and police: Record the estimated ranges. Note that health examination is mandatory for all permanent/provisional visas; police clearance requirements depend on risk assessment but are typical. Include state-specific police clearance costs.

4. For state nomination (Subclass 190, 491 only): Identify the state of nomination. Record the sponsorship fee from the state portals. Note that some states have tiered systems or additional requirements.

5. For employer-sponsored visas (482, 186): Clarify whether the applicant or employer pays which costs. Record employer-typical costs separately.

6. Calculate estimated totals: minimum (lowest component costs) and maximum (highest component costs). Include a cautionary note on the range.

Return formatted output with:
- `visa_subclass` + name
- `visa_stream` (permanent/provisional/temporary)
- `primary_visa_fee_aud` (main + per dependent if applicable)
- `assessment_fee_estimate_aud` (range, by authority)
- `health_examination_aud` (range, note mandatory)
- `police_clearance_aud` (range, by state)
- `state_nomination_aud` (if applicable, by state)
- `employer_costs_aud` (if applicable, note who pays)
- `total_estimated_min_aud`
- `total_estimated_max_aud`
- `cost_breakdown_summary` (itemized list with sources)
- `next_steps` (how to verify each component)
- `assumptions` (unmarried, single applicant, no dependants unless stated)
- `verification_status` (all estimates flagged as "provisional" and "requires_official_confirmation")

## Output contract (JSON example)

```json
{
  "visa_subclass": "189",
  "visa_name": "Skilled Independent",
  "visa_stream": "permanent",
  "cost_breakdown": {
    "visa_fee": {
      "main_applicant_aud": 4035,
      "description": "Home Affairs application fee for primary visa holder"
    },
    "assessment_fee": {
      "estimate_aud": "400-500",
      "authority": "ACS (for ICT roles)",
      "qualification_level": "Bachelor",
      "note": "Actual cost depends on employment verification requirements"
    },
    "health_examination": {
      "estimate_aud": "300-600",
      "note": "Mandatory. Varies by location and medical complexity"
    },
    "police_clearance": {
      "estimate_aud": "90 (NSW)",
      "provider": "NSW Police",
      "note": "Required for all applicants aged 16+"
    },
    "state_nomination": {
      "not_applicable": true,
      "reason": "Subclass 189 is independent; no state sponsorship required"
    },
    "employer_costs": {
      "not_applicable": true
    }
  },
  "totals": {
    "total_estimated_min_aud": 4815,
    "total_estimated_max_aud": 5625,
    "currency": "AUD",
    "note": "Estimate for planning only. Does not include postage, courier, translation services, or other incidental costs."
  },
  "cost_summary": "Visa fee ($4,035) + Assessment ($400–500) + Health exam ($300–600) + Police clearance ($90) = $4,815–$5,625 AUD",
  "next_steps": [
    "Verify current visa fees on https://immi.homeaffairs.gov.au/visas/getting-a-visa/fees-and-charges",
    "Confirm assessment fee with chosen assessing authority (e.g., ACS at https://www.acs.org.au/msa/infohub)",
    "Get health examination quote from local IME panel doctor",
    "Check state police clearance cost for applicable state"
  ],
  "assumptions": [
    "Single applicant, no dependants",
    "Qualification assessed as equivalent to Bachelor degree",
    "No family members included"
  ],
  "verification_status": "provisional",
  "verification_date": "2026-11-15",
  "warning": "These are estimates based on historical fee schedules. All fees require verification against current Home Affairs and assessing authority websites before application submission. Home Affairs indexation occurs 1 July annually."
}
```

## Limitations and uncertainty

- Health examination costs vary significantly by location and IME provider. Estimates are averages only.
- State nomination fees change; always verify against current state portal.
- Assessment fees depend on qualification equivalency and employment verification requirements; contact assessing authority directly.
- Police clearance fees vary by state and may change annually.
- 482 and 186 visa employer costs are not visible to the applicant; note they are employer responsibility and may be covered or negotiated separately.
- A fresh case or changed circumstances may affect applicable fees; re-verify before each application cycle.

## Sources

- Home Affairs fee and charges: https://immi.homeaffairs.gov.au/visas/getting-a-visa/fees-and-charges
- Individual visa subclass pages: https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing
- ACS assessment fees: https://www.acs.org.au/msa/infohub
- State nomination portals: (See visa_costs.json state section)
- AFP National Criminal Record Check: https://www.afp.gov.au/what-we-do/national-criminal-record-check

## Data file reference

All cost data sourced from and synchronized with:
`knowledge/australia/visa_costs.json` (version 1.0.0, status: draft, last verified 2026-11-15)
