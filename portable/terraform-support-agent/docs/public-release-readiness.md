# Public Bob preview: uploaded and verified

Uploaded and verified 2026-10-21. Supersedes the earlier review's statement that no package
was produced; the broader development installer remains unchanged in scope.

## Exact proposed publication

- Repository: https://github.com/imashishchawla/terraform-support-agent
- Issues: https://github.com/imashishchawla/terraform-support-agent/issues
- New issue: https://github.com/imashishchawla/terraform-support-agent/issues/new/choose
- Last API check: private repository, Issues already enabled, Apache-2.0 license.
- Version/profile: `0.1.0-preview.2`, synthetic-case Bob IDE preview.
- Upload only the contents of `release-output/terraform-support-agent-0.1.0-preview.2/`.
- Archive: `release-output/terraform-support-agent-0.1.0-preview.2.tar.gz`.
- Archive SHA-256: `d5dc0bee52bf22de94ea280d5d707845e26ed9500816e105df07884f02c7d5c1`.

Do not upload the STF checkout, `.git`, previous development history, private
memory, or older staging directories. Do not use `git add -A` in STF as a way to
publish the standalone repository. `.gitignore` does not untrack old files.

## Keep / exclude inventory

| Category | Treatment |
|---|---|
| Five core skills | Include intake, diagnosis, source-check, reproduction, communication. Public transformations remove unavailable design pointers and personal onboarding requirements. Canonical STF skills remain unchanged. |
| Six role files | Include as sequential review instructions, not live subagent presets. |
| Templates | Include eight placeholder-based draft templates and a blank preferences example. Omit internal registry routing. |
| Runtime memory | Ignore all `memory/**`, preferences, case-derived patterns/corrections/ops, checkpoints, output. Never copy existing entries. |
| Secrets and runtime storage | Ignore `.env*`, vault, audit, metrics, messages, traces/history, SQLite/sidecars, logs/PIDs, manifests. Never copy existing contents. |
| Generated/temporary files | Ignore Bob skills/mode output, caches, virtual environments, archives, signatures, build output. |
| Development/private components | Exclude A2A/internal submodule, MCP, screen capture, internal routing, archives/PDFs, old plans/designs and evaluation history. Public ignore rules also block their common paths. |
| Public project support | Include README, AGENTS, SECURITY, license copied verbatim from destination, issue templates, installer, tests, public links, integrity manifest. |

Development source, design documents and tests remain maintainable in STF;
omitting them from this distribution does not require deleting or ignoring the
canonical development source. The release uses an explicit file allowlist.

## Installer behavior and Bob setup

Public `install.py` uses only Python's standard library and the local workspace.
No Bob CLI, network, home-directory writes, credentials, or dependency downloads
are needed. Default workspace mode is restricted to `read` and `skill` groups.

1. Open the clean release folder in Bob.
2. Preview `python3 install.py --dry-run`.
3. On the tester's explicit install action, `python3 install.py` creates five
   `.bob/skills/terraform-*/SKILL.md` files, `.bob/custom_modes.yaml`,
   `.install-manifest.json`, and blank `memory/preferences.md` if absent.
4. Existing preferences are preserved; differing existing definitions and
   symlink targets fail before installation writes. Existing global Bob
   definitions are untouched. Generated files have mode 0600 and new directories
   mode 0700; existing directories are not silently re-permissioned.
5. Reload Bob, select Terraform Support Preview, inspect Settings > Skills,
   then try a synthetic case. No automated onboarding or case persistence occurs.

Configuration is based on IBM documentation checked during this review:

- https://bob.ibm.com/docs/ide/features/skills
- https://bob.ibm.com/docs/ide/configuration/custom-modes

## Evidence

- Twelve release tests passed against the extracted final archive: integrity,
  detected personal identity/runtime exclusions, ignore rules, no-write dry-run,
  isolated install/reinstall and preference preservation, conflicting mode
  refusal, symlink refusal, and tampered skill refusal.
- Four development install/privacy tests passed after these changes.
- Ruby YAML parser validated role/skill front matter and issue configuration;
  generated mode parsed with exactly `read` and `skill` groups.
- Archive verified as exactly 35 allowlisted regular text files. Tar owner/group
  names are empty, numeric ownership/timestamps fixed, with no symlinks, personal
  filesystem paths, Git history, binary documents, runtime state or OS metadata.
- Public-text heuristic scan found no configured operator identity, personal
  path, email address, selected credential literals or internal endpoints.
  The explicitly requested public repository ownership URL remains present.
- Existing nine lifecycle and eighteen offline security checks passed in the
  preceding review. A2A and that security implementation are not in this package.
- `git diff --check` passed. Unrelated root `plan/` was preserved.

No dedicated secret scanner is installed here. The heuristic scan plus explicit
allowlist is bounded evidence, not a guarantee against every possible PII type.
Integrity hashes detect changes; this archive is not cryptographically signed
and hashes alone do not authenticate its publisher.

## Remaining gates

The candidate is prepared for upload review as a synthetic preview, not a
production or real-customer-data release. Manual Bob mode discovery, skill
invocation and a synthetic conversation have not been run. Verify these on
the target Bob version before announcing the preview as tested in the IDE.

The user authorized upload after adding the offline welcome guide. The reviewed
35-file release was uploaded to main without force-updating history:

- Commit: https://github.com/imashishchawla/terraform-support-agent/commit/a98e98ba45a924acab743a25b85a5e4ac910dc37
- Guide source: https://github.com/imashishchawla/terraform-support-agent/blob/main/docs/welcome.html
- All 35 remote blob hashes match the reviewed local release.
- The uploaded commit was downloaded and all twelve release tests passed again.
- Issues remain enabled; repository remains private. No visibility change occurred.
- Initial repository history, including its original author attribution, was preserved.
- No home installation, live MCP connection, or production deployment occurred.

The installer opens the local guide only after success. Dry-run never opens a
browser; --no-open disables opening; browser failure prints a manual fallback
without invalidating the installation. These behaviors were tested with mocks.
HTML offline content, internal anchors, source exclusions and integrity passed
automated checks. Native Safari visual verification could not be completed;
no claim of completed visual or Bob IDE acceptance testing is made.

## Rebuild

From STF root, choose a new non-existing output directory:

```sh
python3 -B portable/terraform-support-agent/export/scripts/build-public-release.py \
  --output portable/terraform-support-agent/release-output/review-next
```

This builds a clean tree, archive, and checksum. Any material source change
requires running its release tests and reviewing the new exact artifact/hash
before approving publication. The builder does not read secrets or vault files.
