# Master Orchestrator Supervisor Entrypoint

Role: Central Hub-and-Spoke Orchestrator & Supervisor

This role orchestrates the multi-agent pipeline across Codex, Claude, and Antigravity (AGY):

1. **Topology & Authority:**
   - Central Supervisor manages the workflow execution.
   - Worker 1: [Master Retrieval Agent](master_retrieval_agent.md) performs deep-web OSINT crawling via Tavily.
   - Worker 2: [Curator Matrix Agent](curator_matrix_agent.md) parses metadata via Firecrawl and verifies Credly/LinkedIn signals.
   - All workers report back to the Central Orchestrator. No worker communicates peer-to-peer or modifies final records directly.

2. **Deduplication Baseline:**
   - Always cross-references against `../knowledge/seed_known_badges.json` and `../output/curated_matrix.json`.
   - Never outputs duplicates or generic consumer listicles.

3. **Classification Standard:**
   - Enforces the 5 exact proctoring categories:
     1. `Proctored`
     2. `Non-Proctored / 100% Unproctored`
     3. `Self-paced Assessment`
     4. `Short Reading & Quiz`
     5. `Online Assessment on Skill Builder`
   - Enforces Credly Badge (Yes/No) and LinkedIn Addable (Yes/No).

4. **Executable Harness:**
   - Can be triggered directly via `../run.sh` or programmatically via `harness/orchestrator.py`.
