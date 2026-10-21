# Terraform Support Agent for IBM Bob

Public preview for synthetic-case testing in the IBM Bob IDE. This is an
instruction bundle, not an autonomous Terraform service or official IBM product.
It helps classify issues, evaluate supplied evidence, plan a reproduction, and
draft replies. The operator reviews every output.

Project: https://github.com/imashishchawla/terraform-support-agent

Report a problem: https://github.com/imashishchawla/terraform-support-agent/issues/new/choose

## Install in this workspace

Install IBM Bob separately. Clone or extract this reviewed release, open that
folder in Bob, and run the following in its terminal (Python 3.9+ required):

```sh
python3 install.py --dry-run
python3 install.py
```

The installer makes no network requests and writes only inside this workspace.
It creates five `.bob/skills/terraform-*/SKILL.md` files,
`.bob/custom_modes.yaml`, blank private `memory/preferences.md`, and a local
`.install-manifest.json`. It preserves existing preferences and refuses to
overwrite a different existing Bob configuration. Inspect that conflict manually.
Re-running installation with identical definitions is safe.

After a successful installation, your browser opens the offline
[welcome and operating guide](docs/welcome.html). It covers setup, skills,
privacy, troubleshooting, testing, and issue reporting. Use `python3 install.py
--no-open` on headless systems or open the HTML file manually at any time.
Dry-run never opens a browser. If browser launch fails, installation remains
successful and the installer prints the manual-open instruction.

Reload the Bob window. Select **Terraform Support Preview** in the mode picker.
In **Settings > Skills**, confirm all five Terraform skills are listed. Project
skills and project modes follow [IBM Bob's documented skill locations](https://bob.ibm.com/docs/ide/features/skills)
and [custom mode configuration](https://bob.ibm.com/docs/ide/configuration/custom-modes).
Actual discovery must be checked on your Bob version; a file-copy test is not
proof that the IDE has loaded the mode.

Try: "Use terraform-intake for this synthetic report: a Terraform run fails
after a provider version upgrade. Ask only for evidence needed to diagnose it."

The preview mode grants read and skill tools only. It runs the coordinator and
review steps sequentially in one conversation, without subagent spawning,
terminal execution, edits, MCP connections, telemetry, or background services.
Research is manual: supply a public source excerpt or URL; the agent must say
when a claim has not been retrieved and verified. No credentials are needed.

## Privacy and local files

Use synthetic or independently redacted input only. Remove names, email
addresses, company identifiers, account/workspace/run IDs, tokens, state, and
sensitive log content **before sending input to Bob**. Skill instructions cannot
redact data before the IDE/model has already received it. This preview does not
include an encrypted vault or an automatic PII protection service.

Preferences start empty. You may edit them locally for signatures; all values
are optional and unfilled values stay as placeholders. Runtime memory,
checkpoints, output, credentials, and manifests are ignored. Do not commit or
upload them. No actual customer cases should be used in this preview.

Included: five canonical skills (intake, diagnosis, source-check, reproduction,
communication), supporting role instructions, neutral templates, public source
links, installer, integrity manifest, license, tests, and issue templates.
Excluded: operator identity, case-derived memory, internal routing processes,
archives, A2A/internal dependencies, MCP and screen capture. Never upload the STF
development checkout as a substitute for this curated release.

## Report an issue

Use the project Issues link above for bugs and improvements. Include Bob and OS
versions, the release version, synthetic reproduction steps, and expected versus
actual behavior. Never attach customer cases, identities, credentials, raw logs,
screenshots with private information, `.env`, local preferences, or vault files.
For a suspected security exposure, follow SECURITY.md instead of a public issue.

## Verify

```sh
python3 -B -m unittest discover -s tests -v
python3 install.py --dry-run
```

Version: `0.1.0-preview.2`. Automated checks establish integrity and isolated
installation behavior. They do not establish model accuracy or completion of
manual Bob acceptance testing. Keep this preview limited to synthetic input
until those acceptance checks pass.
