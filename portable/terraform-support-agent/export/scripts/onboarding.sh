#!/usr/bin/env bash
# onboarding.sh — Interactive first-run configuration for the Terraform Support Agent
#
# Run once before starting the agent for the first time:
#   bash export/scripts/onboarding.sh
#
# What it does:
#   1. Asks a series of questions to understand the operator's context, preferences,
#      and prior prompt history.
#   2. Writes answers to .env (never committed) and memory/preferences.md (human-approved).
#   3. Prints a summary and asks: "Save and activate? [y/n/skip]"
#
# What it does NOT do (deferred to installer.sh):
#   - MCP server installation (terraform-mcp, playwright-mcp)
#   - IBM Propel connection configuration
#   Run: bash installer.sh --help for those options.
#
# Requirements: bash 3.2+, standard POSIX utilities.
# Design reference: docs/design/03-skills-and-templates.md §7
#
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$AGENT_ROOT/.env"
PREFS_FILE="$AGENT_ROOT/memory/preferences.md"

# ── Colours ───────────────────────────────────────────────────────────────────
BOLD='\033[1m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RESET='\033[0m'

sep() { echo -e "${CYAN}──────────────────────────────────────────────────────${RESET}"; }
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

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║   Terraform Support Agent — First-Run Configuration  ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════╝${RESET}"
echo ""
echo "This wizard configures your agent for the first time."
echo "All answers are saved to .env (local only, not committed)"
echo "and memory/preferences.md (requires your approval before use)."
echo ""
yn "Do you want to configure now, or skip for later?" CONFIGURE_NOW

if [[ "$CONFIGURE_NOW" == "skip" || "$CONFIGURE_NOW" == "n" ]]; then
  echo ""
  echo -e "${YELLOW}Skipped. Run 'bash export/scripts/onboarding.sh' when ready.${RESET}"
  echo "The agent will ask you these questions on first case intake instead."
  exit 0
fi

echo ""
sep
echo -e "${BOLD}Section 1 — About You${RESET}"
sep
ask "Your full name (used in all communication drafts):" OPERATOR_NAME
ask "Your job title (e.g. 'HCP Terraform Support Engineer'):" OPERATOR_TITLE
ask "Your working hours (e.g. 'Mon–Fri | 09:00–17:00 IST'):" OPERATOR_AVAILABILITY
ask "Where should the agent repository live? (full path, e.g. ~/work/terraform-support-agent):" AGENT_REPO_PATH "$(pwd)"

echo ""
sep
echo -e "${BOLD}Section 2 — How You Use Terraform${RESET}"
sep
echo "This helps the agent understand your customer base and scope."
echo ""
echo "Which Terraform products do you primarily support? (check all that apply)"
echo "  a) HCP Terraform (Terraform Cloud)"
echo "  b) Terraform Enterprise (self-hosted)"
echo "  c) Terraform CLI / Open Source Core"
echo "  d) Terraform Providers (AWS, Azure, GCP, etc.)"
echo "  e) Terraform Private Registry"
echo "  f) Terraform Public Registry"
ask "Enter letters separated by commas (e.g. a,b,d):" TF_PRODUCTS_COVERED "a,b,c,d"

echo ""
echo "Which cloud providers do your customers most commonly use?"
echo "  a) AWS    b) Azure    c) GCP    d) Multiple equally"
ask "Enter letters (e.g. a,b):" CLOUD_PROVIDERS "a,b,c"

echo ""
echo "What execution modes do your customers primarily use?"
echo "  a) Remote execution (HCP Terraform)    b) Agent-based execution    c) Local CLI (remote state)"
ask "Enter letters:" EXECUTION_MODES "a,b"

echo ""
ask "Any specific provider families you see most issues with? (e.g. 'AWS, AzureAD, random'):" TOP_PROVIDERS "AWS, Azure, Google"

echo ""
sep
echo -e "${BOLD}Section 3 — Your Email / Communication Style${RESET}"
sep
echo "The agent uses your style to draft customer replies, handoffs, and closure emails."
echo "Paste 1–3 example customer-reply emails you've sent (or press Enter to skip)."
echo "These will be stored in memory/preferences.md as style samples — not sent anywhere."
echo ""
echo "(Paste email text, then press Enter twice when done, or just press Enter to skip)"
STYLE_SAMPLE_1=""
read -r -d $'\n\n' STYLE_SAMPLE_1 || true
if [[ -z "$STYLE_SAMPLE_1" ]]; then
  STYLE_SAMPLE_1="[No sample provided — agent uses default style rules]"
fi

echo ""
echo "Which tone best describes your writing style?"
echo "  a) Formal and detailed    b) Direct and concise (default)    c) Warm and conversational"
ask "Enter letter:" COMM_TONE "b"

echo ""
sep
echo -e "${BOLD}Section 4 — Prior Prompt / System Prompt${RESET}"
sep
echo "Did you previously use a custom system prompt for Terraform support?"
yn "Do you want to import a prior prompt?" IMPORT_PRIOR_PROMPT

PRIOR_PROMPT_PATH=""
if [[ "$IMPORT_PRIOR_PROMPT" == "y" ]]; then
  ask "Paste the file path to your existing prompt file (or press Enter to skip):" PRIOR_PROMPT_PATH
  if [[ -n "$PRIOR_PROMPT_PATH" && -f "$PRIOR_PROMPT_PATH" ]]; then
    echo -e "${GREEN}  Found: $PRIOR_PROMPT_PATH — will be imported into preferences.md${RESET}"
  elif [[ -n "$PRIOR_PROMPT_PATH" ]]; then
    echo -e "${YELLOW}  File not found. Skipping import.${RESET}"
    PRIOR_PROMPT_PATH=""
  fi
fi

echo ""
sep
echo -e "${BOLD}Section 5 — Trusted Reference Sources${RESET}"
sep
echo "The agent uses a source catalog to prioritise where it looks for information."
echo ""
echo "Here are the default sources included (from sources/catalog.md):"
echo "  • HashiCorp Docs (developer.hashicorp.com/terraform)"
echo "  • HCP Terraform Docs (developer.hashicorp.com/terraform/cloud-docs)"
echo "  • Provider Registry (registry.terraform.io)"
echo "  • HashiCorp Support KB (support.hashicorp.com)"
echo "  • GitHub: hashicorp/terraform"
echo "  • GitHub: hashicorp/terraform-provider-aws, -azurerm, -google"
echo "  • HCP Terraform Status Page (status.hashicorp.com)"
echo "  • Terraform Changelog (github.com/hashicorp/terraform/blob/main/CHANGELOG.md)"
echo ""
yn "Do you want to add additional trusted sources now?" ADD_SOURCES

EXTRA_SOURCES=""
if [[ "$ADD_SOURCES" == "y" ]]; then
  echo "Enter additional sources one per line (title | URL). Press Enter twice when done."
  read -r -d $'\n\n' EXTRA_SOURCES || true
fi

echo ""
sep
echo -e "${BOLD}Section 6 — Registry Routing Process${RESET}"
sep
echo "The registry-routing skill uses an interim Terraform Public Registry process."
echo "Phase II (direct HashiCorp team handling) may have started."
yn "Has Phase II of the registry routing process started in your team? (unsure = skip)" REGISTRY_PHASE2

echo ""
sep
echo -e "${BOLD}Configuration Summary${RESET}"
sep
echo ""
echo -e "  Operator name:       ${GREEN}$OPERATOR_NAME${RESET}"
echo -e "  Title:               ${GREEN}$OPERATOR_TITLE${RESET}"
echo -e "  Availability:        ${GREEN}$OPERATOR_AVAILABILITY${RESET}"
echo -e "  Repo path:           ${GREEN}$AGENT_REPO_PATH${RESET}"
echo -e "  TF products:         ${GREEN}$TF_PRODUCTS_COVERED${RESET}"
echo -e "  Cloud providers:     ${GREEN}$CLOUD_PROVIDERS${RESET}"
echo -e "  Execution modes:     ${GREEN}$EXECUTION_MODES${RESET}"
echo -e "  Top providers:       ${GREEN}$TOP_PROVIDERS${RESET}"
echo -e "  Comm tone:           ${GREEN}$COMM_TONE${RESET}"
echo -e "  Prior prompt:        ${GREEN}${PRIOR_PROMPT_PATH:-none}${RESET}"
echo -e "  Extra sources:       ${GREEN}${EXTRA_SOURCES:-none}${RESET}"
echo -e "  Registry Phase II:   ${GREEN}$REGISTRY_PHASE2${RESET}"
echo ""

yn "Save this configuration and generate .env + memory/preferences.md?" SAVE_CONFIG

if [[ "$SAVE_CONFIG" != "y" ]]; then
  echo -e "${YELLOW}Aborted. Nothing was saved.${RESET}"
  exit 0
fi

# ── Write .env ────────────────────────────────────────────────────────────────
# All onboarding output is private, including files replaced on a later run.
umask 077
mkdir -p "$AGENT_ROOT/memory"
touch "$ENV_FILE" "$PREFS_FILE"
chmod 600 "$ENV_FILE" "$PREFS_FILE"
cat > "$ENV_FILE" << EOF
# Terraform Support Agent — operator configuration
# Generated by onboarding.sh — DO NOT COMMIT THIS FILE
# Re-run onboarding.sh to update.

OPERATOR_NAME="${OPERATOR_NAME}"
OPERATOR_TITLE="${OPERATOR_TITLE}"
OPERATOR_AVAILABILITY="${OPERATOR_AVAILABILITY}"
AGENT_REPO_PATH="${AGENT_REPO_PATH}"

TF_PRODUCTS_COVERED="${TF_PRODUCTS_COVERED}"
CLOUD_PROVIDERS="${CLOUD_PROVIDERS}"
EXECUTION_MODES="${EXECUTION_MODES}"
TOP_PROVIDERS="${TOP_PROVIDERS}"
COMMUNICATION_TONE="${COMM_TONE}"

REGISTRY_PHASE2_STATUS="${REGISTRY_PHASE2}"

# MCP credential placeholders (Phase 4 — fill in only after Phase 4 allowlist review)
# Phase 4: set enabled: true in export/mcp/terraform-mcp.yaml only after Phase 4 allowlist review
TF_MCP_TOKEN=
TF_MCP_URL=
EOF

echo -e "${GREEN}  ✓ Written: $ENV_FILE${RESET}"

# ── Write preferences.md ──────────────────────────────────────────────────────
# Derive signature block
case "$COMM_TONE" in
  a) TONE_LABEL="Formal and detailed" ;;
  c) TONE_LABEL="Warm and conversational" ;;
  *) TONE_LABEL="Direct and concise" ;;
esac

PRIOR_PROMPT_SECTION=""
if [[ -n "$PRIOR_PROMPT_PATH" && -f "$PRIOR_PROMPT_PATH" ]]; then
  PRIOR_PROMPT_CONTENT=$(cat "$PRIOR_PROMPT_PATH")
  PRIOR_PROMPT_SECTION="
## Imported prior prompt

The operator imported the following system prompt. The agent uses this as context for understanding
the operator's prior workflow and preferences. It does not override the agent's boundary constraints.

\`\`\`
$PRIOR_PROMPT_CONTENT
\`\`\`"
fi

EXTRA_SOURCES_SECTION=""
if [[ -n "$EXTRA_SOURCES" ]]; then
  EXTRA_SOURCES_SECTION="
## Additional trusted sources (operator-added)

\`\`\`
$EXTRA_SOURCES
\`\`\`"
fi

cat > "$PREFS_FILE" << EOF
---
schema_version: 1
operator_name: "${OPERATOR_NAME}"
operator_title: "${OPERATOR_TITLE}"
operator_availability: "${OPERATOR_AVAILABILITY}"
agent_repo_path: "${AGENT_REPO_PATH}"
tf_products_covered: "${TF_PRODUCTS_COVERED}"
cloud_providers: "${CLOUD_PROVIDERS}"
execution_modes: "${EXECUTION_MODES}"
top_providers: "${TOP_PROVIDERS}"
communication_tone: "${TONE_LABEL}"
registry_phase2_status: "${REGISTRY_PHASE2}"
onboarding_completed: "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
---

# Preferences

> **Populated via onboarding.sh** on $(date -u +"%Y-%m-%d").
> All fields above were confirmed by the operator and may be updated by re-running onboarding.sh.

## Signature

Resolved at output-generation time from front-matter fields:

\`\`\`
Regards,
${OPERATOR_NAME} | ${OPERATOR_TITLE}
Available ${OPERATOR_AVAILABILITY}
Thank you for choosing IBM Support.
\`\`\`

## Post-resolution survey message (exact)

\`\`\`
You will receive a short survey via email with the subject:
Request #[TICKET_NUMBER]: How would you rate the support you received?
Your feedback helps us improve. Thank you, and have a wonderful day.
\`\`\`

> Block closure drafts unless [TICKET_NUMBER] is replaced with a verified case ticket number.

## Response style

\`\`\`
Tone:        ${TONE_LABEL}
Avoid:       "sorry", "apologize", unsupported promises, vague timelines
Questions:   Ask focused, numbered questions — one clarifying question per message
Links:       Full URLs only — no shortened links, no internal tracker links in customer drafts
Paths:       Precise UI paths (e.g. Settings > General > Execution Mode)
Commands:    Include command examples with expected outputs when validating steps
Rollback:    Always offer safe rollback steps and note side effects for any remediation
Language:    Match customer's language if supplied and if translation is approved
Pronouns:    Use supplied pronouns — never guess personal details
Internal:    Never expose Jira details, entitlement info, or routing steps in customer drafts
\`\`\`

## Troubleshooting workflow (from operator's prior system prompt)

1. **CLARIFY**: Restate issue, expected vs actual behavior
2. **CLASSIFY**: Categorize (auth, VCS, runs, planning, state, policies, registry, agents, networking, drift)
3. **COLLECT**: Gather only missing prerequisites that change the next diagnostic step
4. **ISOLATE**: Minimal reproduction, test new workspace, pin versions, disable policies/run tasks
5. **IDENTIFY**: Map error codes/strings to known issues; check status pages
6. **REMEDIATE**: Step-by-step instructions, risks, rollback procedures
7. **VALIDATE**: Ask customer to confirm resolution
8. **DOCUMENT**: Summarize cause, fix, prevention with references

## Case intake checklist (from operator's prior system prompt)

Gather ONLY necessary prerequisites:
1. Organization and workspace name (mask if needed)
2. Run ID or task ID, time of failure, execution mode (remote, agent, CLI)
3. Terraform Core and provider versions
4. Recent changes: code, variables, permissions, VCS, policies
5. Exact error messages, stack traces, relevant run logs
6. VCS integration details, commit SHA
7. Workspace settings: execution mode, pinned Terraform version, working directory
8. Backend and state details: lock status, potential drift
9. Authentication method (user token, team token, OIDC, service principal)
10. Agent version, status, logs, network egress and proxy config
11. Cloud account details (AWS, Azure, GCP) including project/subscription/account and region
12. Networking constraints: proxies, firewalls, egress allowlists
13. Policy sets and run tasks in the run pipeline
14. Reproduction steps and if issue reproduces in minimal example

## Diagnostic habits

- Start with product scope classification before any investigation (HCP TF vs TFE vs Public Registry vs Private Registry)
- Never surface a hypothesis to the customer as a confirmed finding
- Always cite the evidence item that supports each hypothesis (by ref tag, not verbatim)
- Prefer "I need more information about X" over a low-confidence diagnostic guess
- When two hypotheses are equally supported, present both and ask a targeted clarifying question
- Ask one clarifying question per message — not a list
- For state operations: prefer Terraform operations over direct state edits; require backups if unavoidable
- For agents: always check logs, version, connectivity to app.terraform.io, and proxy/no_proxy config

## Common diagnostics reference (from operator's prior system prompt)

\`\`\`
Versions:    terraform version  |  terraform providers  |  terraform init -upgrade
State:       terraform state list  |  terraform force-unlock <ID> (only if safe)
HCP Runs:    Runs tab in UI or API: GET /api/v2/runs/<RUN_ID>
Agents:      Check agent logs, version, connectivity to app.terraform.io, proxy config
VCS:         Check webhook delivery logs, OAuth connection, repo path
\`\`\`

## Operator scope (from operator's prior system prompt)

**Supported:**
- HCP Terraform features
- Terraform Core
- Official HashiCorp providers
- VCS integrations (GitHub, GitLab, Bitbucket)
- SSO/SCIM
- Sentinel/OPA policies
- Workspaces, runs, agents
- Cost estimation, state, variables, run tasks
- Private registry
- Terraform CLI/HCP workflows

**Not supported:**
- Third-party or community providers/modules (redirect to their issue trackers)
- Custom scripts or organizational security policies (unless affecting HCP Terraform)
- Secrets in plain text (always mask tokens, keys, org/workspace IDs)

## Security and compliance habits

- Never request or paste secrets (tokens, access keys, client secrets) — request redacted logs
- Follow least privilege; avoid destructive operations without confirmation
- Prefer Terraform operations over direct state edits
- If direct state edit unavoidable: take backups, explain risks clearly

## Escalation paths (from operator's prior system prompt)

Check GitHub issues when behavior deviates with a minimal reproduction:
- Terraform Core: https://github.com/hashicorp/terraform/issues
- AWS Provider: https://github.com/hashicorp/terraform-provider-aws/issues
- Link matching issues, provide known workarounds/version pins

## Correction policy

- Accepted corrections are recorded in \`memory/corrections/\` (human-approved)
- A correction supersedes any earlier hypothesis or conclusion on the same topic
- Always check \`memory/corrections/\` before finalising a hypothesis on a case with prior history
${EXTRA_SOURCES_SECTION}
${PRIOR_PROMPT_SECTION}
EOF

echo -e "${GREEN}  ✓ Written: $PREFS_FILE${RESET}"
echo ""
echo -e "${BOLD}${GREEN}Onboarding complete.${RESET}"
echo ""
echo "Next steps:"
echo "  1. Review memory/preferences.md — edit anything that looks wrong."
echo "  2. Check sources/catalog.md — add any internal sources you use."
echo "  3. Verify registry routing status in memory/ops/registry-routing.md."
echo "  4. Run: bash export/scripts/generate-bob-adapter.sh"
echo "  5. To install MCP servers or Propel connections, run: bash installer.sh --help"
echo "  6. Open a real case and run the intake skill for the first time."
echo ""
echo -e "${YELLOW}Remember: .env is never committed. Keep it in your local repo only.${RESET}"
