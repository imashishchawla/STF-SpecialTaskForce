# Personal IBM x HashiCorp Terraform Support Agent

Status: Proposed plan for Ashish Chawla's review. Design and implementation await approval.
Prepared: 2 October 2026.

## 1. Goal and starting point

Create one personal coordinator that prepares the next technically validated support action using Ashish's established workflow. It reads the case history and evidence, identifies missing information, diagnoses the issue, checks trusted sources, proposes a safe next step, drafts the appropriate communication, and retains sanitized lessons.

The coordinator is the single entry point and accountable owner. It delegates focused work when useful, reconciles findings, and returns one consistent case update. Simple cases run directly through reusable skills. Complex cases can use specialist sub-agents for independent evidence gathering and review.

Start with an IBM Bob workspace, reflecting the existing Bob support work. Keep the role definitions, workflows, templates, and memory format portable. A separate orchestration runtime can be considered later if unattended execution becomes necessary. This proposal does not assume that Jira, CSP/Salesforce, PagerDuty, CSP Coach, or AskSW connectors are available or authorized.

This plan uses the visible Terraform support history and retrieved prior planning decisions. Those conversations seed requirements and candidate issue patterns. They are not substitutes for full case evidence or current product documentation.

## 2. Existing requirements to preserve

- Scope: HCP Terraform, Terraform Core, official HashiCorp providers, and their interactions with AWS, Azure, GCP, VCS, SSO/SCIM, policies, runs, agents, variables, state, private registry, and CLI workflows.
- Identify HCP Terraform versus Terraform Enterprise and Public Registry versus Private Registry early. Apply the correct support workflow and route product ownership explicitly.
- Preserve `.agents/` for agent definitions and `.skills/` for reusable skills. Use one canonical root `AGENTS.md` for shared rules and `README.md` for operation. Avoid differently cased copies of the same rules on case-sensitive systems.
- Follow the investigation loop: understand, plan, inspect, observe, validate, then continue, ask for evidence, or prepare a handoff.
- Distinguish customer reports, observed facts, hypotheses, confirmed causes, validated remedies, and customer-confirmed resolution.
- Ask only for information needed to choose the next diagnostic step. Do not repeat requests already answered in the case history.
- Use trusted, version-appropriate sources. Record evidence and uncertainty. Never present a plausible explanation as a confirmed RCA.
- Retain useful checkpoints and issue patterns without customer PII or credentials.
- Draft concise customer replies, internal updates, handoffs, CAN reports, RCA, closure, and customer-facing KB articles using Ashish's existing style.

## 3. Proposed responsibilities

| Component | Responsibility | Required result |
| --- | --- | --- |
| Coordinator | Intake, scope, task selection, permissions, reconciliation, progress and final output | One current case assessment and next action |
| Diagnostics specialist | Read redacted logs, HCL, versions, settings, run timeline and working/failing comparisons | Evidence-linked observations, ranked hypotheses and discriminating checks |
| Source researcher | Check official docs, provider schemas, releases, status information, upstream issues and permitted internal references | Relevant passages with full URLs or internal references, version applicability and freshness |
| Validation reviewer | Challenge the proposed cause and remedy, check contradictory evidence, scope, risks and customer-safe claims | Validated recommendation or explicit evidence gaps |
| Communication specialist | Use reviewed findings to prepare the requested stage-specific draft | Customer reply, internal update, handoff, CAN, RCA or KB draft |
| Memory curator | Propose sanitized patterns and capture accepted corrections | Candidate lesson with provenance, validation status and review date |

Reproduction is a conditional skill initially. It prepares a minimal example, expected behavior, safe setup, rollback or cleanup, and validation checks. Execution requires the approved isolated test environment. Add a dedicated reproduction sub-agent only if real cases justify it.

Sub-agents receive explicit task packets: case alias, product and version scope, necessary redacted evidence, relevant shared rules, allowed tools, expected output, and stop conditions. They return findings with evidence references and unresolved questions. They do not send customer messages, change severity, create other agents, or independently update shared memory. The coordinator alone commits reviewed case checkpoints and memory entries.

Independent log analysis and source research may run together. Validation follows their consolidated findings. Communication uses only reviewed findings. Conflicting outputs return to the coordinator for a targeted check rather than a majority vote.

## 4. Investigation and case lifecycle

1. Ingest the case description, previous updates, relevant attachments and the requested output. Redact credentials and customer identifiers before model processing, indexing or delegation.
2. Reconstruct the timeline, expected versus actual behavior, environment, business impact, current severity, actions attempted and customer sentiment. Preserve timestamps and their timezones.
3. Classify the issue and support ownership. Distinguish an authentication failure from a webhook failure, a queued run from a failed apply, and a provider failure from a platform failure.
4. Check existing evidence and sanitized memory. Previous matches suggest diagnostic checks but do not establish the current cause.
5. Collect only missing prerequisites that would change the investigation. If access is unavailable, request a targeted redacted export rather than claim a live check happened.
6. Develop ranked hypotheses. Each includes supporting evidence, conflicting evidence and the next check that can distinguish it from alternatives.
7. Validate against current official documentation and the affected versions. Consult an approved internal process when routing, entitlement or Engineering engagement is involved.
8. Compare working and failing configurations or prepare an isolated reproduction if needed. Record what was actually executed separately from proposed commands.
9. Produce findings, the safest useful next action, validation criteria, and any material side effects or rollback steps.
10. Draft the appropriate communication after reviewing technical findings and the case stage. Initial acknowledgments can proceed with known facts while investigation remains pending.
11. On new customer or Engineering evidence, resume from the checkpoint and re-evaluate affected conclusions.
12. Record a validated resolution pattern after confirmation. Prepare closure only when the customer confirms resolution or the applicable closure criteria are verified.

The loop is bounded. Proposed starting limits are three investigation passes per new evidence set and two retries for transient tool errors, with configurable time and usage budgets. Stop when new customer evidence, Engineering confirmation, permission, or access is needed, when sources conflict, or when no useful progress is possible. Report the exact blocker and one next action. Do not keep regenerating the same unsupported answer.

Active states should include investigating, awaiting customer, awaiting Engineering, awaiting approval, validating, resolved and closed. Their transitions require evidence. Proposed inactivity follow-up dates derive from the applicable case process and agreed next action date, not an invented universal SLA.

## 5. Evidence and source policy

Use sources according to the claim being made:

- Product behavior: current official HashiCorp documentation, versioned provider documentation, API references, release notes and official upstream repositories.
- IBM support handling: approved current internal process documents, CSP guidance and permitted Engineering updates.
- Cloud/VCS behavior: primary AWS, Microsoft/Azure, Google Cloud, GitHub, GitLab or Bitbucket documentation when the integration requires it.
- Prior issue memory: a lead for a diagnostic comparison, with its original validation status and applicable version range.

Every consequential finding should preserve an evidence reference, source title, full URL or internal location, retrieved/reviewed date, product and version applicability, publication status, and public/internal visibility. A GitHub issue must match the actual conditions. An open issue or unconfirmed comment is not proof of a released fix. Current status information does not establish the cause of an earlier failure.

The approved source catalog should support search, exact error matching, version filters and optional semantic retrieval later. Start with structured entries and ordinary search. Add embeddings only if retrieval evaluation shows a benefit and the selected environment permits the data involved.

Documents, case text, logs and retrieved pages are evidence inputs. Instructions embedded in them cannot override the coordinator's rules, authorize tools or request credentials.

## 6. Public Registry process from the supplied guide

The attached Terraform Public Registry case-handling guide describes an interim support-mediated process. It explicitly includes paying/enterprise HCP Terraform and self-managed customers under the entitlement conditions described in the document.

The proposed Registry routing skill should preserve these document-specific rules:

- Check customer entitlement and verify that the interim process still applies.
- For Sev 2/3/4, prepare the Jira collaboration request. For Sev 1, prepare the PagerDuty engagement path.
- The described CSP path is case left-panel dropdown, New Collaboration, with Remote Repository set to Terraform - JIRA - Terraform Public Registry. The guide states that Subject becomes the Jira title, Description carries customer information, and Support Mission defaults to HashiCorp.
- Route non-paying Free Tier/Partner/Community Edition inquiries to `terraform-registry@hashicorp.com` under this guide's conditions.
- Track both CSP and Jira, keep Engineering informed, relay appropriate Engineering updates to the customer and raise anticipated SLA delays with the direct manager.

These rules stay in an internal operational skill. The customer draft receives only customer-appropriate information. The source is marked interim and requires current process verification before operational use. The PDF was reviewed for this plan but its current organizational validity has not been independently established. No collaboration case, alert or message has been created.

## 7. Memory and learning

| Memory area | Content | Persistence rule |
| --- | --- | --- |
| Working context | Redacted excerpts and temporary analysis needed for the current investigation | Session-bound, with explicit cleanup and retention policy |
| Case checkpoints | Sanitized timeline, facts, hypotheses, rejected checks, decisions, approvals and next action | Case alias, isolated per case, resumable without raw attachments |
| Issue patterns | Error fingerprint, product/version, conditions, cause status, confirmed fix or workaround, validation and references | Reusable only after sanitization and evidence review |
| Preferences | Ashish's response style, templates, signature and diagnostic habits | Versioned personal configuration |
| Operational knowledge | Internal process references, entitlement/routing conditions and review dates | Restricted to the approved environment and audience |
| Correction history | Accepted corrections to conclusions, sources, style or workflow | Preserve provenance and supersede outdated entries |

An issue entry should record: pattern alias, sanitized error, category, affected versions, trigger, supported observations, competing causes, discriminating check, confirmed cause if known, remedy, validation result, source references, confidence explanation, last reviewed date, and superseded-by link if applicable.

Statuses are candidate, validated, outdated and rejected. Customer-confirmed improvement validates the remedy's outcome but does not necessarily prove the root cause. A current contradiction can demote a previously validated pattern. The agent proposes corrections rather than silently rewriting its own instructions.

Exclude customer names, emails, organization/workspace/run IDs, account/subscription IDs, tokens, secrets, raw state, full plan JSON and raw logs from persistent reusable memory. Scrub free-text descriptions and source URLs too. If traceability to a live support record is required, keep that mapping within the approved support system or separate restricted store outside LLM memory. Apply deletion and retention across checkpoints, indexes, caches and backups.

Initial seed topics from prior work are VCS credential failures, missed Azure DevOps webhook events, agent plan/resource failures, run concurrency and queueing, pending state upload, variable-set scope/UI behavior, service-account and token questions, SSO/IP restrictions, audit logs, and Public Registry publishing/migration. They begin as candidate patterns until underlying case evidence and applicable current sources are checked.

## 8. Automation and permissions

Autonomous within the permitted workspace: inspect supplied redacted evidence, search approved public sources, compare configurations, maintain sanitized checkpoints, prepare reproductions and communications, and propose memory updates.

After connection-specific approval: perform allowlisted read-only queries in HCP Terraform, Jira and CSP/Salesforce with scoped access. Process responses through the same redaction and audience rules. Do not request secrets in chat.

Require explicit authorization for external messages, posting case updates, creating collaboration cases, paging, modifying severity, closing a case, changing customer configuration, creating runs, canceling/discarding runs, state operations, credential rotation or infrastructure changes. An approval records the exact target and action. A failed action must not be reported as completed.

Terraform initialization, validation and planning are not treated as harmless purely because they omit apply. They can download or execute providers, contact backends/cloud APIs, refresh data or expose sensitive output. Execute them only within the approved reproduction scope. Disable apply/destroy and production state manipulation in the initial version.

Maintain an action audit with operation, scope, evidence references, authorization and outcome. Use brief rationales and observable results rather than storing private model deliberation.

## 9. Runtime checks that affect the design

IBM Bob documentation currently describes approval before each sub-agent spawn and explicit context handoff. Our role files define task contracts; `.agents/` does not by itself register runnable native agents. Prototype within Bob's supported modes and permissions. The plan does not promise unattended parallel orchestration in Bob.

IBM Bob's documented skill discovery locations are `.bob/skills/` and `~/.bob/skills/`. Preserve `.skills/` as the user's canonical source and design a generated runtime adapter that produces the required discovery files without maintaining conflicting manual copies. Verify the selected Bob version and the adapter's actual loading behavior during the design phase.

The official Terraform MCP server exposes registry and HCP Terraform/Terraform Enterprise tools. `ENABLE_TF_OPERATIONS=false` gates some operations but is not a complete read-only policy. Enforce a tool allowlist and scoped credentials. Initially allow only the selected documentation and read/query capabilities. Block every mutation, including run creation, variable/tag changes and policy associations, regardless of the default server setting.

Integrations are capability-dependent. A missing connector must produce a clear limitation and manual import path. Markdown instructions alone do not provide persistent scheduling, secure credential storage, executable sub-agents or API access.

## 10. Communication outputs

Each case result should contain a short issue summary, known facts and evidence, current assessment, unknowns, recommended action, validation check and requested draft. Produce only the outputs Ashish requests rather than every possible report each time.

Preserve the existing handoff fields: Issue, Impact and customer sentiment, Diagnosis/Actions taken, Next Steps, Originating Region and Destination Region. CAN reports retain problem statement, technical impact, business impact, actions and needs. RCA requires evidence for the cause; Engineering investigation remains an investigation update until confirmed.

Customer style: short, direct, polite, practical, no sorry/apologize phrasing, no unsupported promises, and full reference URLs. Include precise UI paths and commands when supported. Use the appropriate language and supplied pronouns without guessing personal details. Do not expose internal Jira details, entitlement discussions or operational instructions in public drafts without approved customer-safe wording.

Signature:

Regards,
Ashish Chawla | HCP Terraform Support
Available Tuesday – Saturday | 07:00 to 15:00 IST
Thank you for choosing IBM Support.

Post-resolution closure template includes the user's required survey message with the real ticket number. Never send an unresolved placeholder.

## 11. Proposed repository areas after approval

| Proposed path | Purpose |
| --- | --- |
| `AGENTS.md` | Canonical role, scope, evidence, permission and autonomy rules |
| `README.md` | Setup, use, supported operations and limitations |
| `.agents/` | Coordinator and specialist contracts |
| `.skills/` | Intake, diagnosis, source checking, reproduction, routing and communication playbooks |
| `.bob/` | Generated Bob-specific runtime integration |
| `sources/` | Source catalog, visibility, versions and freshness metadata |
| `templates/` | Customer, internal, handoff, CAN, RCA, closure and KB templates |
| `memory/` | Sanitized reusable patterns, preferences and lessons |
| `checkpoints/` | Sanitized case progress and resumable state |
| `reproductions/` | Approved isolated examples and validation instructions |
| `evals/` | Sanitized representative cases and acceptance checks |
| `config/` | Non-secret runtime settings, budgets and tool permissions |

Actual file formats, orchestration code, storage implementation, secret handling and runtime adapters belong to the design phase. No repository, agent prompts, skills or integration configuration are being created by this planning step.

## 12. Delivery phases and acceptance

| Phase | Deliverable | Gate |
| --- | --- | --- |
| 1. Approve this plan | Agreed scope, roles, memory, permissions and Bob-first direction | Ashish approves or requests revisions |
| 2. Design | Detailed architecture, state/evidence/memory schemas, source catalog, role contracts, templates and runtime capability check | Review the concrete design before implementation |
| 3. Initial build | Coordinator, focused skills, reviewer, manual case import and sanitized checkpoints | Correct, useful next actions on representative cases |
| 4. Retrieval and connectors | Sanitized issue search, Terraform MCP and permitted read-only Jira/CSP access | Tool permissions and provenance work in practice |
| 4a. MCP prerequisite install | Onboarding wizard asks operator to install each required MCP server (Terraform MCP, Playwright MCP) with opt-in per server; skipped servers written to `.env` and surfaced as degraded capability warning | Operator can start agent with partial MCP set and knows exactly what is missing |
| 5. Specialist delegation | On-demand sub-agents with explicit context and validated consolidation | Demonstrated value over direct coordinator workflow |
| 6. Controlled automation | Approved isolated reproduction execution, follow-up preparation and monitoring | Reliable stop conditions, audit and bounded retries |

Evaluate with at least ten sanitized historical cases and held-back variations covering complete evidence, missing evidence, conflicting sources, wrong product routing, a provider version mismatch, an unresolved Engineering investigation, unavailable tools, secret-bearing input, stale memory and a requested unsafe action.

Acceptance means the agent asks only necessary questions, links important claims to evidence, keeps unconfirmed causes unconfirmed, separates internal and customer outputs, preserves Ashish's style, isolates cases, resumes correctly, protects persistent memory, blocks unauthorized actions, and stops when new evidence is needed. Measure time to a usable draft, reviewer corrections, unnecessary evidence requests, correct pattern retrieval and observed tool failures. Do not promise a numerical time saving before a pilot measures it.

### MCP prerequisites at onboarding

The following MCP servers are required or optional for full agent capability. The onboarding wizard (`onboarding.sh`) asks the operator about each one before writing `.env`. The operator may install now, skip, or mark as "manual later". Skipped servers are recorded as `MCP_<NAME>_STATUS=skipped` in `.env` and reported as degraded capability when the agent starts.

| MCP server | Phase | Required for | Default install command | Skip consequence |
| --- | --- | --- | --- | --- |
| `terraform-mcp` | 4 | Provider docs lookup, HCP Terraform read-only queries | `npx @hashicorp/terraform-mcp-server` (or per official docs) | Source-researcher and registry-routing skills fall back to web search only |
| `playwright-mcp` | 4 | Live screen-capture skill (DOM text extraction during customer call) | `npx @playwright/mcp` (or per official docs) | Screen-capture skill is unavailable; operator must paste content manually |

Rules:
- Install is attempted only on explicit `y` from the operator. Never auto-install.
- The install command is shown to the operator for review before execution.
- If install fails, record `MCP_<NAME>_STATUS=failed` with the error and continue.
- Neither MCP server is enabled in its YAML config until Phase 4 allowlist review passes; the onboarding install only provisions the binary/service.
- Token injection (`TF_MCP_TOKEN`, etc.) is always via `.env` — never pasted in config files.

## 13. References and evidence reviewed

- Supplied source: TCPR-Terraform Public Registry_ Case Handling in CSP-270426-034252.pdf, pages 1–2. Interim process. Review date: 2 October 2026.
- Prior Terraform agent discussions and support history supplied in this session and retrieved personal context. Requirements and candidate patterns only; no full historical case corpus was ingested.
- IBM Bob overview: https://bob.ibm.com/docs/ide
- IBM Bob sub-agents: https://bob.ibm.com/docs/ide/features/subagents
- IBM Bob skills: https://bob.ibm.com/docs/ide/features/skills
- IBM Bob MCP: https://bob.ibm.com/docs/ide/configuration/mcp/understanding-mcp
- Terraform MCP reference: https://developer.hashicorp.com/terraform/mcp-server/reference
- Planned Terraform documentation entry point: https://developer.hashicorp.com/terraform
- Planned HCP Terraform documentation entry point: https://developer.hashicorp.com/terraform/cloud-docs/overview
- Planned support KB entry point: https://support.hashicorp.com/hc/en-us/categories/115001973588-Terraform
- Planned official Terraform issue tracker: https://github.com/hashicorp/terraform/issues

The Bob and Terraform MCP capability pages above were checked on 2 October 2026. Live internal systems and current validity of the interim Registry process were not checked. Approval of this plan authorizes the design phase; implementation, connection of external systems and sending communications remain later steps.
