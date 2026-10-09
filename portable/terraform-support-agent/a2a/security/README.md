# A2A Security Model

> **Phase**: 3b scaffold — incomplete. Finalise during Phase 4 security review.

---

## Trust boundary

The A2A server is a **local-only** component. It binds exclusively to
`127.0.0.1` (loopback). No inbound connections from outside the operator's
workstation are permitted or supported.

```
[External orchestrator]  ←— loopback only —→  [A2A server :8080]  →  [Bob skills]
```

Only software running on the same machine as the operator can reach the server.
Exposing port 8080 to a network interface (`0.0.0.0`) or through a reverse proxy
requires a separate security review and is explicitly **not** supported at this phase.

---

## Authentication

Every inbound request must include a bearer token in the `Authorization` header:

```
Authorization: Bearer <token>
```

Tokens are HMAC-SHA256 signatures derived from `A2A_SECRET` in `a2a/.env`.
The `auth.py` module validates each request before it reaches any skill logic.

Requests without a valid token receive `HTTP 401 Unauthorized`.

---

## Secret management

| Item | Rule |
|---|---|
| `A2A_SECRET` | Minimum 32 bytes of random hex. Never a human-memorable string. |
| `a2a/.env` | Git-ignored. Never committed. Created by `installer.sh --a2a`. |
| Token lifetime | Tokens do not expire automatically. Rotate on any suspected compromise. |

### Generating a secret

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Paste the output into `a2a/.env` as `A2A_SECRET=<value>`.

### Rotating the secret

1. Generate a new secret (command above).
2. Stop the A2A server: `bash installer.sh stop --a2a`.
3. Update `A2A_SECRET` in `a2a/.env`.
4. Restart: `bash installer.sh start --a2a`.
5. Reissue tokens to any callers that used the old secret.

---

## Logging

The server logs to `a2a/a2a-server.log` (git-ignored).

Logged events:
- Server start/stop with bind address and port
- Each inbound request: method, path, response status (no body content)
- Authentication failures (no token detail in log — just `AUTH_FAIL`)

Never log: bearer tokens, `A2A_SECRET`, case content, or operator credentials.

---

## Incident response

If a token or secret is suspected compromised:

1. Immediately stop the server: `bash installer.sh stop --a2a`
2. Rotate `A2A_SECRET` (see above)
3. Review `a2a/a2a-server.log` for unexpected requests
4. Restart with new secret
5. Notify any upstream orchestrators that used the old token

---

## Open items (Phase 4)

- [ ] Decide on token expiration / rotation policy
- [ ] Evaluate whether mTLS is needed for multi-host deployments
- [ ] Define which skill operations the A2A layer is permitted to expose
- [ ] Add rate limiting to `auth.py`
- [ ] Complete threat model for remote orchestrator scenario
