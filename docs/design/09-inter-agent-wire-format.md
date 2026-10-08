# 09 — Inter-Agent Wire Format

**Status:** Draft v1  
**Applies to:** All coordinator ↔ specialist message passing  
**Depends on:** `task.schema.json` (v1), `result.schema.json` (v1), doc 08 (PII/encryption)

---

## 1. Purpose

Every message that crosses an agent boundary travels in a **SignedEnvelope**. The envelope:

1. Wraps the existing `task` or `result` payload unchanged.
2. Adds routing, versioning, and timing metadata.
3. Carries a `redaction_summary` that tells the receiver which fields were substituted with XCVBH tokens **without** including the vault mapping itself.
4. Is opaque to the LLM — field values for redacted data are token IDs, never plain text.

---

## 2. Top-Level Structure

```jsonc
{
  // ── Envelope header ──────────────────────────────────────────────────────
  "env_version":    1,                       // increment on breaking changes
  "msg_id":         "msg_<ulid>",            // unique per message
  "sent_at_ms":     1718000000000,           // Unix epoch ms (UTC)
  "ttl_ms":         30000,                   // receiver must reject if stale
  "from":           "coordinator",           // agent_id as in agent.schema.json
  "to":             "specialist/terraform",  // agent_id
  "msg_type":       "task | result | ack | nack | heartbeat",

  // ── Payload ──────────────────────────────────────────────────────────────
  // Exactly one of "task" or "result" is present; others are null / absent.
  "task":   { /* task.schema.json v1 */ },
  "result": { /* result.schema.json v1 */ },

  // ── Redaction manifest ───────────────────────────────────────────────────
  // Lists which payload fields were substituted; does NOT include vault path.
  "redaction_summary": {
    "token_count":    3,
    "fields_redacted": ["input.customer_name", "input.account_id", "intent"],
    "vault_ref":      "session_<ulid>"        // opaque; receiver uses its own vault
  },

  // ── Integrity ─────────────────────────────────────────────────────────────
  "payload_hash":   "sha256:<hex>",           // hash of canonical payload JSON
  "sig":            null                      // Phase 3: HMAC-SHA256 of envelope JSON
}
```

### Rules

| Rule | Detail |
|------|--------|
| **One payload type** | Exactly one of `task` / `result` is populated; the other key is omitted. |
| **msg_id uniqueness** | ULID-prefixed; coordinator generates for outbound, specialist echoes in `ack`. |
| **TTL enforcement** | Receiver computes `now_ms - sent_at_ms`; if > `ttl_ms`, logs a `nack` and discards. |
| **payload_hash** | Computed over the `task` or `result` object only (not the envelope). Receiver verifies before processing. |
| **vault_ref** | The vault mapping file for this session's tokens; stored locally; never transmitted to LLM. |

---

## 3. XCVBH Token Substitution in Payloads

Before a payload is placed inside the envelope, the **Redaction Filter** (intake skill) walks every `string` field and replaces sensitive values.

### Token format

```
XCVBH-<8-char-sha256-prefix>-<4-digit-counter>
```

Example:
- Input string: `"Acme Corp"`
- Token ID:     `XCVBH-3f9a1b2c-0001`

The token is:
- **Deterministic** within a session — same input string → same token ID (enables the LLM to notice "this field appears again").
- **Non-guessable** — the prefix is truncated SHA-256 of `(session_salt + input)`; without the session salt it reveals nothing.
- **Session-scoped** — tokens from session A cannot be re-used in session B (different salt).

### What travels vs what stays local

| Location | Content |
|----------|---------|
| **Envelope payload** | XCVBH token IDs only — no plain text |
| **LLM context window** | Envelope payload — sees tokens, never values |
| **Local vault file** | `vault/<session_ulid>.jsonl` — maps token ID → AES-GCM encrypted value |
| **redaction_summary** | Field names + token count — no values |

### Substitution depth

The filter recurses into nested objects and arrays. It does **not** substitute:
- `task_id`, `msg_id`, `schema_version`, `env_version`, `sent_at_ms`, `ttl_ms`, `from`, `to`, `msg_type` — these are structural, not PII.
- Values that are already XCVBH token IDs (idempotent).

---

## 4. Message Types

### 4.1 `task` — Coordinator → Specialist

The coordinator sends a `task.schema.json` payload with XCVBH substitution applied.

```jsonc
{
  "env_version": 1,
  "msg_id":      "msg_01J1ABCDEF000000000001",
  "sent_at_ms":  1718000000000,
  "ttl_ms":      60000,
  "from":        "coordinator",
  "to":          "specialist/terraform",
  "msg_type":    "task",
  "task": {
    "schema_version":        1,
    "task_id":               "task_01J1ABCDEF000000000002",
    "requested_by":          "coordinator",
    "task_type":             "terraform_plan_review",
    "intent":                "Review plan for XCVBH-3f9a1b2c-0001 account",
    "input": {
      "customer_name":       "XCVBH-3f9a1b2c-0001",
      "account_id":          "XCVBH-4a2b3c1d-0002",
      "tf_module":           "vpc",
      "error_class":         "NoSuchKey"
    },
    "acceptance_criteria":   ["Plan renders without error", "All variables resolved"],
    "requested_capabilities": ["terraform", "file_read"],
    "state":                 "ready"
  },
  "redaction_summary": {
    "token_count":     2,
    "fields_redacted": ["task.intent", "task.input.customer_name", "task.input.account_id"],
    "vault_ref":       "session_01J1ABCDEF000000000000"
  },
  "payload_hash": "sha256:e3b0c44298fc1c149afb..."
}
```

### 4.2 `result` — Specialist → Coordinator

```jsonc
{
  "env_version": 1,
  "msg_id":      "msg_01J1ABCDEF000000000003",
  "sent_at_ms":  1718000005000,
  "ttl_ms":      30000,
  "from":        "specialist/terraform",
  "to":          "coordinator",
  "msg_type":    "result",
  "result": {
    "schema_version":  1,
    "task_id":         "task_01J1ABCDEF000000000002",
    "status":          "success",
    "summary":         "Plan renders cleanly for XCVBH-3f9a1b2c-0001; 3 resources added.",
    "next_actions":    ["Apply after operator approval"],
    "artifacts":       ["checkpoints/task_01J1ABCDEF.md"],
    "evidence_refs":   ["evidence/vpc-plan.txt"]
  },
  "redaction_summary": {
    "token_count":     1,
    "fields_redacted": ["result.summary"],
    "vault_ref":       "session_01J1ABCDEF000000000000"
  },
  "payload_hash": "sha256:a4c2e1f8b3d7..."
}
```

### 4.3 `ack` / `nack`

```jsonc
{
  "env_version": 1,
  "msg_id":      "msg_01J1ABCDEF000000000004",
  "sent_at_ms":  1718000005100,
  "from":        "specialist/terraform",
  "to":          "coordinator",
  "msg_type":    "ack",
  "ack_msg_id":  "msg_01J1ABCDEF000000000001",  // echoes the msg being acknowledged
  "reason":      null
}
```

`nack.reason` is a short string: `"ttl_expired"`, `"hash_mismatch"`, `"schema_invalid"`, `"unknown_msg_type"`.

---

## 5. Schema Extension Points

The `task.schema.json` `input` field is `"type": "object"` with no `additionalProperties` constraint — specialist-specific inputs go there without schema changes.

The `result.schema.json` `artifacts` array carries local file paths. For sensitive artifact content, the artifact file itself uses XCVBH tokens; the path is not redacted.

---

## 6. Versioning

| Field | Rule |
|-------|------|
| `env_version` | Incremented only on breaking envelope changes. Receivers reject mismatched versions. |
| `schema_version` | Carried from `task.schema.json` / `result.schema.json`; envelope version is independent. |
| Forward compatibility | Unknown envelope keys are ignored by receivers at the same `env_version`. |

---

## 7. What the LLM Sees vs What Stays Local

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LLM CONTEXT WINDOW                                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  SignedEnvelope (msg_type=task)                                       │  │
│  │  task.input.customer_name  =  XCVBH-3f9a1b2c-0001   ← token only     │  │
│  │  task.input.account_id     =  XCVBH-4a2b3c1d-0002   ← token only     │  │
│  │  task.intent               =  "...XCVBH-3f9a1b2c-0001 account"       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  redaction_summary.vault_ref  =  "session_01J1..."  ← opaque reference      │
│  (vault file is never loaded into context)                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  LOCAL VAULT  (vault/session_01J1....jsonl — AES-GCM encrypted)             │
│  {"token": "XCVBH-<8hexchars>-0001", "enc_value": "<ciphertext>"}           │
│  {"token": "XCVBH-<8hexchars>-0002", "enc_value": "<ciphertext>"}           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Relationship to Existing Schemas

| Schema | Role in wire format |
|--------|---------------------|
| `task.schema.json` | Payload inside `task` envelope key; no modification required |
| `result.schema.json` | Payload inside `result` envelope key; no modification required |
| `trace-event.schema.json` | Produced by the envelope layer after each send/receive; `input_ref` / `output_ref` point to local envelope files |
| `agent.schema.json` | Provides canonical `agent_id` values used in `from` / `to` fields |

---

## 9. Phase Roadmap

| Phase | Wire format capability |
|-------|----------------------|
| 1 (current) | JSON files written to `messages/` directory; no network; coordinator reads specialist output file directly |
| 2 | Structured envelope enforced; `payload_hash` verified; `ttl_ms` checked |
| 3 | `sig` field populated with HMAC-SHA256; envelope encryption optional (TLS for any networked transport) |
