---
correction_id: C002-response-rules
schema_version: 1
topic: Citation labelling, copy-paste email format, time estimates, session timer
supersedes_pattern: null
correction_date: "2026-10-02"
corrected_by: operator
source_ref:
  title: "Session — operator requirements captured 2 October 2026"
  url: "local/session"
  retrieved: "2026-10-02"
---

# Correction C002 — Response Behaviour Rules

Four operator-requested rules to apply in every response from this point forward.

---

## Rule 1 — Citation Labelling (REQUIRED on every factual claim)

Every factual claim in a response must end with one of:

```
Ref: https://full-url-here
```
or
```
⚠️ LLM-based — not verified against official documentation
```

- Use `Ref:` when the information was retrieved from an official source in `sources/catalog.md`.
- Use `⚠️ LLM-based` when no retrieval was performed and the claim comes from training knowledge only.
- Never omit the label. Never mix both on the same claim.
- Multiple refs are allowed if more than one source supports the same claim.

---

## Rule 2 — Copy-Paste Email Block Format (REQUIRED for all drafted emails)

All customer-facing and internal email drafts must be wrapped in a copy-paste block:

```
─────────────────────────────────────────────
COPY FROM HERE
─────────────────────────────────────────────
Subject: Re: [Case #XXXXX] — <issue title>

Hi <Name>,

<body>

Regards,
{{operator_name}} | {{operator_title}}
Available {{operator_availability}}
Thank you for choosing IBM Support.
─────────────────────────────────────────────
END COPY
─────────────────────────────────────────────
```

- Subject line must always be included.
- `{{operator_name}}`, `{{operator_title}}`, `{{operator_availability}}` resolve from `memory/preferences.md`.
- If preferences are unset, substitute `[NAME]`, `[TITLE]`, `[AVAILABILITY]` as explicit placeholders.
- The block must contain only what the operator sends — no rules comments, no internal notes.

---

## Rule 3 — Time Estimates (REQUIRED on every config, email, reproduction task)

Append to every response that produces actionable work output:

```
⏱ Suggested Estimate:
  - [Task A]:   ~Xm
  - [Task B]:   ~Xm
  Total:        ~Xh Ym
```

- Provide one line per distinct task (write config, draft email, reproduce, test, etc.).
- Estimates are calibrated from `memory/patterns/time-estimates.md`.
- When the operator corrects an estimate, record the correction in `memory/patterns/time-estimates.md`
  and recalibrate future estimates of the same task type.
- Never promise a numerical time saving before the pilot measures it.

---

## Rule 4 — Session Timer Tooltip (REQUIRED every 3 replies)

Every 3rd reply in a session must append:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱ SESSION TRACKER  [Reply #N]
  Active case: [ticket # or "none"]
  Replies this session: N
  Reminder: Log your time before closing the browser tab.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

- Reply count resets when a new session starts (page reload / new conversation).
- Active case is taken from the most recent intake case alias, or "none" if no case is active.
- This tooltip is for the operator only — never include in customer-facing drafts.
