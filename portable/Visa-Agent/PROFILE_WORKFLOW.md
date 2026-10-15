# Client profiles

Work from the `Visa-Agent` folder. `.profile/` contains one private folder per client profile, named from the supplied given and family names. A second profile with the same name receives `-2`, `-3`, and so on. Each folder has its own `state.sqlite3` and `profile.json`; documents saved through the runtime go into that folder's `documents/` tree. Folders and databases have local restrictive permissions. They are not encrypted.

```sh
python3 profile.py create --given-names "Asha" --family-name "Example"
python3 profile.py list
python3 profile.py show Asha_Example
```

These names are synthetic examples. Run profile commands containing real folder names only in a direct local terminal; their command arguments can otherwise enter an agent transcript. `create` records `candidate_reported` by default. Use `--name-basis passport_seen --provenance "..."` only after actual inspection. Default output omits names and paths; `show` gives the opaque case ID and revision. A human can use `--reveal` before the command in an interactive terminal for full local details. The program does not validate a passport or create a visa application.

To work on a selected profile, use `profile.py show` to get its case ID and current revision, then pass its folder to the existing runtime:

```sh
python3 -m runtime.cli --private-root .profile/Asha_Example checklist CASE_ID --revision 1 --token checklist_1 --input .profile/Asha_Example/route.json
```

Keep input JSON, notes, and saved outputs in the selected profile folder. See [runtime guide](./README_RUNTIME.md), [document workflow](./DOCUMENT_WORKFLOW.md), and [client/document schema](./schemas/client-documents.json). A public source must be checked again when answering a current-rule question. A local checklist cannot guarantee that it matches the particular ImmiAccount application.

To use the prompt agent, open this folder as a trusted Codex workspace and address `@visa_agent` if your client exposes configured roles through its mention picker. The project role is declared in [.codex/config.toml](./.codex/config.toml) and points to [.agents/visa_agent.toml](./.agents/visa_agent.toml). If the picker does not list it, refer to `.agents/visa-agent.md` in the request. This is a configured role and local workflow, not a background service.
