# Migration Intelligence Harvester Agent — Instructions & Architecture

**Document Version:** 2.0.0 (Enhanced with Political Horizon Scanning & Autonomous Source Trust Engine)  
**Effective Date:** 10 November 2026  
**Package:** `portable/Visa-Agent/`  
**Agent Role:** `agent_migration_intelligence_harvester`

---

## 1. System Overview & Cognitive Mission

The **Migration Intelligence Harvester Agent** is an autonomous, self-evaluating intelligence gathering and policy analysis agent integrated into the `Visa-Agent` ecosystem. Beyond simple scraping, it possesses **cognitive comprehension capabilities** designed to:

1. **Nationwide PR & Visa Radar:** Continuously track skilled migration (189, 190, 491), employer sponsorship (482, Skills in Demand, 186), visitor visas (600), and student transitions across all Australian states and territories.
2. **Political & Legislative Horizon Scanning:** Monitor federal politics, parliamentary debates (Hansard), ministerial statements, Senate inquiry hearings, and electoral party platforms (Labor, Coalition, Greens) regarding Net Overseas Migration (NOM) caps, housing targets, and immigration intake quotas.
3. **Autonomous Source Discovery & Trust Validation:** Dynamically evaluate newly discovered sources, legal blogs, and news outlets against an objective **Trust & Reputation Matrix** before ingesting claims into the knowledge bank.
4. **Self-Managed Cognitive Knowledge Bank:** Autonomously process raw articles, discern **Signal vs. Noise**, calculate legislative probabilities, assess cohort-level impacts (specifically for ICT/Tech occupations), and publish curated Daily and Weekly Digests.

---

## 2. End-to-End System Architecture (ASCII Flow Diagram)

```text
+---------------------------------------------------------------------------------------------------+
|                                 WIDE-SPECTRUM DISCOVERY HORIZON                                   |
+---------------------------------------------------------------------------------------------------+
|  [Official Statutory Portals]      [Political & Legislative Radar]   [Community & Industry Pulse] |
|  * DHA Gazettes & SkillSelect      * Parliamentary Hansard & Bills   * Reddit (r/AusVisa, r/Aus)  |
|  * State Migration (VIC/NSW/WA/QLD)* Ministerial Press Releases      * Whirlpool Immigration      |
|  * Assessing Bodies (ACS/VETASSESS)* Election Manifestos & NOM Policy* Law Council & MARA Blogs   |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                         SCRAPING & RETRIEVAL LAYER (Existing Engine Keys)                         |
+---------------------------------------------------------------------------------------------------+
|   +-----------------------+   +------------------------+   +----------------------------------+   |
|   |       EXA API         |   |      FIRECRAWL         |   |           TAVILY API             |   |
|   | (Neural / Discussions |   | (Deep DOM Crawler /    |   | (Real-time Breaking News /       |   |
|   |  & Community Forums)  |   |  JS-Rendered Portals)  |   |  Parliament & Press Releases)    |   |
|   +-----------------------+   +------------------------+   +----------------------------------+   |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                 MIGRATION INTELLIGENCE HARVESTER: COGNITIVE PROCESSING BRAIN                      |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|   +-------------------------------------------------------------------------------------------+   |
|   | 1. Dynamic Source Discovery & Trust Scorer:                                               |   |
|   |    * Inspects new domain authority, OMARA registration, legal citations, and past bias.   |   |
|   |    * Assigns Trust Score (0-100) -> Admits into catalog or flags as Unverified Lead.     |   |
|   +-------------------------------------------------------------------------------------------+   |
|                                                 |                                                 |
|                                                 v                                                 |
|   +-------------------------------------------------------------------------------------------+   |
|   | 2. Political & Legislative Impact Evaluator:                                              |   |
|   |    * Classifies: Enacted Law vs. Tabled Bill vs. Inquiry Recommendation vs. Party Rhetoric|   |
|   |    * Calculates Impact Probability: High (Passed), Medium (Bipartisan), Low (Rhetoric)    |   |
|   +-------------------------------------------------------------------------------------------+   |
|                                                 |                                                 |
|                                                 v                                                 |
|   +-------------------------------------------------------------------------------------------+   |
|   | 3. Cohort & Policy Synthesis Engine:                                                      |   |
|   |    * Maps macro announcements directly to candidate cohorts (e.g. ICT 2613/2631, 189, 190)|   |
|   |    * Determines actionable consequence: (e.g. "Quota tightening imminent -> Lodge now")  |   |
|   +-------------------------------------------------------------------------------------------+   |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                  SELF-MANAGED PERSISTENT KNOWLEDGE LEDGER (Visa-Agent/knowledge/)                 |
+---------------------------------------------------------------------------------------------------+
|   * digests/daily_YYYY-MM-DD.md       (Chronological daily regulatory & political briefs)         |
|   * digests/weekly_summary.md         (Weekly macro trends, quota health & legislative risks)     |
|   * live_cutoffs/gsm_rounds.md        (189/190/491 invite cutoffs by ANZSCO)                      |
|   * political_radar/policy_bills.md   (Active legislative bills, ministerial targets & NOM caps)  |
|   * trusted_sources_catalog.json      (Self-updating domain trust reputation registry)            |
+---------------------------------------------------------------------------------------------------+
                       |                                                     ^
                       | (Feeds Fresh Rules, Cutoffs & Risks)                | (Queries Intel / Trends)
                       v                                                     |
+---------------------------------------------------------------------------------------------------+
|                          VISA-AGENT SYSTEM TOPOLOGY & SPECIALISTS                                 |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|                       +--------------------------------------------------+                        |
|                       |            MASTER MIGRATION COORDINATOR          |                        |
|                       |        (master_migration_coordinator.md)         |                        |
|                       +--------------------------------------------------+                        |
|                                                 |                                                 |
|         +-----------------------+---------------+-----------------------+                         |
|         |                       |                                       |                         |
|         v                       v                                       v                         |
|   +-------------------+   +--------------------+                  +---------------------------+   |
|   |  PR / GSM EXPERT  |   |  VISITOR EXPERT    |                  |    ACS EVIDENCE AUDITOR   |   |
|   | (agent_pr_gsm_    |   | (agent_visitor_    |                  |  (agent_acs_evidence_     |   |
|   |  specialist.md)   |   |  visa_specialist)  |                  |   auditor.md)             |   |
|   +-------------------+   +--------------------+                  +---------------------------+   |
|         |                       |                                       |                         |
|         v                       v                                       v                         |
|   +-------------------------------------------------------------------------------------------+   |
|   |                         ISOLATED CLIENT CASE DATA & DOSSIERS                              |   |
|   |                  (Strict PII Isolation: .profile/<client-name>/)                          |   |
|   +-------------------------------------------------------------------------------------------+   |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
                                                  ^
                                                  |
                                            USER INQUIRY
                          (e.g., "Any political updates on PR caps?"
                             or "Did Victoria change tech cutoffs?")
```

---

## 3. Autonomous Source Discovery & Trust Validation Engine

When the Harvester uncovers a new URL, news platform, law firm advisory, or industry report during web crawls, it does not accept it blindly. It runs an automated **4-Factor Source Trust Evaluation**:

```text
[Raw Web Hit / New Domain Discovered]
                  │
                  ▼
┌────────────────────────────────────────────────────────┐
│             4-FACTOR TRUST SCORING MATRIX              │
│                                                        │
│  1. Legal Accreditation: Is author MARA / Legal Firm?  │
│  2. Direct Statutory Citation: Links to Acts/Gazettes? │
│  3. Historical Accuracy: Verified vs clickbait record  │
│  4. Publication Origin: Official Gov vs Tabloid/Blog   │
└────────────────────────────────────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────────────────┐
│ Score >= 85 : Confirmed Trusted Authority (Tier 1/2)   │
│ Score 50-84 : Qualified Secondary Source (Context only)│
│ Score < 50  : Speculative / Community Lead (Tier 3)    │
└────────────────────────────────────────────────────────┘
```

The evaluated domain is automatically recorded in `portable/Visa-Agent/knowledge/trusted_sources_catalog.json` with an audit date and verification trail.

---

## 4. Political & Macro-Economic Horizon Scanning

Immigration policy in Australia does not occur in a vacuum; it is heavily shaped by housing politics, federal election cycles, and Treasury economic forecasts. The Harvester actively monitors four macro signals:

1. **Net Overseas Migration (NOM) Caps & Federal Targets:**  
   Tracks federal government budget papers and Treasury announcements regarding nationwide permanent migration planning levels (e.g. 185,000 annual cap) and international student/temporary visa compression.
2. **Parliamentary Debates & Hansard Records:**  
   Monitors legislative debates in the Australian House of Representatives and Senate regarding proposed migration amendment bills before they receive Royal Assent.
3. **Electoral & Cross-Bench Sentiment:**  
   Tracks policy platform proposals from the Labor Party, Liberal-National Coalition, Greens, and key cross-benchers regarding regional migration incentives or point-test tightening.
4. **State-Level Budget Allocations:**  
   Tracks when state governments (Victoria, NSW, WA, Queensland) exhaust their interim Subclass 190/491 nomination allocations or lobby the federal government for emergency seat expansions.

---

## 5. Cognitive Synthesis: Distinguishing "Signal" from "Noise"

The Harvester processes every piece of political and immigration news through an **Impact Probability Matrix**:

| News / Event Type | Nature of Article | Regulatory Weight | Strategic Action for Client |
|---|---|---|---|
| **Enacted Law / Ministerial Direction** | Migration Amendment Regulations signed by Minister; effective immediately. | **100% Impact** | Immediate update to client points, checklists, and submission timelines. |
| **Tabled Parliamentary Bill** | Formal bill introduced to Parliament with cross-party backing. | **High Probability (70–85%)** | Pre-emptive action: lodge EOIs/visas before the bill's gazetted start date. |
| **Senate Inquiry / Think-Tank Report** | Parliamentary committee findings (e.g. Joint Standing Committee on Migration) or Grattan Institute proposals. | **Medium Probability (40–60%)** | Tracked as a forward indicator for 1–2 year outlooks; no panic changes. |
| **Political Rhetoric / Campaign Speech** | Politicians debating migration numbers in the media without draft legislation. | **Noise / Speculative (<20%)** | Filtered into a separate "Political Commentary" appendix; explicitly marked so clients do not panic. |

---

## 6. Self-Managed Knowledge Bank Structure

The Harvester autonomously maintains its dedicated knowledge repository under `portable/Visa-Agent/knowledge/` (strictly separated from private candidate files in `.profile/`):

```
portable/Visa-Agent/knowledge/
├── digests/
│   ├── daily_YYYY-MM-DD.md             <-- Daily news, statutory, and political briefs
│   └── weekly_YYYY-WXX.md              <-- Weekly executive intelligence roundups
├── political_radar/
│   ├── federal_parliament_tracker.md   <-- Active bills, debate summaries, NOM quotas
│   └── state_treasury_signals.md       <-- State-by-state political sentiment & allocations
├── live_cutoffs/
│   ├── gsm_skillselect_rounds.md       <-- Subclass 189, 190, 491 points cutoffs by code
│   └── occupation_ceilings_2026.md     <-- Quota usage for Software & Systems Engineers
├── trusted_sources_catalog.json        <-- Dynamic registry of vetted and rated domains
└── alerts/
    └── breaking_policy_changes.md      <-- Urgent ministerial directions & fee adjustments
```

---

## 7. Sample Enhanced Daily Digest Layout

Every generated digest integrates statutory updates, political signals, and client-specific consequences:

```markdown
# Australia Migration Daily Digest — 10 Nov 2026

### 1. Macro Political & Legislative Radar (Signals & Debates)
* **Parliamentary Debate on Migration Planning Levels (Hansard Review):**
  - The Minister for Immigration confirmed in Senate Estimates that the 2026–27 permanent migration ceiling will maintain a 70% allocation for the Skill Stream.
  - *Political Context:* Ongoing housing pressure has triggered calls for tighter temporary student visa caps, but the skilled PR intake for enterprise engineering occupations remains legally protected.
  - *Legislative Status:* Confirmed Federal Budget Target (Tier 1 Ground Truth).

### 2. State Nomination & Allocation News
* **Victoria (Live in Melbourne) Selection Behavior:**
  - Fast-tracked processing announced for offshore tech candidates who declare family connections in Victoria.
  - *Direct Source:* [Live in Melbourne Policy Notice](https://liveinmelbourne.vic.gov.au/...)

### 3. Community Intelligence & Real Cutoffs (Tier 3 - Verified)
* **Reddit r/AusVisa & Whirlpool Observations:**
  - Subclass 190 invitations for Developer Programmers (261312) and Systems Engineers (263111) reported at 85 points.
  - Multiple reports confirm that dual-income couples claiming +10 partner points received priority queue positioning in Victoria.

### 4. Strategic Impact on Ashish & Khushboo File
* **Verdict:** Bullish. Current political focus is restricting low-skill temporary visas while aggressively recruiting high-earning, dual-tech PR candidates. Your 85/90 point score and Melbourne family tie place you in the optimal demographic favored by current federal and state policies.
```

---

## 8. Integration with Other Visa Agents

* **Master Migration Coordinator:** Ingests `knowledge/political_radar/` to evaluate long-term visa viability and advise clients on legislative timing.
* **PR / GSM Specialist:** Consumes `knowledge/live_cutoffs/` to recalibrate minimum points thresholds across Subclasses 189 and 190.
* **Visitor Visa Specialist:** Queries the Harvester for heightened GTE (Genuine Temporary Entrant) scrutiny alerts driven by political crackdowns on temporary entrants.
* **ACS Evidence Auditor:** Ingests updated assessing body circulars to ensure technical job duties match evolving ANZSCO classifications.
