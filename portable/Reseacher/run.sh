#!/usr/bin/env bash
# ==============================================================================
# Master Certification Retrieval & Curation Agent - CLI Runner
# Proven build for Codex, Claude, Antigravity (AGY) - November 2026 Ready
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Detect Python 3.11+
PYTHON_BIN=""
if command -v /opt/homebrew/bin/python3.11 >/dev/null 2>&1; then
    PYTHON_BIN="/opt/homebrew/bin/python3.11"
elif command -v python3.11 >/dev/null 2>&1; then
    PYTHON_BIN="python3.11"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    echo "[-] Error: Python 3 not found in PATH." >&2
    exit 1
fi

VENV_DIR="$SCRIPT_DIR/.venv"

setup_venv() {
    if [[ ! -d "$VENV_DIR" ]]; then
        echo "[+] Creating virtual environment with $PYTHON_BIN..."
        "$PYTHON_BIN" -m venv "$VENV_DIR"
        "$VENV_DIR/bin/pip" install --upgrade pip >/dev/null 2>&1
        echo "[+] Installing core dependencies..."
        "$VENV_DIR/bin/pip" install -r requirements.txt
    fi
}

show_help() {
    cat <<EOF
Master Certification Retrieval & Curation Agent (Deep-Web Scraper Variant)

Usage:
  ./run.sh setup                 Initialize virtualenv and install dependencies
  ./run.sh test                  Execute test suite (unit & taxonomy validation)
  ./run.sh crawl [query]         Run autonomous deep-web crawl and curation
  ./run.sh export                Display the latest curated markdown matrix
  ./run.sh help                  Display this help message

Environment:
  Copy .env.example to .env and configure your TAVILY_API_KEY, FIRECRAWL_API_KEY,
  and chosen LLM API key (GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY).
EOF
}

CMD="${1:-help}"

case "$CMD" in
    setup)
        setup_venv
        echo "[✓] Environment initialized successfully."
        ;;
    test)
        setup_venv
        echo "[+] Running test suite..."
        "$VENV_DIR/bin/pytest" tests/ -v
        ;;
    crawl)
        setup_venv
        shift || true
        TARGET_QUERY="${*:-Kubernetes DevSecOps}"
        echo "[+] Triggering Orchestrator with query: '$TARGET_QUERY'"
        "$VENV_DIR/bin/python" harness/orchestrator.py "$TARGET_QUERY"
        ;;
    export)
        if [[ -f "output/curated_matrix.md" ]]; then
            cat output/curated_matrix.md
        else
            echo "[-] No output found. Run './run.sh crawl' first."
        fi
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "[-] Unknown command: $CMD"
        show_help
        exit 1
        ;;
esac
