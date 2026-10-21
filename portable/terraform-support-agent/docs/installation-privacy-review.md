# Installation and privacy review for IBM employee testing

Reviewed 2026-10-21. Local edits only; no upload, home installation, live MCP,
A2A startup, or customer input. Repository status before this work included an
untracked root `plan/` directory, which was left untouched.

## File creation: current implementation

Paths below are relative to the agent unless explicitly prefixed with `~`.

| Action / time | Created or overwritten | Purpose / handling |
|---|---|---|
| Agent `installer.sh install` or `reinstall` | `memory/preferences.md`, only when absent | Copy blank `export/templates/preferences.example.md`; mode 0600; never replace existing answers. Dry-run only prints the action. |
| Agent install / reinstall / modify | Seven `~/.bob/skills/terraform-<slug>/SKILL.md` files | Slugs: communication, diagnosis, intake, registry-routing, reproduction, screen-capture, source-check. Generator writes Bob metadata and canonical skill bodies. Source provenance is now relative. These files are outside repository ignore scope. |
| Agent install / reinstall | `~/.bob/modes/terraform-support.yaml` | Copy `export/agents/bob-mode-terraform-support.yaml`; outside repository. |
| Agent install / reinstall | `.install-manifest` | Timestamp, absolute agent root, version, mode directory, optional host/A2A metadata; local only. This is installation metadata, not a complete per-file ownership inventory. |
| Root `install.sh` live host-copy path | `.install-manifest.txt` | Host, skill, and absolute target paths; local only. |
| Root live host-copy path | `~/.bob/skills/<slug>/SKILL.md` or corresponding selected host paths | Copies seven source files under unprefixed slugs. Bob then invokes adapter generator, producing seven additional prefixed copies. This differs from the agent installer. |
| Onboarding, only after save confirmation | `.env`, `memory/preferences.md` | Personal answers, path, style samples, optional imported prompt; existing files overwritten. Both now use mode 0600. Installer does not automatically collect these answers. |
| Optional A2A setup | `a2a/.venv/**` | Python environment and dependencies; requires separately supplied `a2a/.env`. Setup does not create that credentials file. Not exercised in this review. |
| Optional A2A start | `a2a/a2a-server.log`, `a2a/.a2a.pid` | Local process output and PID; not created by core Bob install. Not exercised. |
| First `SessionVault` construction / redaction | `vault/`, `vault/.key`, then `vault/<session-id>.jsonl` when values are stored | Created by security code, not core installer. Excluded from sharing. Existing local vault contents were not read. |
| Case workflow, after actual case work | `checkpoints/**`, operational memory changes | Case checkpoints are local. Memory changes still require human review. Core install does not create customer cases. |
| Evaluation runner | `evals/results/session-<date>.md`, or chosen `--output` | Generated reports; ignored by default. `--dry-run` on this runner still writes a report. |
| Explicit package command | `terraform-support-agent-<version>-<timestamp>.tar.gz`, `.sig`, `.sha256` in chosen output directory | Default `/tmp`; release filenames are ignored if placed under agent. Not produced in this review. |

Other root installer host locations are `~/.agents/skills`,
`~/.gemini/config/skills`, `~/.config/opencode/skills`, and `~/.claude/skills`.
There is no proven uniform runtime discovery across those hosts in this review.

`audit/`, `metrics/`, `messages/`, and `stf.db` are documented runtime storage,
not files proven to be created by core installation. Their directories and
SQLite sidecars are ignored. `.bob/skills/`, Python caches and build output,
credentials, A2A logs/PID/venv were already covered; missing manifest variants,
preferences, broader checkpoints, evaluation output and release output were added.

## Required installation structure for the testing release

1. Distribute a reviewed source snapshot with blank preferences template only;
   omit the existing personal preferences and all runtime state. Use a fresh
   release history if old history contains private data.
2. Use one documented installer entry point: the agent-local installer for the
   initial Bob test cohort. Reconcile the root installer's duplicate naming and
   standalone repository layout before advertising it for this release.
3. Preview from the local clone with `bash installer.sh install --dry-run`.
   Confirm no home writes; select `skip` for A2A. Never use remote bootstrap as
   proof of a network-free dry-run.
4. After exact-version approval, core installation creates only the blank local
   preferences (if absent), Bob definitions, and manifest. It must preserve prior
   operator answers. The directory should remain writable by that tester only;
   the current installer does not enforce directory ownership or 0700 on the
   entire clone.
5. Run onboarding separately, review answers, and save only when accepted. Use
   synthetic style samples and sanitized prompts. `.env` is not interchangeable
   with `a2a/.env`. Do not source user-provided `.env` as shell code.
6. Create encrypted case storage on first case use, not in the distributable.
   Before real cases, verify 0700 directory / 0600 file permissions, encryption,
   retention, and redaction behavior. Current vault code has a non-AES fallback
   and does not enforce all these permissions; this remains a real-data blocker.
7. Start employee testing with synthetic cases only. Keep MCP disabled and A2A
   inactive. Record Bob discovery/invocation and failure behavior on each target
   OS separately before expanding support claims.

## Files with personal identity references still present

All paths in this section are relative to this agent. This is a tracked-text
identity/path search, not a claim of exhaustive PII detection.

- `memory/preferences.md`: actual operator name, availability, personal path,
  and populated preferences. Now ignored, but STILL TRACKED in Git.
- `AGENTS.md`: named operator.
- `installer.sh`: author name and personal GitHub link in branding.
- `README.md`: owner-identifying GitHub installation URL.
- `export/agents/bob-mode-terraform-support.yaml`: named operator's workflow.
- `docs/design/04-memory-and-evidence-schemas.md`: named correction author.
- `docs/design/05-runtime-and-integration.md`: named authorization example.
- `docs/design/07-implementation-plan.md`: named onboarding completion record.
- `evals/cases/E11-live-call-screen-capture.md`: named operator in scenario.
- `memory/corrections/C001-yaml-comment-inference.md`: actual name in example
  and explanation of a prior error.
- `plan/portability-readiness-plan.md`: author name and attribution requirements.
- `plan/archive/ibm-bob-terraform-agent-design-prompt.txt`: personal references.
- `plan/archive/terraform-support-agent-plan.md`: personal workflow/name/signature.

Public attribution and repository ownership identify a person too. If the
requirement is literally no personal identity in distributed content, decide
the permitted ownership/attribution treatment before release; retain legally
required notices. No existing attribution was removed in this review.

## Other sensitive or review-required material

- `.env`, `a2a/.env` if present, and `vault/**`: local secret/PII containers;
  contents deliberately not inspected. Never upload, even if encrypted.
- `memory/ops/{entitlement-checks,registry-routing,escalation-paths}.md`,
  `export/skills/registry-routing.md`,
  `export/templates/registry-routing-internal.md`, and
  `docs/design/{03-skills-and-templates,06-registry-routing}.md`: internal
  processes and/or role mailboxes. Mailbox matches are not proof of individual
  PII; review audience and confidentiality before sharing.
- `plan/archive/01-TCPR-Terraform-Public-Registry_-Case-Handling-in-CSP-270426-034252.pdf`:
  archived internal input; PDF content and metadata have not been cleared.
- `a2a/tests/security/test_redactor.py`: email/credential-shaped synthetic
  fixtures; distinguish them from real secrets during scan review.
- `a2a/lib/aicoe-agent-utils`: internal IBM submodule. Verify employee access,
  license, approved distribution and dependency installation before enabling.
- Tracked patterns, corrections, existing evaluation reports, and all Git history:
  require content review; ignore rules alone do not sanitize or untrack them.

## Validation and release blockers

Passed locally:

- Four new privacy/install tests: seven adapters generated in a temporary target,
  relative provenance, clean-fixture dry-run with no file changes, ignore-rule
  coverage and blank template assertions.
- Nine existing installer lifecycle checks. These primarily exercise dry-runs
  and output, not a complete real installation or enforced home-write isolation.
- Eighteen security unit tests using copied source and temporary synthetic vaults.
- Root Bob install dry-run, shell syntax and `git diff --check`.

No real home installation, Bob UI discovery, model invocation, live server,
network dependency installation, package signature exercise, full-history secret
scan or binary metadata scan was performed. Existing evaluation runner results
are not behavioral proof: it counts parsed assertions and does not execute agent
answers against them.

Remaining implementation concerns found during inspection:

- Root remote bootstrap clones before flag parsing, including `--dry-run`.
- Core installer writes a manifest before optional A2A success; reinstall reads
  previous A2A inclusion after rewriting that manifest.
- Package includes operational memory and named documents. It excludes the
  internal library while including A2A code. Signing is not privacy clearance.
- Onboarding accepts raw style samples/imported prompts and interpolates answers
  into shell/YAML formats without robust escaping. Synthetic-only input is
  required until this is hardened and tested.
- Vault's custom fallback cannot substantiate the AES-256-GCM promise.
- README status sections conflict; supported installation/version claims need
  reconciliation before distribution.

Release decision: NOT YET CLEARED for upload or employee distribution. First
prepare the curated snapshot, resolve the above for the advertised scope, scan
the exact release including metadata/history, then obtain publishing approval
under `docs/security.md`. No Git index or history was changed by this review.
