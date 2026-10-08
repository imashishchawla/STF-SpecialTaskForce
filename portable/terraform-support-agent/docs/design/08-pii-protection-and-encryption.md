# 08 — PII Protection and Encryption

**Status:** Draft v1  
**Applies to:** All case intake, agent context loading, and message passing  
**Related:** doc 09 (wire format), doc 10 (storage), intake skill

---

## 1. Threat Model

The STF agent bundle passes case data into an LLM context window. That window may:
- Be logged by the LLM provider.
- Appear in debug traces.
- Be reconstructed from output artefacts.

**Goal:** Sensitive fields never appear in plaintext in any LLM call, any checkpoint file committed to version control, or any log file that leaves the local machine.

**In scope for Phase 1–2:**
- Customer-identifying strings (names, account IDs, email addresses, IP addresses, domain names).
- Internal infrastructure identifiers (resource ARNs, VPC IDs, cluster names).
- Credentials or tokens if accidentally included in case input.

**Out of scope for Phase 1:**
- Terraform state file content (treated as a file reference, not inlined).
- Log file content (stored as an evidence reference, not quoted verbatim in context).

---

## 2. Data Classification Tiers

| Tier | Examples | Treatment |
|------|----------|-----------|
| **Public** | Error class labels (`NoSuchKey`, `AccessDenied`), Terraform resource types, AWS region codes | Plain text; no substitution |
| **Internal** | Module paths, repo names, team slugs (non-customer) | Plain text unless the operator marks them sensitive |
| **Redacted** | Customer names, account IDs, project codes, email addresses | Replaced with XCVBH token in LLM context; stored encrypted in vault |
| **Encrypted** | Passwords, API tokens, secret ARNs, private keys | Replaced with XCVBH token; vault entry itself encrypted with AES-256-GCM |

The intake skill classifies fields using a **field-name allowlist** (Tier Public/Internal) plus a **pattern scanner** (Tier Redacted/Encrypted). Field names not on the allowlist are Redacted by default.

---

## 3. XCVBH Token Scheme

### 3.1 Token format

```
XCVBH-<8-char-prefix>-<4-digit-counter>
```

- `XCVBH` — fixed sentinel; immediately recognisable as a synthetic token.
- `<8-char-prefix>` — first 8 hex characters of `SHA-256(session_salt || raw_value)`.
- `<4-digit-counter>` — zero-padded integer, incremented per unique value in the session.

### 3.2 Properties

| Property | Description |
|----------|-------------|
| **Deterministic per session** | Same `raw_value` in the same session → same token ID. The LLM can see "this token appears in both the task and the evidence" without knowing the value. |
| **Non-guessable** | Without `session_salt` (stored only in the vault key file), the prefix is computationally opaque. |
| **Session-scoped** | `session_salt` is a fresh 32-byte random value per case session; tokens from session A are meaningless in session B. |
| **Idempotent** | Applying the filter twice to already-tokenised text is a no-op. |

### 3.3 Token generation (pseudocode)

```python
def make_token(raw_value: str, session_salt: bytes, counter: int) -> str:
    digest = sha256(session_salt + raw_value.encode()).hexdigest()
    prefix = digest[:8]
    return f"XCVBH-{prefix}-{counter:04d}"
```

### 3.4 Session vault file

Location: `vault/<session_ulid>.jsonl`  
Format: one JSON object per line.

```jsonl
{"token": "XCVBH-<8hexchars>-0001", "tier": "redacted",   "enc_value": "<base64-AES-GCM>"}
{"token": "XCVBH-<8hexchars>-0002", "tier": "encrypted",  "enc_value": "<base64-AES-GCM>"}
```

- `enc_value` — AES-256-GCM ciphertext of the UTF-8 raw value.
- The AES key is derived from the operator's machine keychain entry (Phase 1: a local passphrase stored in `vault/.key` with `chmod 600`).
- The vault file is **never** loaded into LLM context, passed over the wire to any agent, or committed to version control.

---

## 4. Redaction Filter Pipeline

```
Incoming case text
        │
        ▼
┌──────────────────────────────┐
│  1. Pattern scanner          │  Regex: email, IP, AWS ARN, UUID, credit card…
│     → marks spans as         │  Field names: customer_*, account_*, secret_*…
│       Redacted / Encrypted   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  2. Token lookup / create    │  Check vault for existing token
│     (per unique value)       │  If new: increment counter, AES-encrypt, append to vault
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  3. Substitution             │  Replace each span with XCVBH token ID
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  4. Redaction manifest       │  Build redaction_summary for envelope
│     (field names + count)    │  No values; no vault path
└──────────────┬───────────────┘
               │
               ▼
        Sanitised payload → SignedEnvelope → LLM
```

---

## 5. De-tokenisation

De-tokenisation is performed **only at display time** — when the operator reads a checkpoint or the dashboard renders output. It is **never** performed inside the LLM context window.

```
Checkpoint / result text
        │
        ▼
┌──────────────────────────────┐
│  Regex: find XCVBH-*-* spans │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Open vault for session      │  Decrypt AES key from keychain
│  Build token → value map     │  Decrypt each enc_value with AES-GCM
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Replace token IDs with      │
│  plain-text values           │
└──────────────┬───────────────┘
               │
               ▼
        Human-readable output (terminal / dashboard only)
```

---

## 6. What Each Role Sees

| Role | Sees plain-text values? | Notes |
|------|------------------------|-------|
| **LLM (any provider)** | No | Only XCVBH token IDs |
| **Coordinator agent** | No | Works entirely in tokenised space |
| **Specialist agents** | No | Receive task envelopes with tokens |
| **Operator (terminal)** | Yes, on demand | De-tokenisation at display time only |
| **Dashboard HTML** | Yes, on demand | De-tokenisation called from local JS reading vault |
| **Audit log (JSONL)** | No | Stores token IDs; vault separate |
| **Checkpoint Markdown** | No (raw) / Yes (rendered) | Raw file contains tokens; viewer de-tokenises |

---

## 7. Credential Interception

If the pattern scanner finds a string matching a known credential format (AWS access key, GitHub PAT, PEM header), it:

1. Replaces with an `Encrypted`-tier XCVBH token.
2. Appends a `credential_warning` event to the session trace log.
3. Does **not** surface the warning in the LLM context window (to avoid the LLM repeating it back).
4. Presents a terminal warning to the operator before any LLM call proceeds.

---

## 8. Checklist: Operator Onboarding

Before the first case in a new installation:

- [ ] `vault/` directory exists and is in `.gitignore`.
- [ ] `vault/.key` exists with `chmod 600` (or keychain entry is configured).
- [ ] `memory/preferences.md` `operator_name` is set (non-empty).
- [ ] Intake skill has run the redaction filter on at least one test case.
- [ ] No XCVBH-free sensitive strings appear in any `messages/` or `checkpoints/` file.

---

## 9. Phase Roadmap

| Phase | Capability |
|-------|-----------|
| **1 (current)** | Pattern scanner + XCVBH substitution; AES-GCM vault keyed from local passphrase file |
| **2** | Keychain integration (macOS Keychain, Linux Secret Service); audit log of all redaction events |
| **3** | Differential privacy budget tracking; optional encrypted export of vault for cross-machine restore |
