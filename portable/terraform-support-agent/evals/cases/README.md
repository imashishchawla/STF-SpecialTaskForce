# evals/cases/

Sanitized evaluation cases for the Terraform Support Agent Phase 3 pilot.

## Pilot requirement

- Minimum **3 cases** before Phase 3 deployment
- Minimum **10 cases** (full scenario matrix) before Phase 4

## Case index

| ID | Scenario | Status | What it tests |
|---|---|---|---|
| [E01](E01-happy-path.md) | Happy path — complete evidence, confirmed fix | ✅ Ready | Correct next action, source citation, no unnecessary questions |
| [E02](E02-missing-evidence.md) | Missing log evidence | ✅ Ready | Intake asks only for what changes the diagnostic step |
| [E03](E03-conflicting-sources.md) | Conflicting sources | ✅ Ready | Coordinator resolves without majority vote; version-specific source preferred |
| [E04](E04-wrong-product-routing.md) | Wrong product routing (TF vs Azure DevOps) | ✅ Ready | Scope classifier catches ownership; no run logs requested |
| [E05](E05-provider-version-mismatch.md) | Provider version mismatch | ✅ Ready | Source researcher finds version-specific fix with changelog URL |
| [E06](E06-unresolved-engineering.md) | Unresolved Engineering investigation | ✅ Ready | Internal update vs customer reply correctly separated |
| [E07](E07-unavailable-tool.md) | Unavailable tool | ✅ Ready | Manual path provided; no hallucinated lookup; no dead stop |
| [E08](E08-secret-in-input.md) | Secret-bearing input | ✅ Ready | Intake detects; halts; redacted version confirmed before proceeding |
| [E09](E09-stale-memory-pattern.md) | Stale memory pattern | ✅ Ready | Pattern used as lead only; staleness flagged; current source consulted |
| [E10](E10-unsafe-action.md) | Unsafe action request | ✅ Ready | Returns `status: blocked` + correct `approval_class` |
| [E11](E11-live-call-screen-capture.md) | Live call — screen capture redaction gate | ✅ Ready | Redaction gate strips customer IDs before evidence enters case packet |
| E12 | Registry routing (paying customer, Sev 3) | 📋 Phase 5 | `registry-routing` skill triggered |
| E13 | Registry routing (Free Tier customer) | 📋 Phase 5 | Email routing returned |
| E14 | Closure without ticket number | 📋 Phase 5 | Closure blocked until real ticket number supplied |
| E15 | Re-evaluation after new Engineering evidence | 📋 Phase 5 | Re-evaluation of affected conclusions only |
| E16 | Duplicate memory pattern detection | 📋 Phase 5 | Curator proposes update, not new entry |

## Case file format

Each case file contains:
- YAML front matter (`eval_id`, `scenario`, `phase`, `status`, `created`)
- Input section: sanitized case packet the coordinator receives
- Expected output section: key assertions that must be present
- Acceptance criteria table
- Evaluator notes

## Running a case

1. Copy the case's Input section into a new Bob session
2. Invoke the coordinator with that input
3. Check each acceptance criterion against the actual output
4. Record: `pass | fail | partial` per criterion
5. Note any failures with the actual output for review

## No live customer data

All case files use synthesized or sanitized inputs. Real customer data must never be added here.
