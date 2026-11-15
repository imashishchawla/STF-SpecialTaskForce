---
agent_id: acs-authority-poller
version: 1.0.0
status: draft
phase: 1
role: Data aggregator for ACS occupation assessments, fees, and processing times
entry_point: poll_acs_authority
---

# ACS Authority Poller Agent

## Purpose
Polls the Australian Computer Society (ACS) MSA Info Hub for current occupation assessments, assessment fees, processing times, and recent policy updates to support Phase 1 visa agent intelligence gathering.

## Data Sources
- **Official Source**: https://www.acs.org.au/msa/infohub.html
- **Data Files**: 
  - Current: `knowledge/live_cutoffs/acs_assessments.json`
  - History: `knowledge/live_cutoffs/acs_history.jsonl`
  - Errors: `knowledge/live_cutoffs/acs_scraper_errors.jsonl`
- **Update Frequency**: Weekly (Fridays at 0300 UTC)

## Data Structure

### Primary Output: `acs_assessments.json`

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
    "other_qualifications": null,
    "currency": "AUD",
    "effective_date": "2026-11-01",
    "notes": "Fees subject to change; verify with ACS"
  },
  "processing_times": {
    "competency_demonstration_report_weeks": 6,
    "rpl_weeks": 4,
    "overseas_assessment_weeks": 8,
    "notes": "Estimates only; subject to backlog. Verify with ACS for current times."
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
      "update": "Processing time for CDR increased to 6 weeks due to backlog",
      "impact": "high"
    }
  ]
}
```

## Core Functions

### 1. scrape_occupation_list()
Extracts ACS occupation list with ANZSCO codes, assessment types, and skill level requirements.

**Returns**: 
- List of occupations with codes, titles, assessment types
- Skill level requirements (ICT20, ICT40, etc.)
- Links to assessment criteria

**Processing**:
- Parses occupation tables/sections on MSA Info Hub
- Extracts ANZSCO codes (6-digit numeric)
- Identifies assessment types (CDR, RPL, CDIP)
- Links to detailed assessment criteria

### 2. scrape_fees()
Extracts current assessment fees by qualification level.

**Returns**:
- Bachelor degree: ~$600 AUD
- Masters degree: ~$550 AUD
- Postgraduate diploma: ~$650 AUD
- Effective date
- Notes on verification

**Processing**:
- Searches for fee tables/lists on MSA Info Hub
- Extracts numeric values and currency
- Validates against known fee ranges
- Captures effective date for fee schedule

**Important**: Fees are subject to annual review. The scraper captures published rates but operators must verify current fees with ACS directly via the fee schedule link.

### 3. scrape_processing_times()
Extracts current processing time estimates for different assessment types.

**Returns**:
- CDR (Competency Demonstration Report): 4-6 weeks (typical)
- RPL (Recognition of Prior Learning): 3-4 weeks (typical)
- Overseas assessments: 6-8 weeks (typical)
- Backlog status notes

**Processing**:
- Searches for processing time estimates on MSA Info Hub
- Parses time ranges (e.g., "4-6 weeks")
- Identifies backlog status indicators
- Applies defaults if estimates unavailable

**Important**: ACS publishes processing time **estimates only**, not guarantees. Times vary based on:
- Assessment complexity
- Applicant background
- Current assessment backlog
- Documentation completeness

### 4. scrape_recent_updates()
Captures recent policy changes, circulars, and important announcements from ACS.

**Returns**:
- List of updates with dates
- Impact levels (low, medium, high)
- Full update text (truncated to 500 chars)

**Processing**:
- Searches for news/circulars section on MSA Info Hub
- Extracts dates and update text
- Categorizes impact level based on keywords
- Limits to updates from last 90 days

## Resilience & Error Handling

### Retry Logic
- Maximum 3 attempts per request
- Exponential backoff: 1.5s → 2.25s → 3.375s
- Timeout: 30 seconds per request

### Fallback Strategies
- **CSS Selectors First**: Attempts targeted class-based parsing
- **XPath Fallback**: Falls back to generic element matching
- **Default Values**: Uses reasonable defaults if scraping fails
  - Fees: Bachelor $600, Masters $550, Postgraduate $650
  - Processing times: CDR 6 weeks, RPL 4 weeks, Overseas 8 weeks

### Error Logging
- Logs all errors to `acs_scraper_errors.jsonl`
- Includes timestamp, operation, error message, and context
- Does not halt execution on single-element parse failures

## Integration Points

### Phase 1 Data Pipeline
1. **Skills Assessment Routing**: Use occupation list to map applicant occupations to ACS assessment requirements
2. **Fee Calculation**: Include ACS assessment fees in total migration cost estimates
3. **Timeline Planning**: Factor ACS processing times into overall visa timeline recommendations
4. **Policy Updates**: Surface recent ACS changes to operator context

### Operator Integration
Operators can query ACS data via:
```python
from runtime.scrapers import ACSPoller

poller = ACSPoller()

# Get current occupation list
occupations = poller.scrape_occupation_list()

# Get fees
fees = poller.scrape_fees()

# Get processing times
times = poller.scrape_processing_times()

# Run complete poll
results = poller.poll_all()
```

### Data Validation
Before using ACS data in applicant recommendations:
1. **Verify Fees**: Cross-check published fees with current ACS rate card
2. **Verify Times**: Confirm processing time estimates match current guidance
3. **Check Updates**: Review recent_updates for any policy changes affecting assessment

## Schedule

**Cron Configuration** (Fridays 0300 UTC):
```
0 3 * * 5 /path/to/acs_poller.py --all
```

**Rationale**: Weekly frequency (vs daily) because:
- ACS updates occupation list infrequently
- Fees change annually (typically February)
- Processing times update quarterly
- Early Friday morning (03:00 UTC) = Friday afternoon in Western Australia

**Expected Runtime**: 1-2 minutes per full poll cycle

## Important Disclaimers

### Processing Times
- **Not Guarantees**: ACS provides estimates; actual times may vary
- **Backlog Sensitive**: Times increase during high-volume periods
- **Complexity Dependent**: Times vary by applicant background complexity
- **Always Verify**: Operators must confirm current times with ACS when advising applicants

### Fees
- **Annual Review**: ACS typically reviews fees in February each year
- **Subject to Change**: Fees shown are historical; always verify before quoting
- **Grandfathering**: Fees may have transition periods for existing applicants
- **Exemptions**: Certain categories may have different fees

### Occupation List
- **Dynamic**: ACS may add/remove occupations based on demand and policy
- **Skill Level Changes**: Skill Level Requirements can change mid-year
- **Assessment Pathways**: Assessment types and eligibility criteria evolve
- **Always Link**: Provide operators with link to official ACS occupation list

## Implementation Notes

### Parsing Strategy
The scraper uses a two-tier parsing approach:
1. **Primary**: Target CSS selectors for structured data (tables, divs with specific classes)
2. **Secondary**: Regex patterns for unstructured text (news items, fee announcements)

This hybrid approach handles both well-formatted official tables and informal announcement sections.

### Data Validation
All scraped values pass through validation:
- **Occupation Codes**: Must be 6-digit ANZSCO codes
- **Fees**: Must be numeric, in AUD, within $400-$800 range
- **Times**: Must be 1-12 week range
- **Dates**: Normalized to YYYY-MM-DD format

### History Tracking
Weekly snapshots are appended to `acs_history.jsonl` for trend analysis:
- Track fee changes over time
- Identify processing time patterns
- Detect occupation list changes
- Analyze update frequency

## Testing

### Test Coverage
- ✓ Mock ACS website parsing
- ✓ Occupation list extraction
- ✓ Fee parsing and validation
- ✓ Processing time extraction
- ✓ Recent updates scraping
- ✓ Error handling and retry logic
- ✓ JSON schema validation
- ✓ Date normalization

### Manual Validation Steps
1. Run `python -m runtime.scrapers.acs_poller --all`
2. Verify fees match current ACS rate card
3. Cross-check processing times with latest guidance
4. Review occupation list for any recent changes
5. Spot-check 5-10 occupation codes in official ACS list

## Files

- **Implementation**: `runtime/scrapers/acs_poller.py`
- **Current Data**: `knowledge/live_cutoffs/acs_assessments.json`
- **History**: `knowledge/live_cutoffs/acs_history.jsonl`
- **Error Log**: `knowledge/live_cutoffs/acs_scraper_errors.jsonl`
- **Tests**: `tests/test_acs_poller.py`

## References

- ACS MSA Info Hub: https://www.acs.org.au/msa/infohub.html
- ACS Occupation List: https://www.acs.org.au/occupations
- ACS Assessment Paths: https://www.acs.org.au/assessment
- ACS Fee Schedule: https://www.acs.org.au/fees
