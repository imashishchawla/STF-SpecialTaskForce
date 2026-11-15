# Visa Agent: Operations Runbook

**Version:** 1.0  
**Last Updated:** 2026-11-15  
**Audience:** Daily Operators, On-Call Engineers  

---

## Quick Links

- [Daily Morning Briefing](#daily-morning-briefing-0600-utc-5-minutes)
- [Weekly ACS Update](#weekly-acs-update-friday-1000-utc-15-minutes)
- [Weekly SkillSelect Snapshot](#weekly-skillselect-snapshot-monday-1000-utc-15-minutes)
- [Monthly Verification](#monthly-verification-last-friday-2-hours)
- [Emergency: Scraper Failure](#emergency-scraper-failure-30-minutes)
- [Emergency: CRITICAL Alert](#emergency-critical-alert-1-hour)

---

## Daily Morning Briefing (0600 UTC, 5 minutes)

**Time:** 0600 UTC every day  
**Duration:** 5 minutes  
**Operator:** Daily operator on shift  

### Checklist

```
□ 0600 UTC: Wake up, check email for alerts
□ 0605 UTC: Open terminal, navigate to work directory
□ 0607 UTC: View digest
□ 0610 UTC: Review CRITICAL alerts
□ 0612 UTC: Check data quality section
□ 0614 UTC: Note KEY METRICS changes
□ 0616 UTC: Check occupations matching client profiles
□ 0620 UTC: Document findings and escalate if needed
```

### Step-by-Step Procedure

**Step 1: Navigate to Work Directory**

```bash
cd /path/to/portable/Visa-Agent

# Verify you're in correct location
pwd
# Should output: /home/user/STF-SpecialTaskForce/portable/Visa-Agent
```

**Step 2: View Today's Digest**

```bash
# Option A: View with date
DIGEST=$(ls -1 knowledge/digests/daily_digest_$(date +%Y-%m-%d).md 2>/dev/null)

if [ -f "$DIGEST" ]; then
    cat "$DIGEST"
else
    echo "⚠ No digest found for today!"
    ls -lh knowledge/digests/ | tail -5
fi
```

**Step 3: Review CRITICAL Alerts Section**

```
Look for this section in digest:
────────────────────────────────────
### CRITICAL Alerts
────────────────────────────────────

If found, read the following:
- Occupation name
- Visa subclass (189/190/491)
- Change description (what changed)
- Impact (why it matters)
```

**Example CRITICAL Alert:**
```
### CRITICAL Alerts

⚠️ **Software Engineer (261311) - 189 Visa Cutoff Spike**
- Previous: 85 points (2026-11-13)
- Current: 95 points (2026-11-14)  
- Change: +10 points (confirmed 2 consecutive days)
- Impact: 15 additional candidates now ineligible for this round
- Action: Review client database for borderline (85-94) profiles
```

**Action if CRITICAL alert found:**
- [ ] Note the occupation and change
- [ ] Verify against official SkillSelect website
  - Go to: https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect
  - Search for occupation code
  - Confirm cutoff matches digest
- [ ] Check if affects any client profiles in database
- [ ] Notify Visa Coordinator (use email template in Operator Manual)
- [ ] Document in incident log (see below)

**Example Incident Log Entry:**
```bash
cat >> knowledge/incidents/YYYY-MM-DD_briefing_log.txt << 'EOF'
Time: 2026-11-15T06:15:00Z
Operator: John Smith
Alert: CRITICAL - Software Engineer cutoff 85→95 (189)
Action: Verified on SkillSelect website ✓
Affected clients: 3 profiles reviewed
Escalated: YES - email sent to visa-coordinator@company.com
Follow-up: Monitor occupation for next 5 days
EOF
```

**Step 4: Check Data Quality Section**

```
Look for this section:
────────────────────────────────────
### Data Quality
────────────────────────────────────

Expected messages:
✓ All scrapers successful
✓ Data freshness: All <24h old
✓ No missing states

⚠ Warning example:
⚠ DHA scraper offline 48h, using fallback data
```

**Action if quality warning found:**
- [ ] Note which scraper is offline
- [ ] Check logs: `tail -30 logs/scraper.log | grep -i error`
- [ ] For minor issues: Continue, monitor next 24 hours
- [ ] For major issues: Alert DevOps immediately (see Escalation section)

**Step 5: Review KEY METRICS**

```
Look for table like:
────────────────────────────────────
### KEY METRICS

Latest Round Date: 2026-11-15
Total Invitations (This Round): 2,850
Total Invitations (FY): 45,320
Top 5 Occupations by Cutoff: [list]
────────────────────────────────────
```

**Action:**
- [ ] Note if any tracked occupations in top 5
- [ ] Compare cutoffs with yesterday (usually shown in digest)
- [ ] If significant change (>5 points), note for coordinator

**Step 6: Check Occupation Snapshot**

```
Digest shows table:
────────────────────────────────────
Occupation Code | Name | 189 | 190 | 491 | Status
261311 | Software Engineer | 95 | 75 | 70 | active
```

**Action:**
- [ ] Scan for any "closed" or "no_allocation" status
- [ ] Check if tracked occupations have updated cutoffs
- [ ] Flag any new occupations added

**Step 7: Wrap Up**

```bash
# Document completion
cat >> logs/operator_briefing.log << 'EOF'
$(date): Daily briefing completed - No CRITICAL alerts
EOF

# Or if alerts found:
cat >> logs/operator_briefing.log << 'EOF'
$(date): Daily briefing completed - 1 CRITICAL alert escalated
EOF
```

### If Digest Is Missing After 0700 UTC

**Escalation Procedure:**

```bash
# 1. Check if digester is still running
ps aux | grep digester

# 2. Check logs
tail -50 logs/digester.log | head -30

# 3. If timeout or error, manually trigger
python3 -m runtime.intelligence.digester

# 4. Verify new digest
ls -lh knowledge/digests/daily_digest_*.md | tail -1

# 5. If still fails, contact DevOps
echo "DIGEST MISSING - Manual trigger failed" | mail -s "⚠ Visa Agent Digest Error" devops@company.com
```

---

## Weekly ACS Update (Friday, 1000 UTC, 15 minutes)

**Time:** Friday 1000 UTC  
**Duration:** 15 minutes  
**Operator:** Any operator (usually designated "data" person)

### Checklist

```
□ Friday 1000 UTC: Set aside 15 minutes
□ 1005 UTC: Visit ACS website
□ 1010 UTC: Extract processing times and fees
□ 1012 UTC: Update local JSON file
□ 1013 UTC: Regenerate digest
□ 1015 UTC: Verify digest updated
□ 1016 UTC: Commit changes to git
```

### Step-by-Step Procedure

**Step 1: Visit ACS Website**

```bash
# Open browser and navigate to:
# https://www.acs.org.au/

# Find: Resources → MSA InfoHub
# Look for current processing times and fees

# Take screenshot or note:
# - Processing time (e.g., "10 weeks for Bachelor degree")
# - Fees by qualification level
# - Last updated date on their website
```

**Step 2: Record Data**

```
Example data from ACS (November 2026):

Bachelor Degree:
- Processing time: 10 weeks
- Fee: AUD 580

Master Degree:
- Processing time: 8 weeks
- Fee: AUD 580

Diploma:
- Processing time: 12 weeks
- Fee: AUD 385

Associate Degree:
- Processing time: 12 weeks
- Fee: AUD 315
```

**Step 3: Update Local Database**

```bash
cd /path/to/portable/Visa-Agent

# Open editor
nano knowledge/live_cutoffs/acs_assessments.json

# Replace entire file with:
```

```json
{
  "meta": {
    "source": "https://www.acs.org.au/",
    "last_updated": "2026-11-15T10:30:00Z",
    "updated_by": "operator_name",
    "version": "1.0"
  },
  "assessments": [
    {
      "qualification": "Bachelor degree (IT)",
      "processing_time_weeks": 10,
      "processing_time_note": "Updated Nov 2026",
      "fee_aud": 580
    },
    {
      "qualification": "Master degree (IT)",
      "processing_time_weeks": 8,
      "processing_time_note": "Updated Nov 2026",
      "fee_aud": 580
    },
    {
      "qualification": "Diploma (IT)",
      "processing_time_weeks": 12,
      "processing_time_note": "Updated Nov 2026",
      "fee_aud": 385
    },
    {
      "qualification": "Associate degree (IT)",
      "processing_time_weeks": 12,
      "processing_time_note": "Updated Nov 2026",
      "fee_aud": 315
    }
  ]
}
```

**Step 4: Regenerate Digest**

```bash
cd /path/to/portable/Visa-Agent

# Run digester with new ACS data
python3 -m runtime.intelligence.digester

# Verify digest updated
ls -lh knowledge/digests/daily_digest_*.md | tail -1
# Should show recent timestamp
```

**Step 5: Verify ACS Section in Digest**

```bash
# Check digest includes new ACS data
tail -50 knowledge/digests/daily_digest_*.md | grep -A 10 "ACS Processing"

# Expected output:
# ## ACS Processing Times & Fees
# 
# Last Updated: 2026-11-15T10:30:00Z
# Source: https://www.acs.org.au/
# 
# | Qualification | Processing Time | Fee (AUD) |
# | Bachelor | 10 weeks | 580 |
# | Master | 8 weeks | 580 |
```

**Step 6: Commit to Git**

```bash
cd /path/to/portable/Visa-Agent

# Stage changes
git add knowledge/live_cutoffs/acs_assessments.json

# Commit with message
git commit -m "update: ACS processing times and fees (Nov 2026)"

# Verify commit
git log --oneline | head -1
```

---

## Weekly SkillSelect Snapshot (Monday, 1000 UTC, 15 minutes)

**Time:** Monday 1000 UTC  
**Duration:** 15 minutes  
**Operator:** Any operator

### Checklist

```
□ Monday 1000 UTC: Set aside 15 minutes
□ 1005 UTC: Visit SkillSelect website
□ 1010 UTC: Extract occupation cutoffs
□ 1012 UTC: Update JSON and JSONL files
□ 1014 UTC: Regenerate digest
□ 1015 UTC: Verify digest updated
```

### Step-by-Step Procedure

**Step 1: Visit SkillSelect Website**

```bash
# Open browser and navigate to:
# https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect

# Find: "Invitation Rounds" or "Latest Round"
# Look for:
# - Round date (e.g., "15 November 2026")
# - List of occupations with cutoff points
# - Invitations issued for this round
```

**Step 2: Extract Cutoff Data**

```
Example data from SkillSelect (November 2026):

Round Date: 2026-11-15

Software Engineer (261311):
- Visa 189: 95 points (250 invitations)
- Visa 190 (NSW): 75 points (50 invitations)
- Visa 491 (NSW): 70 points (30 invitations)

Accountant (221111):
- Visa 189: 85 points (180 invitations)
- Visa 190 (VIC): 70 points (40 invitations)
- Status: Active
```

**Step 3: Update skillselect_cutoffs.json**

```bash
cd /path/to/portable/Visa-Agent

# Open editor
nano knowledge/live_cutoffs/skillselect_cutoffs.json

# Update with today's cutoffs:
```

```json
{
  "meta": {
    "source": "https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect",
    "scrape_timestamp": "2026-11-15T10:00:00Z",
    "updated_by": "operator_name",
    "round_date": "2026-11-15T00:00:00Z"
  },
  "cutoffs": [
    {
      "occupation_code": "261311",
      "occupation_name": "Software Engineer",
      "visa_type": "189",
      "cutoff_points": 95,
      "invitations_issued": 250,
      "status": "active"
    },
    {
      "occupation_code": "261311",
      "occupation_name": "Software Engineer",
      "visa_type": "190",
      "visa_state": "NSW",
      "cutoff_points": 75,
      "invitations_issued": 50,
      "status": "active"
    },
    {
      "occupation_code": "221111",
      "occupation_name": "Accountant",
      "visa_type": "189",
      "cutoff_points": 85,
      "invitations_issued": 180,
      "status": "active"
    }
  ]
}
```

**Step 4: Append to History**

```bash
cd /path/to/portable/Visa-Agent

# Add entry to history (append-only log)
# One line per occupation per visa type

cat >> knowledge/live_cutoffs/skillselect_history.jsonl << 'EOF'
{"date":"2026-11-15","occupation_code":"261311","occupation_name":"Software Engineer","visa_type":"189","cutoff_points":95,"invitations_issued":250,"status":"active"}
{"date":"2026-11-15","occupation_code":"261311","occupation_name":"Software Engineer","visa_type":"190","visa_state":"NSW","cutoff_points":75,"invitations_issued":50,"status":"active"}
{"date":"2026-11-15","occupation_code":"221111","occupation_name":"Accountant","visa_type":"189","cutoff_points":85,"invitations_issued":180,"status":"active"}
EOF

# Verify appended
tail -5 knowledge/live_cutoffs/skillselect_history.jsonl
```

**Step 5: Regenerate Digest**

```bash
cd /path/to/portable/Visa-Agent

# Run digester with new data
python3 -m runtime.intelligence.digester

# Verify digest updated
ls -lh knowledge/digests/daily_digest_*.md | tail -1
```

**Step 6: Verify Digest Includes New Cutoffs**

```bash
# Check digest shows latest cutoffs
tail -50 knowledge/digests/daily_digest_*.md | grep -A 5 "Software Engineer"

# Should show cutoff of 95 points for 189
```

---

## Monthly Verification (Last Friday, 2 hours)

**Time:** Last Friday of month, 1400-1600 UTC  
**Duration:** 2 hours  
**Operator:** Senior operator or data team lead

### Checklist

```
□ Last Friday 1400 UTC: Block 2 hours in calendar
□ 1410 UTC: Verify DHA occupation list (20 min)
□ 1430 UTC: Verify state monitor data (20 min)
□ 1450 UTC: Verify ACS data (20 min)
□ 1510 UTC: Calculate false positive rate (30 min)
□ 1540 UTC: Document findings (20 min)
□ 1600 UTC: Complete and archive report
```

### Step-by-Step Procedure

**Part 1: Verify DHA Occupation List (20 minutes)**

```bash
cd /path/to/portable/Visa-Agent

# Get latest occupation list
LATEST_OCC=$(ls -1 knowledge/raw_dha/occupation_list_*.json | sort | tail -1)

echo "Verifying: $LATEST_OCC"

# Sample 5 random occupations from our data
python3 << 'EOF'
import json
import random

with open('knowledge/raw_dha/occupation_list_*.json', 'r') as f:
    data = json.load(f)

occupations = data['data'][:200]
sample = random.sample(occupations, min(5, len(occupations)))

print("=== Occupation Verification Sample ===\n")
for i, occ in enumerate(sample, 1):
    print(f"{i}. ANZSCO {occ['occupation_code']}: {occ['occupation_title']}")
    print(f"   Assessing Authorities: {occ.get('assessing_authorities', [])}")
    print()
EOF

# Manually verify each against official website:
# https://immi.homeaffairs.gov.au/visas/working-in-australia/skill-occupation-list
# (Search for ANZSCO code, verify title and authorities match)
```

**Step: Document Verification**

```bash
cat > knowledge/incidents/monthly_verification_$(date +%Y-%m).md << 'EOF'
# Monthly Verification Report - YYYY-MM

Date: YYYY-MM-DD
Verified by: operator_name

## Part 1: DHA Occupation List Verification

Occupation Samples Verified: 5

| ANZSCO | Title | Our Data | Official | Match |
|--------|-------|----------|----------|-------|
| 261311 | Software Engineer | ✓ | ✓ | YES |
| 221111 | Accountant | ✓ | ✓ | YES |
| [more rows] | | | | |

Discrepancies Found: 0
Status: ✓ PASS

EOF
```

**Part 2: Verify State Monitor Data (20 minutes)**

```bash
cd /path/to/portable/Visa-Agent

# Check state monitor files exist
echo "=== State Monitor Files ==="
ls -1h knowledge/live_cutoffs/state_*.json

# Sample 2 states (NSW, VIC)
for STATE in NSW VIC; do
    echo
    echo "=== Verifying $STATE ==="
    
    # Show our data
    if [ -f "knowledge/live_cutoffs/state_$STATE.json" ]; then
        echo "Data from our system:"
        cat "knowledge/live_cutoffs/state_$STATE.json" | head -30
    fi
    
    echo
    echo "Expected:"
    echo "Visit official portal (NSW: https://www.iatskillselect.immi.gov.au/)"
    echo "Note: Manually verify 3-5 occupations match current cutoffs"
done

# Document findings
```

**Part 3: Verify ACS Data (20 minutes)**

```bash
# Visit https://www.acs.org.au/
# Compare our data with official source

echo "=== Comparing ACS Data ==="
cat knowledge/live_cutoffs/acs_assessments.json | grep -E "qualification|processing_time|fee"

# Manual comparison:
# Bachelor Degree: Official says 10 weeks, we have: ?
# [Document all matches and mismatches]
```

**Part 4: Calculate False Positive Alert Rate (30 minutes)**

```bash
cd /path/to/portable/Visa-Agent

python3 << 'EOF'
import json
from pathlib import Path
from datetime import datetime, timedelta

# Get all alerts from last 30 days
today = datetime.utcnow()
thirty_days_ago = today - timedelta(days=30)

alert_files = []
for f in Path('knowledge/alerts').glob('*.json'):
    mtime = datetime.fromtimestamp(f.stat().st_mtime)
    if mtime > thirty_days_ago:
        alert_files.append(f)

print(f"=== Alert Analysis (Last 30 days) ===")
print(f"Alert files found: {len(alert_files)}")

total_alerts = 0
confirmed_alerts = 0
false_positives = 0

for alert_file in sorted(alert_files):
    try:
        with open(alert_file) as f:
            alerts = json.load(f)
        
        for alert in alerts:
            total_alerts += 1
            
            # Check if 2-day confirmation was met
            if alert.get('days_confirmed', 0) >= 2:
                confirmed_alerts += 1
            else:
                false_positives += 1
    
    except json.JSONDecodeError:
        print(f"✗ Error reading: {alert_file}")

print(f"\nTotal alerts: {total_alerts}")
print(f"Confirmed (2-day rule): {confirmed_alerts}")
print(f"False positives: {false_positives}")

if total_alerts > 0:
    fp_rate = (false_positives / total_alerts) * 100
    print(f"False positive rate: {fp_rate:.1f}%")
    
    if fp_rate < 5:
        print("Status: ✓ PASS (target: <5%)")
    else:
        print(f"Status: ✗ FAIL (above target)")
        print("\nRecommended actions:")
        print("1. Review recent alert logic in digester.py")
        print("2. Check 2-day confirmation rule is working")
        print("3. Audit CSS selectors for false positives")
EOF
```

**Part 5: Document Findings**

```bash
cat >> knowledge/incidents/monthly_verification_$(date +%Y-%m).md << 'EOF'

## Part 2: State Monitor Verification

States Verified: NSW, VIC
Occupations Spot-Checked: 6

Discrepancies Found: 0
Status: ✓ PASS

## Part 3: ACS Data Verification

Items Verified: Processing times (4 qualifications), Fees (4 levels)
Discrepancies: 0
Last Official Update: [Check ACS website]
Status: ✓ PASS

## Part 4: False Positive Rate Analysis

Period: Last 30 days
Total Alerts: 45
Confirmed Alerts: 43
False Positives: 2
False Positive Rate: 4.4%
Status: ✓ PASS (target: <5%)

## Overall Status: ✓ VERIFICATION PASSED

All checks passed. System is operating normally.

Signed: operator_name
Date: YYYY-MM-DD
EOF

# Archive report
tar -czf backups/verification_$(date +%Y-%m).tar.gz knowledge/incidents/monthly_verification_*.md
```

---

## Emergency: Scraper Failure (30 minutes)

**Trigger:** No digest for 24+ hours, OR scraper errors for 2+ consecutive days  
**Time to Resolution:** 30 minutes  
**Escalation Path:** Operator → DevOps → Data Lead

### Checklist

```
□ 0600 UTC (Day 2): Discover scraper failure
□ 0605 UTC: Verify home affairs website is up
□ 0610 UTC: Check scraper logs for errors
□ 0615 UTC: Manually trigger scraper
□ 0620 UTC: If still fails, use fallback data
□ 0625 UTC: Regenerate digest with fallback
□ 0630 UTC: Notify coordinator of stale data
□ 0635 UTC: Document incident
□ 0640 UTC: Escalate to DevOps if needed
```

### Step-by-Step Procedure

**Step 1: Verify Home Affairs Website Status**

```bash
# Test website connectivity
curl -I https://immi.homeaffairs.gov.au/ --max-time 10

# Expected: HTTP/1.1 200 OK
# If timeout/error: Website may be down

# Alternative: Visit https://immi.homeaffairs.gov.au/
# in browser and check if it loads
```

**Step 2: Check Scraper Logs**

```bash
cd /path/to/portable/Visa-Agent

# View recent errors
tail -100 logs/scraper.log | grep -i "error\|fail\|timeout"

# Example errors:
# - "Connection timeout after 30 seconds"
# - "HTTPError 503: Service Unavailable"
# - "Could not parse occupation list (no matches found)"
```

**Step 3: Check Scraper Error Log**

```bash
# View detailed error log
tail -20 knowledge/live_cutoffs/scraper_errors.jsonl | python3 -m json.tool

# Example error:
{
  "timestamp": "2026-11-15T03:15:00Z",
  "endpoint": "visa_finder",
  "error_type": "timeout",
  "message": "Connection timeout after 30 seconds"
}
```

**Step 4: Manually Trigger Scraper**

```bash
cd /path/to/portable/Visa-Agent

# Run specific scraper with verbose output
python3 -m runtime.scrapers.dha_scraper --target visa_finder --verbose 2>&1

# Wait for completion (2-3 minutes)
# If successful: "✓ Data saved to knowledge/raw_dha/visa_finder_*.json"
# If failed: Shows error message

# If successful, run other scrapers:
python3 -m runtime.scrapers.dha_scraper --target skillselect --verbose
python3 -m runtime.scrapers.state_monitor --all --verbose
```

**Step 5: If Scraper Still Fails**

```bash
# Use fallback data from previous day
cd /path/to/portable/Visa-Agent

bash << 'EOF'
# Find yesterday's data files
YESTERDAY=$(date -d '1 day ago' +%Y-%m-%d)
YESTERDAY_DATA=$(ls -1 knowledge/raw_dha/*_$YESTERDAY.json 2>/dev/null | head -1)

if [ -z "$YESTERDAY_DATA" ]; then
    echo "✗ No previous day's data found"
    exit 1
fi

# Copy yesterday's files (simulating successful scrape)
for file in knowledge/raw_dha/*_$YESTERDAY.json; do
    NEW_NAME=$(echo $file | sed "s/$YESTERDAY/$(date +%Y-%m-%d)/")
    cp "$file" "$NEW_NAME"
    echo "✓ Created fallback: $NEW_NAME"
done

# Mark as fallback in metadata
# (Operator should manually edit JSON to note: "fallback data")
EOF
```

**Step 6: Regenerate Digest with Fallback**

```bash
python3 -m runtime.intelligence.digester

# Verify digest created
ls -lh knowledge/digests/daily_digest_*.md | tail -1
```

**Step 7: Notify Coordinator of Stale Data**

```bash
# Email template
cat << 'EOF' | mail -s "⚠ Visa Agent: Digest Using Fallback Data" coordinator@company.com

Subject: ⚠ Visa Agent: Digest Using Fallback Data

Body:
Today's digest (2026-11-15) is using fallback data from 2026-11-14
because the DHA scraper failed to retrieve current data.

Reason: [Connection timeout / Home Affairs temporarily unavailable]

This means:
- Occupation cutoffs are 1 day old
- SkillSelect round data is 1 day old
- State quota data is 1 day old

Action:
- Review today's digest with understanding that data is 1 day stale
- Do not escalate CRITICAL alerts until scraper recovers
- Check official SkillSelect website for any urgent changes

Status:
- DevOps investigating scraper issue
- Next automated scrape: 2026-11-16 0300 UTC
- Will escalate if issue persists >24 hours

Coordinator should not inform candidates of changes until scraper recovers.

Best regards,
Visa Agent Operations
EOF
```

**Step 8: Document Incident**

```bash
cat >> knowledge/incidents/YYYY-MM-DD_scraper_failure.md << 'EOF'
# Scraper Failure Incident Report

Date: 2026-11-15
Incident Type: Scraper Failure (24h+ without data update)
Affected Scraper: DHA (visa_finder, skillselect, occupation_list, visa_listing)

## Discovery
- Time Discovered: 0615 UTC
- Discovery Method: Daily operator briefing (digest missing)
- First Failure: 2026-11-14 0300 UTC

## Root Cause Analysis
- Primary Cause: Home Affairs website timeout (HTTP 503)
- Secondary Cause: [If known]
- Network Connectivity: OK (verified DNS, ping, alternate sites)

## Impact
- Digest uses fallback (1 day stale)
- Affected clients: All monitoring SkillSelect changes
- Severity: Medium (temporary, data recovers)

## Resolution
- Manual scraper triggered: 0620 UTC
- Result: Failed again (persistent timeout)
- Fallback activated: 0630 UTC
- Digest regenerated with fallback: 0635 UTC
- Coordinator notified: 0640 UTC

## Follow-Up
- [ ] DevOps investigate Home Affairs connectivity
- [ ] Check if CSS selectors need updating
- [ ] Monitor 2026-11-16 scrape (if issue persists)
- [ ] Document any infrastructure changes needed

Incident Duration: ~35 minutes
Operator: Jane Doe
Escalated to: DevOps Lead
EOF

# Archive incident
git add knowledge/incidents/YYYY-MM-DD_scraper_failure.md
git commit -m "incident: document scraper failure on 2026-11-15"
```

**Step 9: Escalate to DevOps if Issue Persists**

```bash
# Send escalation email if scraper offline >24h

cat << 'EOF' | mail -s "🚨 ESCALATION: Visa Agent Scraper Offline >24h" devops@company.com

Subject: 🚨 ESCALATION: Visa Agent Scraper Offline >24h

Body:
DHA Scraper has been offline since 2026-11-14 0300 UTC (38 hours).

Details:
- Endpoint: visa_finder, skillselect, occupation_list, visa_listing
- Error: Connection timeout (HTTP 503)
- Manual trigger attempts: 3 (all failed)
- Fallback activated: Yes (digest using 1-day-old data)

Investigation Completed:
- Home Affairs website status: UNKNOWN (timeout prevents verification)
- Network connectivity: OK
- CSS selectors: Assumed correct (no parse errors in logs)

Action Requested:
1. Investigate Home Affairs website status
2. Check if IP/domain is being rate-limited
3. Verify network path to immi.homeaffairs.gov.au
4. Consider proxy/VPN requirement if Home Affairs changed access policy

Urgency: HIGH (affects visa immigration intelligence for all clients)

Operator: Jane Doe
Ticket: [optional incident tracking ID]
EOF
```

---

## Emergency: CRITICAL Alert (1 hour)

**Trigger:** Occupation closes, cutoff spikes >15 points, quota fills early, or major status change  
**Time to Resolution:** 1 hour  
**Escalation Path:** Operator → Visa Coordinator → Clients (if needed)

### Checklist

```
□ 0630 UTC: Operator reads CRITICAL alert in digest
□ 0635 UTC: Verify alert against official source
□ 0645 UTC: Assess impact (how many clients affected?)
□ 0655 UTC: Notify Visa Coordinator
□ 0700 UTC: Document incident
□ 0730 UTC: Monitor occupation for next 5 days
□ 0745 UTC: Follow-up communication
□ 0800 UTC: Incident report complete
```

### Step-by-Step Procedure

**Step 1: Verify CRITICAL Alert**

```bash
cd /path/to/portable/Visa-Agent

# Read CRITICAL alert from digest
DIGEST=$(ls -1 knowledge/digests/daily_digest_$(date +%Y-%m-%d).md)
grep -A 5 "⚠️ CRITICAL" "$DIGEST"

# Example output:
# ⚠️ CRITICAL: Software Engineer (261311) - 189 Visa Cutoff Spike
# Previous: 85 points → Current: 95 points
# Change: +10 points (confirmed 2 consecutive days)
# Impact: ~15 candidates now ineligible
```

**Step 2: Verify Against Official Source**

```bash
# Visit SkillSelect website
# https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect

# Find the occupation in latest round
# Verify:
# ✓ Occupation code matches (261311 = Software Engineer)
# ✓ Visa subclass matches (189 = Skilled Independent)
# ✓ Cutoff points matches (95 points)
# ✓ Status is correct (active, closed, etc.)

# Document verification
cat >> knowledge/incidents/YYYY-MM-DD_critical_alert.md << 'EOF'
## Verification

- [ ] Occupation code verified: 261311 ✓
- [ ] Visa subclass verified: 189 ✓
- [ ] Cutoff verified: 95 points ✓
- [ ] Status verified: Active ✓
- [ ] Official source: SkillSelect website
- [ ] Verified by: operator_name
- [ ] Time: 2026-11-15T06:40:00Z

EOF
```

**Step 3: Assess Impact**

```bash
cd /path/to/portable/Visa-Agent

# Determine how many clients are affected
# This requires access to client database (not shown here)

# Example impact assessment:
# - Occupation: Software Engineer (261311)
# - Visa: 189 (Skilled Independent)
# - Cutoff: 85 → 95 points
# - Affected profiles: 3 candidates with 85-94 points
# - Recommended action: Advise 190 (state sponsorship) instead

cat >> knowledge/incidents/YYYY-MM-DD_critical_alert.md << 'EOF'

## Impact Assessment

Affected Client Profiles:
- Client A: 89 points (189) - NOW INELIGIBLE
- Client B: 91 points (189) - NOW INELIGIBLE
- Client C: 94 points (189) - NOW INELIGIBLE
- Total affected: 3 clients

Recommended Actions:
1. Contact affected clients immediately
2. Suggest 190 state sponsorship pathway
3. Increase focus on points accumulation activities
4. Monitor occupation for next 5 days (may continue rising)

EOF
```

**Step 4: Notify Visa Coordinator**

```bash
# Send structured email with all details

cat > /tmp/critical_alert_email.txt << 'EOF'
To: visa-coordinator@company.com
Subject: 🚨 CRITICAL Alert: Software Engineer Cutoff Spike (189 Visa)

Body:

CRITICAL ALERT DETECTED
──────────────────────────────────────────────────────

Occupation: Software Engineer (261311)
Visa Subclass: 189 (Skilled Independent)
Change: 85 points → 95 points
Change Magnitude: +10 points
Confirmed: YES (2 consecutive days)
Verified Source: SkillSelect official website

IMPACT
──────────────────────────────────────────────────────
Affected Profiles: 3 clients with 85-94 points
Recommendation: Switch to 190 state sponsorship
Urgency: HIGH

AFFECTED CLIENTS
──────────────────────────────────────────────────────
- Client A (89 pts for 189): NOW INELIGIBLE
- Client B (91 pts for 189): NOW INELIGIBLE
- Client C (94 pts for 189): NOW INELIGIBLE

ACTION REQUIRED
──────────────────────────────────────────────────────
1. Contact affected clients within 2 hours
2. Provide updated advice on visa pathways (190 or 491)
3. Assess if state sponsorship is viable
4. Plan points accumulation strategy for future rounds

TREND MONITORING
──────────────────────────────────────────────────────
This occupation will be monitored for next 5 days.
If cutoff continues rising or occupation closes, 
immediate additional notification will be sent.

DATA SOURCE
──────────────────────────────────────────────────────
Digest: knowledge/digests/daily_digest_2026-11-15.md
Alert Generated: 2026-11-15T06:30:00Z
Operator: John Smith

Questions? Contact Visa Agent Operations.

EOF

# Send email
mail -s "🚨 CRITICAL Alert: Software Engineer Cutoff Spike (189 Visa)" \
     visa-coordinator@company.com < /tmp/critical_alert_email.txt

echo "✓ Email sent to coordinator"
```

**Step 5: Document Incident**

```bash
cat > knowledge/incidents/YYYY-MM-DD_critical_alert_software_engineer.md << 'EOF'
# CRITICAL ALERT INCIDENT REPORT

Date: 2026-11-15
Occupation: Software Engineer (261311)
Visa: 189 (Skilled Independent)
Alert Type: Cutoff Spike
Severity: CRITICAL

## Alert Details

Previous State (2026-11-13): 85 points
Current State (2026-11-14): 95 points  
Change: +10 points
Confirmation: 2 consecutive days ✓

## Verification

Source: SkillSelect official website
Verified By: operator_name
Time Verified: 2026-11-15T06:40:00Z
Result: VERIFIED ✓

## Impact Assessment

Affected Candidates: 3
- Client A (89 points): Ineligible
- Client B (91 points): Ineligible  
- Client C (94 points): Ineligible

Recommendation: Switch to 190 state sponsorship

## Coordinator Notification

Notified: 2026-11-15T06:45:00Z
Contact: visa-coordinator@company.com
Method: Email with client list
Status: Sent ✓

## Follow-Up Actions

- [ ] Monitor occupation cutoff daily for next 5 days
- [ ] Check if other occupations affected (similar trend)
- [ ] Update client roadmaps for affected profiles
- [ ] Re-assess state sponsorship options

## Closure

Status: OPEN (monitoring)
Next Review: 2026-11-16 (check if trend continues)
Escalation: If continues rising OR occupation closes

Incident Handler: John Smith
Timestamp: 2026-11-15T06:50:00Z

EOF

# Archive incident
git add knowledge/incidents/YYYY-MM-DD_critical_alert_software_engineer.md
git commit -m "incident: document critical alert for Software Engineer cutoff spike"
```

**Step 6: Monitor for 5 Days**

```bash
# Add reminder to check next 5 days of digests
# Look for Software Engineer (261311) cutoff in:
# - 2026-11-16 digest (check if >95)
# - 2026-11-17 digest (check if >95)
# - 2026-11-18 digest (check if >95)
# - 2026-11-19 digest (check if >95)
# - 2026-11-20 digest (check if occupation closes)

cat > /tmp/5day_monitor.txt << 'EOF'
MONITOR SCHEDULE: Software Engineer (261311) - 189 Visa

2026-11-15: Cutoff 95 (CRITICAL ALERT ISSUED)
2026-11-16: Cutoff ? (monitor tomorrow)
2026-11-17: Cutoff ? (monitor)
2026-11-18: Cutoff ? (monitor)
2026-11-19: Cutoff ? (monitor)
2026-11-20: Cutoff ? (final check)

Action:
- If continues rising: Escalate to clients again
- If occupation closes: Create new CRITICAL alert
- If stabilizes: Close incident report

EOF
```

---

## Handoff Checklist (End of Shift)

Before handing off to next operator:

```bash
cd /path/to/portable/Visa-Agent

# Create handoff report
cat > /tmp/shift_handoff.txt << 'EOF'
=== SHIFT HANDOFF REPORT ===

Date: 2026-11-15
Operator (Previous Shift): John Smith
Operator (Next Shift): Jane Doe

Morning Briefing Summary:
- ✓ Digest generated successfully
- ✓ No CRITICAL alerts
- ✓ All data sources fresh (<24h old)
- ✓ Disk space: 45% utilized

Actions Completed:
- ✓ Reviewed digest
- ✓ Checked scraper logs (no errors)
- ✓ Verified ACS data up-to-date
- ✓ Escalated 1 occupation change to coordinator

Known Issues:
- None

Upcoming Tasks (Today):
- [ ] Friday ACS update (1000 UTC) - Jane to perform
- [ ] Monitor Software Engineer occupation trend (5 days)

Escalations Active:
- None

Incident Reports:
- See: knowledge/incidents/YYYY-MM-DD_briefing_log.txt

Questions for Incoming Operator:
- None

Handoff completed: 2026-11-15T07:00:00Z
Signed: John Smith

EOF

# Send handoff email
mail -s "Shift Handoff: 2026-11-15 Visa Agent Operations" jane.doe@company.com < /tmp/shift_handoff.txt
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-11-15  
**Next Review:** 2026-12-15
