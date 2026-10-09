#!/usr/bin/env bash
# installer.sh — Lifecycle manager for the Terraform Support Agent
#
# Usage:
#   bash installer.sh install   [--dry-run] [--host bob]
#   bash installer.sh modify    [--dry-run]
#   bash installer.sh start     [--a2a]
#   bash installer.sh stop      [--a2a]
#   bash installer.sh status
#   bash installer.sh remove    [--dry-run]
#   bash installer.sh mcp       [--dry-run]
#   bash installer.sh propel    [--dry-run]
#
# Commands:
#   install   Copy skills to Bob, register mode, create manifest.
#   modify    Re-run Bob adapter generation after skill edits.
#   start     Start the A2A server (--a2a flag required for A2A component).
#   stop      Stop the A2A server.
#   status    Show which components are installed and running.
#   remove    Unregister and clean up installed files (dry-run safe).
#   mcp       Install MCP server prerequisites (terraform-mcp, playwright-mcp).
#   propel    Configure IBM Propel connections (product-knowledge, w3-people, propel-web-search).
#
# Requirements: bash 3.2+, standard POSIX utilities.
#               For 'install': IBM Bob must be installed (bob CLI on PATH).
#               For 'mcp':     Node.js / npx must be available.
#               For 'propel':  IBM Bob must be installed.
#               For 'start':   Python 3.11+ and venv must be available.
#
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_ROOT="$SCRIPT_DIR"
MANIFEST_FILE="$AGENT_ROOT/.install-manifest"

# ── Colours ───────────────────────────────────────────────────────────────────
BOLD='\033[1m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
RESET='\033[0m'

sep()     { echo -e "${CYAN}──────────────────────────────────────────────────────${RESET}"; }
info()    { echo -e "  ${CYAN}→${RESET} $*"; }
ok()      { echo -e "  ${GREEN}✓${RESET} $*"; }
warn()    { echo -e "  ${YELLOW}⚠${RESET} $*"; }
err()     { echo -e "  ${RED}✗${RESET} $*" >&2; }
heading() { echo ""; sep; echo -e "${BOLD}$*${RESET}"; sep; }

DRY_RUN=false
START_A2A=false

# ── Parse flags ───────────────────────────────────────────────────────────────
COMMAND="${1:-help}"
shift || true

for arg in "$@"; do
  case "$arg" in
    --dry-run)  DRY_RUN=true ;;
    --a2a)      START_A2A=true ;;
    --host)     : ;;   # accepted, currently no-op (future multi-host support)
    --host=*)   : ;;
    *)          : ;;
  esac
done

dry() {
  if $DRY_RUN; then
    echo -e "  ${YELLOW}[dry-run]${RESET} $*"
  else
    eval "$@"
  fi
}

# ── Helpers ───────────────────────────────────────────────────────────────────
require_bob() {
  if ! command -v bob >/dev/null 2>&1; then
    err "IBM Bob CLI not found on PATH."
    echo "    Install Bob first: https://propel.ibm.com"
    exit 1
  fi
}

require_npx() {
  if ! command -v npx >/dev/null 2>&1; then
    err "npx not found. Install Node.js (https://nodejs.org) first."
    exit 1
  fi
}

require_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    err "python3 not found."
    exit 1
  fi
}

ask() {
  local prompt="$1" var="$2" default="${3:-}"
  if [[ -n "$default" ]]; then
    echo -e "${BOLD}$prompt${RESET} ${YELLOW}[default: $default]${RESET}"
  else
    echo -e "${BOLD}$prompt${RESET}"
  fi
  read -r "$var"
  if [[ -z "${!var}" && -n "$default" ]]; then
    printf -v "$var" '%s' "$default"
  fi
}

yn() {
  local prompt="$1" var="$2"
  while true; do
    echo -e "${BOLD}$prompt${RESET} ${YELLOW}[y/n/skip]${RESET}"
    read -r "$var"
    case "${!var}" in y|n|skip|Y|N|SKIP) break ;; esac
    echo "  Please enter y, n, or skip."
  done
}

# ── command: help ─────────────────────────────────────────────────────────────
cmd_help() {
  echo ""
  echo -e "${BOLD}Terraform Support Agent — installer.sh${RESET}"
  echo ""
  echo "  bash installer.sh install   [--dry-run]   Install skills + Bob mode"
  echo "  bash installer.sh modify    [--dry-run]   Re-generate Bob skill adapters"
  echo "  bash installer.sh start     [--a2a]       Start A2A server (--a2a flag required)"
  echo "  bash installer.sh stop      [--a2a]       Stop A2A server"
  echo "  bash installer.sh status                  Show installation + process status"
  echo "  bash installer.sh remove    [--dry-run]   Uninstall skills and clean up"
  echo "  bash installer.sh mcp       [--dry-run]   Install MCP server prerequisites"
  echo "  bash installer.sh propel    [--dry-run]   Configure IBM Propel connections"
  echo ""
  echo "  Notes:"
  echo "    - Run 'install' once on a new machine, then 'modify' after any skill edit."
  echo "    - The A2A server is optional. Do not run 'start' unless you need A2A mode."
  echo "    - 'mcp' and 'propel' are independent of Bob install — run them at any time."
  echo ""
}

# ── command: install ──────────────────────────────────────────────────────────
cmd_install() {
  heading "Install — Terraform Support Agent"

  if $DRY_RUN; then
    warn "DRY RUN — no files will be written."
    echo ""
  fi

  require_bob

  # 1. Run Bob adapter generation
  info "Generating Bob skill adapters from export/skills/ …"
  dry "bash \"$AGENT_ROOT/export/scripts/generate-bob-adapter.sh\""
  ok "Bob skill adapters generated."

  # 2. Register Bob mode
  local MODE_SRC="$AGENT_ROOT/export/agents/bob-mode-terraform-support.yaml"
  local BOB_MODES_DIR="$HOME/.bob/modes"
  if [[ -f "$MODE_SRC" ]]; then
    info "Registering Bob mode from $MODE_SRC …"
    dry "mkdir -p \"$BOB_MODES_DIR\""
    dry "cp \"$MODE_SRC\" \"$BOB_MODES_DIR/terraform-support.yaml\""
    ok "Bob mode registered: $BOB_MODES_DIR/terraform-support.yaml"
  else
    warn "Bob mode file not found at $MODE_SRC — skipping mode registration."
  fi

  # 3. Write manifest
  if ! $DRY_RUN; then
    {
      echo "# install-manifest — written by installer.sh install"
      echo "installed_at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
      echo "agent_root: $AGENT_ROOT"
      echo "bob_modes_dir: $BOB_MODES_DIR"
    } > "$MANIFEST_FILE"
  else
    info "[dry-run] Would write: $MANIFEST_FILE"
  fi

  echo ""
  ok "Installation complete."
  echo ""
  echo "  Next steps:"
  echo "    1. Run onboarding (first-time):  bash export/scripts/onboarding.sh"
  echo "    2. Optionally install MCP tools: bash installer.sh mcp"
  echo "    3. Optionally configure Propel:  bash installer.sh propel"
  echo "    4. Open Bob in this directory and start a case with the intake skill."
  echo ""
}

# ── command: modify ───────────────────────────────────────────────────────────
cmd_modify() {
  heading "Modify — Re-generate Bob skill adapters"

  if $DRY_RUN; then
    warn "DRY RUN — no files will be written."
    echo ""
  fi

  info "Re-generating Bob skill adapters from export/skills/ …"
  dry "bash \"$AGENT_ROOT/export/scripts/generate-bob-adapter.sh\""
  ok "Bob skill adapters regenerated."
  echo ""
}

# ── command: start ────────────────────────────────────────────────────────────
cmd_start() {
  if ! $START_A2A; then
    echo ""
    warn "'start' requires the --a2a flag. The A2A server is an optional component."
    echo "  Usage: bash installer.sh start --a2a"
    echo ""
    echo "  The Terraform Support Agent runs natively inside Bob."
    echo "  You only need 'start' if you want to expose the agent as an A2A server"
    echo "  (e.g. to accept calls from other agents or frameworks)."
    echo ""
    exit 0
  fi

  heading "Start — A2A server"

  require_python

  local A2A_DIR="$AGENT_ROOT/a2a"
  local VENV_DIR="$A2A_DIR/.venv"
  local PID_FILE="$A2A_DIR/.a2a.pid"

  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
      warn "A2A server is already running (PID $pid)."
      exit 0
    fi
    rm -f "$PID_FILE"
  fi

  if [[ ! -d "$VENV_DIR" ]]; then
    info "Creating Python venv in a2a/.venv …"
    python3 -m venv "$VENV_DIR"
    ok "venv created."
    info "Installing A2A dependencies …"
    "$VENV_DIR/bin/pip" install --quiet -r "$A2A_DIR/requirements.txt"
    ok "Dependencies installed."
  fi

  if [[ ! -f "$A2A_DIR/.env" ]]; then
    if [[ -f "$A2A_DIR/.env.example" ]]; then
      err "a2a/.env not found. Copy a2a/.env.example to a2a/.env and fill in your credentials."
    else
      err "a2a/.env not found. Create it with the required environment variables."
    fi
    exit 1
  fi

  info "Starting A2A server (background) …"
  cd "$A2A_DIR"
  nohup "$VENV_DIR/bin/python" main.py >> "$A2A_DIR/a2a-server.log" 2>&1 &
  echo $! > "$PID_FILE"
  cd "$AGENT_ROOT"

  ok "A2A server started (PID $(cat "$PID_FILE"))."
  info "Log: $A2A_DIR/a2a-server.log"
  info "PID: $PID_FILE"
  echo ""
  info "To smoke-test: cd a2a && ../.venv/bin/python test_client.py"
  echo ""
}

# ── command: stop ─────────────────────────────────────────────────────────────
cmd_stop() {
  heading "Stop — A2A server"

  local PID_FILE="$AGENT_ROOT/a2a/.a2a.pid"

  if [[ ! -f "$PID_FILE" ]]; then
    warn "No PID file found at $PID_FILE — server may not be running."
    exit 0
  fi

  local pid
  pid=$(cat "$PID_FILE")

  if kill -0 "$pid" 2>/dev/null; then
    info "Stopping A2A server (PID $pid) …"
    kill "$pid"
    rm -f "$PID_FILE"
    ok "A2A server stopped."
  else
    warn "Process $pid not found — already stopped."
    rm -f "$PID_FILE"
  fi
  echo ""
}

# ── command: status ───────────────────────────────────────────────────────────
cmd_status() {
  heading "Status — Terraform Support Agent"

  # Manifest
  if [[ -f "$MANIFEST_FILE" ]]; then
    ok "Installed (manifest: $MANIFEST_FILE)"
    while IFS= read -r line; do
      echo "    $line"
    done < "$MANIFEST_FILE"
  else
    warn "Not installed — run: bash installer.sh install"
  fi

  echo ""

  # Bob skills
  local BOB_SKILLS="$AGENT_ROOT/.bob/skills"
  if [[ -d "$BOB_SKILLS" ]] && [[ -n "$(ls -A "$BOB_SKILLS" 2>/dev/null)" ]]; then
    ok "Bob skills present: $BOB_SKILLS"
  else
    warn "Bob skills not found — run: bash installer.sh modify"
  fi

  echo ""

  # A2A server
  local PID_FILE="$AGENT_ROOT/a2a/.a2a.pid"
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
      ok "A2A server running (PID $pid)"
    else
      warn "A2A PID file found but process $pid is not running — stale PID."
    fi
  else
    info "A2A server: not running (optional component)"
  fi

  echo ""

  # .env
  if [[ -f "$AGENT_ROOT/.env" ]]; then
    ok ".env present (not committed)"
  else
    warn ".env missing — run: bash export/scripts/onboarding.sh"
  fi

  # MCP status from .env
  if [[ -f "$AGENT_ROOT/.env" ]]; then
    local tf_status pw_status
    tf_status=$(grep '^MCP_TERRAFORM_STATUS=' "$AGENT_ROOT/.env" 2>/dev/null | cut -d= -f2 || echo "unknown")
    pw_status=$(grep '^MCP_PLAYWRIGHT_STATUS=' "$AGENT_ROOT/.env" 2>/dev/null | cut -d= -f2 || echo "unknown")
    info "terraform-mcp status: ${tf_status:-not set}"
    info "playwright-mcp status: ${pw_status:-not set}"
  fi

  echo ""
}

# ── command: remove ───────────────────────────────────────────────────────────
cmd_remove() {
  heading "Remove — Terraform Support Agent"

  if $DRY_RUN; then
    warn "DRY RUN — no files will be deleted."
    echo ""
  fi

  # Stop A2A if running
  local PID_FILE="$AGENT_ROOT/a2a/.a2a.pid"
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
      info "Stopping A2A server (PID $pid) …"
      dry "kill $pid"
    fi
    dry "rm -f \"$PID_FILE\""
  fi

  # Remove Bob mode
  local BOB_MODE="$HOME/.bob/modes/terraform-support.yaml"
  if [[ -f "$BOB_MODE" ]]; then
    info "Removing Bob mode: $BOB_MODE"
    dry "rm -f \"$BOB_MODE\""
    ok "Bob mode removed."
  fi

  # Remove generated Bob skills (these are regenerated by generate-bob-adapter.sh)
  local BOB_SKILLS="$AGENT_ROOT/.bob/skills"
  if [[ -d "$BOB_SKILLS" ]]; then
    info "Removing generated Bob skills: $BOB_SKILLS"
    dry "rm -rf \"$BOB_SKILLS\""
    ok "Generated skills removed."
  fi

  # Remove manifest
  if [[ -f "$MANIFEST_FILE" ]]; then
    info "Removing manifest: $MANIFEST_FILE"
    dry "rm -f \"$MANIFEST_FILE\""
    ok "Manifest removed."
  fi

  echo ""
  ok "Remove complete."
  warn ".env, memory/, checkpoints/, and a2a/ source files were NOT deleted."
  warn "To fully clean A2A venv: rm -rf a2a/.venv a2a/a2a-server.log"
  echo ""
}

# ── command: mcp ──────────────────────────────────────────────────────────────
cmd_mcp() {
  heading "MCP — Install optional MCP server prerequisites"
  echo "  These unlock additional agent capabilities but are not required for basic use."
  echo ""

  if $DRY_RUN; then
    warn "DRY RUN — no packages will be installed."
    echo ""
  fi

  require_npx

  # ── terraform-mcp ──────────────────────────────────────────────────────────
  echo -e "${BOLD}MCP 1: terraform-mcp${RESET}"
  echo "  Provider docs lookup, resource/data-source search, HCP Terraform read queries."
  echo "  Without it: source-researcher and registry-routing skills fall back to web search."
  echo ""

  local yn_tf
  yn "Install terraform-mcp now?" yn_tf
  if [[ "$yn_tf" == "y" ]]; then
    info "Running: npx -y @hashicorp/terraform-mcp-server --version"
    if $DRY_RUN; then
      info "[dry-run] Would run: npx -y @hashicorp/terraform-mcp-server --version"
    elif npx -y @hashicorp/terraform-mcp-server --version 2>/dev/null; then
      ok "terraform-mcp installed."
      # Write status to .env if present
      if [[ -f "$AGENT_ROOT/.env" ]]; then
        if grep -q '^MCP_TERRAFORM_STATUS=' "$AGENT_ROOT/.env"; then
          sed -i.bak 's/^MCP_TERRAFORM_STATUS=.*/MCP_TERRAFORM_STATUS=installed/' "$AGENT_ROOT/.env"
          rm -f "$AGENT_ROOT/.env.bak"
        else
          echo "" >> "$AGENT_ROOT/.env"
          echo "MCP_TERRAFORM_STATUS=installed" >> "$AGENT_ROOT/.env"
        fi
        ok "MCP_TERRAFORM_STATUS=installed written to .env"
      fi
    else
      err "Install failed. Retry manually: npx -y @hashicorp/terraform-mcp-server"
      echo "    Docs: https://developer.hashicorp.com/terraform/mcp-server"
    fi
  else
    warn "Skipped. Source-researcher will use web search only until installed."
  fi

  echo ""

  # ── playwright-mcp ─────────────────────────────────────────────────────────
  echo -e "${BOLD}MCP 2: playwright-mcp${RESET}"
  echo "  Live DOM text extraction from a customer's browser tab during a support call."
  echo "  Without it: screen-capture skill is unavailable — paste content manually."
  echo ""

  local yn_pw
  yn "Install playwright-mcp now?" yn_pw
  if [[ "$yn_pw" == "y" ]]; then
    info "Running: npx -y @playwright/mcp --version"
    if $DRY_RUN; then
      info "[dry-run] Would run: npx -y @playwright/mcp --version"
    elif npx -y @playwright/mcp --version 2>/dev/null; then
      ok "playwright-mcp installed."
      if [[ -f "$AGENT_ROOT/.env" ]]; then
        if grep -q '^MCP_PLAYWRIGHT_STATUS=' "$AGENT_ROOT/.env"; then
          sed -i.bak 's/^MCP_PLAYWRIGHT_STATUS=.*/MCP_PLAYWRIGHT_STATUS=installed/' "$AGENT_ROOT/.env"
          rm -f "$AGENT_ROOT/.env.bak"
        else
          echo "" >> "$AGENT_ROOT/.env"
          echo "MCP_PLAYWRIGHT_STATUS=installed" >> "$AGENT_ROOT/.env"
        fi
        ok "MCP_PLAYWRIGHT_STATUS=installed written to .env"
      fi
    else
      err "Install failed. Retry manually: npx -y @playwright/mcp"
      echo "    Docs: https://playwright.dev/docs/mcp"
    fi
  else
    warn "Skipped. Screen-capture skill will be unavailable until installed."
  fi

  echo ""
  echo -e "${YELLOW}NOTE: After installing MCP servers, set enabled: true in export/mcp/*.yaml${RESET}"
  echo -e "${YELLOW}      (terraform-mcp.yaml stays disabled until Phase 4 allowlist review)${RESET}"
  echo ""
}

# ── command: propel ───────────────────────────────────────────────────────────
cmd_propel() {
  heading "Propel — Configure IBM Propel connections"
  echo "  IBM Propel provides pre-built MCP connections for IBM internal tools."
  echo "  Prerequisite: IBM Bob must be installed."
  echo ""

  if $DRY_RUN; then
    warn "DRY RUN — no connections will be configured."
    echo ""
  fi

  require_bob

  # ── product-knowledge ──────────────────────────────────────────────────────
  echo -e "${BOLD}Propel 1: product-knowledge${RESET}"
  echo "  Semantic search across IBM product documentation (Instana, watsonx.ai, etc.)"
  echo "  Useful for researching IBM-side context when customers mix Terraform with IBM products."
  echo "  Docs: https://propel.ibm.com/connections/product-knowledge"
  echo ""

  local yn_pkb
  yn "Enable product-knowledge connection?" yn_pkb
  if [[ "$yn_pkb" == "y" ]]; then
    local token
    ask "Paste your Propel product-knowledge Bearer token (from propel.ibm.com → API Keys):" token
    if [[ -n "$token" ]]; then
      if $DRY_RUN; then
        info "[dry-run] Would write token to ~/.bob/settings/mcp.json under 'product-knowledge'."
      else
        ok "Token received. Add it to ~/.bob/settings/mcp.json under 'product-knowledge'."
        ok "Refer to Bob docs: https://propel.ibm.com/connections/product-knowledge"
      fi
    else
      warn "No token entered. Skipped."
    fi
  else
    warn "Skipped."
  fi

  echo ""

  # ── w3-people ──────────────────────────────────────────────────────────────
  echo -e "${BOLD}Propel 2: w3-people${RESET}"
  echo "  Search IBM employee directory (name, email, manager, org chart)."
  echo "  Useful for looking up IBM team members or escalation contacts."
  echo "  Docs: https://propel.ibm.com/connections/w3-people"
  echo ""

  local yn_w3
  yn "Enable w3-people connection?" yn_w3
  if [[ "$yn_w3" == "y" ]]; then
    local key
    ask "Paste your IBM Bluepages API key (from w3id settings):" key
    if [[ -n "$key" ]]; then
      if $DRY_RUN; then
        info "[dry-run] Would write API key to ~/.bob/settings/mcp.json under 'w3-people'."
      else
        ok "API key received. Add it to ~/.bob/settings/mcp.json under 'w3-people'."
        ok "Refer to Bob docs: https://propel.ibm.com/connections/w3-people"
      fi
    else
      warn "No key entered. Skipped."
    fi
  else
    warn "Skipped."
  fi

  echo ""

  # ── propel-web-search ──────────────────────────────────────────────────────
  echo -e "${BOLD}Propel 3: propel-web-search${RESET}"
  echo "  Free web search via Propel (no external API key required)."
  echo "  Useful for searching HashiCorp docs, GitHub issues, and status pages."
  echo "  Docs: https://propel.ibm.com/connections/propel-web-search"
  echo ""

  local yn_web
  yn "Enable propel-web-search connection?" yn_web
  if [[ "$yn_web" == "y" ]]; then
    if $DRY_RUN; then
      info "[dry-run] Would run: bob propel install propel-web-search"
    elif command -v bob >/dev/null 2>&1 && bob propel install propel-web-search 2>/dev/null; then
      ok "propel-web-search installed via Bob CLI."
    else
      warn "Bob CLI not found or install failed."
      echo "    Install manually: open Bob → Settings → Propel → propel-web-search → Install"
    fi
  else
    warn "Skipped."
  fi

  echo ""
}

# ── Dispatch ──────────────────────────────────────────────────────────────────
case "$COMMAND" in
  install)  cmd_install ;;
  modify)   cmd_modify  ;;
  start)    cmd_start   ;;
  stop)     cmd_stop    ;;
  status)   cmd_status  ;;
  remove)   cmd_remove  ;;
  mcp)      cmd_mcp     ;;
  propel)   cmd_propel  ;;
  help|--help|-h) cmd_help ;;
  *)
    err "Unknown command: $COMMAND"
    cmd_help
    exit 1
    ;;
esac
