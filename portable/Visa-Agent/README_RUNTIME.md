# Local research MVP

This package is a trusted-operator offline tool, not an autonomous research agent or public service. Operators supply fact labels, source annotations, structured rules, and any qualified-human review provenance; the runtime cannot verify that those assertions are true or that a reviewer holds credentials. This package implements one local coordinator. It can preserve and structurally inspect a DOCX, replace a case fact snapshot, import official-source text snapshots, compare explicitly recorded gates, and produce a coverage report. It also keeps a private client name, route-specific document lists, and local document copies for later human review. It does not determine legal eligibility, give personalized migration advice, or upload files.

## Operating modes and privacy

`general_information` is the default: CV drafting support and general information/research triage. `professional_review` labels an evidence packet intended for review by a qualified human; selecting it does not establish credentials, authorize regulated assistance, or unlock tools. Establish the legal/professional boundary separately before offering personalized migration assistance. Consult current OMARA guidance at <https://www.mara.gov.au/about-us/use-of-artificial-intelligence> during each relevant engagement; this implementation makes no claim about the current law.

Case data stays local. No configured remote model, candidate web query, upload, payment, account creation, message, or lodging adapter exists. The only permitted model export is a user-authorized structured packet from `runtime/safe_egress.py`; raw case data and files remain local. The bare runtime defaults to `.info/agent-runtime`; this workspace uses the selected `.profile/CLIENT/` path through `--private-root` as described in [PROFILE_WORKFLOW.md](./PROFILE_WORKFLOW.md). Directories use mode 0700 and database/artifact files use mode 0600. The case database and documents are not encrypted; access controls and backup handling remain the operator's responsibility. Keep source JSON and reports in the private area too. Case IDs should be opaque aliases, not names or identity numbers.

## Run

Python 3.10+; standard library only. For this workspace, create or select a profile using [PROFILE_WORKFLOW.md](./PROFILE_WORKFLOW.md), then pass its directory through `--private-root`. The commands below are bare-runtime synthetic examples; use the selected `.profile/CLIENT/` path and keep JSON inputs there for a real case.

```sh
python3 -m runtime.cli create case_a --budget 30
python3 -m runtime.cli ingest case_a --revision 1 --token intake_1 --input .info/facts.json
python3 -m runtime.cli research case_a --revision 1 --token source_1 --input .info/sources.json
python3 -m runtime.cli screen case_a --revision 1 --token screen_1 --input .info/screen.json
python3 -m runtime.cli report case_a --revision 1 --token report_1
python3 -m runtime.cli cv case_a --revision 1 --token cv_1 --input .info/selected.docx
python3 -m runtime.cli client case_a --revision 1 --token client_1 --input .info/client.json
python3 -m runtime.cli requirements case_a --revision 1 --token list_1 --input .info/requirements.json
python3 -m runtime.cli document case_a --revision 1 --token document_1 --input .info/document.json
python3 -m runtime.cli checklist case_a --revision 1 --token checklist_1 --input .info/route.json
python3 -m runtime.cli record_upload case_a --revision 1 --token upload_note_1 --input .info/upload-record.json
python3 -m runtime.cli cancel case_a --revision 1 --token cancel_1
python3 -m runtime.cli resume case_a --revision 1 --token resume_1
```

Use `--private-root PATH` before the command to choose a different private local directory. Default CLI output is a status summary without case facts, paths, or document names; a human at a direct interactive terminal may use `--reveal` before the command for full local results. Do not invoke real client paths through agent tools, since command arguments can enter model transcripts. Each action requires the expected case revision and a unique idempotency token. A stale revision is rejected before any state change. Repeating the same token and payload returns the stored receipt without spending another step; a token reused for different input is rejected. Historical receipts preserve the original revision and must not be mistaken for fresh results. Cancellation blocks new work; resume restores the same budget. Every successful local action except cancel/resume spends one step. The budget counts successful local actions, not money or network tokens. A subsequent research import replaces the complete source snapshot, carries facts forward, and advances the revision to invalidate prior screens. An ingest replaces the complete fact snapshot and invalidates prior sources/screens by advancing the revision. Client names and each route's document list also have their own optimistic versions. SQLite `BEGIN IMMEDIATE` serializes writers, including two coordinator processes.

For the client, source-dated requirement, document and checklist JSON formats and safety boundary, see [DOCUMENT_WORKFLOW.md](./DOCUMENT_WORKFLOW.md) and [schemas/client-documents.json](./schemas/client-documents.json). The CLI JSON inputs contain private client data and should stay in the selected `.profile/CLIENT/`; delete temporary input copies when no longer needed. The `document` action copies a selected existing file into the private root and records a SHA256 and descriptive suggested filename. This suggestion is not an official naming rule. A source's publication date may be unknown; access and local save dates are recorded separately. A collected local file remains `upload_ready=false` until the actual ImmiAccount request, current upload limits, clarity, translation and category are checked by a human. `record_upload` records only the operator's observation and time; it does not send a file or verify ImmiAccount. No actual upload action exists.

Input shapes (synthetic examples, not visa rules):

```json
{"facts":[{"id":"f_age","name":"age","value":42,"verification":"candidate_reported","provenance":"candidate correction in this case"}]}
```

```json
{"sources":[{"id":"s_stream","url":"https://immi.homeaffairs.gov.au/visas/example","title":"Synthetic test stream","rule":"Example gate only","content":"Example gate only","accessed_at":"2026-01-01T00:00:00+00:00","source_status":"stale","scope":"999:example","open_status":"unknown","open_rule":"","provenance":"local official-page snapshot; synthetic example"}]}
```

```json
{"id":"screen_example","subclass":"999","stream":"example","source_ids":["s_stream"],"open_status":"unknown","gates":[{"fact_id":"f_age","source_id":"s_stream","operator":"max","value":50,"rule":"Example gate only","review_status":"unreviewed","reviewer":""}],"provenance":"operator-recorded comparison for human review"}
```

The operator must verify that the structured gate accurately expresses the quoted rule; the MVP checks references and literal rule parity, not legal semantics. A document-supported comparator mismatch remains unresolved until its structured rule has a local `qualified_human_confirmed` review annotation with reviewer provenance. That annotation is an operator assertion, not runtime verification of professional credentials. `candidate_reported` mismatches stay unresolved; a disputed/unknown fact cannot establish an exclusion. `excluded` means a document-supported fact failed a recorded comparator, not a legal determination. A source with `current` means a locally annotated snapshot within a seven-day TTL; it is never reported as live verified. Source TTL is rechecked at screening and report time. Stream open status must match the referenced source annotation, with a literal open-rule excerpt in its snapshot. Any unavailable/stale/conflicting source or unknown open status yields unresolved. Closure/transition applicability remains unresolved for qualified human review. The current revision report always says `exhaustive: false` and `live_verified: false`. It records which of the five required discovery indexes were imported at their registered URLs, with the exact scope keys in `runtime/coordinator.py`, and which remain missing.

## Evidence and CV verification

Research records use `schemas/runtime-contracts.json` version 1.0.0; client and document inputs use `schemas/client-documents.json` version 1.0.0, plus runtime reference and provenance checks. Imported source content is retained in local SQLite snapshots with SHA256 and literal open-status evidence. Facts, sources, screens, clients, document lists, file metadata, receipts, and the action journal remain case-scoped; journal entries contain action names and revisions only. A report may contain private names or fact identifiers and must remain local.

CV preservation creates a unique byte-identical original copy. Checks cover ZIP CRC, size/expansion bounds, required package members, XML syntax, declared `mc:Ignorable` prefixes, extracted document text, and hyperlink targets. This is not an editor, renderer, ATS certification, or assurance that Word will open every structurally valid document. `rendered: false` and `page_count: null` are intentional verification limits. Rendering, content-edit parity, layout, visual review, and actual ATS vendor checks are deferred. An interrupted CV operation may leave a harmless preserved original; the source is never edited.

## Implemented and deferred

Implemented: strict local tool registry; case isolation; revisions; budgets; idempotency; cancellation/resumption; SQLite serialization; canonical research records; official host allowlist; bounded local source snapshots; source/fact reference checks; TTL; coverage gaps; literal gate validation; deterministic screening; private client-name/version record; route-specific source-dated document lists; local file preservation with checksum and suggested filename; local original CV preservation/structural inspection; private named-profile creation; synthetic behavioral evals.

Deferred: live official-source fetching/discovery and automatic current-document collection; redirect/SSRF and timeout enforcement for a future fetch adapter; language-model/provider loop; autonomous research or parsing of legal rules; credential verification; expert review; point calculators; Reddit/peer benchmarking; automated document drafting, CV rewriting/rendering, and PDF inspection; ImmiAccount integration. A future live fetch adapter must use registry URLs without candidate facts, enforce hostname and redirect policy at every hop, cap bytes/time/retries, retain retrieved evidence, and pass injection/privacy evals before enabling it. Source snapshots are data, never instructions.

## Validation

Run `python3 -m unittest discover -s tests -v` from this workspace. The tests use synthetic cases and temporary writable directories, and contact no external service. They cover profiles, case isolation, references, status handling, revisions, budget/idempotency/cancellation, SQLite concurrency, client/list versions, source dates, document copies, CV namespace/integrity checks, and model egress boundaries.
