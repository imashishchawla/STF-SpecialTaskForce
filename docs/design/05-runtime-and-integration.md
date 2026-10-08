# Design 05 — Runtime and Integration Assessment

> **Status**: Draft — awaiting operator review.  
> **Prepared**: 2 October 2026.  
> **Scope**: Design phase only. No runtime code, MCP configs, or skill adapters are created here.

---

## 1. Chosen runtime: IBM Bob (Phase 1–3)

The coordinator and specialists run within IBM Bob's workspace, reflecting the existing support work. Bob is the primary runtime for the foreseeable future.

Key constraints that affect the design (verified from plan Section 9 and IBM Bob documentation references):

| Constraint | Impact on design |
|---|---|
| Bob requires approval before each sub-agent spawn | Parallel Diagnostics + Source Researcher is intended but cannot be guaranteed; coordinator must handle sequential fallback |
| Sub-agents are context-explicit (no implicit shared state) | Coordinator must package all necessary context in each task packet |
| `.agents/` does not register runnable native agents by itself | Role contracts in `.agents/` are specifications; they become effective only through Bob's skill/agent mechanisms |
| Bob skill discovery paths: `.bob/skills/` and `~/.bob/skills/` | `.skills/` is canonical human source; a generated adapter produces `.bob/skills/` entries |
| No unattended or scheduled execution in this runtime | Manual case import is the only entry path |
| Bob runs within IBM workspace permissions | All STF approval gate hierarchy applies |

---

## 2. Bob skill adapter design

### Problem

Bob discovers skills from `.bob/skills/`, but the canonical human-maintained source for this agent is `.skills/`. Maintaining copies in both locations manually would create drift and conflicts.

### Solution: Generated adapter

```
.skills/                          ← CANONICAL (human edits here)
    intake.md
    diagnosis.md
    source-check.md
    registry-routing.md
    reproduction.md
    communication.md

        │
        │  adapter generation script (future — Phase 3)
        │  e.g., scripts/generate-bob-adapter.sh
        ▼

.bob/skills/                      ← GENERATED (never edit manually)
    intake.md                     ← symlink or copy with Bob-specific front matter injected
    diagnosis.md
    source-check.md
    registry-routing.md
    reproduction.md
    communication.md
```

### Adapter rules

1. `.bob/skills/` entries are **never edited manually** — all changes go to `.skills/` first.
2. The generation script is run manually when `.skills/` changes (no auto-sync in Phase 3).
3. The generation script adds any Bob-specific front matter (e.g., `model`, `temperature`, `tools`) without altering the skill content.
4. If `.bob/skills/` and `.skills/` diverge (e.g., after a failed generation), `.skills/` is the authoritative source.

### Verification required (before Phase 3 implementation)

- [ ] Confirm the exact front matter format required by the target Bob version for skill files
- [ ] Confirm whether Bob supports symlinks or requires full copies
- [ ] Confirm whether `.bob/skills/` entries require a specific `skill_id` format
- [ ] Confirm whether the Bob version in use loads from both `.bob/skills/` and `~/.bob/skills/`, and which takes precedence

---

## 3. Terraform MCP server integration

### Overview

The official Terraform MCP server provides registry and HCP Terraform / Terraform Enterprise tools. It is an optional capability (Phase 4 onward). The agent must not depend on it in Phase 3.

### Read-only allowlist (proposed)

`ENABLE_TF_OPERATIONS=false` is **not** a complete read-only policy (confirmed from plan Section 9). An explicit tool allowlist is mandatory.

Proposed initial allowlist — read and query only:

```yaml
terraform_mcp_allowed_tools:
  # Documentation tools
  - resolveProviderDocID        # resolve provider doc ID from registry
  - getProviderDocs             # fetch provider documentation
  - searchProviderDocs          # search within provider docs

  # Registry query tools (read-only)
  - listProviderDataSources     # list available data sources
  - listProviderResources       # list available resource types
  - getResourceDetails          # get resource schema details
  - searchModules               # search the public registry for modules

  # HCP Terraform query tools (read-only — pending credential scope confirmation)
  # None enabled in Phase 4 initial; enable after explicit allowlist review

terraform_mcp_blocked_tools:
  # ALL mutation and execution tools — blocked regardless of ENABLE_TF_OPERATIONS setting
  - createRun
  - cancelRun
  - discardRun
  - createWorkspace
  - updateWorkspace
  - createVariable
  - updateVariable
  - deleteVariable
  - lockWorkspace
  - unlockWorkspace
  - createPolicySet
  - assignPolicySet
  - uploadStateVersion
  - createConfigurationVersion
  - uploadConfigurationFiles
  # ... any tool that creates, modifies, or deletes a resource
```

> This allowlist is a design proposal. The exact tool names must be verified against the current Terraform MCP server reference during Phase 4.

### Scoped credentials

When HCP Terraform read-only tools are enabled (Phase 4):

- Credentials must be scoped to read-only team token or read-only user token
- Token must not have `write` scope on workspaces, variables, runs, state, or policies
- Token must never be passed in chat — only injected via environment variable or approved secrets vault
- Token scope must be documented in the approval record before first use

---

## 4. Integration dependency assessment

### Jira

| Aspect | Status |
|---|---|
| Connector availability | Not assumed; not authorized |
| Manual fallback | the operator creates Jira collaboration cases manually using the steps from `registry-routing` skill |
| Phase for integration | Phase 4 (if approved) — read-only query of assigned Jira issues only |
| Approval class | `collaboration_case_creation` (write) requires explicit approval |

### CSP / Salesforce

| Aspect | Status |
|---|---|
| Connector availability | Not assumed; not authorized |
| Manual fallback | the operator inputs case context manually via case packet |
| Phase for integration | Phase 4 (if approved) — read-only case query only |
| Approval class | `case_update` (write) and `severity_change` require explicit approval |

### PagerDuty

| Aspect | Status |
|---|---|
| Connector availability | Not assumed; not authorized |
| Manual fallback | the operator executes PagerDuty engagement manually using steps from `registry-routing` skill |
| Phase for integration | Not planned; Sev 1 requires human judgment |
| Approval class | `pagerduty_engagement` always requires explicit approval — never automated |

### AskSW / Internal KB

| Aspect | Status |
|---|---|
| Connector availability | Not assumed; not authorized |
| Manual fallback | the operator pastes relevant excerpts into case packet |
| Phase for integration | Evaluate in Phase 4 based on availability |

---

## 5. Missing connector handling

When a capability is not available or not authorized, the coordinator must:

1. State the specific capability that is missing
2. Provide the manual path — what the operator should do instead
3. Not claim the action was taken
4. Not retry in ways that could expose credentials or access restricted systems

Example output when Jira is unavailable:

```
⚠️ Jira connector not available
Manual path: [steps from registry-routing skill for creating the collaboration case]
```

---

## 6. Capability declaration model

Each agent contract declares `required_capabilities` and `optional_capabilities` (from STF `agent.schema.json`). Mapping to runtime availability:

| Capability | Phase available | Source |
|---|---|---|
| `read_supplied_evidence` | Phase 3 | Manual case packet |
| `search_approved_public_sources` | Phase 3 | Tavily / web search via Bob |
| `write_sanitized_checkpoints_proposed` | Phase 3 | File write to `checkpoints/draft/` |
| `read_current_memory_entries` | Phase 3 | File read from `memory/` |
| `spawn_*_subagent` | Phase 3 (approval each time) | Bob sub-agent mechanism |
| `terraform_mcp_read_allowlist` | Phase 4 | Terraform MCP server (read-only) |
| `jira_read_assigned_cases` | Phase 4 (if approved) | Jira connector |
| `csp_read_case_details` | Phase 4 (if approved) | CSP connector |
| `reproduction_execution` | Phase 6 | Approved isolated environment |

---

## 7. Action audit log design

Each approved and executed action produces an audit record. Format:

```markdown
## Action audit: <action_id>

| Field | Value |
|---|---|
| Timestamp | ISO 8601 with timezone |
| Action | exact action taken |
| Target | exact target (system, resource, identifier) |
| Authorization | `authorized_by: ashish_chawla` + `authorized_at: <timestamp>` |
| Evidence reference | STF evidence_ref ID |
| Rationale | one sentence |
| Outcome | what actually happened |
| Status | completed / failed / partial |
```

Audit records go in `checkpoints/<case_alias>-pass-<n>.md` under an "Approved actions" section. They are sanitized before checkpoint promotion.

---

## 8. Alternative runtime (future consideration)

If unattended execution or scheduled tasks become necessary, a separate orchestration runtime (e.g., LangChain, Autogen, custom script) could host the coordinator. This is not planned for Phases 1–5. Requirements for that phase:

- Same `.agents/` and `.skills/` definitions (portable)
- Separate credential storage (vault, not chat)
- Same approval gate and audit model
- Explicit user authorization for scheduling itself

---

## 9. Unresolved design questions

| # | Question | Impact |
|---|---|---|
| RQ-01 | What is the exact front matter format required by the current Bob version for skill files? | Blocks Phase 3 adapter implementation |
| RQ-02 | Does Bob support symlinks in `.bob/skills/`, or must files be full copies? | Affects adapter design |
| RQ-03 | What is the maximum context size for a Bob sub-agent task packet? | Affects how much evidence can be included per delegation |
| RQ-04 | What is the exact Terraform MCP tool name list in the current server version? | Affects allowlist accuracy |
| RQ-05 | Are Jira and CSP read-only connectors available and authorized in the operator's IBM Bob workspace? | Affects Phase 4 scope |
| RQ-06 | Does the Bob version support parallel sub-agent spawning, or is approval always sequential? | Affects whether parallel Diagnostics + Source Researcher is possible |

---

*Previous: [`04-memory-and-evidence-schemas.md`](04-memory-and-evidence-schemas.md) | Next: [`06-registry-routing.md`](06-registry-routing.md)*
