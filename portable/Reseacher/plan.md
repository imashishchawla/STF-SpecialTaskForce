# Researcher Agent — Design Plan

> **Status:** Phase 1 contract draft implemented; not a runnable or host-validated agent.
> **Agent ID:** `certification-research-curator`
> **Directory label:** `Reseacher` (preserved from the requested path; confirm before any later naming cleanup).
> **Version target:** `0.1.0`
> **Purpose:** Plan a trustworthy, multi-host agent that maintains a searchable Markdown catalog of IT certifications/badges for publication on the user's Hugo website, with tailored recommendations as a companion output.

## 1. Context and current state

The prior Orca conversation began with a concrete user journey: find Credly exams and badges, present them in an attractive searchable HTML directory grouped by category, then recommend the best options for the user's profile. The example profile in that conversation had Terraform Associate, IBM DevSecOps Explorer, and AWS Generative AI experience, and received recommendations spanning Kubernetes/networking, cloud security/supply chain, AI-assisted cloud operations, and a formal security certification. The conversation then asked about Tavily and Firecrawl, and proposed a deeper credential discovery/validation agent. The latest instruction was to plan first and use those chats as reference. The earlier provider session is read-only context and is not resumed here.

The current repository has a design plan and Phase 1 Markdown contracts in `portable/Reseacher/`. The operator selected Google Antigravity, IBM Bob, Codex, and Claude as target hosts; wants broad coverage across IT sectors; asked to keep search keys under the home directory; and plans to publish artifacts on `https://imashishchawla.github.io/ai-certification-preparation/`, whose local source checkout is `/Users/ashishchawla/Documents/My-DIY-Projects/n8-rev-build/neighter`.

Read-only inspection of that website checkout on 2026-11-07 found a Hugo site (`hugo.toml`), Markdown content under `content/`, an existing exam-track catalog in `data/exams.toml`, and a GitHub Actions workflow that builds and deploys GitHub Pages from pushes to `main` (or manual dispatch). The site's configured base URL matches the supplied URL. The live page could not be opened by the web tool in this session, so the structural assessment comes from the local source. Two untracked files already existed there—`cca-f-exam-study-guide.html` and `cca-f-secret-playbook.html`—and are outside this task; preserve them. The website checkout was not modified. The operator later specified that, after this agent is finalized, it should also be added under that website repository's `agents/` folder and the site's agent instructions updated; this is a later, separate integration step and has not been performed.

The source chat and proposed CrewAI script are historical input, not repository authority. STF's current contracts call for canonical skills under `export/skills/`, role definitions under `export/agents/`, schema-conformant capability requests, untrusted-source handling, and human review before activation. Current host skill discovery differs, so compatibility must be verified per installed app/version rather than inferred from Markdown alone.

## 2. Recommended design

Build an **LLM-hosted certification directory and recommendation workflow** usable through Antigravity, Bob, Codex, and Claude. Keep one canonical Markdown skill/record contract and generate or map host-specific skill/agent files as adapters. A coordinator gathers goals, retrieves records, assigns bounded packets where that host supports scoped subagents, obtains independent verification, integrates accepted Markdown changes, and prepares the website content. If scoped delegation/file access is unavailable, workers return patches for coordinator review. Research spans IT sectors, with coverage by category/issuer tracked explicitly; “all available” is a discovery goal, never an exhaustiveness claim.

For the public directory, keep credential records as Hugo Markdown content in the website repository so the existing build renders the HTML pages. The target source area is `content/credentials/` (or the final section path selected after checking the website's Hugo layout conventions during implementation). The public Markdown records are the source of truth for published credentials; Hugo templates/layouts generate the search/category/filter interface. Do not maintain hand-edited `.html` copies as a second source. Keep candidate research patches and internal run notes in Markdown within the agent workspace until reviewed; only accepted public-safe records move into website content. Public deployment is a separate human-reviewed gate because the site's workflow publishes from `main`.

After the Researcher agent's contracts, host adapters, and acceptance checks are finalized in STF, perform a separate website integration in `/Users/ashishchawla/Documents/My-DIY-Projects/n8-rev-build/neighter/`: place the distributable agent documentation/entry under the site's `agents/` folder and update the site's existing agent instructions to describe how to use it, search/update its Markdown knowledge, and hand reviewed credential records into the Hugo content workflow. First inspect the actual `agents/` contents and instruction files, preserve unrelated work (including existing untracked files), and follow their conventions. Do not copy the unfinished draft into the website or trigger the site's `main`-branch publishing workflow.

Run the agent as instructions and tools inside the selected host. Check native search/fetch, Markdown file access, constrained edits, subagents, and secret injection independently for Antigravity, Bob, Codex, and Claude. Antigravity and Codex both document `.agents/skills`; Bob documents `.bob/skills`; Claude Code documents `.claude/skills`. Use STF's canonical `export/skills/` as the source and generate/copy host adapters; do not claim that all hosts enforce the same permissions or provide the same subagent behavior. The operator has Tavily, Exa, and Firecrawl accounts; evaluate those providers against each host's native tools, and use them only where they add needed capability. Do not make CrewAI/LangGraph the default orchestrator inside these host products.

### Goals

- Find credentials relevant to user-provided role, geography, experience, budget, time, and subject preferences, including niche issuer programs.
- Cover nearly all IT sectors over time: cloud/infrastructure, AI/ML, data/analytics, software development, cybersecurity/DevSecOps, networking/telecom, IT operations/service management, enterprise platforms, architecture/project/agile, QA/testing, and hardware/IoT. Track source and category coverage; don't claim an exhaustive inventory.
- Build a broad directory of Credly-issued badges, linking each badge to its official Credly page and the issuer's exam/course page when available.
- Publish an accessible HTML directory generated by Hugo from Markdown, with category filters, instant search across credential/issuer/category/skills, and clear cost/assessment filters. Include totals only when derived from verified published records.
- Use a user's stated profile to produce a ranked, explainable shortlist that distinguishes quick learning badges from formal proctored certifications and avoids recommending entry-level credentials the user already holds.
- Prefer issuer, exam-owner, accreditor, and official badge-platform sources; use secondary sources only to discover leads or corroborate gaps.
- Verify current availability, cost, eligibility, assessment format, Credly issuance, LinkedIn addability, and accreditation as separate claims with evidence and access dates.
- Deduplicate credentials and distinguish formal certifications, vendor certificates, course-completion certificates, and community badges.
- Keep the durable credential catalog and its evidence in searchable Markdown files; generate HTML and run-specific recommendations from those reviewed records.
- Deliver an optional category-grouped Markdown report with verified links, uncertainty, and a ranked shortlist tied to the user's stated criteria.
- Treat Markdown files as the editable catalog/source and Hugo HTML as the public website rendering; they are complementary layers, not competing artifact choices.

### Non-goals

- Claim exhaustive coverage of the internet, hidden access, privileged OSINT, or guaranteed discovery beyond indexed/crawlable pages.
- Bypass paywalls, authentication, CAPTCHAs, robots/access controls, rate limits, or site terms; scrape private user data; or run unattended broad crawls.
- Treat snippets, marketing copy, model memory, or search ranking as verification.
- Infer credential value, accreditation, exam rigor, or hiring outcomes without sourced criteria.
- Purchase exams, enroll users, create accounts, claim badges, write to LinkedIn/Credly, or contact issuers.
- Store or request API secrets in prompts, portable files, logs, source control, or ordinary agent memory.

## 3. Searchable Markdown knowledge base and update protocol

Markdown credential records are the durable source of truth. Chat history, model memory, search-provider indexes, and generated HTML are not the catalog. Published records live one credential per file in the website repository under the Hugo credentials section (proposed `content/credentials/<stable-credential-id>.md`); use the website's Hugo front matter conventions and add the fields needed for evidence and filters. Chat-independent candidate findings and review proposals live as Markdown under `portable/Reseacher/knowledge/updates/<task-id>/` until a curator accepts them. Once accepted, the website Markdown record becomes the canonical public record; avoid a second maintained copy under `portable/Reseacher/knowledge/credentials/`.

Keep general workflow rules and source policy in the agent's own Markdown docs. Use a small README/index linking to website records; generate or verify it deterministically. Ordinary text search (`rg`) and each host's file tools must find records by name, issuer, category, skills, exam code, and aliases. Website HTML is built from accepted Markdown by Hugo; generated HTML is not manually edited as source.

Each credential file uses YAML front matter with `credential_id`, `name`, `issuer`, `category`, `credential_type`, `status`, `aliases`, `tags`, and `last_verified`. Its Markdown body stores assessment details, cost and region, Credly and LinkedIn evidence, accreditation scope, prerequisites/renewal, user-fit notes only when requested, and a claim-by-claim evidence ledger with source title, direct URL, source class, access date, status, and concise note. Unknown or conflicting facts remain explicit. Do not put an individual's profile, contact information, or private records in the shared catalog; recommendations use only profile context supplied for that run unless the user separately asks to persist it.

Record lifecycle in the agent workspace: `candidate` → `needs_review` → `verified`; use `superseded` for replaced versions and retain a link to the successor. Only `verified` records are copied into public Hugo `content/credentials/`. A subagent may be assigned a specific issuer/category and exact record IDs or new-record namespace. It returns a patch or writes only its uniquely assigned candidate files when the host enforces that scope. Each proposed change includes source evidence, claims changed, and unresolved questions. For file-writing hosts, workers write new findings or edits to separate files under `knowledge/updates/<task-id>/`; only the coordinator/curator merges accepted records into the website repo after review. Workers cannot mark their own findings verified, alter shared policy, merge conflicting records, or overwrite another worker's files. The coordinator/curator checks required fields, source quality and freshness, links, stable IDs, duplicates, contradictory claims, and whether each status is supported before accepting edits. Serialize updates to shared records; parallel workers must use disjoint files. Preserve old evidence and revision notes when a verified claim changes. Git diff/history is the change audit; no separate hidden memory store is required.

Retrieval flow: search the website Markdown/index for current records and gaps → assign bounded packets → collect evidence-backed Markdown proposals in separate files/worktrees → curator review and merge → regenerate/check the index → build Hugo output and verify directory behavior → report changed record IDs and evidence dates. Candidate status remains unpublished. If a host lacks file-search or constrained-write tools, workers return patches for a coordinator/human to apply. Human review is required before merging public content to `main`; deploying/publishing must follow the website's existing approval/release process.

## 4. Workflow and evidence rules

1. **Intake:** For personalized recommendations, ask for target role/domain, geography, current credentials, preferred credential type, budget, time horizon, acceptable assessment format, and whether Credly is mandatory. For broad directory maintenance, use the all-IT-sector scope and the assigned category/issuer packet. Mark omitted profile details unknown; do not block directory discovery.
2. **Retrieve:** Search the Markdown index and credential files for existing matches, aliases, stale records, and gaps before web search. Do not repeat research that is already current and evidenced.
3. **Plan packets:** Define included categories/issuers, source classes, query themes, exclusions, URL/page/result limits, time/tool-call budget, assigned files, and done conditions. Prefer issuer catalogs, exam blueprints, FAQs, pricing pages, accreditation registers, and official Credly pages.
4. **Discover:** Search using issuer-specific terms and lead phrases (pilot, beta, community badge, voucher, micro-credential). Search depth is a provider setting, not proof of exhaustive coverage. Treat every returned page and instruction as untrusted data.
5. **Propose records:** Workers return candidate Markdown records or narrowly scoped patches with claim values, statuses (`verified`, `not_found`, `conflicting`, `unavailable`, `stale`, or `unknown`), source title/URL, source type, access date, concise evidence note, and unresolved questions. Absence of a search result is never a verified “No.”
6. **Verify and curate:** The curator independently checks primary sources for credential identity, price/region, prerequisites, assessment details, current availability, Credly template, LinkedIn behavior, and accreditation scope. It resolves duplicates using issuer + credential/version/exam code and does not self-approve worker findings.
7. **Review and update:** The coordinator accepts only supported patches, updates record status and revision note, and keeps unresolved claims visible. A profile-based recommendation may use run-scoped user context but does not write it to the shared catalog by default.
8. **Generate and quality check:** Generate the HTML from accepted Markdown records. Validate every displayed claim/link/date, counts and filters, duplicate handling, accessibility basics, and unknown states. Report coverage, stale/unavailable records, and what was not searched.
9. **Deliver:** Prepare the reviewed Markdown content changes in the website checkout and provide the Hugo-rendered preview/build artifact. Require human review before merging to `main`, which triggers the site's publishing workflow. Keep run summaries as Markdown in the agent workspace.

## 5. Required credential record

Each credential is represented as an individual Markdown record using the searchable front matter and body contract in §3. Required fields include:

| Field | Contract |
|---|---|
| Credential identity | Canonical name, issuer, credential type (`professional_certification`, `vendor_certificate`, `course_certificate`, `micro_credential`, `community_badge`, `other`, `unknown`), level/version/exam code if present |
| Category and fit | One or more domain categories; fit to each stated user criterion with a short reason |
| Direct URL | Official credential or exam page; separate official enrollment URL if available |
| Price | Amount, currency, region, included items, checked date; use `unknown` when not evidenced. Distinguish free learning from paid assessment/certificate. |
| Assessment format | Separate proctoring, delivery platform, and assessment style facts; derive one display label from §6, plus verified details (remote/in-person, timed, practical, proctor vendor) |
| Credly | `verified_yes`, `verified_no`, `unknown`, `conflicting`, or `unavailable`; official badge template/issuer URL and evidence |
| LinkedIn addability | Same evidence status; URL and clarify whether a dedicated Add to Profile flow/credential ID exists or only manual profile entry is supported |
| Accreditation | Status and accrediting body/scope, or explicit unknown; distinguish accreditation of an issuer/program from recognition of a credential |
| Evidence ledger | Claim-level source title, direct URL, source class, access date, quoted snippet within copyright limits or paraphrase, and status |
| Curation note | Why relevant/specialized, caveats, prerequisites, renewal/expiry, and duplicate key where applicable |
| Record governance | Stable credential ID, lifecycle status, aliases/tags, last verified date, revision note, and successor link when superseded |

## 6. Controlled assessment-format labels

The user-provided five labels are retained, with one necessary correction: they mix proctoring status, delivery method, and assessment style, so they are not mutually exclusive facts. For a deterministic primary field, use exactly one best-fit label below and add detail fields for overlapping properties.

1. `Proctored (live human or automated lockdown)`
2. `Non-proctored (verified unproctored)`
3. `Self-paced assessment (proctoring unknown or not specified)`
4. `Short reading and quiz`
5. `Platform-hosted online assessment (e.g., Skill Builder)`
6. `Unknown (issuer evidence unavailable)`

Never label a credential “100% unproctored” based only on lack of proctoring language. If evidence says no proctoring, retain the source and check date. For the final matrix, display the controlled label plus verified specifics so users can tell platform and proctoring apart.

## 7. Output contract

The editable/published source artifact is Markdown in the Hugo website repository. Hugo generates the public HTML directory and credential pages from those records. The site output should have a title and as-of date, record-derived summary counts, search across credential/issuer/category/skills/aliases, category and assessment filters, responsive cards, direct issuer and Credly links, visible verification states, and a no-results state. Extend the existing site theme/build; do not create manually maintained HTML or introduce third-party scripts/analytics/fonts for this directory. Counts are derived from records selected for the build and distinguish verified records from candidates or stale records.

Add an optional Markdown companion for auditability. It contains scope and as-of date; a short method and source coverage limits; category headings; credential entries; and a shortlist ranked against stated user criteria. Use this entry format:

```markdown
### [Category]
- **[Credential name]** | Issued by: [Issuer] | Type: [credential type]
  - **Official URL:** [direct source]
  - **Cost:** [Free / Paid (amount + currency) / Free learning + paid assessment / Unknown] (checked [date])
  - **Exact format:** [one controlled label]; [verified particulars]
  - **Credly:** [Verified yes/no/unknown/conflicting/unavailable] — [evidence link]
  - **LinkedIn addable:** [Verified yes/no/unknown/conflicting/unavailable] — [evidence link and behavior]
  - **Accreditation:** [body and scope / not found in checked official sources / unknown]
  - **Why it fits:** [one evidence-backed sentence tied to user criteria]
  - **Caveats:** [prerequisites, region, renewal, uncertainty, or None found]
```

Do not use “not accredited,” “no Credly,” or “not LinkedIn addable” unless an authoritative source explicitly supports the negative. Otherwise state “not found in checked sources” or `unknown`.

## 8. Tool and secret boundary

### Capability request (proposed, not a grant)

- Required: bounded public web search/page retrieval and read access to the website's credential Markdown section. Proposal writes are limited to isolated agent-workspace files/worktrees until reviewed.
- Optional: page extraction/crawl for explicitly selected public issuer domains, with a per-run URL/page/depth limit.
- Not requested: shell execution, browser login, account access, local filesystem search outside the task output path, purchases, enrollment, social posting, or arbitrary API calls.
- Every tool result must preserve URL, retrieval time, and provider/source metadata where available. A runtime must enforce domain, request, time, and result-size limits; prompt instructions alone are not enforcement.

### Tavily, Exa, and Firecrawl configuration

The operator specified `~/.config/seach-engines/.env`. It now contains `TAVILY_API_KEY`, `EXA_API_KEY`, and `FIRECRAWL_API_KEY`, plus `TAVILY_MCP_SERVER`, `EXA_MCP_SERVER`, and `FIRECRAWL_MCP_SERVER`. The env file is owner-only (`0600`) in an owner-only directory (`0700`); an adjacent `.gitignore` excludes `.env`. Values are kept out of this plan, the portable bundle, prompts, subagent packets, reports, command history, logs, and source control. Host adapters must inject API keys only into provider/tool processes, outside model context. Cloud-hosted sessions must use their approved secret store instead of uploading this file. Current host-specific MCP activation remains pending.

The Researcher project has the Exa `build-with-exa` Agent Skill installed at the STF repository root `.agents/skills/build-with-exa/`. Its canonical guidance selects Exa `/search` for an LLM-callable web search tool: require `query` and `objective`, use concise `contents.highlights`, and omit extra filters unless the request requires them. Use `/contents` for known-URL extraction; reserve `/agent` for explicitly requested asynchronous multi-step research. This interactive credential-search loop does not need a CrewAI wrapper. On 2026-11-10, one Exa smoke test returned HTTP 200 with 10 results from AWS, Skill Builder, Credly, and other hosts; Exa reported a $0.007 search cost. This validates key-based API access, not the quality of credential claims or any host MCP integration.

The official Tavily CLI is installed (`tvly` 0.2.1). Browser OAuth completed on 2026-11-10, and `tvly auth --json` now reports `authenticated: true`, method `oauth`. This authenticates the CLI only. Global Tavily Agent Skills have not been installed or verified; provider MCP connections remain inactive.

## 9. Current draft repository structure

```text
portable/Reseacher/                         # requested spelling; normalize to kebab-case before release
├── .agents/                                # navigation entrypoints, not a second prompt source
├── README.md
├── agent.json                              # STF capability request draft
├── plan.md
├── evals/                                  # acceptance criteria; not yet run
├── export/
│   ├── agents/                             # canonical role contracts
│   ├── skills/                             # canonical Markdown skills
│   └── templates/                          # request, record, and output contracts
└── knowledge/
    ├── README.md
    ├── index.md                            # historical leads only; no records verified yet
    └── policies/
```

Publishable records live in the website checkout, not the portable agent bundle:

```text
/Users/ashishchawla/Documents/My-DIY-Projects/n8-rev-build/neighter/
└── content/credentials/
    ├── _index.md                   # Hugo catalog landing page
    └── <stable-credential-id>.md   # one public credential record per file
```

Confirm the final Hugo section layout and fields before adding public records. The existing `data/exams.toml` describes exam-preparation tracks and should not be assumed to be the Credly credential schema.

Keep the stable agent ID kebab-case to match `portable/schemas/agent.schema.json`; resolve the requested directory spelling before implementation so the canonical `portable/{agent-name}/` directory follows `portable/README.md`. The user's requested `.agents/` role prompts must not become a second source of truth: keep canonical role definitions under `export/agents/` and generate/map host-specific files only when the chosen LLM runtime requires them. Store the capability request in a manifest matching the actual `agent.schema.json` fields, including `schema_version`, `agent_id`, `version`, `description`, `inputs_schema`, `outputs_schema`, `required_capabilities`, `optional_capabilities`, `approval_classes`, and `eval_refs`; validate it against that schema before advertising compatibility.

## 10. Evaluation plan (for implementation phase)

Create fixtures for: (1) broad Credly directory grouping and accurate record-derived totals, (2) text search across title/issuer/category/skills/aliases, (3) category and assessment filters, (4) free course + paid exam distinction, (5) unknown rather than false for absent Credly evidence, (6) official LinkedIn verification, (7) conflicting prices across regions, (8) stale exam/version page, (9) duplicate alias/version handling, (10) accreditation scope confusion, (11) prompt injection in fetched content, (12) blocked/private/paywalled page, (13) search budget exhaustion and transparent coverage limits, (14) worker patch missing evidence, (15) conflicting concurrent proposals and no self-approval, (16) profile-based ranking that does not recommend already-held credentials, and (17) no external enrollment/posting. Require source citations per claim, no secret disclosure, valid Markdown record metadata, accessible HTML controls, no external runtime dependencies, and explicit unresolved status for evidence gaps.

No evaluation has been run. The acceptance matrix exists, but provider tools, host adapters, a sample research run, and executable fixtures are not implemented.

## 11. Phased work plan

| Phase | Work | Exit evidence |
|---|---|---|
| 0 — Design review | Review scope, requested directory name, output contract, and approval boundaries | User choices captured; directory spelling remains a release convention issue |
| 1 — Contract draft | Create manifest, role/skills, Markdown record contract, index guide, and evaluation criteria | Draft files created; JSON syntax checked; JSON Schema and host conformance remain unverified |
| 2 — Host/provider assessment | Check Antigravity, Bob, Codex, and Claude versions for search/fetch, file search/write, delegation, secret injection, and approvals; compare native tools with Tavily, Exa, and Firecrawl | Four-host capability matrix, provider/tool choice, and budget/secret-injection plan |
| 3 — Markdown catalog and eval fixtures | Add reviewed seed records from historical leads; create synthetic cases for retrieval, updates, conflict resolution, and injection | No historical claim marked verified without current evidence; fixtures and update workflow documented |
| 4 — Bounded prototype | Implement only after host/provider selection; public read-only research, isolated Markdown proposals, approved website edits, and Hugo-rendered directory | Passing evaluations plus limits and per-host adapter capability report |
| 5 — Review and optional activation | Present exact bundle, requested tools, key injection, content scope, public diff, build/eval evidence, and recovery | Human review before installing adapters or merging to website `main`; main-branch push is the site's publish trigger |
| 6 — Website agent integration | After STF agent finalization, add its approved distributable docs under the website repo's `agents/` folder and update the site's existing agent instructions; prepare the reviewed Markdown credential workflow | Website diff reviewed; Hugo/build checks pass; no publish until separately approved |

## 12. Open decisions

The user selected Antigravity, IBM Bob, Codex, and Claude, broad IT coverage, the target Hugo website, Markdown as source with generated HTML, Tavily/Exa/Firecrawl, and `~/.config/seach-engines/.env`. The Exa skill is installed project-locally, the Researcher prompts require Exa's `query` + `objective` pattern, and a single Exa API smoke test succeeded. Tavily CLI OAuth is authenticated. Remaining checks: install/verify any requested Tavily Agent Skill in the intended coding hosts; configure/test provider MCP integrations only in hosts with a supported secret mechanism; verify all four hosts' file/delegation/tool support; choose numeric research budgets; and confirm the website content section. After the agent itself is finalized, add it under the website repository's `agents/` folder and update existing site instructions as Phase 6. Normalize the requested `portable/Reseacher/` spelling to kebab-case before release.

## 13. Decisions deliberately deferred

This draft installs no provider SDK packages and creates no live MCP server connection or crawler. The Exa Agent Skill is installed project-locally and was used to make one successful API smoke test; Tavily CLI 0.2.1 is installed and OAuth-authenticated. Global Tavily Agent Skills and per-host MCP integration have not been completed. Provider keys/endpoints are configured in the user's private home env file; their values were not copied into the project. The Markdown role/skill/contracts remain drafts; executable adapters and later website `agents/` integration remain gated on provider/runtime assessment and agent finalization.

## 14. Specialist gap review and implementation decisions

Three specialist reviews (LLM-host/runtime, Markdown knowledge workflow, and research quality/security) found the following details must be settled or made explicit before implementation. These are design findings, not evidence that any tool or provider has been installed or validated.

| Missing piece | Recommended default for implementation | Decision status |
|---|---|---|
| LLM hosts and capability maps | Support Antigravity, Bob, Codex, and Claude from one canonical skill/role source using host-specific adapters. Check installed versions and native search/fetch, file search, constrained writes, subagent isolation/delegation, approval gates, secret injection, and website access separately. Add code/providers only for missing capabilities; mark unsupported actions unavailable per host. | Hosts selected; per-host validation remains |
| Canonical agent path and `.agents/` | Use one kebab-case canonical `portable/{agent-id}/` directory, `export/agents/` for canonical role, and `export/skills/` for canonical skills. Requested `portable/Reseacher/.agents/` files are navigation shims only; normalize the directory before release. | Role/skill source drafted; directory normalization deferred |
| Initial catalog scope | Cover nearly all IT sectors, organized by category, while tracking which issuer/category sources were actually checked. Describe the catalog as broad and evidence-bounded, never an exhaustive inventory of every Credly badge. | Operator selected broad IT scope |
| Prior chat seed list | Treat AWS, Tigera, Chainguard, Cisco, ISC2, and other historical examples only as search leads. Promote each into the catalog only after current primary-source verification. | Fixed safety rule |
| Credential Markdown contract | Version the record format. Require stable `credential_id`, name, issuer, canonical URL, category, credential type, version/exam code, aliases, tags, record lifecycle, created/updated/last-verified dates, reviewer reference, and supersedes/successor links. Store each claim with typed value, claim status, source title/type/authority/URL, access date, page publication/update date if available, region/version, evidence note, and conflict reference. Separate record lifecycle from claim status. | Blank record template drafted; sourced sample awaits live verification |
| Search and index | MVP uses host-native full-text search or `rg` over Markdown; index sorted deterministically by category, issuer, and credential ID and generated/checked from front matter. Search name, issuer, aliases, skills, category, and exam code. Defer embeddings until keyword search misses a measured need. | Default unless host lacks search |
| Record freshness | Record access date separately from page publication/update date. Recheck price, availability, assessment, and enrollment claims on every report that presents them as current; otherwise display stale/unknown. Identity and Credly template can use a longer review interval set during implementation. Keep old evidence, but stale records do not count as currently verified. | Exact longer interval to define with evaluation fixtures |
| Research limits and coverage | Each run records categories/issuers checked, queries/pages, limits reached, and known gaps. Enforce per-worker and total page, call, time, and cost budgets in the host/tool layer; stop and report gaps when exhausted. Never imply search depth proves exhaustiveness. | Exact numeric budgets depend on provider and plan |
| Source and claim policy | Prefer issuer/exam-owner sources for credential, cost, prerequisites, and assessment; official Credly for badge issuance; accreditor/register for accreditation; LinkedIn's official flow/help for addability. Secondary sources discover leads only. Negative claims require explicit authoritative evidence; search absence means `not_found` or `unknown`. Preserve conflicting sources and explain resolution. | Drafted in `knowledge/policies/source-policy.md` |
| Assessment taxonomy | The original five labels mix dimensions. Store proctoring, delivery platform, and assessment style separately; derive one display label, including unknown, from those fields. | Applied in the credential-record template |
| Subagent controls | Every packet names task ID, exact issuer/category and record IDs, allowed tools/sources, proposal path, expected fields, done condition, page/call/time/cost limit, and retry/timeout. Workers write only isolated `knowledge/updates/<task-id>/` proposals or return patches; never write canonical records directly. Coordinator/curator validates evidence and duplicates, merges serially, and alone promotes status. Archive or close proposals after merge; never allow self-review. | Numeric limits depend on host; control pattern is fixed |
| Personalization | Run-scoped profile fields: target role/domain, geography, current credentials, experience level, budget/currency, time, preferred formats, and ranked priorities. Exclude already-held credentials. Explain ranking factors and uncertainty; do not claim ATS advantage, hiring outcomes, or prestige without evidence. Do not persist personal profile data in shared catalog by default. | Default can be used unless user changes it |
| Website artifact format and target | Store publishable credential records as Markdown in the specified Hugo website repository; let Hugo render HTML. Keep research proposals as Markdown in the STF agent workspace. Do not maintain raw HTML as a second catalog source. After agent finalization, also add its distributable docs under the site's `agents/` folder and update existing site instructions. | Operator selected website and later specified `agents/` integration; local source confirms Hugo; site edit is deferred until agent finalization |
| HTML generation and safety | Generate from reviewed Markdown. Include only records and claims whose statuses are visible; derive counts from included record IDs and lifecycle state. Escape retrieved text, allow only safe `https` links, and do not render fetched HTML as trusted markup. Preserve keyboard/screen-reader behavior, mobile layout, no-results state, and existing site build conventions. Keep user profile details out of the general directory. | Site-specific acceptance checks remain |
| Run audit notes | Optionally save a Markdown run summary listing scope/as-of date, packet IDs, records created/changed, source dates, unresolved claims, coverage gaps, and output artifact path. It is non-authoritative and contains no raw prompts, keys, or unnecessary personal data. | Recommended |
| Manifest and launch gates | Use the exact fields in `portable/schemas/agent.schema.json`, with real input/output contract references and evaluation IDs. Validate manifest and credential records; check index consistency, search by alias/exam code, patch review, safe links/HTML escaping, accessibility basics, and no candidate counted verified. Report host gaps before activation. | Fixed contract; run mechanism depends on host |
| Search key and MCP endpoint location | Use `~/.config/seach-engines/.env` with owner-only permissions for local hosts; cloud sessions use host secret stores. API keys and endpoint variables are present there. Keep values out of Git and model/subagent context. Host runtime injection and MCP activation are distinct steps. | File configured; runtime injection/MCP verification pending |

### Remaining operator choices

The contract draft is in place. Remaining runtime checks (not new product choices) are:

1. Check the installed versions and actual skill/subagent/tool behavior in all four hosts before generating adapters or granting file writes.
2. Confirm the website's final Hugo content section/layout and visible fields before adding credential Markdown there.
3. Choose numeric query/page/time/cost limits from the provider plans; report actual coverage rather than promise exhaustiveness.
4. Configure local host/tool secret injection from the home `.env` without exposing key values to model context; cloud hosts must use their approved secret stores.

Language remains host-dependent: keep agent instructions, policies, and credential data in Markdown. The website already builds with Hugo and Node scripts, so first use the existing Hugo/Node build path. Add a small helper only if a verified host/site gap requires one; Python is not a prerequisite.

## 15. Host documentation checked

Current official host documentation reviewed on 2026-11-07 for skill discovery and host-specific adapter planning:

- Google Antigravity IDE skills: <https://antigravity.google/docs/skills?app=antigravity-ide>
- IBM Bob skills: <https://bob.ibm.com/docs/ide/features/skills>
- OpenAI Codex skills: <https://developers.openai.com/codex/skills>
- OpenAI Codex `AGENTS.md`: <https://developers.openai.com/codex/guides/agents-md>
- Claude Code skills: <https://code.claude.com/docs/en/skills>
- Claude Code subagents: <https://code.claude.com/docs/en/sub-agents>

These docs establish current skill/instruction mechanisms, not equivalent capabilities across host products. Verify each installed app and available tool surface before claiming that a host can search the website catalog, delegate isolated work, constrain file edits, or inject a home-directory secret.
