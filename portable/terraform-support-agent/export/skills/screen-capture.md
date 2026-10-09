---
skill_id: terraform-screen-capture
version: "0.1.0-draft"
status: draft
source: portable/terraform-support-agent/export/skills/screen-capture.md
canonical: true
bob_generated: false
phase: 4
approval_class: screen_capture_session
---

# Skill: screen-capture
> **Status**: Draft — Phase 4 capability. Requires Playwright MCP server to be configured and active.
> Full specification: `docs/design/05-runtime-and-integration.md §3`
> **⚠️ Security gate**: Raw screen content MUST pass through redaction before entering a case packet.

---

## Purpose

Capture and extract text content from a customer's shared screen during a live troubleshooting call — HCP Terraform UI pages, terminal output, run logs, error dialogs — and convert it into redacted evidence for the coordinator's case packet.

**This skill is a controlled evidence collector. It does not diagnose. It does not send messages.**
All captured content passes through the intake redaction gate before being used by any other skill.

---

## When to invoke

All three conditions must be met:
1. Customer is actively sharing their screen on a live call
2. The operator has confirmed: "I want to capture the current view as evidence"
3. The operator has identified which window/tab/region to capture

> **Never invoke this skill on a recording or unattended capture.** Live, operator-initiated only.

---

## Capture modes

### Mode 1 — Screenshot + OCR (Phase 3 bridge, no MCP required)
The operator takes a screenshot manually (OS screenshot tool) and pastes the image directly into Bob. Bob extracts visible text and passes it to the redaction gate below.

**Use this mode in Phase 3.** No additional tooling required.

### Mode 2 — Playwright DOM extraction (Phase 4, Playwright MCP required)
The Playwright MCP server reads the active browser tab's visible text content (DOM text nodes) without rendering JavaScript or executing scripts. Returns structured text only — no cookies, no session tokens, no network requests.

**Playwright MCP constraints (non-negotiable):**
- Read visible text content only — `page.textContent()` or equivalent
- No form submission, no click actions, no navigation
- No reading of `localStorage`, `sessionStorage`, cookies, or request headers
- No screenshots saved to disk — extracted text only, returned to the redaction gate
- Scope: the specific tab/window the operator identifies — not the whole browser

---

## Redaction gate (mandatory — runs before any captured content enters the case packet)

Captured content from either mode MUST pass through this gate before being used as evidence.

### Step 1 — Auto-detect and flag
Scan extracted text for:

| Pattern | Action |
|---|---|
| HCP workspace IDs (`ws-[a-zA-Z0-9]{16}`) | Replace with `[WS-ID-REDACTED]` |
| HCP run IDs (`run-[a-zA-Z0-9]{16}`) | Replace with `[RUN-ID-REDACTED]` |
| HCP plan/task IDs | Replace with `[PLAN-ID-REDACTED]` |
| Organization names (if identifiable) | Flag for operator review |
| Customer email addresses | Replace with `[EMAIL-REDACTED]` |
| Authentication tokens | Replace with `[TOKEN-REDACTED]` |
| API keys / access keys | Replace with `[KEY-REDACTED]` |
| Cloud account IDs (AWS account ID, Azure subscription ID, GCP project ID) | Flag for operator review |
| Full workspace names (if they contain customer identifiers) | Flag for operator review |

### Step 2 — Present redacted diff to operator
Show the operator:
```
Captured content (redacted):
─────────────────────────────────────────────────
[redacted text block]
─────────────────────────────────────────────────
Redacted items: [count] — [types found, not values]
Flagged for review: [items that need manual decision]
─────────────────────────────────────────────────
Approve to add as evidence, edit, or discard?
```

### Step 3 — Operator approval
- **Approve** → content added to case packet as an evidence item with ref tag (e.g., `E3-screen-capture-<timestamp>`)
- **Edit** → operator modifies the redacted block → re-present for approval
- **Discard** → content discarded entirely, not added to case packet

**If operator approves without reviewing flagged items → halt and require explicit confirmation for each flagged item.**

---

## Evidence format (output added to case packet)

```yaml
evidence_ref: E<n>-screen-capture-<ISO-timestamp>
source: screen_capture
capture_mode: screenshot_ocr | playwright_dom
captured_at: <ISO timestamp>
operator_approved: true
redaction_applied: true
redacted_count: <n>
content: |
  [redacted text content — approved by operator]
```

---

## What this skill must NOT do

- Pass raw (unredacted) screen content to any other skill
- Save screenshots or DOM content to disk without operator approval
- Capture automatically (no background watchers, no polling)
- Navigate the customer's browser — read-only DOM text extraction only
- Infer conclusions from screen content — that is the diagnosis skill's role
- Capture content from windows the operator did not explicitly identify

---

## Phase 4 Playwright MCP configuration

When the Playwright MCP server is active, add to `export/mcp/playwright-mcp.yaml`:

```yaml
server:
  name: playwright-mcp
  enabled: false   # enable only after Phase 4 review
  
allowed_tools:
  - browser_snapshot     # accessibility tree / text extraction
  - browser_find         # search visible text
  # NO navigation, form, click, or screenshot-to-disk tools

blocked_tools:
  - browser_navigate
  - browser_click
  - browser_fill
  - browser_fill_form
  - browser_type
  - browser_press_key
  - browser_select_option
  - browser_take_screenshot  # no disk writes during live capture
  - browser_evaluate         # no JS execution on customer page
  - browser_file_upload
  - browser_drag
```

> Verify exact tool names against the current Playwright MCP server before enabling.

---

## Related

- [`intake.md`](intake.md) — redaction logic (this skill reuses the same patterns)
- [`diagnosis.md`](diagnosis.md) — consumes approved screen-capture evidence items
- [`docs/design/05-runtime-and-integration.md §3`](../../docs/design/05-runtime-and-integration.md) — MCP integration design
- [`export/mcp/terraform-mcp.yaml`](../mcp/terraform-mcp.yaml) — MCP config pattern to follow
