---
agent_id: state-nomination-monitor
version: 1.0.0
status: draft
phase: 3b
role: Daily monitor for all 8 Australian state and territory nomination programs
entry_point: scrape_state_quotas
---

# State Nomination Monitor Agent

## Purpose
Provides daily monitoring of all 8 Australian state and territory nomination quotas, available occupations, and visa type requirements. Enables real-time tracking of nomination capacity changes across all jurisdictions.

## Monitored States
1. **Victoria (VIC)** → https://immi.vic.gov.au/
2. **NSW (NSW)** → https://www.nsw.gov.au/business-and-economy/skilled-migration
3. **Western Australia (WA)** → https://www.wa.gov.au/government/migration
4. **Queensland (QLD)** → https://www.findazjob.qld.gov.au/nominationskill
5. **South Australia (SA)** → https://migration.sa.gov.au/
6. **Tasmania (TAS)** → https://www.tas.gov.au/
7. **Northern Territory (NT)** → https://migration.nt.gov.au/
8. **ACT (ACT)** → https://www.act.gov.au/

## Data Sources
- **State Portals**: 8 official state/territory migration websites (listed above)
- **Data Files**: 
  - Current snapshots: `knowledge/live_cutoffs/state_*.json` (one per state)
  - Append-only history: `knowledge/live_cutoffs/state_history.jsonl`
  - Error log: `knowledge/live_cutoffs/state_scraper_errors.jsonl`
- **Update Frequency**: Daily at 0300 UTC (parallel with DHA scraper)
- **Expected Runtime**: 3-5 minutes (4 concurrent scrapers, 8 states total)

## Key Concepts

### Visa Types Monitored
- **190 (Skilled Nominated)**: Permanent, state-sponsored occupation lists
- **491 (Skilled Work Regional)**: Temporary, regional occupation lists (4-year visa)

### State Nomination Process
Each state maintains:
1. **Available occupation list**: ANZSCO codes that accept nominations
2. **Nomination quota**: Remaining spots for current financial year
3. **Processing times**: Weeks from application to decision
4. **Regional requirements**: Commitment periods, location restrictions

### Occupations Tracked per State
Each occupation record includes:
- ANZSCO occupation code (5 digits)
- Occupation title
- Eligible visa types (190, 491, or both)
- Availability status (open/closed)
- Estimated processing time in weeks (if available)

## Core Functions

### 1. Scrape Single State
**Input**: `state_code` (VIC, NSW, WA, QLD, SA, TAS, NT, ACT)
**Output**: JSON with occupations, quotas, metadata

```python
from runtime.scrapers import StateMonitor

monitor = StateMonitor()
result = monitor.scrape_state("VIC")

# Returns:
{
  "meta": {
    "state_code": "VIC",
    "state_name": "Victoria",
    "source": "https://immi.vic.gov.au/",
    "scrape_timestamp": "2026-11-15T03:30:00Z",
    "scrape_status": "success",  # success|partial|failed
    "occupation_count": 45
  },
  "occupations": [
    {
      "occupation_code": "261313",
      "occupation_title": "Software Engineer",
      "visa_type": ["190", "491"],
      "available": true,
      "processing_time_weeks": 8
    }
  ],
  "quotas": {
    "visa_190_available": 250,
    "visa_491_available": 100,
    "notes": "Updated 2026-11-15"
  }
}
```

### 2. Scrape All States in Parallel
**Input**: None (scrapes all 8 states)
**Output**: Dictionary of results + individual JSON files

```python
from runtime.scrapers import StateMonitor

monitor = StateMonitor(max_workers=4)  # 4 concurrent scrapers
results = monitor.scrape_all()

# Outputs:
# - knowledge/live_cutoffs/state_vic.json
# - knowledge/live_cutoffs/state_nsw.json
# - ... (6 more states)
# - knowledge/live_cutoffs/state_history.jsonl (append-only)
# - knowledge/live_cutoffs/state_scraper_errors.jsonl (error log)
```

### 3. Query Recent History
**Input**: Optional state code
**Output**: 12-month trend per state

```python
def analyze_occupation_trend(occupation_code, state_code):
    """
    Load knowledge/live_cutoffs/state_history.jsonl
    Filter by state_code + timestamp
    Calculate:
      - 30-day trend: occupation_count change
      - 90-day trend: availability changes
      - Anomalies: sudden quota drops
    Return: {trend, velocity, anomalies}
    """
    import json
    from datetime import datetime, timedelta
    
    records = []
    with open("knowledge/live_cutoffs/state_history.jsonl") as f:
        for line in f:
            record = json.loads(line)
            if record["state_code"] == state_code:
                records.append(record)
    
    # Calculate trends...
```

## CLI Usage

### Scrape Single State
```bash
python -m runtime.scrapers.state_monitor --state VIC
python -m runtime.scrapers.state_monitor --state NSW
# ... etc for all 8 states
```

### Scrape All 8 States (Parallel)
```bash
python -m runtime.scrapers.state_monitor --all
```

### Specify Output Directory
```bash
python -m runtime.scrapers.state_monitor --all --output-dir /custom/path
```

## Scraper Implementation Details

### Resilience Strategy
1. **HTTP Retry Logic**: 3 attempts with exponential backoff (2s, 4s)
2. **Timeout Handling**: 30-second request timeout
3. **Error Logging**: All failures appended to `state_scraper_errors.jsonl`
4. **Fallback**: Use most recent successful JSON if scrape fails

### Parallel Execution
- **Framework**: `concurrent.futures.ThreadPoolExecutor`
- **Max Concurrent**: 4 workers (configurable)
- **Coordination**: Futures collected, individual results saved to JSON
- **Atomicity**: Each state JSON written independently (no partial writes)

### CSS Selector Fallbacks
Each state portal may require different selector strategies:
- **Table-based**: CSS `table > tr > td` selectors
- **Div-based**: Nested `div.occupation-list > div.item` patterns
- **List-based**: `li.occupation` or `ul > li` patterns
- **XPath fallback**: `//*[@class="occupation-list"]/descendant::*` for resilience

### Error Handling
- **Network errors**: Log and retry with backoff
- **Parse errors**: Log context, save partial results, continue
- **Timeout**: Move to next state, log for manual review
- **Invalid HTML**: Flag as "partial" status, save what was extracted

## Output Schema Per State

### File: `knowledge/live_cutoffs/state_<code>.json`
```json
{
  "meta": {
    "state_code": "VIC",
    "state_name": "Victoria",
    "source": "https://immi.vic.gov.au/",
    "scrape_timestamp": "2026-11-15T03:30:00Z",
    "scrape_status": "success",
    "occupation_count": 45
  },
  "occupations": [
    {
      "occupation_code": "261313",
      "occupation_title": "Software Engineer",
      "visa_type": ["190", "491"],
      "available": true,
      "processing_time_weeks": 8
    }
  ],
  "quotas": {
    "visa_190_available": 250,
    "visa_491_available": 100,
    "notes": "Updated 2026-11-15"
  }
}
```

### File: `knowledge/live_cutoffs/state_history.jsonl`
Append-only line-delimited JSON:
```jsonl
{"timestamp": "2026-11-15T03:30:00Z", "state_code": "VIC", "occupation_count": 45, "scrape_status": "success"}
{"timestamp": "2026-11-15T03:35:00Z", "state_code": "NSW", "occupation_count": 52, "scrape_status": "success"}
...
```

### File: `knowledge/live_cutoffs/state_scraper_errors.jsonl`
Append-only error log:
```jsonl
{"timestamp": "2026-11-15T02:00:00Z", "state_code": "WA", "error": "Connection timeout", "context": "scrape_wa"}
...
```

## Scheduling

### Cron Expression
```bash
0 3 * * * /usr/local/bin/python3 -m runtime.scrapers.state_monitor --all --output-dir /path/to/knowledge/live_cutoffs
```

### Execution Timing
- **Trigger**: Daily at 03:00 UTC (or operator's preferred time)
- **Parallel**: Runs concurrently with DHA SkillSelect scraper
- **Duration**: 3-5 minutes (4 concurrent scrapers × 8 states)
- **Dependencies**: None (standalone scraper, read-only output)

## Fallback Behavior

### If Scrape Fails
1. Check for most recent successful JSON file
2. Use stale data if available (flag with `scrape_status: "using_stale"`
3. Alert operator if stale data >7 days old
4. Log error with timestamp and context

### If Portal Requires JavaScript
1. Scraper detects JS-rendered content (checks for placeholder divs)
2. Flags as `scrape_status: "partial"` or `"failed"`
3. Suggests manual review or headless browser upgrade
4. Falls back to previous JSON snapshot

## State-Specific Notes

### Victoria (VIC)
- **Portal Structure**: Table-based occupation list on main portal
- **Update Frequency**: Typically weekly
- **Data Quirk**: Separate processing time pages per occupation

### NSW
- **Portal Structure**: Dedicated occupation list page
- **Update Frequency**: Bi-weekly
- **Data Quirk**: Includes regional variations (metro vs. regional)

### Western Australia (WA)
- **Portal Structure**: Accordion-style occupation categories
- **Update Frequency**: Monthly
- **Data Quirk**: May require JS rendering for full list expansion

### Queensland (QLD)
- **Portal Structure**: Searchable database (may require JS)
- **Update Frequency**: Quarterly reviews + ad-hoc changes
- **Data Quirk**: "Find a Job" portal doubles as visa occupation list

### South Australia (SA)
- **Portal Structure**: Simple text list + PDF documents
- **Update Frequency**: Quarterly
- **Data Quirk**: Maintains separate priority occupation lists

### Tasmania (TAS)
- **Portal Structure**: Minimal occupation list (small program)
- **Update Frequency**: Rarely updated
- **Data Quirk**: May have very limited or no nomination availability

### Northern Territory (NT)
- **Portal Structure**: Regional occupation list + relocation requirements
- **Update Frequency**: Quarterly
- **Data Quirk**: Emphasizes regional commitment periods (2+ years typical)

### ACT
- **Portal Structure**: Categories by eligibility + salary thresholds
- **Update Frequency**: Quarterly
- **Data Quirk**: Higher salary minimums for some occupations

## Limitations & Known Issues

1. **Portal Structure Changes**: State portals redesign periodically
   - Mitigation: Monitor HTTP 404 errors, maintain selector fallbacks
   
2. **JavaScript Rendering**: Some states use JS to load occupation lists
   - Mitigation: Use headless browser approach in future phases
   - Current: Fall back to stale data, flag for manual review
   
3. **Occupation Code Variations**: Not all states use ANZSCO exactly
   - Mitigation: Map variations to standard codes where possible
   - Store original codes in "raw_occupation_code" field
   
4. **Quota Data Inconsistency**: Quotas may not be explicitly published
   - Mitigation: Infer from nomination lists, store as estimates
   - Flag uncertain quotas with "estimated: true"

## Integration with Other Agents

### Used By
- **Migration Intelligence Harvester**: Consumes state data for daily digests
- **Points Calculator**: References available occupations per state
- **SkillSelect Tracker**: Compares state vs. 189 occupation lists

### Feeds Into
- **Client Roadmap Generator**: Considers state nomination chances
- **Visa Strategy Planner**: Evaluates 190/491 pathways by state
- **Cost Aggregator**: References state processing fees (future)

## Implementation Status
- **Phase 3b**: Core scraper module complete, 8 state methods, parallel execution
- **Phase 4**: JavaScript rendering for portal updates, real-time quota tracking
- **Phase 5**: Integration with ML anomaly detection, trend forecasting
