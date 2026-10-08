# Harness interface (future)

No harness implementation runs from this repository yet. The planned broker owns task/run identity, tool mediation, scoped credentials, approval checks, timeouts, retries, cancellation, and trace emission. Agent prompts may request actions, but cannot grant authority.

The stable operations are `submit_task`, `inspect_context`, `request_approval`, `invoke_tool`, `emit_event`, `checkpoint`, `cancel_task`, and `finalize_task`. Inputs and results use the versioned contracts under `portable/schemas/`. Each tool result includes status, summary, actionable next steps, artifact references, and an error/recovery hint when relevant.

Use narrow typed tools for high-impact actions. The effective grant is the intersection of host/OS restrictions, STF hard denials, admin policy, exact task approval, and bundle requests. Unknown capabilities fail closed. Side-effecting actions require observed trace coverage at the tier declared for that task; a host that cannot provide it must remain read-only.

See [policy](policies/README.md) and [evaluation](evals/README.md) for the conditions to implement before operation.
