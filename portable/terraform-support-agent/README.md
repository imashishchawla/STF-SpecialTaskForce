# Terraform Support Agent

> **Status**: `v0.1.0-draft`; Phase 3b consolidation and installer remediation active. P0 (consolidation), P1 (installer rewrite), and P2 (A2A security package) complete. P4 documentation & eval suite active.

A Bob-based agent that helps a HashiCorp / IBM HCP Terraform support engineer
diagnose cases, draft communications, and capture resolved patterns — without
ever taking unsupervised action.

---

## Quick start

```bash
# Preview all options without writing anything
bash installer.sh help
bash installer.sh install --dry-run

# Interactive menu (detects existing install automatically)
bash installer.sh

# Machine-readable output for Bob chat
bash installer.sh status --json
```

### Commands — new system (no existing install)

| Command | Description |
|---|---|
| `install` | Stage and verify agent, register Bob mode, optionally add A2A. |
| `package` | Create a signed `.tar.gz` release archive of approved assets. |
| `status` | Show that no install exists yet. |
| `help` | Print full usage. |

### Commands — existing install detected

| Command | Description |
|---|---|
| `reinstall` | Reinstall the same verified version; repair manifest-owned files only. |
| `install` | Stage, verify, and activate a reviewed local version (covers updates too). |
| `package` | Create a signed release archive. |
| `remove` | Preview then remove installed agent, owned adapters, and launcher. |
| `propel` | Show Bob/Propel version, display permission changes, install on approval. |
| `update` | Check configured trusted remote for a newer signed release and install on approval. |
| `status` | Show install state, Bob skills, A2A, and MCP status. |
| `help` | Print full usage. |

### Additional subcommands (always available)

| Command | Description |
|---|---|
| `modify` | Preview and apply a scoped change to host, settings, version, or A2A component. |
| `start` | Start the A2A server (requires prior install with A2A; use `--a2a`). |
| `stop` | Stop the A2A server. |
| `mcp` | Install optional MCP server prerequisites (`terraform-mcp`, `playwright-mcp`). |

### Flags

| Flag | Description |
|---|---|
| `--dry-run` | List all planned writes, network requests, and process actions — no changes made. |
| `--json` | Machine-readable `{"status":…,"message":…}` output for Bob chat integration. |
| `--no-start` | During `install`, stage A2A but do not start the server. |
| `--purge` | With `remove`: also remove named local state after a backup preview. |
| `--host bob\|propel` | Target host adapter. Unknown values error — never silently ignored. |
| `--a2a` | Include A2A setup during `install`/`reinstall`/`modify`. Default is to skip. |

### Safety contract

- `dry_exec()` never uses `eval` — all mutating calls use explicit argument arrays.
- `--host` is validated; unknown values error immediately.
- Installed-state detection runs before any prompt or action.
- `remove` deletes only manifest-owned files; operator data is preserved unless `--purge`.
- `update` never executes unreviewed code; shows diff, verifies GPG signature, requires selection.
- No `git reset --hard` or `git clean -fd` at any point.

---

## Directory layout

```
terraform-support-agent/
├── installer.sh          ← lifecycle manager (P1 rewrite complete; commit 6338fd0)
├── docs/
│   ├── agent-dashboard.html ← standalone diagnostic dashboard
│   └── design/          ← canonical Terraform design documents (00–10 + 00a)
├── export/
│   ├── agents/           ← coordinator.md + Bob mode YAML
│   ├── skills/           ← 7 canonical skill files (EDIT HERE, not .bob/skills/)
│   ├── templates/        ← 9 communication templates
│   ├── mcp/              ← terraform-mcp.yaml (enabled: false until Phase 4)
│   └── scripts/          ← onboarding.sh (manual), generate-bob-adapter.sh
├── a2a/                  ← optional A2A scaffold; P2 security package implemented
│   ├── security/         ← PII redaction, AES-GCM session vault, SignedEnvelope validation, bind guard
│   └── tests/            ← 18 passing offline unit tests
├── memory/
│   ├── preferences.md    ← operator config (populated by installer/onboarding)
│   ├── patterns/         ← confirmed issue patterns (written after real cases)
│   ├── ops/              ← internal process docs (registry routing, escalation)
│   └── corrections/      ← accepted corrections to prior diagnoses
├── checkpoints/          ← active case checkpoints (draft/ for in-progress)
├── sources/
│   └── catalog.md        ← 40+ curated sources, priority by claim type
├── evals/
│   ├── runner.py         ← automated eval runner for cases E01–E10
│   ├── cases/            ← 11 sanitized cases (E01–E11)
│   └── results/          ← session result records
└── plan/
    ├── portability-readiness-plan.md ← active priorities (P0 ✅, P1 ✅, P2 ✅, P4 🔄)
    └── archive/          ← completed original plan, prompt, PDF, agent history
```

---

## Rules (non-negotiable)

| Rule | Detail |
|---|---|
| **Edit skills in `export/skills/`** | Never edit `.bob/skills/` directly — run `generate-bob-adapter.sh` after changes |
| **No `.env` in git** | `.env` is excluded by `.gitignore` — never commit it |
| **No live customer data in `evals/`** | All eval cases use sanitized or synthesized inputs only |
| **Memory writes require human approval** | The agent proposes, you approve — Memory Curator never writes directly |
| **Auth boundary** | External messages, case updates, severity changes, closures all require explicit per-action approval |
| **Redact before delegate** | Intake must confirm redaction before any evidence is passed to a specialist |

---

## Phase status

| Phase | Status |
|---|---|
| 1 — Plan approved | ✅ Complete |
| 2 — Design | ✅ Complete (11 design docs, decisions signed off) |
| 3 — Initial build | Source files present; pilot evaluations pending |
| 3b — Portability remediation | Active; installer and A2A behavior not yet verified |
| 4 — Retrieval / MCP | ⏳ Requires Phase 3 acceptance — Terraform MCP + Jira/CSP connectors |
| 5 — Specialist delegation | ⏳ Requires Phase 4 acceptance |
| 6 — Controlled automation | ⏳ Requires Phase 5 acceptance |

---

## References

- Full design: [`docs/design/00-overview.md`](docs/design/00-overview.md)
- Implementation plan: [`docs/design/07-implementation-plan.md`](docs/design/07-implementation-plan.md)
- Diagnostic dashboard: [`docs/agent-dashboard.html`](docs/agent-dashboard.html)
- Installer: [`installer.sh`](installer.sh)
- Plan index: [`plan/README.md`](plan/README.md)
- Portability plan: [`plan/portability-readiness-plan.md`](plan/portability-readiness-plan.md)
- Completed planning inputs: [`plan/archive/`](plan/archive/)
- Source catalog: [`sources/catalog.md`](sources/catalog.md)
- Eval cases: [`evals/cases/README.md`](evals/cases/README.md)
