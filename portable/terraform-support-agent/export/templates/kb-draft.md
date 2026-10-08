# Template: kb-draft.md — Customer-Facing Knowledge Base Article
# Classification: Customer-facing after operator review and approval
# Requires: Confirmed resolution + Validation Reviewer approval + operator sign-off

---

─────────────────────────────────────────────
COPY FROM HERE  [Review before publishing — remove case alias from version history]
─────────────────────────────────────────────

## KB Draft: [Short descriptive title]

**Product**: [HCP Terraform / Terraform Enterprise / Terraform Core / Provider name]
**Versions affected**: [version range or "all current versions"]
**Category**: [Authentication | VCS | Runs | State | Policies | Registry | Agents | Networking | Providers]
**Status**: Draft — requires operator review before submission

---

### Summary

[One sentence: what symptom the user encounters and what resolves it.]

---

### Symptoms

Users may observe:

- [Symptom 1 — exact error message or behavior, quoted if known]
- [Symptom 2 — if applicable]

**Affected configuration** (if specific):
- Execution mode: [remote / agent / local]
- Backend type: [if relevant]
- Provider version: [if relevant]

---

### Root cause

[Confirmed cause in customer-appropriate language. Do not include internal Jira IDs, entitlement details, or internal routing information.]

---

### Resolution

Follow these steps to resolve the issue:

1. [Step 1 — with exact UI path or command]
   ```
   [command or code snippet if applicable]
   ```
2. [Step 2]
3. [Step 3]

**Expected result**: [What the customer should see after completing the steps.]

---

### Rollback / if the above does not work

[Optional — include only if a rollback path exists and is validated.]

---

### Prevention

[Optional — validated preventive configuration or monitoring, if applicable.]

---

### References

- [Title — Full URL]
- [Title — Full URL]

---

### Version history

| Version | Date | Change |
|---|---|---|
| Draft | [date] | Initial draft from case [alias — internal only, remove before publishing] |

---

─────────────────────────────────────────────
END COPY
─────────────────────────────────────────────

> **Before publishing**: Remove the case alias from Version history. Verify all URLs resolve. Confirm product version applicability with the current docs.
