# Research provider MCP configuration notes

The user stores provider endpoint values and API keys in `~/.config/seach-engines/.env`. Never copy their values into this repository. The host must read these variables through its own supported secret/environment mechanism:

| Provider | API key variable | MCP endpoint variable | Purpose |
|---|---|---|---|
| Tavily | `TAVILY_API_KEY` | `TAVILY_MCP_SERVER` | Search, extract, map, and bounded crawl |
| Exa | `EXA_API_KEY` | `EXA_MCP_SERVER` | Semantic search and known-page retrieval |
| Firecrawl | `FIRECRAWL_API_KEY` | `FIRECRAWL_MCP_SERVER` | Public-page extraction and bounded crawling |

These variables are configured locally, but this file does not establish an active MCP connection. Configure each host separately, allow only the tools needed by the Researcher, and verify that the host can inject credentials without exposing them in model context, tool output, or persistent agent files. If a host cannot safely pass the provider's required authentication header, use the host's supported secret integration or the provider's API from a trusted local process; do not put a key into a URL or checked-in config.

## Exa routing for this agent

For the interactive LLM search loop, prefer Exa's hosted MCP `web_search_exa` tool when the host has it enabled. Exa's canonical hosted endpoint is `https://mcp.exa.ai/mcp`; use the configured `EXA_MCP_SERVER` value when setting up the host. Exa MCP can run at a free rate limit without a key; authenticated use requires sending the key with the provider-supported header. Do not assume that one host's header/environment support applies to another host.

When using Exa's API or SDK directly, follow the installed `build-with-exa` skill. Each LLM search call supplies `query` and `objective`; retrieve concise highlights with the default search mode. Use query phrasing and the objective for source preferences; don't add categories, domain filters, result counts, or freshness options unless requested. `/contents` is for a known URL. `/agent` is for explicitly asynchronous, long-running discovery—not the normal per-turn search tool.

## Other providers

Tavily's official remote MCP endpoint is documented in the Tavily setup guide. Use the configured endpoint value and the provider's auth scheme; do not treat the installed `tvly` CLI as authenticated until `tvly auth --json` succeeds. Firecrawl's configured MCP endpoint is similarly host-specific. Keep all three providers optional so one unsupported or unauthenticated MCP server does not block the other search path.

## Per-host verification checklist

- Record host and version; confirm the actual endpoint and approved auth mechanism without recording key material.
- Confirm only the required tools are exposed and that public-page access limits are enforced.
- Run one test search and one known-URL retrieval; record status, source URLs, retrieval time, and sanitized error information.
- Confirm the host treats fetched pages as untrusted data and the agent cites primary evidence.
- If tools were added after the host session started, restart/rescan before claiming they are active.
