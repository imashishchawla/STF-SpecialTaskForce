# Terraform Support Agent

> **Status**: `v0.1.0-draft`; Phase 3b consolidation and installer remediation are active. No portable install or A2A runtime has been accepted.

A Bob-based agent that helps a HashiCorp / IBM HCP Terraform support engineer
diagnose cases, draft communications, and capture resolved patterns — without
ever taking unsupervised action.

---

## Current entry points

The existing `installer.sh` has draft commands that can write to `~/.bob/`. Its `install --a2a` option does not yet install or start A2A, and the new menu, package, update, signing, and rollback behavior is specified in the [priority plan](plan/portability-readiness-plan.md). Inspect the plan and preview before using the live path.

```bash
bash installer.sh help
bash installer.sh install --dry-run
```

The planned single installer will detect existing installations and offer Re-install, Install / Update, Package, Remove Installer, Install / Update Propel, and Update from Repo. In a terminal these are numbered choices; Bob chat will offer equivalent buttons. The planned ASCII Terraform-themed mark will show “Making Terraform Support Simple” and “Created by Ashish Chawla.” Signed packages and repository permissions will establish authorship and detect changes; a distributed executable script cannot be made uneditable by encryption. Propel and MCP activation remain behind their phase gates.

---

## Directory layout

```
terraform-support-agent/
├── installer.sh          ← draft lifecycle script; expanded menu planned
├── docs/
│   ├── agent-dashboard.html ← standalone diagnostic dashboard
│   └── design/          ← canonical Terraform design documents (00–10)
├── export/
│   ├── agents/           ← coordinator.md + 5 specialist agent definitions
│   ├── skills/           ← 6 canonical skill files (EDIT HERE, not .bob/skills/)
│   ├── templates/        ← 9 communication templates
│   ├── mcp/              ← terraform-mcp.yaml (enabled: false until Phase 4)
│   └── scripts/          ← onboarding.sh (manual), generate-bob-adapter.sh
├── a2a/                  ← optional A2A scaffold; security implementation pending
├── memory/
│   ├── preferences.md    ← operator config (populated by installer/onboarding)
│   ├── patterns/         ← confirmed issue patterns (written after real cases)
│   ├── ops/              ← internal process docs (registry routing, escalation)
│   └── corrections/      ← accepted corrections to prior diagnoses
├── checkpoints/          ← active case checkpoints (draft/ for in-progress)
├── sources/
│   └── catalog.md        ← 40+ curated sources, priority by claim type
├── evals/
│   └── cases/            ← 11 sanitized cases (E01–E11); pilot results pending
└── plan/
    ├── portability-readiness-plan.md ← active priorities
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
