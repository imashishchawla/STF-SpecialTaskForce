# A2A component

This directory contains an **optional, unverified** Agent2Agent server scaffold for the Terraform Support Agent. Core Bob guidance does not need it. The existing agent-local installer has a `start --a2a` command, but `install --a2a` does not yet install this component. The [active plan](../plan/portability-readiness-plan.md) specifies the installer and security work required before use.

## Current files

| File | Purpose | Status |
|---|---|---|
| `main.py`, `a2a_factory.py`, `terraform_agent.py` | Server entry, factory, coordinator prompt | Syntax checked; framework API and startup unverified |
| `config.py`, `.env.example` | Provider and server configuration | Example is tracked; safe defaults still require review |
| `requirements.txt` | Python dependencies | Depends on an unavailable local `lib/aicoe-agent-utils` path |
| `test_client.py` | One manual streaming smoke prompt | Requires a running server |
| `security/README.md` | Planned security boundary | Implementation is pending |

The former Dockerfile is outside the local-install scope. The dependency source, pin, and licensing must be verified before the installer offers A2A. Do not put real case material into the current scaffold.

## Planned installation and checks

The agent's `installer.sh` will offer A2A as an explicit optional component. When selected, it will verify prerequisites, create an isolated environment, run onboarding, enforce the security module, and start on loopback only. The same script will support status, stop, update, and scoped removal. Its `--dry-run` must show writes and network requests without performing them.

Before advertising A2A as ready, prove a clean-checkout dependency install, local server startup, agent-card retrieval, authenticated request, invalid-token rejection, redaction before model use, and shutdown. Record the results in `evals/` and the active plan.
