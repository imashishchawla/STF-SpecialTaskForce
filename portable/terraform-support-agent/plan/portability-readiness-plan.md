# Terraform Support Agent portability readiness plan

**Status:** Agreed scope updated 2026-10-09: repair onboarding; offer A2A as an optional installer component; use one script for install, modify, start/stop, and removal; implement a security module; update the README set. This plan authorizes no installation, connector activation, credential use, or live case processing.

## Decision and intended product

Keep two explicit delivery modes from one reviewed source bundle:

1. **Core host guidance:** selected skills, agent instructions, templates, and onboarding for an operator in a supported host. This works without A2A and claims guidance only.
2. **Optional A2A component:** the same agent can expose its coordinator to other agents through a local A2A service. `installer.sh` must ask whether to add A2A; only a selected, successfully validated A2A component is started. A2A can later be added or removed through the same script without losing core guidance or operator settings.

The first portability target is a clean clone on a second macOS or Linux account. Windows needs its own installer/adapter validation before it is advertised. “Any system” means a declared compatibility matrix and per-destination checks, not one shell script presumed to work everywhere. Phase 4 MCP and live data remain outside this remediation.

## 1. Stop misleading installation paths

| Target | Change | Why / acceptance |
|---|---|---|
| Root `install.sh` | During Phase 3b, make the executable path preview-only or otherwise prevent host writes; remove `--yes` as a shortcut to unreviewed installation. Later, expose its host-adapter functions safely to the agent-local installer or retire duplicate copy logic. | Current script overwrites host `SKILL.md` files and truncates a manifest. A dry run must leave the repo and home unchanged. |
| `portable/terraform-support-agent/installer.sh` (create) | Make this the single Terraform-agent entry point for `install`, `modify`, `start`, `stop`, `status`, and `remove`, plus `--dry-run`. It invokes repaired onboarding and approved adapter-generation routines as needed. A2A is an explicit optional component. | One script must manage the complete lifecycle without silently overwriting host skills or touching unrelated installations. |
| `portable/bundle.yaml` | Retain as a clearly labelled draft template; create a separate agent-specific release manifest only when the export set, version, license, hashes, and compatibility are known. | Current template has no agents/files and is not an installable release. |
| README files listed in section 6 | Correct structure, phase, commands, and ownership after behavior is fixed. | Instructions must match what the scripts actually do. |

Do not invoke the existing live install path to validate these changes. Use temporary destinations and a clean checkout.

### Agent-local `installer.sh` commands and sequence

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
| `a2a/Dockerfile` | Remove it from the active scaffold and its setup instructions after reviewing its Git history. Do not create `.dockerignore`. Reintroduce container packaging only for a separately approved deployment target. | Docker is unnecessary for a local Python virtual environment and currently contains an invalid `COPY ../export/...` path. It must not block installation on systems without Docker. |
| `a2a/.env.example`, agent `.gitignore` | Track the example with an explicit ignore exception; continue ignoring real `.env` files. | The template is currently ignored and absent from a clone. |
| `a2a/README.md` (create) | Document the optional component, supported providers, direct developer startup, endpoint, smoke test, shutdown, and installer commands. | The current agent README has no usable A2A runbook. |
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

Review **every existing repository README** against the final structure and commands: root `README.md`; `builder/README.md`; `evals/README.md`; `harness/README.md`, `harness/evals/README.md`, `harness/policies/README.md`; `portable/README.md`, `portable/adapters/README.md`, `portable/schemas/README.md`; and every README under `portable/terraform-support-agent/` (`README.md`, `checkpoints/README.md`, `checkpoints/draft/README.md`, `config/README.md`, `evals/cases/README.md`, `export/templates/README.md`, `memory/README.md`, `memory/corrections/README.md`, `memory/ops/README.md`, `memory/patterns/README.md`). Update each description, diagram, path, phase, or command that is inaccurate; leave unrelated content intact. Create `a2a/README.md` and `a2a/security/README.md`. Check every listed command and relative link against the final tree. The agent README must show `installer.sh install`, `modify`, `start`, `stop`, `status`, and `remove`, including the optional A2A choice.

Sync `portable/terraform-support-agent/docs/design/05-runtime-and-integration.md` and `07-implementation-plan.md` to their root `docs/design/` mirrors after updating the authoritative portable copies. Correct completed checkboxes that only indicate files exist: A2A startup, streaming, and portable install remain unverified; remove Docker as a Phase 3b acceptance condition. Move `export/agents/specialists.md.archived` to `plan/archive/` if it is still needed for history; otherwise remove it in a reviewed cleanup. Keep the PDF and original prompt in `plan/` as design references, outside the release.

## Completion gates

1. **Source integrity:** clean clone contains `.env.example` and every declared core asset; the optional A2A dependency is pinned and available when selected; no secret or local case state is packaged.
2. **Installer lifecycle:** every command has a no-write dry run. A core-only install succeeds without Python packages or Docker. A selected A2A install runs onboarding once, passes security checks, starts locally, and answers an authorized request. `modify` can add or remove A2A; `remove` leaves unrelated files and private data intact.
3. **Safety:** the security module blocks or tokenizes sensitive input before model use; unauthenticated non-loopback startup fails; MCP and side-effect paths stay disabled.
4. **Portability:** core guidance installs under a temporary account on each declared target OS and rolls back. Optional A2A installation is tested separately on each OS with its declared prerequisites. The guidance release is discovered by two selected host adapters.
5. **Documentation and pilot:** every existing README is checked against the tree, commands, and supported states; E01–E10 results and failures are recorded. The operator reviews the exact release, permissions, destination, and recovery procedure before any shared home installation or activation.

## Explicitly deferred

Docker/container deployment, live MCP, Jira/CSP access, customer data, screen capture, specialist spawning, encrypted trace service, Windows support, and shared home promotion remain in their later approved phases. This plan does not treat an A2A server as a replacement for the STF harness or host adapters.
