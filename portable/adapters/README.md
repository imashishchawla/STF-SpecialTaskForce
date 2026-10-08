# Host adapters (future)

One portable bundle will be rendered into each host's supported skill/agent discovery location or exposed through a brokered tool bridge. This directory will hold adapter source and conformance notes after agent design. It currently contains no active adapter.

Documented global skill locations are [Codex `~/.agents/skills/`](https://learn.chatgpt.com/docs/build-skills), [Antigravity `~/.gemini/config/skills/`](https://antigravity.google/docs/skills), [IBM Bob `~/.bob/skills/`](https://bob.ibm.com/docs/ide/features/skills), [OpenCode `~/.config/opencode/skills/`](https://opencode.ai/docs/skills), and [Claude Code `~/.claude/skills/`](https://code.claude.com/docs/en/skills). Installed versions and discovery behavior require direct checks. Cloud sessions may require separate installation.

Every adapter will declare its support tier: guidance only, mediated tools, or full observation. It must report version, installation path, capability mapping, approval behavior, trace coverage, unsupported features, uninstall, and rollback. Loading a skill never implies that host-native shell or filesystem actions are mediated.
