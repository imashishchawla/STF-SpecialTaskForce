# Certification Researcher

**Status:** Draft instructions and contracts. Not installed or activated in a host.

This is an LLM-hosted research workflow for Antigravity, IBM Bob, Codex, and Claude. The model follows the role and skill Markdown; the host supplies search, page extraction, file search, and scoped file access. Tavily, Exa, and Firecrawl are optional provider backends, not an independent CrewAI runtime.

## Start here

1. Read [`plan.md`](plan.md) and [`export/agents/certification-research-curator.md`](export/agents/certification-research-curator.md).
2. Load the discovery and verification skills from `export/skills/` as needed.
3. Search the Markdown knowledge base using the host's file search or ordinary text search. See [`knowledge/README.md`](knowledge/README.md).
4. Put worker findings in a unique `knowledge/updates/<task-id>/` folder. The curator reviews evidence and duplicates before accepting changes.
5. Keep accepted public records as Markdown in the Hugo website repository; its build generates HTML. Website edits and publication are separate review gates.

## Repository map

- `export/agents/`: canonical role contracts.
- `export/skills/`: canonical, reusable discovery and validation procedures.
- `.agents/`: requested navigation/compatibility entrypoints. These point to canonical contracts and must not become a second source of truth.
- `export/templates/`: request, record, and report shapes.
- `knowledge/`: source policy, lifecycle, search index, and isolated proposals.
- `evals/`: evaluation criteria and fixtures; no evaluations have been run.

The Exa `build-with-exa` skill is installed for this STF project at the repository root `.agents/skills/build-with-exa/`. No Researcher-specific host adapter or provider MCP connection has been activated. Do not place key or endpoint values in this repository. Provider keys and MCP endpoint settings are in `~/.config/seach-engines/.env`; see `plan.md` for the boundary and cloud-hosted secret-store requirement.

## Current limitations

Host versions and actual tool support have not been tested. A host must provide public web search and page retrieval plus scoped Markdown read/write before this workflow can run. Delegation is optional: when unavailable, the coordinator performs the same retrieve-review-merge steps serially. No output may claim an exhaustive Credly inventory.
