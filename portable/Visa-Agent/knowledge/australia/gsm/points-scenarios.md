> **Source:** Adapted from ScriptSavvy's AustraliaVisaSkills
> License: CC BY-NC 4.0 | Attribution: ScriptSavvy/Immigent

# Conditional points ranges

## Purpose and required labels
When an applicant answers unsure, skips a fact, cannot supply readable evidence, or leaves a material question unresolved, retain the uncertainty and continue independent checks. Do not repeatedly demand an answer they cannot provide. Offer the smallest useful evidence request once; revisit only if new information or a material decision requires it.

At the end, show three distinct outputs:
- **Provisional evidence-supported subtotal:** only reviewed supported factor values, with factual and legal-currency limits. It can be incomplete and is not necessarily the lower scenario total.
- **Lower scenario total:** minimum across the defensible, compatible scenarios covered by this assessment.
- **Upper scenario total:** maximum across those same scenarios, not an invitation prediction, approval probability, guaranteed entitlement or permission to claim that score in an EOI.

Call the interval a **conditional points range under stated assumptions**. Say whether it covers all relevant factors or only named factors. A range does not verify an unknown fact. Do not present every intermediate integer as attainable; scores may occur only in discrete combinations.

## Build defensible scenarios
1. Reuse the claims ledger, scope, invitation/assessment dates and applicable factor rules. Preserve supported facts. Do not substitute future achievements for invitation-time requirements.
2. For each unresolved issue record an ID, question, uncertainty type (fact, evidence, applicability or law), relevant rule/source, feasible alternatives, affected factors and evidence/clarification needed. Do not assume both yes and no are possible when known facts rule one out.
3. Use qualifying/non-qualifying branches for a genuinely binary claim. For English, employment, education or partner categories, enumerate the relevant category alternatives instead of reducing them to yes/no. Never manufacture all maximum categories solely because evidence is missing. A band domain must be grounded in known facts and applicable rules, or explicitly restricted to a named planning assumption.
4. Connect shared assumptions. For example, regional-study points require the Australian study requirement as well as their additional tests: an Australian-study failure cannot coexist with an affirmative regional-study award. Shared study, work, relationship or date assumptions must be consistent across every affected factor. Do not automatically change specialist-education points merely because ordinary Australian study changes; their tests differ.
5. Select only one mutually exclusive category per factor. Apply the combined employment cap after assigning both employment factors in each scenario. Do not add independent maximum bonuses that cannot coexist. Document why a joint scenario is feasible; arithmetic alone does not establish that.
6. Calculate complete compatible factor assignments mechanically using a host calculator or the existing total_points.py helper separately for each assignment. The helper does not generate scenarios or enforce cross-factor dependencies: the agent must establish those before using it. For large combinations use host-side deterministic enumeration of reviewed domains and constraints; do not estimate endpoints mentally or silently sample combinations and call them global bounds. If exhaustive enumeration is impractical, report named scenarios, not an asserted overall minimum/maximum.
7. Take the minimum and maximum of the totals actually calculated over the complete defensible scenario set. Retain at least one full factor assignment and its assumption IDs supporting each endpoint. Account for every relevant factor or mark the interval partial. Do not send null factors to the helper and interpret its partial subtotal as a complete scenario total.

## Legal conflicts, missing bounds and fixed failures
A factual yes/no branch is different from a conflicting interpretation of law. Show legal interpretations separately with their supporting source positions, dates and unresolved authority. Their numerical effects may form an expressly interpretation-dependent range only where the alternatives and point values can be identified defensibly. Neither endpoint resolves the conflict. Unknown legal bands or insufficient scope/dates may prevent a defensible numerical bound; say **range not yet calculable** or **partial range excluding [factors]**, with the exact reason. Do not use a theoretical universal maximum to fill gaps.

Confirmed failures remain failures, not optimistic alternatives. A condition acquired only after invitation is not a valid upper scenario for an actual invitation-date claim. A missing document is not proof of non-qualification. A lower scenario assigning no points to an uncertain claim is a planning assumption, not a finding of zero entitlement or Not applicable. An applicant declaration can support a declared scenario, not inspected evidence.

If no relevant uncertainty remains, endpoints may be equal; describe a provisional point estimate, not an artificial uncertainty interval. Legal-currency limits still apply. Do not infer complete visa eligibility from a calculable total.

## Applicant-facing report
Start standalone reports with the skill's full notice. Use the report template and include:
- Evidence-supported subtotal, conditional lower–upper range and scope/currency limits.
- Concise assumptions for each endpoint and any excluded factors.
- An unresolved-issue table: issue, alternatives, effect on points, dependencies, and smallest next action. This may be the same table as the points/evidence ledger when all these fields are visible; do not duplicate the same issue, scenario effect and action in a second table solely to follow headings. Keep endpoint assignments, scope and unresolved-authority details explicit.
- Priorities based on the actual change to compatible totals, urgency and invitation-score impact. A factor's nominal points are not necessarily its effect after caps/dependencies. Do not add issue impacts as though independent; state the held-fixed scenario used for any quoted difference.
- For known and verified invitation/qualifying scores, distinguish all covered scenarios below, scenarios on both sides, and all covered scenarios meeting the comparison. Unknown targets stay unresolved. Passing either comparison is not visa eligibility or an invitation guarantee.

Explain plainly: 'The lower total assumes these unresolved claims do not qualify. The upper total assumes the listed qualifying conditions are met and can be supported. These assumptions are not confirmed facts.' Do not tell the applicant to select a favourable answer or submit the upper score as verified.

Keep assumptions and scenario results in the applicant report, not in reusable policy files. Preserve the ledger, endpoint assignments, excluded factors and unresolved authority in handoff to later subclass skills.
