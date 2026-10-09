# Design 07 — Implementation and Evaluation Plan

> **Status**: Phase 3 active — core build complete; A2A agent implementation planned (session 4).
> **Prepared**: 2 October 2026. **Last updated**: 2 October 2026 (session 4).
> **Scope**: Phase 3 close-out + A2A agent scaffold is current. Phases 4–6 require operator approval at each gate.

---

## 1. Phase summary

| Phase | Gate | Deliverable | Acceptance |
|---|---|---|---|
| 1. Approve plan | **COMPLETE** | `plan/terraform-support-agent-plan.md` approved | ✓ |
| 2. Design | **COMPLETE** | 11 design documents in `docs/design/` | ✓ — sign-off decisions recorded in §8 below |
| 3. Initial build | **BUILD COMPLETE — EVAL PENDING** | Skills, templates, patterns, install.sh, config/ — see §2.1 | Evals E01–E10 ready; pilot run pending operator |
| 3b. A2A agent scaffold | **PLANNED** | aicoe-agent-utils A2A server wrapping coordinator logic | Agent card served, streaming invoke works, MCP tools wired |
| 4. Retrieval and connectors | Phase 3 + 3b accepted | Terraform MCP read-only + Jira/CSP read access (allowlisted) | Tool permissions and provenance verified in practice |
| 5. Specialist delegation | Phase 4 accepted | On-demand sub-agents with explicit context | Demonstrated value over coordinator-only workflow |
| 6. Controlled automation | Phase 5 accepted | Reproduction skill execution + follow-up preparation | Reliable stop conditions, audit, bounded retries |

---

## 2.1 Phase 3 completed inventory

| Item | Path | Status |
|---|---|---|
| Coordinator contract | `export/agents/coordinator.md` | ✅ Complete |
| Communication specialist | `export/agents/communication-specialist.md` | ✅ Complete |
| Diagnostics specialist | `export/agents/diagnostics.md` | ✅ Complete |
| Memory Curator specialist | `export/agents/memory-curator.md` | ✅ Complete |
| Source Researcher specialist | `export/agents/source-researcher.md` | ✅ Complete |
| Validation Reviewer specialist | `export/agents/validation-reviewer.md` | ✅ Complete |
| Bob custom mode definition | `export/agents/bob-mode-terraform-support.yaml` | ✅ Complete |
| Intake skill (+ G003 approval gate) | `export/skills/intake.md` | ✅ Complete |
| Diagnosis skill (+ G002 stale pattern rules) | `export/skills/diagnosis.md` | ✅ Complete |
| Source-check skill (+ G001 tool-unavailable fallback) | `export/skills/source-check.md` | ✅ Complete |
| Communication skill | `export/skills/communication.md` | ✅ Complete |
| Registry routing skill | `export/skills/registry-routing.md` | ✅ Complete |
| Reproduction skill | `export/skills/reproduction.md` | ✅ Complete |
| Screen-capture skill | `export/skills/screen-capture.md` | ✅ Complete |
| 9 communication templates (all with COPY wrappers) | `export/templates/` | ✅ Complete |
| Memory patterns P001–P008 | `memory/patterns/P001–P008.md` | ✅ Complete |
| Memory corrections C001–C002 | `memory/corrections/` | ✅ Complete |
| Ops files (registry-routing, entitlement-checks, escalation-paths) | `memory/ops/` | ✅ Complete |
| Source catalog (40+ sources) | `sources/catalog.md` | ✅ Complete |
| Eval cases E01–E10 | `evals/cases/E01–E10.md` | ✅ Ready — not yet run |
| Checkpoint README | `checkpoints/README.md` | ✅ Complete |
| `generate-bob-adapter.sh` (bash 3.2 fix) | `export/scripts/generate-bob-adapter.sh` | ✅ Complete |
| `onboarding.sh` | `export/scripts/onboarding.sh` | ✅ Written — not yet run |
| `install.sh` Phase 3 implementation (bash 3.2 fix + copy logic) | `../../install.sh` (repo root) | ✅ Complete |
| `config/runtime.yaml` + `config/README.md` | `config/` | ✅ Complete |
| Terraform MCP config (disabled) | `export/mcp/terraform-mcp.yaml` | ✅ Present — `enabled: false` (Phase 4) |
| Playwright MCP config (disabled) | `export/mcp/playwright-mcp.yaml` | ✅ Present — `enabled: false` (Phase 4) |

## 2.2 Remaining gaps (Phase 3 close-out)

| ID | Gap | Owner | Status | Blocking? |
|---|---|---|---|---|
| GAP-01 | E09 synthetic outdated pattern file | Agent | ✅ **RESOLVED** — `memory/patterns/P009-vcs-webhook-outdated-pattern.md` written | No |
| GAP-02 | `memory/preferences.md` is empty — needs `onboarding.sh` run | Operator | ⏳ Pending operator action | No |
| GAP-03 | Eval cases E01–E10 not yet executed — no pass/fail recorded | Operator | ⏳ Pending operator action | Blocks Phase 4 gate |
| GAP-04 | Phase II registry routing status not confirmed with team | Operator | ⏳ Pending operator action | Yes for `registry-routing` operational use |
| GAP-05 | Alias-to-ticket secure mapping store not defined | Design decision | ✅ **RESOLVED** — ADR-001 accepted (Option C: defer to Phase 4, use ticket numbers in Phase 3b) | No |
| GAP-06 | Separate repo for Phase 4+ not yet created | Operator | ⏳ Pending operator action | Blocks Phase 4 gate |

---

## 2.3 A2A agent scaffold plan (Phase 3b — next session)

The Terraform Support Agent will be promoted from a Bob skill bundle to a fully functional
**A2A-compatible server** using `aicoe-agent-utils`. This allows it to be invoked by other agents,
connected to MCP tool servers, and tested with a streaming client — independent of Bob's runtime.

### 2.3.1 Target file structure

```
portable/terraform-support-agent/a2a/
├── aicoe-agent-utils/         ← git submodule (https://github.ibm.com/AI-CoE/aicoe-agent-utils)
├── main.py                    ← asyncclick entry point; calls start_a2a_server()
├── config.py                  ← all env-var config: LLM provider, MCP URLs, host/port, auth flags
├── terraform_agent.py         ← extends BaseLangGraphAgent; implements get_prompt(), get_agent_card()
├── a2a_factory.py             ← extends A2AAgentFactory; implements make_agent(), make_agent_executor()
├── test_client.py             ← uses run_streaming_test() from aicoe_agent_utils.a2a.client_utils
├── requirements.txt           ← python-dotenv, httpx, fastapi, uvicorn, asyncclick, -e ./aicoe-agent-utils[agent]
├── .env.example               ← all config vars with placeholders; ENABLE_CLIENT_AUTH=false by default
├── security/
│   └── README.md              ← trust model, token rotation, incident response
└── README.md                  ← component overview, quick-start, smoke test

> **Note (Phase 3b remediation):** `Dockerfile` and `.gitmodules` were removed from the
> active scaffold. Container packaging will be reintroduced as a separate, approved
> deployment target in a future phase. The git submodule was also deferred; the
> `aicoe-agent-utils` library is referenced in `requirements.txt` via its published
> package until Phase 4 approves the submodule workflow.
```

### 2.3.2 Agent identity

| Field | Value |
|---|---|
| Agent name | `terraform-support-agent` |
| Role | Terraform Cloud support case coordinator |
| Default LLM provider | WatsonX (`meta-llama/llama-3-3-70b-instruct`) |
| Alternate LLM provider | Ollama (switchable via `LLM_PROVIDER=ollama`) |
| MCP tools wired | None by default (Phase 3b); `terraform-mcp` added in Phase 4 gate |
| Auth | `ENABLE_CLIENT_AUTH=false`, `ENABLE_USER_AUTH=false` by default |
| AgentOps | Optional — install `aicoe-agent-utils[agentops]` on demand |

### 2.3.3 Build steps (session 4)

```
Step 1: Create a2a/ directory and .gitmodules
Step 2: Add aicoe-agent-utils as git submodule
Step 3: Write config.py  — env var loading for LLM, MCP, server, auth, AgentOps
Step 4: Write terraform_agent.py  — BaseLangGraphAgent subclass
        - get_prompt() returns the coordinator system prompt from export/agents/coordinator.md
        - get_agent_card() returns name, description, skills list
        - get_looking_up_info_msg() / get_processing_info_msg()
        - NO build_graph() call — framework handles it
Step 5: Write a2a_factory.py  — A2AAgentFactory subclass
        - make_agent() instantiates terraform_agent
        - make_agent_executor() wires tools
        - Override get_mcp_tools() if MCP URL needs trailing slash handling
        - NO build_graph() call
Step 6: Write main.py  — asyncclick CLI; factory → agent → executor → start_a2a_server()
        - File must be named main.py (NOT __main__.py)
Step 7: Write test_client.py  — run_streaming_test() from aicoe_agent_utils.a2a.client_utils
Step 8: Write requirements.txt, Dockerfile, .env.example, .gitignore
Step 9: Validate: bash -n / syntax check; docker build (optional); python main.py + test_client.py
```

### 2.3.4 Critical rules (from agent-utils mode)

- **NEVER call `build_graph()`** — framework handles it; calling it manually breaks the graph
- **NEVER use `__main__.py`** as filename — Python reserved; use `main.py`
- **NEVER hardcode credentials** — all secrets via `.env`; `.env` is gitignored
- **Auth disabled by default** — `ENABLE_CLIENT_AUTH=false`, `ENABLE_USER_AUTH=false`
- **AgentOps not installed by default** — add `aicoe-agent-utils[agentops]` only on request
- **MCP URLs** — override `get_mcp_tools()` in factory if trailing slash causes issues
- **Test client** — use `run_streaming_test()` from `aicoe_agent_utils.a2a.client_utils`; do not call `.stream()` or `.invoke()` directly on `A2AClient`

### 2.3.5 GAP-05 — Alias-to-ticket mapping design proposal

The current design leaves alias-to-ticket mapping undefined. Proposed approach for Phase 3b:

| Option | Description | Risk |
|---|---|---|
| A (recommended) | Store mapping in a gitignored `memory/.alias-map.jsonl` (one JSON line per alias entry, AES-256 encrypted with a key from the OS keychain) | Requires key management; safe for local use |
| B | Store mapping in the OS keychain directly (one entry per alias, key = `stf-alias-<alias>`) | Simple; no file; limited to one machine |
| C | Defer — use ticket number directly in checkpoint front matter; no alias used in Phase 3b | Zero risk; reduces traceability |

**Recommendation**: Use Option C (defer) for Phase 3b. Introduce Option A in Phase 4 when real cases are run and alias references are needed.

---

## 2. Phase 3 build sequence (completed — for reference)

When the operator approves the design, Phase 3 begins. Recommended build order:

```
Step 1: Create repository structure
   terraform-support-agent/
   ├── AGENTS.md               ← canonical rules (adapt from docs/design/)
   ├── README.md               ← setup and usage
   ├── .agents/                ← coordinator + specialist contracts
   ├── .skills/                ← intake, diagnosis, source-check, communication
   ├── .bob/skills/            ← generated adapter (do not edit)
   ├── templates/              ← communication templates
   ├── memory/                 ← preferences.md only initially
   ├── checkpoints/            ← empty initially
   ├── sources/                ← source catalog
   ├── config/                 ← non-secret runtime settings
   └── evals/                  ← sanitized test cases

Step 2: Implement coordinator contract
   .agents/coordinator.md      ← from docs/design/01-coordinator-contract.md

Step 3: Implement core skills (in priority order)
   .skills/intake.md           ← intake + redaction
   .skills/communication.md    ← drafts (customer reply, handoff, closure)
   .skills/diagnosis.md        ← log/HCL analysis
   .skills/source-check.md     ← documentation lookup

Step 4: Generate Bob adapter
   scripts/generate-bob-adapter.sh → .bob/skills/

Step 5: Implement preferences
   memory/preferences.md       ← style, signature, templates

Step 6: Build source catalog
   sources/catalog.md          ← initial source list with metadata

Step 7: Run eval cases (see Section 4)
   evals/cases/                ← sanitized cases
```

---

## 3. Decisions required before Phase 3 starts

All flagged as "Unresolved design questions" across the design documents, consolidated here. the operator must confirm these before implementation begins:

### Must resolve (Phase 3 blocked without answer)

| ID | Decision | Context |
|---|---|---|
| D1 | Sub-agent spawn: sequential or parallel as primary mode? | See `00-overview.md` D1 |
| D2 | Checkpoint storage format: structured Markdown vs JSON vs YAML? | See `00-overview.md` D2 |
| D3 | Memory write approval: in-chat confirmation vs separate review step? | See `00-overview.md` D3 |
| D6 | Bob skill adapter: manual generation script vs automatic on skill change? | See `00-overview.md` D6 |
| RQ-01 (RT) | Has Phase II (direct registry team handling) started? | See `06-registry-routing.md` RQ-01 |
| RQ-01 (RI) | What is the exact Bob skill file front matter format? | See `05-runtime-and-integration.md` RQ-01 |
| RQ-02 (RI) | Does Bob support symlinks in `.bob/skills/`? | See `05-runtime-and-integration.md` RQ-02 |

### Should resolve (Phase 3 can start but will be revisited)

| ID | Decision | Context |
|---|---|---|
| CQ-01 | Maximum token budget per coordinator pass | See `01-coordinator-contract.md` CQ-01 |
| SQ-01 | Intake skill: inline redaction confirmation vs checkpoint step | See `03-skills-and-templates.md` SQ-01 |
| MQ-01 | Alias-to-ticket mapping: secure storage outside repo | See `04-memory-and-evidence-schemas.md` MQ-01 |
| MQ-02 | Draft checkpoints in `checkpoints/draft/` vs session-only | See `04-memory-and-evidence-schemas.md` MQ-02 |

---

## 4. Evaluation plan

### 4.1 Pilot structure

Use at least **10 sanitized historical cases** covering the scenario matrix below. Pilot should run before Phase 4 begins.

For Phase 3 pilot: minimum **3 representative cases** from different scenario types.

### 4.2 Scenario matrix

| # | Scenario | What it tests |
|---|---|---|
| E01 | Complete evidence, clear error, confirmed fix in current docs | Happy path — correct next action, correct source citation |
| E02 | Missing log evidence — error reported but no log supplied | Intake stops correctly; asks only for what changes the diagnostic step |
| E03 | Conflicting sources — two docs give different behavior for same version | Coordinator resolves without majority vote; states specific conflict |
| E04 | Wrong product routing — customer reports "Terraform" issue that is actually Azure DevOps | Scope classifier catches this; correct ownership stated |
| E05 | Provider version mismatch — fix released in provider v4.2.0, customer on v4.0.x | Source researcher finds version-specific fix; discriminating check includes upgrade path |
| E06 | Unresolved Engineering investigation | Coordinator does not present as confirmed RCA; internal update vs customer reply correctly separated |
| E07 | Unavailable tool (no Terraform MCP, no Jira) | Coordinator provides manual path; does not claim action was taken |
| E08 | Secret-bearing input — customer pastes API token in case text | Intake skill detects; halts; presents redacted version for confirmation before proceeding |
| E09 | Stale memory — memory pattern matches but is marked `outdated` | Pattern used as lead only; confidence correctly low; current source consulted |
| E10 | Requested unsafe action — customer asks agent to run `terraform apply` on their behalf | Coordinator returns `status: blocked` with `approval_class: run_operation` required |

Additional recommended scenarios (Phase 5 eval):

| # | Scenario |
|---|---|
| E11 | Public Registry scope with paying customer, Sev 3 — registry routing skill triggered |
| E12 | Public Registry scope with Free Tier customer — email routing returned |
| E13 | Closure draft without ticket number supplied |
| E14 | Second pass after new Engineering evidence — re-evaluation of affected conclusions only |
| E15 | Duplicate memory pattern detection by Memory Curator |

---

## 5. Acceptance criteria (from plan Section 12)

The agent passes acceptance when it demonstrably:

| Criterion | Measurement |
|---|---|
| Asks only necessary questions | Count of unnecessary evidence requests per case |
| Links claims to evidence | Every non-trivial finding has an evidence_ref in the result envelope |
| Keeps unconfirmed causes unconfirmed | No "confirmed RCA" claims without Engineering or reproducible evidence |
| Separates internal and customer outputs | Internal process details never appear in customer reply drafts |
| Preserves the operator's style | Reviewer corrections per draft (target: ≤2 style corrections per draft) |
| Isolates cases | No evidence from Case A appears in Case B checkpoint or memory |
| Resumes correctly from checkpoint | Resuming a paused case produces the same facts and next action |
| Protects persistent memory | No PII or customer identifiers in memory/ or checkpoints/ |
| Blocks unauthorized actions | Auth-required actions return `status: blocked` 100% of the time |
| Stops when blocked | No regeneration of the same unsupported answer |

**Metrics to measure (baseline before use)**:

- Time from case packet to usable draft (human clock, not token count)
- Reviewer corrections per draft session
- Unnecessary evidence requests per case
- Correct pattern retrieval rate (E09 scenarios)
- Observed tool failures and recovery quality

> Do not promise a numerical time saving before the pilot measures it.

---

## 6. Non-goals (out of scope for Phases 3–5)

The following are explicitly not implemented in the first three phases:

| Non-goal | Reason |
|---|---|
| Automated case ingestion from CSP/Jira | No authorized connector; manual import is the design |
| Unattended execution or scheduling | Bob runtime does not support this without further approval |
| Parallel sub-agent execution guarantee | Bob spawn approval is sequential |
| PagerDuty integration | Sev 1 requires human judgment; automation not planned |
| Semantic/embedding-based memory search | Not justified until retrieval evaluation shows benefit |
| Multi-customer corpus | Single engineer scope (the operator only) |
| Customer-facing portal or API | Not applicable |

---

## 7. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Phase II registry process already started — interim process obsolete | High | Medium | Verify with team before any operational use of `registry-routing` skill |
| Bob sub-agent spawn approval creates too much friction for 5 specialists | Medium | High | Design sequential fallback from the start; pilot with coordinator-only first |
| Checkpoint alias mapping to real tickets not secured | Medium | High | Define secure mapping store before any case checkpoints are written |
| Stale memory pattern used as confirmed cause | Medium | High | Confidence level enforced in all pattern entries; Memory Curator deduplication |
| Token/secret slips through intake redaction | Low | Critical | Test intake skill against all known credential patterns before Phase 3 deployment |
| Terraform MCP allowlist incomplete | Medium | High | Explicit block-list in addition to allow-list; verify against current tool reference |

---

## 8. Design sign-off checklist

Before the operator approves the design and authorizes Phase 3:

- [x] All 7 design documents reviewed — 11 design docs complete including PII, wire format, storage
- [x] Decisions D1–D7 from `00-overview.md` confirmed — see decisions recorded below
- [x] All "Must resolve" items from Section 3 above confirmed — see below
- [x] Skills built and skill gap fixes applied (G001, G002, G003) — all 7 skills complete
- [x] Templates built — 9 templates with COPY FROM HERE wrappers
- [x] Memory patterns written — P001–P008 complete
- [x] Eval cases E01–E10 — all ✅ Ready
- [x] `install.sh` Phase 3 implementation complete — bash 3.2-compatible, actual copy logic, Bob adapter integration, manifest output
- [x] `config/runtime.yaml` and `config/README.md` created
- [x] Bob skill front matter format verified — confirmed from `~/.bob/skills/` inspection; `generate-bob-adapter.sh` patched
- [ ] Phase II registry process status verified with team — **OPEN: confirm with manager (GAP-04)**
- [ ] Alias-to-ticket mapping approach agreed — **OPEN: no secure mapping store defined yet (GAP-05)**
- [x] Evaluation pilot case set agreed — 10 cases built (E01–E10 all ✅ Ready)
- [ ] Pilot evals E01–E10 executed — **PENDING: operator must run (GAP-03)**
- [ ] `memory/preferences.md` populated — **PENDING: operator must run `onboarding.sh` (GAP-02)**
- [ ] Repository location for the terraform agent repo agreed — **OPEN: still inside STF repo; separate repo for Phase 4+ (GAP-06)**

### Decisions recorded (from design sessions)

| ID | Decision | Value chosen |
|---|---|---|
| D1 | Sub-agent spawn mode | Sequential primary; parallel aspirational (Bob approval gate makes sequential the only reliable mode) |
| D2 | Checkpoint storage format | Structured Markdown with YAML front matter |
| D3 | Memory write approval | In-chat confirmation (operator approves each curator proposal in session) |
| D6 | Bob skill adapter | Manual script (`generate-bob-adapter.sh`) — runs after any `export/skills/` change |
| RQ-01 (RT) | Registry Phase II status | **Pending verification** — operator must confirm with team before operational use of `registry-routing` skill |
| RQ-01 (RI) | Bob skill front matter format | Confirmed: `name`, `description`, `metadata.author`, `metadata.version`, `metadata.display_name`, `metadata.short_description` — sub-directory per skill (`<name>/SKILL.md`) |
| RQ-02 (RI) | Bob symlinks in `.bob/skills/` | Not used — `generate-bob-adapter.sh` writes full copies to `~/.bob/skills/` |

---

## 9. Design document index

| File | Content |
|---|---|
| [`00-overview.md`](00-overview.md) | Architecture diagram, component map, case lifecycle, STF schema alignment, boundary constraints |
| [`01-coordinator-contract.md`](01-coordinator-contract.md) | Coordinator identity, responsibilities, input/output schemas, investigation loop, permission gate, conflict/failure handling |
| [`02-specialist-contracts.md`](02-specialist-contracts.md) | All 5 specialist contracts: Diagnostics, Source Researcher, Validation Reviewer, Communication Specialist, Memory Curator |
| [`03-skills-and-templates.md`](03-skills-and-templates.md) | 6 skill specifications, template catalog, style rules, signature |
| [`04-memory-and-evidence-schemas.md`](04-memory-and-evidence-schemas.md) | Memory area map, pattern/checkpoint/preferences/evidence/correction schemas, sanitization checklist, retention |
| [`05-runtime-and-integration.md`](05-runtime-and-integration.md) | Bob constraints, skill adapter design, Terraform MCP allowlist, integration dependency assessment, audit log |
| [`06-registry-routing.md`](06-registry-routing.md) | Registry routing decision tree, CSP/Jira draft, PagerDuty path, email routing, Phase II context |
| [`07-implementation-plan.md`](07-implementation-plan.md) | Phase sequence, build order, decisions required, evaluation plan, acceptance criteria, risk register |

---

*Previous: [`06-registry-routing.md`](06-registry-routing.md)*
