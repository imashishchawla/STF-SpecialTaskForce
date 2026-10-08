---
skill_id: terraform-source-check
version: "0.1.0-draft"
status: draft
source: portable/terraform-support-agent/export/skills/source-check.md
canonical: true
bob_generated: false
phase: 3
---

# Skill: source-check
> **Status**: Draft skeleton — not yet validated or active.
> Full specification: `docs/design/03-skills-and-templates.md §4`

## Purpose
Structured search of approved sources for a specific research question, returning findings with version applicability and freshness assessment.

## Steps (condensed)
1. Receive research question + product scope + version constraints
2. Select appropriate sources by claim type
3. Search in priority order:
   a. Official HashiCorp docs for the exact product version
   b. Provider changelog / release notes for the exact provider version
   c. Official GitHub issues (hashicorp/<repo>) — verify issue matches exact conditions
   d. Status page — only for current incidents, not historical causes
   e. If IBM process claim: approved internal document (session only, not persisted)
4. For each finding: record title, full URL, retrieved date, version applicability, publication status
5. Explicitly note: confirmed behavior / known bug with fix / open issue / planned feature
6. Return: source findings with freshness assessment

## Source authority rules
| Claim type | Authoritative source |
|---|---|
| Feature behavior | Official docs for the exact product version |
| Bug / regression | Release notes or confirmed GitHub issue with fix version |
| Current incident | Status page only |
| IBM process | Approved internal document (session only) |
| Community workaround | Not authoritative — present as unconfirmed |

## Tool unavailable — graceful degradation (G001)

When no retrieval tool (Terraform MCP, web search, or browser) is available:

1. **State the limitation explicitly**: "I have not retrieved this — [tool name] is not available in this session."
2. **Do NOT claim to have performed a lookup** — never say "I checked the docs and..." without a real retrieval
3. **Do NOT hallucinate the answer** from training data and present it as retrieved fact
4. **Provide the exact manual URL** the operator should check:
   - Primary: `https://registry.terraform.io/providers/<namespace>/<name>/<version>/docs`
   - Fallback: `https://github.com/hashicorp/terraform-provider-<name>/blob/<tag>/` for schema/source
5. **Describe what to look for** at that URL — the specific attribute, section, or table
6. **Provide a next-action path** — what the operator should do once they have verified the answer manually

> Correct middle path: state the limitation + give the exact URL to check + describe what to look for.
> Never: fabricate an answer | dead-stop with "I cannot help without MCP"

## What this skill must NOT do
- Present a GitHub comment as authoritative if the issue is open or comment is unconfirmed
- Use a status page finding to explain a historical failure
- Infer a fix was released from an issue being closed (check fix version in release notes)
- Mix findings from different product versions without explicit version labeling

## Output format
```
findings:
  - source: <title>
    url: <full URL>
    retrieved: <ISO date>
    version_applicability: <version or range>
    publication_status: official | beta | issue | community
    claim_type: confirmed_behavior | known_bug_fixed | open_issue | planned_feature
    relevant_excerpt: <quote or paraphrase>
freshness_assessment: <overall assessment>
unresolved_questions: [string]
```
