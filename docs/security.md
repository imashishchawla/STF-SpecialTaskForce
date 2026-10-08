# STF security and approval boundaries

## Trust boundaries

The human sets intent. Repository documents and agent manifests are versioned proposals. Websites, third-party packages, tool responses, and device output are untrusted data. The future harness, rather than prompt text, must mediate side effects and emit observed events. Host/OS restrictions and STF hard denials cannot be widened by a skill or a model suggestion.

## Approval classes

| Action | Boundary |
| :--- | :--- |
| Read-only repository inspection and scoped local drafts | Allowed within the requested task |
| Installing or activating an agent, adapter, policy, or shared memory change | Human review of the exact version and effects |
| Sending external messages, changing shared Git state, changing permissions, deployment, or using credentials | Exact-action authorization and applicable host policy |
| Deleting user work, resetting devices, reinstalling firmware/OS, or changing live network configuration | Device/target-specific approval, recovery proof, maintenance window, and post-change checks |

Approval is bound to action, target, version, scope, and expiry. A materially changed action needs a new approval. A denial is not overridable by a lower-priority instruction.

## Portable library and secrets

An export contains definitions, schemas, provenance, checksums, licenses, and evaluation references. It excludes credentials, private keys, personal memory, raw chats, device backups, and traces. Future installers must resolve user home per OS and verify bundle integrity before activation. Runtime secrets come from the destination's credential store and are scoped to the task.

## Admin activity map

The initial recommended administrator is the human owner of STF. Enroll a distinct key pair or passkey and a recovery credential. Keep private material in an OS credential store or hardware authenticator. `~/.stf/` must not contain the admin private key or readable fleet traces. Runners use a narrow run-scoped event submission channel with no list/search/decrypt access. A separate encrypted service or OS identity protects trace storage. If a host has unrestricted shell under that same privileged identity, admin-only visibility has not been proven and must not be claimed.

Map access and export require admin authentication and are audited. Trace payloads are minimized and redacted before storage. Define retention and deletion before recording real task content. Missing telemetry is shown as unknown; where audit is required, a failed collector pauses side effects after a bounded encrypted buffer fills.

## Recovery

Inspect `git status` and exact task-owned paths before changing repository state. Prefer isolated worktrees or scoped patches for risky work. Broad reset and clean commands are not automatic rollback. For devices, verify out-of-band or physical recovery before any action that could remove network access.
