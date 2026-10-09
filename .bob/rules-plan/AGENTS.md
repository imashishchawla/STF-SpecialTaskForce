# AGENTS.md — Plan mode

This file provides guidance to agents when working with code in this repository.

## Non-obvious architectural constraints for planning

- **Current milestone is Phase 1 (foundation only)** — Phases 2–7 exist but are explicitly deferred. Any plan that creates agents, installs files, connects MCP servers, or touches devices is out-of-scope until Phase 2+ is approved.
- **`portable/{agent}/` is the canonical agent structure** — all new agents get `docs/`, `plan/`, and `export/` subdirectories. `export/` contains `agents/`, `skills/`, `mcp/`, `scripts/`, `templates/`. The installer (`install.sh`) discovers agents by scanning for `export/skills/*.md`.
- **`install.sh` is a Phase 1 skeleton** — it validates prerequisites and prints the plan, then halts. Phase 3 will add actual home-directory writes (commented-out stubs already present). Non-interactive invocation: `--agent <name> --hosts <list> [--dry-run]`.
- **Bob skill adapter is generated, not hand-maintained** — `.bob/skills/` is produced by `generate-bob-adapter.sh` from `export/skills/`. The adapter script itself is also a Phase 3 stub: Bob front matter format, symlink support, `skill_id` field format, and path precedence must be confirmed before running it.
- **MCP config is deliberately disabled** — `terraform-mcp.yaml` has `enabled: false`; `allowed_tools` tool names need verification against the live Terraform MCP server before Phase 4. Plans that reference MCP must treat the allowlist as provisional.
- **Skill source files have typed YAML front matter** — `skill_id`, `version`, `status`, `source`, `canonical`, `bob_generated`, `phase`. Planning changes to skills must preserve these fields. `bob_generated` distinguishes canonical sources from generated copies.
- **Harness is not yet implemented** — the planned broker (`submit_task`, `invoke_tool`, `emit_event`, etc.) is a contract in `harness/README.md` only. No enforcement exists today; everything is guidance-tier at best.
- **Authority resolution order is fixed** — host/OS hard restrictions → STF hard denials → admin policy → exact task approval → bundle capability request. A lower layer cannot widen a higher one. Plan changes must respect this hierarchy.
- **Portable bundle export excludes secrets, traces, and private memory by design** — plans that suggest syncing `~/.stf/` across machines or including credentials in bundles violate the architecture.
- **Agent promotion is a multi-step human-approval process** — draft in repo → human review → bundle export + integrity check → operator-reviewed activation. A plan that skips any step is non-compliant.
- **Delegation requires scoped identity and bounded budgets** — coordinator-to-subagent delegation can be disabled without changing specialist contracts. Plans must not assume delegation is always available.
- **Network-device work (Phase 7) requires physical/out-of-band recovery proof before any live change** — never plan a network change without a verified rollback path documented first.
- **Schema `schema_version: 1` is a forward-compat gate** — future importers reject unknown versions. Any plan that bumps `schema_version` must also plan importer, adapter, and conformance-case updates simultaneously.
- **`docs/design/` at repo root and `portable/terraform-support-agent/docs/design/` are identical** — plans must account for keeping both in sync; the `portable/` copy is the distribution copy. Both now include `00a-architecture-diagrams.md`.
- **`memory/` (terraform agent) ≠ `.memory/` (STF project)** — completely separate repos and directories. Plans that reference "memory" must specify which system.
- **Issue pattern `confidence` lifecycle is `candidate → validated → outdated`** — superseded entries are kept (never deleted); `rejected` is also a terminal state. Plans for pattern curation must respect immutability of history.
- **Sub-agent spawn order is fixed** — Diagnostics + Source Researcher (parallel intent, sequential fallback) → Validation Reviewer → Communication Specialist → Memory Curator. No specialist may spawn another specialist.
- **`ENABLE_TF_OPERATIONS=false` is NOT a complete read-only policy** — an explicit tool allowlist in `terraform-mcp.yaml` is mandatory. Plans for MCP integration must include both the flag and the allowlist.
- **10 approval classes each require 3 explicit steps** — pre-announce, in-chat confirmation, audit record. Plans that reference any auth-required action must budget for this overhead.
