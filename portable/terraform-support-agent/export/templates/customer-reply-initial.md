# Template: customer-reply-initial.md — First-Response Acknowledgment
# Classification: CUSTOMER-VISIBLE — reviewed by operator before sending
# Use: Send as the first reply when case has just been received and investigation has not yet completed

---

─────────────────────────────────────────────
COPY FROM HERE
─────────────────────────────────────────────
Subject: Re: [Case #XXXXX] — [brief issue description]

Hi [Customer name or team],

Thank you for reaching out to IBM Support.

I've received your case and am reviewing the details. I'm currently investigating
[describe confirmed scope only — no hypotheses, no promises about cause].

[Optional: If a specific piece of information is immediately needed:]
To help me investigate more effectively, could you provide [one specific item]?

I'll follow up with [expected output — e.g. next update, questions, diagnostic steps]
[timeframe only if confirmed — omit if unknown].

Regards,
{{operator_name}} | {{operator_title}}
Available {{operator_availability}}
Thank you for choosing IBM Support.
─────────────────────────────────────────────
END COPY
─────────────────────────────────────────────

---

<!-- RULES (strip before sending) -->
<!-- ✅ May be sent before full investigation is complete — use only confirmed facts -->
<!-- ✅ Signature tokens resolve from memory/preferences.md -->
<!-- ❌ Must not: mention a hypothesis or potential cause -->
<!-- ❌ Must not: promise a resolution timeline unless confirmed with Engineering -->
<!-- ❌ Must not: ask more than one clarifying question in this first message -->
<!-- ❌ Must not: include internal routing, Jira IDs, or entitlement details -->
