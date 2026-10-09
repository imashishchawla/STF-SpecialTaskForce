# Terraform Support Agent

> **Status**: Build-phase artifact — `v0.1.0-draft`. Not yet in active use.
> **Phase**: 3b (Portability Remediation) — `installer.sh` ready; pending pilot run.

A Bob-based agent that helps a HashiCorp / IBM HCP Terraform support engineer
diagnose cases, draft communications, and capture resolved patterns — without
ever taking unsupervised action.

---

## Quick Start (first time)

```bash
# 1. Run the installer (fills .env, memory/preferences.md, generates Bob adapters)
bash installer.sh install

# Optionally include the A2A optional component:
bash installer.sh install --a2a

# Preview what would happen without touching anything:
bash installer.sh install --dry-run
```

Other useful subcommands:

```bash
bash installer.sh status          # show .env, preferences, MCP, and A2A status
bash installer.sh mcp             # install/enable Terraform MCP server
bash installer.sh propel          # configure Propel connections
bash installer.sh start --a2a     # start the A2A server (if installed)
bash installer.sh stop  --a2a     # stop the A2A server
bash installer.sh remove          # uninstall (prompts before removing data)
```

For manual steps only: `bash export/scripts/onboarding.sh` (fills `.env` and `memory/preferences.md` interactively).

---

## Directory layout

```
terraform-support-agent/
├── installer.sh          ← single entry point: install/modify/start/stop/status/remove/mcp/propel
├── docs/design/          ← 11 design documents (architecture through storage)
├── export/
│   ├── agents/           ← coordinator.md + 5 specialist agent definitions
│   ├── skills/           ← 6 canonical skill files (EDIT HERE, not .bob/skills/)
│   ├── templates/        ← 9 communication templates
│   ├── mcp/              ← terraform-mcp.yaml (enabled: false until Phase 4)
│   └── scripts/          ← onboarding.sh (manual), generate-bob-adapter.sh
├── a2a/                  ← optional A2A component (not installed by default)
├── memory/
│   ├── preferences.md    ← operator config (populated by installer/onboarding)
│   ├── patterns/         ← confirmed issue patterns (written after real cases)
│   ├── ops/              ← internal process docs (registry routing, escalation)
│   └── corrections/      ← accepted corrections to prior diagnoses
├── checkpoints/          ← active case checkpoints (draft/ for in-progress)
├── sources/
│   └── catalog.md        ← 40+ curated sources, priority by claim type
├── evals/
│   └── cases/            ← 10 sanitized evaluation cases (E01–E10 all ✅ Ready)
└── plan/                 ← design prompt, plan documents, and archive
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
| 3 — Initial build | 🔄 Active — skills ✅ templates ✅ evals ✅ A2A scaffold ✅ `installer.sh` ✅ — pending pilot run |
| 3b — Portability remediation | 🔄 Active — Dockerfile removed ✅ onboarding scoped ✅ `installer.sh` created ✅ |
| 4 — Retrieval / MCP | ⏳ Requires Phase 3 acceptance — Terraform MCP + Jira/CSP connectors |
| 5 — Specialist delegation | ⏳ Requires Phase 4 acceptance |
| 6 — Controlled automation | ⏳ Requires Phase 5 acceptance |

---

## References

- Full design: [`docs/design/00-overview.md`](docs/design/00-overview.md)
- Implementation plan: [`docs/design/07-implementation-plan.md`](docs/design/07-implementation-plan.md)
- Installer: [`installer.sh`](installer.sh)
- Portability plan: [`plan/portability-readiness-plan.md`](plan/portability-readiness-plan.md)
- Source catalog: [`sources/catalog.md`](sources/catalog.md)
- Eval cases: [`evals/cases/README.md`](evals/cases/README.md)
