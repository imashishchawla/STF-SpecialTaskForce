---
agent_id: home-affairs-scraper
version: 1.0.0
status: production
phase: 1
role: Home Affairs public data harvester and parser
entry_point: scrape_visa_data
---

# Home Affairs Scraper Agent

## Purpose

Autonomously scrapes and parses publicly available Australian Department of Home Affairs visa data daily. Fetches current visa subclasses, skilled occupation lists, SkillSelect invitation rounds, and visa listings to feed the Visa Agent's knowledge base.

## Data Sources

Four public Home Affairs endpoints:

| Endpoint | URL | Data Extracted | Output File |
|----------|-----|-----------------|-------------|
| **Visa Finder** | `https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-finder` | All visa subclasses, types (work, family, skilled, temporary) | `visa_finder_YYYY-MM-DD.json` |
| **Skilled Occupation List** | `https://immi.homeaffairs.gov.au/visas/working-in-australia/skill-occupation-list` | ANZSCO codes, occupation titles, assessing authorities | `occupation_list_YYYY-MM-DD.json` |
| **SkillSelect Rounds** | `https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect/invitation-rounds` | Latest invitation dates, occupation codes, cutoff points (189/190/491) | `skillselect_latest_YYYY-MM-DD.json` |
| **Visa Listing** | `https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing` | Visa subclasses, open/closed status, conditions | `visa_listing_YYYY-MM-DD.json` |

**Output Directory**: `knowledge/raw_dha/`  
**Error Log**: `knowledge/raw_dha/scraper_errors.jsonl` (append-only)

## Technical Specification

### Module
- **Location**: `runtime/scrapers/dha_scraper.py`
- **Language**: Python 3.10+
- **Dependencies**: `requests`, `beautifulsoup4` (optional for enhanced parsing)
- **CLI**: `python3 runtime/scrapers/dha_scraper.py [--target ENDPOINT | --all] [--verbose]`

### Class: `DHAScraper()`

#### Methods

**`scrape_all() → Dict[str, Dict[str, Any]]`**
```python
scraper = DHAScraper()
results = scraper.scrape_all()
# Output: {
#   "visa_finder": {"status": "success", "path": "...", "rows": 152},
#   "occupation_list": {...},
#   "skillselect": {...},
#   "visa_listing": {...}
# }
```

**`scrape_visa_finder() → Dict[str, Any]`**
- Extracts all visa subclasses and types
- Returns: `{status, path, rows, timestamp, errors}`

**`scrape_occupation_list() → Dict[str, Any]`**
- Extracts ANZSCO codes, occupation titles, assessing authorities
- Returns: `{status, path, rows, timestamp, errors}`

**`scrape_skillselect_rounds() → Dict[str, Any]`**
- Extracts latest invitation round data and cutoff points
- Returns: `{status, path, rows, timestamp, errors}`

**`scrape_visa_listing() → Dict[str, Any]`**
- Extracts visa subclasses, status (open/closed), conditions
- Returns: `{status, path, rows, timestamp, errors}`

## Resilience Architecture

### Retry Logic (Exponential Backoff)
```
Attempt 1: Immediate
Attempt 2: Wait 1s
Attempt 3: Wait 2s
Attempt 4: Wait 4s
Max Retries: 3 (can fail after attempt 3)
```

### Fallback Strategy
1. **Attempt 1-3**: Fetch live data with retry + backoff
2. **Failure after 3 retries**: Check for stale data
3. **Stale data exists**: Use most recent snapshot with `status: "partial"`
4. **No stale data**: Return error with `status: "failed"`

### Error Handling Layers

| Layer | Handles | Action |
|-------|---------|--------|
| **Network** | Timeout, HTTPError, URLError | Retry with backoff; log attempt |
| **Parsing** | Malformed HTML, missing fields | Log error; save partial data or fallback |
| **Validation** | Missing required fields | Log validation error; mark `status: "partial"` |
| **Storage** | Disk write failures | Log error; alert operator |

### Header & Timeout
- **User-Agent**: `Visa-Agent-Scraper/1.0 (Australian visa intelligence)`
- **Request Timeout**: 30 seconds per endpoint
- **Identifies as**: Official Visa Agent scraper (transparent identification)

## Output Schema

### JSON Snapshot Structure
```json
{
  "meta": {
    "source": "https://immi.homeaffairs.gov.au/visas/...",
    "scrape_timestamp": "2026-11-15T03:15:00Z",
    "scrape_status": "success|partial|failed",
    "row_count": 152,
    "next_scrape": "2026-11-16T03:00:00Z"
  },
  "data": [
    // parsed structured data
  ],
  "errors": [
    // parsing errors or warnings
  ]
}
```

### Error Log Entry (JSONL)
```jsonl
{"timestamp": "2026-11-15T03:15:00Z", "endpoint": "visa_finder", "error_type": "fetch_error", "message": "Connection timeout"}
```

## Integration Points

### Phase 1 Pipeline
1. **Daily Schedule**: Cron job runs at 0300 UTC
2. **Output**: JSON snapshots feed into `Visa Agent` knowledge base
3. **SkillSelect Tracker**: `skillselect_latest_YYYY-MM-DD.json` updates occupation cutoff data
4. **Occupation Indexer**: `occupation_list_YYYY-MM-DD.json` updates ANZSCO reference
5. **Points Calculator**: Uses latest visa conditions and requirements

### Alert Integration
- 2+ consecutive failures for same endpoint → Alert operator
- Stale data older than 7 days → Warning log
- Parsing errors → Recorded in error log with timestamp

## Usage

### CLI Usage
```bash
# Scrape all 4 endpoints
python3 runtime/scrapers/dha_scraper.py --all

# Scrape single endpoint
python3 runtime/scrapers/dha_scraper.py --target visa_finder
python3 runtime/scrapers/dha_scraper.py --target occupation_list
python3 runtime/scrapers/dha_scraper.py --target skillselect
python3 runtime/scrapers/dha_scraper.py --target visa_listing

# Verbose logging
python3 runtime/scrapers/dha_scraper.py --all --verbose
```

### Programmatic Usage
```python
from runtime.scrapers import DHAScraper

scraper = DHAScraper(verbose=True)

# Scrape all
results = scraper.scrape_all()

# Scrape single endpoint
visa_finder_data = scraper.scrape_visa_finder()
occupation_data = scraper.scrape_occupation_list()
skillselect_data = scraper.scrape_skillselect_rounds()
visa_listing_data = scraper.scrape_visa_listing()
```

## Cron Schedule Configuration

### Production Daily Run
```cron
0 3 * * * /usr/bin/python3 /path/to/portable/Visa-Agent/runtime/scrapers/dha_scraper.py --all
```

**Timing**: 0300 UTC (chosen to align with Home Affairs data updates, typically around 1500 AEDT / 0400 UTC)
**Frequency**: Daily
**Expected Runtime**: 2-3 minutes (assuming typical network conditions)
**Timeout**: 5 minutes (allows for retries)
**Output**: JSON files to `knowledge/raw_dha/`; errors to `knowledge/raw_dha/scraper_errors.jsonl`

### Alternative: Run from Python
```python
import subprocess
import json

result = subprocess.run([
    "python3",
    "runtime/scrapers/dha_scraper.py",
    "--all",
    "--verbose"
], capture_output=True, text=True)

output = json.loads(result.stdout)
print(f"Scrape results: {output}")
```

## Error Scenarios & Resolution

### Scenario 1: Network Timeout (Transient)
```
Error: HTTPError 504 Gateway Timeout
Action: Retry with backoff (automatic)
Resolution: Usually succeeds on 2nd-3rd attempt
```

### Scenario 2: Home Affairs Site Maintenance
```
Error: HTTP 503 Service Unavailable / multiple consecutive timeouts
Action: After 3 retries, use stale data
Resolution: Data marked "partial"; logs alert; operator investigates
```

### Scenario 3: HTML Structure Changed
```
Error: Parse error (expected CSS selector not found)
Action: Fallback to XPath/alternative selectors
Resolution: Log partial data; alert operator for manual review
```

### Scenario 4: No Historical Data Available
```
Error: First scrape attempt fails and no stale data exists
Action: Return error; recommend manual fetch
Resolution: Operator manually downloads snapshot; stores in `knowledge/raw_dha/`
```

## Testing

### Test Suite
**Location**: `tests/test_dha_scraper.py`

**Coverage**:
- CSS selector + XPath fallback parsing
- Error handling (timeout, HTTP errors, malformed HTML)
- Retry logic with exponential backoff
- JSON output schema validation
- Stale data fallback behavior
- Edge cases (empty HTML, unicode content, missing fields)

**Run Tests**:
```bash
# All tests
python3 -m pytest tests/test_dha_scraper.py -v

# Specific test
python3 -m pytest tests/test_dha_scraper.py::TestDHAScraperFetch::test_retry_on_timeout -v

# With coverage
python3 -m pytest tests/test_dha_scraper.py --cov=runtime.scrapers.dha_scraper
```

### Mock Endpoints
All tests use mock HTTP responses (no real calls to Home Affairs during testing).

## Performance Characteristics

| Metric | Target | Notes |
|--------|--------|-------|
| **Single Endpoint** | <45s | Includes retries if needed |
| **All 4 Endpoints** | <3min | Sequential; can parallelize if needed |
| **Memory** | <50MB | Per scraper instance |
| **Disk** | <5MB | Per daily snapshot |

## Known Limitations

1. **HTML Parsing Fragility**: If Home Affairs changes HTML structure, CSS selectors may need updating
2. **No Official API**: Scrapes public HTML only; subject to website changes
3. **Rate Limiting**: No explicit rate limiting; Home Affairs may throttle frequent requests
4. **Occupations Limit**: Currently parses first 100 occupations to manage memory
5. **No Authentication**: Only accesses public, unauthenticated endpoints

## Maintenance & Updates

### Monthly Review Checklist
- [ ] Verify JSON output structure matches expected schema
- [ ] Check error log for parsing failures
- [ ] Confirm stale data is < 7 days old
- [ ] Inspect first 5 parsed records for accuracy
- [ ] Review CSS selectors against live Home Affairs site

### Update Triggers
- Home Affairs changes HTML structure → Update CSS/XPath selectors
- New visa types or occupation categories → Extend parsing logic
- Performance issues → Consider parallel scraping or caching
- API availability → Migrate to official API if released

## Related Resources

- **Official Home Affairs**: https://immi.homeaffairs.gov.au/
- **SkillSelect**: https://skillselect.gov.au/
- **ANZSCO Codes**: https://www.abs.gov.au/ausstats/abs@.nsf/mf/1220.0
- **Home Affairs Visa Listing**: https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing
- **Migration Harvester**: `.agents/agent_migration_intelligence_harvester.md` (higher-level source integration)

## Integration Checklist

- [ ] `runtime/scrapers/dha_scraper.py` exists and is executable
- [ ] `knowledge/raw_dha/` directory created
- [ ] `tests/test_dha_scraper.py` runs successfully
- [ ] Cron job configured and tested
- [ ] Error log setup verified
- [ ] Stale data fallback tested
- [ ] SkillSelect Tracker reads `skillselect_latest_*.json`
- [ ] Occupation Indexer reads `occupation_list_*.json`
- [ ] Documentation updated with cron schedule

---

**Last Updated**: 2026-11-15  
**Status**: Production-ready for Phase 1  
**Next Review**: 2026-12-15  
**Maintenance Owner**: Data Architecture Team
