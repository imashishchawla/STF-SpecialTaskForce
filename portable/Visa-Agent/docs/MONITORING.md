# Visa Agent: Monitoring & Metrics Dashboard

**Version:** 1.0  
**Last Updated:** 2026-11-15  
**Purpose:** Track system health, performance, and data quality metrics

---

## Key Performance Metrics

### System Availability

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Digest generation rate | 7/7 days/week | <7/7 | Missing 2+ days |
| Scraper success rate | 100% | <95% | <80% |
| Data freshness (all sources <24h) | 100% | <95% | <80% |
| Cron execution success | 100% | <95% | Failed 2+ days |
| System uptime | 99.5% | <99% | <95% |

**Tracking Method:**
```bash
# Count digests generated this week
ls knowledge/digests/daily_digest_*.md | grep $(date +%Y-%m) | wc -l
# Should be 7 (or days since deployment if <7 days old)

# Count scraper failures
grep -c "error_type.*fail" knowledge/live_cutoffs/scraper_errors.jsonl || echo 0
# Should be 0 or <5% of total scrapes
```

### Data Quality Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| False positive alert rate | <5% | 5-10% | >10% |
| JSON validation pass rate | 100% | <99% | <95% |
| Occupations tracked | 150+ | <150 | <100 |
| SkillSelect history depth | 180+ days | <180 days | <90 days |

**Tracking Method:**
```bash
# Check false positive rate (alerts that were later contradicted)
grep '"days_confirmed":[01]' knowledge/alerts/*.json 2>/dev/null | wc -l
# Calculate: FP count / Total alerts * 100

# Verify JSON files
find knowledge -name "*.json" -exec python3 -m json.tool {} \; 2>/dev/null | grep -c error || echo 0
# Should be 0 errors

# Count history entries
wc -l knowledge/live_cutoffs/skillselect_history.jsonl
# Should be >180 (days * ~2 occupations per day avg)
```

### Performance Metrics

| Component | Baseline | Warning | Timeout |
|---|---|---|---|
| DHA Scraper | 2-3 min | >4 min | >30 sec |
| State Monitors | 3-5 min | >6 min | >30 sec |
| ACS Poller | 1-2 min | >3 min | >30 sec |
| Digester | 3-5 min | >6 min | >30 sec |
| **Total Pipeline** | **5-10 min** | **>12 min** | **>60 sec** |

**Tracking Method:**
```bash
# Extract runtime from logs
grep "completed in" logs/scraper.log | tail -5

# Visualize performance trend
python3 << 'EOF'
import re
from pathlib import Path

pattern = r'(\d+\.\d+)\s*seconds'
for log_file in Path('logs').glob('*.log'):
    with open(log_file) as f:
        matches = re.findall(pattern, f.read())
    if matches:
        times = [float(m) for m in matches[-10:]]
        avg = sum(times) / len(times)
        print(f"{log_file.name}: avg {avg:.1f}s (last 10 runs)")
EOF
```

---

## Alert Rules & Thresholds

### Automated Alerts

| Alert | Trigger | Action | Recipient |
|---|---|---|---|
| **No Digest Today** | Missing after 0700 UTC | Check cron, manual trigger | Operator |
| **Scraper Failed 2x** | 2 consecutive days | Investigate endpoint | DevOps |
| **Data Stale >48h** | All sources offline | Use fallback, escalate | Operator + DevOps |
| **Disk >80%** | <500MB remaining | Archive old data | SysAdmin |
| **CRITICAL Alert** | Cutoff spike >10 or close | Verify + notify coordinator | Operator + Coordinator |
| **JSON Corrupt** | Parse error on key files | Restore from backup | DevOps |
| **Cron Not Running** | No execution logs | Check daemon, restart | SysAdmin |

**Implementation:**
```bash
# health_check.sh runs daily at 0600 UTC
# Logs all issues to logs/health_check_report_YYYY-MM-DD.txt
# Email sent if >0 failures

# To enable email alerts, edit scripts/health_check.sh:
# Uncomment: send_email_if_failed
```

---

## Metrics Dashboard (Manual Tracking)

### Weekly Summary Template

Create file: `logs/weekly_summary_YYYY-WXX.txt`

```
=== WEEKLY SUMMARY ===
Week: November 8-14, 2026
Operator: John Smith

AVAILABILITY
────────────────────────────────────
Digests Generated: 7/7 ✓
Scraper Success Rate: 100% ✓
Data Freshness: 100% (all <24h) ✓
System Uptime: 99.8% ✓

DATA QUALITY
────────────────────────────────────
False Positive Rate: 2% ✓
JSON Validation: 100% ✓
Occupations Tracked: 152 ✓
History Depth: 185 days ✓

PERFORMANCE
────────────────────────────────────
DHA Scraper Avg: 2.5 min ✓
State Monitor Avg: 4.2 min ✓
ACS Poller Avg: 1.8 min ✓
Digester Avg: 4.1 min ✓
Total Pipeline Avg: 7.8 min ✓

INCIDENTS THIS WEEK
────────────────────────────────────
0 CRITICAL alerts
2 SIGNIFICANT alerts
5 MINOR alerts

Issues Encountered:
- 1 timeout (resolved manually)
- 0 data corruption
- 0 missed digests

ACTIONS TAKEN
────────────────────────────────────
- Updated ACS processing times (Friday)
- Updated SkillSelect cutoffs (Monday)
- Escalated 1 occupation change to coordinator
- Archived old logs (220MB freed)

UPCOMING
────────────────────────────────────
- Monthly verification (next Friday)
- Review CSS selectors (ACS portal changed)
- Expand knowledge/ storage (approaching 80%)

STATUS: ✓ HEALTHY
```

**Create weekly summary:**
```bash
# Add to crontab (Sunday 1700 UTC)
0 17 * * 0 cd /path && bash << 'EOF'
cat > logs/weekly_summary_$(date +%Y-W%V).txt << 'REPORT'
[Template above]
REPORT
EOF
```

---

## Dashboard: Live Metrics View

### One-Minute Health Check

```bash
#!/bin/bash
# Quick status overview

cd /path/to/portable/Visa-Agent

echo "=== VISA AGENT LIVE STATUS ==="
echo "Time: $(date)"
echo

# 1. Latest digest
DIGEST=$(ls -1 knowledge/digests/daily_digest_*.md 2>/dev/null | sort | tail -1)
if [ -f "$DIGEST" ]; then
    SIZE=$(wc -c < "$DIGEST")
    CRITICAL=$(grep -c "CRITICAL" "$DIGEST" || echo 0)
    echo "✓ Digest: $(basename "$DIGEST") ($SIZE bytes, $CRITICAL alerts)"
else
    echo "✗ Digest: MISSING"
fi
echo

# 2. Data freshness
DHA=$(ls -1t knowledge/raw_dha/visa_finder_*.json 2>/dev/null | head -1)
if [ ! -z "$DHA" ]; then
    HOURS=$(( ($(date +%s) - $(stat -c %Y "$DHA" 2>/dev/null || stat -f "%m" "$DHA" 2>/dev/null)) / 3600 ))
    echo "✓ DHA Data: ${HOURS}h old"
else
    echo "✗ DHA Data: Missing"
fi
echo

# 3. Scraper errors
ERRORS=$(wc -l < knowledge/live_cutoffs/scraper_errors.jsonl 2>/dev/null || echo 0)
echo "• Scraper Errors (all-time): $ERRORS"
echo

# 4. Disk space
AVAIL=$(df . | tail -1 | awk '{print $(NF-2)/1024}' | cut -d. -f1)
echo "• Disk Available: ${AVAIL}MB"
echo

# 5. Recent logs
RECENT=$(tail -1 logs/digester.log 2>/dev/null)
echo "• Recent: $RECENT"
echo

echo "=== END STATUS ==="
```

Run this command anytime to see quick status:
```bash
bash scripts/health_check.sh  # Comprehensive (5 min)
# OR
bash -c "cat /dev/stdin" << 'EOF'
[live metrics view script above]
EOF
```

---

## Metrics Tracking Spreadsheet

### Example: Monthly Metrics Log

| Date | Digest | Scraper | Data Fresh | Alerts | Incidents | Notes |
|------|--------|---------|-----------|--------|-----------|-------|
| 2026-11-01 | ✓ | ✓ | ✓ | 0 | 0 | All systems nominal |
| 2026-11-02 | ✓ | ✓ | ✓ | 2 | 0 | Expected SIGNIFICANT alerts |
| 2026-11-03 | ✓ | ✓ | ✓ | 0 | 0 | Quiet day |
| 2026-11-04 | ✗ | ⚠ | ⚠ | 0 | 1 | DHA timeout, used fallback |
| ... | | | | | | |
| 2026-11-30 | ✓ | ✓ | ✓ | 1 | 0 | Monthly verification passed |

**Record Template:**
```bash
cat >> logs/metrics_log.csv << 'EOF'
$(date +%Y-%m-%d),digest_ok,scraper_ok,data_fresh,alert_count,incident_count,notes
EOF
```

---

## Monitoring Automation

### Create Metrics Collection Script

```bash
#!/bin/bash
# metrics_collector.sh - Runs hourly to collect metrics

PROJECT_DIR="/path/to/portable/Visa-Agent"
METRICS_FILE="logs/metrics_hourly.jsonl"

cd "$PROJECT_DIR"

# Collect metrics
python3 << 'EOF'
import json
import os
from pathlib import Path
from datetime import datetime

metrics = {
    "timestamp": datetime.utcnow().isoformat(),
    "digest_exists": os.path.exists(f"knowledge/digests/daily_digest_{datetime.now().strftime('%Y-%m-%d')}.md"),
    "error_count": 0,
    "disk_available_mb": 0,
    "latest_digest_age_hours": 0
}

# Count errors
error_file = Path("knowledge/live_cutoffs/scraper_errors.jsonl")
if error_file.exists():
    metrics["error_count"] = error_file.stat().st_size / 100  # Rough estimate

# Get disk space
import subprocess
df = subprocess.run(['df', '.'], capture_output=True, text=True)
try:
    metrics["disk_available_mb"] = int(df.stdout.split('\n')[1].split()[3]) / 1024
except:
    pass

# Get digest age
digest_files = list(Path('knowledge/digests').glob('daily_digest_*.md'))
if digest_files:
    latest = max(digest_files, key=lambda x: x.stat().st_mtime)
    age_seconds = datetime.utcnow().timestamp() - latest.stat().st_mtime
    metrics["latest_digest_age_hours"] = age_seconds / 3600

# Append to metrics log
with open("logs/metrics_hourly.jsonl", "a") as f:
    json.dump(metrics, f)
    f.write("\n")

print(json.dumps(metrics, indent=2))
EOF
```

**Add to crontab (every hour):**
```bash
0 * * * * cd /path && python3 scripts/metrics_collector.py >> logs/metrics_hourly.log 2>&1
```

---

## Alert Notification Template

### Email Alert Format

```
To: [recipient]
Subject: [SEVERITY] Visa Agent Alert - [Component] [Issue]

Body Format:
────────────────────────────────────────

ALERT TYPE: [System Health / Data Quality / Performance]
SEVERITY: [CRITICAL / WARNING / INFO]
TRIGGERED: [Timestamp UTC]

ISSUE:
[Description of what went wrong]

METRIC:
[Current value] vs [Expected/Target value]

IMPACT:
[Who/what is affected]

ACTION REQUIRED:
1. [Immediate action]
2. [Follow-up action]
3. [Long-term fix]

LINK TO DETAILS:
[Path to log file or digest]

────────────────────────────────────────
Visa Agent Monitoring System
```

### Example CRITICAL Alert

```
To: devops@company.com
Subject: 🚨 CRITICAL - Visa Agent: Digest Missing 36 Hours

Body:

ALERT TYPE: System Health
SEVERITY: CRITICAL
TRIGGERED: 2026-11-15T07:00:00Z

ISSUE:
Daily digest was not generated on 2026-11-15.
This is the second consecutive day with missing digest.

METRIC:
Expected: 1 digest per day
Current: 0 digests (missing for 36 hours)

IMPACT:
- Operator has no intelligence briefing
- CRITICAL alerts may be undetected
- Clients not notified of cutoff changes

ACTION REQUIRED:
1. Check if cron daemon is running: sudo service cron status
2. Verify crontab entries: crontab -l
3. Manually trigger digester: python3 -m runtime.intelligence.digester
4. If manual succeeds, investigate why cron failed
5. Check /var/log/syslog for cron errors

LINK TO DETAILS:
- Digester logs: logs/digester.log
- Scraper logs: logs/scraper.log
- Last digest: knowledge/digests/daily_digest_*.md

────────────────────────────────────────
```

---

## Metrics Analysis Tools

### Weekly Performance Report

```python
#!/usr/bin/env python3
"""Generate weekly performance report"""

import json
from pathlib import Path
from datetime import datetime, timedelta

def analyze_performance():
    """Analyze scraper performance over last 7 days"""
    
    perf_file = Path('logs/performance.json')
    if not perf_file.exists():
        print("No performance data available")
        return
    
    with open(perf_file) as f:
        data = json.load(f)
    
    # Get last 7 days
    today = datetime.utcnow()
    week_ago = today - timedelta(days=7)
    
    recent = {
        k: v for k, v in data.items()
        if datetime.fromisoformat(k) > week_ago
    }
    
    if not recent:
        print("Insufficient data")
        return
    
    # Analyze
    components = ['dha_scraper', 'state_monitor', 'acs_poller', 'digester']
    
    print("=== WEEKLY PERFORMANCE REPORT ===\n")
    
    for comp in components:
        times = [v[comp] for v in recent.values() if comp in v]
        if times:
            avg = sum(times) / len(times)
            min_t = min(times)
            max_t = max(times)
            
            print(f"{comp:20}")
            print(f"  Average:   {avg:6.2f}s")
            print(f"  Min:       {min_t:6.2f}s")
            print(f"  Max:       {max_t:6.2f}s")
            print(f"  Runs:      {len(times)}")
            print()

if __name__ == '__main__':
    analyze_performance()
```

### Alert Frequency Analysis

```python
#!/usr/bin/env python3
"""Analyze alert frequency and types"""

import json
from pathlib import Path
from collections import Counter

alert_files = list(Path('knowledge/alerts').glob('*.json'))
alert_types = Counter()

for alert_file in alert_files:
    try:
        with open(alert_file) as f:
            alerts = json.load(f)
        
        for alert in alerts:
            alert_type = alert.get('type', 'unknown')
            alert_types[alert_type] += 1
    except:
        pass

print("=== ALERT FREQUENCY ANALYSIS ===\n")
for alert_type, count in alert_types.most_common():
    print(f"{alert_type:20} {count:5d}")
```

---

## Dashboard Maintenance

### Monthly Dashboard Update

1. **Review Metrics**
   - Run: `python3 scripts/analyze_performance.py`
   - Record in: `logs/monthly_metrics_YYYY-MM.txt`
   - Compare with previous month

2. **Update Alert Thresholds**
   - Review false positive rate
   - Adjust timeout values if needed
   - Document changes in: `docs/ALERTS.md`

3. **Archive Old Metrics**
   ```bash
   tar -czf backups/metrics_archive_$(date +%Y-%m).tar.gz logs/metrics_hourly.jsonl
   rm logs/metrics_hourly.jsonl
   ```

4. **Review Incident Log**
   - Count incidents by type
   - Identify root causes
   - Document lessons learned

---

## Status Page (For External Visibility)

### Public Status Update Template

```markdown
# Visa Agent System Status

**Last Updated:** 2026-11-15 08:00 UTC

## Current Status
🟢 All Systems Operational

## Metrics
- Digest Generation: ✓ 7/7 days this week
- Scraper Success Rate: ✓ 100%
- Data Freshness: ✓ All <24h old
- Uptime: ✓ 99.8%

## Recent Issues
- None this week

## Scheduled Maintenance
- Next backup: 2026-11-22 (Tuesday)
- Next review: 2026-11-30 (Monthly verification)

## Contact
For operational questions: visa-agent-team@company.com
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-11-15  
**Next Review:** 2026-12-15
