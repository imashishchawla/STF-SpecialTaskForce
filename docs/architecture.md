# STF architecture

This document describes the repository foundation. `plan.md` is the master specification. Components below are contracts or planned components unless the repository explicitly contains an implementation.

## Source, distribution, and execution

1. **Repository source:** Human-reviewed manifests, skills, policies, schemas, evaluation cases, and adapter source live here. Draft work stays separate from approved releases.
2. **Portable bundle:** A versioned export contains only approved, non-secret definitions and evidence of its provenance. `portable/bundle.yaml` is currently a template, not a released agent.
3. **Per-host import:** An importer will resolve the account's home directory on macOS, Linux, or Windows and install immutable bundle versions under `~/.stf/bundles/`. An active pointer selects a reviewed version. Another machine, OS account, or cloud session requires its own import or authenticated sync.
4. **Host adapter:** Codex, Google Antigravity, IBM Bob, OpenCode, and Claude Code each discover skills and agents differently. A small adapter will expose the active STF bundle through the host's supported location or tool interface. Discovery of instructions alone does not prove enforcement.
5. **Harness:** A future trusted broker will own task identity, typed tool calls, capability checks, approvals, budgets, cancellation, and observed trace events. A host lacking required mediation must decline side-effecting tasks.
6. **Admin trace service:** Run events will be sent through a narrow write interface to an encrypted, administrator-controlled store outside the shared bundle. Runners may receive their own task result and limited status; the fleet map is admin-only.

## Portable contracts

`portable/schemas/` defines the initial JSON Schema vocabulary for bundles, agents, tasks, results, and trace events. A task is data; an agent is a versioned role; a runtime identity is the process or host acting on that task; and a capability is a narrowly scoped permission. These must not be collapsed into a key per task.

Effective authority is the intersection of host/OS restrictions, STF hard denials, administrator policy, exact task approval, and bundle capability requests. A manifest describes requested authority; the harness must decide and enforce actual authority. Unknown mappings are denied.

## Support tiers

| Tier | What is established | What it cannot claim |
| :--- | :--- | :--- |
| Guidance only | Host discovers the skill or agent instructions | Harness tool enforcement or complete tracing |
| Mediated tools | Side effects pass through scoped STF tools | Complete fleet activity map unless events are correlated |
| Full observation | Mediated tools and correlated run/approval/artifact events | Visibility into unmediated host actions |

An adapter reports its tier and gaps. Portability proof needs the same approved bundle to pass task, policy, and recovery cases on at least two host applications. Each advertised host also needs a discovery check on its target OS.

## Repository boundaries

The current milestone creates documents and draft schemas. It does not create `.agents/` or `.skills/`, install files into `~/.stf/`, start a broker, collect real traces, or touch network hardware. Those actions belong to later phases in `plan.md`.
