#!/usr/bin/env bash
# generate-bob-adapter.sh
#
# Generates ~/.bob/skills/ entries from the canonical export/skills/ source.
# Run this after any change to export/skills/.
#
# Bob skill format (confirmed from ~/.bob/skills/ inspection):
#   ~/.bob/skills/<skill-name>/SKILL.md
#
#   SKILL.md front matter:
#   ---
#   name: <skill-name>
#   description: <single-line trigger description>
#   metadata:
#     author: <author>
#     version: "1.0"
#     display_name: <Display Name>
#     short_description: <short description>
#   ---
#
# NEVER edit ~/.bob/skills/ directly — all changes go to export/skills/ first.
# If ~/.bob/skills/ and export/skills/ diverge, export/skills/ is authoritative.
#
# Usage:
#   bash export/scripts/generate-bob-adapter.sh
#   bash export/scripts/generate-bob-adapter.sh --dry-run    # preview without writing
#   bash export/scripts/generate-bob-adapter.sh --target ~/.bob/skills  # override target
#
# Design reference: docs/design/05-runtime-and-integration.md §2
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SOURCE_DIR="$AGENT_ROOT/export/skills"
TARGET_DIR="${HOME}/.bob/skills"   # default: user-global Bob skills directory
DRY_RUN=false

# ── Argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)   DRY_RUN=true; shift ;;
    --target)    TARGET_DIR="$2"; shift 2 ;;
    *)           echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

BOLD='\033[1m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; RESET='\033[0m'

[[ "$DRY_RUN" == "true" ]] && echo -e "${YELLOW}DRY-RUN — no files will be written${RESET}\n"

# ── Pre-flight ────────────────────────────────────────────────────────────────
if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "ERROR: Source directory not found: $SOURCE_DIR" >&2; exit 1
fi

skill_files=("$SOURCE_DIR"/*.md)
if [[ ${#skill_files[@]} -eq 0 || ! -f "${skill_files[0]}" ]]; then
  echo "ERROR: No skill .md files found in $SOURCE_DIR" >&2; exit 1
fi

echo -e "${BOLD}generate-bob-adapter.sh${RESET}"
echo "  Source : $SOURCE_DIR"
echo "  Target : $TARGET_DIR"
echo ""

# ── Skill metadata map ────────────────────────────────────────────────────────
# Maps source filename → (bob-dir-name, display-name, short-description)
# Bob dir name must be a clean slug (no .md extension).
#
# Implemented as parallel indexed arrays for bash 3.2 compatibility (macOS default).
# Each index position corresponds to the same skill across all three arrays.

SKILL_KEYS=(
  "intake.md"
  "diagnosis.md"
  "source-check.md"
  "communication.md"
  "registry-routing.md"
  "reproduction.md"
  "screen-capture.md"
)

SKILL_DIR_NAMES=(
  "terraform-intake"
  "terraform-diagnosis"
  "terraform-source-check"
  "terraform-communication"
  "terraform-registry-routing"
  "terraform-reproduction"
  "terraform-screen-capture"
)

SKILL_DISPLAY_NAMES=(
  "TF: Intake"
  "TF: Diagnosis"
  "TF: Source Check"
  "TF: Communication"
  "TF: Registry Routing"
  "TF: Reproduction"
  "TF: Screen Capture"
)

SKILL_SHORT_DESCS=(
  "Ingest a Terraform support case, enforce redaction, and produce a structured case packet."
  "Analyse logs, HCL, and version strings to produce ranked hypotheses with discriminating checks."
  "Search approved HashiCorp and IBM sources for a specific research question."
  "Draft customer replies, handoffs, closures, RCAs, and CANs using validated findings."
  "Apply the Terraform Public Registry interim routing process (internal only)."
  "Prepare a minimal isolated reproduction plan (no execution — operator runs separately)."
  "Capture and redact live screen content during a customer call for use as case evidence (Phase 4 — requires Playwright MCP)."
)

# Lookup helpers — return value for a given source basename
_get_dir_name()   { local k="$1"; for i in "${!SKILL_KEYS[@]}"; do [[ "${SKILL_KEYS[$i]}" == "$k" ]] && echo "${SKILL_DIR_NAMES[$i]}" && return; done; }
_get_display()    { local k="$1"; for i in "${!SKILL_KEYS[@]}"; do [[ "${SKILL_KEYS[$i]}" == "$k" ]] && echo "${SKILL_DISPLAY_NAMES[$i]}" && return; done; }
_get_short_desc() { local k="$1"; for i in "${!SKILL_KEYS[@]}"; do [[ "${SKILL_KEYS[$i]}" == "$k" ]] && echo "${SKILL_SHORT_DESCS[$i]}" && return; done; }

# Check whether a basename is in the metadata map
_in_map() { local k="$1"; for key in "${SKILL_KEYS[@]}"; do [[ "$key" == "$k" ]] && return 0; done; return 1; }

# ── Extract description from source front matter ──────────────────────────────
get_description() {
  local src_file="$1"
  # Pull the 'description' line from YAML front matter if present
  awk '
    BEGIN { in_fm=0; found=0 }
    /^---$/ { if (!in_fm) { in_fm=1; next } else { exit } }
    in_fm && /^description:/ {
      sub(/^description:[[:space:]]*/, "")
      gsub(/^"|"$/, "")
      print
      found=1
      exit
    }
  ' "$src_file"
}

# ── Extract body (strip YAML front matter) ────────────────────────────────────
strip_front_matter() {
  local src_file="$1"
  awk '
    BEGIN { in_fm=0; done_fm=0 }
    /^---$/ && !done_fm { if (!in_fm) { in_fm=1; next } else { done_fm=1; next } }
    done_fm { print }
  ' "$src_file"
}

# ── Generation loop ───────────────────────────────────────────────────────────
generated=0
skipped=0

for src_file in "$SOURCE_DIR"/*.md; do
  src_basename="$(basename "$src_file")"

  # Skip files not in our metadata map
  if ! _in_map "$src_basename"; then
    echo -e "  ${YELLOW}SKIP${RESET} (not in metadata map): $src_basename"
    ((skipped++))
    continue
  fi

  dir_name="$(_get_dir_name "$src_basename")"
  display_name="$(_get_display "$src_basename")"
  short_desc="$(_get_short_desc "$src_basename")"

  # Use description from source front matter if richer than our short desc
  src_description="$(get_description "$src_file")"
  [[ -z "$src_description" ]] && src_description="$short_desc"

  skill_target_dir="$TARGET_DIR/$dir_name"
  skill_target_file="$skill_target_dir/SKILL.md"

  if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "  ${CYAN}WOULD WRITE${RESET}: $skill_target_file"
    continue
  fi

  mkdir -p "$skill_target_dir"

  # Assemble Bob SKILL.md: Bob front matter + body from export/skills/
  {
    cat <<FRONTMATTER
---
name: ${dir_name}
description: ${src_description}
metadata:
  author: Terraform Support Agent (generated)
  version: "0.1.0-draft"
  display_name: ${display_name}
  short_description: ${short_desc}
  generated_from: ${src_file}
  generated_at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
---
FRONTMATTER
    echo ""
    echo "> **Bob adapter** — do not edit. Source: \`export/skills/${src_basename}\`"
    echo ""
    strip_front_matter "$src_file"
  } > "$skill_target_file"

  echo -e "  ${GREEN}✓${RESET} $skill_target_dir/"
  ((generated++))
done

echo ""
if [[ "$DRY_RUN" == "true" ]]; then
  echo -e "${YELLOW}Dry-run complete. Re-run without --dry-run to write files.${RESET}"
else
  echo -e "${GREEN}Done.${RESET} Generated: $generated | Skipped: $skipped"
  echo ""
  echo "Next steps:"
  echo "  1. Open Bob and verify skills appear: type 'terraform' in skill search"
  echo "  2. If skills don't appear, check Bob version supports ~/.bob/skills/ loading"
  echo "  3. If installing globally, confirm ~/.bob/skills/ takes precedence over workspace .bob/skills/"
fi
