# Visa Agent Quick Wins + Phase 1: Operator Manual

**Version:** 1.0  
**Last Updated:** 2026-11-15  
**Audience:** Daily Operators & Intelligence Analysts  
**Time Commitment:** 5 min/day (briefing) + 1 hour/week (manual updates) + emergency response

---

## Table of Contents

1. [Role Overview](#role-overview)
2. [Daily Responsibilities](#daily-responsibilities)
3. [Weekly Responsibilities](#weekly-responsibilities)
4. [Monthly Responsibilities](#monthly-responsibilities)
5. [CRITICAL Alert Response](#critical-alert-response)
6. [Manual Data Updates](#manual-data-updates)
7. [Monitoring & Escalation](#monitoring--escalation)
8. [Common Issues & Quick Fixes](#common-issues--quick-fixes)

---

## Role Overview

As Visa Agent Operator, you are responsible for:

- **Daily Intelligence Review:** Morning briefing on occupation cutoff changes and alerts
- **Incident Response:** Respond to CRITICAL alerts (occupation closures, quota fills, major spikes)
- **Data Accuracy:** Verify scraped data weekly against official sources
- **Manual Updates:** Weekly updates to ACS fees and SkillSelect cutoffs
- **Escalation:** Flag significant changes to Visa Coordinator for client notification
- **Documentation:** Log incidents and maintain audit trail

**Expected Time:**
- Daily: 5 minutes (review digest)
- Weekly: 60 minutes (ACS update + spot checks + archiving)
- Monthly: 2 hours (verification + documentation updates)
- Emergency: Variable (depends on incident severity)

**Key Skills Required:**
- Familiarity with Australian visa programs (189, 190, 491, 494)
- Understanding of occupation cutoff mechanics (points-based allocation)
- Ability to spot data anomalies and validate against official sources
- Communication skills for escalating to coordinator

---

## Daily Responsibilities

### Morning Briefing (0600 UTC, 5 minutes)

**Every morning, review the day's digest:**

```bash
# Navigate to work directory
cd /path/to/portable/Visa-Agent

# View today's digest
cat knowledge/digests/daily_digest_$(date +%Y-%m-%d).md

# Or view latest (useful if digest date format varies)
cat knowledge/digests/daily_digest_*.md | tail -1 | head -200
```

**In the digest, look for:**

1. **CRITICAL Alerts Section**
   - Red flag entries starting with `⚠️ CRITICAL`
   - Examples:
     - "Occupation X closed (invitations ceased)"
     - "Cutoff spike: Software Engineer +15 points (190 visa)"
     - "State quota filled early: NSW 2 months ahead of schedule"
   - **Action:** Read the full alert, check the "Change" and "Impact" sections
   - **Next Step:** See [CRITICAL Alert Response](#critical-alert-response) section

2. **Data Quality Section**
   - Look for any `⚠` warnings about stale data
   - Example: "DHA scraper offline 24h, using previous day's data"
   - **Action:** Check logs: `tail -20 logs/scraper.log`
   - **Next Step:** Alert DevOps if scrapers consistently failing

3. **Key Metrics Section**
   - Note the latest round date and total invitations
   - Check if occupation you track has appeared
   - Review cutoff trends for monitored occupations
   - **Action:** Compare with yesterday's metrics (usually 10+ lines in digest)

4. **Occupation Snapshot**
   - Table showing cutoff for each occupation
   - Look for new occupations added or removed
   - Check if any occupation is close to "no allocation" (meaning closed)
   - **Action:** Flag coordinator if any occupations match client profiles

**Daily Checklist:**
- [ ] Digest file exists and is dated today (0600 UTC deadline)
- [ ] No `⚠️ CRITICAL` alerts (or understood and being handled)
- [ ] Data quality all green (no stale data warnings)
- [ ] Disk space >80% available
- [ ] Reviewed KEY METRICS section
- [ ] Checked if any matched occupations need candidate notification

**If digest is missing after 0700 UTC:**
```bash
# Check if digester is still running
ps aux | grep digester

# Check logs
tail -50 logs/digester.log

# Manually trigger if needed
python3 -m runtime.intelligence.digester

# Verify new digest created
ls -lh knowledge/digests/daily_digest_*.md | tail -1
```

---

## Weekly Responsibilities

### Friday: ACS Processing Time Update (15 minutes)

**Every Friday morning, update ACS fees and processing times:**

1. **Visit ACS Website**
   - Go to https://www.acs.org.au/
   - Navigate to: Resources → MSA InfoHub → Infohub
   - Look for current processing times and fees

2. **Record Current Data**
   - Note processing time estimates (e.g., "8 weeks for Bachelor degree")
   - Copy current fees by qualification level
   - Check date of last update on their website

3. **Update Local Database**
   ```bash
   cd /path/to/portable/Visa-Agent
   
   # Open editor
   nano knowledge/live_cutoffs/acs_assessments.json
   # or
   vim knowledge/live_cutoffs/acs_assessments.json
   
   # Update structure:
   {
     "meta": {
       "source": "https://www.acs.org.au/",
       "last_updated": "2026-11-21T10:30:00Z",
       "updated_by": "operator_name"
     },
     "assessments": [
       {
         "qualification": "Bachelor degree",
         "processing_time_weeks": 8,
         "processing_time_note": "As of Nov 2026",
         "fee_aud": 500,
         "url": "https://www.acs.org.au/"
       }
     ]
   }
   ```

4. **Regenerate Daily Digest**
   ```bash
   # This ensures digest includes latest ACS data
   python3 -m runtime.intelligence.digester
   
   # Verify new digest includes ACS section
   tail -30 knowledge/digests/daily_digest_*.md | grep -A 5 "ACS"
   ```

**Checklist:**
- [ ] Visited ACS website and verified latest data
- [ ] Updated `acs_assessments.json` with new processing times
- [ ] Updated `last_updated` timestamp
- [ ] Regenerated daily digest
- [ ] Verified digest includes ACS data
- [ ] Checked no errors in logs

---

### Monday: SkillSelect Weekly Snapshot (15 minutes)

**Every Monday morning, capture latest SkillSelect round:**

1. **Visit SkillSelect Tracker**
   - Go to https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect
   - Look for latest "Invitation Round" information
   - May be under: "Invitation Rounds" → latest date

2. **Extract Data**
   - Note the latest round date (e.g., "Round 15/11/2026")
   - Copy occupation codes and cutoffs (189/190/491 for each state)
   - Note total invitations issued

3. **Update SkillSelect Cutoffs**
   ```bash
   cd /path/to/portable/Visa-Agent
   
   # Edit the cutoffs file
   nano knowledge/live_cutoffs/skillselect_cutoffs.json
   
   # Structure:
   {
     "meta": {
       "source": "https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect",
       "scrape_timestamp": "2026-11-18T10:00:00Z",
       "updated_by": "operator_name",
       "round_date": "2026-11-15T00:00:00Z"
     },
     "cutoffs": [
       {
         "occupation_code": "261311",
         "occupation_name": "Software Engineer",
         "visa_type": "189",
         "cutoff_points": 85,
         "invitations_issued": 250,
         "status": "active"
       }
     ]
   }
   ```

4. **Append to History**
   ```bash
   # Add entry to history file (append-only log)
   cat >> knowledge/live_cutoffs/skillselect_history.jsonl << 'EOF'
   {"date":"2026-11-18","occupation_code":"261311","visa_type":"189","cutoff_points":85,"invitations_issued":250}
   EOF
   
   # Verify appended
   tail -5 knowledge/live_cutoffs/skillselect_history.jsonl
   ```

**Checklist:**
- [ ] Visited SkillSelect website (Monday morning)
- [ ] Extracted all occupation cutoffs
- [ ] Updated `skillselect_cutoffs.json`
- [ ] Appended entry to `skillselect_history.jsonl`
- [ ] Regenerated digest with new data
- [ ] Verified digest shows latest cutoffs

---

### Friday: Archive Old Digests (5 minutes)

```bash
cd /path/to/portable/Visa-Agent

# Archive digests older than 90 days
find knowledge/digests -name "daily_digest_*.md" -mtime +90 -type f | wc -l
# If >0, back them up:
tar -czf backups/digests_archive_$(date +%Y-%m).tar.gz \
  $(find knowledge/digests -name "daily_digest_*.md" -mtime +90)

# Remove after backup
find knowledge/digests -name "daily_digest_*.md" -mtime +90 -delete

# Verify
echo "Remaining digests: $(ls knowledge/digests/daily_digest_*.md | wc -l)"
```

---

## Monthly Responsibilities

### Month-End Verification (2 hours)

**Last Friday of month: Verify scraper accuracy**

1. **Spot-Check DHA Scraper (20 min)**
   ```bash
   cd /path/to/portable/Visa-Agent
   
   # Pick 5 random occupations
   # Against https://immi.homeaffairs.gov.au/visas/working-in-australia/skill-occupation-list
   
   python3 << 'EOF'
   import json
   import random
   
   with open('knowledge/raw_dha/occupation_list_*.json', 'r') as f:
       data = json.load(f)
   
   occupations = data['data'][:100]
   sample = random.sample(occupations, min(5, len(occupations)))
   
   for occ in sample:
       print(f"Verify ANZSCO {occ['occupation_code']}: {occ['occupation_title']}")
       print(f"  Assessing authorities: {occ.get('assessing_authorities', [])}")
       print()
   EOF
   
   # Visit official source and verify each occupation exists
   # Note discrepancies in scraper_spot_checks.jsonl
   ```

2. **Spot-Check State Monitors (20 min)**
   ```bash
   # Sample state quotas
   ls knowledge/live_cutoffs/state_*.json
   
   # Pick 2 states (NSW, VIC)
   # Against official state nomination portals
   
   python3 << 'EOF'
   import json
   
   states = ['NSW', 'VIC']
   for state in states:
       try:
           with open(f'knowledge/live_cutoffs/state_{state}.json') as f:
               data = json.load(f)
           print(f"{state}: {data.get('occupations', {})}")
           print(f"  Last updated: {data.get('meta', {}).get('scrape_timestamp')}")
       except:
           pass
   EOF
   
   # Visit official portal and verify quotas match
   ```

3. **Verify ACS Data (20 min)**
   ```bash
   # Compare ACS data with official website
   # https://www.acs.org.au/
   
   cd /path/to/portable/Visa-Agent
   cat knowledge/live_cutoffs/acs_assessments.json | grep -E "processing_time|fee"
   
   # Note any mismatches
   ```

4. **Calculate False Positive Rate (30 min)**
   ```bash
   python3 << 'EOF'
   import json
   from pathlib import Path
   
   # Check alerts from last 30 days
   alert_files = sorted(Path('knowledge/alerts').glob('*.json'))[-30:]
   
   total_alerts = 0
   false_positives = 0
   
   for alert_file in alert_files:
       with open(alert_file) as f:
           alerts = json.load(f)
       
       for alert in alerts:
           total_alerts += 1
           # Check if 2-day rule confirmed it
           if alert.get('days_confirmed', 0) < 2:
               false_positives += 1
   
   if total_alerts > 0:
       rate = (false_positives / total_alerts) * 100
       print(f"False positive rate: {rate:.1f}% ({false_positives}/{total_alerts})")
       print(f"Target: <5%")
       if rate > 5:
           print("⚠ Above target - investigate scraper accuracy")
   else:
       print("No alerts to analyze")
   EOF
   ```

5. **Update Documentation**
   ```bash
   # Document any issues found
   cat >> knowledge/incidents/monthly_verification_$(date +%Y-%m).md << 'EOF'
   # Monthly Verification Report - YYYY-MM
   
   Date: YYYY-MM-DD
   Verified by: operator_name
   
   ## Spot Checks
   - [ ] DHA occupation list: X discrepancies found
   - [ ] State monitors: X discrepancies found
   - [ ] ACS data: X mismatches found
   
   ## False Positive Rate
   - Last 30 days: X%
   - Status: PASS / FAIL (if >5%)
   
   ## Action Items
   - Item 1
   - Item 2
   
   EOF
   ```

---

## CRITICAL Alert Response

### Alert Severity Levels

| Level | Examples | Response Time | Action |
|---|---|---|---|
| **CRITICAL** | Occupation closed, quota fills early, cutoff spike >10 | Immediate (<30 min) | Verify, notify coordinator, update candidates |
| **SIGNIFICANT** | Cutoff change +5-10 points, new occupation added | Same day (<2 hours) | Review, note in digest, monitor next 2 days |
| **MINOR** | Cutoff change 1-4 points, historical note | Next briefing | Monitor trend, no action needed |

### Checklist for CRITICAL Alert Response

**When you see a CRITICAL alert in the digest:**

1. **Verify against official source (5 min)**
   ```bash
   # Example: Software Engineer (261311) cutoff jumped to 95
   
   # Step 1: Check official SkillSelect website
   # https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect
   # Look for latest round, find occupation 261311, confirm 95 points
   ```

2. **Check 2-day rule confirmation (5 min)**
   ```bash
   # The digest should only alert if change appeared 2 consecutive days
   # Look in digest for "2-day confirmation" note
   
   cat knowledge/digests/daily_digest_*.md | tail -50 | grep -A 3 "Software Engineer"
   # Should show: "Day 1: 85 → Day 2: 95 (CONFIRMED)"
   ```

3. **Review change history (5 min)**
   ```bash
   # Check historical data
   grep '"occupation_code":"261311"' knowledge/live_cutoffs/skillselect_history.jsonl | tail -5
   
   # Should show increasing trend leading to this alert
   ```

4. **Determine impact (5 min)**
   - **If cutoff increased:** Fewer candidates will be invited, waiting time longer
   - **If occupation closed:** No further invitations (status = "no allocation")
   - **If new occupation:** New opportunity for candidates in that field
   - **If quota filled early:** Round may close sooner than expected

5. **Notify Visa Coordinator (5 min)**
   ```bash
   # Email template:
   
   Subject: ⚠️ CRITICAL Alert: Software Engineer cutoff jumped to 95 points
   
   Body:
   Occupation: Software Engineer (261311)
   Visa subclass: 189 (skilled independent)
   Change: 85 → 95 points (confirmed 2 consecutive days)
   Official source: https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect
   Verified: YES
   Date: 2026-11-15
   
   ACTION REQUIRED:
   - Review client profile database for candidates with 189 points for this occupation
   - Consider advising clients to apply for 190 (state sponsorship) if borderline
   - Flag those below 95 points for 189 that this path is closing
   
   Next steps: Monitor this occupation for next 5 days. If trend continues, may signal
   occupation approaching full capacity.
   ```

6. **Document the incident (5 min)**
   ```bash
   cat >> knowledge/incidents/YYYY-MM-DD_critical_alert.md << 'EOF'
   # CRITICAL Alert: Software Engineer Cutoff Spike
   
   Date: 2026-11-15T06:00:00Z
   Occupation: Software Engineer (261311)
   Visa: 189
   Change: 85 → 95 points
   
   ## Verification
   - [x] Confirmed on official SkillSelect website
   - [x] 2-day rule confirmed (Day 14: 85, Day 15: 95)
   - [x] Notified Visa Coordinator
   
   ## Impact
   - Affected clients: ~5 with 189 points for this occupation
   - Recommendation: Encourage 190 state sponsorship path
   
   ## Follow-up
   - [ ] Monitor for next 5 days
   - [ ] Check if trend continues toward closure
   - [ ] If closes: alert all affected clients immediately
   
   Handled by: operator_name
   EOF
   ```

7. **Monitor for next 5 days**
   - Check daily digest for this occupation
   - If cutoff jumps again, escalate to Visa Coordinator
   - If it stabilizes, document conclusion in incident file
   - If occupation closes, create separate alert

### Common CRITICAL Alert Types

#### Type 1: Occupation Closed (No Allocation)

**Symptom in Digest:**
```
⚠️ CRITICAL: Software Engineer (261311) - 189 visa CLOSED
Status changed: active → no_allocation
Invitations issued this round: 0
```

**Response:**
1. Verify on SkillSelect website (look for status = "no allocation")
2. Check if this is permanent or temporary
3. Immediately notify Visa Coordinator
4. Create alert for all clients with this occupation in profile
5. Update client advice: Focus on 190/491 state sponsorship instead

#### Type 2: Cutoff Spike > 10 Points

**Symptom in Digest:**
```
⚠️ CRITICAL: Accountant (221111) - 190 visa cutoff jump
Previous: 75 points → Current: 87 points (confirmed 2 days)
Change: +12 points
```

**Response:**
1. Verify on official state nomination website
2. Check if all states affected or just one
3. Review candidate database for borderline profiles
4. Calculate how many candidates will be affected
5. Notify Visa Coordinator with affected client count

#### Type 3: State Quota Fills Early

**Symptom in Digest:**
```
⚠️ CRITICAL: NSW 190 visa quota FILLED
Expected closure: February 2027
Actual closure: November 2026 (3 months early)
```

**Response:**
1. Verify on NSW state nomination website
2. Check if other states also filling early
3. Review waiting candidates for NSW
4. Recommend alternative states if available
5. Consider 189 independent visa as fallback

#### Type 4: New High-Demand Occupation

**Symptom in Digest:**
```
⚠️ SIGNIFICANT: Data Analyst (261311) - NEW in SkillSelect
Initial cutoff: 75 points (189 visa)
Status: Active, strong allocation
```

**Response:**
1. Not typically CRITICAL unless very high demand
2. Review client database for this occupation
3. Flag as opportunity for those qualified
4. Monitor cutoff trend over next 2-4 weeks
5. Update client advice: "This is a growing opportunity"

---

## Manual Data Updates

### Cost Aggregator: Visa Fees Update

**When:** When Home Affairs announces fee changes (typically annually)  
**Source:** https://immi.homeaffairs.gov.au/help-support/fees

1. **Download fee schedule**
   - Visit Home Affairs visa fees page
   - Download official fee PDF or take screenshots

2. **Update local database**
   ```bash
   nano knowledge/australia/visa_costs.json
   ```

3. **Structure:**
   ```json
   {
     "meta": {
       "source": "https://immi.homeaffairs.gov.au/",
       "last_updated": "2026-11-15T00:00:00Z",
       "updated_by": "operator_name",
       "effective_date": "2026-11-15"
     },
     "visa_costs": {
       "subclass_189": {
         "name": "Skilled Independent",
         "base_fee_aud": 4290,
         "per_family_member": 2145,
         "currency": "AUD"
       },
       "subclass_190": {
         "name": "Skilled Nominated",
         "base_fee_aud": 4290,
         "per_family_member": 2145
       }
     }
   }
   ```

4. **Regenerate digest**
   ```bash
   python3 -m runtime.intelligence.digester
   ```

### SkillSelect Tracker: Occupation History

**Manual weekly tracking (takes 10-15 minutes):**

```bash
# Visit: https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect

# In your terminal, append new entry:
cat >> knowledge/live_cutoffs/skillselect_history.jsonl << 'EOF'
{"date":"YYYY-MM-DD","round_number":"N","occupation_code":"XXXXXX","occupation_name":"Job Title","visa_subclass":"189","cutoff_points":XX,"invitations_issued":XXX,"status":"active"}
EOF

# Repeat for each occupation in the latest round
```

### State Quotas: Manual Fallback

**If state monitor scraper fails, update manually:**

```bash
# Visit state nomination website (example: NSW)
# https://www.iatskillselect.immi.gov.au/

# Update file:
nano knowledge/live_cutoffs/state_NSW.json

# Structure:
{
  "meta": {
    "state": "NSW",
    "scrape_timestamp": "2026-11-15T10:00:00Z",
    "source": "https://www.iatskillselect.immi.gov.au/",
    "note": "Manual update - scraper offline"
  },
  "occupations": [
    {
      "occupation_code": "261311",
      "occupation_name": "Software Engineer",
      "visa_subclass": "190",
      "quota_remaining": 45,
      "cutoff_points": 85,
      "last_updated": "2026-11-15T10:00:00Z"
    }
  ]
}
```

---

## Monitoring & Escalation

### Daily Monitoring Checklist

**In your calendar each morning at 0600 UTC:**

- [ ] Read digest for CRITICAL alerts
- [ ] Check data quality warnings
- [ ] Verify no scraper failures (2+ consecutive days)
- [ ] Note any occupation changes matching client profiles
- [ ] Update status log: `echo "$(date): Briefing complete" >> logs/operator_briefing.log`

### Weekly Escalation

| Issue | Escalation Path | Action |
|---|---|---|
| Scraper failure 2+ days | DevOps lead | Run manual test, provide logs |
| CRITICAL alert verified | Visa Coordinator | Provide digest extract + official source link |
| False positive alert | Data team | Investigate 2-day rule, check CSS selectors |
| Disk space >80% | System admin | Archive old data, expand storage |
| New occupation field added | Product team | Verify scraper handles new field, update schema |

### Escalation Email Template

```
To: visa-coordinator@company.com
Subject: ⚠️ CRITICAL Alert - [Occupation Name] [Action Required]

Details:
- Occupation: [Name] ([ANZSCO Code])
- Visa subclass: [189/190/491]
- Change: [Previous value] → [Current value]
- Severity: CRITICAL
- Verified: YES (link to official source)
- Date: [YYYY-MM-DD HH:MM:SS UTC]

Action Required:
1. Review affected client profiles
2. [Specific action for this alert type]
3. Notify affected candidates

Attached: digest extract, verification screenshot

Questions: Contact Visa Agent Operator
```

---

## Common Issues & Quick Fixes

### Issue 1: Digest Shows Old Data (Appears to Be Yesterday's)

**Cause:** Scraper failed, digester used fallback data

**Quick Fix:**
```bash
# Check scraper logs
tail -30 logs/scraper.log | grep -E "error|fail|timeout"

# If site down, check status
curl -I https://immi.homeaffairs.gov.au/ 2>&1 | head -3

# Manually trigger scraper
cd /path/to/portable/Visa-Agent
python3 -m runtime.scrapers.dha_scraper --all --verbose

# Regenerate digest
python3 -m runtime.intelligence.digester

# Verify new digest
cat knowledge/digests/daily_digest_$(date +%Y-%m-%d).md | head -30
```

**Prevention:** Check scraper logs every morning for errors.

---

### Issue 2: ACS Data Looks Outdated (From 2 Months Ago)

**Cause:** ACS data not being updated (it requires manual weekly update)

**Quick Fix:**
```bash
# Visit https://www.acs.org.au/
# Copy current processing times and fees

# Update local file
nano knowledge/live_cutoffs/acs_assessments.json

# Regenerate digest
python3 -m runtime.intelligence.digester

# Verify includes new data
tail -20 knowledge/digests/daily_digest_*.md | grep -A 3 "ACS"
```

**Prevention:** Set calendar reminder for Fridays at 1000 UTC.

---

### Issue 3: Alert for Occupation Closing, But Website Shows Still Active

**Cause:** Possible data stale, web scraper missed occupation, or site changed HTML

**Quick Fix:**
```bash
# Manually check SkillSelect website
# https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect

# If occupation IS active:
# 1. Note discrepancy in logs
# 2. Manually update skillselect_cutoffs.json with correct status
# 3. Check CSS selector in dha_scraper.py for changes

# If occupation IS closed:
# 1. Verify on 2-3 different sections of website
# 2. Alert is correct, proceed with CRITICAL response

# Document the incident
cat >> knowledge/incidents/data_discrepancy_$(date +%Y-%m-%d).md << 'EOF'
Occupation: [Name]
Reported status: [Closed/Status Changed]
Actual status: [Active/Closed]
Root cause: [Scraper missed, website changed, delay in updating]
Resolution: [Manual update / CSS selector fix / etc]
EOF
```

---

### Issue 4: State Monitor Missing Data (Only 6 of 8 States)

**Cause:** State portal offline, CSS selector changed, or parsing error

**Quick Fix:**
```bash
# Manually check state portals
# Visit each state nomination website

# Update manually for missing states
nano knowledge/live_cutoffs/state_VIC.json  # Example: Victoria missing

# Copy data from official portal into JSON

# Note in meta field
{
  "meta": {
    "state": "VIC",
    "scrape_timestamp": "2026-11-15T10:30:00Z",
    "note": "Manual update - scraper offline 2026-11-15 to 2026-11-16"
  },
  ...
}

# Regenerate digest
python3 -m runtime.intelligence.digester

# Alert to DevOps about scraper issue
```

---

### Issue 5: Too Many False CRITICAL Alerts (More Than 5 in One Week)

**Cause:** 2-day rule not working correctly, or real volatility in data

**Quick Fix:**
```bash
# Analyze alert frequency
python3 << 'EOF'
import json
from pathlib import Path
from collections import defaultdict

# Load last 7 days of digests
critical_count = defaultdict(int)
for digest in sorted(Path('knowledge/digests').glob('daily_digest_*.md'))[-7:]:
    content = digest.read_text()
    critical_count[digest.name] = content.count('⚠️ CRITICAL')

for digest, count in sorted(critical_count.items()):
    print(f"{digest}: {count} CRITICAL alerts")

total = sum(critical_count.values())
print(f"\nTotal this week: {total}")
if total > 5:
    print("⚠ Above normal frequency - check for scraper instability")
EOF

# Check scraper logs for data inconsistencies
tail -100 logs/scraper.log | grep -i "error\|parse\|fail"

# If scraper is unstable, contact DevOps
```

---

## Sign-Off Checklist (After First Week)

- [ ] Completed 5 daily briefings (Mon-Fri)
- [ ] Performed Friday ACS update
- [ ] Performed Monday SkillSelect update
- [ ] Responded to at least 1 CRITICAL alert (real or test)
- [ ] Escalated to Visa Coordinator successfully
- [ ] Reviewed Troubleshooting Guide
- [ ] Confirmed all 141+ tests passing
- [ ] Set up calendar reminders for recurring tasks
- [ ] Reviewed incident response procedures
- [ ] Trained colleague for backup coverage

---

## Quick Reference

### Key File Locations
```
Daily digest:          knowledge/digests/daily_digest_YYYY-MM-DD.md
SkillSelect cutoffs:   knowledge/live_cutoffs/skillselect_cutoffs.json
SkillSelect history:   knowledge/live_cutoffs/skillselect_history.jsonl
ACS data:              knowledge/live_cutoffs/acs_assessments.json
Visa fees:             knowledge/australia/visa_costs.json
Scraper logs:          logs/scraper.log
Digester logs:         logs/digester.log
Error log:             knowledge/live_cutoffs/scraper_errors.jsonl
Incidents:             knowledge/incidents/YYYY-MM-DD_incident.md
```

### Key Commands
```bash
# View today's digest
cat knowledge/digests/daily_digest_$(date +%Y-%m-%d).md

# Check scraper status
tail -50 logs/scraper.log

# Regenerate digest manually
python3 -m runtime.intelligence.digester

# Test ACS poller
python3 -m runtime.scrapers.acs_poller --verbose

# View last error
tail -1 knowledge/live_cutoffs/scraper_errors.jsonl | python3 -m json.tool
```

### Emergency Numbers
- **DevOps Team:** [contact info]
- **Visa Coordinator:** [contact info]
- **On-call Support:** [contact info]

---

**Document Version:** 1.0  
**Last Tested:** 2026-11-15  
**Next Review:** 2026-12-15  
**Feedback:** Share suggestions with product team
