# Architecture Decisions — Terraform Support Agent

This register records accepted design decisions for the Terraform Support Agent.
Format follows `plan.md §7.3`. Proposals are made by the agent; entries are committed
only after operator approval.

---

## [ADR-001] Alias-to-ticket mapping — defer to Phase 4, use ticket numbers directly in Phase 3b

- **Date:** 2026-10-02
- **Status:** Accepted
- **Context:**
  Design doc `04-memory-and-evidence-schemas.md` (MQ-01) left the alias-to-ticket
  mapping store undefined. The concern is that checkpoints must not contain real
  customer identifiers (ticket numbers, company names), so a pseudonym/alias scheme
  was proposed. Three options were evaluated:

  - **Option A** — Gitignored `memory/.alias-map.jsonl` with AES-256 encryption, key from OS keychain.
  - **Option B** — OS keychain entries directly (one per alias).
  - **Option C** — Defer alias scheme; use ticket number directly in checkpoint front matter for Phase 3b.

- **Alternatives Evaluated:**
  1. *Option A (encrypted local file):* Provides strong pseudonymisation but requires key
     management infrastructure and an encryption/decryption utility that does not yet exist.
     Appropriate for Phase 4+ when real cases are processed.
  2. *Option B (OS keychain):* Simple but limited to a single machine; does not scale when
     the agent moves to a separate repo or CI environment.
  3. *Option C (defer):* Uses ticket number directly in checkpoint YAML front matter for
     Phase 3b eval runs. Eval cases are sanitized (no real customer data), so the risk
     of PII exposure is zero. Alias mapping is introduced in Phase 4 when real cases begin.

- **Decision:** Option C — defer alias mapping to Phase 4. Use ticket number directly in
  checkpoint front matter during Phase 3b. All Phase 3b runs use sanitized eval cases only.

- **Rationale:**
  Phase 3b evals (E01–E10) use sanitized synthetic data — no real customer identifiers.
  Building encryption infrastructure before it is needed would add complexity with zero
  current security benefit. The decision is revisited at the Phase 4 gate when real cases
  are first processed.

- **Consequences:**
  - Positive: No encryption dependency in Phase 3b; simpler checkpoint schema.
  - Positive: Reduces Phase 3b scope, allowing faster iteration on A2A scaffold.
  - Negative: If a real case is accidentally processed before Phase 4, the ticket number
    appears in plaintext in the checkpoint. Mitigation: coordinator skill explicitly
    blocks real-case use until operator approves Phase 4 gate.
  - Action required in Phase 4: Implement Option A (encrypted alias map) before Phase 4
    gate approval. Update checkpoint schema to replace ticket refs with alias tokens.

---
