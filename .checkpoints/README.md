# Checkpoints and recovery

Before risky implementation, inspect `git status`, identify task-owned paths, and choose an isolated worktree, scoped patch, or other recoverable snapshot. Record exact paths, creation time, owner, and restore method. Do not stage all files or commit the user's unrelated work as an implicit checkpoint.

If work fails, stop writes and review the current diff before restoring only task-owned changes. Broad `git reset --hard` or `git clean -fd` is not an automatic rollback. A later installer also needs an atomic previous-version pointer and a proven revert path before promoting an agent into `~/.stf/`.

No checkpoint has been created for this documentation milestone.
