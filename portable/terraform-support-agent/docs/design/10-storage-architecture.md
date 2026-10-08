# 10 — Storage Architecture

**Status:** Draft v1  
**Applies to:** All persistent state: cases, checkpoints, memory, audit logs, metrics  
**Related:** doc 08 (PII/encryption), doc 09 (wire format), `trace-event.schema.json`

---

## 1. Design Principles

1. **Flat-file first** — Phase 1 and 2 use no daemon, no server, no network service. All storage is local files the operator can inspect with a text editor.
2. **SQLite for indexed lookups only** — SQLite is used as an index and search layer, not as the source of truth. The source of truth is always the Markdown checkpoint or JSONL log file.
3. **PII stays encrypted** — Raw sensitive values live only in `vault/`; all other files hold XCVBH tokens (see doc 08).
4. **Append-only logs** — Audit JSONL files are never edited; corrections are new entries with a `corrects_event_id` field.
5. **No cloud sync in Phase 1–2** — Everything stays on the operator's local machine. Phase 3 adds optional encrypted export.

---

## 2. Directory Layout

```
<agent_repo_path>/                    ← set in memory/preferences.md
├── vault/
│   ├── .key                          ← AES-256 passphrase (chmod 600, gitignored)
│   └── <session_ulid>.jsonl          ← token → encrypted value, one per session
│
├── cases/
│   └── <case_alias>/
│       ├── intake.md                 ← original (tokenised) case description
│       ├── pass_1.md                 ← checkpoint after first 3-pass loop
│       ├── pass_N.md                 ← subsequent passes
│       └── result.md                 ← final operator-facing summary
│
├── messages/
│   └── <session_ulid>/
│       ├── <msg_id>.json             ← raw SignedEnvelope JSON (tokenised)
│       └── …
│
├── evidence/
│   └── <case_alias>/
│       ├── <evidence_slug>.txt       ← raw evidence files (tokenised)
│       └── …
│
├── memory/
│   ├── preferences.md                ← operator identity (YAML front matter)
│   ├── patterns/
│   │   └── <pattern_slug>.md         ← reusable solution patterns
│   └── corrections/
│       └── <correction_id>.md        ← operator corrections to past responses
│
├── audit/
│   └── <YYYY-MM-DD>.jsonl            ← trace-event.schema.json records, one per line
│
├── metrics/
│   └── <YYYY-MM>.jsonl               ← performance/volume metrics, aggregated daily
│
└── stf.db                            ← SQLite index (see §4); source of truth is files above
```

---

## 3. File Formats

### 3.1 Case checkpoint (`cases/<alias>/pass_N.md`)

YAML front matter followed by Markdown body.

```yaml
---
case_alias:    acme-vpc-nosuchkey-20240610
session_id:    session_01J1ABCDEF000000000000
pass:          1
state:         waiting_approval          # draft | running | waiting_approval | completed | failed
started_at:    2024-06-10T09:00:00Z
completed_at:  2024-06-10T09:04:12Z
operator:      "{{operator_name}}"
approved_by:   null
artifacts:
  - evidence/acme-vpc-nosuchkey-20240610/plan.txt
---

## Diagnosis

Customer XCVBH-3f9a1b2c-0001 reported `NoSuchKey` on Terraform apply for the `vpc` module.
…
```

### 3.2 Audit log (`audit/<YYYY-MM-DD>.jsonl`)

One JSON object per line; conforms to `trace-event.schema.json`.

```jsonl
{"schema_version":1,"event_id":"evt_01J1...","task_id":"task_01J1...","run_id":"run_01J1...","agent_id":"coordinator","runner_id":"bob","host_id":"macbook-pro","adapter_id":"stf-v1","adapter_version":"0.1.0","sequence":1,"timestamp":"2024-06-10T09:00:01Z","event_type":"task_received","status":"success","capability":"intake","tool":null,"input_ref":"messages/session_01J1.../msg_01J1....json","output_ref":null,"policy_version":"v1","policy_decision":"allow","duration_ms":0}
```

### 3.3 Metrics log (`metrics/<YYYY-MM>.jsonl`)

Lightweight aggregates; not `trace-event` format.

```jsonl
{"date":"2024-06-10","case_alias":"acme-vpc-nosuchkey-20240610","pass_count":2,"total_duration_ms":248000,"specialist_calls":{"terraform":3,"communication":1},"approval_required":true,"resolved":true}
```

### 3.4 Memory patterns (`memory/patterns/<slug>.md`)

```yaml
---
pattern_id:    terraform-nosuchkey-s3
created_at:    2024-06-10T09:05:00Z
applies_to:    ["terraform", "s3", "NoSuchKey"]
confidence:    high
source_case:   acme-vpc-nosuchkey-20240610
---

## Pattern: Terraform S3 `NoSuchKey` on Apply

When `aws_s3_object` resources reference a bucket that doesn't yet exist in the same plan…
```

---

## 4. SQLite Index (`stf.db`)

The DB is an index only. Deleting it and re-running the `rebuild_index` maintenance skill reconstructs it from the flat files.

### Tables

```sql
-- Case registry
CREATE TABLE cases (
    case_alias       TEXT PRIMARY KEY,
    session_id       TEXT NOT NULL,
    state            TEXT NOT NULL,          -- last known state from front matter
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL,
    checkpoint_path  TEXT NOT NULL           -- relative path to latest pass_N.md
);

-- Pattern registry
CREATE TABLE patterns (
    pattern_id       TEXT PRIMARY KEY,
    slug             TEXT NOT NULL,
    applies_to_json  TEXT NOT NULL,          -- JSON array of tags
    confidence       TEXT NOT NULL,
    file_path        TEXT NOT NULL
);

-- Corrections index
CREATE TABLE corrections (
    correction_id    TEXT PRIMARY KEY,
    case_alias       TEXT,
    created_at       TEXT NOT NULL,
    file_path        TEXT NOT NULL
);

-- Audit event index (fast lookups; full events in JSONL)
CREATE TABLE audit_index (
    event_id         TEXT PRIMARY KEY,
    task_id          TEXT NOT NULL,
    run_id           TEXT NOT NULL,
    agent_id         TEXT NOT NULL,
    timestamp        TEXT NOT NULL,
    event_type       TEXT NOT NULL,
    status           TEXT NOT NULL
);
```

### Index maintenance

| Operation | Trigger |
|-----------|---------|
| Insert/update case | After each checkpoint write |
| Insert pattern | After Memory Curator creates a pattern file |
| Insert audit_index row | After each audit JSONL append |
| Full rebuild | Manual: `stf rebuild-index` (skill call) |

---

## 5. Access Control by Actor

| Actor | Read | Write | Delete |
|-------|------|-------|--------|
| **Coordinator** | `cases/`, `memory/`, `messages/`, `stf.db` | `cases/`, `messages/`, `audit/` (append) | ✗ |
| **Specialist agents** | Assigned `evidence/` files | `evidence/` (their case), `messages/` (replies) | ✗ |
| **Memory Curator** | `cases/`, `memory/` | `memory/patterns/`, `memory/corrections/` | Old pattern files (with operator approval) |
| **Operator** | All | `memory/preferences.md`, approval decisions | `cases/` (archive only) |
| **LLM context window** | Tokenised content only | ✗ | ✗ |
| **Vault** | Operator + de-tokeniser only | Intake skill (append) | ✗ |

---

## 6. Retention and Rotation

| Store | Retention | Rotation |
|-------|-----------|----------|
| `cases/` | Indefinite | Operator archives to `cases/archive/` manually |
| `vault/` | Per-session files kept until case is archived | Deleted with case archive |
| `messages/` | 30 days default | `stf prune-messages --older-than 30d` |
| `audit/` | 90 days default | Rotate to `audit/archive/YYYY/` after 90 days |
| `metrics/` | 12 months | Annual JSONL files; auto-rotate on new year |
| `stf.db` | Rebuilt on demand | Not backed up; rebuild from files |

---

## 7. Gitignore Requirements

The following paths must appear in `.gitignore` at the `agent_repo_path` root:

```gitignore
vault/
stf.db
audit/
metrics/
messages/
```

`cases/`, `memory/patterns/`, and `memory/corrections/` may be committed if the operator is comfortable with tokenised (non-plain-text) content in version control.

---

## 8. Data Flow Diagram

```
 Operator input
       │
       ▼
 Intake skill ──── redaction filter ────► vault/<session>.jsonl  (encrypted values)
       │
       ▼
 SignedEnvelope (tokenised)
       │
       ├──► messages/<session>/<msg>.json   (wire format, tokenised)
       │
       ▼
 Coordinator / Specialists (LLM calls, tokenised context)
       │
       ├──► cases/<alias>/pass_N.md         (checkpoint, tokenised front matter + body)
       ├──► evidence/<alias>/<slug>.txt     (evidence, tokenised)
       └──► audit/<date>.jsonl             (trace events, tokenised)
                │
                └──► stf.db audit_index   (fast lookup only)

 Operator reads result
       │
       ▼
 De-tokeniser reads vault/<session>.jsonl
       │
       ▼
 Plain-text rendered in terminal / dashboard
```

---

## 9. Phase Roadmap

| Phase | Storage capability |
|-------|--------------------|
| **1 (current)** | Flat files only; SQLite index built on demand; no automated pruning |
| **2** | Automated pruning scheduler; `stf.db` updated live; `rebuild_index` skill |
| **3** | Encrypted export of `cases/` + `vault/` bundle for cross-machine restore; optional remote backup via SFTP/S3 with client-side AES-GCM |
