# A2A — Optional Agent-to-Agent Component

> **Status**: Phase 3b scaffold — not required for core Bob-mode operation.  
> **Install gate**: Must be explicitly requested with `installer.sh install --a2a`.

---

## What this is

The `a2a/` directory contains a lightweight Python/FastAPI server that implements
the [Google Agent-to-Agent (A2A) protocol](https://google.github.io/A2A/).  
It wraps the Terraform Support Agent's skills so that an external orchestrator
(e.g., another AI agent or a workflow runner) can call them over HTTP rather than
through Bob's chat interface.

**This component is optional.** The core Bob-mode workflow — case intake, diagnosis,
communication drafting, memory capture — does not require A2A at all.

---

## Prerequisites

- Python 3.11+
- The agent already installed via `installer.sh install` (`.env` and
  `memory/preferences.md` must exist)

---

## Quick start

```bash
# Install + enable A2A in one step
bash ../installer.sh install --a2a

# Or enable A2A on an already-installed agent
bash ../installer.sh modify --a2a

# Start the A2A server
bash ../installer.sh start --a2a

# Check status
bash ../installer.sh status

# Stop the server
bash ../installer.sh stop --a2a
```

The server listens on `127.0.0.1:8080` by default (see `a2a/.env`).  
To change the port, edit `A2A_PORT` in `a2a/.env`.

---

## Smoke test

With the server running:

```bash
# Health check
curl -s http://127.0.0.1:8080/health | jq .

# Agent card (A2A discovery)
curl -s http://127.0.0.1:8080/.well-known/agent.json | jq .

# Send a simple task (intake skill)
curl -s -X POST http://127.0.0.1:8080/tasks/send \
  -H "Content-Type: application/json" \
  -d '{"task_id":"smoke-01","message":{"role":"user","parts":[{"text":"Hello, run intake"}]}}' \
  | jq .
```

Expected: each call returns HTTP 200 with a JSON body.

---

## Directory layout

```
a2a/
├── .env.example      ← template — copy to .env and fill in values
├── .env              ← live config (git-ignored; created by installer.sh --a2a)
├── main.py           ← FastAPI entry point
├── agent_card.json   ← A2A agent discovery metadata
├── task_manager.py   ← in-memory task state machine
├── skills_adapter.py ← bridges A2A task calls to Bob skill logic
├── auth.py           ← HMAC-SHA256 bearer token validation
├── requirements.txt  ← Python dependencies
├── startup.sh        ← used by installer start/stop; writes .a2a.pid
└── security/
    └── README.md     ← security model, trust boundary, token rotation
```

---

## Configuration (`.env`)

| Variable | Default | Purpose |
|---|---|---|
| `A2A_HOST` | `127.0.0.1` | Bind address (never `0.0.0.0`) |
| `A2A_PORT` | `8080` | Listen port |
| `A2A_SECRET` | *(required)* | HMAC signing secret for bearer tokens |
| `A2A_LOG_LEVEL` | `info` | Uvicorn log level |

Copy `.env.example` → `.env` and set `A2A_SECRET` to a random 32-byte hex string:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Security

See [`security/README.md`](security/README.md) for the trust model, token rotation
procedure, and incident response guidance.

Key rules:
- The server binds only to `127.0.0.1` — never expose it on `0.0.0.0`
- All requests require a valid HMAC-SHA256 bearer token
- No customer case data is stored by the A2A layer; it delegates immediately to skills
- Rotate `A2A_SECRET` whenever a token is suspected compromised

---

## Uninstalling

```bash
# Stop the server, remove A2A files, leave core agent intact
bash ../installer.sh remove --a2a
```
