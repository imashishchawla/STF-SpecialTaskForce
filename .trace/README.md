# Activity trace interface (future)

This directory documents trace contracts only. It is not a storage location for readable run data. The shared portable bundle and host skill directories must never include the fleet activity map or admin keys.

A future runner submits bounded, redacted events through a run-scoped write-only channel. The admin-controlled collector correlates task, parent/child run, runner, host, adapter, policy, approval, tool, artifact, and verification events. Only the authenticated admin may list, search, export, or decrypt fleet traces. The requester may receive their own task result and limited status.

Encrypt content before persistence, define retention and deletion, audit views/exports, and represent missing events as unknown. A collector outage must not silently permit side effects. See `portable/schemas/trace-event.schema.json` and `docs/security.md`.
