# AGENTS.md — Ask (documentation) mode

This file provides guidance to agents when working with code in this repository.

## Non-obvious documentation context

- **`plan.md` is the canonical master document** — it contains all schema/contract templates (§7.1–7.5), the ADR format, lesson format, task-history format, and checkpoint SOP. §11.2 has canonical install paths. §13 has installer intent. Other docs summarize it; `plan.md` is authoritative.
- **`harness/`, `builder/`, `.agents/`, `.skills/` contain only READMEs or do not exist** — nothing is implemented. Never describe them as working systems.
- **`portable/bundle.yaml` is not an installable agent** — its `status: draft` with empty `agents` and `skills` arrays is intentional.
- **`portable/{agent-name}/` is the only implemented agent structure** — `docs/design/`, `plan/`, and `export/` (agents, skills, mcp, scripts, templates) sub-directories. Only `terraform-support-agent` exists so far, at design-phase.
- **`export/skills/` source files have YAML front matter** — `skill_id`, `version`, `status`, `source`, `canonical`, `bob_generated`, `phase`. The `bob_generated: false` flag marks canonical source; generated Bob copies use `true`. This distinction is non-obvious from file content alone.
- **`generate-bob-adapter.sh` is a stub with unresolved questions** — Bob front matter format, symlink vs copy preference, `skill_id` field format, and `.bob/skills/` vs `~/.bob/skills/` precedence are all marked TODO for Phase 3 verification.
- **`install.sh` is interactive by design** — it blocks on `read` prompts unless `--agent` and `--hosts` are passed. With `--dry-run`, it exits cleanly after showing the plan. Nothing writes to home directories (Phase 1 boundary).
- **"Portability" means same contracts, not identical behavior** — the same bundle on two runtimes will behave differently; the portable core is neutral, host adapters handle specifics.
- **Admin activity map vs. runner view** — runners see only their own task result and status; fleet map/cross-run search is admin-only. This distinction is non-negotiable.
- **Five planned host targets** — IBM Bob (`~/.bob/skills/`), Codex (`~/.agents/skills/`), Google Gemini (`~/.gemini/config/skills/`), OpenCode (`~/.config/opencode/skills/`), Claude Code (`~/.claude/skills/`). None is installed or verified yet.
- **Support tier vocabulary** — "guidance only", "mediated tools", "full observation" are defined terms with specific meanings in `docs/architecture.md`. Do not use them loosely.
- **`docs/design/` at repo root and `portable/terraform-support-agent/docs/design/` are identical** — the `portable/` copy is the distribution copy; the repo root is the working draft. Both now include `00a-architecture-diagrams.md` (8 Mermaid diagrams).
- **`memory/` (terraform agent) ≠ `.memory/` (STF project)** — two completely separate directories in two separate repos. Never describe them as the same thing. The agent's `memory/` does not exist yet; it is a Phase 3 artifact.
- **CasePacket is a structured Markdown document with 9 sections** — not a JSON payload. `case_alias` is always an internal alias, never the real ticket number. Real ticket ↔ alias mapping lives outside the agent repo (MQ-01).
- **Three `RequestedOutput` types that produce structured artifacts**: `handoff` → exact 5-field format; `can_report` → exact 5-field format; both are in `memory/preferences.md`.
- **Operational knowledge files (`memory/ops/`) are session-scoped by default** — the coordinator reads them per session but must never embed their content in checkpoints, memory patterns, or customer-visible output.
- **Support tier vocabulary** — "guidance only", "mediated tools", "full observation" are defined terms in `docs/architecture.md`. Do not use loosely.
