# LLM host entrypoints

These files provide the requested `.agents/` entrypoints. They are navigation shims; the canonical instructions live under `../export/agents/` and `../export/skills/` so hosts share one source of truth. If a host requires another file layout, generate a reviewed adapter from the canonical Markdown rather than editing a second prompt copy.

- [Master retrieval role](master_retrieval_agent.md)
- [Curator role](curator_matrix_agent.md)
- [Shared operating contract](operating_contract.md)

Host compatibility and tool availability are not implied by these files. Consult the plan's host matrix before enabling a runtime.
