---
skill_id: terraform-reproduction
version: "0.1.0-draft"
status: draft
source: portable/terraform-support-agent/export/skills/reproduction.md
canonical: true
bob_generated: false
phase: 3
approval_class: reproduction_execution
---

# Skill: reproduction
> **Status**: Draft skeleton — not yet validated or active.
> Full specification: `docs/design/03-skills-and-templates.md §6`

## Purpose
Prepare a minimal isolated reproduction example — **plan only**. Execution is always a manual step requiring separate explicit approval.

## Trigger conditions (ALL must be met before invoking)
1. Coordinator has validated that remote environment access is insufficient to confirm the cause
2. A reproducible setup exists (no production state, no customer credentials, no live org)
3. the operator has **explicitly approved** the reproduction scope

## Steps (condensed)
1. Derive minimal configuration from redacted case evidence — strip to smallest HCL that reproduces the reported behavior; replace all customer-specific values with generic placeholders
2. State: expected behavior (what should happen)
3. State: observed behavior (what the reported issue produces)
4. List: prerequisites (Terraform version, provider version, backend type)
5. List: safe setup steps
6. List: rollback or cleanup steps
7. List: validation checks (how to confirm the issue is reproduced vs not)
8. Output: self-contained Markdown file for the operator's review and optional execution

## What this skill must NOT do
- Execute `terraform init`, `terraform validate`, `terraform plan`, or any Terraform CLI command directly (even read-only operations can download providers, contact backends, or expose sensitive output)
- Contact any customer backend, cloud account, or HCP Terraform organization
- Use customer tokens, credentials, or state

## Execution gate
Execution requires a separate explicit approval (`approval_class: reproduction_execution`) specifying the isolated environment. This skill produces the **plan only**.
