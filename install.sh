#!/usr/bin/env bash
# install.sh — STF agent installer (interactive CLI)
#
# Interactively selects an agent from portable/ and installs its skills to the
# appropriate host application directories. No agent is activated, no network
# calls are made, and no home directory changes are committed to this repository.
#
# Supported host applications and their skill paths:
#   IBM Bob         ~/.bob/skills/<skill_id>/SKILL.md
#   Codex           ~/.agents/skills/<skill_id>/SKILL.md
#   Google Gemini   ~/.gemini/config/skills/<skill_id>/SKILL.md
#   OpenCode        ~/.config/opencode/skills/<skill_id>/SKILL.md
#   Claude Code     ~/.claude/skills/<skill_id>/SKILL.md
#
# Reference: plan.md §11.2 (canonical install paths), §13 (interactive installer intent)
# Reference: docs/architecture.md (portability boundaries)
#
# Safety constraints (from AGENTS.md and docs/security.md):
#   - No runnable agent is created or activated as part of this script
#   - No MCP server is connected
#   - No network devices are accessed
#   - Home directory changes are install-only; they are NOT committed to this repo
#   - Credentials and tokens must never be copied by this script
#   - The ~/.stf/ runtime installation is a separate, versioned promotion step
#
# Status: Phase 3 active — prerequisites check, plan preview, and actual skill
#         file copy to selected host application directories.
# Compatible with bash 3.2+ (macOS default shell).
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Colour helpers (graceful degradation if terminal has no colour) ────────────
if command -v tput &>/dev/null && tput colors &>/dev/null 2>&1 && [[ "$(tput colors)" -ge 8 ]]; then
  BOLD="$(tput bold)"    ; RESET="$(tput sgr0)"
  GREEN="$(tput setaf 2)"; YELLOW="$(tput setaf 3)"; RED="$(tput setaf 1)"
  CYAN="$(tput setaf 6)" ; DIM="$(tput dim)"
else
  BOLD="" ; RESET="" ; GREEN="" ; YELLOW="" ; RED="" ; CYAN="" ; DIM=""
fi

print_header() { echo "${BOLD}${CYAN}$*${RESET}"; }
print_ok()     { echo "${GREEN}  ✓${RESET} $*"; }
print_warn()   { echo "${YELLOW}  ⚠${RESET}  $*"; }
print_err()    { echo "${RED}  ✗${RESET} $*"; }
print_dim()    { echo "${DIM}    $*${RESET}"; }

# ── Locate repo root ───────────────────────────────────────────────────────────
if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
  REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
  REPO_ROOT="$(pwd)"
fi
PORTABLE_DIR="$REPO_ROOT/portable"

# If running via curl | bash outside an existing clone, download a shallow clone
CLEANUP_TEMP=false
if [[ ! -d "$PORTABLE_DIR" ]]; then
  print_header "Remote installation detected — fetching latest STF repository..."
  TEMP_CLONE="$(mktemp -d /tmp/stf-install-XXXXXX)"
  CLEANUP_TEMP=true
  trap 'if $CLEANUP_TEMP && [[ -d "$TEMP_CLONE" ]]; then rm -rf "$TEMP_CLONE"; fi' EXIT INT TERM
  git clone --depth 1 https://github.com/imashishchawla/STF-SpecialTaskForce.git "$TEMP_CLONE" >/dev/null 2>&1 || {
    print_err "Failed to clone repository from https://github.com/imashishchawla/STF-SpecialTaskForce.git"
    exit 1
  }
  REPO_ROOT="$TEMP_CLONE"
  PORTABLE_DIR="$REPO_ROOT/portable"
fi

# ── Parse flags ───────────────────────────────────────────────────────────────
DRY_RUN=false
VERBOSE=false
NON_INTERACTIVE=false
SELECTED_AGENT=""
SELECTED_HOSTS=""

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  --dry-run             Show what would be installed without writing any files
  --agent <name>        Select agent non-interactively (must match portable/<name>/)
  --hosts <list>        Comma-separated hosts: bob,codex,gemini,opencode,claude (default: prompt)
  --yes                 Non-interactive: skip confirmation prompts
  --verbose             Show detailed output
  -h, --help            Show this help

Examples:
  bash install.sh                                   # interactive mode
  bash install.sh --dry-run                         # preview only
  bash install.sh --agent terraform-support-agent --hosts bob --dry-run
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)       DRY_RUN=true ;;
    --verbose)       VERBOSE=true ;;
    --yes)           NON_INTERACTIVE=true ;;
    --agent)         SELECTED_AGENT="${2:-}"; shift ;;
    --hosts)         SELECTED_HOSTS="${2:-}"; shift ;;
    -h|--help)       usage ;;
    *) echo "Unknown option: $1" >&2; usage ;;
  esac
  shift
done

# ── Banner ─────────────────────────────────────────────────────────────────────
echo ""
print_header "╔══════════════════════════════════════════════════════╗"
print_header "║           STF Agent Installer  (v0.2-phase3)         ║"
print_header "╚══════════════════════════════════════════════════════╝"
echo ""
[[ "$DRY_RUN" == true ]] && print_warn "DRY-RUN mode — no files will be written"
echo ""

# ── Discover available agents ─────────────────────────────────────────────────
declare -a AGENTS=()
if [[ -d "$PORTABLE_DIR" ]]; then
  while IFS= read -r -d '' dir; do
    name="$(basename "$dir")"
    if compgen -G "$dir/export/skills/*.md" > /dev/null 2>&1; then
      AGENTS+=("$name")
    fi
  done < <(find "$PORTABLE_DIR" -mindepth 1 -maxdepth 1 -type d -print0 | sort -z)
fi

if [[ ${#AGENTS[@]} -eq 0 ]]; then
  print_err "No installable agents found in $PORTABLE_DIR"
  print_dim "An agent directory must contain export/skills/*.md to be installable."
  exit 1
fi

# ── Agent selection ───────────────────────────────────────────────────────────
if [[ -n "$SELECTED_AGENT" ]]; then
  if [[ ! -d "$PORTABLE_DIR/$SELECTED_AGENT" ]]; then
    print_err "Agent not found: $SELECTED_AGENT"
    exit 1
  fi
  AGENT_NAME="$SELECTED_AGENT"
else
  print_header "Available agents:"
  for i in "${!AGENTS[@]}"; do
    echo "  $((i+1)). ${AGENTS[$i]}"
  done
  echo ""
  while true; do
    read -r -p "Select agent [1–${#AGENTS[@]}]: " choice
    if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#AGENTS[@]} )); then
      AGENT_NAME="${AGENTS[$((choice-1))]}"
      break
    fi
    print_warn "Please enter a number between 1 and ${#AGENTS[@]}"
  done
fi

AGENT_DIR="$PORTABLE_DIR/$AGENT_NAME"
SKILLS_DIR="$AGENT_DIR/export/skills"
echo ""
print_ok "Selected agent: ${BOLD}$AGENT_NAME${RESET}"

# ── Host application paths (bash 3.2-compatible — no associative arrays) ──────
# Parallel arrays: HOST_NAMES and a lookup function replace declare -A
HOST_NAMES=(bob codex gemini opencode claude)
HOST_PATH_bob="$HOME/.bob/skills"
HOST_PATH_codex="$HOME/.agents/skills"
HOST_PATH_gemini="$HOME/.gemini/config/skills"
HOST_PATH_opencode="$HOME/.config/opencode/skills"
HOST_PATH_claude="$HOME/.claude/skills"

get_host_path() {
  local _host="$1"
  local _varname="HOST_PATH_${_host}"
  echo "${!_varname:-}"
}

declare -a SELECTED=()

if [[ -n "$SELECTED_HOSTS" ]]; then
  IFS=',' read -ra SELECTED <<< "$SELECTED_HOSTS"
  for h in "${SELECTED[@]}"; do
    if [[ -z "$(get_host_path "$h")" ]]; then
      print_err "Unknown host: $h (valid: bob, codex, gemini, opencode, claude)"
      exit 1
    fi
  done
else
  print_header "Supported host applications:"
  for h in "${HOST_NAMES[@]}"; do
    path="$(get_host_path "$h")"
    if [[ -d "$path" ]]; then
      print_ok "$h: $path  ${DIM}(directory exists)${RESET}"
    else
      print_dim "  $h: $path  (not present)"
    fi
  done
  echo ""
  echo "Enter comma-separated hosts to install to (e.g. bob,claude), or 'all':"
  read -r -p "> " host_input
  if [[ "$host_input" == "all" ]]; then
    SELECTED=("${HOST_NAMES[@]}")
  else
    IFS=',' read -ra SELECTED <<< "$host_input"
    for i in "${!SELECTED[@]}"; do
      SELECTED[$i]="${SELECTED[$i]// /}"
    done
  fi
fi

# ── Prerequisites check ───────────────────────────────────────────────────────
echo ""
print_header "Prerequisites check:"
prereq_ok=true

skill_files=("$SKILLS_DIR"/*.md)
if [[ ${#skill_files[@]} -eq 0 || ! -f "${skill_files[0]}" ]]; then
  print_err "No skill files found in $SKILLS_DIR"
  prereq_ok=false
else
  print_ok "${#skill_files[@]} skill file(s) found in export/skills/"
  if [[ "$VERBOSE" == true ]]; then
    for f in "${skill_files[@]}"; do print_dim "  $(basename "$f")"; done
  fi
fi

for h in "${SELECTED[@]}"; do
  target_base="$(get_host_path "$h")"
  if [[ -d "$target_base" ]]; then
    print_ok "$h: target directory exists ($target_base)"
  elif [[ "$DRY_RUN" == true ]]; then
    print_warn "$h: target directory absent — would be created: $target_base"
  else
    print_warn "$h: target directory absent — will be created: $target_base"
  fi
done

if [[ "$prereq_ok" == false ]]; then
  print_err "Prerequisites check failed. Resolve errors above and re-run."
  exit 1
fi

# ── Dry-run / Installation plan ───────────────────────────────────────────────
echo ""
print_header "Installation plan:"

declare -a INSTALL_ACTIONS=()

for skill_file in "$SKILLS_DIR"/*.md; do
  skill_name="$(basename "$skill_file" .md)"
  for h in "${SELECTED[@]}"; do
    target_base="$(get_host_path "$h")"
    target_dir="$target_base/$skill_name"
    target_file="$target_dir/SKILL.md"
    INSTALL_ACTIONS+=("$h|$skill_name|$skill_file|$target_file")
    echo "  ${BOLD}$h${RESET} → $target_file"
    print_dim "    source: $skill_file"
  done
done

echo ""
echo "Total: ${#INSTALL_ACTIONS[@]} file(s) across ${#SELECTED[@]} host(s)"

# ── Confirmation ──────────────────────────────────────────────────────────────
if [[ "$DRY_RUN" == true ]]; then
  echo ""
  print_warn "DRY-RUN complete — no files written."
  exit 0
fi

if [[ "$NON_INTERACTIVE" == false ]]; then
  echo ""
  read -r -p "Proceed with installation? [y/N] " confirm
  if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
  fi
fi

# ── Execute installation ───────────────────────────────────────────────────────
echo ""
print_header "Installing skill files…"

MANIFEST_FILE="$AGENT_DIR/.install-manifest.txt"
INSTALL_COUNT=0
INSTALL_ERRORS=0
ADAPTER_NEEDED=false

# Create/truncate manifest for this run
printf "# STF install manifest\n# Agent: %s\n# Date: %s\n\n" \
  "$AGENT_NAME" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" > "$MANIFEST_FILE"

for action in "${INSTALL_ACTIONS[@]}"; do
  IFS='|' read -r host skill_name src_file target_file <<< "$action"
  target_dir="$(dirname "$target_file")"

  if ! mkdir -p "$target_dir" 2>/dev/null; then
    print_err "Cannot create directory: $target_dir"
    (( INSTALL_ERRORS++ )) || true
    continue
  fi

  if cp "$src_file" "$target_file" 2>/dev/null; then
    print_ok "Installed: ${BOLD}$host${RESET}/$skill_name → $target_file"
    printf "%s|%s|%s\n" "$host" "$skill_name" "$target_file" >> "$MANIFEST_FILE"
    (( INSTALL_COUNT++ )) || true
    [[ "$host" == "bob" ]] && ADAPTER_NEEDED=true
  else
    print_err "Failed to copy: $src_file → $target_file"
    (( INSTALL_ERRORS++ )) || true
  fi
done

echo ""
echo "Installed: $INSTALL_COUNT file(s), Errors: $INSTALL_ERRORS"

# ── Optionally invoke Bob adapter generator ────────────────────────────────────
ADAPTER_SCRIPT="$AGENT_DIR/export/scripts/generate-bob-adapter.sh"
if [[ "$ADAPTER_NEEDED" == true && -f "$ADAPTER_SCRIPT" ]]; then
  echo ""
  print_header "Generating Bob skill adapter…"
  if bash "$ADAPTER_SCRIPT" 2>&1 | while IFS= read -r line; do print_dim "$line"; done; then
    print_ok "Bob adapter generated via generate-bob-adapter.sh"
  else
    print_warn "Bob adapter generation returned a non-zero exit; check output above"
  fi
fi

echo ""
if [[ "$INSTALL_ERRORS" -eq 0 ]]; then
  print_ok "Installation complete. Manifest written to: $MANIFEST_FILE"
else
  print_warn "Installation completed with $INSTALL_ERRORS error(s). Check output above."
  print_dim "Manifest (partial): $MANIFEST_FILE"
fi
print_header "Done."
