#!/bin/bash
#
# Visa Agent Daily Health Check Script
# Runs automated health verification every morning
# Usage: bash scripts/health_check.sh
#

set -euo pipefail

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="logs/health_check.log"
REPORT_FILE="logs/health_check_report_$(date +%Y-%m-%d).txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Initialize report
{
    echo "====== VISA AGENT HEALTH CHECK REPORT ======"
    echo "Date: $(date)"
    echo "Project Directory: $PROJECT_DIR"
    echo ""
} | tee "$REPORT_FILE"

# Track overall status
FAILED_CHECKS=0
TOTAL_CHECKS=0

#######################################
# Health Check 1: Digest Exists
#######################################
check_digest_exists() {
    local check_name="Digest Generation"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    echo -n "Checking: $check_name... "

    local digest_file="knowledge/digests/daily_digest_$(date +%Y-%m-%d).md"

    if [ -f "$digest_file" ]; then
        local size=$(wc -c < "$digest_file")
        local hours_ago=$(( ($(date +%s) - $(stat -c %Y "$digest_file" 2>/dev/null || stat -f "%m" "$digest_file" 2>/dev/null)) / 3600 ))

        if [ "$hours_ago" -lt 24 ]; then
            echo -e "${GREEN}✓ PASS${NC}"
            {
                echo "✓ $check_name: PASS"
                echo "  File: $digest_file"
                echo "  Size: $size bytes"
                echo "  Age: $hours_ago hours"
            } >> "$REPORT_FILE"
        else
            echo -e "${YELLOW}⚠ STALE${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            {
                echo "⚠ $check_name: STALE (Age: $hours_ago hours)"
                echo "  File: $digest_file"
            } >> "$REPORT_FILE"
        fi
    else
        echo -e "${RED}✗ FAIL${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        {
            echo "✗ $check_name: FAIL"
            echo "  Expected file: $digest_file"
            echo "  Action: Run manually: python3 -m runtime.intelligence.digester"
        } >> "$REPORT_FILE"
    fi
}

#######################################
# Health Check 2: Scraper Data Freshness
#######################################
check_scraper_freshness() {
    local check_name="Scraper Data Freshness"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    echo -n "Checking: $check_name... "

    local dha_file=$(ls -1t "knowledge/raw_dha/visa_finder_"*.json 2>/dev/null | head -1)

    if [ -z "$dha_file" ]; then
        echo -e "${YELLOW}⚠ NO DATA${NC}"
        {
            echo "⚠ $check_name: No scraper data found"
        } >> "$REPORT_FILE"
        return
    fi

    local hours_ago=$(( ($(date +%s) - $(stat -c %Y "$dha_file" 2>/dev/null || stat -f "%m" "$dha_file" 2>/dev/null)) / 3600 ))

    if [ "$hours_ago" -lt 48 ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        {
            echo "✓ $check_name: PASS"
            echo "  Latest scraper data: $hours_ago hours old"
            echo "  File: $(basename "$dha_file")"
        } >> "$REPORT_FILE"
    else
        echo -e "${RED}✗ FAIL${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        {
            echo "✗ $check_name: FAIL (Data is $hours_ago hours old)"
            echo "  File: $dha_file"
            echo "  Action: Manually trigger scraper"
        } >> "$REPORT_FILE"
    fi
}

#######################################
# Health Check 3: Scraper Error Rate
#######################################
check_scraper_errors() {
    local check_name="Scraper Error Rate"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    echo -n "Checking: $check_name... "

    local error_file="knowledge/live_cutoffs/scraper_errors.jsonl"

    if [ ! -f "$error_file" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        {
            echo "✓ $check_name: PASS"
            echo "  No errors logged"
        } >> "$REPORT_FILE"
        return
    fi

    local error_count=$(wc -l < "$error_file")
    local last_24h_errors=$(find "$error_file" -mtime -1 2>/dev/null | wc -l)

    # Alert if 2+ errors in last 24 hours (indicates scraper instability)
    if [ "$last_24h_errors" -gt 2 ]; then
        echo -e "${RED}✗ FAIL${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        {
            echo "✗ $check_name: FAIL"
            echo "  Errors in last 24h: $last_24h_errors"
            echo "  Total errors: $error_count"
            echo "  Action: Check scraper logs"
        } >> "$REPORT_FILE"
    else
        echo -e "${GREEN}✓ PASS${NC}"
        {
            echo "✓ $check_name: PASS"
            echo "  Errors in last 24h: $last_24h_errors"
            echo "  Total errors (all time): $error_count"
        } >> "$REPORT_FILE"
    fi
}

#######################################
# Health Check 4: Disk Space
#######################################
check_disk_space() {
    local check_name="Disk Space"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    echo -n "Checking: $check_name... "

    # Get available space in MB
    local available_mb=$(df "$PROJECT_DIR" | tail -1 | awk '{print $(NF-2)/1024}' | cut -d. -f1)

    if [ "$available_mb" -gt 2000 ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        {
            echo "✓ $check_name: PASS"
            echo "  Available: ${available_mb}MB"
        } >> "$REPORT_FILE"
    elif [ "$available_mb" -gt 500 ]; then
        echo -e "${YELLOW}⚠ WARNING${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        {
            echo "⚠ $check_name: WARNING"
            echo "  Available: ${available_mb}MB (recommended: >2GB)"
            echo "  Action: Archive old files or expand storage"
        } >> "$REPORT_FILE"
    else
        echo -e "${RED}✗ CRITICAL${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        {
            echo "✗ $check_name: CRITICAL"
            echo "  Available: ${available_mb}MB"
            echo "  Action: URGENT - Free disk space immediately"
        } >> "$REPORT_FILE"
    fi
}

#######################################
# Health Check 5: JSON Validity
#######################################
check_json_validity() {
    local check_name="JSON File Validity"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    echo -n "Checking: $check_name... "

    local bad_files=0

    # Check key JSON files
    for json_file in \
        "knowledge/live_cutoffs/skillselect_cutoffs.json" \
        "knowledge/live_cutoffs/acs_assessments.json" \
        "knowledge/australia/visa_costs.json"
    do
        if [ -f "$json_file" ]; then
            if ! python3 -c "import json; json.load(open('$json_file'))" 2>/dev/null; then
                bad_files=$((bad_files + 1))
            fi
        fi
    done

    if [ "$bad_files" -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        {
            echo "✓ $check_name: PASS"
            echo "  All key JSON files valid"
        } >> "$REPORT_FILE"
    else
        echo -e "${RED}✗ FAIL${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        {
            echo "✗ $check_name: FAIL"
            echo "  Invalid JSON files: $bad_files"
            echo "  Action: Restore from backup or manually fix"
        } >> "$REPORT_FILE"
    fi
}

#######################################
# Health Check 6: CRITICAL Alerts
#######################################
check_critical_alerts() {
    local check_name="CRITICAL Alerts"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    echo -n "Checking: $check_name... "

    local digest_file="knowledge/digests/daily_digest_$(date +%Y-%m-%d).md"

    if [ -f "$digest_file" ]; then
        local critical_count=$(grep -c "^### CRITICAL" "$digest_file" 2>/dev/null || echo 0)

        if [ "$critical_count" -eq 0 ]; then
            echo -e "${GREEN}✓ PASS${NC}"
            {
                echo "✓ $check_name: PASS"
                echo "  No CRITICAL alerts"
            } >> "$REPORT_FILE"
        else
            echo -e "${YELLOW}⚠ ALERT${NC}"
            {
                echo "⚠ $check_name: $critical_count CRITICAL alert(s)"
                echo "  Review digest for details"
            } >> "$REPORT_FILE"
        fi
    else
        echo -e "${YELLOW}⚠ NO DIGEST${NC}"
        {
            echo "⚠ $check_name: Cannot check (no digest)"
        } >> "$REPORT_FILE"
    fi
}

#######################################
# Health Check 7: Cron Status
#######################################
check_cron_status() {
    local check_name="Cron Scheduling"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    echo -n "Checking: $check_name... "

    # Check if crontab is configured
    if crontab -l 2>/dev/null | grep -q "digester"; then
        echo -e "${GREEN}✓ PASS${NC}"
        {
            echo "✓ $check_name: PASS"
            echo "  Crontab configured with digester job"
        } >> "$REPORT_FILE"
    else
        echo -e "${YELLOW}⚠ WARNING${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        {
            echo "⚠ $check_name: WARNING"
            echo "  Crontab not configured or digester job missing"
            echo "  Action: Re-run crontab -e and add job"
        } >> "$REPORT_FILE"
    fi
}

#######################################
# Summary Report
#######################################
generate_summary() {
    local status="PASS"

    if [ "$FAILED_CHECKS" -gt 0 ]; then
        status="FAIL"
    fi

    {
        echo ""
        echo "====== SUMMARY ======"
        echo "Total Checks: $TOTAL_CHECKS"
        echo "Failed: $FAILED_CHECKS"
        echo "Passed: $((TOTAL_CHECKS - FAILED_CHECKS))"
        echo "Status: $status"
        echo "Timestamp: $(date)"
    } | tee -a "$REPORT_FILE"

    # Log to health check log
    echo "$(date): Health check completed - Status: $status (Failed: $FAILED_CHECKS)" >> "$LOG_FILE"
}

#######################################
# Email Report (if failures)
#######################################
send_email_if_failed() {
    if [ "$FAILED_CHECKS" -gt 0 ]; then
        {
            echo "Subject: ⚠ Visa Agent Health Check Failed ($FAILED_CHECKS issues)"
            echo "To: operator@company.com"
            echo ""
            cat "$REPORT_FILE"
        } | mail -t 2>/dev/null || true
    fi
}

#######################################
# Main Execution
#######################################
cd "$PROJECT_DIR"

echo "Starting health checks..."
echo ""

check_digest_exists
check_scraper_freshness
check_scraper_errors
check_disk_space
check_json_validity
check_critical_alerts
check_cron_status

echo ""
generate_summary

# Optionally send email
# Uncomment to enable email notifications:
# send_email_if_failed

echo ""
echo "Report saved to: $REPORT_FILE"

exit $FAILED_CHECKS
