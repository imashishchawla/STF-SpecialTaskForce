# Visa Agent Quick Wins + Phase 1: Deployment Guide

**Version:** 1.0  
**Last Updated:** 2026-11-15  
**Status:** Production Ready  

## Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [System Requirements](#system-requirements)
4. [Installation Steps](#installation-steps)
5. [Verification & Testing](#verification--testing)
6. [Scheduler Setup](#scheduler-setup)
7. [Monitoring & Health Checks](#monitoring--health-checks)
8. [Rollback Procedures](#rollback-procedures)
9. [Performance Baselines](#performance-baselines)
10. [Troubleshooting During Deployment](#troubleshooting-during-deployment)

---

## Overview

The Visa Agent Quick Wins + Phase 1 system consists of four integrated components:

1. **DHA Scraper** — Fetches occupation cutoffs, visa info, and SkillSelect rounds from Home Affairs
2. **State Monitor** — Tracks state nomination quotas and cutoff changes across all 8 Australian states
3. **ACS Poller** — Monitors ACS assessment processing times and fees
4. **Intelligence Digester** — Synthesizes daily digest with anomaly detection and alert routing

**Key Features:**
- Automated daily scraping (0300 UTC)
- Intelligent digest generation (0500 UTC)
- 2-day anomaly confirmation rule (prevents false positives)
- Alert routing: CRITICAL / SIGNIFICANT / MINOR
- Comprehensive error logging and fallback strategies
- ~2GB knowledge base for 6+ months of historical data

**Deployment Time:** 30-45 minutes  
**Ongoing Daily Runtime:** 5-10 minutes (automated)  
**Operator Involvement:** 5 min/day (morning briefing) + 15 min/week (manual updates)

---

## Pre-Deployment Checklist

**Before you start, verify:**

- [ ] Python 3.10 or later installed (`python3 --version`)
- [ ] pip package manager available (`python3 -m pip --version`)
- [ ] Git installed (`git --version`)
- [ ] 2 GB free disk space available
- [ ] Internet connectivity to:
  - `immi.homeaffairs.gov.au` (Home Affairs)
  - State nomination portals (NSW, VIC, QLD, WA, SA, TAS, ACT, NT)
  - `acs.org.au` (ACS Assessment Authority)
- [ ] Access to crontab (Linux/macOS) or Task Scheduler (Windows)
- [ ] Terminal/shell access with read/write permissions to deployment directory
- [ ] Log file write permissions (`/var/log/` or equivalent)

**Network Connectivity Test:**
```bash
# Test Home Affairs
curl -I https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect 2>&1 | head -1

# Test ACS
curl -I https://www.acs.org.au/ 2>&1 | head -1

# Verify DNS
nslookup immi.homeaffairs.gov.au
nslookup acs.org.au
```

---

## System Requirements

### Python & Dependencies

**Minimum Python Version:** 3.10  
**Recommended Python Version:** 3.11 or 3.12

**Required Packages:**
```
requests>=2.31.0          # HTTP requests
beautifulsoup4>=4.12.0    # HTML parsing
pydantic>=2.0.0           # Data validation
pytest>=7.0.0             # Testing framework
pytest-mock>=3.10.0       # Test mocking
black>=23.0.0             # Code formatter
flake8>=6.0.0             # Linter
mypy>=1.0.0               # Type checker
```

### Disk Space Requirements

- **Core installation:** ~150 MB
- **Knowledge base (initial):** ~500 MB
- **Log files (monthly):** ~50 MB
- **Digests & alerts:** ~10 MB
- **Historical data (6 months):** ~1.5 GB
- **Reserve buffer:** 500 MB

**Total Recommended:** 2.5-3 GB free space

### Operating System Support

| OS | Status | Notes |
|---|---|---|
| Linux (Ubuntu 20.04+) | ✓ Tested | Primary deployment target |
| macOS (12+) | ✓ Tested | Intel & Apple Silicon supported |
| Windows 11 | ✓ Supported | Use WSL2 or native Python 3.10+ |
| Docker | ✓ Optional | See container deployment section |

---

## Installation Steps

### Step 1: Clone Repository

```bash
# Clone the STF repository
git clone https://github.com/your-org/STF-SpecialTaskForce.git
cd STF-SpecialTaskForce/portable/Visa-Agent

# Verify you're in the correct directory
pwd
# Expected output: /path/to/STF-SpecialTaskForce/portable/Visa-Agent

# Check git status
git status
```

### Step 2: Create Required Directories

```bash
# Create knowledge base structure
mkdir -p knowledge/digests
mkdir -p knowledge/live_cutoffs
mkdir -p knowledge/alerts
mkdir -p knowledge/raw_dha
mkdir -p knowledge/australia
mkdir -p knowledge/incidents

# Create logs directory
mkdir -p logs

# Create backups directory
mkdir -p backups

# Create scripts directory (if not present)
mkdir -p scripts

# Verify directory structure
ls -la knowledge/
```

### Step 3: Install Python Dependencies

```bash
# Upgrade pip to latest version
python3 -m pip install --upgrade pip setuptools wheel

# Install requirements
python3 -m pip install -r requirements.txt

# Verify installation
python3 -c "import requests; import bs4; import pydantic; print('✓ All packages installed')"
```

### Step 4: Verify Installation

```bash
# Check each scraper is importable
python3 -c "from runtime.scrapers import DHAScraper; print('✓ DHA Scraper OK')"
python3 -c "from runtime.scrapers import StateMonitor; print('✓ State Monitor OK')"
python3 -c "from runtime.scrapers import ACSPoller; print('✓ ACS Poller OK')"
python3 -c "from runtime.intelligence import IntelligenceDigester; print('✓ Digester OK')"

# Check point calculator
python3 -c "from runtime import PointsCalculator; print('✓ Points Calculator OK')"

# List all available agents
python3 -c "import os; agents = [f for f in os.listdir('.agents') if f.endswith('.md')]; print(f'✓ Found {len(agents)} agents')"
```

### Step 5: Populate Initial Data

```bash
# Download current visa and occupation lists
python3 -m runtime.scrapers.dha_scraper --all --verbose

# Check for successful scrape
ls -lh knowledge/raw_dha/
# Expected files: visa_finder_YYYY-MM-DD.json, occupation_list_YYYY-MM-DD.json, etc.

# Initialize SkillSelect cutoffs (manual placeholder)
cat > knowledge/live_cutoffs/skillselect_cutoffs.json << 'EOF'
{
  "meta": {
    "source": "https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect",
    "scrape_timestamp": "2026-11-15T00:00:00Z",
    "scrape_status": "initial_setup",
    "row_count": 0
  },
  "cutoffs": []
}
EOF

# Initialize SkillSelect history
cat > knowledge/live_cutoffs/skillselect_history.jsonl << 'EOF'
EOF

# Initialize ACS assessments
cat > knowledge/live_cutoffs/acs_assessments.json << 'EOF'
{
  "meta": {
    "source": "https://www.acs.org.au/",
    "last_updated": "2026-11-15T00:00:00Z",
    "note": "Update manually from ACS website on first Friday of each month"
  },
  "assessments": []
}
EOF

# Initialize visa costs (manual update)
cat > knowledge/australia/visa_costs.json << 'EOF'
{
  "meta": {
    "source": "https://immi.homeaffairs.gov.au/",
    "last_updated": "2026-11-15T00:00:00Z",
    "note": "Update manually from Home Affairs website when fees change"
  },
  "costs": {}
}
EOF

echo "✓ Initial data setup complete"
```

### Step 6: Run Test Suite

```bash
# Run all tests (should pass 141+ tests)
pytest tests/ -v --tb=short

# Run scraper tests specifically
pytest tests/test_dha_scraper.py -v

# Run digester tests
pytest tests/test_digester.py -v

# Run state monitor tests
pytest tests/test_state_monitor.py -v

# Run ACS poller tests
pytest tests/test_acs_poller.py -v
```

**Expected Output:**
```
======================== 141 passed in 8.23s ========================
```

If tests fail, check troubleshooting section below.

### Step 7: Run First Manual Cycle

```bash
# Run DHA scraper
echo "=== Running DHA Scraper ===" 
python3 -m runtime.scrapers.dha_scraper --all --verbose

# Check output
ls -lh knowledge/raw_dha/*.json | tail -5
# Expected: Files dated today with reasonable sizes (>10KB each)

# Run state monitors (if configured)
echo "=== Running State Monitors ===" 
python3 -m runtime.scrapers.state_monitor --all --verbose 2>&1 | head -50

# Run ACS poller
echo "=== Running ACS Poller ===" 
python3 -m runtime.scrapers.acs_poller --verbose 2>&1 | head -50

# Generate first digest
echo "=== Generating Daily Digest ===" 
python3 -m runtime.intelligence.digester

# Check digest was generated
ls -lh knowledge/digests/
# Expected: daily_digest_YYYY-MM-DD.md (>5KB, <100KB)

# View digest
cat knowledge/digests/daily_digest_*.md | head -100
```

---

## Verification & Testing

### Health Check Checklist

```bash
# 1. Verify all scrapers complete without error
[ -f "knowledge/raw_dha/visa_finder_*.json" ] && echo "✓ DHA scraper OK" || echo "✗ DHA scraper FAILED"

# 2. Verify digest exists and has content
[ -f "knowledge/digests/daily_digest_*.md" ] && [ -s "knowledge/digests/daily_digest_*.md" ] && echo "✓ Digest generated" || echo "✗ Digest FAILED"

# 3. Check error logs are minimal
[ ! -f "knowledge/live_cutoffs/scraper_errors.jsonl" ] && echo "✓ No scraper errors" || echo "⚠ Check scraper_errors.jsonl"

# 4. Verify no >2 consecutive scraper failures
error_count=$([ -f "knowledge/live_cutoffs/scraper_errors.jsonl" ] && wc -l < "knowledge/live_cutoffs/scraper_errors.jsonl" || echo 0)
[ "$error_count" -lt 4 ] && echo "✓ Error count acceptable ($error_count)" || echo "⚠ High error count: $error_count"

# 5. Check disk space
available=$(df . | tail -1 | awk '{print $4}')
[ "$available" -gt 2000000 ] && echo "✓ Disk space OK ($(($available/1024/1024))GB)" || echo "✗ CRITICAL: Low disk space!"
```

### Data Quality Validation

```bash
# Validate JSON structure of key files
python3 << 'PYEOF'
import json
from pathlib import Path

files_to_check = [
    'knowledge/raw_dha/visa_finder_*.json',
    'knowledge/live_cutoffs/skillselect_cutoffs.json',
    'knowledge/digests/daily_digest_*.md'
]

base_path = Path('.')
for pattern in files_to_check:
    matches = list(base_path.glob(pattern))
    if not matches:
        print(f"⚠ No files match pattern: {pattern}")
        continue
    
    for filepath in sorted(matches)[-1:]:  # Check latest file only
        if filepath.suffix == '.json':
            try:
                with open(filepath) as f:
                    json.load(f)
                print(f"✓ {filepath.name} - Valid JSON")
            except Exception as e:
                print(f"✗ {filepath.name} - Invalid JSON: {e}")
        elif filepath.suffix == '.md':
            try:
                content = filepath.read_text()
                if len(content) > 1000:  # Digest should be >1KB
                    print(f"✓ {filepath.name} - Valid Markdown ({len(content)} bytes)")
                else:
                    print(f"⚠ {filepath.name} - Digest appears short ({len(content)} bytes)")
            except Exception as e:
                print(f"✗ {filepath.name} - Error: {e}")
PYEOF
```

---

## Scheduler Setup

### Linux/macOS: Cron Setup

```bash
# Edit crontab
crontab -e

# Add these lines (paste into editor):
# ========================= VISA AGENT CRON JOBS =========================
# Run scrapers at 0300 UTC daily (retrieves latest data)
0 3 * * * cd /path/to/portable/Visa-Agent && python3 -m runtime.scrapers.dha_scraper --all >> logs/scraper.log 2>&1
0 3 * * * cd /path/to/portable/Visa-Agent && python3 -m runtime.scrapers.state_monitor --all >> logs/state_monitor.log 2>&1
0 3 * * * cd /path/to/portable/Visa-Agent && python3 -m runtime.scrapers.acs_poller >> logs/acs_poller.log 2>&1

# Generate daily digest at 0500 UTC (after all scrapers complete)
0 5 * * * cd /path/to/portable/Visa-Agent && python3 -m runtime.intelligence.digester >> logs/digester.log 2>&1

# Run health check at 0600 UTC (after digest is ready)
0 6 * * * cd /path/to/portable/Visa-Agent && bash scripts/health_check.sh >> logs/health_check.log 2>&1

# Rotate logs daily at 2300 UTC
0 23 * * * cd /path/to/portable/Visa-Agent && bash scripts/rotate_logs.sh
# ==========================================================================

# Save and exit (in nano: Ctrl+O, Enter, Ctrl+X)
```

**Replace `/path/to/` with your actual deployment path:**
```bash
# Get absolute path
pwd
# Example output: /home/operator/STF-SpecialTaskForce/portable/Visa-Agent
```

**Verify cron jobs:**
```bash
# List active cron jobs
crontab -l

# Monitor next scheduled run
crontab -l | grep visa-agent

# Check system logs for past executions
tail -50 /var/log/syslog | grep CRON
```

### Windows: Task Scheduler Setup

```powershell
# Create basic task (replace paths as needed)
$action = New-ScheduledTaskAction `
  -Execute "python3" `
  -Argument "-m runtime.scrapers.dha_scraper --all" `
  -WorkingDirectory "C:\path\to\portable\Visa-Agent"

$trigger = New-ScheduledTaskTrigger `
  -Daily `
  -At 3:00am

Register-ScheduledTask `
  -TaskName "VisaAgent-DHA-Scraper" `
  -Action $action `
  -Trigger $trigger `
  -RunLevel Highest
```

Or use GUI:
1. Open Task Scheduler
2. Create Basic Task → "VisaAgent-DHA-Scraper"
3. Trigger: Daily at 03:00 UTC
4. Action: Start program `python3` with arguments `-m runtime.scrapers.dha_scraper --all`
5. Conditions: Run only if network available

### Log Rotation Setup

Create `/path/to/portable/Visa-Agent/scripts/rotate_logs.sh`:

```bash
#!/bin/bash
# Log rotation script - compress and archive old logs

LOG_DIR="logs"
ARCHIVE_DIR="logs/archive"
DAYS_TO_KEEP=90

mkdir -p "$ARCHIVE_DIR"

# Rotate log files older than 30 days
find "$LOG_DIR" -maxdepth 1 -name "*.log" -type f -mtime +30 -exec gzip {} \;
find "$LOG_DIR" -maxdepth 1 -name "*.log.gz" -type f -exec mv {} "$ARCHIVE_DIR" \;

# Remove archives older than 90 days
find "$ARCHIVE_DIR" -name "*.log.gz" -type f -mtime +$DAYS_TO_KEEP -delete

echo "$(date): Log rotation complete"
```

Make executable:
```bash
chmod +x scripts/rotate_logs.sh
```

---

## Monitoring & Health Checks

### Daily Health Monitoring

**Manual Daily Check (5 minutes):**

```bash
#!/bin/bash
# Quick health check - run each morning

cd /path/to/portable/Visa-Agent

echo "=== Visa Agent Daily Health Check ==="
echo "Time: $(date)"
echo

# 1. Check digest exists and is fresh
DIGEST=$(ls -1 knowledge/digests/daily_digest_*.md 2>/dev/null | sort | tail -1)
if [ -f "$DIGEST" ]; then
    SIZE=$(wc -c < "$DIGEST")
    MTIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$DIGEST" 2>/dev/null || stat -c %y "$DIGEST" 2>/dev/null | cut -d' ' -f1-2)
    echo "✓ Digest exists: $DIGEST ($SIZE bytes, $MTIME)"
else
    echo "✗ CRITICAL: No digest found!"
fi
echo

# 2. Check for scraper errors
ERROR_FILE="knowledge/live_cutoffs/scraper_errors.jsonl"
if [ -f "$ERROR_FILE" ]; then
    ERROR_COUNT=$(wc -l < "$ERROR_FILE")
    LAST_ERROR=$(tail -1 "$ERROR_FILE")
    echo "⚠ Scraper errors detected ($ERROR_COUNT total):"
    echo "  Last error: $LAST_ERROR" | head -80
else
    echo "✓ No scraper errors logged"
fi
echo

# 3. Check data freshness (should be <24h old)
DHA_FILE=$(ls -1 knowledge/raw_dha/visa_finder_*.json 2>/dev/null | sort | tail -1)
if [ -f "$DHA_FILE" ]; then
    HOURS_AGO=$(( ($(date +%s) - $(stat -f "%m" "$DHA_FILE" 2>/dev/null || stat -c %Y "$DHA_FILE" 2>/dev/null)) / 3600 ))
    if [ "$HOURS_AGO" -lt 24 ]; then
        echo "✓ DHA data fresh ($HOURS_AGO hours old)"
    else
        echo "⚠ DHA data stale ($HOURS_AGO hours old)"
    fi
else
    echo "⚠ No DHA data found"
fi
echo

# 4. Check disk space
AVAILABLE=$(df . | tail -1 | awk '{print $(NF-2)}')
if [ "$AVAILABLE" -gt 2000 ]; then
    echo "✓ Disk space: ${AVAILABLE}MB available"
else
    echo "✗ CRITICAL: Low disk space! ${AVAILABLE}MB remaining"
fi
echo

# 5. Show CRITICAL alerts from digest
if [ -f "$DIGEST" ]; then
    CRITICAL_COUNT=$(grep -c "^### CRITICAL" "$DIGEST" 2>/dev/null || echo 0)
    if [ "$CRITICAL_COUNT" -gt 0 ]; then
        echo "⚠ CRITICAL Alerts ($CRITICAL_COUNT):"
        grep -A 3 "^### CRITICAL" "$DIGEST" | head -20
    else
        echo "✓ No CRITICAL alerts"
    fi
fi
echo

echo "=== End Health Check ==="
```

### Automated Health Monitoring

See `scripts/health_check.sh` for automated daily health check.

### Alert Rules

| Alert | Trigger | Action |
|---|---|---|
| **No Digest Today** | Digest missing after 0600 UTC | Manual trigger digester, check logs |
| **Scraper Failed 2x** | 2 consecutive days of scraper error | Investigate endpoint, notify operator |
| **Data Stale >3 days** | All scrapers offline >72h | Use previous data, escalate |
| **Disk >80%** | Available space <500MB | Archive old logs, clean up |
| **CRITICAL Alert** | Cutoff spike >10 points | Manual review vs. source, notify candidates |

---

## Rollback Procedures

### Scenario 1: Scraper Corrupted Data

**Symptoms:** Invalid JSON in scraper output, digest generation fails

**Recovery Steps:**
```bash
# 1. Restore from git backup
cd /path/to/portable/Visa-Agent
git status

# 2. Identify problematic files
ls -lh knowledge/raw_dha/

# 3. Revert to last known-good state
git checkout HEAD -- knowledge/raw_dha/*.json  # If tracked
# OR manually restore from backup
cp backups/raw_dha_YYYY-MM-DD.tar.gz .
tar -xzf raw_dha_YYYY-MM-DD.tar.gz

# 4. Verify restored data
python3 << 'EOF'
import json
files = ['knowledge/raw_dha/visa_finder_*.json']
for f in files:
    with open(f) as fp:
        json.load(fp)
    print(f"✓ {f} valid")
EOF

# 5. Regenerate digest
python3 -m runtime.intelligence.digester

# 6. Verify digest
ls -lh knowledge/digests/daily_digest_*.md | tail -1
```

### Scenario 2: Digest Generation Failed

**Symptoms:** No digest created, digester times out, invalid output

**Recovery Steps:**
```bash
# 1. Check what data sources are available
ls -lh knowledge/live_cutoffs/skillselect_cutoffs.json
ls -lh knowledge/digests/daily_digest_*.md | tail -1

# 2. Manually trigger digester with debug logging
python3 -m runtime.intelligence.digester --log-level DEBUG

# 3. Check error logs
tail -50 logs/digester.log

# 4. If input files missing, use previous day's digest
YESTERDAY_DIGEST="knowledge/digests/daily_digest_$(date -d '1 day ago' +%Y-%m-%d).md"
if [ -f "$YESTERDAY_DIGEST" ]; then
    echo "Using previous day's digest as fallback"
    cp "$YESTERDAY_DIGEST" "knowledge/digests/daily_digest_$(date +%Y-%m-%d).md"
    # Mark in digest as stale
    sed -i '1s/^/⚠️ STALE DATA - Generated from previous day\n\n/' \
        "knowledge/digests/daily_digest_$(date +%Y-%m-%d).md"
fi

# 5. Verify digest exists
ls -lh knowledge/digests/daily_digest_*.md | tail -1
```

### Scenario 3: Cron Jobs Not Running

**Symptoms:** No logs in `logs/scraper.log`, no digests generated for days

**Recovery Steps:**
```bash
# 1. Verify cron daemon is running
sudo service cron status  # Linux
sudo launchctl list | grep cron  # macOS

# 2. Check crontab is configured
crontab -l | grep visa-agent

# 3. Manually test one cron command
cd /path/to/portable/Visa-Agent
python3 -m runtime.scrapers.dha_scraper --all

# 4. If manual works, check cron environment
# Add verbose logging to crontab:
crontab -e
# Change line to include path setup:
PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/opt/python/bin
0 3 * * * cd /path/to/portable/Visa-Agent && python3 -m runtime.scrapers.dha_scraper --all >> logs/scraper.log 2>&1

# 5. Force cron to re-read
sudo service cron restart  # Linux
sudo launchctl unload /System/Library/LaunchDaemons/com.vix.cron.plist  # macOS
sudo launchctl load /System/Library/LaunchDaemons/com.vix.cron.plist

# 6. Verify next execution time
crontab -l
```

### Scenario 4: Out-of-Disk Space

**Symptoms:** Scraper fails with "No space left on device", digest missing

**Recovery Steps:**
```bash
# 1. Find largest files/directories
du -sh knowledge/* | sort -h | tail -10
du -sh logs/* | sort -h | tail -10

# 2. Backup and archive old digests
tar -czf backups/digests_archive_$(date +%Y-%m).tar.gz knowledge/digests/
# Keep only last 30 days
find knowledge/digests -name "*.md" -mtime +30 -delete

# 3. Compress old logs
find logs -name "*.log" -mtime +7 -exec gzip {} \;
find logs -name "*.log.gz" -mtime +90 -delete

# 4. Archive raw_dha if >1GB
if [ $(du -s knowledge/raw_dha | cut -f1) -gt 1000000 ]; then
    tar -czf backups/raw_dha_archive_$(date +%Y-%m).tar.gz knowledge/raw_dha/
    # Keep only last 90 days of raw_dha
    find knowledge/raw_dha -name "*.json" -mtime +90 -delete
fi

# 5. Check freed space
df -h .
```

---

## Performance Baselines

### Expected Runtimes

| Component | Runtime | Notes |
|---|---|---|
| DHA Scraper | 2-3 min | Single endpoint, retry logic included |
| State Monitors | 3-5 min | Parallel for 8 states, CSS parsing |
| ACS Poller | 1-2 min | Single endpoint, minimal data |
| Digester | 3-5 min | Includes anomaly detection, report generation |
| **Total Pipeline** | **5-10 min** | All 4 running sequentially |

### Actual Runtime Tracking

Add to `logs/performance.json`:

```json
{
  "2026-11-15T03:00:00Z": {
    "dha_scraper": 2.5,
    "state_monitor": 4.2,
    "acs_poller": 1.8,
    "digester": 4.1,
    "total": 12.6
  }
}
```

**Performance analysis script:**

```bash
#!/bin/bash
# Extract timing from logs

if [ ! -f "logs/performance.json" ]; then
    echo "No performance data yet"
    exit 0
fi

# Python script to analyze
python3 << 'EOF'
import json
from pathlib import Path
from statistics import mean, stdev

perf_file = Path('logs/performance.json')
if not perf_file.exists():
    print("No performance data")
    exit(0)

with open(perf_file) as f:
    data = json.load(f)

# Get last 30 days of data
recent = {k: v for k, v in list(data.items())[-30:]}

if not recent:
    print("Insufficient data")
    exit(0)

components = ['dha_scraper', 'state_monitor', 'acs_poller', 'digester']
for comp in components:
    times = [v[comp] for v in recent.values() if comp in v]
    if times:
        print(f"{comp:20} avg={mean(times):6.2f}s  min={min(times):6.2f}s  max={max(times):6.2f}s  stdev={stdev(times) if len(times) > 1 else 0:6.2f}s")

total_times = [v['total'] for v in recent.values() if 'total' in v]
if total_times:
    print(f"{'total':20} avg={mean(total_times):6.2f}s  min={min(total_times):6.2f}s  max={max(total_times):6.2f}s")
EOF
```

---

## Troubleshooting During Deployment

### Issue: "ModuleNotFoundError: No module named 'requests'"

**Cause:** Dependencies not installed

**Solution:**
```bash
python3 -m pip install -r requirements.txt
python3 -m pip list | grep -E "requests|beautifulsoup"
```

### Issue: "Permission denied: 'knowledge/digests'"

**Cause:** Insufficient write permissions

**Solution:**
```bash
chmod -R 755 knowledge/
chmod -R 755 logs/
ls -ld knowledge logs
# Should show: drwxr-xr-x
```

### Issue: "DHA Scraper timeout after 30s"

**Cause:** Home Affairs site slow or network issue

**Solution:**
```bash
# Test network connectivity
curl -I https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect -m 10

# Try with longer timeout
python3 << 'EOF'
import requests
try:
    resp = requests.get('https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect', timeout=60)
    print(f"Status: {resp.status_code}")
except requests.Timeout:
    print("Site timeout - try again later")
except Exception as e:
    print(f"Error: {e}")
EOF
```

### Issue: "Digest shows yesterday's data"

**Cause:** Scraper failed, digester fell back to previous day

**Solution:**
```bash
# Check scraper logs
tail -100 logs/scraper.log

# Check error log
tail -20 knowledge/live_cutoffs/scraper_errors.jsonl

# Manually run scraper with verbose output
python3 -m runtime.scrapers.dha_scraper --all --verbose

# Regenerate digest
python3 -m runtime.intelligence.digester
```

### Issue: "Tests fail with 'AssertionError'"

**Cause:** Environment issue or missing test data

**Solution:**
```bash
# Run with verbose output
pytest tests/ -vv --tb=long

# Run single test to debug
pytest tests/test_dha_scraper.py::TestDHAScraperFetch::test_retry_on_timeout -vv

# Check test data files exist
ls tests/fixtures/ 2>/dev/null || echo "No fixtures directory"

# If fixtures missing, regenerate
python3 -m pytest --fixtures 2>&1 | head -50
```

---

## Post-Deployment Verification

**Wait 24 hours, then verify:**

1. ✓ Cron jobs executed (check `/var/log/syslog` or `logs/*.log`)
2. ✓ Digests generated automatically at 0500 UTC daily
3. ✓ No scraper errors logged for 3+ consecutive days
4. ✓ Alert emails (if configured) received at 0600 UTC
5. ✓ Disk space stable (not growing >100MB/day)
6. ✓ Points calculator validates against official tool
7. ✓ SkillSelect cutoff history populated

**Sign-Off Checklist:**
- [ ] All tests passing (141+ tests)
- [ ] First 3 daily cycles completed successfully
- [ ] Operator has read Operator Manual
- [ ] Incident response procedures reviewed
- [ ] Backup strategy confirmed
- [ ] Monitoring dashboard set up
- [ ] Team trained on daily responsibilities

---

## Next Steps

1. **Day 1:** Review [Operator Manual](./OPERATOR_MANUAL.md) for daily responsibilities
2. **Week 1:** Complete [Installation Checklist](./INSTALLATION_CHECKLIST.md)
3. **Ongoing:** Monitor via [Operations Runbook](./OPERATIONS_RUNBOOK.md)
4. **As Needed:** Consult [Troubleshooting Guide](./TROUBLESHOOTING.md)

---

## Support & Escalation

**For deployment issues:**
1. Check [Troubleshooting Guide](./TROUBLESHOOTING.md)
2. Review log files: `tail -100 logs/*.log`
3. Run manual cycle: `python3 -m runtime.scrapers.dha_scraper --all --verbose`
4. Contact DevOps team with logs attached

**For operational questions:**
- Refer to [Operator Manual](./OPERATOR_MANUAL.md)
- Check [Operations Runbook](./OPERATIONS_RUNBOOK.md) for step-by-step procedures

---

**Document Version:** 1.0  
**Last Tested:** 2026-11-15  
**Next Review:** 2026-12-15
