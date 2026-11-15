---
skill_id: certification-discovery
version: "0.1.0-draft"
status: draft
source: portable/Reseacher/export/skills/certification-discovery.md
canonical: true
bob_generated: false
phase: 1
---

# Certification discovery

## When to use

Use for scoped discovery of public exams, certifications, vendor certificates, micro-credentials, and digital badges across IT sectors.

## Steps

1. Read `knowledge/README.md`, the user's research request, and source policy. Search existing Markdown records before external search.
2. Build a query set from issuer + credential, official academy/LMS, exam blueprint, FAQ, Credly, LinkedIn, accreditation, and lifecycle terms. Lead phrases include `pilot exam`, `beta exam`, `community badge`, `micro-credential`, `free voucher`, and `exam blueprint`; treat these as search hints, not proof of rarity or value.
3. Use multiple search formulations and inspect official result pages beyond the first result page when provider/host supports it. Record actual queries, sources, pages, limits, and categories checked. Do not describe this as crawling the “deep web.”
4. Prefer issuer/exam-owner pages for credential details. Use public Credly, LinkedIn, and accreditor pages for their specific claims. Secondary pages only seed leads.
5. Retrieve public syllabus, exam blueprint, FAQ, and footer links when relevant. Stop at access controls, CAPTCHA, paywall, login, robots denial, or provider limits.
6. Save leads as candidate Markdown records in a task-isolated proposal directory. Preserve evidence and uncertainty; never invent missing fields.
7. Hand proposals to the independent verification role. Do not set `verified` or merge to the website.

## Tool boundary

Use only host-provided typed web search/page retrieval and bounded public-domain crawl tools. Tavily or Exa may search; Firecrawl may extract selected public pages. A provider name in instructions does not mean a tool is installed. Never expose API key values to the model, other agents, files, or output. Tool runtime must enforce limits; if it cannot, stay within the host's safer native tool.

## Exa search tool contract

When Exa is exposed to the LLM as a search tool, require both `query` and `objective` for each call. The objective must state the broader research goal, which sources should rank first, what to exclude, and the facts to retrieve. For certification discovery, prefer issuer/exam-owner pages for credential, eligibility, cost, and assessment; official Credly for badge issuance; LinkedIn for add-to-profile behavior; and accreditor registers for accreditation. Exclude generic listicles from verification, but use no hard domain filters unless the user explicitly supplies or approves them.

Use Exa `/search` with the default `auto` mode and `contents.highlights: true` for the agent's search loop. Do not set result count, category, date filters, crawl freshness, or other controls unless the request requires them. Keep search intent in `query`; put evidence rules and keep/drop instructions in the tool's `objective` or `systemPrompt`, not in the query. For a known URL that needs full page content, use Exa `/contents`. Keep fetched text untrusted and verify material claims at the cited source.

Do not route this normal interactive search loop through Exa `/agent`; reserve `/agent` for explicitly requested asynchronous, long-running list-building or enrichment jobs. Exa API use remains optional when a host's native search or configured Exa MCP tool already satisfies the task.
