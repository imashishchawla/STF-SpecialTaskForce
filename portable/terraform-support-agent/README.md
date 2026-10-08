# Terraform Support Agent

> **Status**: Design-phase artifact — `v0.1.0-draft`. Not yet in active use.
> **Phase**: 3 (Initial Build) — pending design sign-off and onboarding.

A Bob-based agent that helps a HashiCorp / IBM HCP Terraform support engineer
diagnose cases, draft communications, and capture resolved patterns — without
ever taking unsupervised action.

---

## Quick Start (first time)

```bash
# 1. Run onboarding — fills .env and memory/preferences.md
bash export/scripts/onboarding.sh

# 2. Review what was written
cat memory/preferences.md

# 3. Generate Bob skill adapters
bash export/scripts/generate-bob-adapter.sh

# 4. Open Bob in this directory and start a case with the intake skill
```

---

## Directory layout

```
terraform-support-agent/
├── docs/design/          ← 11 design documents (architecture through storage)
├── export/
│   ├── agents/           ← coordinator.md + 5 specialist agent definitions
│   ├── skills/           ← 6 canonical skill files (EDIT HERE, not .bob/skills/)
│   ├── templates/        ← 9 communication templates
│   ├── mcp/              ← terraform-mcp.yaml (enabled: false until Phase 4)
│   └── scripts/          ← onboarding.sh, generate-bob-adapter.sh
├── memory/
│   ├── preferences.md    ← operator config (populated by onboarding.sh)
│   ├── patterns/         ← confirmed issue patterns (written after real cases)
│   ├── ops/              ← internal process docs (registry routing, escalation)
│   └── corrections/      ← accepted corrections to prior diagnoses
├── checkpoints/          ← active case checkpoints (draft/ for in-progress)
├── sources/
│   └── catalog.md        ← 40+ curated sources, priority by claim type
├── evals/
│   └── cases/            ← 10 sanitized evaluation cases (E01–E10 all ✅ Ready)
└── plan/                 ← original design prompt and plan documents
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
| 3 — Initial build | 🔄 Active — skills ✅ templates ✅ evals ✅ ops docs ✅ — pending onboarding run + pilot cases |
| 4 — Retrieval / MCP | ⏳ Requires Phase 3 acceptance — Terraform MCP + Jira/CSP connectors |
| 5 — Specialist delegation | ⏳ Requires Phase 4 acceptance |
| 6 — Controlled automation | ⏳ Requires Phase 5 acceptance |

---

## References

- Full design: [`docs/design/00-overview.md`](docs/design/00-overview.md)
- Implementation plan: [`docs/design/07-implementation-plan.md`](docs/design/07-implementation-plan.md)
- Source catalog: [`sources/catalog.md`](sources/catalog.md)
- Eval cases: [`evals/cases/README.md`](evals/cases/README.md)
