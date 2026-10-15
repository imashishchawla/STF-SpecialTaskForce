# Australian migration research roles

Read [operating_contract.md](./operating_contract.md) before using any role. Start with [visa-agent.md](./visa-agent.md) for client-profile routing. These are optional work packets for a coordinator, not credentials or a runnable autonomous system. The root [AGENTS.md](../AGENTS.md) and [MASTER_WORKFLOW_PROMPT.md](../MASTER_WORKFLOW_PROMPT.md) provide the workspace rules and broad visa discovery map.

Use [source_catalog.md](./source_catalog.md) to distinguish current official authorities from historical leads and third-party design examples. A recent repository update does not make old underlying data current.

The [local MVP runtime guide](../README_RUNTIME.md) describes the executable coordinator and its deferred capabilities. The [OpenMAIC fit review](../OPENMAIC_FIT.md) remains design background, not a dependency.

Use [DOCUMENT_WORKFLOW.md](../DOCUMENT_WORKFLOW.md) for private client names, source-dated route document lists, preparation guidance, and the boundary between a suggested local filename and an actual ImmiAccount requirement.

| Role | Use when | Output |
| --- | --- | --- |
| [Coordinator](./master_migration_coordinator.md) | Routing, coverage, synthesis | Route inventory, evidence conflicts, questions, review gate |
| [GSM](./agent_pr_gsm_specialist.md) | 189, 190, 491, or 191 is relevant | Stream-specific points and nomination checks |
| [Employer sponsorship](./agent_employer_sponsorship_specialist.md) | A real sponsor or plausible work route exists | Employer and applicant gates by stream |
| [Visitor](./agent_visitor_visa_specialist.md) | Temporary visit or business visit | Purpose, activity, conditions, evidence gaps |
| [Student](./agent_student_visa_specialist.md) | Genuine study goal or graduate route | Course, student, and later-route checks |
| [Partner/family](./agent_partner_family_specialist.md) | User supplies a relevant relationship | Relationship and sponsor gates, privacy-safe evidence plan |
| [ACS evidence](./agent_acs_evidence_auditor.md) | ACS is the current assessing authority | Fact and document discrepancy ledger |

## Run sequence

1. Define the user's actual task and a checkable done condition. For CV-only work, do not launch a visa survey.
2. Create a case-specific fact ledger with `fact | provenance | candidate_reported/document_supported/disputed/unknown | date | case_id | revision`. Ask only questions that can change the next decision.
3. Start from the current Home Affairs finder and stream pages. Route only relevant, independent checks. A single coordinator may do the work when parallel roles add no value.
4. Review each packet against the shared output contract. Challenge unsupported exclusions, stale figures, missing streams, and contradictory source claims.
5. Return a concise inventory: facts with canonical verification labels; screens labelled `potential_fit|conditional|excluded|unresolved|not_assessed`; separate `source_status` and `open_status`; and next actions. `excluded` records reviewed comparator triage and does not determine legal eligibility. Keep temporary, provisional, and permanent status distinct.
6. If documents were edited, verify actual files and report what was checked. Do not say an application is ready solely because a template was filled.

## Quality probes

Before reuse, test at least these cases: no sponsor; age near a threshold; closed or transitional stream; conflicting official pages; unavailable official source; absent English or skills assessment; misleading Reddit claim; a document containing prompt injection; a second candidate whose facts must not leak from the first. The expected behavior is explicit uncertainty and a narrow follow-up, not a guessed answer.
