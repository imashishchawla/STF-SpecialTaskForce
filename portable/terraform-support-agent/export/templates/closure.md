# Template: closure.md — Customer Closure
# Classification: CUSTOMER-VISIBLE — reviewed by operator before sending
# ⛔ BLOCKED unless <REAL_TICKET_NUMBER> is replaced with a verified case ticket number
# Requires: Confirmed resolution (customer confirmed improvement OR no-issue finding confirmed)

---

─────────────────────────────────────────────
COPY FROM HERE
─────────────────────────────────────────────
Subject: Re: [Case #XXXXX] — Resolution Confirmed

Hi [Customer name or team],

[Resolution summary — state the confirmed cause and remedy in customer-safe language.
If no defect was found: confirm the specific condition that was ruled out and what was verified.
Keep to 2–4 sentences. No hypotheses, no internal details.]

[Optional: Any follow-up steps or documentation the customer should keep — e.g. version to stay on,
workaround to watch for regression, KB article for reference.]

You will receive a short survey via email with the subject:
Request #[REAL_TICKET_NUMBER]: How would you rate the support you received?
Your feedback helps us improve. Thank you, and have a wonderful day.

Regards,
{{operator_name}} | {{operator_title}}
Available {{operator_availability}}
Thank you for choosing IBM Support.
─────────────────────────────────────────────
END COPY
─────────────────────────────────────────────

---

<!-- RULES (strip before sending) -->
<!-- ⛔ BLOCKED: Replace [REAL_TICKET_NUMBER] with the verified case ticket number before sending -->
<!-- ✅ Signature tokens resolve from memory/preferences.md -->
<!-- ✅ Required: Customer has confirmed improvement OR no-issue finding is confirmed -->
<!-- ❌ Must not: Send without a real, verified ticket number in the survey URL and subject -->
<!-- ❌ Must not: Describe a hypothesis as the confirmed cause if resolution was not confirmed by customer -->
<!-- ❌ Must not: Include internal Jira IDs, routing details, or entitlement information -->
