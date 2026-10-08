# Template: customer-reply.md — Standard Customer Reply
# Classification: CUSTOMER-VISIBLE — reviewed by operator before sending
# Requires: Validated findings from Validation Reviewer + operator review of draft

---

─────────────────────────────────────────────
COPY FROM HERE
─────────────────────────────────────────────
Subject: Re: [Case #XXXXX] — [brief issue description]

Hi [Customer name or team],

[Body — validated findings only. No unconfirmed hypotheses presented as conclusions.
Use precise UI paths, CLI commands with expected output, and full reference URLs.
One clarifying question per message if information is still needed.]

[Validated next steps or requested information — numbered list if more than one item]

Regards,
{{operator_name}} | {{operator_title}}
Available {{operator_availability}}
Thank you for choosing IBM Support.
─────────────────────────────────────────────
END COPY
─────────────────────────────────────────────

---

<!-- RULES (strip before sending) -->
<!-- ✅ Signature tokens {{operator_name}}, {{operator_title}}, {{operator_availability}} resolve from memory/preferences.md -->
<!-- ✅ Required fields: customer name/team, validated body, next steps -->
<!-- ❌ Must not: include internal Jira IDs, entitlement info, routing steps, or unvalidated claims -->
<!-- ❌ Must not: present a hypothesis as a confirmed cause -->
<!-- ❌ Must not: promise a timeline unless Engineering has confirmed it -->
<!-- ❌ Must not: use shortened links — full URLs only -->
