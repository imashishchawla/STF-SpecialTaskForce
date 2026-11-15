# Visa Agent: Installation Checklist

**Version:** 1.0  
**Last Updated:** 2026-11-15  
**Total Time:** 45-60 minutes  
**Audience:** System Administrator, DevOps Engineer

---

## Pre-Installation Phase (15 minutes)

### Step 1: Verify Prerequisites

- [ ] **Python Version**
  - [ ] Run: `python3 --version`
  - [ ] Result: Python 3.10 or higher
  - [ ] If not: Install Python 3.10+ from https://www.python.org/

- [ ] **Disk Space**
  - [ ] Run: `df -h /`
  - [ ] Result: >2.5 GB free
  - [ ] If not: Expand disk or clean up space

- [ ] **Git Repository**
  - [ ] Run: `git --version`
  - [ ] Result: git version 2.0 or higher
  - [ ] Repo cloned: `ls -la .git/` shows git directory

- [ ] **Network Connectivity**
  - [ ] Run: `curl -I https://immi.homeaffairs.gov.au`
  - [ ] Result: HTTP 200 or 301 (redirect)
  - [ ] Run: `ping -c 1 8.8.8.8`
  - [ ] Result: Replies within 100ms

- [ ] **Permissions**
  - [ ] Current user: `whoami` shows non-root user
  - [ ] Directory writable: `touch /path/to/visa-agent/test.txt && rm test.txt`
  - [ ] Result: File created and deleted successfully

- [ ] **Terminal/Shell**
  - [ ] Shell: `echo $SHELL` shows bash or zsh
  - [ ] Result: `/bin/bash` or `/bin/zsh`

### Step 2: Create Deployment Plan

- [ ] **Deployment Path**
  - [ ] Location: `/path/to/portable/Visa-Agent`
  - [ ] Record path: `pwd > /tmp/deployment_path.txt`
  - [ ] Verify path: `cat /tmp/deployment_path.txt`

- [ ] **User Account**
  - [ ] Username: Record deployment user
  - [ ] Group: Record primary group
  - [ ] Home directory: Verify writable

- [ ] **Email Notifications** (if sending alerts)
  - [ ] Operator email: [recorded]
  - [ ] Coordinator email: [recorded]
  - [ ] DevOps lead email: [recorded]
  - [ ] Mail relay configured: `echo "test" | mail -s "test" user@company.com`

---

## Installation Phase (20 minutes)

### Step 1: Clone Repository

- [ ] **Clone Repo**
  ```bash
  git clone https://github.com/your-org/STF-SpecialTaskForce.git
  cd STF-SpecialTaskForce/portable/Visa-Agent
  ```

- [ ] **Verify Location**
  - [ ] Run: `pwd`
  - [ ] Result: Shows correct path ending in `/portable/Visa-Agent`
  - [ ] Run: `ls -la .git/` 
  - [ ] Result: Shows git configuration

### Step 2: Create Directory Structure

```bash
mkdir -p knowledge/{digests,live_cutoffs,alerts,raw_dha,australia,incidents}
mkdir -p logs
mkdir -p backups
mkdir -p scripts
```

- [ ] **Verify Directories**
  ```bash
  ls -la knowledge/
  ls -la logs/
  ls -la backups/
  ```
  - [ ] All 9 directories exist
  - [ ] Permissions: `drwxr-xr-x`

### Step 3: Install Python Dependencies

- [ ] **Upgrade pip**
  ```bash
  python3 -m pip install --upgrade pip setuptools wheel
  ```

- [ ] **Install Requirements**
  ```bash
  python3 -m pip install -r requirements.txt
  ```

- [ ] **Verify Installation**
  ```bash
  python3 -m pip list | grep -E "requests|beautifulsoup4|pydantic|pytest"
  ```
  - [ ] All packages listed with versions
  - [ ] No errors shown

### Step 4: Verify Python Imports

- [ ] **Test DHA Scraper**
  ```bash
  python3 -c "from runtime.scrapers import DHAScraper; print('✓ DHA OK')"
  ```

- [ ] **Test State Monitor**
  ```bash
  python3 -c "from runtime.scrapers import StateMonitor; print('✓ State Monitor OK')"
  ```

- [ ] **Test ACS Poller**
  ```bash
  python3 -c "from runtime.scrapers import ACSPoller; print('✓ ACS Poller OK')"
  ```

- [ ] **Test Digester**
  ```bash
  python3 -c "from runtime.intelligence import IntelligenceDigester; print('✓ Digester OK')"
  ```

- [ ] **Test Points Calculator**
  ```bash
  python3 -c "from runtime import PointsCalculator; print('✓ Points Calculator OK')"
  ```

---

## Verification Phase (10 minutes)

### Step 1: Run Test Suite

- [ ] **Run All Tests**
  ```bash
  pytest tests/ -v --tb=short 2>&1 | tee /tmp/test_results.txt
  ```
  - [ ] Result: "passed" message
  - [ ] Count: 141+ tests passed
  - [ ] No failing tests (except known skips)

- [ ] **Check Test Output**
  ```bash
  tail -20 /tmp/test_results.txt | grep -E "passed|failed"
  ```
  - [ ] Result: Shows all tests passing

### Step 2: Run First Scraper Cycle

- [ ] **DHA Scraper**
  ```bash
  python3 -m runtime.scrapers.dha_scraper --all --verbose 2>&1 | tee /tmp/dha_scrape.log
  ```
  - [ ] Runs without error
  - [ ] Creates files in `knowledge/raw_dha/`
  - [ ] Check: `ls -lh knowledge/raw_dha/*.json | tail -5`

- [ ] **State Monitor**
  ```bash
  python3 -m runtime.scrapers.state_monitor --all --verbose 2>&1 | tee /tmp/state_scrape.log
  ```
  - [ ] Creates state files: `ls knowledge/live_cutoffs/state_*.json`
  - [ ] Should show 8 states (or some if partial failure)

- [ ] **ACS Poller**
  ```bash
  python3 -m runtime.scrapers.acs_poller --verbose 2>&1 | tee /tmp/acs_scrape.log
  ```
  - [ ] Completes without error
  - [ ] Updates: `knowledge/live_cutoffs/acs_assessments.json`

### Step 3: Generate First Digest

- [ ] **Run Digester**
  ```bash
  python3 -m runtime.intelligence.digester 2>&1 | tee /tmp/digester.log
  ```
  - [ ] Completes successfully
  - [ ] Creates digest file
  - [ ] Check: `ls -lh knowledge/digests/daily_digest_*.md`

- [ ] **Verify Digest Content**
  ```bash
  cat knowledge/digests/daily_digest_*.md | head -50
  ```
  - [ ] Shows markdown content
  - [ ] Has sections like "KEY METRICS", "CRITICAL Alerts"
  - [ ] No errors in content

- [ ] **Verify Digest Size**
  ```bash
  wc -c knowledge/digests/daily_digest_*.md
  ```
  - [ ] Size: >5,000 bytes (5KB)
  - [ ] Size: <100,000 bytes (100KB)

### Step 4: Data Quality Checks

- [ ] **Validate JSON Files**
  ```bash
  for f in knowledge/live_cutoffs/*.json; do
    python3 -m json.tool "$f" > /dev/null && echo "✓ $f" || echo "✗ $f"
  done
  ```
  - [ ] All files valid JSON
  - [ ] No errors shown

- [ ] **Check Occupations Tracked**
  ```bash
  grep -o '"occupation_code"' knowledge/live_cutoffs/skillselect_cutoffs.json | wc -l
  ```
  - [ ] Result: >150 occupations
  - [ ] Shows diversity of tracked fields

---

## Configuration Phase (10 minutes)

### Step 1: Initialize Data Files

- [ ] **Create SkillSelect Cutoffs**
  ```bash
  cat > knowledge/live_cutoffs/skillselect_cutoffs.json << 'EOF'
  {
    "meta": {
      "source": "https://immi.homeaffairs.gov.au/",
      "scrape_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
      "scrape_status": "initial_setup"
    },
    "cutoffs": []
  }
  EOF
  ```

- [ ] **Create SkillSelect History**
  ```bash
  touch knowledge/live_cutoffs/skillselect_history.jsonl
  ```

- [ ] **Create ACS Assessments**
  ```bash
  cat > knowledge/live_cutoffs/acs_assessments.json << 'EOF'
  {
    "meta": {
      "source": "https://www.acs.org.au/",
      "last_updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    },
    "assessments": []
  }
  EOF
  ```

- [ ] **Create Visa Costs**
  ```bash
  cat > knowledge/australia/visa_costs.json << 'EOF'
  {
    "meta": {
      "source": "https://immi.homeaffairs.gov.au/",
      "last_updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    },
    "costs": {}
  }
  EOF
  ```

### Step 2: Set File Permissions

- [ ] **Directory Permissions**
  ```bash
  chmod -R 755 knowledge/ logs/ backups/ scripts/
  chmod 644 knowledge/live_cutoffs/*.json
  chmod 644 knowledge/live_cutoffs/*.jsonl
  chmod 644 knowledge/digests/*.md
  ```

- [ ] **Script Permissions**
  ```bash
  chmod +x scripts/*.sh
  ```

- [ ] **Verify Permissions**
  ```bash
  ls -ld knowledge/ logs/ backups/
  # Should show: drwxr-xr-x
  ```

### Step 3: Configure Logging

- [ ] **Create Log Files**
  ```bash
  touch logs/scraper.log logs/state_monitor.log logs/acs_poller.log logs/digester.log logs/health_check.log
  chmod 644 logs/*.log
  ```

- [ ] **Verify Log Files**
  ```bash
  ls -la logs/
  ```
  - [ ] All log files created
  - [ ] Permissions: `-rw-r--r--`

---

## Scheduler Configuration Phase (15 minutes)

### Step 1: Set Up Cron Jobs (Linux/macOS)

- [ ] **Edit Crontab**
  ```bash
  crontab -e
  ```

- [ ] **Add Cron Entries**
  ```
  # Replace /path/to/ with actual deployment path
  # Get path first:
  pwd > /tmp/deployment_path.txt
  
  # Then in crontab:
  SHELL=/bin/bash
  PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
  
  # Run scrapers at 0300 UTC daily
  0 3 * * * cd /path/to/portable/Visa-Agent && /usr/bin/python3 -m runtime.scrapers.dha_scraper --all >> logs/scraper.log 2>&1
  0 3 * * * cd /path/to/portable/Visa-Agent && /usr/bin/python3 -m runtime.scrapers.state_monitor --all >> logs/state_monitor.log 2>&1
  0 3 * * * cd /path/to/portable/Visa-Agent && /usr/bin/python3 -m runtime.scrapers.acs_poller >> logs/acs_poller.log 2>&1
  
  # Run digester at 0500 UTC (after scrapers)
  0 5 * * * cd /path/to/portable/Visa-Agent && /usr/bin/python3 -m runtime.intelligence.digester >> logs/digester.log 2>&1
  
  # Run health check at 0600 UTC
  0 6 * * * cd /path/to/portable/Visa-Agent && bash scripts/health_check.sh >> logs/health_check.log 2>&1
  ```

- [ ] **Verify Crontab**
  ```bash
  crontab -l | grep visa
  ```
  - [ ] All 5 cron jobs listed
  - [ ] Paths are absolute (start with `/`)
  - [ ] No errors shown

### Step 2: Test Cron Execution

- [ ] **Create Test Job**
  ```bash
  crontab -e
  # Add: * * * * * echo "$(date)" >> /tmp/cron_test.log
  ```

- [ ] **Wait and Verify** (wait 2 minutes)
  ```bash
  cat /tmp/cron_test.log
  ```
  - [ ] File has at least 2 lines
  - [ ] Timestamps are recent
  - [ ] Cron daemon is working

- [ ] **Remove Test Job**
  ```bash
  crontab -e
  # Remove the test line
  ```

### Step 3: Verify Cron Daemon Running

- [ ] **Linux: Check Cron Service**
  ```bash
  sudo service cron status
  # Or:
  sudo systemctl status cron
  ```
  - [ ] Shows: "active (running)" or similar
  - [ ] If not, run: `sudo service cron start`

- [ ] **macOS: Check Cron Launch Daemon**
  ```bash
  sudo launchctl list | grep cron
  ```
  - [ ] Shows cron process
  - [ ] If not, run:
    ```bash
    sudo launchctl load /System/Library/LaunchDaemons/com.vix.cron.plist
    ```

---

## Post-Deployment Phase (5 minutes)

### Step 1: Generate Baseline Report

- [ ] **Create Installation Report**
  ```bash
  cat > /tmp/installation_report.txt << 'EOF'
  # VISA AGENT INSTALLATION REPORT
  
  Installation Date: $(date)
  Installer: $(whoami)
  
  ## Environment
  - Python Version: $(python3 --version)
  - Git Repo: $(git log --oneline | head -1)
  - Deployment Path: $(pwd)
  
  ## Tests Passed
  - Unit Tests: $(pytest tests/ -q 2>&1 | tail -1)
  - Integration Tests: OK (first cycle completed)
  
  ## Initial Data
  - Scrapers Executed: YES
  - Digest Generated: YES
  - First Cycle Duration: [recorded above]
  
  ## Cron Jobs Configured
  - DHA Scraper (0300 UTC): YES
  - State Monitor (0300 UTC): YES
  - ACS Poller (0300 UTC): YES
  - Digester (0500 UTC): YES
  - Health Check (0600 UTC): YES
  
  ## System Status
  - Disk Space: $(df . | tail -1 | awk '{print $(NF-2)/1024}')MB
  - Log Files: $(ls logs/*.log | wc -l)
  - Digest Files: $(ls knowledge/digests/*.md 2>/dev/null | wc -l)
  
  ## Sign-Off
  - All checks: PASS
  - Ready for production: YES
  - Approved by: [admin name]
  - Date: $(date)
  
  EOF
  
  cat /tmp/installation_report.txt
  ```

- [ ] **Archive Report**
  ```bash
  cp /tmp/installation_report.txt backups/installation_report_$(date +%Y-%m-%d).txt
  ```

### Step 2: Document Configuration

- [ ] **Save Cron Configuration**
  ```bash
  crontab -l > backups/crontab_$(date +%Y-%m-%d).txt
  ```

- [ ] **Save Deployment Path**
  ```bash
  echo "Deployment path: $(pwd)" > backups/deployment_path.txt
  ```

- [ ] **Create Operations Handoff**
  ```bash
  cat > /tmp/handoff.md << 'EOF'
  # SYSTEM HANDOFF DOCUMENT
  
  ## Deployment Complete
  - Installation Date: $(date)
  - Installer: $(whoami)
  - Status: READY FOR OPERATIONS
  
  ## Key Files
  - Deployment: $(pwd)
  - Digests: knowledge/digests/
  - Logs: logs/
  - Docs: docs/
  
  ## Next Steps for Operator
  1. Read docs/OPERATOR_MANUAL.md
  2. Review docs/DEPLOYMENT.md (Verification section)
  3. Start daily briefings (0600 UTC onwards)
  4. Set calendar reminders:
     - Friday 1000 UTC: Update ACS data
     - Monday 1000 UTC: Update SkillSelect cutoffs
     - Last Friday month: Monthly verification
  
  ## On-Call Support
  - DevOps lead: [contact]
  - Visa coordinator: [contact]
  - Emergency escalation: [contact]
  
  EOF
  
  cat /tmp/handoff.md
  ```

---

## Final Verification Checklist

### Day 1 (Deployment Day)

- [ ] **Morning (0600 UTC)**
  - [ ] Digest exists: `ls knowledge/digests/daily_digest_$(date +%Y-%m-%d).md`
  - [ ] No errors in logs: `tail logs/digester.log | grep -i error`
  - [ ] Data is fresh: `ls -lh knowledge/raw_dha/visa_finder_*.json | tail -1`

- [ ] **Afternoon**
  - [ ] Test manual scraper: `python3 -m runtime.scrapers.dha_scraper --target visa_finder`
  - [ ] Verify output: `tail knowledge/raw_dha/visa_finder_*.json`
  - [ ] Check no cascading errors: `wc -l knowledge/live_cutoffs/scraper_errors.jsonl`

### Day 2-3 (Automated Cycles)

- [ ] **After First Automated Run (0300 UTC Day 2)**
  - [ ] Check logs created: `ls -lh logs/scraper.log logs/digester.log`
  - [ ] Digest generated automatically: `ls knowledge/digests/daily_digest_*.md`
  - [ ] No permission errors: `grep -i "permission denied" logs/*.log`

- [ ] **After First Health Check (0600 UTC Day 2)**
  - [ ] Health check report created: `ls logs/health_check_report_*.txt`
  - [ ] Report shows "PASS": `tail logs/health_check_report_*.txt | grep -i "pass\|fail"`

### Week 1

- [ ] **After 7 Days (1 full week)**
  - [ ] All 7 daily digests exist: `ls knowledge/digests/daily_digest_*.md | wc -l` (should be ≥7)
  - [ ] No scraper failures: `wc -l knowledge/live_cutoffs/scraper_errors.jsonl` (should be <5)
  - [ ] Data is complete: All occupations in SkillSelect history
  - [ ] Operator trained: Operator has read all docs and performed daily briefings

---

## Sign-Off

Once all checks are complete, sign off on installation:

```bash
cat > backups/INSTALLATION_SIGN_OFF.txt << 'EOF'
INSTALLATION SIGN-OFF

System: Visa Agent Quick Wins + Phase 1
Deployment Date: $(date)
Installer: $(whoami)

CHECKLIST STATUS: ALL ITEMS COMPLETED ✓

Pre-Installation: 8/8 items ✓
Installation: 4/4 sections ✓
Verification: 4/4 sections ✓
Configuration: 3/3 sections ✓
Scheduler: 3/3 sections ✓
Post-Deployment: 2/2 sections ✓

Final Verification:
- Day 1 checks: PASS ✓
- Day 2-3 checks: PASS ✓
- Week 1 checks: PASS ✓

SYSTEM STATUS: READY FOR PRODUCTION ✓

Signed:
- Installer: ___________________
- Approver: ____________________
- Date: _______________________

Next Review: [Date + 30 days]

EOF

cat backups/INSTALLATION_SIGN_OFF.txt
```

---

## Troubleshooting During Installation

If you encounter issues during installation, see [docs/TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for:
- Python import errors
- Cron configuration issues
- Disk space problems
- Network connectivity issues
- File permission problems

---

## Quick Reference: Key Commands

```bash
# Verify installation
python3 --version
pip list | grep -E "requests|pytest|pydantic"

# Test scrapers
python3 -m runtime.scrapers.dha_scraper --all --verbose
python3 -m runtime.scrapers.state_monitor --all --verbose
python3 -m runtime.scrapers.acs_poller --verbose

# Test digester
python3 -m runtime.intelligence.digester

# Run tests
pytest tests/ -v

# Check cron
crontab -l

# View logs
tail -50 logs/digester.log
tail -50 logs/scraper.log

# View latest digest
cat knowledge/digests/daily_digest_$(date +%Y-%m-%d).md | head -100
```

---

**Installation Checklist Version:** 1.0  
**Last Updated:** 2026-11-15  
**Estimated Time:** 45-60 minutes  
**Success Criteria:** All checkboxes completed, system ready for operations
