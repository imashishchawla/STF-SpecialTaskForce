# STF — Special Task Force

STF is a repository for designing portable, human-governed agents. The current milestone builds the repository foundation. No agent, adapter, harness service, home installation, or network automation is active yet.

Start with [plan.md](plan.md). It records the full target architecture, the repo-first roadmap, portability and admin visibility rules, and the supplied network-device inventory. [AGENTS.md](AGENTS.md) gives contributors the repository operating rules.

## Repository map

| Location | Purpose | State |
| :--- | :--- | :--- |
| `docs/` | Architecture, workflow, and security decisions | Foundation specification |
| `portable/` | Bundle template and runtime-neutral contract schemas | Draft contracts; no published bundle |
| `harness/` | Tool mediation, policy, and evaluation interface | Design only |
| `builder/` | Interactive agent-creation flow | Design only |
| `evals/` | Acceptance gates for future implementations | Design only |
| `.mcp/`, `.trace/`, `.memory/`, `.history/`, `.checkpoints/` | Integration and state governance | Documentation only |
| `.agents/`, `.skills/` | Future agent and skill definitions | Deferred until the human-led agent-design phase |

## How the portable library will work

An approved bundle will be exported from this repository and imported into each user's home as `~/.stf/`. Each LLM application needs its own small adapter or supported tool bridge to discover that bundle. The shared library will not contain credentials or readable fleet activity traces. [Architecture](docs/architecture.md) and [security](docs/security.md) describe the boundaries.

## Next milestone

After the repository foundation is reviewed, interview the human about the first agent's problem and workflow, research existing solutions and licenses, then draft and evaluate an agent. The Sophos, Cyberoam, Aruba, TP-Link, Syrotech, and Netgear inventory is planning context in [plan.md](plan.md); it does not authorize device changes.
