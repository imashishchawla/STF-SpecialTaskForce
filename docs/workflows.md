# STF workflows

## Repository foundation (current)

Read `plan.md` and `AGENTS.md`; inspect the worktree; make a scoped documentation or contract change; review the result; record exactly what is specified versus implemented. Do not mark an agent or integration available from a file blueprint alone.

## Agent creation (later)

1. Ask the human what problem they want solved, how they work today, inputs, expected output, and unacceptable behavior. Capture an example and success criteria.
2. Search current first-party documentation, local assets, and reputable open-source candidates. Check source, version, license, dependencies, maintenance, and fit. Present reuse, adapt, combine, or build options.
3. Draft a manifest, skill, capability request, adapter plan, and evaluation cases in the repository. Show the proposed plan, tool use, output, uncertainty, and approval points.
4. Let the human correct the draft. Evaluate it in an isolated environment and record failures.
5. Present the exact bundle, permissions, sources, checks, destination, and recovery method. Promote only the approved version.

## Task run (later)

Intake → inspect and validate → propose plan → obtain any exact-action approvals → execute through mediated tools → verify independently → produce a human summary → propose durable lessons for review. The harness records concise plan revisions and observed events with parent and child run IDs. It does not store hidden reasoning.

## Export and installation (later)

Build a non-secret portable archive; validate hashes and schemas; import to the account's `~/.stf/` on each target host; generate only the selected host adapters; verify discovery, invocation, effective policy, and rollback. Cloud or remote hosts need explicit import or synchronization. No installer is implemented yet.

## Network-device work (later)

Use the inventory in `plan.md` to ask for exact models, firmware, topology, target state, backup and recovery access, and maintenance window. Begin with read-only discovery. A reset, OS reinstall, or reconfiguration requires a device-specific runbook, verified backup/recovery path, exact-action approval, and independent post-change checks. This repository milestone does not operate devices.
