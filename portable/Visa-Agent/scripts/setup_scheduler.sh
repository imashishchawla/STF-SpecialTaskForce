#!/bin/bash
# Setup Cron Scheduler for Visa Agent Phase 1 Pipeline
#
# This script configures daily and weekly automated intelligence gathering:
# - DHA scraper: Daily at 3 AM UTC (runs 5 min in parallel with states)
# - State monitors: Daily at 3 AM UTC (8 parallel monitors)
# - ACS poller: Weekly on Fridays at 3 AM UTC (lower frequency)
# - Digester: Daily at 5 AM UTC (after scrapers complete)
#
# Usage:
#   bash setup_scheduler.sh [--dry-run] [--install] [--uninstall] [--status]
#
# Options:
#   --dry-run:      Show what would be done without making changes
#   --install:      Install/update cron jobs
#   --uninstall:    Remove all cron jobs
#   --status:       Show current cron job status

set -euo pipefail

# ===== Configuration =====

# Base directory (should be Visa-Agent root)
AGENT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="${AGENT_ROOT}/runtime"
KNOWLEDGE_DIR="${AGENT_ROOT}/knowledge"
LOGS_DIR="${AGENT_ROOT}/logs"
SCRIPTS_DIR="${AGENT_ROOT}/scripts"

# Python executable (use venv if available)
if [ -d "${AGENT_ROOT}/.venv" ]; then
    PYTHON="${AGENT_ROOT}/.venv/bin/python3"
elif [ -d "${AGENT_ROOT}/venv" ]; then
    PYTHON="${AGENT_ROOT}/venv/bin/python3"
else
    PYTHON="python3"
fi

# Log rotation (keep 30 days of logs)
LOG_RETENTION_DAYS=30
CRON_EMAIL="root@localhost"  # Email for cron notifications

# ===== Functions =====

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[ERROR] $*" >&2
    exit 1
}

create_log_rotation_config() {
    """Create logrotate config for scraper logs."""
    local logrotate_config="/etc/logrotate.d/visa-agent"

    if [ ! -w "$(dirname "$logrotate_config")" ]; then
        log "⚠️  Skipping logrotate config (requires root): $logrotate_config"
        return 0
    fi

    cat > "$logrotate_config" << 'EOF'
/path/to/visa-agent/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        # Optional: notify on rotation
    endscript
}
EOF

    log "✓ Created logrotate config: $logrotate_config"
}

setup_directories() {
    """Create required directory structure."""
    log "Creating directory structure..."

    mkdir -p "$LOGS_DIR"
    mkdir -p "$KNOWLEDGE_DIR/raw_dha"
    mkdir -p "$KNOWLEDGE_DIR/live_cutoffs"
    mkdir -p "$KNOWLEDGE_DIR/digests"
    mkdir -p "$KNOWLEDGE_DIR/alerts"

    log "✓ Directories created"
}

verify_dependencies() {
    """Check that required Python modules are available."""
    log "Verifying dependencies..."

    if ! command -v "$PYTHON" &> /dev/null; then
        error "Python not found at: $PYTHON"
    fi

    log "✓ Python: $PYTHON"
}

generate_cron_jobs() {
    """Generate cron job entries."""
    local dha_job="0 3 * * * cd ${AGENT_ROOT} && ${PYTHON} ${RUNTIME_DIR}/scrapers/dha_scraper.py --all >> ${LOGS_DIR}/dha_scraper.log 2>&1"
    local states_job="0 3 * * * cd ${AGENT_ROOT} && ${PYTHON} ${RUNTIME_DIR}/scrapers/state_monitor.py --all >> ${LOGS_DIR}/state_monitor.log 2>&1"
    local acs_job="0 3 * * 5 cd ${AGENT_ROOT} && ${PYTHON} ${RUNTIME_DIR}/scrapers/acs_poller.py --all >> ${LOGS_DIR}/acs_poller.log 2>&1"
    local digester_job="0 5 * * * cd ${AGENT_ROOT} && ${PYTHON} ${RUNTIME_DIR}/intelligence/digester.py >> ${LOGS_DIR}/digester.log 2>&1"

    cat << EOF
# === Visa Agent Phase 1 Intelligence Pipeline ===
# DHA Scraper (Daily at 3 AM UTC)
$dha_job

# State Monitors (Daily at 3 AM UTC, parallel with DHA)
$states_job

# ACS Poller (Weekly on Friday at 3 AM UTC)
$acs_job

# Intelligence Digester (Daily at 5 AM UTC - after scrapers)
$digester_job

EOF
}

install_cron_jobs() {
    """Install cron jobs."""
    log "Installing cron jobs..."

    local temp_crontab=$(mktemp)
    local cron_comment="Visa Agent Phase 1 Intelligence Pipeline"

    # Get existing crontab (without our jobs)
    crontab -l 2>/dev/null | grep -v "$cron_comment" | grep -v "dha_scraper" | grep -v "state_monitor" | grep -v "acs_poller" | grep -v "digester" > "$temp_crontab" || true

    # Add header comment
    echo "# $cron_comment" >> "$temp_crontab"
    echo "# DO NOT EDIT - managed by setup_scheduler.sh" >> "$temp_crontab"
    echo "" >> "$temp_crontab"

    # Add our jobs
    generate_cron_jobs >> "$temp_crontab"

    # Install
    crontab "$temp_crontab"
    rm "$temp_crontab"

    log "✓ Cron jobs installed"
}

uninstall_cron_jobs() {
    """Remove cron jobs."""
    log "Uninstalling cron jobs..."

    local temp_crontab=$(mktemp)

    # Get existing crontab (without our jobs)
    crontab -l 2>/dev/null | grep -v "Visa Agent Phase 1" | grep -v "dha_scraper" | grep -v "state_monitor" | grep -v "acs_poller" | grep -v "digester" > "$temp_crontab" || true

    crontab "$temp_crontab"
    rm "$temp_crontab"

    log "✓ Cron jobs removed"
}

show_status() {
    """Show current cron job status."""
    log "Current cron jobs:"
    echo ""

    if crontab -l 2>/dev/null | grep -q "dha_scraper"; then
        log "✓ DHA Scraper is scheduled"
        crontab -l | grep "dha_scraper"
    else
        log "✗ DHA Scraper is NOT scheduled"
    fi

    if crontab -l 2>/dev/null | grep -q "state_monitor"; then
        log "✓ State Monitor is scheduled"
        crontab -l | grep "state_monitor"
    else
        log "✗ State Monitor is NOT scheduled"
    fi

    if crontab -l 2>/dev/null | grep -q "acs_poller"; then
        log "✓ ACS Poller is scheduled"
        crontab -l | grep "acs_poller"
    else
        log "✗ ACS Poller is NOT scheduled"
    fi

    if crontab -l 2>/dev/null | grep -q "digester"; then
        log "✓ Digester is scheduled"
        crontab -l | grep "digester"
    else
        log "✗ Digester is NOT scheduled"
    fi

    echo ""
    log "Execution schedule:"
    cat << 'EOF'
    DHA Scraper:     Daily at 3:00 AM UTC (15 min timeout)
    State Monitors:  Daily at 3:00 AM UTC (runs parallel, 20 min timeout)
    ACS Poller:      Weekly Friday at 3:00 AM UTC (30 min timeout)
    Digester:        Daily at 5:00 AM UTC (depends on scrapers)
EOF
}

show_help() {
    """Show help message."""
    cat << 'EOF'
Usage: bash setup_scheduler.sh [OPTIONS]

Setup cron scheduler for Visa Agent Phase 1 intelligence pipeline.

Options:
    --install       Install/update cron jobs
    --uninstall     Remove all cron jobs
    --status        Show current cron job status
    --dry-run       Show what would be done without making changes
    --help          Show this help message

Examples:
    # Preview what will be installed
    bash setup_scheduler.sh --install --dry-run

    # Install cron jobs
    bash setup_scheduler.sh --install

    # Check status
    bash setup_scheduler.sh --status

    # Remove cron jobs
    bash setup_scheduler.sh --uninstall

Cron Schedule:
    DHA Scraper:     0 3 * * *   (Daily 3 AM UTC)
    State Monitors:  0 3 * * *   (Daily 3 AM UTC, parallel)
    ACS Poller:      0 3 * * 5   (Weekly Friday 3 AM UTC)
    Digester:        0 5 * * *   (Daily 5 AM UTC)

Logs:
    All output logged to: ./logs/

Notes:
    - Times are UTC (adjust for your timezone)
    - DHA and State monitors run in parallel
    - Digester runs after both complete
    - ACS runs only once weekly (lower API load)

EOF
}

dry_run_mode() {
    """Show what would be done without making changes."""
    log "DRY RUN MODE - No changes will be made"
    echo ""
    log "Setup directories would be created:"
    echo "  - $LOGS_DIR"
    echo "  - $KNOWLEDGE_DIR/raw_dha"
    echo "  - $KNOWLEDGE_DIR/live_cutoffs"
    echo "  - $KNOWLEDGE_DIR/digests"
    echo "  - $KNOWLEDGE_DIR/alerts"
    echo ""

    log "Cron jobs that would be installed:"
    echo ""
    generate_cron_jobs
    echo ""

    log "Log files that would be created:"
    echo "  - $LOGS_DIR/dha_scraper.log"
    echo "  - $LOGS_DIR/state_monitor.log"
    echo "  - $LOGS_DIR/acs_poller.log"
    echo "  - $LOGS_DIR/digester.log"
}

# ===== Main =====

main() {
    local mode="help"
    local dry_run=false

    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            --install)
                mode="install"
                shift
                ;;
            --uninstall)
                mode="uninstall"
                shift
                ;;
            --status)
                mode="status"
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --help|-h)
                mode="help"
                shift
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done

    # Log start
    log "Visa Agent Phase 1 Scheduler Setup"
    log "Agent root: $AGENT_ROOT"
    log "Python: $PYTHON"
    log "Mode: $mode"
    [ "$dry_run" = true ] && log "DRY RUN enabled"
    echo ""

    # Execute mode
    case "$mode" in
        install)
            setup_directories
            verify_dependencies
            if [ "$dry_run" = true ]; then
                dry_run_mode
            else
                install_cron_jobs
                log "✓ Setup complete"
            fi
            ;;
        uninstall)
            if [ "$dry_run" = true ]; then
                log "Would uninstall cron jobs"
            else
                uninstall_cron_jobs
                log "✓ Uninstall complete"
            fi
            ;;
        status)
            show_status
            ;;
        help)
            show_help
            ;;
    esac
}

# Run main function
main "$@"
