# Terraform Support Agent portability readiness plan

**Status:** Active remediation plan, updated 2026-10-09. P0 complete (consolidation commit `aafbf67`). P1 installer rewrite complete (commit `6338fd0`). P2 A2A security module is next. This plan authorizes no home installation, connector activation, credential use, or live case processing.

## Priority order

| Priority | Outcome | Status | Required proof |
|---|---|---|---|
| P0 — ownership and safety | Keep one Terraform-specific copy under this agent; archive completed inputs; repair stale paths. Preserve the STF-wide `plan.md`, schemas, and generic installer at root. | ✅ **Complete** (`aafbf67`) | Done: root `docs/design/` mirror retired; three archived inputs moved to `plan/archive/`; 15+ READMEs updated. |
| P1 — installer lifecycle | Add installed-state detection and a single menu/command interface for install, re-install, modify/update, package, removal, Propel, and repository updates. | ✅ **Complete** (`6338fd0`) | `installer.sh` rewritten (1248 lines): `dry_exec()` (no eval), validated `--host`, 8-choice menu, subcommands `reinstall`/`package`/`update`, flags `--json`/`--purge`/`--no-start`, ASCII banner + branding, GPG signing for `package`/`update`. Syntax verified (`bash -n`). End-to-end lifecycle test pending until clean target account is available (P4). |
| P2 — security and release authenticity | Implement the dedicated A2A security module and signed release/installer verification with operator-owned signing authority. | ✅ **Complete** | Dedicated A2A security package implemented (`vault.py`, `redactor.py`, `wire_validator.py`, `bind_guard.py`); 18 unit tests passing in `a2a/tests/security/`. GPG signing integrated in `installer.sh`. |
| P3 — experience and distribution | Add the CLI Terraform visual, tagline, author credit, and Bob chat choice flow; keep A2A optional. | ✅ **Merged into P1** | ASCII banner ("Making Terraform Support Simple", "Created by Ashish Chawla", GitHub URL) ships in the P1 rewrite. Bob chat `--json` mode delivers structured choices via same code path. |
| P4 — documentation and pilot | Update affected READMEs, design links, and evaluation records; test on declared target systems. | 🔄 In progress | README.md and AGENTS.md updated for P1. Full 20-README audit and E01–E10 eval recording remain open. |

## Decision and intended product

Keep two explicit delivery modes from one reviewed source bundle:

1. **Core host guidance:** selected skills, agent instructions, templates, and onboarding for an operator in a supported host. This works without A2A and claims guidance only.
2. **Optional A2A component:** the same agent can expose its coordinator to other agents through a local A2A service. `installer.sh` must ask whether to add A2A; only a selected, successfully validated A2A component is started. A2A can later be added or removed through the same script without losing core guidance or operator settings.

The first portability target is a clean clone on a second macOS or Linux account. Windows needs its own installer/adapter validation before it is advertised. “Any system” means a declared compatibility matrix and per-destination checks, not one shell script presumed to work everywhere. Phase 4 MCP and live data remain outside this remediation.

## File ownership and archive decision

The canonical Terraform design documents and dashboard belong in `docs/` inside this agent. The approved original agent plan, source prompt, and interim Public Registry PDF are completed planning inputs and belong in `plan/archive/`; the active plan is this file. Root copies of those Terraform-only files are redundant after content comparison and reference repair. The root `plan.md` remains STF-wide architecture and history, `portable/schemas/` remains shared contracts, and root `install.sh` remains generic host-installation code. A Terraform-specific file found elsewhere later must be classified as runtime input, active plan, historical source, or shared STF material before moving it.

## 1. Stop misleading installation paths

| Target | Change | Why / acceptance |
|---|---|---|
| Root `install.sh` | During Phase 3b, make the executable path preview-only or otherwise prevent host writes; remove `--yes` as a shortcut to unreviewed installation. Later, expose its host-adapter functions safely to the agent-local installer or retire duplicate copy logic. | Current script overwrites host `SKILL.md` files and truncates a manifest. A dry run must leave the repo and home unchanged. |
| `portable/terraform-support-agent/installer.sh` (exists; revise) | Make this the single Terraform-agent entry point for the menu and subcommands below. It invokes repaired onboarding and approved adapter-generation routines as needed. A2A is an explicit optional component. | One script must manage the complete lifecycle without silently overwriting host skills or touching unrelated installations. |
| `portable/bundle.yaml` | Retain as a clearly labelled draft template; create a separate agent-specific release manifest only when the export set, version, license, hashes, and compatibility are known. | Current template has no agents/files and is not an installable release. |
| README files listed in section 6 | Correct structure, phase, commands, and ownership after behavior is fixed. | Instructions must match what the scripts actually do. |

Do not invoke the existing live install path to validate these changes. Use temporary destinations and a clean checkout.

### Agent-local `installer.sh` commands and sequence

When an installation is detected, show interactive **choice buttons** in Bob and the equivalent numbered CLI menu: **Re-install**, **Install / Update**, **Package**, **Remove Installer**, **Install / Update Propel**, **Update from Repo**, plus **Status** and **Cancel**. On a new system, show **Install**, **Package**, **Status**, and **Cancel**. A noninteractive invocation uses the same named actions and `--json` output for Bob; it must never infer a destructive choice from missing input. “Remove Installer” means remove the installed agent, its owned adapters, and its installed launcher after a path preview; it does not delete this source-repository script. Preserve operator data unless a separately confirmed purge is selected.

The current script needs a safety rewrite before adding menu choices: `install --a2a` currently copies Bob skills without preparing A2A, `--host` is accepted but has no effect, and the `dry()` helper uses `eval`. Replace command-string evaluation with explicit argument arrays/functions, validate every flag, and make status messages reflect completed actions. Do not run the live installer as a substitute for these checks.

- **Re-install:** reinstall the same verified version, repair only manifest-owned files, and retain settings and unrelated host files.
- **Install / Update:** select a reviewed local version; stage and verify it, show the diff and rollback target, then atomically activate it. `modify` remains the command for scoped settings, host, or optional A2A changes.
- **Package:** create a portable release archive containing only approved agent assets, dependency metadata, manifest, hashes, and signature; exclude `.env`, populated preferences, checkpoints, vault, traces, and internal raw case data. Output to an operator-selected destination, not an ignored runtime directory in this repository.
- **Install / Update Propel:** discover the installed Bob/Propel version, display exact connection changes and permissions, and run only after operator approval and the applicable connector phase gate. A skip reports degraded capability without breaking core install.
- **Update from Repo:** check a configured trusted Git remote for a newer signed release, report current and candidate versions and changed files, and require an explicit selection before fetching/installing. Never execute unreviewed code from a moving branch or use `git reset --hard`/`git clean -fd`.

On CLI startup display an accessible ASCII Terraform-themed mark, the tagline **“Making Terraform Support Simple”**, and **“Created by Ashish Chawla”**. Add my Github link as hyperlink, Do not rely on terminal color or Unicode for meaning. In Bob chat, present the same branding and structured choices, then call the same installer actions rather than a separate code path. Review Terraform logo/brand usage before packaging official artwork; an ASCII mark works offline, making sure it contains exact design and colours.

An executable local shell file cannot be encrypted and still run everywhere without distributing a decryption key; anyone who controls their local copy can edit it. To make an Ashish-authored release verifiable, restrict source-repository write access, sign versioned packages with a private signing key controlled by Ashish, publish the verification key, and make installation/updates reject missing or invalid signatures. Encrypt distributed packages or configuration at rest only if a key-delivery design is approved. Signing proves origin and detects edits; it does not prevent a recipient from editing an independent copy.

1. **Preflight and preview:** detect supported OS and architecture, Bash, and required local files. Check the target and existing installation without overwriting it. For A2A only, check Python 3.11 and the pinned agent-utils source. Every mutating command accepts `--dry-run`, listing planned writes, dependency sources, network requests, and process actions without changing them.
2. **`install`:** stage and verify a versioned core release, then call the corrected onboarding script. Ask whether to include A2A; the default is to skip it. If selected, create an isolated Python virtual environment and install pinned dependencies after showing the source and receiving authorization. Never modify system Python. After onboarding and security validation succeed, start the selected A2A component in the foreground by default; offer `--no-start` for staged setup. A skipped or cancelled onboarding leaves no active install.
3. **`modify`:** preview a scoped change to host selection, operator settings, version, or the optional A2A component. Reuse verified dependencies; call onboarding only for changed settings. Adding A2A runs its prerequisites and security checks. Removing A2A stops its process and removes only its owned environment; core guidance and local operator data remain.
4. **`start`, `stop`, `status`:** act only on an installed A2A component. Start it locally after provider, port, prompt, dependency, redaction, and auth checks; report endpoint, health, process ownership, and stop command. Propagate shutdown signals and exit codes. `status` distinguishes core-only, A2A stopped, and A2A healthy states.
5. **`remove`:** show exact owned files and host adapters, stop A2A, and remove only the selected agent version and adapters. Preserve operator settings and case data by default; a separately confirmed purge may remove named local state after a backup preview. Never remove unrelated host skills.
6. **Recovery:** failed install or modify leaves the previous version active; an interrupted removal reports what remains. Test rollback and repeat each command to prove it is safe to rerun.

## 2. Repair onboarding and separate local state

| Target | Change | Why / acceptance |
|---|---|---|
| `export/scripts/onboarding.sh` | Resolve the agent root with `../..`; write only to the intended local paths; validate answers before writing; use restrictive permissions and atomic writes for local config. | Current path resolves to `export/`, so the documented quick start cannot finish. An isolated test must show exact output paths and no writes outside a temporary agent copy. |
| `memory/preferences.md` | Keep the committed template blank. Store populated operator preferences in ignored local state or a reviewed private store; never prescribe committing names and availability to a portable release. | Operator details do not belong in a distributable bundle. |
| Onboarding connector prompts | Remove or defer `npx` MCP/Playwright installs and Bob Propel configuration from Phase 3b onboarding. | They cross the current phase boundary and make first-run setup depend on network access and unrelated services. |

## 3. Make the optional A2A service buildable

| Target | Change | Why / acceptance |
|---|---|---|
| `a2a/.gitmodules`, `a2a/lib/` | Replace the nested placeholder with a correctly registered repository-root submodule and tracked gitlink, or use a reviewed package release. Verify the private source, license, commit, and interfaces before choosing. | A fresh clone currently lacks `aicoe-agent-utils`; `git submodule status` reports none. |
| `a2a/requirements.txt` | Pin a tested dependency set, including the exact agent-utils revision; document Python version and private access requirements. | Open lower bounds and a missing editable source cannot reproduce an install. |
| `a2a/Dockerfile` | Already removed from the active scaffold. Keep it absent and do not create `.dockerignore`; reintroduce container packaging only for a separately approved deployment target. | Docker is unnecessary for a local Python virtual environment. |
| `a2a/.env.example`, agent `.gitignore` | The example is now tracked. Keep it free of real credentials and continue ignoring real `.env` files. | A clean clone must contain the template. |
| `a2a/README.md` | Keep its status and commands aligned with observed behavior as the optional component is completed. | It must not describe planned endpoints or security as implemented. |
| `a2a/config.py`, `main.py`, `a2a_factory.py`, `terraform_agent.py` | Check signatures against the pinned dependency, validate provider configuration at startup, and load the reviewed prompt/assets from an explicit path. | Syntax parsing alone does not establish that the framework API or prompt packaging works. |

## 4. Enforce the case-data and network boundary

- Create `a2a/security/` as a dedicated Python package with redaction and local vault handling, inbound message validation, and bind/auth policy. `main.py` and the request handler call it before any LLM or delegation path; startup fails when the module is missing or its configuration is invalid. Add focused tests under `a2a/tests/security/` and document the module in `a2a/security/README.md`.
- Default A2A binding to `127.0.0.1`; require a deliberate deployment configuration, authentication, transport protection, and origin/network policy before remote access. Fail startup when exposure is requested without the required controls.
- Reject or replace sensitive strings before an LLM call according to design doc 08, keep mappings out of model context, and cover the failure path. Do not claim this is implemented merely because the prompt says “redact.”
- Define the bridge between external A2A messages and the repository's `SignedEnvelope` design in doc 09. They are separate formats. Validate identity, message size, TTL, schema, and correlation at the boundary; do not forward raw case payloads to another agent by default.
- Keep MCP disabled. No Terraform command execution, case update, external message, or memory promotion is added in this pass.

## 5. Make installation selective and reversible

- Build a release inventory from `export/agents`, approved `export/skills`, required templates, and declared dependencies. Exclude `docs/design`, `plan`, checkpoints, live memory, `.env`, vault, audit, messages, metrics, and traces.
- Filter by status and phase. Keep the canonical `export/skills/screen-capture.md`, but do not expose its Phase 4 capability in a Phase 3 guidance install.
- Generate host-specific wrappers from canonical files. Do not copy raw skill Markdown and assume discovery or policy enforcement. Validate each selected host's actual discovery, naming, and precedence. The Terraform `installer.sh` owns its adapter install, modify, and removal operations; shared adapter code may be reused from the root installer only after its safety repairs.
- Stage immutable versions under the destination's STF library, verify hashes and schemas, preview exact files and permissions, then require operator review before activation. Preserve the previous active version and test uninstall/rollback. Do not overwrite unrelated host skills.
- State support tiers per host: guidance only, mediated tools, or full observation. The first release may claim guidance only.

## 6. Verify behavior and resolve file drift

Create `a2a/tests/` for offline tests of config validation, prompt loading, redaction rejection, authentication/exposure rules, and A2A request handling with a pinned test dependency. Add isolated lifecycle tests for `installer.sh install|modify|start|stop|status|remove --dry-run`, core-only setup, optional A2A setup, reruns, and scoped removal. Keep `a2a/test_client.py` as a manual smoke client. Add a repeatable runner and a result template under `evals/`; record outcomes for E01–E10 before pilot acceptance. E11 remains Phase 4 because screen capture depends on Playwright MCP.

Review **every existing repository README** against the final structure and commands: root `README.md`; `builder/README.md`; `evals/README.md`; `harness/README.md`, `harness/evals/README.md`, `harness/policies/README.md`; `portable/README.md`, `portable/adapters/README.md`, `portable/schemas/README.md`; and every README under `portable/terraform-support-agent/` (`README.md`, `a2a/README.md`, `a2a/security/README.md`, `checkpoints/README.md`, `checkpoints/draft/README.md`, `config/README.md`, `evals/cases/README.md`, `export/templates/README.md`, `memory/README.md`, `memory/corrections/README.md`, `memory/ops/README.md`, `memory/patterns/README.md`). Update each description, diagram, path, phase, or command that is inaccurate; leave unrelated content intact. Check every listed command and relative link against the final tree. The agent README must explain the archive, dashboard, all installer choices, optional A2A, and the distinction between signing and encryption.

The root `docs/design/` mirror is retired; update STF navigation to the canonical agent copy. Correct completed checkboxes that only indicate files exist: A2A startup, streaming, and portable install remain unverified; remove Docker as a Phase 3b acceptance condition. Keep the already archived specialist history and the completed original plan, PDF, and design prompt in `plan/archive/`, outside the release. Update source references to those archive paths. The root copies were identical to the agent copies except that the agent's original plan and design 05 contained additional material; those fuller copies were retained.

## Completion gates

1. **Source integrity:** clean clone contains `.env.example` and every declared core asset; the optional A2A dependency is pinned and available when selected; no secret or local case state is packaged.
2. **Installer lifecycle:** every command has a no-write dry run. A core-only install succeeds without Python packages or Docker. A selected A2A install runs onboarding once, passes security checks, starts locally, and answers an authorized request. `modify` can add or remove A2A; `remove` leaves unrelated files and private data intact.
3. **Safety:** the security module blocks or tokenizes sensitive input before model use; unauthenticated non-loopback startup fails; MCP and side-effect paths stay disabled.
4. **Portability:** core guidance installs under a temporary account on each declared target OS and rolls back. Optional A2A installation is tested separately on each OS with its declared prerequisites. The guidance release is discovered by two selected host adapters.
5. **Documentation and pilot:** every existing README is checked against the tree, commands, and supported states; E01–E10 results and failures are recorded. The operator reviews the exact release, permissions, destination, and recovery procedure before any shared home installation or activation.

## Explicitly deferred

Docker/container deployment, live MCP, Jira/CSP access, customer data, screen capture, specialist spawning, encrypted trace service, Windows support, and shared home promotion remain in their later approved phases. This plan does not treat an A2A server as a replacement for the STF harness or host adapters.
