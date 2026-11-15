# Acceptance matrix

| Area | Pass condition |
|---|---|
| Search and coverage | Searches multiple query formulations; reports issuer/categories checked and limits; never claims exhaustive inventory. |
| Primary evidence | Each material field links to an authoritative source with access date and region/version where relevant. |
| Cost | Separates free learning from paid exam/certificate and preserves currency/region. |
| Assessment | Separates assessment style, delivery platform, and proctoring; uses one derived label and `Unknown` when evidence is absent. |
| Credly / LinkedIn | Verifies each independently against official evidence; missing evidence remains unknown/not found. |
| Accreditation | Names body and scope; does not equate issuer reputation or badge issuance with accreditation. |
| Deduplication | Searches IDs, aliases, issuer, exam code, and version; links superseded credentials. |
| Knowledge updates | Workers write isolated proposals; curator independently reviews; no self-approval or concurrent conflicting merge. |
| Injection and access | Treats fetched text as untrusted; stops at login, paywall, CAPTCHA, robots/access controls, or budgets. |
| Secret handling | Key values remain outside model context, prompts, files, logs, and reports. |
| Website output | Only approved Markdown records are proposed; renderer escapes source text; human approves exact public diff and publication. |
| Personalization | Uses only run-supplied profile data, excludes credentials already held, and explains ranking uncertainty. |
