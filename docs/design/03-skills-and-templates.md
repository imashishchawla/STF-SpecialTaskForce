# Design 03 — Skills and Communication Templates

> **Status**: Draft — awaiting operator review.  
> **Prepared**: 2 October 2026.  
> **Scope**: Design phase only. No skill files, prompts, or templates are created here — this document specifies what to build in Phase 3.

---

## 1. Skills overview

Skills are reusable, stateless playbooks that the coordinator or sub-agents invoke. They live in `.skills/` (canonical human-maintained source). A generated adapter produces `.bob/skills/` entries — see [`05-runtime-and-integration.md`](05-runtime-and-integration.md).

| Skill | Trigger condition | Owner |
|---|---|---|
| `intake` | Every new case — first pass | Coordinator |
| `diagnosis` | Cases with supplied logs, HCL, or version strings | Diagnostics sub-agent |
| `source-check` | Any claim requiring source verification | Source Researcher sub-agent |
| `registry-routing` | Product scope = `public_registry`; entitlement conditions met | Coordinator |
| `reproduction` | Conditional — only with approved isolated environment | Coordinator (skill) |
| `communication` | After validation reviewer approves findings | Communication Specialist sub-agent |

---

## 2. Skill: `intake`

**Purpose**: Ingest raw case input, enforce redaction, classify scope, and populate the structured case packet.

**Steps**:

```
1. Accept raw case text (paste or attachment description)
2. Identify and strip: tokens/secrets/passwords, org/workspace/run IDs, customer names/emails,
   raw state, full plan JSON, raw logs
   → If any are found: pause and present a redacted version to the operator for confirmation before proceeding
3. Extract: error messages (redacted), version strings, configuration snippets, timeline fragments
4. Classify product scope (see coordinator Section 7)
5. Determine case stage and requested output type
6. Populate CasePacket struct (see coordinator Section 3)
7. Check checkpoint directory for an existing checkpoint matching the case alias
8. Output: structured case packet ready for coordinator's investigation loop
```

**Redaction patterns to detect**:

```
- Terraform tokens:    /\b(tf[a-z]?[_\-][a-zA-Z0-9]{20,}|[a-z0-9]{20,}\.[a-z0-9]{20,})/
- AWS credentials:     /\bAKIA[0-9A-Z]{16}\b/ and /\b[A-Za-z0-9/+=]{40}\b/ near "aws_secret"
- Azure credentials:   /\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/ in auth context
- HCP workspace IDs:   /\bws-[a-zA-Z0-9]{16}\b/
- HCP run IDs:         /\brun-[a-zA-Z0-9]{16}\b/
- HCP org names:       context-dependent; prompt the operator to confirm what to redact
- Customer email:      standard email regex in non-HashiCorp domain context
```

> Note: These are pattern guidelines for the skill specification, not production regex. Actual implementation should use a tested redaction library.

**Failure**: If redaction cannot be confirmed, halt and present a summary of what was found (without quoting the values) to the operator.

---

## 3. Skill: `diagnosis`

**Purpose**: Systematic analysis of supplied evidence to produce observations and ranked hypotheses.

**Steps**:

```
1. Reconstruct run timeline from log timestamps (preserve timezone offsets as-is — do not normalize)
2. Identify: Terraform version, provider versions, backend type, workspace/org type (HCP TF vs TFE)
3. Identify: exact error message(s), error codes, module/resource paths where error occurred
4. Extract: last successful state (if log includes it), first failure point, any retry behavior
5. Compare working vs failing if both are in supplied evidence
6. Map each error/observation to a hypothesis (see DiagnosticsOutput.hypotheses format)
7. For each hypothesis: identify the one discriminating check that would confirm or exclude it
8. Flag: any configuration pattern known to cause false positives or confusing errors
   (see memory/patterns/ for candidate entries once populated)
```

**Known Terraform-specific patterns to check (initial seed from plan Section 7)**:

- VCS credential failures: OAuth token expiry vs webhook secret mismatch vs repo permission change
- Azure DevOps webhook events: push event format difference vs branch filter vs workspace trigger config
- Agent plan/resource failures: agent pool capacity vs network vs provider auth within agent container
- Run concurrency and queueing: auto-queue vs concurrency limit vs run discard threshold
- Pending state upload: network interruption vs state lock vs version conflict
- Variable-set scope/UI behavior: variable set apply scope vs workspace variable override precedence
- SSO/IP restriction: SSO enforcement vs team/workspace membership vs IP allowlist vs SAML assertion
- Audit log gaps: audit trail coverage limitations per plan tier

> These are candidate patterns until underlying case evidence and current sources are checked. None are treated as confirmed causes.

---

## 4. Skill: `source-check`

**Purpose**: Structured search of approved sources for a specific research question.

**Steps**:

```
1. Receive research question + product scope + version constraints
2. Select appropriate sources by claim type (see Source Researcher Section: Source authority rules)
3. Search in priority order:
   a. Official HashiCorp docs for the exact product version
   b. Provider changelog / release notes for the exact provider version
   c. Official GitHub issues (hashicorp/<repo>) — check if issue matches exact conditions
   d. Status page — only for current incidents, not historical causes
   e. If IBM process claim: approved internal document (session only, not persisted)
4. For each finding: record title, full URL, retrieved date, version applicability, publication status
5. Explicitly note: is this a confirmed behavior, a known bug with fix, an open issue, or a planned feature?
6. Return: source findings with freshness assessment
```

**What this skill must not do**:

- Present a GitHub comment as authoritative if the issue is open or comment is unconfirmed
- Use a status page finding to explain a historical failure
- Infer a fix was released from an issue being closed (check the fix version in release notes)
- Mix findings from different product versions without explicit version labeling

---

## 5. Skill: `registry-routing`

**Purpose**: Apply the interim Terraform Public Registry case-handling process when applicable.

> ⚠️ **Operational classification**: This skill uses internal process information from the supplied PDF. Its content is restricted to internal use only — no detail may appear in customer-visible drafts. The source document is marked interim and requires current process verification before operational use.

**Applicability check** (coordinator must verify before invoking):

```
Required:
  - Product scope = public_registry
  - Customer type = paying/enterprise HCP Terraform OR self-managed under entitlement conditions
    described in the source document
  - Entitlement condition = public registry entitlement is OFF in CSP

Route to terraform-registry@hashicorp.com instead if:
  - Customer type = Free Tier / Partner / Community Edition
```

**Steps** (when applicable):

```
1. Confirm entitlement status (from coordinator's scope classification)
2. Determine severity (from current case severity field)
3. For Sev 2 / 3 / 4:
   a. Prepare Jira collaboration case request for coordinator's output:
      - Path: CSP case left panel → New Collaboration
      - Remote Repository: "Terraform - JIRA - Terraform Public Registry"
      - Subject: becomes Jira title
      - Description: carries customer information
      - Support Mission: defaults to "HashiCorp"
   b. Output: internal collaboration case draft (the operator creates it — agent never creates it)
4. For Sev 1:
   a. Prepare PagerDuty engagement path draft for coordinator's output
   b. Output: internal engagement steps (the operator executes — agent never pages independently)
5. Tracking reminders:
   - Track both CSP case and Jira collaboration case
   - Keep Engineering informed per process
   - Relay appropriate Engineering updates to customer (customer-safe wording only)
   - Flag anticipated SLA delays to direct manager
```

**Output**: Internal-only draft with the above steps. Never populate a customer reply with internal routing details.

**Verification status**: Process marked as interim (review date: 2 October 2026). Must verify current applicability with team before using in a live case.

---

## 6. Skill: `reproduction`

**Purpose**: Prepare a minimal isolated reproduction example when investigation requires it.

**Trigger conditions (all must be met)**:

1. Coordinator has validated that remote environment access is insufficient to confirm the cause
2. A reproducible setup exists (no production state, no customer credentials, no live org)
3. the operator has explicitly approved the reproduction scope

**Steps**:

```
1. Derive minimal configuration from redacted case evidence
   - Strip to smallest HCL that reproduces the reported behavior
   - Replace all customer-specific values with generic placeholders
2. State: expected behavior (what should happen)
3. State: observed behavior (what the reported issue produces)
4. List: prerequisites (Terraform version, provider version, backend type)
5. List: safe setup steps
6. List: rollback or cleanup steps
7. List: validation checks (how to confirm the issue is reproduced vs not)
8. Output: self-contained Markdown file for the operator's review and optional execution
```

**What this skill must not do**:

- Execute `terraform init`, `terraform validate`, `terraform plan`, or any Terraform CLI command directly (even read-only operations can download providers, contact backends, or expose sensitive output)
- Contact any customer backend, cloud account, or HCP Terraform organization
- Use customer tokens, credentials, or state

**Execution gate**: Reproduction execution requires a separate explicit approval (approval_class: `reproduction_execution`) specifying the isolated environment. This skill produces the plan only — execution is always a manual step.

---

## 7. Skill: `communication`

**Purpose**: Produce stage-appropriate communication drafts in the operator's established style.

See Communication Specialist contract ([`02-specialist-contracts.md`](02-specialist-contracts.md) Section 4) for full template specifications. This skill is the implementation of that contract's template logic.

**Style rules** (from plan Section 10 — the definitive reference):

```
Tone:     Short, direct, polite, practical
Avoid:    "sorry", "apologize", unsupported promises
Links:    Full URLs only — no shortened links, no internal tracker links in customer drafts
Paths:    Precise UI paths and commands when validated
Language: Match customer's language if supplied and if translation is approved
Pronouns: Use supplied pronouns; do not guess personal details
Internal: Never expose Jira details, entitlement info, or operational instructions in customer drafts
```

**Signature** (resolved from `memory/preferences.md` at output-generation time):

```
Regards,
{{operator_name}} | {{operator_title}}
Available {{operator_availability}}
Thank you for choosing IBM Support.
```

**Closure survey line** (exact — fill in real ticket number):

```
Please take a moment to complete our customer satisfaction survey:
https://www.ibm.com/mysupport/s/case/<REAL_TICKET_NUMBER>/survey
```

> Block closure drafts without a real ticket number. See Communication Specialist failure handling.

---

## 8. Template catalog

Full template files are to be created in `templates/` during Phase 3 implementation. Planned entries:

| File | Content |
|---|---|
| `templates/customer-reply.md` | Standard customer reply with signature |
| `templates/customer-reply-initial.md` | First-response acknowledgment |
| `templates/internal-update.md` | IBM internal case notes |
| `templates/handoff.md` | Shift handoff with all required fields |
| `templates/can-report.md` | Customer Advocacy Notification |
| `templates/rca.md` | Root cause analysis (confirmed vs investigation update) |
| `templates/closure.md` | Customer closure with survey URL |
| `templates/kb-draft.md` | Customer-facing knowledge base article |
| `templates/registry-routing-internal.md` | Internal Jira collaboration steps (restricted) |

---

## 9. Unresolved design questions

| # | Question | Impact |
|---|---|---|
| SQ-01 | Should the `intake` skill present the redacted version for confirmation inline, or as a separate checkpoint step? | Affects first-pass latency |
| SQ-02 | How should the diagnosis skill handle partial logs (beginning or end cut off)? | Affects confidence scoring |
| SQ-03 | Should `registry-routing` be a skill or a section within the coordinator's scope-classification step? | Affects skill granularity |
| SQ-04 | Should the `reproduction` skill produce the HCL as inline Markdown or as a separate artifact file? | Affects checkpoint portability |
| SQ-05 | What is the approved translation mechanism for non-English customer replies? | Affects communication specialist scope |

---

*Previous: [`02-specialist-contracts.md`](02-specialist-contracts.md) | Next: [`04-memory-and-evidence-schemas.md`](04-memory-and-evidence-schemas.md)*
