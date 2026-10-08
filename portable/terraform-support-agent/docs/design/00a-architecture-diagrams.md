# Design 00a — Architecture and Data-Flow Diagrams

> **Status**: Draft — awaiting operator review.
> **Prepared**: companion to `00-overview.md` and `01-coordinator-contract.md`.  
> **Scope**: Design-phase Mermaid diagrams only. No runnable code is created.

---

## 1. End-to-end system flow

```mermaid
flowchart TD
    A([Operator — manual input]) -->|case packet\nMarkdown + YAML front matter| B[Coordinator\nterraform-support-coordinator]

    B --> C{complexity\nthreshold?}
    C -->|simple| D[Coordinator solo\ninvestigation]
    C -->|complex| E[Request Bob\nspawn approval]

    E -->|Bob approves\nDiagnostics| F[Diagnostics\nsub-agent]
    E -->|Bob approves\nSource Researcher| G[Source Researcher\nsub-agent]
    E -->|Bob declines spawn| D

    F -->|findings: observations\nhypotheses ranked\ndiscriminating checks| H[Coordinator\nconsolidate]
    G -->|findings: doc passages\nURLs\nversion applicability| H

    H --> I{conflict\ndetected?}
    I -->|yes — targeted re-check| H
    I -->|no| J[Validation Reviewer\nsub-agent]

    D --> J
    J -->|validated findings\nOR evidence gaps| K{validated?}
    K -->|gaps — return blocker| Z1([Return: status=blocked\nrecovery_hint])
    K -->|yes| L[Communication Specialist\nsub-agent]

    L -->|draft reply / update\n/ handoff / CAN / RCA| M[Coordinator\nassemble result envelope]
    M --> N([STF result.schema.json\nstatus · summary · next_actions\nartifacts · evidence_refs])

    N --> O{resolution\nconfirmed?}
    O -->|yes| P[Memory Curator\nsub-agent proposes]
    O -->|no| Z2([Case remains open\ncheckpoint saved])

    P -->|candidate entries| Q{Operator\napproves?}
    Q -->|yes| R[(memory/\npatterns · prefs · ops\ncorrections)]
    Q -->|no| S([Proposal discarded])

    style R fill:#d4edda,stroke:#28a745
    style Z1 fill:#fff3cd,stroke:#ffc107
    style Z2 fill:#fff3cd,stroke:#ffc107
    style S fill:#f8d7da,stroke:#dc3545
```

---

## 2. Investigation loop (bounded 3-pass)

```mermaid
flowchart TD
    START([CasePacket received]) --> P1

    subgraph P1["Pass 1 (or resumed pass N)"]
        direction TB
        T1[Reconstruct timeline\nclassify ownership] --> T2[Identify missing\nprerequisites]
        T2 --> T3[Check checkpoint\nfor prior patterns]
        T3 --> T4[Formulate ranked\nhypotheses]
        T4 --> T5{Spawn specialists?}
        T5 -->|yes| T6[Diagnostics +\nSource Researcher]
        T5 -->|no| T7[Coordinator-only\nanalysis]
        T6 --> T8[Consolidate\nfindings]
        T7 --> T8
        T8 --> T9[Validation Reviewer]
    end

    P1 --> SC{Stop\ncondition?}
    SC -->|3 passes exhausted\non same evidence| BLOCKED([status: blocked])
    SC -->|2 tool errors\nsame operation| BLOCKED
    SC -->|sources conflict\nno resolution| BLOCKED
    SC -->|auth action\nwithout approval| BLOCKED
    SC -->|credential in\ninput| REDACT([Redact first\nthen resume])
    SC -->|ownership\nambiguous| ASK([Ask one\nclarifying question])
    SC -->|new evidence\nmid-pass| RESUME([Complete pass\nresume from checkpoint])
    SC -->|validated| COMM[Communication\nSpecialist]

    COMM --> RESULT([STF result envelope])
    RESULT --> P2{New evidence\nreceived?}
    P2 -->|yes — max 3 passes total| P1
    P2 -->|no| END([Case closed or\nawaiting customer/engineering])

    style BLOCKED fill:#fff3cd,stroke:#ffc107
    style REDACT fill:#cce5ff,stroke:#004085
    style ASK fill:#cce5ff,stroke:#004085
```

---

## 3. Input — CasePacket structure

```mermaid
classDiagram
    class CasePacket {
        +string case_alias
        +RequestedOutput requested_output
        +ProductScope product_scope
        +CaseStage case_stage
        +string description_redacted
        +string[] previous_actions
        +EvidenceItem[] supplied_evidence
        +string? current_hypothesis
        +string? checkpoint_path
    }
    class ProductScope {
        +primary: hcp_terraform|terraform_enterprise|terraform_core|provider|public_registry|private_registry
        +string? provider_name
        +string? product_version
        +string? cli_version
    }
    class EvidenceItem {
        +string label
        +string content_redacted
        +string format
    }
    class RequestedOutput {
        <<enumeration>>
        assessment
        customer_reply
        internal_update
        handoff
        can_report
        rca
        closure
        kb_draft
    }
    class CaseStage {
        <<enumeration>>
        open
        investigating
        awaiting_customer
        awaiting_engineering
        escalated
        pending_closure
    }

    CasePacket --> ProductScope
    CasePacket --> EvidenceItem
    CasePacket --> RequestedOutput
    CasePacket --> CaseStage
```

---

## 4. Output — STF result envelope

```mermaid
classDiagram
    class ResultEnvelope {
        +int schema_version
        +string task_id
        +ResultStatus status
        +string summary
        +string[] next_actions
        +string[] artifacts
        +EvidenceRef[] evidence_refs
        +string? error_class
        +string? recovery_hint
    }
    class ResultStatus {
        <<enumeration>>
        success
        partial
        blocked
        failed
        cancelled
    }
    class EvidenceRef {
        +string ref_id
        +string title
        +SourceType source_type
        +string? url
        +string? internal_ref
        +string retrieved_date
        +string version_applicability
        +PublicationStatus publication_status
        +Visibility visibility
        +string? excerpt
    }
    class SourceType {
        <<enumeration>>
        public_docs
        release_notes
        github_issue
        status_page
        internal_process
        memory_pattern
        supplied_evidence
    }

    ResultEnvelope --> ResultStatus
    ResultEnvelope --> EvidenceRef
    EvidenceRef --> SourceType
```

---

## 5. Memory and local storage layout

```mermaid
flowchart LR
    subgraph SESSION["Session memory (not persisted)"]
        WC[Working context\nredacted excerpts\ntemp analysis]
    end

    subgraph CHECKPOINTS["checkpoints/  (human-approved)"]
        CD["checkpoints/draft/\ncurrent-pass-N.md\n─ staging area"]
        CP["checkpoints/CASE-alias-pass-N.md\n─ promoted after approval"]
        CD -->|operator approves\npromotion| CP
    end

    subgraph MEMORY["memory/  (human-approved, in agent repo)"]
        PAT["patterns/\n<slug>.md\ncandidate→validated→outdated"]
        PREF["preferences.md\nresponse style · signature\ntemplates · handoff fields"]
        OPS["ops/<topic>.md\ninternal process refs\nrouting conditions\nsession-scoped by default"]
        CORR["corrections/<slug>.md\npermanent audit\naccepted corrections"]
    end

    CURATOR[Memory Curator\nsubagent proposes]
    CURATOR -->|proposes candidate| CD
    CURATOR -->|proposes pattern| PAT
    CURATOR -->|proposes pref update| PREF
    CURATOR -->|proposes correction| CORR

    OPERATOR([Operator approves]) -->|per write| CP
    OPERATOR -->|per write| PAT
    OPERATOR -->|per write| PREF
    OPERATOR -->|per write| OPS
    OPERATOR -->|per write| CORR

    COORD[Coordinator] -->|reads\n(not writes)| CP
    COORD -->|reads| PAT
    COORD -->|reads| PREF
    COORD -->|reads| OPS
    COORD -->|writes draft\nonly| CD

    note1["⚠ memory/ is NOT .memory/\n.memory/ = STF project governance\nmemory/ = terraform agent's own repo\n(separate repo, Phase 3)"]

    style CD fill:#fff3cd,stroke:#ffc107
    style note1 fill:#f8d7da,stroke:#dc3545,color:#333
```

---

## 6. Case lifecycle state machine

```mermaid
stateDiagram-v2
    [*] --> IMPORTED : manual import\n(only entry path)

    IMPORTED --> INVESTIGATING : intake complete

    INVESTIGATING --> AWAITING_CUSTOMER : requires customer evidence
    INVESTIGATING --> AWAITING_ENGINEERING : requires Engineering input
    INVESTIGATING --> VALIDATING : evidence consolidated

    AWAITING_CUSTOMER --> INVESTIGATING : evidence received
    AWAITING_ENGINEERING --> INVESTIGATING : evidence received

    VALIDATING --> INVESTIGATING : conflicting sources\n(targeted re-check)
    VALIDATING --> AWAITING_APPROVAL : reviewer approved\nauth action required

    AWAITING_APPROVAL --> RESOLVED : operator approves

    RESOLVED --> CLOSED : checkpoint + memory curation\ncustomer confirms OR closure criteria met

    CLOSED --> [*]

    note right of INVESTIGATING
        7 stop conditions:
        • 3 passes exhausted
        • 2 tool errors
        • sources conflict
        • auth without approval
        • credential in input
        • ownership ambiguous
        • new evidence mid-pass
    end note

    note right of AWAITING_APPROVAL
        10 approval classes:
        external_message · case_update
        severity_change · collaboration_case_creation
        pagerduty_engagement · case_closure
        run_operation · state_operation
        config_change · memory_commit
    end note
```

---

## 7. Approval gate — per-action protocol

```mermaid
sequenceDiagram
    participant C as Coordinator
    participant A as Operator
    participant S as Target System

    C->>A: PRE-ANNOUNCE<br/>action · target · evidence_ref · expected outcome
    A-->>C: explicit confirmation (in-chat)
    C->>C: record authorization<br/>(authorized_by · authorized_at · action · target · rationale)
    C->>S: execute action
    S-->>C: actual outcome
    C->>C: record actual outcome in checkpoint
    C->>A: report outcome (honest — failed ≠ completed)
```

---

## 8. STF schema alignment

```mermaid
flowchart LR
    subgraph SCHEMAS["portable/schemas/"]
        TS[task.schema.json\ntask_id · parent_task_id\ntask_type · intent · input\nacceptance_criteria\nrequested_capabilities · state]
        RS[result.schema.json\nstatus · summary · next_actions\nartifacts · evidence_refs\nerror_class · recovery_hint]
        AS[agent.schema.json\nagent_id · version · description\ninputs_schema · outputs_schema\nrequired_capabilities · optional_capabilities\napproval_classes · eval_refs]
    end

    COORD[terraform-support-coordinator] -->|every sub-agent invocation\ncreates a task| TS
    COORD -->|every agent returns\nthis envelope| RS
    AS -->|describes each\n.agents/*.md contract| COORD

    STATES["task.state → case lifecycle\ndraft → IMPORTED\nrunning → INVESTIGATING\nwaiting_approval → AWAITING APPROVAL\ncompleted → RESOLVED/CLOSED\nfailed → CLOSED (unresolved)\npaused → AWAITING CUSTOMER/ENGINEERING"]

    TS --> STATES
```

---

*Previous: [`00-overview.md`](00-overview.md) | Part of design set — see also [`01-coordinator-contract.md`](01-coordinator-contract.md) and [`04-memory-and-evidence-schemas.md`](04-memory-and-evidence-schemas.md)*
