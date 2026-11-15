# ACS Authority Poller

Production-ready scraper for the Australian Computer Society (ACS) MSA Info Hub, extracting occupation assessments, fees, processing times, and recent updates.

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Usage

```python
from runtime.scrapers import ACSPoller

# Initialize poller
poller = ACSPoller()

# Run complete polling cycle
result = poller.poll_all()

# Or run individual scrapers
occupations = poller.scrape_occupation_list()
fees = poller.scrape_fees()
times = poller.scrape_processing_times()
updates = poller.scrape_recent_updates()
```

### Command Line

```bash
# Run complete polling cycle
python -m runtime.scrapers.acs_poller --all

# Or run specific components
python -m runtime.scrapers.acs_poller --occupations
python -m runtime.scrapers.acs_poller --fees
python -m runtime.scrapers.acs_poller --times
python -m runtime.scrapers.acs_poller --updates
```

## Output Files

The poller creates/updates three files in `knowledge/live_cutoffs/`:

### 1. `acs_assessments.json` (Current Data)
Latest snapshot of ACS assessment data with complete metadata.

```json
{
  "meta": {
    "source": "https://www.acs.org.au/msa/infohub.html",
    "scrape_timestamp": "2026-11-15T03:45:00Z",
    "scrape_status": "success|partial|failed",
    "last_updated_acs": "2026-11-10T00:00:00Z",
    "next_scrape": "2026-11-22T03:00:00Z"
  },
  "fee_schedule": {
    "bachelor_degree": 600,
    "masters_degree": 550,
    "postgraduate_diploma": 650,
    "currency": "AUD",
    "effective_date": "2026-11-01",
    "notes": "Fees subject to change; verify with ACS"
  },
  "processing_times": {
    "competency_demonstration_report_weeks": 6,
    "rpl_weeks": 4,
    "overseas_assessment_weeks": 8,
    "notes": "Estimates only; subject to backlog"
  },
  "occupations": [
    {
      "occupation_code": "261313",
      "occupation_title": "Software Engineer",
      "skill_level_requirement": "ICT20",
      "assessment_types": ["CDR", "RPL"],
      "assessment_criteria_url": "https://www.acs.org.au/..."
    }
  ],
  "recent_updates": [
    {
      "date": "2026-11-10",
      "update": "Processing time for CDR increased to 6 weeks",
      "impact": "high"
    }
  ]
}
```

### 2. `acs_history.jsonl` (Historical Data)
Line-delimited JSON file with weekly snapshots for trend analysis.

```jsonl
{"timestamp": "2026-11-08T03:00:00Z", "occupation_count": 31, "status": "success", "fees": {...}, "processing_times": {...}}
{"timestamp": "2026-11-15T03:00:00Z", "occupation_count": 31, "status": "success", "fees": {...}, "processing_times": {...}}
```

### 3. `acs_scraper_errors.jsonl` (Error Log)
Records all scraping errors with context for debugging.

```jsonl
{"timestamp": "2026-11-15T03:45:00Z", "operation": "fetch_page", "error": "Connection timeout", "context": {"url": "https://www.acs.org.au/msa/infohub.html"}}
```

## Scheduling

The poller is designed to run weekly on Fridays at 0300 UTC:

```cron
0 3 * * 5 /path/to/acs_poller.py --all
```

**Why Friday 0300 UTC?**
- Weekly frequency matches ACS update cadence (occupation list, fees change infrequently)
- Fees reviewed annually (typically February)
- Processing times updated quarterly
- Friday afternoon in Western Australia = early-week data in Eastern Australia

**Expected Runtime:** 1-2 minutes per full cycle

## Key Features

### Resilience
- **Retry Logic**: 3 attempts with exponential backoff (1.5s, 2.25s, 3.375s)
- **Fallback Strategies**: CSS selectors → XPath → regex patterns
- **Error Handling**: Graceful degradation; missing data doesn't halt execution
- **Timeout**: 30 seconds per request

### Data Validation
- **Occupation Codes**: Must be 6-digit ANZSCO format
- **Fees**: Numeric, AUD currency, $400-$800 range
- **Processing Times**: 1-12 weeks range
- **Dates**: Normalized to YYYY-MM-DD format

### Dual-Tier Parsing
1. **Primary**: Structured data (CSS selectors on tables/divs)
2. **Secondary**: Unstructured text (regex patterns)

### Status Reporting
Scrape status determined by data completeness:
- **success**: All major data types scraped (occupations, fees, times)
- **partial**: Some data types missing but not critical failures
- **failed**: Unable to extract any meaningful data

## Integration Points

### For Operators
```python
# Load current ACS data
import json

with open("knowledge/live_cutoffs/acs_assessments.json") as f:
    acs_data = json.load(f)

# Get fees for applicant
bachelor_fee = acs_data["fee_schedule"]["bachelor_degree"]  # $600
masters_fee = acs_data["fee_schedule"]["masters_degree"]    # $550

# Get processing time for CDR
cdr_weeks = acs_data["processing_times"]["competency_demonstration_report_weeks"]  # 6

# Find occupation assessment path
occupation = next(
    (occ for occ in acs_data["occupations"] 
     if occ["occupation_code"] == "261313"),
    None
)
assessment_types = occupation["assessment_types"]  # ["CDR", "RPL"]
```

### For Trend Analysis
```python
# Load history for trend analysis
import json

assessments = []
with open("knowledge/live_cutoffs/acs_history.jsonl") as f:
    for line in f:
        assessments.append(json.loads(line))

# Analyze fee changes
recent_fee = assessments[-1]["fees"]["bachelor_degree"]
older_fee = assessments[-12]["fees"]["bachelor_degree"]  # 12 weeks ago
fee_change = recent_fee - older_fee
```

## Important Disclaimers

### Processing Times ⚠️
- **Estimates only**, not guarantees
- Vary based on backlog, complexity, documentation
- ACS may increase times during high-volume periods
- **Always verify current times with ACS when advising applicants**

### Fees ⚠️
- Subject to annual review (typically February)
- Transition periods may apply
- Some applicant categories have different fees
- **Always cross-check with official ACS rate card before quoting**

### Occupation List ⚠️
- Occupations added/removed based on demand and policy
- Skill Level Requirements can change mid-year
- Assessment pathways evolve
- **Always link operators to official ACS occupation list**

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
python3 -m unittest tests.test_acs_poller -v

# Run specific test class
python3 -m unittest tests.test_acs_poller.TestACSPollerFees -v

# Run specific test
python3 -m unittest tests.test_acs_poller.TestACSPollerFees.test_scrape_fees_success -v
```

### Test Coverage
- ✓ Occupation list parsing
- ✓ Fee schedule extraction
- ✓ Processing time parsing
- ✓ Recent updates scraping
- ✓ Error handling and retries
- ✓ Date normalization
- ✓ JSON schema validation
- ✓ Graceful degradation on parse errors

### Manual Validation
After running the scraper, verify:

1. **Fees match current ACS rate card**
   - Check: https://www.acs.org.au/fees

2. **Processing times are current**
   - Check: https://www.acs.org.au/msa/infohub.html

3. **Occupation list is complete**
   - Check: https://www.acs.org.au/occupations
   - Sample check: Verify 5-10 random occupation codes

4. **Recent updates are reflected**
   - Check news section: https://www.acs.org.au/news

## Architecture

### Class: `ACSPoller`

**Methods:**
- `fetch_page(url)` → HTML content (with retries)
- `scrape_occupation_list()` → occupation dict
- `scrape_fees()` → fee schedule dict
- `scrape_processing_times()` → processing times dict
- `scrape_recent_updates()` → list of updates
- `poll_all()` → runs all scrapers, saves output

**Private Methods:**
- `_parse_occupation_section()`
- `_extract_assessment_types()`
- `_extract_skill_level()`
- `_parse_update_section()`
- `_extract_numeric_value()`
- `_normalize_date()`
- `_parse_date()`
- `_determine_scrape_status()`
- `_log_error()`

### Error Handling
All exceptions are caught and logged; no failures propagate to caller.

Errors logged to `acs_scraper_errors.jsonl` with:
- Timestamp
- Operation name
- Error message
- Context (URL, failed field, etc.)

## Files

- **Implementation**: `/runtime/scrapers/acs_poller.py`
- **Agent Docs**: `.agents/agent_acs_authority_poller.md`
- **Tests**: `tests/test_acs_poller.py`
- **Current Data**: `knowledge/live_cutoffs/acs_assessments.json`
- **History**: `knowledge/live_cutoffs/acs_history.jsonl`
- **Error Log**: `knowledge/live_cutoffs/acs_scraper_errors.jsonl`
- **Dependencies**: `requirements.txt`

## Troubleshooting

### No data scraped
- Check network connectivity
- Verify ACS website is accessible: https://www.acs.org.au/msa/infohub.html
- Check error log: `knowledge/live_cutoffs/acs_scraper_errors.jsonl`

### Partial data (some sections missing)
- This is expected; scraper has graceful fallback
- Default fees and times used if not found
- Review error log for which sections failed

### Fees don't match official ACS
- Fees are captured from published page; may lag official updates
- Always verify with: https://www.acs.org.au/fees
- Consider running scraper more frequently if frequent changes

### Processing times seem wrong
- ACS updates these quarterly or during backlog changes
- Times are estimates; verify with official guidance
- Check recent updates for backlog notices

## References

- **ACS MSA Info Hub**: https://www.acs.org.au/msa/infohub.html
- **Occupation List**: https://www.acs.org.au/occupations
- **Assessment Paths**: https://www.acs.org.au/assessment
- **Fee Schedule**: https://www.acs.org.au/fees
- **Agent Documentation**: `.agents/agent_acs_authority_poller.md`
