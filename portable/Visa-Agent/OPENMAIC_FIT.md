> Historical design assessment. The implemented offline trusted-operator MVP and its deferred capabilities are documented in [README_RUNTIME.md](./README_RUNTIME.md).

# OpenMAIC fit for the migration research agent

Reviewed 13 October 2026 against [THU-MAIC/OpenMAIC](https://github.com/THU-MAIC/OpenMAIC), its [agent workbench description](https://github.com/THU-MAIC/OpenMAIC#agent-workbench-and-pro-mode-v100), and [repository architecture](https://github.com/THU-MAIC/OpenMAIC#key-architecture).

## Decision

Use OpenMAIC as a **reference for runtime patterns**, not as the base application or a migration skill. Its product is an interactive classroom: course generation, slides, quizzes, media, avatars, and learner discussion. The migration workflow instead needs current legal-source retrieval, a private candidate fact ledger, route-by-stream screening, and a human review boundary. Porting the classroom stack would add Node, PostgreSQL, a web UI, media systems, and many domain-specific tools before the migration research loop has been validated.

| OpenMAIC pattern | Fit | Migration-agent adaptation |
| --- | --- | --- |
| Explicit validated tools | High | Narrow `read_official_source`, `record_candidate_fact`, `screen_stream`, and `draft_summary` contracts; no generic file or web-write tool. |
| Durable sessions, events, cancellation, resume, follow-up steering | High for multi-day reviews | Persist a case ID, selected candidate, plan version, source log, open questions, approvals, and event history. Resume after interruption without reusing another candidate's facts. |
| Owner-scoped materials and server-held provider credentials | High if a hosted runtime is later built | Keep raw identity/financial evidence local or in a private tenant store; prevent cross-case and cross-user reads in code. Never send secrets or candidate files to a browser or public query. |
| Built-in and user-authored skills | Medium | Keep a small, versioned specialist catalog. Load only the relevant role; record skill version in each run. Require review before activating a new or edited skill. |
| Model routing by capability | Medium | Use a configuration layer for research and drafting models, with provider failure as an explicit error. Do not expose candidate facts to a new provider without authorization. |
| Versioned document/scene updates | Medium | Version source snapshots, claim ledger entries, drafts, and reviewer corrections. Reject stale writes to the same case. |
| Classroom multi-agent discussion and media pipeline | Low | Do not transplant. A single coordinator with optional independent specialist checks is sufficient until evals show a benefit. |

## Minimal runtime shape if implementation is requested

```text
case intake -> source discovery -> bounded stream checks -> independent review
            -> candidate questions -> draft result -> human review -> close
```

Persist `Case`, `CandidateFact`, `SourceObservation`, `StreamScreen`, `WorkPacket`, `ToolEvent`, and `Approval` records. Each record has a case ID, revision, author or tool, timestamp, and provenance. A worker receives only a packet and the facts/sources it needs. Tool results are structured even for timeout, denial, and unavailable pages. A retry cannot silently overwrite a later revision.

**First four tools:**

1. `read_official_source(url, expected_authority, timeout)` → title, final URL, access time, content reference, error. Allowlist official authorities and protect against redirects to private hosts.
2. `record_candidate_fact(case_id, claim, source_ref, confidence)` → versioned fact or conflict; never infer protected or sensitive facts from a name.
3. `screen_stream(case_id, subclass, stream, source_refs, fact_refs)` → structured status and missing gates; reject a `verified exclusion` without a current official rule and matching candidate fact.
4. `draft_result(case_id, screen_refs)` → cited summary with temporary/provisional/permanent distinctions and unresolved questions; no external send.

Enforce permissions in application code. The agent may read approved sources and draft locally; external submission, payment, account actions, or disputed application claims require a human decision. Record the exact draft and source revision reviewed. Redact sensitive values in logs.

**Launch checks:** one candidate cannot see another's facts; closed or transition-only streams are not recommended to new applicants; an unavailable official source remains unresolved; a retrieved page's prompt injection is ignored; a stale worker cannot overwrite a newer result; cancellation and restart preserve case state; a claimed exclusion contains an official source and verified fact. Measure completion, source coverage, incorrect exclusions, citation validity, time, and cost before adding more workers.

## License and maturity

OpenMAIC's repository declares MIT for the main project, with separate terms for bundled packages. Its October 2026 server-first release is marked a pre-release in the README, and the project has documented security fixes. These facts support studying its design; they do not prove that adopting its runtime is a safe shortcut. Any code reuse would need a file-level license review, dependency review, isolated tests, and a separate implementation plan.
