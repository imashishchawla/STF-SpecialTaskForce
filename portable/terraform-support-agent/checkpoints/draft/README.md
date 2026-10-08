# checkpoints/draft/

Staging area for in-progress checkpoint writes during a coordinator pass.

Files here are **not yet approved** — they are working copies only.

## Lifecycle

1. Coordinator writes a draft checkpoint here during an active investigation pass.
2. At the end of the pass, the coordinator presents the draft to the operator for review.
3. Operator approves → file is promoted to `checkpoints/<case_alias>-pass-<n>.md`.
4. Operator rejects or modifies → draft is updated and re-presented.

## Rules

- Draft files follow the same sanitization requirements as promoted checkpoints.
- Draft files are deleted or archived after promotion.
- Never reference a draft checkpoint path in a customer communication.

## Empty — populated during active case passes.
