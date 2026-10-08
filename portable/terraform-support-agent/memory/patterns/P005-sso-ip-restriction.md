---
pattern_alias: P005-sso-ip-restriction
schema_version: 1
status: candidate
category: authentication_authorization
product_scope: hcp_terraform
affected_versions: "all"
last_reviewed: "2026-10-02"
---

# Pattern P005 — SSO Enforcement / IP Allowlist Block

## Error fingerprint
- User cannot log in to HCP Terraform: `SSO required`, `access denied`, or silent redirect loop
- Specific users affected while others in the same org are not
- OR: all users suddenly locked out after a SSO/IP policy change

## Trigger conditions
- SSO enforcement was enabled at org level — users not yet linked to SSO provider
- IP allowlist was added or changed — user's IP is now blocked
- SAML assertion is missing a required attribute (e.g. email, team mapping)
- Session expired and SSO IdP is returning an unexpected attribute
- User's team membership in IdP was removed — no longer has access to the HCP TF team

## Supporting observations
- Audit log shows failed authentication events for the affected user
- Other users on the same IP/network can access fine (if IP-specific)
- Issue started after a SSO policy change or IdP maintenance

## Conflicting evidence
- If all users are locked out including org owners → IP allowlist likely blocked org owner too (common misconfiguration)
- If the user can log in but can't see workspaces → not auth, check team/workspace permissions instead

## Discriminating check
Ask: "Is SSO enforcement enabled for your org? Can you check the HCP Terraform audit log for the affected user's last login attempt? What does the IP allowlist currently contain?"

## Confirmed cause status: unconfirmed (candidate)

## Remedy (if confirmed)
**SSO not yet linked:**
1. User must log in via SSO link, not username/password
2. Org admin can send SSO invite from HCP TF → Settings → SSO

**IP allowlist blocking users:**
1. Org owner must add the correct IP range: HCP TF → Settings → IP Allowlist
2. ⚠️ Ensure org owner's own IP is in the allowlist before saving — locking yourself out requires HashiCorp support

**SAML attribute issue:**
1. Check IdP SAML assertion attributes against HCP TF requirements
2. Ref: https://developer.hashicorp.com/terraform/cloud-docs/users-teams-organizations/single-sign-on/saml

## Source references
- Ref: https://developer.hashicorp.com/terraform/cloud-docs/users-teams-organizations/single-sign-on
- Ref: https://developer.hashicorp.com/terraform/cloud-docs/users-teams-organizations/ip-allowlisting

## Confidence explanation
Candidate only. SSO and IP issues share similar symptoms. Requires audit log and org settings inspection to confirm.
