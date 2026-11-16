#!/bin/bash
# Visa Agent Virtual Environment Activation Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_PATH" ]; then
    echo "✗ Virtual environment not found at: $VENV_PATH"
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    python3 -m pip install --upgrade pip
    python3 -m pip install -r "$SCRIPT_DIR/requirements.txt"
    python3 -m playwright install chromium
else
    echo "✓ Virtual environment found at: $VENV_PATH"
fi

# Activate venv
source "$VENV_PATH/bin/activate"

echo ""
echo "=========================================="
echo "✓ Visa Agent Environment Activated"
echo "=========================================="
echo ""
echo "Python: $(python3 --version)"
echo "Playwright: $(python3 -c 'from playwright import __version__; print(__version__)' 2>/dev/null || echo 'Not installed')"
echo "BeautifulSoup4: $(python3 -c 'from bs4 import __version__; print(__version__)' 2>/dev/null || echo 'Not installed')"
echo ""
echo "Quick Start:"
echo "  python3 runtime/scrapers/dha_scraper.py --all"
echo "  python3 runtime/scrapers/state_monitor.py --all"
echo ""
