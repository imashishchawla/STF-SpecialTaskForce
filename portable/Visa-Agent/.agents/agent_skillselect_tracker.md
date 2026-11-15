---
agent_id: skillselect-tracker
version: 1.0.0
status: draft
phase: 3b
role: Data aggregator for SkillSelect invitation cutoff tracking
entry_point: query_skillselect_data
---

# SkillSelect Cutoff Tracker Agent

## Purpose
Provides current and historical SkillSelect invitation cutoff data, 12-month trend analysis, and occupation-specific insights to support visa agent recommendations.

## Data Sources
- **Official Source**: https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect/invitation-rounds
- **Data Files**: 
  - Current: `knowledge/live_cutoffs/skillselect_cutoffs.json`
  - History: `knowledge/live_cutoffs/skillselect_history.jsonl`
- **Update Frequency**: Monthly (typically around 15th of each month)

## Key Concepts

### Tie-Break Dates vs. Points Cutoffs
Modern SkillSelect uses **tie-break dates** rather than traditional points minimums:
- **Tie-Break Date**: The date when an EOI must have reached its full points score to be invited
- **Interpretation**: Earlier tie-break date = less demand (older EOIs can still be invited); Later tie-break date = high demand (only recent EOIs invited)
- **Example**: 
  - Software Engineer (2026-10-13): Very high demand, only EOIs from Oct 13, 2026 and later invited
  - Plumber (2026-06-11): Moderate demand, EOIs from June 11, 2026 and earlier still in the queue

## Core Functions

### 1. Query Current Cutoffs
**Input**: `occupation_code` (optional, ANZSCO code)
**Output**: Latest round cutoff data + invitation status

```python
def get_current_cutoffs(occupation_code=None):
    """
    Load knowledge/live_cutoffs/skillselect_cutoffs.json
    If occupation_code provided: filter to single occupation
    If None: return all occupations
    Return: {occupation, invited_count, tiebreak_date, status}
    """
    import json
    with open("knowledge/live_cutoffs/skillselect_cutoffs.json") as f:
        data = json.load(f)
    
    if occupation_code:
        return next(
            (occ for occ in data["cutoffs"] 
             if occ["occupation_code"] == occupation_code),
            None
        )
    return data["cutoffs"]
```

### 2. Calculate 12-Month Trend
**Input**: `occupation_code`, `period` ("latest", "12m_trend", "6m_trend")
**Output**: Trend direction, velocity, anomalies

```python
def analyze_trend(occupation_code, period="12m_trend"):
    """
    Load knowledge/live_cutoffs/skillselect_history.jsonl
    Filter by occupation_code, parse timestamps
    Calculate:
      - 1-month change: latest vs 1 month ago
      - 3-month trend: direction + velocity
      - 12-month comparison: min/max tiebreak dates
      - Anomalies: tiebreak jumps >7 days
    Return: {trend_direction, velocity, anomalies, min_max}
    """
    import json
    from datetime import datetime, timedelta
    
    records = []
    with open("knowledge/live_cutoffs/skillselect_history.jsonl") as f:
        for line in f:
            rec = json.loads(line)
            if rec["occupation_code"] == occupation_code:
                records.append(rec)
    
    records.sort(key=lambda x: datetime.fromisoformat(x["date"]))
    
    if len(records) < 2:
        return {"status": "insufficient_history"}
    
    # Calculate 1-month change
    latest = records[-1]
    one_month_ago = records[-2] if len(records) >= 2 else None
    
    # Calculate 12-month trend
    oldest = records[0]
    
    return {
        "occupation_code": occupation_code,
        "current_tiebreak": latest["tiebreak_date"],
        "current_invited": latest["invited"],
        "one_month_change": {
            "invited_delta": latest["invited"] - (one_month_ago["invited"] if one_month_ago else 0),
            "tiebreak_days_shift": (
                datetime.fromisoformat(latest["tiebreak_date"]) - 
                datetime.fromisoformat(one_month_ago["tiebreak_date"])
            ).days if one_month_ago else None
        },
        "trend_12m": {
            "oldest_date": oldest["date"],
            "oldest_tiebreak": oldest["tiebreak_date"],
            "oldest_invited": oldest["invited"],
            "direction": "improving" if datetime.fromisoformat(latest["tiebreak_date"]) > datetime.fromisoformat(oldest["tiebreak_date"]) else "tightening"
        }
    }
```

### 3. Identify Anomalies
**Input**: None (scans all occupations)
**Output**: List of occupations with unusual patterns

Anomaly Detection Rules:
- **Cutoff Spike**: Tiebreak date jumps >7 days month-over-month
- **Invited Collapse**: Invitations drop >50% month-over-month
- **Oscillation**: Tiebreak dates fluctuate >5 days over 3-month period
- **No Allocation**: Occupation receives 0 invitations for 2+ consecutive rounds

```python
def detect_anomalies():
    """
    Scan all occupations in history
    Flag occupations with:
      - Tiebreak jumps >7 days
      - Invitation drops >50%
      - Oscillating patterns
      - Zero invitations for 2+ rounds
    Return: {anomaly_type, occupation, severity}
    """
    pass
```

## Usage Examples

### Example 1: Check Software Engineer Cutoff
```
Input: Query occupation_code="261313"
Output:
{
  "occupation": "Software Engineer",
  "latest_round": "2026-10-15",
  "invited_this_round": 456,
  "tiebreak_date": "2026-10-13",
  "interpretation": "Very high demand. Only EOIs dated Oct 13, 2026 or later invited.",
  "trend_12m": "invitations increasing, tiebreak dates becoming more recent"
}
```

### Example 2: Identify Tightening Occupations
```
Input: Query period="12m_trend"
Output: [
  {
    "occupation": "Software Engineer",
    "trend": "tightening",
    "velocity": "rapid",
    "12m_change": "tiebreak advanced by 45 days",
    "anomaly": "cutoff spike of 12 days in September 2026"
  }
]
```

### Example 3: Find Consistent Occupations
```
Input: Query period="stability"
Output: [
  {
    "occupation": "Database Administrator",
    "stability": "moderate",
    "tiebreak_variance": 18 days over 12 months,
    "trend": "stable"
  }
]
```

## Data Structure Reference

### skillselect_cutoffs.json
```json
{
  "meta": {
    "source": "official_url",
    "last_updated": "YYYY-MM-DD",
    "next_update": "YYYY-MM-DD",
    "round_date": "YYYY-MM-DD"
  },
  "cutoffs": [
    {
      "date": "YYYY-MM-DD",
      "occupation_code": "ANZSCO",
      "occupation_title": "string",
      "invited_this_round": integer,
      "visa_189_tiebreak_date": "YYYY-MM-DD or null",
      "visa_189_status": "invited | no_allocation | closed",
      "notes": "string"
    }
  ]
}
```

### skillselect_history.jsonl
```jsonl
{"date": "YYYY-MM-DD", "round": "Mon YYYY", "occupation_code": "ANZSCO", "occupation_title": "string", "invited": integer, "tiebreak_date": "YYYY-MM-DD or null", "status": "active | closed | no_allocation"}
```

## Trend Analysis Methods

### 1. Month-over-Month (MoM) Change
- Compare current month's tiebreak date to previous month
- Calculate days shifted (positive = earlier tiebreak = higher demand)
- Classify as: Significant (>5 days), Moderate (2-5 days), Stable (<2 days)

### 2. Quarterly Velocity
- Average rate of tiebreak date change over 3-month period
- Calculate: (current_tiebreak - 3months_ago_tiebreak) / 90 days
- Interpret: Days per month of cutoff shift

### 3. Annual Comparison
- Compare min/max tiebreak dates across 12-month period
- Calculate: max_date - min_date = total tiebreak swing
- High swing (>30 days) = volatile demand
- Low swing (<10 days) = stable demand

### 4. Anomaly Detection
```
IF tiebreak_jump > 7 days in any month:
  SEVERITY = "high"
  ACTION = "flag for manual review"

IF invited_count < 20 and status = "invited":
  SEVERITY = "medium"
  ACTION = "monitor for closure"

IF tiebreak oscillates >5 days within 3 months:
  SEVERITY = "medium"
  ACTION = "indicate unpredictable demand"
```

## Recommendations for Clients

### For High-Demand Occupations (recent tiebreak dates)
- Strategy: Maximize points before EOI submission
- Timeline: Submit as soon as ready; delays cost position in queue
- Risk: Tiebreak may shift forward rapidly

### For Moderate-Demand Occupations
- Strategy: Prepare strong EOI while accumulating points
- Timeline: Submit within 1-2 months of points target
- Risk: Moderate risk of tiebreak shifts

### For Low-Demand Occupations
- Strategy: Can afford to optimize over longer period
- Timeline: 3-6 months to prepare
- Risk: May receive no invitations even with strong profile

### For Oscillating Occupations
- Strategy: Monitor monthly rounds before committing
- Timeline: Wait for pattern to stabilize
- Risk: High uncertainty; may miss rounds

## Maintenance

### Monthly Update Process
1. Visit https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect/invitation-rounds
2. Extract latest invitation round data (typically mid-month)
3. Append new records to `skillselect_history.jsonl`
4. Update `skillselect_cutoffs.json` with current round
5. Run anomaly detection to flag new patterns
6. Document any policy changes or occupation closures

### Field Definitions
- **tiebreak_date**: Latest EOI submission date invited in current round (YYYY-MM-DD)
- **invited**: Number of EOIs invited in this round
- **status**: "invited" (occupation is receiving invitations), "no_allocation" (no places allocated), "closed" (occupation closed to invitations)
- **round**: Monthly identifier (e.g., "Oct 2026")

## Integration Points

### Visa Agent Checklist Integration
Use this data to populate:
- "Current SkillSelect Status" section of occupation assessment
- Historical trend analysis for "Occupation Demand" scorecard
- Anomaly alerts for "Watch List" occupations
- Timeline recommendations based on trend velocity

### Client Profile Integration
Use tiebreak dates to:
- Calculate EOI submission deadline for target occupation
- Compare client's current points to occupation tiebreak
- Identify if current points sufficient for invitation
- Estimate turnaround time based on historical velocity

## Known Limitations

1. **Tie-Break Date System**: Newer system (2022+) makes direct historical comparison difficult with older points-based system
2. **Occupation Closures**: Some occupations close/reopen without warning
3. **Data Lag**: Official data updated ~15th of each month; estimates for interim periods
4. **State-Specific Data**: 190 and 491 visas have state-based allocations not captured in main cutoffs.json
5. **Frequency Variations**: Department may run unscheduled invitation rounds

## Related Resources

- Official SkillSelect: https://skillselect.gov.au/
- ANZSCO Occupation List: https://www.abs.gov.au/ausstats/abs@.nsf/mf/1220.0
- Previous Rounds Archive: https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect/previous-rounds
- Visa Agent Occupation Guide: `.agents/visa-agent.md`

---

**Last Updated**: 2026-11-15  
**Data Freshness**: Current as of 2026-10-15 invitation round  
**Next Data Update Expected**: ~2026-12-15  
**Maintenance Owner**: Data Architect Agent
