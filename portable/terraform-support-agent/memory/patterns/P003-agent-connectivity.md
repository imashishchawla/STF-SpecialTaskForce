---
pattern_alias: P003-agent-connectivity
schema_version: 1
status: candidate
category: agents_and_networking
product_scope: hcp_terraform
affected_versions: "all"
last_reviewed: "2026-10-02"
---

# Pattern P003 — Agent Connectivity / Plan Failure

## Error fingerprint
- Run queued in agent pool but never starts, or starts and immediately fails
- Error: `agent is not responding`, `no agents available`, `failed to connect to backend`
- Agent appears registered in HCP TF UI but runs don't execute

## Trigger conditions
- Agent process crashed or was restarted — not reconnected to pool
- Network egress from agent host to `app.terraform.io:443` blocked (firewall rule change)
- `HTTPS_PROXY` or `NO_PROXY` misconfigured — agent can't reach HCP TF
- Agent version is outdated and incompatible with current HCP TF API
- Agent token was revoked or expired

## Supporting observations
- Agent logs show repeated connection attempts or auth failures
- `Agent status` in HCP TF UI shows `idle` but no runs execute, or shows `errored`
- Issue started after a network change, agent host OS update, or agent restart

## Conflicting evidence
- If runs execute on some agents in the pool but not others → not a pool-wide issue; check that specific agent host
- If run starts but provider auth fails → not this pattern (provider credentials issue)

## Discriminating check
Ask: "Can you share the agent log output from the time a run was queued? Specifically: does the log show the agent receiving the run assignment?"

Verify: `curl -v https://app.terraform.io/api/v2/ping` from the agent host — confirms egress.

## Confirmed cause status: unconfirmed (candidate)

## Remedy (if confirmed)
1. Restart the agent process and watch logs for successful connection
2. Verify egress: `curl https://app.terraform.io/api/v2/ping` from agent host must return 200
3. Check proxy: `echo $HTTPS_PROXY $NO_PROXY` — ensure `app.terraform.io` is not blocked
4. Verify agent token in HCP TF: Organization → Agent Pools → [pool] → Agents → check token status
5. Upgrade agent if version is pinned to an old release
6. Rollback: no state changes — restart is safe

## Source references
- Ref: https://developer.hashicorp.com/terraform/cloud-docs/agents
- Ref: https://developer.hashicorp.com/terraform/cloud-docs/agents/agents#network-requirements

## Confidence explanation
Candidate only. Multiple root causes share the same surface symptom. Requires agent log inspection before confirming.
