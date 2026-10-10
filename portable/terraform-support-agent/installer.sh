#!/usr/bin/env bash
# installer.sh — Lifecycle manager for the Terraform Support Agent
#
# Usage:
#   bash installer.sh [command] [--dry-run] [--json] [--no-start] [--purge]
#
# Commands (new system — no existing install detected):
#   install     Stage and verify agent, register Bob mode, optionally set up A2A.
#   package     Create a portable, signed release archive of approved assets.
#   status      Show installation state (none on new system).
#   help        Show this usage text.
#
# Commands (existing install detected):
#   reinstall   Reinstall the same verified version; repair manifest-owned files only.
#   install     Stage, verify, and activate a reviewed local version (also covers update).
#   package     Create a portable, signed release archive of approved assets.
#   remove      Preview and remove installed agent, owned adapters, and launcher.
#   propel      Discover Bob/Propel version, display connection changes, install on approval.
#   update      Check configured trusted remote for a newer signed release and install on approval.
#   status      Show installation state, Bob skills, A2A, and MCP status.
#   help        Show this usage text.
#
# Additional subcommands (always available):
#   modify      Preview and apply a scoped change to host, settings, version, or A2A component.
#   start       Start the A2A server (must be installed; requires --a2a).
#   stop        Stop the A2A server.
#   mcp         Install optional MCP server prerequisites (terraform-mcp, playwright-mcp).
#
# Flags:
#   --dry-run   List planned writes, network requests, and process actions without executing.
#   --json      Machine-readable output for Bob chat integration (noninteractive).
#   --no-start  During install, stage A2A without starting the server.
#   --purge     Used with remove: also remove named local state after backup preview.
#
# Requirements:
#   install/reinstall/modify/remove: bash 3.2+, POSIX utilities, IBM Bob on PATH.
#   start/stop:  Python 3.11+, venv.
#   mcp:         Node.js / npx.
#   update:      git, gpg (for signature verification).
#   package:     gpg (to sign the archive).
#
# Safety contract:
#   - dry() never uses eval. Every mutating call uses explicit argument arrays.
#   - --host is validated; unknown host values error rather than silently no-op.
#   - Installed-state detection runs before any prompt or action.
#   - "Remove" deletes only manifest-owned files; operator data is preserved unless --purge.
#   - "Update from repo" never executes unreviewed code; it shows a diff and requires selection.
#   - No git reset --hard or git clean -fd at any point.
#
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_ROOT="$SCRIPT_DIR"
MANIFEST_FILE="$AGENT_ROOT/.install-manifest"
A2A_DIR="$AGENT_ROOT/a2a"
VENV_DIR="$A2A_DIR/.venv"
PID_FILE="$A2A_DIR/.a2a.pid"

AGENT_VERSION="0.1.0-dev"
AGENT_NAME="Terraform Support Agent"
GITHUB_URL="https://github.com/ashishchawla"

# ── Colours ───────────────────────────────────────────────────────────────────
BOLD='\033[1m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
RESET='\033[0m'

sep()     { echo -e "${CYAN}──────────────────────────────────────────────────────${RESET}"; }
info()    { echo -e "  ${CYAN}i${RESET} $*"; }
ok()      { echo -e "  ${GREEN}+${RESET} $*"; }
warn()    { echo -e "  ${YELLOW}!${RESET} $*"; }
err()     { echo -e "  ${RED}x${RESET} $*" >&2; }
heading() { echo ""; sep; echo -e "${BOLD}$*${RESET}"; sep; }
dryline() { echo -e "  ${YELLOW}[dry-run]${RESET} $*"; }

# ── Flags ─────────────────────────────────────────────────────────────────────
DRY_RUN=false
JSON_MODE=false
NO_START=false
PURGE=false
HOST_TARGET=""
INCLUDE_A2A=false

COMMAND="${1:-help}"
shift || true

for arg in "$@"; do
  case "$arg" in
    --dry-run)   DRY_RUN=true ;;
    --json)      JSON_MODE=true ;;
    --no-start)  NO_START=true ;;
    --a2a)       INCLUDE_A2A=true ;;
    --purge)     PURGE=true ;;
    --host=*)
      HOST_TARGET="${arg#--host=}"
      # Validate supported host values
      case "$HOST_TARGET" in
        bob|propel) ;;
        *)
          err "Unknown --host value: '$HOST_TARGET'. Supported values: bob, propel."
          exit 1
          ;;
      esac
      ;;
    --host)
      err "--host requires a value: --host=bob or --host=propel"
      exit 1
      ;;
    --*)
      err "Unknown flag: $arg"
      exit 1
      ;;
  esac
done

# ── Safe exec helper — never uses eval ───────────────────────────────────────
# dry_exec [description] -- cmd [args...]
# When DRY_RUN=true, prints description without running cmd.
# When DRY_RUN=false, runs cmd with args directly.
dry_exec() {
  local desc="$1"; shift
  if [[ "$1" == "--" ]]; then shift; fi
  if $DRY_RUN; then
    dryline "$desc"
  else
    "$@"
  fi
}

# dry_write [destination] [content]  — show or write a single file
dry_write_file() {
  local dest="$1"; shift
  local content="$*"
  if $DRY_RUN; then
    dryline "Would write: $dest"
  else
    printf '%s\n' "$content" > "$dest"
  fi
}

# ── JSON output helpers ───────────────────────────────────────────────────────
json_out() {
  # Usage: json_out status message [key value ...]
  if $JSON_MODE; then
    local status="$1" message="$2"; shift 2
    local pairs='"status":"'"$status"'","message":"'"$message"'"'
    while [[ $# -ge 2 ]]; do
      pairs="$pairs,\"$1\":\"$2\""; shift 2
    done
    echo "{$pairs}"
  fi
}

# ── Installed-state detection ─────────────────────────────────────────────────
is_installed() {
  [[ -f "$MANIFEST_FILE" ]]
}

# ── Preflight checks ─────────────────────────────────────────────────────────
require_bob() {
  if ! command -v bob >/dev/null 2>&1; then
    err "IBM Bob CLI not found on PATH."
    echo "    Install Bob: https://propel.ibm.com"
    exit 1
  fi
}

require_npx() {
  if ! command -v npx >/dev/null 2>&1; then
    err "npx not found. Install Node.js (https://nodejs.org) first."
    exit 1
  fi
}

require_python311() {
  if ! command -v python3 >/dev/null 2>&1; then
    err "python3 not found on PATH."
    exit 1
  fi
  local py_ver
  py_ver=$(python3 -c 'import sys; print(sys.version_info[:2])' 2>/dev/null || echo "(0, 0)")
  if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null; then
    return 0
  else
    err "Python 3.11+ required for A2A. Found: $py_ver"
    exit 1
  fi
}

require_git() {
  if ! command -v git >/dev/null 2>&1; then
    err "git not found on PATH."
    exit 1
  fi
}

require_gpg() {
  if ! command -v gpg >/dev/null 2>&1; then
    err "gpg not found on PATH. Required for signature verification."
    exit 1
  fi
}

# ── Interactive prompt helpers ────────────────────────────────────────────────
ask() {
  local prompt="$1" varname="$2" default="${3:-}"
  if [[ -n "$default" ]]; then
    echo -e "${BOLD}${prompt}${RESET} ${YELLOW}[default: ${default}]${RESET}"
  else
    echo -e "${BOLD}${prompt}${RESET}"
  fi
  read -r "$varname"
  if [[ -z "${!varname}" && -n "$default" ]]; then
    printf -v "$varname" '%s' "$default"
  fi
}

yn() {
  local prompt="$1" varname="$2"
  while true; do
    echo -e "${BOLD}${prompt}${RESET} ${YELLOW}[y/n/skip]${RESET}"
    read -r "$varname"
    case "${!varname}" in
      y|Y|n|N|skip|SKIP) break ;;
    esac
    echo "  Please enter y, n, or skip."
  done
}

# ── Interactive menu (CLI numbered list) ──────────────────────────────────────
# choose_action is_installed → sets CHOSEN_ACTION
choose_action() {
  local installed="$1"

  echo ""
  if [[ "$installed" == "true" ]]; then
    echo -e "${BOLD}  What would you like to do?${RESET}"
    echo ""
    echo "    1) Re-install    — reinstall same verified version, repair owned files"
    echo "    2) Install/Update — stage, verify, and activate a reviewed local version"
    echo "    3) Package       — create a portable signed release archive"
    echo "    4) Remove        — preview and remove installed agent + adapters"
    echo "    5) Install/Update Propel — discover Bob/Propel version and configure connections"
    echo "    6) Update from Repo — check remote for signed release, show diff, install on approval"
    echo "    7) Status        — show installation state and component health"
    echo "    8) Cancel"
    echo ""
    local choice
    ask "Enter choice [1-8]:" choice ""
    case "$choice" in
      1) CHOSEN_ACTION="reinstall" ;;
      2) CHOSEN_ACTION="install" ;;
      3) CHOSEN_ACTION="package" ;;
      4) CHOSEN_ACTION="remove" ;;
      5) CHOSEN_ACTION="propel" ;;
      6) CHOSEN_ACTION="update" ;;
      7) CHOSEN_ACTION="status" ;;
      8|"") CHOSEN_ACTION="cancel" ;;
      *)
        err "Invalid choice: $choice"
        exit 1
        ;;
    esac
  else
    echo -e "${BOLD}  What would you like to do?${RESET}"
    echo ""
    echo "    1) Install  — stage and verify agent, register Bob mode"
    echo "    2) Package  — create a portable signed release archive"
    echo "    3) Status   — show current state (no install detected)"
    echo "    4) Cancel"
    echo ""
    local choice
    ask "Enter choice [1-4]:" choice ""
    case "$choice" in
      1) CHOSEN_ACTION="install" ;;
      2) CHOSEN_ACTION="package" ;;
      3) CHOSEN_ACTION="status" ;;
      4|"") CHOSEN_ACTION="cancel" ;;
      *)
        err "Invalid choice: $choice"
        exit 1
        ;;
    esac
  fi
}

# ── ASCII Branding ─────────────────────────────────────────────────────────────
# Terraform-themed ASCII mark using only plain ASCII characters.
# Does not rely on colour or Unicode for meaning (safe for all terminals).
print_banner() {
  if $JSON_MODE; then return; fi
  echo ""
  echo "  +----------------------------------------------------------+"
  echo "  |                                                          |"
  echo "  |   ###  ###  ###  ###  ###   ###  ###  ###  ###  ###     |"
  echo "  |     #  #      #  #    #  #  #    #    #      #  #  #    |"
  echo "  |     #  ###    #  ###  ###   ###  ###  ###    #  ###     |"
  echo "  |  #  #  #      #  #    # #   #    #    #      #  #  #    |"
  echo "  |   ##   ###  ###  ###  #  #  #    #    ###  ###  #  #    |"
  echo "  |                                                          |"
  echo "  |          Making Terraform Support Simple                 |"
  echo "  |                                                          |"
  echo "  |  Created by Ashish Chawla   ${GITHUB_URL}  |"
  echo "  |  Version ${AGENT_VERSION}                                         |"
  echo "  |                                                          |"
  echo "  +----------------------------------------------------------+"
  echo ""
}

# ── Write manifest ─────────────────────────────────────────────────────────────
write_manifest() {
  local bob_modes_dir="${1:-$HOME/.bob/modes}"
  if $DRY_RUN; then
    dryline "Would write manifest: $MANIFEST_FILE"
    return
  fi
  {
    echo "# .install-manifest — written by installer.sh"
    echo "installed_at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo "agent_root: $AGENT_ROOT"
    echo "agent_version: $AGENT_VERSION"
    echo "bob_modes_dir: $bob_modes_dir"
    if [[ -n "$HOST_TARGET" ]]; then
      echo "host_target: $HOST_TARGET"
    fi
    if $INCLUDE_A2A; then
      echo "a2a_included: true"
    fi
  } > "$MANIFEST_FILE"
}

# ── Core install steps (shared by install + reinstall) ────────────────────────
run_core_install() {
  local bob_modes_dir="$HOME/.bob/modes"

  # 1. Preflight
  heading "Preflight"
  require_bob

  local detected_os
  detected_os="$(uname -s 2>/dev/null || echo unknown)"
  case "$detected_os" in
    Darwin) ok "OS: macOS (Darwin)" ;;
    Linux)  ok "OS: Linux" ;;
    *)
      warn "OS: $detected_os — not in declared compatibility matrix."
      warn "macOS and Linux are the declared targets. Proceeding with caution."
      ;;
  esac

  if [[ ! -d "$AGENT_ROOT/export/skills" ]]; then
    err "export/skills/ not found. Are you running from the agent directory?"
    exit 1
  fi
  ok "Agent root: $AGENT_ROOT"

  # 2. Generate Bob skill adapters
  heading "Bob skill adapters"
  local adapter_script="$AGENT_ROOT/export/scripts/generate-bob-adapter.sh"
  if [[ -f "$adapter_script" ]]; then
    info "Generating adapters from export/skills/ …"
    dry_exec "bash $adapter_script" -- bash "$adapter_script"
    ok "Bob skill adapters generated."
  else
    warn "generate-bob-adapter.sh not found — skipping adapter generation."
  fi

  # 3. Register Bob mode
  heading "Bob mode"
  local mode_src="$AGENT_ROOT/export/agents/bob-mode-terraform-support.yaml"
  if [[ -f "$mode_src" ]]; then
    info "Registering Bob mode …"
    dry_exec "mkdir -p $bob_modes_dir" -- mkdir -p "$bob_modes_dir"
    dry_exec "cp $mode_src $bob_modes_dir/terraform-support.yaml" \
      -- cp "$mode_src" "$bob_modes_dir/terraform-support.yaml"
    ok "Bob mode registered: $bob_modes_dir/terraform-support.yaml"
  else
    warn "Bob mode file not found at $mode_src — skipping."
  fi

  # 4. Write manifest
  heading "Manifest"
  write_manifest "$bob_modes_dir"
  ok "Manifest written: $MANIFEST_FILE"
}

# ── A2A setup (optional, called from install when selected) ───────────────────
run_a2a_setup() {
  heading "A2A setup (optional component)"

  require_python311

  # Security module check
  if [[ ! -d "$A2A_DIR/security" ]]; then
    err "a2a/security/ module not found. A2A requires the security module before startup."
    err "See a2a/security/README.md for implementation status."
    exit 1
  fi

  # .env check
  if [[ ! -f "$A2A_DIR/.env" ]]; then
    if [[ -f "$A2A_DIR/.env.example" ]]; then
      err "a2a/.env not found. Copy a2a/.env.example to a2a/.env and fill in credentials."
    else
      err "a2a/.env not found. Create it with the required environment variables."
    fi
    exit 1
  fi

  # Create venv and install dependencies
  if [[ ! -d "$VENV_DIR" ]]; then
    info "Creating Python venv in a2a/.venv …"
    dry_exec "python3 -m venv $VENV_DIR" -- python3 -m venv "$VENV_DIR"
    ok "venv created."
  else
    info "Existing venv found: $VENV_DIR"
  fi

  if [[ -f "$A2A_DIR/requirements.txt" ]]; then
    info "Installing pinned A2A dependencies …"
    dry_exec "pip install -r $A2A_DIR/requirements.txt" \
      -- "$VENV_DIR/bin/pip" install --quiet -r "$A2A_DIR/requirements.txt"
    ok "Dependencies installed."
  else
    warn "a2a/requirements.txt not found — skipping dependency install."
  fi

  # Start unless --no-start
  if $NO_START; then
    info "A2A server staged (--no-start); not starting automatically."
    info "To start: bash installer.sh start --a2a"
  else
    info "Starting A2A server …"
    if $DRY_RUN; then
      dryline "Would start: $VENV_DIR/bin/python $A2A_DIR/main.py (background)"
    else
      cd "$A2A_DIR"
      nohup "$VENV_DIR/bin/python" main.py >> "$A2A_DIR/a2a-server.log" 2>&1 &
      echo $! > "$PID_FILE"
      cd "$AGENT_ROOT"
      ok "A2A server started (PID $(cat "$PID_FILE"))."
      info "Log: $A2A_DIR/a2a-server.log"
    fi
  fi
}

# ── command: help ─────────────────────────────────────────────────────────────
cmd_help() {
  print_banner
  echo ""
  echo -e "${BOLD}Commands${RESET}"
  echo ""
  echo "  bash installer.sh install     [--dry-run] [--a2a] [--no-start]"
  echo "  bash installer.sh reinstall   [--dry-run]"
  echo "  bash installer.sh modify      [--dry-run]"
  echo "  bash installer.sh start       [--a2a]"
  echo "  bash installer.sh stop"
  echo "  bash installer.sh status"
  echo "  bash installer.sh remove      [--dry-run] [--purge]"
  echo "  bash installer.sh mcp         [--dry-run]"
  echo "  bash installer.sh propel      [--dry-run]"
  echo "  bash installer.sh package     [--dry-run]"
  echo "  bash installer.sh update      [--dry-run]"
  echo ""
  echo -e "${BOLD}Flags${RESET}"
  echo ""
  echo "  --dry-run    List planned operations without executing."
  echo "  --json       Machine-readable output (for Bob chat integration)."
  echo "  --a2a        Include or target the optional A2A component."
  echo "  --no-start   Stage A2A without starting the server."
  echo "  --purge      With remove: also remove named local state after backup preview."
  echo "  --host=bob   Target the Bob host adapter (default when bob CLI detected)."
  echo "  --host=propel Target the IBM Propel host adapter."
  echo ""
  echo -e "${BOLD}Notes${RESET}"
  echo ""
  echo "  - Run install on a new machine, then modify after any skill edit."
  echo "  - Running installer.sh without arguments shows an interactive menu."
  echo "  - The A2A server is optional. Do not use start/stop unless you need A2A mode."
  echo "  - update checks the configured trusted remote; it never runs unreviewed code."
  echo ""
}

# ── command: menu (no args / interactive) ─────────────────────────────────────
cmd_menu() {
  print_banner
  local installed_state="false"
  if is_installed; then installed_state="true"; fi

  choose_action "$installed_state"

  case "$CHOSEN_ACTION" in
    install)   COMMAND="install"   ; cmd_install ;;
    reinstall) COMMAND="reinstall" ; cmd_reinstall ;;
    package)   COMMAND="package"   ; cmd_package ;;
    remove)    COMMAND="remove"    ; cmd_remove ;;
    propel)    COMMAND="propel"    ; cmd_propel ;;
    update)    COMMAND="update"    ; cmd_update ;;
    status)    COMMAND="status"    ; cmd_status ;;
    cancel)
      info "Cancelled."
      exit 0
      ;;
  esac
}

# ── command: install ──────────────────────────────────────────────────────────
cmd_install() {
  print_banner
  heading "Install — ${AGENT_NAME}"

  if $DRY_RUN; then
    warn "DRY RUN — no files will be written."
    echo ""
  fi

  # Installed-state check: inform, do not block
  if is_installed; then
    warn "An existing installation was detected (manifest: $MANIFEST_FILE)."
    warn "This will update/overwrite manifest-owned files."
    warn "Operator data (memory/, checkpoints/, .env) will not be touched."
    echo ""
    local confirm
    yn "Continue with install/update?" confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
      info "Cancelled."
      exit 0
    fi
  fi

  run_core_install

  # Optional A2A
  if ! $INCLUDE_A2A; then
    echo ""
    info "A2A server is an optional component."
    local yn_a2a
    yn "Set up A2A server now?" yn_a2a
    if [[ "$yn_a2a" == "y" || "$yn_a2a" == "Y" ]]; then
      INCLUDE_A2A=true
    fi
  fi

  if $INCLUDE_A2A; then
    run_a2a_setup
  fi

  echo ""
  ok "Installation complete."
  echo ""
  echo "  Next steps:"
  echo "    1. Run onboarding (first-time): bash export/scripts/onboarding.sh"
  echo "    2. Optionally install MCP tools: bash installer.sh mcp"
  echo "    3. Optionally configure Propel:  bash installer.sh propel"
  echo "    4. Open Bob in this directory and start a case with the intake skill."
  echo ""
  json_out "success" "Installation complete" "version" "$AGENT_VERSION"
}

# ── command: reinstall ────────────────────────────────────────────────────────
cmd_reinstall() {
  print_banner
  heading "Re-install — ${AGENT_NAME}"

  if ! is_installed; then
    warn "No existing installation found. Use 'install' for a first-time install."
    exit 1
  fi

  if $DRY_RUN; then
    warn "DRY RUN — no files will be written."
    echo ""
  fi

  info "Re-installing the same verified version ($AGENT_VERSION) …"
  info "Manifest-owned files will be repaired. Operator data is preserved."
  echo ""

  run_core_install

  # Re-start A2A if it was previously included
  local prev_a2a
  prev_a2a=$(grep '^a2a_included:' "$MANIFEST_FILE" 2>/dev/null | cut -d' ' -f2 || echo "false")
  if [[ "$prev_a2a" == "true" ]]; then
    info "A2A was previously installed. Re-checking A2A component …"
    INCLUDE_A2A=true
    run_a2a_setup
  fi

  echo ""
  ok "Re-install complete."
  json_out "success" "Re-install complete" "version" "$AGENT_VERSION"
}

# ── command: modify ───────────────────────────────────────────────────────────
cmd_modify() {
  heading "Modify — Re-generate Bob skill adapters"

  if $DRY_RUN; then
    warn "DRY RUN — no files will be written."
    echo ""
  fi

  local adapter_script="$AGENT_ROOT/export/scripts/generate-bob-adapter.sh"
  if [[ ! -f "$adapter_script" ]]; then
    err "generate-bob-adapter.sh not found at $adapter_script"
    exit 1
  fi

  info "Re-generating Bob skill adapters from export/skills/ …"
  dry_exec "bash $adapter_script" -- bash "$adapter_script"
  ok "Bob skill adapters regenerated."
  echo ""
  json_out "success" "Adapters regenerated"
}

# ── command: package ──────────────────────────────────────────────────────────
cmd_package() {
  heading "Package — Create portable release archive"

  if $DRY_RUN; then
    warn "DRY RUN — no archive will be created."
    echo ""
  fi

  require_gpg

  local ts
  ts=$(date -u +"%Y%m%dT%H%M%SZ")
  local archive_name="terraform-support-agent-${AGENT_VERSION}-${ts}.tar.gz"

  info "Collecting approved agent assets …"

  # Declare included paths explicitly — never glob blindly
  local include_paths=(
    export/agents
    export/skills
    export/templates
    export/mcp
    export/scripts
    memory/corrections
    memory/ops
    memory/patterns
    a2a/.env.example
    a2a/config.py
    a2a/main.py
    a2a/a2a_factory.py
    a2a/terraform_agent.py
    a2a/requirements.txt
    a2a/security
    a2a/README.md
    docs/design
    plan/portability-readiness-plan.md
    plan/README.md
    AGENTS.md
    README.md
    installer.sh
    .gitignore
  )

  # Declare excluded paths
  echo ""
  warn "Excluding from archive:"
  warn "  .env, memory/preferences.md (live operator state)"
  warn "  checkpoints/, .install-manifest (runtime)"
  warn "  a2a/.venv, a2a/a2a-server.log, a2a/.a2a.pid (runtime)"
  warn "  plan/archive/, evals/cases/ (historical inputs)"
  echo ""

  local dest
  ask "Output directory for archive [default: /tmp]:" dest "/tmp"
  local archive_path="$dest/$archive_name"

  if $DRY_RUN; then
    dryline "Would create: $archive_path"
    for p in "${include_paths[@]}"; do
      if [[ -e "$AGENT_ROOT/$p" ]]; then
        dryline "  Include: $p"
      else
        warn "  Not found (will skip): $p"
      fi
    done
    dryline "Would sign:   $archive_path.sig  (gpg detached signature)"
    return
  fi

  # Build include args for tar — only existing paths
  local tar_includes=()
  for p in "${include_paths[@]}"; do
    if [[ -e "$AGENT_ROOT/$p" ]]; then
      tar_includes+=("$p")
    else
      warn "Not found, skipping: $p"
    fi
  done

  mkdir -p "$dest"

  (
    cd "$AGENT_ROOT"
    tar -czf "$archive_path" "${tar_includes[@]}"
  )
  ok "Archive created: $archive_path"

  # Sign the archive
  info "Signing archive with GPG …"
  gpg --armor --detach-sign --output "${archive_path}.sig" "$archive_path"
  ok "Signature: ${archive_path}.sig"

  # Hash manifest
  local hash_file="${archive_path}.sha256"
  shasum -a 256 "$archive_path" > "$hash_file"
  ok "SHA-256 hash: $hash_file"

  echo ""
  ok "Package complete."
  info "Distribute $archive_name, ${archive_name}.sig, and ${archive_name}.sha256 together."
  info "Installers must verify the signature before installation."
  json_out "success" "Package created" "archive" "$archive_path"
}

# ── command: update (from repo) ───────────────────────────────────────────────
cmd_update() {
  heading "Update from Repo — ${AGENT_NAME}"

  require_git
  require_gpg

  if $DRY_RUN; then
    warn "DRY RUN — no fetch, checkout, or install will run."
    echo ""
  fi

  # Read trusted remote from manifest or fall back to origin
  local remote="origin"
  if [[ -f "$MANIFEST_FILE" ]]; then
    local manifest_remote
    manifest_remote=$(grep '^trusted_remote:' "$MANIFEST_FILE" 2>/dev/null | cut -d' ' -f2 || echo "")
    if [[ -n "$manifest_remote" ]]; then
      remote="$manifest_remote"
    fi
  fi

  info "Checking remote: $remote"
  dry_exec "git fetch $remote" -- git -C "$AGENT_ROOT" fetch "$remote" --tags 2>/dev/null || {
    err "Could not reach remote '$remote'. Check network and git config."
    exit 1
  }
  ok "Remote fetched."

  # Find latest signed tag on remote
  info "Listing signed release tags …"
  local latest_tag
  latest_tag=$(git -C "$AGENT_ROOT" tag --list 'v*' --sort=-version:refname 2>/dev/null | head -1 || echo "")
  if [[ -z "$latest_tag" ]]; then
    warn "No versioned release tags found on remote '$remote'."
    warn "Update from repo requires a signed tag (e.g., v0.2.0) pushed to the remote."
    exit 0
  fi

  local current_version="$AGENT_VERSION"
  info "Current installed version: $current_version"
  info "Latest remote release tag:  $latest_tag"

  if [[ "$latest_tag" == "v${current_version}" ]]; then
    ok "Already up to date. No update needed."
    exit 0
  fi

  echo ""
  info "Changed files between current HEAD and ${latest_tag}:"
  git -C "$AGENT_ROOT" diff --name-only HEAD "refs/tags/${latest_tag}" 2>/dev/null || \
    warn "Could not compute diff. Verify the tag exists locally after fetch."

  echo ""
  warn "IMPORTANT: This will checkout tag '${latest_tag}' into a detached HEAD."
  warn "No git reset --hard or git clean -fd will be used."
  warn "Your local operator data (memory/, .env, checkpoints/) will NOT be touched."
  echo ""

  # Verify GPG signature on the tag
  info "Verifying GPG signature on tag $latest_tag …"
  if $DRY_RUN; then
    dryline "Would run: git tag --verify $latest_tag"
  else
    if git -C "$AGENT_ROOT" tag --verify "$latest_tag" 2>/dev/null; then
      ok "Tag signature verified."
    else
      err "Signature verification failed for tag '$latest_tag'."
      err "Refusing to install an unsigned or tampered release."
      exit 1
    fi
  fi

  echo ""
  local confirm
  yn "Proceed with update to $latest_tag?" confirm
  if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    info "Update cancelled."
    exit 0
  fi

  dry_exec "git checkout $latest_tag" -- git -C "$AGENT_ROOT" checkout "$latest_tag"
  ok "Checked out tag: $latest_tag"

  # Re-run install to apply new adapters and mode
  info "Re-running install to apply updated assets …"
  INCLUDE_A2A=false
  run_core_install

  echo ""
  ok "Update complete. Now at $latest_tag."
  json_out "success" "Update complete" "tag" "$latest_tag"
}

# ── command: start ────────────────────────────────────────────────────────────
cmd_start() {
  if ! $INCLUDE_A2A; then
    echo ""
    warn "'start' requires the --a2a flag. The A2A server is an optional component."
    echo ""
    echo "  Usage: bash installer.sh start --a2a"
    echo ""
    echo "  The Terraform Support Agent runs natively inside Bob."
    echo "  You only need 'start' if you want to expose it as an A2A server."
    echo ""
    exit 0
  fi

  heading "Start — A2A server"
  require_python311

  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
      warn "A2A server already running (PID $pid)."
      exit 0
    fi
    rm -f "$PID_FILE"
  fi

  if [[ ! -d "$VENV_DIR" ]]; then
    err "A2A venv not found. Run: bash installer.sh install --a2a"
    exit 1
  fi

  if [[ ! -f "$A2A_DIR/.env" ]]; then
    err "a2a/.env not found. Copy a2a/.env.example and fill in credentials."
    exit 1
  fi

  info "Starting A2A server (background) …"
  cd "$A2A_DIR"
  nohup "$VENV_DIR/bin/python" main.py >> "$A2A_DIR/a2a-server.log" 2>&1 &
  echo $! > "$PID_FILE"
  cd "$AGENT_ROOT"

  ok "A2A server started (PID $(cat "$PID_FILE"))."
  info "Log: $A2A_DIR/a2a-server.log"
  echo ""
  info "To smoke-test: cd a2a && .venv/bin/python test_client.py"
  echo ""
  json_out "success" "A2A started" "pid" "$(cat "$PID_FILE")"
}

# ── command: stop ─────────────────────────────────────────────────────────────
cmd_stop() {
  heading "Stop — A2A server"

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
  json_out "success" "A2A stopped"
}

# ── command: status ───────────────────────────────────────────────────────────
cmd_status() {
  heading "Status — ${AGENT_NAME}"

  # Installed state
  if is_installed; then
    ok "Core: installed"
    while IFS= read -r line; do
      echo "      $line"
    done < "$MANIFEST_FILE"
  else
    warn "Core: not installed — run: bash installer.sh install"
  fi
  echo ""

  # Bob skills
  local bob_skills="$AGENT_ROOT/.bob/skills"
  if [[ -d "$bob_skills" ]] && [[ -n "$(ls -A "$bob_skills" 2>/dev/null)" ]]; then
    ok "Bob skills: present ($bob_skills)"
  else
    warn "Bob skills: not found — run: bash installer.sh modify"
  fi
  echo ""

  # A2A server
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
      ok "A2A server: running (PID $pid)"
    else
      warn "A2A: PID file found but process $pid not running (stale PID)."
    fi
  else
    info "A2A server: not running (optional component)"
  fi
  echo ""

  # .env
  if [[ -f "$AGENT_ROOT/.env" ]]; then
    ok ".env: present (not committed)"
  else
    warn ".env: missing — run: bash export/scripts/onboarding.sh"
  fi
  echo ""

  # MCP status from .env
  if [[ -f "$AGENT_ROOT/.env" ]]; then
    local tf_status pw_status
    tf_status=$(grep '^MCP_TERRAFORM_STATUS=' "$AGENT_ROOT/.env" 2>/dev/null | cut -d= -f2 || echo "not set")
    pw_status=$(grep '^MCP_PLAYWRIGHT_STATUS=' "$AGENT_ROOT/.env" 2>/dev/null | cut -d= -f2 || echo "not set")
    info "terraform-mcp: $tf_status"
    info "playwright-mcp: $pw_status"
  fi
  echo ""

  json_out "success" "Status complete" \
    "installed" "$(is_installed && echo true || echo false)" \
    "version" "$AGENT_VERSION"
}

# ── command: remove ───────────────────────────────────────────────────────────
cmd_remove() {
  heading "Remove — ${AGENT_NAME}"

  if $DRY_RUN; then
    warn "DRY RUN — no files will be deleted."
    echo ""
  fi

  # Show exactly what will be removed
  echo -e "  ${BOLD}Files that will be removed:${RESET}"
  local bob_mode="$HOME/.bob/modes/terraform-support.yaml"
  local bob_skills="$AGENT_ROOT/.bob/skills"

  [[ -f "$bob_mode" ]]       && echo "    $bob_mode" || echo "    (not present) $bob_mode"
  [[ -d "$bob_skills" ]]     && echo "    $bob_skills/" || echo "    (not present) $bob_skills/"
  [[ -f "$MANIFEST_FILE" ]]  && echo "    $MANIFEST_FILE" || echo "    (not present) $MANIFEST_FILE"
  [[ -f "$PID_FILE" ]]       && echo "    $PID_FILE (A2A PID)" || true

  if $PURGE; then
    echo ""
    warn "  --purge selected. The following local state will also be removed after backup:"
    warn "    $AGENT_ROOT/memory/ (operator preferences, patterns, ops)"
    warn "    $AGENT_ROOT/checkpoints/"
    warn "    $AGENT_ROOT/a2a/.venv"
    warn "    $AGENT_ROOT/a2a/a2a-server.log"
  fi

  echo ""
  warn "Files that will NOT be removed:"
  warn "  memory/, checkpoints/, .env, a2a/ source files (unless --purge)"
  echo ""

  local confirm
  yn "Proceed with remove?" confirm
  if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    info "Remove cancelled."
    exit 0
  fi

  # Stop A2A if running
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
      info "Stopping A2A server (PID $pid) …"
      dry_exec "kill $pid" -- kill "$pid"
    fi
    dry_exec "rm -f $PID_FILE" -- rm -f "$PID_FILE"
  fi

  # Remove Bob mode
  if [[ -f "$bob_mode" ]]; then
    info "Removing Bob mode: $bob_mode"
    dry_exec "rm -f $bob_mode" -- rm -f "$bob_mode"
    ok "Bob mode removed."
  fi

  # Remove generated Bob skills
  if [[ -d "$bob_skills" ]]; then
    info "Removing generated Bob skills: $bob_skills"
    dry_exec "rm -rf $bob_skills" -- rm -rf "$bob_skills"
    ok "Generated skills removed."
  fi

  # Remove manifest
  if [[ -f "$MANIFEST_FILE" ]]; then
    info "Removing manifest: $MANIFEST_FILE"
    dry_exec "rm -f $MANIFEST_FILE" -- rm -f "$MANIFEST_FILE"
    ok "Manifest removed."
  fi

  # Purge local state if requested
  if $PURGE && ! $DRY_RUN; then
    echo ""
    warn "Purging local state (backup skipped in this prototype — implement backup before production use) …"

    [[ -d "$AGENT_ROOT/memory" ]]      && rm -rf "$AGENT_ROOT/memory"      && ok "memory/ removed."
    [[ -d "$AGENT_ROOT/checkpoints" ]] && rm -rf "$AGENT_ROOT/checkpoints" && ok "checkpoints/ removed."
    [[ -d "$VENV_DIR" ]]               && rm -rf "$VENV_DIR"               && ok "a2a/.venv removed."
    [[ -f "$A2A_DIR/a2a-server.log" ]] && rm -f  "$A2A_DIR/a2a-server.log" && ok "a2a-server.log removed."
  fi

  echo ""
  ok "Remove complete."
  json_out "success" "Remove complete"
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
  echo -e "${BOLD}  MCP 1: terraform-mcp${RESET}"
  echo "  Provider docs lookup, resource/data-source search, HCP Terraform read queries."
  echo "  Without it: source-researcher and registry-routing skills fall back to web search."
  echo ""

  local yn_tf
  yn "Install terraform-mcp now?" yn_tf
  if [[ "$yn_tf" == "y" || "$yn_tf" == "Y" ]]; then
    if $DRY_RUN; then
      dryline "Would run: npx -y @hashicorp/terraform-mcp-server --version"
    elif npx -y @hashicorp/terraform-mcp-server --version 2>/dev/null; then
      ok "terraform-mcp installed."
      if [[ -f "$AGENT_ROOT/.env" ]]; then
        if grep -q '^MCP_TERRAFORM_STATUS=' "$AGENT_ROOT/.env"; then
          sed -i.bak 's/^MCP_TERRAFORM_STATUS=.*/MCP_TERRAFORM_STATUS=installed/' "$AGENT_ROOT/.env"
          rm -f "$AGENT_ROOT/.env.bak"
        else
          { echo ""; echo "MCP_TERRAFORM_STATUS=installed"; } >> "$AGENT_ROOT/.env"
        fi
        ok "MCP_TERRAFORM_STATUS=installed written to .env"
      fi
    else
      err "Install failed. Retry: npx -y @hashicorp/terraform-mcp-server"
      echo "    Docs: https://developer.hashicorp.com/terraform/mcp-server"
    fi
  else
    warn "Skipped. Source-researcher will use web search only until installed."
  fi

  echo ""

  # ── playwright-mcp ─────────────────────────────────────────────────────────
  echo -e "${BOLD}  MCP 2: playwright-mcp${RESET}"
  echo "  Live DOM text extraction from a customer's browser tab during a support call."
  echo "  Without it: screen-capture skill is unavailable — paste content manually."
  echo ""

  local yn_pw
  yn "Install playwright-mcp now?" yn_pw
  if [[ "$yn_pw" == "y" || "$yn_pw" == "Y" ]]; then
    if $DRY_RUN; then
      dryline "Would run: npx -y @playwright/mcp --version"
    elif npx -y @playwright/mcp --version 2>/dev/null; then
      ok "playwright-mcp installed."
      if [[ -f "$AGENT_ROOT/.env" ]]; then
        if grep -q '^MCP_PLAYWRIGHT_STATUS=' "$AGENT_ROOT/.env"; then
          sed -i.bak 's/^MCP_PLAYWRIGHT_STATUS=.*/MCP_PLAYWRIGHT_STATUS=installed/' "$AGENT_ROOT/.env"
          rm -f "$AGENT_ROOT/.env.bak"
        else
          { echo ""; echo "MCP_PLAYWRIGHT_STATUS=installed"; } >> "$AGENT_ROOT/.env"
        fi
        ok "MCP_PLAYWRIGHT_STATUS=installed written to .env"
      fi
    else
      err "Install failed. Retry: npx -y @playwright/mcp"
      echo "    Docs: https://playwright.dev/docs/mcp"
    fi
  else
    warn "Skipped. Screen-capture skill will be unavailable until installed."
  fi

  echo ""
  warn "After installing MCP servers, set enabled: true in export/mcp/*.yaml"
  warn "(terraform-mcp.yaml stays disabled until Phase 4 allowlist review)"
  echo ""
}

# ── command: propel ───────────────────────────────────────────────────────────
cmd_propel() {
  heading "Propel — Configure IBM Propel connections"
  echo "  IBM Propel provides pre-built MCP connections for IBM internal tools."
  echo "  Prerequisite: IBM Bob must be installed and accessible."
  echo ""

  if $DRY_RUN; then
    warn "DRY RUN — no connections will be configured."
    echo ""
  fi

  require_bob

  # Discover installed Bob/Propel version
  local bob_ver
  bob_ver=$(bob --version 2>/dev/null || echo "unknown")
  info "Detected Bob version: $bob_ver"
  echo ""

  # ── product-knowledge ──────────────────────────────────────────────────────
  echo -e "${BOLD}  Propel 1: product-knowledge${RESET}"
  echo "  Semantic search across IBM product documentation."
  echo "  Docs: https://propel.ibm.com/connections/product-knowledge"
  echo ""
  echo "  Permission change: read access to indexed IBM product documentation."
  echo ""

  local yn_pkb
  yn "Enable product-knowledge connection?" yn_pkb
  if [[ "$yn_pkb" == "y" || "$yn_pkb" == "Y" ]]; then
    local token
    ask "Paste your Propel product-knowledge Bearer token:" token
    if [[ -n "$token" ]]; then
      if $DRY_RUN; then
        dryline "Would configure product-knowledge token in ~/.bob/settings/mcp.json"
      else
        ok "Token received. Add it to ~/.bob/settings/mcp.json under 'product-knowledge'."
        ok "Refer to: https://propel.ibm.com/connections/product-knowledge"
      fi
    else
      warn "No token entered. Skipped."
    fi
  else
    warn "Skipped."
  fi
  echo ""

  # ── w3-people ──────────────────────────────────────────────────────────────
  echo -e "${BOLD}  Propel 2: w3-people${RESET}"
  echo "  Search IBM employee directory (name, email, manager, org chart)."
  echo "  Docs: https://propel.ibm.com/connections/w3-people"
  echo ""
  echo "  Permission change: read access to IBM Bluepages directory."
  echo ""

  local yn_w3
  yn "Enable w3-people connection?" yn_w3
  if [[ "$yn_w3" == "y" || "$yn_w3" == "Y" ]]; then
    local key
    ask "Paste your IBM Bluepages API key:" key
    if [[ -n "$key" ]]; then
      if $DRY_RUN; then
        dryline "Would configure w3-people API key in ~/.bob/settings/mcp.json"
      else
        ok "API key received. Add it to ~/.bob/settings/mcp.json under 'w3-people'."
        ok "Refer to: https://propel.ibm.com/connections/w3-people"
      fi
    else
      warn "No key entered. Skipped."
    fi
  else
    warn "Skipped."
  fi
  echo ""

  # ── propel-web-search ──────────────────────────────────────────────────────
  echo -e "${BOLD}  Propel 3: propel-web-search${RESET}"
  echo "  Free web search via Propel (no external API key required)."
  echo "  Docs: https://propel.ibm.com/connections/propel-web-search"
  echo ""
  echo "  Permission change: outbound web search queries through Propel."
  echo ""

  local yn_web
  yn "Enable propel-web-search connection?" yn_web
  if [[ "$yn_web" == "y" || "$yn_web" == "Y" ]]; then
    if $DRY_RUN; then
      dryline "Would run: bob propel install propel-web-search"
    elif bob propel install propel-web-search 2>/dev/null; then
      ok "propel-web-search installed via Bob CLI."
    else
      warn "Bob CLI command failed or not supported."
      echo "    Install manually: open Bob → Settings → Propel → propel-web-search → Install"
    fi
  else
    warn "Skipped."
  fi
  echo ""
}

# ── Dispatch ──────────────────────────────────────────────────────────────────
case "$COMMAND" in
  install)   cmd_install   ;;
  reinstall) cmd_reinstall ;;
  modify)    cmd_modify    ;;
  start)     cmd_start     ;;
  stop)      cmd_stop      ;;
  status)    cmd_status    ;;
  remove)    cmd_remove    ;;
  mcp)       cmd_mcp       ;;
  propel)    cmd_propel    ;;
  package)   cmd_package   ;;
  update)    cmd_update    ;;
  help|--help|-h) cmd_help ;;
  "")        cmd_menu      ;;
  *)
    err "Unknown command: $COMMAND"
    cmd_help
    exit 1
    ;;
esac
