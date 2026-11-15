# Home Affairs Data Scraper (DHAScraper)

Production-ready scraper for Australian Department of Home Affairs public visa data.

## Quick Start

### Installation

The scraper uses only Python standard library + optional BeautifulSoup4 for enhanced parsing.

```bash
# Core dependency (required)
python3 -m pip install --user requests

# Optional (for enhanced HTML parsing)
python3 -m pip install --user beautifulsoup4
```

### Basic Usage

```python
from runtime.scrapers import DHAScraper

# Initialize scraper
scraper = DHAScraper(verbose=True)

# Scrape all 4 endpoints
results = scraper.scrape_all()

# Or scrape specific endpoint
visa_finder = scraper.scrape_visa_finder()
occupations = scraper.scrape_occupation_list()
skillselect = scraper.scrape_skillselect_rounds()
visas = scraper.scrape_visa_listing()
```

### Command Line Usage

```bash
# Scrape all endpoints
python3 runtime/scrapers/dha_scraper.py --all

# Scrape single endpoint
python3 runtime/scrapers/dha_scraper.py --target visa_finder
python3 runtime/scrapers/dha_scraper.py --target occupation_list
python3 runtime/scrapers/dha_scraper.py --target skillselect
python3 runtime/scrapers/dha_scraper.py --target visa_listing

# Verbose logging
python3 runtime/scrapers/dha_scraper.py --all --verbose
```

## Endpoints

### 1. Visa Finder
```
URL: https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-finder
Extracts: All visa subclasses, visa types (work, family, skilled, temporary)
Output: knowledge/raw_dha/visa_finder_YYYY-MM-DD.json
```

### 2. Skilled Occupation List
```
URL: https://immi.homeaffairs.gov.au/visas/working-in-australia/skill-occupation-list
Extracts: ANZSCO codes, occupation titles, assessing authorities, visa codes
Output: knowledge/raw_dha/occupation_list_YYYY-MM-DD.json
```

### 3. SkillSelect Invitation Rounds
```
URL: https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect/invitation-rounds
Extracts: Latest round date, occupation codes, cutoff points (189/190/491 per state)
Output: knowledge/raw_dha/skillselect_latest_YYYY-MM-DD.json
```

### 4. Visa Listing
```
URL: https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing
Extracts: All visa subclasses, open/closed status, conditions
Output: knowledge/raw_dha/visa_listing_YYYY-MM-DD.json
```

## Resilience Features

### Retry Logic (Exponential Backoff)
- **Max Retries**: 3
- **Delays**: 1s, 2s, 4s
- **Total Time**: ~7s per endpoint
- **Timeout**: 30s per request

### Fallback Strategy
1. Try live fetch (3 retries)
2. If all fail, check for stale data
3. Use most recent local snapshot
4. Mark as `status: "partial"` with warning

### Error Handling
- Network errors → Automatic retry with backoff
- Parse errors → Log and continue
- Storage errors → Alert and report
- Stale data fallback → Transparent degradation

## Output Schema

All JSON files follow this structure:

```json
{
  "meta": {
    "source": "https://immi.homeaffairs.gov.au/...",
    "scrape_timestamp": "2026-11-15T03:15:00Z",
    "scrape_status": "success|partial|failed",
    "row_count": 152,
    "next_scrape": "2026-11-16T03:00:00Z"
  },
  "data": [
    // Parsed content here
  ],
  "errors": [
    // Any parsing errors
  ]
}
```

## Error Logging

All errors logged to `knowledge/raw_dha/scraper_errors.jsonl` (append-only):

```jsonl
{"timestamp": "2026-11-15T03:15:00Z", "endpoint": "visa_finder", "error_type": "fetch_error", "message": "Connection timeout"}
```

## Testing

Run test suite:
```bash
# All tests
python3 -m unittest tests.test_dha_scraper -v

# Specific test class
python3 -m unittest tests.test_dha_scraper.TestDHAScraperFetch -v

# Specific test
python3 -m unittest tests.test_dha_scraper.TestDHAScraperFetch.test_retry_on_timeout -v
```

All tests use mock endpoints (no real calls to Home Affairs).

## Cron Schedule

Run daily at 0300 UTC:

```bash
# In crontab:
0 3 * * * /usr/bin/python3 /path/to/portable/Visa-Agent/runtime/scrapers/dha_scraper.py --all
```

Or using Python:
```python
import subprocess
import json
from datetime import datetime, timezone

result = subprocess.run(
    ["python3", "runtime/scrapers/dha_scraper.py", "--all"],
    capture_output=True,
    text=True,
    timeout=300
)

output = json.loads(result.stdout)
timestamp = datetime.now(timezone.utc).isoformat()
print(f"[{timestamp}] Scrape completed: {output}")
```

## Performance

| Metric | Typical |
|--------|---------|
| Single endpoint | <45s |
| All 4 endpoints | <3min |
| Memory usage | <50MB |
| Disk per day | <5MB |

## Dependencies

### Required
- `requests` - HTTP client
- `Python 3.10+`

### Optional
- `beautifulsoup4` - Enhanced HTML parsing (falls back to built-in parser if unavailable)

### Standard Library
- `urllib` - HTTP requests (fallback)
- `html.parser` - HTML parsing (fallback)
- `json` - JSON handling
- `logging` - Error logging

## Implementation Details

### Parsing Approach
1. **Primary**: CSS selectors (BeautifulSoup4 if available)
2. **Fallback**: XPath-like queries with built-in parser
3. **Graceful**: Returns partial data if parsing fails

### Error Recovery
- **Network**: Automatic retry with exponential backoff
- **Parse**: Log error, continue with partial results
- **Storage**: Fail loudly, alert operator
- **Data Loss**: Never - stale data always available as fallback

## File Structure

```
runtime/
├── scrapers/
│   ├── __init__.py              # Package init
│   ├── dha_scraper.py           # Main scraper module
│   └── README.md                # This file

knowledge/
├── raw_dha/
│   ├── visa_finder_YYYY-MM-DD.json
│   ├── occupation_list_YYYY-MM-DD.json
│   ├── skillselect_latest_YYYY-MM-DD.json
│   ├── visa_listing_YYYY-MM-DD.json
│   └── scraper_errors.jsonl     # Error log

tests/
└── test_dha_scraper.py          # Test suite
```

## Known Limitations

1. **HTML Fragility**: Parses public HTML; changes break selectors
2. **No Official API**: Only public web scraping
3. **Rate Limiting**: No explicit protection; Home Affairs may throttle
4. **Occupations Cap**: First 100 occupations per endpoint
5. **Network Dependent**: Requires stable internet connection

## Troubleshooting

### "BeautifulSoup4 not installed"
This is a warning, not an error. Scraper works fine with built-in parser.

### "All retries exhausted"
Check network connection. Use `--verbose` to see detailed error messages.

### "No stale data available"
First-time scrape failed. Check Home Affairs is accessible; retry manually.

### Parsing returns empty results
HTML structure may have changed. Inspect Home Affairs site; update selectors.

## Maintenance

### Monthly Checklist
- [ ] Verify JSON structure matches expected schema
- [ ] Spot-check parsed data accuracy
- [ ] Review error log for patterns
- [ ] Confirm stale data < 7 days old

### When to Update
- Home Affairs HTML changes → Update CSS selectors
- New visa categories → Extend parsing logic
- Performance issues → Consider parallelization

## Related Documentation

- `.agents/agent_home_affairs_scraper.md` - Full agent specification
- `MASTER_WORKFLOW_PROMPT.md` - Integration context
- `knowledge/raw_dha/scraper_errors.jsonl` - Error history

---

# State Nomination Monitor (StateMonitor)

Production-ready scraper for monitoring all 8 Australian state and territory nomination programs.

## Quick Start

### Scrape a Single State

```python
from runtime.scrapers.state_monitor import StateMonitor

monitor = StateMonitor()
result = monitor.scrape_state('VIC')  # Victoria

print(f"Status: {result['meta']['scrape_status']}")
print(f"Occupations: {result['meta']['occupation_count']}")
print(f"Quotas: {result['quotas']}")
```

### Scrape All 8 States in Parallel

```python
monitor = StateMonitor(max_workers=4)
results = monitor.scrape_all()

for state_code, data in results.items():
    print(f"{state_code}: {data['meta']['scrape_status']}")
```

### Output Files

After scraping, files are saved to `knowledge/live_cutoffs/`:

- `state_vic.json`, `state_nsw.json`, ... (one per state)
- `state_history.jsonl` (append-only history)
- `state_scraper_errors.jsonl` (error log)

## States Monitored

| Code | State | URL |
|------|-------|-----|
| VIC | Victoria | https://immi.vic.gov.au/ |
| NSW | New South Wales | https://www.nsw.gov.au/business-and-economy/skilled-migration |
| WA | Western Australia | https://www.wa.gov.au/government/migration |
| QLD | Queensland | https://www.findazjob.qld.gov.au/nominationskill |
| SA | South Australia | https://migration.sa.gov.au/ |
| TAS | Tasmania | https://www.tas.gov.au/ |
| NT | Northern Territory | https://migration.nt.gov.au/ |
| ACT | Australian Capital Territory | https://www.act.gov.au/ |

## CLI Usage

### Scrape single state
```bash
python -m runtime.scrapers.state_monitor --state VIC
python -m runtime.scrapers.state_monitor --state NSW
# ... etc for all 8 states
```

### Scrape all states in parallel
```bash
python -m runtime.scrapers.state_monitor --all
```

### Custom output directory
```bash
python -m runtime.scrapers.state_monitor --all --output-dir /custom/path
```

## Output Schema

Each state JSON contains:

```json
{
  "meta": {
    "state_code": "VIC",
    "state_name": "Victoria",
    "source": "https://immi.vic.gov.au/",
    "scrape_timestamp": "2026-11-15T03:30:00Z",
    "scrape_status": "success|partial|failed",
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

## Configuration

### Timeout & Retries

```python
monitor = StateMonitor(
    output_dir="path/to/knowledge/live_cutoffs",
    max_retries=3,           # Retry failed requests 3 times
    timeout=30,              # 30-second request timeout
    max_workers=4            # 4 concurrent scraper threads
)
```

### Parallel Execution

- Uses `concurrent.futures.ThreadPoolExecutor`
- Default: 4 concurrent workers (configurable)
- All 8 states scraped together, typical runtime: 3-5 minutes

## Error Handling

### Retry Logic
1. Exponential backoff: 2s, 4s, 8s after each failed attempt
2. Max 3 retries per request (configurable)
3. Timeout: 30 seconds per request

### Fallback Strategy
1. If scrape fails: Status marked as "failed"
2. Occupations list: Empty array
3. Quotas: Empty object
4. Error logged to `state_scraper_errors.jsonl`
5. History entry created with failure timestamp

## Testing

Run all tests:
```bash
python -m unittest tests.test_state_monitor -v
```

Test counts: 36 tests covering:
- Initialization and configuration
- Output schema validation (all 8 states)
- Parallel execution
- Error handling and retry logic
- File I/O and history management
- Data structure validation

## Scheduled Execution
```bash
# Daily at 0300 UTC
0 3 * * * /usr/local/bin/python3 -m runtime.scrapers.state_monitor --all
```

## Performance

| Metric | Typical |
|--------|---------|
| Single state | <15s (including retries) |
| All 8 states (parallel) | 3-5 minutes |
| Memory usage | <50MB |
| Disk per day | <2MB |

## Limitations & Known Issues

1. **Portal Structure**: Each state has different page structure
   - CSS selectors may need updates when portals redesign
   - Solution: Maintain selector fallbacks, monitor HTTP errors

2. **JavaScript Rendering**: Some states may use JS-rendered content
   - Current: Fallback to stale data
   - Future: Add headless browser support

3. **Data Format Variations**: Not all states use ANZSCO exactly
   - Stored as-is in `occupation_code` field
   - Mapping layer for normalization in future

4. **Quota Estimates**: Not all states publish explicit quotas
   - May be inferred from available occupation counts
   - Flagged as "estimated: true" when uncertain

## Future Enhancements

- Phase 4: Headless browser support for JS-rendered content
- Phase 4: Real-time quota tracking with webhooks
- Phase 5: ML-based anomaly detection for sudden changes
- Phase 5: Trend forecasting for occupation demand

## File Structure

```
runtime/scrapers/
├── __init__.py              # Package init
├── state_monitor.py         # StateMonitor class (this file)
└── README.md                # This file

knowledge/live_cutoffs/
├── state_vic.json
├── state_nsw.json
├── ... (6 more states)
├── state_history.jsonl      # Append-only history
└── state_scraper_errors.jsonl # Error log

tests/
└── test_state_monitor.py    # Test suite (36 tests)
```
