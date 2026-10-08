# Design 01 — Coordinator Contract

> **Status**: Draft — awaiting operator review.
> **Prepared**: 2 October 2026.  
> **Scope**: Design phase only. No agent code, prompts, or configuration are created here.

---

## 1. Identity

```yaml
agent_id: terraform-support-coordinator
version: 0.1.0
description: >
  Single entry point for the operator's Terraform support workflow.
  Owns the case from intake to closure. Delegates focused work to
  specialist sub-agents. Returns one consistent case assessment and
  next action per invocation. Never sends external messages directly.
```

STF schema fields (from `portable/schemas/agent.schema.json`):

```json
{
  "schema_version": 1,
  "agent_id": "terraform-support-coordinator",
  "version": "0.1.0",
  "description": "Single entry point for Terraform support case management.",
  "inputs_schema": "see Section 3",
  "outputs_schema": "see Section 4",
  "required_capabilities": [
    "read_supplied_evidence",
    "search_approved_public_sources",
    "write_sanitized_checkpoints_proposed"
  ],
  "optional_capabilities": [
    "spawn_diagnostics_subagent",
    "spawn_source_researcher_subagent",
    "spawn_validation_reviewer_subagent",
    "spawn_communication_specialist_subagent",
    "spawn_memory_curator_subagent"
  ],
  "approval_classes": [
    "external_message",
    "case_update",
    "severity_change",
    "collaboration_case_creation",
    "pagerduty_engagement",
    "case_closure",
    "run_operation",
    "state_operation",
    "config_change",
    "memory_commit"
  ],
  "eval_refs": [
    "evals/cases/README.md"
  ],
  "timeout_seconds": 300,
  "max_cost_units": 50
}
```

---

## 2. Responsibilities

### Always owned by the coordinator (never delegated)

| Responsibility | Description |
|---|---|
| Intake and redaction | Receive case packet; strip credentials, names, org/workspace/run IDs, tokens, raw state, plan JSON, raw logs before any sub-agent receives them |
| Scope classification | Determine HCP Terraform vs Terraform Enterprise vs Public Registry vs Private Registry ownership; identify product and version early |
| Task selection | Decide which sub-agents to invoke, in which order, with which evidence slice |
| Permission gate | Block any auth-required action until explicit per-action approval is recorded |
| Conflict resolution | If sub-agent findings conflict, own the targeted re-check — do not majority-vote |
| Result assembly | Produce one STF result envelope from reconciled findings |
| Progress and blocker reporting | If progress halts, name the exact blocker and exactly one next action |
| Checkpoint write (proposed) | Write sanitized case checkpoint — as a candidate requiring human approval |

### Delegated work

| Work | Delegate | Condition |
|---|---|---|
| Log/HCL/version analysis | Diagnostics | Any case with supplied logs, plans, or configuration |
| Documentation lookup | Source Researcher | Any case requiring source verification |
| Cause/remedy challenge | Validation Reviewer | After Diagnostics + Source Researcher findings are consolidated |
| Draft communication | Communication Specialist | After Validation Reviewer approves findings |
| Memory curation | Memory Curator | After customer confirms resolution |
| Minimal reproduction | Reproduction skill | Conditional — only with approved isolated environment |

---

## 3. Input schema

The coordinator receives a **case packet** — a structured Markdown document with the following required sections:

```
## Case alias
[Internal alias — never the real case/ticket number in persistent memory]

## Requested output
[What the operator wants: assessment | customer reply | internal update | handoff | CAN | RCA | closure | KB draft]

## Product and version scope
[HCP Terraform | Terraform Enterprise | Terraform Core | Provider name + version | CLI version]

## Case stage
[open | investigating | awaiting customer | awaiting engineering | escalated | pending closure]

## Case description
[Redacted narrative — no credentials, no real org/workspace/run IDs, no tokens, no raw state]

## Previous actions
[What has been tried; what the customer has confirmed or denied]

## Supplied evidence
[Attached redacted logs, HCL, run output, error messages — or "none"]

## Current hypothesis (optional)
[If the operator has a working theory — coordinator will validate or challenge it]

## Checkpoint (optional)
[Path to previously saved sanitized checkpoint, if resuming]
```

Full input type definition:

```typescript
interface CasePacket {
  case_alias: string;                    // e.g. "CASE-2026-001" — never real ticket ID in memory
  requested_output: RequestedOutput;
  product_scope: ProductScope;
  case_stage: CaseStage;
  description: string;                   // redacted
  previous_actions: string[];
  supplied_evidence: EvidenceItem[];     // each: { label, content_redacted, format }
  current_hypothesis?: string;
  checkpoint_path?: string;
}

type RequestedOutput =
  | "assessment"
  | "customer_reply"
  | "internal_update"
  | "handoff"
  | "can_report"
  | "rca"
  | "closure"
  | "kb_draft";

type CaseStage =
  | "open"
  | "investigating"
  | "awaiting_customer"
  | "awaiting_engineering"
  | "escalated"
  | "pending_closure";

interface ProductScope {
  primary: "hcp_terraform" | "terraform_enterprise" | "terraform_core" | "provider" | "public_registry" | "private_registry";
  provider_name?: string;
  product_version?: string;
  cli_version?: string;
}
```

---

## 4. Output schema (STF result envelope)

The coordinator always returns a valid `result.schema.json` envelope:

```json
{
  "schema_version": 1,
  "task_id": "<case_alias>-<pass_number>",
  "status": "success | partial | failed | blocked | cancelled",
  "summary": "<2–4 sentence plain-English case summary>",
  "next_actions": [
    "<one primary recommended next action>",
    "<optional secondary action if parallel track is useful>"
  ],
  "artifacts": [
    "checkpoints/<case_alias>-pass-<n>.md",
    "drafts/<case_alias>-<output_type>.md"
  ],
  "evidence_refs": [
    "<source title> | <full URL or internal ref> | retrieved <date> | <product+version> | public|internal"
  ],
  "error_class": "<only if status is failed or blocked>",
  "recovery_hint": "<only if status is failed or blocked — exact blocker + one next action>"
}
```

### `status` semantics

| Value | Meaning |
|---|---|
| `success` | Findings complete, draft produced, no outstanding blockers |
| `partial` | Findings complete but one or more sections require additional evidence; draft is provisional |
| `blocked` | Progress halted — exact blocker and one next action stated in `recovery_hint` |
| `failed` | Tool or process error — `error_class` and `recovery_hint` populated |
| `cancelled` | the operator stopped the task explicitly |

---

## 5. Investigation loop (bounded)

```
Pass 1 of 3 (per evidence set):
  1. Reconstruct timeline from supplied evidence
  2. Classify ownership (HCP TF / TFE / Registry / Provider / Cloud)
  3. Identify missing prerequisites — ask only for what changes the next diagnostic step
  4. Check checkpoint for prior matching patterns (as leads, not confirmed causes)
  5. Formulate ranked hypotheses (each: supporting evidence, conflicting evidence, discriminating check)

  → If complex: spawn Diagnostics + Source Researcher (parallel intent, sequential fallback)
  → Consolidate findings; detect conflicts → targeted re-check if conflict found
  → Spawn Validation Reviewer
  → If findings validated: spawn Communication Specialist for requested output type
  → Produce result envelope

Pass 2–3: triggered only by new customer or Engineering evidence
  Resume from checkpoint; re-evaluate affected conclusions only

Stop conditions (halt and return blocker):
  - 3 passes exhausted on same evidence set
  - 2 transient tool errors on same operation
  - Sources conflict with no clear resolution path
  - Auth-required action encountered without explicit approval
  - Credential or secret identified in input (must redact first)
  - Support ownership cannot be determined
  - New evidence received mid-pass (complete current pass, then resume from checkpoint)
```

---

## 6. Permission gate

Every action in `approval_classes` requires:

1. **Prior to execution**: coordinator states the exact target, action, evidence reference, and expected outcome. Presents to the operator for explicit confirmation.
2. **At execution**: records authorization (`authorized_by: {{operator_name}}`, `authorized_at: <ISO timestamp>`, `action: <exact action>`, `target: <exact target>`, `rationale: <one sentence>`).
3. **Post-execution**: records actual outcome. A failed action must never be reported as completed.

The coordinator must not imply that an action has been taken if it has not. It must not request credentials in chat.

---

## 7. Scope classification rules

The coordinator must resolve product ownership before any diagnosis:

| Signal | Ownership |
|---|---|
| `.terraform.lock.hcl`, workspace ID format `ws-*`, run ID format `run-*` | HCP Terraform |
| Self-hosted, license file, `terraform-enterprise` hostname pattern | Terraform Enterprise |
| `registry.terraform.io/` in module/provider source; publishing workflow | Public Registry |
| Private module/provider source within an HCP TF or TFE org | Private Registry |
| `terraform` binary version mismatch, core error in `terraform apply/plan/init` | Terraform Core |
| Provider-specific error, `hashicorp/<provider>` or third-party provider | Provider (identify vendor) |
| AWS/Azure/GCP/VCS/SSO error in context of Terraform integration | Cloud/VCS provider — IBM support owns Terraform side, cloud vendor owns their side |

If the signal is ambiguous, state the ambiguity and ask one clarifying question before proceeding.

---

## 8. Conflict handling

When Diagnostics and Source Researcher findings conflict:

1. **Do not majority-vote** — the coordinator owns the re-check.
2. State the specific conflict precisely: which finding, which source, which version.
3. Perform a targeted check — does the conflicting source apply to the exact product version in the case?
4. If resolvable: annotate which finding is applicable and why; proceed with validated findings.
5. If unresolvable: return `status: blocked` with the conflict as the exact blocker and one disambiguation question as `recovery_hint`.

---

## 9. Failure handling

| Failure type | Coordinator action |
|---|---|
| Sub-agent returns `status: failed` | Log `error_class` + `recovery_hint`; attempt once with reduced scope; if second failure: return partial result with blocker |
| Tool transient error | Retry once (2 attempts total); if both fail: return `status: blocked` with tool name as blocker |
| Sub-agent exceeds timeout | Treat as partial — proceed without that specialist's input, flag the gap in result |
| Bob spawn approval declined | Proceed with coordinator-only investigation; note reduced confidence in result |
| Conflicting sources | See Section 8 |
| Auth-required action without approval | Return `status: blocked`; do not attempt action |

---

## 10. Unresolved design questions

| # | Question | Impact |
|---|---|---|
| CQ-01 | What is the maximum token budget per coordinator pass? | Affects how much evidence can be included in sub-agent packets |
| CQ-02 | Should checkpoint writes be inline (same pass) or post-pass? | Affects atomicity and resumption fidelity |
| CQ-03 | How should conflicting-but-equally-valid sources from different product versions be surfaced? | Affects hypothesis confidence scoring |
| CQ-04 | What constitutes "new evidence" that triggers a fresh pass (vs a clarification that fits the existing pass)? | Affects pass counter management |

---

*Previous: [`00-overview.md`](00-overview.md) | Next: [`02-specialist-contracts.md`](02-specialist-contracts.md)*
