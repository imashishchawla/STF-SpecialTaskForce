# AGENTS.md — Agent (coding) mode

This file provides guidance to agents when working with code in this repository.

## Non-obvious coding rules for this repo

- **No executables to run** — there is no `package.json`, `Makefile`, `pyproject.toml`, or any build tool. Every file change is Markdown, JSON Schema, or shell scripts only.
- **`export/skills/` is the canonical skill source** — never edit `.bob/skills/` directly. After any skill change, run `portable/{agent}/export/scripts/generate-bob-adapter.sh` manually.
- **Skill YAML front matter fields**: `skill_id`, `version`, `status`, `source`, `canonical`, `bob_generated`, `phase` — `bob_generated: false` = canonical source; `true` = generated Bob copy. Don't mix them up.
- **Agent YAML front matter fields**: `agent_id`, `version`, `status`, `phase`, `role`, `entry_point` — structurally different from skill front matter.
- **`generate-bob-adapter.sh` is a Phase 3 stub** — uses `awk` to strip `--- ... ---` YAML blocks and prepend a Bob comment header. Before running: confirm Bob front matter format, symlink vs copy preference, `skill_id` field requirements, and `.bob/skills/` vs `~/.bob/skills/` precedence.
- **`terraform-mcp.yaml` has `enabled: false`** — must be manually set to `true` after Phase 4 allowlist review. Tool names in `allowed_tools` need verification against current Terraform MCP server before Phase 4.
- **`install.sh` halts at a Phase 1 boundary** — actual home directory writes are commented-out stubs gated for Phase 3. Do not uncomment without explicit approval.
- **`install.sh` uses `set -euo pipefail`** — any error exits immediately. Non-interactive test command: `bash install.sh --agent terraform-support-agent --hosts bob --dry-run`.
- **Agent installer auto-discovers agents** by scanning `portable/*/export/skills/*.md` — no registry file needed.
- **Creating `.agents/` or `.skills/` at repo root is forbidden this milestone** — per-agent contracts live in `portable/{agent}/export/agents/`. Check `plan.md` Phase 2–3 before adding anything to repo root.
- **Schema changes require coordinated updates** — editing any file in `portable/schemas/` also requires updating the importer, adapters, conformance cases, and migration notes. Do not edit schemas in isolation.
- **`agent_id` pattern is `^[a-z0-9]+(-[a-z0-9]+)*$`** (kebab, no dots) — `bundle_id` allows dots and dashes `^[a-z0-9]+([.-][a-z0-9]+)*$`. These differ; check the schema before naming.
- **`bundle.schema.json` uses a conditional `if/then`** — released bundles (`status: "released"`) must have non-empty `agents` and `files` and a non-`"UNDECIDED"` license. The current template uses `status: "draft"` intentionally.
- **`.memory/` writes require human curation** — propose, do not commit, lessons or ADRs directly.
- **PII protection and session vault (doc 08)** — all sensitive tokens replaced with `XCVBH-*` tokens before LLM context; raw secrets live in AES-256-GCM vault.
- **Wire format (doc 09)** — inter-agent SignedEnvelope wrapping with TTL and canonical payload hash.
- **`portable/terraform-support-agent/docs/design/` is canonical** — root mirror was retired in P0.
- **A2A component includes submodule** — `portable/terraform-support-agent/a2a/lib/aicoe-agent-utils` is linked via git submodule.
- **`memory/` (terraform agent repo) ≠ `.memory/` (STF repo)** — the agent's persistent memory lives in a separate repo created in Phase 3; STF's `.memory/` is project governance only. Never write terraform case data to `.memory/`.
- **Case aliases are never real ticket numbers in persistent storage** — real ticket ↔ alias mapping lives outside the agent repo in a separate restricted record (MQ-01 unresolved).
- **Draft checkpoints go to `checkpoints/draft/` during a pass; promotion requires operator approval** — coordinator can write drafts, but cannot promote them.
- **Operator tokens** — use `{{operator_name}}`, `{{operator_title}}`, `{{operator_availability}}` in all skill/template output; never hard-code. Resolved from `memory/preferences.md` YAML front matter at runtime.
- **`memory/preferences.md` front matter**: `operator_name`, `operator_title`, `operator_availability`, `agent_repo_path` — all empty strings by default; intake skill asks two onboarding questions if empty, then Memory Curator proposes the write.
- **`docs/agent-dashboard.html`** — standalone HTML diagnostic dashboard; Mermaid from CDN (offline fallback built in); checklist state in `localStorage`. Regenerate by editing `00a-architecture-diagrams.md` in `portable/` and re-running the sync: `cp portable/terraform-support-agent/docs/design/*.md docs/design/`.
- **`result.schema.json` `status: partial`** means findings are complete but one or more sections need more evidence; the draft is provisional. It is not the same as `blocked`.
- **`approval_classes` have a 3-step protocol**: pre-announce → in-chat confirmation → record authorization + actual outcome. Recording a failed action as completed is explicitly prohibited.
- **The 10 approval classes**: `external_message`, `case_update`, `severity_change`, `collaboration_case_creation`, `pagerduty_engagement`, `case_closure`, `run_operation`, `state_operation`, `config_change`, `memory_commit`.
- **Sanitization checklist has 13 items** — all must pass before Memory Curator proposes any persistent write. See `04-memory-and-evidence-schemas.md §10`.
