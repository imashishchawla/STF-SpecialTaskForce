# memory/ops/

Internal operational knowledge — process references, entitlement conditions, escalation paths.

**Contents are internal-only.** Nothing from this directory may appear in customer-visible communication drafts.

## Files

| File | Status | Content |
|---|---|---|
| [`registry-routing.md`](registry-routing.md) | ✅ Created — ⚠️ process_status: interim | Terraform Public Registry routing process (Jira collaboration or email, by severity). **Verify Phase II status with team before use.** |
| [`entitlement-checks.md`](entitlement-checks.md) | ✅ Created — process_status: current | How to verify public registry entitlement in CSP |
| [`escalation-paths.md`](escalation-paths.md) | ✅ Created — process_status: current | Severity upgrade, PagerDuty steps, manager notification triggers, Engineering escalation |

## Phase 4 note

When Jira and CSP MCP connectors are active (Phase 4), the coordinator will use them to populate drafts and query case status. Each ops file has a `## MCP tool integration (Phase 4+)` section with update instructions for that phase.

## Rules

- All entries have a `last_verified` date and a `process_status` field (`current | interim | superseded`).
- Entries marked `interim` must be re-verified before operational use.
- The coordinator loads the relevant ops entry when the case scope requires it.
- Session-only — ops entries are read for the current session; they are not delegated to customer outputs.
- Human-edit only — ops files are updated directly by the operator (not via Memory Curator).
