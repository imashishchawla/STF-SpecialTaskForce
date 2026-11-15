# Visa Agent: Troubleshooting Guide

**Version:** 1.0  
**Last Updated:** 2026-11-15  
**Audience:** Operators, Developers, DevOps  

---

## Quick Diagnostic Flowchart

```
Is the system working?
├─ NO digest today?
│  └─→ Section 1: "No Daily Digest Generated"
├─ Digest appears stale (yesterday's data)?
│  └─→ Section 2: "Scraper Failed Silently"
├─ CRITICAL alert, but data looks wrong?
│  └─→ Section 3: "False Positive Alerts"
├─ Missing state (only 6 of 8)?
│  └─→ Section 4: "State Monitor Partial Failure"
├─ ACS data outdated (months old)?
│  └─→ Section 5: "Manual Update Not Running"
├─ Cron jobs never ran (no logs)?
│  └─→ Section 6: "Cron Not Executing"
└─ Tests failing (after deployment)?
   └─→ Section 7: "Test Suite Failures"
```

---

## Common Issues & Solutions

### Issue 1: No Daily Digest Generated

**Symptom:**
- `knowledge/digests/daily_digest_YYYY-MM-DD.md` doesn't exist
- Time is past 0600 UTC, but operator sees no digest
- Digest folder exists but is empty or has only old files

**Root Causes:** (In order of likelihood)
1. Digester failed to run (cron didn't execute)
2. Scraper failed, digester never started
3. Disk full (no space to write digest)
4. Permission denied on `knowledge/digests/` folder
5. Python environment broken or outdated

**Diagnostic Steps:**

```bash
cd /path/to/portable/Visa-Agent

# Step 1: Check if digester process is still running
ps aux | grep digester
# If showing: "[user] python3 -m runtime.intelligence.digester"
# → Digester is still running, wait 5 more minutes

# Step 2: Check digester logs
tail -100 logs/digester.log

# Expected: "Loading data sources for 2026-11-15"
# Or actual error message

# Step 3: Check digest folder permissions
ls -ld knowledge/digests/
# Should show: drwxr-xr-x (755)
# If not, fix with: chmod 755 knowledge/digests

# Step 4: Check disk space
df -h . | tail -1
# Should show >100MB available

# Step 5: Verify scraper data exists
ls -lh knowledge/live_cutoffs/skillselect_cutoffs.json
# Should be dated today
```

**Solutions by Root Cause:**

**If cron didn't execute:**
```bash
# Check crontab is set up
crontab -l | grep digester

# Check system logs
tail -50 /var/log/syslog | grep CRON

# If missing from crontab, re-add:
crontab -e
# Add: 0 5 * * * cd /path && python3 -m runtime.intelligence.digester >> logs/digester.log 2>&1

# Force restart cron
sudo service cron restart  # Linux
sudo launchctl unload /System/Library/LaunchDaemons/com.vix.cron.plist  # macOS
sudo launchctl load /System/Library/LaunchDaemons/com.vix.cron.plist
```

**If scraper failed:**
```bash
# Check scraper logs
tail -100 logs/scraper.log

# Manually run scraper
python3 -m runtime.scrapers.dha_scraper --all --verbose 2>&1 | tail -50

# If timeout, check site status
curl -I https://immi.homeaffairs.gov.au/ --max-time 10

# Retry after 30 minutes, or use fallback from Section 2
```

**If disk is full:**
```bash
# See Section: "Disk Space Critical"
du -sh knowledge/ logs/ backups/
# Find largest directory and clean up

# Temporarily fix:
rm -rf logs/*.log.gz  # Compressed old logs
rm -rf knowledge/raw_dha/*_*.json  # Old scraper data >30 days
```

**If permission denied:**
```bash
# Fix permissions recursively
chmod -R u+w knowledge/digests
chmod -R u+w logs/

# If still fails, check owner
ls -l knowledge/digests/
# Must match current user: whoami

# If not, change owner
sudo chown -R $(whoami):$(whoami) knowledge/ logs/
```

**If Python broken:**
```bash
# Test Python environment
python3 -c "import sys; print(sys.version)"
# Should show Python 3.10+

# Test imports
python3 -c "from runtime.intelligence import IntelligenceDigester; print('✓')"

# If import fails, reinstall dependencies
python3 -m pip install --upgrade -r requirements.txt
```

**Fallback: Manual Digest Generation**

```bash
# If automated digest is broken, manually trigger:
cd /path/to/portable/Visa-Agent

python3 << 'EOF'
from runtime.intelligence import IntelligenceDigester

digester = IntelligenceDigester()
digester.load_sources()
digester.compare_with_yesterday()
digester.score_anomalies()
digest_content = digester.generate_markdown_digest()
print(digest_content)

# Save to file
with open(f'knowledge/digests/daily_digest_{digester.today_date}.md', 'w') as f:
    f.write(digest_content)

print(f"✓ Manual digest generated: knowledge/digests/daily_digest_{digester.today_date}.md")
EOF
```

---

### Issue 2: Digest Shows Yesterday's Data (Scraper Failed Silently)

**Symptom:**
- Digest exists, but shows data from yesterday or 2+ days ago
- Digest has warning: "⚠ Using previous day's data - scraper offline"
- No errors in cron logs, but scraper didn't update files

**Root Causes:** (In order of likelihood)
1. Home Affairs website timeout or down (1-5% of requests fail)
2. CSS selectors changed on website (regular maintenance breaks scraper)
3. Network connectivity issue (ISP, DNS, proxy)
4. Scraper hung on specific endpoint (needs manual restart)

**Diagnostic Steps:**

```bash
cd /path/to/portable/Visa-Agent

# Step 1: Check scraper output freshness
ls -lh knowledge/raw_dha/visa_finder_*.json | tail -3
# Should show today's date, if yesterday or earlier = scraper failed

# Step 2: Check scraper logs for errors
tail -50 logs/scraper.log | grep -E "error|timeout|fail|connection"
# Look for specific endpoint that failed

# Step 3: Test manual scraper run
python3 -m runtime.scrapers.dha_scraper --target visa_finder --verbose
# Note any errors or timeouts

# Step 4: Check if Home Affairs website is up
curl -I https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect -m 10
# Should return: HTTP/1.1 200 OK (or 301 redirect)

# Step 5: Check network connectivity
ping 8.8.8.8 -c 1  # Test DNS
curl -I https://www.acs.org.au/ -m 5  # Test alternate site
```

**Solutions by Root Cause:**

**If Home Affairs is timing out:**
```bash
# Increase timeout and retry
python3 << 'EOF'
from runtime.scrapers import DHAScraper

# Scraper has 3 retries + 30s timeout built in
# If still failing after 3 retries, wait 30 min and retry
scraper = DHAScraper(verbose=True)

# Try specific endpoint
try:
    visa_finder = scraper.scrape_visa_finder()
    print("✓ Scraper successful")
except TimeoutError:
    print("✗ Still timing out - site may be down")
    print("  Fallback: Use previous day's data")
EOF

# Check site status
# Visit: https://immi.homeaffairs.gov.au/
# If site is up but slow, retry in 1 hour
```

**If CSS selectors changed:**
```bash
# This is common when websites update UI
# Scraper logs will show: "Could not parse element" or "No matches found"

# Step 1: Check recent changes
git log --oneline runtime/scrapers/dha_scraper.py | head -5

# Step 2: Compare against website
# Visit: https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect
# Right-click → Inspect Element
# Check if CSS classes/IDs are different from code

# Step 3: Update CSS selector in scraper
nano runtime/scrapers/dha_scraper.py
# Find the parse section (around line 150-200)
# Update CSS selectors to match current website HTML

# Step 4: Test the fix
python3 -m runtime.scrapers.dha_scraper --target skillselect --verbose

# Step 5: Regenerate digest
python3 -m runtime.intelligence.digester

# Step 6: Commit fix
git add runtime/scrapers/dha_scraper.py
git commit -m "fix: update CSS selectors for Home Affairs website changes"
```

**If network is unreliable:**
```bash
# Add manual retries with longer delays
bash << 'EOF'
cd /path/to/portable/Visa-Agent

for attempt in 1 2 3; do
    echo "Attempt $attempt..."
    
    if python3 -m runtime.scrapers.dha_scraper --all --verbose; then
        echo "✓ Scraper successful on attempt $attempt"
        python3 -m runtime.intelligence.digester
        exit 0
    fi
    
    if [ $attempt -lt 3 ]; then
        echo "Retry in 5 minutes..."
        sleep 300
    fi
done

echo "✗ Scraper failed after 3 attempts"
echo "Check network connectivity and Home Affairs website status"
EOF
```

**Fallback: Use Previous Day's Data**

```bash
# If scraper keeps failing after 24 hours, use fallback
cd /path/to/portable/Visa-Agent

YESTERDAY_DIGEST="knowledge/digests/daily_digest_$(date -d '1 day ago' +%Y-%m-%d).md"
TODAY_DIGEST="knowledge/digests/daily_digest_$(date +%Y-%m-%d).md"

if [ -f "$YESTERDAY_DIGEST" ]; then
    cp "$YESTERDAY_DIGEST" "$TODAY_DIGEST"
    
    # Mark as stale
    sed -i '1s/^/⚠️ STALE DATA: This digest uses yesterdays data because the scraper failed.\n\n/' "$TODAY_DIGEST"
    
    echo "✓ Fallback digest created from yesterday"
else
    echo "✗ No previous digest to use as fallback"
fi
```

---

### Issue 3: False CRITICAL Alerts (Cutoff Change Appears, Then Disappears)

**Symptom:**
- Digest shows: "⚠️ CRITICAL: Software Engineer cutoff 85 → 95"
- Next day's digest shows cutoff back to 85
- Alert causes unnecessary panic/communication to clients

**Root Causes:**
1. Scraper returned stale data (HTML cache issue)
2. Website was in transition (temporary state while updating)
3. CSS selector bug (parsing wrong field)
4. SkillSelect history not updated correctly

**Diagnostic Steps:**

```bash
cd /path/to/portable/Visa-Agent

# Step 1: Check history for this occupation
grep '"occupation_code":"261311"' knowledge/live_cutoffs/skillselect_history.jsonl | tail -5
# Should show smooth progression, not wild swings

# Step 2: Check if 2-day rule was applied
tail -50 knowledge/digests/daily_digest_*.md | grep -A 3 "Software Engineer"
# Should say "confirmed 2 consecutive days"

# Step 3: Visit website manually and verify current cutoff
# https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect
# Find Software Engineer, note actual cutoff

# Step 4: Check scraper output (raw data)
python3 << 'EOF'
import json
files = sorted(glob.glob('knowledge/raw_dha/skillselect_*.json'))[-3:]
for f in files:
    with open(f) as fp:
        data = json.load(fp)
    for occ in data.get('data', []):
        if occ.get('occupation_code') == '261311':
            print(f"{f}: {occ['occupation_name']} = {occ.get('cutoff_points', 'N/A')} points")
EOF
```

**Solutions:**

**If scraper returned stale data:**
```bash
# Problem: Website had cached version
# Solution: Force fresh scrape (bypassing browser cache)

python3 << 'EOF'
from runtime.scrapers import DHAScraper

scraper = DHAScraper(verbose=True)
# Add fresh=True to skip caching (if implemented)
result = scraper.scrape_skillselect(headers={
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
})
print(json.dumps(result, indent=2))
EOF
```

**If 2-day rule not working:**
```bash
# Check logic in digester
nano runtime/intelligence/digester.py
# Search for: "2_day_confirmation" or "days_confirmed"

# The rule should only alert if:
# Day N-1: cutoff was X
# Day N: cutoff is Y (where Y != X)
# Day N+1: cutoff still Y (confirms change)

# If history is broken, rebuild from SkillSelect history
python3 << 'EOF'
import json
from pathlib import Path

history_file = Path('knowledge/live_cutoffs/skillselect_history.jsonl')

# Validate history integrity
with open(history_file) as f:
    lines = f.readlines()

previous_date = None
anomalies = []

for line_num, line in enumerate(lines):
    try:
        entry = json.loads(line)
        current_date = entry.get('date')
        
        # Check if dates are chronological
        if previous_date and current_date < previous_date:
            anomalies.append(f"Line {line_num}: Date went backwards ({previous_date} → {current_date})")
        
        previous_date = current_date
    except json.JSONDecodeError:
        anomalies.append(f"Line {line_num}: Invalid JSON")

if anomalies:
    print("⚠ History anomalies found:")
    for a in anomalies:
        print(f"  {a}")
else:
    print("✓ History looks good")
EOF
```

**Prevention:**

```bash
# Add validation to digester before alerting
# Update: runtime/intelligence/digester.py

# Before generating CRITICAL alert, check:
# 1. Cutoff change appeared 2 consecutive days (already done)
# 2. Cutoff change matches pattern (not wild swing like 85 → 95 → 85)
# 3. Web page confirms current state

# Example validation:
def validate_alert_credibility(occupation_code, previous_cutoff, current_cutoff):
    """Validate alert before marking CRITICAL"""
    
    # Check history for this occupation (last 7 days)
    history = get_history_for_occupation(occupation_code, days=7)
    
    # Check if change is consistent with trend
    if current_cutoff < min([h['cutoff'] for h in history[-5:]]):
        # Cutoff dropped below recent minimum = suspicious
        return False
    
    # Check if change is too large (>15 points is rare)
    if abs(current_cutoff - previous_cutoff) > 15:
        # May be false positive, require manual verification
        return 'UNCONFIRMED'
    
    return True  # Looks legitimate
```

---

### Issue 4: State Monitor Missing Data (Only 6 of 8 States)

**Symptom:**
- Digest shows: "⚠ State monitors: 6 of 8 states available"
- Missing: VIC and NSW (or other states)
- Digest says: "State Monitor PARTIAL - retry manually"

**Root Causes:** (In order of likelihood)
1. State portal temporarily down or unreachable
2. CSS selectors broke (state portal redesigned)
3. Scraper timeout on specific states
4. State portal requires JavaScript (BeautifulSoup can't parse)

**Diagnostic Steps:**

```bash
cd /path/to/portable/Visa-Agent

# Step 1: Check which states are missing
ls knowledge/live_cutoffs/state_*.json | wc -l
# Should show 8, if less = some states failed

# Step 2: Manually check each state portal
# NSW: https://www.iatskillselect.immi.gov.au/
# VIC: https://www.liveinvictoria.vic.gov.au/
# ... (check others)

# Step 3: Run state monitor manually with verbose output
python3 -m runtime.scrapers.state_monitor --all --verbose 2>&1 | head -100

# Step 4: Check state monitor logs
tail -50 logs/state_monitor.log | grep -E "error|fail|timeout"
```

**Solutions:**

**If state portal is down:**
```bash
# Temporarily use previous day's data
bash << 'EOF'
for state in NSW VIC; do
    if [ ! -f "knowledge/live_cutoffs/state_$state.json" ]; then
        # Find most recent version
        PREVIOUS=$(ls -1 knowledge/live_cutoffs/state_${state}_*.json 2>/dev/null | tail -1)
        
        if [ -f "$PREVIOUS" ]; then
            cp "$PREVIOUS" "knowledge/live_cutoffs/state_$state.json"
            echo "✓ Using fallback for $state: $PREVIOUS"
        fi
    fi
done
EOF

# Regenerate digest
python3 -m runtime.intelligence.digester
```

**If CSS selectors broke:**
```bash
# State portals change HTML frequently
# Fix: Update CSS selectors in state_monitor.py

nano runtime/scrapers/state_monitor.py

# Find the CSS selector (around line 100-200)
# Example (NSW):
# OLD: selector = "table tr td:nth-child(2)"
# NEW: selector = "div.quota-table tbody tr td.occupation"

# Test with curl/inspect element on website
# Then update and test:

python3 -m runtime.scrapers.state_monitor --target NSW --verbose

# Commit fix
git add runtime/scrapers/state_monitor.py
git commit -m "fix: update NSW state portal CSS selectors after redesign"
```

**If portal requires JavaScript:**
```bash
# BeautifulSoup only reads static HTML
# Portals with JavaScript rendering are harder to scrape

# Option 1: Use Selenium (browser automation)
pip install selenium

# Option 2: Use JavaScript extraction (if API available)
# Check if portal has JSON API endpoint

# Option 3: Manual fallback (operator updates manually)
cat > knowledge/live_cutoffs/state_NSW_MANUAL.json << 'EOF'
{
  "meta": {
    "state": "NSW",
    "source": "https://www.iatskillselect.immi.gov.au/",
    "updated_by": "operator",
    "update_timestamp": "2026-11-15T10:00:00Z",
    "note": "Manual update - portal requires JavaScript"
  },
  "occupations": [
    {
      "occupation_code": "261311",
      "occupation_name": "Software Engineer",
      "visa_subclass": "190",
      "quota_remaining": 50,
      "cutoff_points": 85
    }
  ]
}
EOF
```

---

### Issue 5: ACS Data Outdated (Shows Fees From 2 Months Ago)

**Symptom:**
- Digest shows ACS processing time: "8 weeks (as of September 2026)"
- Current date is November 2026
- ACS data not updating automatically

**Root Cause:**
- ACS data requires manual updates (not automated in scraper)
- Operator forgot to update (or unaware of requirement)

**Solution:**

```bash
cd /path/to/portable/Visa-Agent

# Step 1: Visit ACS website
# https://www.acs.org.au/ → Resources → MSA InfoHub

# Step 2: Record current data (fees, processing times)

# Step 3: Update local file
cat > knowledge/live_cutoffs/acs_assessments.json << 'EOF'
{
  "meta": {
    "source": "https://www.acs.org.au/",
    "last_updated": "2026-11-15T10:30:00Z",
    "updated_by": "operator_name"
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
    }
  ]
}
EOF

# Step 4: Regenerate digest to include new ACS data
python3 -m runtime.intelligence.digester

# Verify digest now shows new ACS data
grep -A 5 "ACS Processing" knowledge/digests/daily_digest_*.md | tail -10
```

**Prevention:**

```bash
# Set up automatic reminder
# Add to calendar: "Update ACS data" every Friday at 1000 UTC
# Or add cron job reminder:
# 0 10 * * 5 echo "Remember: Update ACS data at https://www.acs.org.au/" | mail -s "ACS Update Reminder" operator@company.com
```

---

### Issue 6: Cron Jobs Never Executed (No Logs, No Digests Generated)

**Symptom:**
- No logs in `logs/scraper.log`, `logs/digester.log`
- No digests generated for 3+ days
- Manual scraper run works fine

**Root Causes:** (In order of likelihood)
1. Crontab not configured (operator forgot to add it)
2. Cron daemon not running
3. Crontab path wrong (absolute paths needed)
4. Environment variables not set (e.g., PATH, PYTHONPATH)

**Diagnostic Steps:**

```bash
# Step 1: Check if crontab exists
crontab -l | grep digester
# If empty, crontab not configured

# Step 2: Check if cron daemon is running
ps aux | grep cron
# Should show: [daemon] or similar

# Step 3: Check system logs for cron errors
sudo grep CRON /var/log/syslog | tail -10
# Should show: "CMD executed", not errors

# Step 4: Check if manual command works
cd /path/to/portable/Visa-Agent && python3 -m runtime.scrapers.dha_scraper --all
# If this works but cron doesn't, it's an environment issue
```

**Solutions:**

**If crontab not configured:**
```bash
# Add crontab entries
crontab -e

# Paste these lines:
# ===== VISA AGENT PIPELINE =====
# Run at 0300 UTC
0 3 * * * cd /absolute/path/to/portable/Visa-Agent && /usr/bin/python3 -m runtime.scrapers.dha_scraper --all >> logs/scraper.log 2>&1
0 3 * * * cd /absolute/path/to/portable/Visa-Agent && /usr/bin/python3 -m runtime.scrapers.state_monitor --all >> logs/state_monitor.log 2>&1
0 3 * * * cd /absolute/path/to/portable/Visa-Agent && /usr/bin/python3 -m runtime.scrapers.acs_poller >> logs/acs_poller.log 2>&1

# Run at 0500 UTC (after scrapers)
0 5 * * * cd /absolute/path/to/portable/Visa-Agent && /usr/bin/python3 -m runtime.intelligence.digester >> logs/digester.log 2>&1
# ================================

# Save and verify
crontab -l | grep visa
```

**If cron daemon not running:**
```bash
# Linux
sudo service cron status
# If stopped:
sudo service cron start
sudo service cron enable  # Auto-start on reboot

# macOS
sudo launchctl list | grep cron
# If not listed:
sudo launchctl load /System/Library/LaunchDaemons/com.vix.cron.plist
```

**If path is wrong:**
```bash
# Problem: Cron uses minimal PATH, Python might not be found
# Solution: Use absolute path to python3

which python3
# Example output: /usr/local/bin/python3

# Update crontab to use absolute path:
crontab -e

# Change:
# FROM: python3 -m runtime.scrapers.dha_scraper
# TO:   /usr/local/bin/python3 -m runtime.scrapers.dha_scraper

# Also verify working directory:
# Add cd command first:
0 3 * * * cd /home/user/STF-SpecialTaskForce/portable/Visa-Agent && /usr/local/bin/python3 ...
```

**If environment variables missing:**
```bash
# Cron runs with minimal environment
# Add env vars to crontab

crontab -e

# Add at the top:
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
HOME=/home/username
PYTHONPATH=/home/username/STF-SpecialTaskForce/portable/Visa-Agent

# Then add jobs below
0 3 * * * cd $HOME/STF-SpecialTaskForce/portable/Visa-Agent && python3 ...
```

**Test cron setup:**
```bash
# Create test job
crontab -e
# Add: * * * * * echo "test" >> /tmp/cron-test.log

# Wait 1 minute, then check:
cat /tmp/cron-test.log
# If file was updated, cron is working

# Then remove test job and re-add real jobs
```

---

### Issue 7: Test Suite Fails After Deployment

**Symptom:**
- `pytest tests/ -v` fails with errors
- Some tests pass, others fail randomly
- Error messages are cryptic

**Root Causes:**
1. Dependencies not installed or wrong version
2. Test data missing or corrupted
3. Temporary files from previous runs interfere
4. Timezone issues (tests expect UTC)

**Diagnostic Steps:**

```bash
cd /path/to/portable/Visa-Agent

# Step 1: Check Python version
python3 --version
# Should be 3.10+ 

# Step 2: Check dependencies
python3 -m pip list | grep -E "pytest|requests|beautifulsoup"
# Should show all packages installed

# Step 3: Run tests with verbose output
pytest tests/ -v --tb=short

# Step 4: Check for specific failing test
pytest tests/test_dha_scraper.py -v
# Identify which test is failing

# Step 5: Run failing test in isolation
pytest tests/test_dha_scraper.py::TestDHAScraperFetch::test_retry_on_timeout -vv
```

**Solutions:**

**If dependencies missing:**
```bash
# Reinstall all dependencies
python3 -m pip install --upgrade --force-reinstall -r requirements.txt

# Verify installation
python3 -c "import requests; import bs4; import pydantic; print('✓ All OK')"

# Run tests again
pytest tests/ -v
```

**If test data corrupted:**
```bash
# Check if fixtures exist
ls tests/fixtures/ 2>/dev/null || echo "No fixtures directory"

# Some tests generate temp files
# Clean up:
rm -rf .pytest_cache/
rm -rf tests/__pycache__/
rm -rf /tmp/visa_agent_test_*

# Re-run tests
pytest tests/ -v
```

**If timezone issues:**
```bash
# Set timezone to UTC
export TZ=UTC
python3 -c "import datetime; print(datetime.datetime.now(datetime.timezone.utc))"

# Run tests with UTC
TZ=UTC pytest tests/ -v

# Add to crontab if needed:
TZ=UTC
0 3 * * * cd /path && TZ=UTC python3 -m runtime.scrapers.dha_scraper
```

**Specific Test Failures:**

**Test: `test_dha_scraper_timeout` fails**
```bash
# This test checks retry logic
# May fail if network is genuinely slow

# Solution: Increase timeout in test
nano tests/test_dha_scraper.py
# Find: timeout=5
# Change to: timeout=30

# Or skip network tests
pytest tests/test_dha_scraper.py -v -m "not network"
```

**Test: `test_digester_2day_rule` fails**
```bash
# This test checks 2-day confirmation rule
# May fail if dates are in the past

# Solution: Check test uses relative dates
nano tests/test_digester.py
# Make sure test uses:
# datetime.now(timezone.utc)  ← relative to current time
# NOT: hardcoded dates like "2026-11-15"

# Re-run test
pytest tests/test_digester.py::test_digester_2day_rule -vv
```

---

## Advanced Troubleshooting

### Disk Space Critical (>80% full)

```bash
cd /path/to/portable/Visa-Agent

# Find largest items
du -sh * | sort -rh | head -10

# Clean up old raw_dha files (>90 days old)
find knowledge/raw_dha -name "*.json" -mtime +90 -delete

# Compress and archive old logs
find logs -name "*.log" -mtime +30 -exec gzip {} \;
mkdir -p backups/logs_archive
mv logs/*.log.gz backups/logs_archive/

# Archive old digests
tar -czf backups/digests_archive_$(date +%Y-%m).tar.gz knowledge/digests/daily_digest_*.md
# Keep only last 30 days
find knowledge/digests -name "*.md" -mtime +30 -delete

# Check freed space
df -h .
```

### Database Corruption (SQLite index)

```bash
cd /path/to/portable/Visa-Agent

# If exists, check state
ls -lh stf.db 2>/dev/null

# Verify integrity
python3 << 'EOF'
import sqlite3
try:
    conn = sqlite3.connect('stf.db')
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM sqlite_master")
    count = cursor.fetchone()[0]
    print(f"✓ Database OK ({count} objects)")
except Exception as e:
    print(f"✗ Database corrupted: {e}")
EOF

# If corrupted, rebuild (loses index only, not source data)
rm stf.db
echo "✓ Index rebuilt on next run"
```

### JSON File Corruption

```bash
cd /path/to/portable/Visa-Agent

# Validate all JSON files
python3 << 'EOF'
import json
from pathlib import Path

bad_files = []
for json_file in Path('knowledge').rglob('*.json'):
    try:
        with open(json_file) as f:
            json.load(f)
    except json.JSONDecodeError as e:
        bad_files.append((json_file, str(e)))

if bad_files:
    print(f"✗ {len(bad_files)} corrupted files:")
    for f, error in bad_files:
        print(f"  {f}: {error}")
else:
    print("✓ All JSON files valid")
EOF

# Fix corrupted files by restoring from git
git checkout HEAD -- knowledge/live_cutoffs/skillselect_cutoffs.json  # Example
```

---

## Quick Reference: Common Commands

```bash
# View latest digest
cat knowledge/digests/daily_digest_$(date +%Y-%m-%d).md | head -50

# Manually run scraper
python3 -m runtime.scrapers.dha_scraper --all --verbose

# Manually run digester
python3 -m runtime.intelligence.digester

# Check logs
tail -100 logs/scraper.log
tail -100 logs/digester.log

# View errors
tail -20 knowledge/live_cutoffs/scraper_errors.jsonl | python3 -m json.tool

# Test specific module
python3 -m pytest tests/test_dha_scraper.py -v

# Check cron status
crontab -l
sudo service cron status

# Check disk space
df -h .
du -sh knowledge/ logs/

# Restart system
python3 -m runtime.intelligence.digester  # Manual trigger
```

---

**Document Version:** 1.0  
**Last Tested:** 2026-11-15  
**Next Review:** 2026-12-15
