---
skill_id: terraform-diagnosis
version: "0.1.0-draft"
status: draft
source: portable/terraform-support-agent/export/skills/diagnosis.md
canonical: true
bob_generated: false
phase: 3
---

# Skill: diagnosis
> **Status**: Draft skeleton — not yet validated or active.
> Full specification: `docs/design/03-skills-and-templates.md §3`

## Purpose
Systematic analysis of supplied evidence to produce observations and ranked hypotheses with discriminating checks.

## Steps (condensed)
1. Reconstruct run timeline from log timestamps (preserve timezone offsets as-is — do not normalize)
2. Identify: Terraform version, provider versions, backend type, workspace/org type
3. Identify: exact error message(s), error codes, module/resource paths
4. Extract: last successful state, first failure point, any retry behavior
5. Compare working vs failing if both are in supplied evidence
6. Map each error/observation to a hypothesis with supporting and conflicting evidence
7. For each hypothesis: identify one discriminating check that would confirm or exclude it
8. Flag: configuration patterns known to cause false positives or confusing errors

## Known initial candidate patterns to check
- VCS credential failures: OAuth token expiry vs webhook secret mismatch vs repo permission change
- Azure DevOps webhook events: push event format vs branch filter vs workspace trigger config
- Agent plan/resource failures: agent pool capacity vs network vs provider auth within agent container
- Run concurrency: auto-queue vs concurrency limit vs run discard threshold
- Pending state upload: network interruption vs state lock vs version conflict
- Variable-set scope: apply scope vs workspace variable override precedence
- SSO/IP restriction: SSO enforcement vs team/workspace membership vs IP allowlist vs SAML assertion
- Audit log gaps: audit trail coverage limitations per plan tier

## Output format (DiagnosticsOutput)
```
observations: [string]          — confirmed facts from evidence
hypotheses:
  - id: H-<n>
    statement: <cause claim>
    supporting_evidence: [ref]
    conflicting_evidence: [ref]
    confidence: low|medium|high
    discriminating_check: <one check to confirm or exclude>
unresolved: [string]            — gaps or missing evidence
```

## Memory pattern confidence rules (G002)

When a hypothesis originates from a `memory/patterns/` entry:

1. **Always check the `freshness` field** before using the pattern
2. **If `freshness: possibly_stale` or `freshness: stale`**:
   - Downgrade hypothesis confidence by one level (e.g., `high` → `medium`, `medium` → `low`)
   - Label the hypothesis: `"pattern-based (possibly stale — see stale_reason)"`
   - Do NOT use the pattern's discriminating check as current without verifying it against a current source first
   - Instruct Source Researcher to verify the specific claim the pattern makes against current documentation
3. **If `freshness: current`** or no freshness field: use the pattern's confidence as-is, still labeled "pattern-based"
4. **After source verification**: update the hypothesis label to "pattern-confirmed" or "pattern-outdated" based on the result
5. **Never treat a `possibly_stale` pattern as confirmed** regardless of its recorded confidence level

> Stale patterns are leads, not answers. The correct action is: surface the pattern, flag its staleness, trigger a source check, then update confidence after verification.

## Candidate patterns seed investigation only. None are treated as confirmed causes without evidence.
