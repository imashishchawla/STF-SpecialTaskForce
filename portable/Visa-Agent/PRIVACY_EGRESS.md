# Local validation and model egress

1. Identify one client profile and keep source documents, extracted text, local paths, and audit output inside that profile. Do not print them in an agent tool result.
2. Validate salary slips locally with `python3 audit_salary_slips.py`. This checks text extraction and file permissions across profiles and reports aggregate field presence. It does not authenticate records or reconcile figures. Perform any content checks in local code or a private human review.
3. Select only facts needed for the model task. `salary_evidence` accepts employer and employee names/ID, pay period, currency, payment mode, slip count, and locally computed booleans. It excludes exact pay, tax, bank, and document values. `identity_check` accepts name, phone, email, passport or employee ID, plus a locally computed match boolean. All identity strings become random tokens.
4. Call `prepare_packet(profile_dir, task, selected_facts)` and pass its result to `send_prepared_packet(packet, model_caller)`. The encrypted token map stays in the selected profile. The model callback receives only the JSON packet; neither function opens a document. Unknown fields and arbitrary prompts are rejected.
5. Keep `mcp.json` empty and the legacy model adapter disabled unless a reviewed provider integration calls only `send_prepared_packet`. Do not log packet inputs, vault values, exceptions with raw inputs, or provider responses containing unexpected personal data.
6. Profile and vault CLIs hide private fields by default. Their `--reveal` mode is for a human at a direct terminal. Real profile folder names and command arguments can themselves enter a model transcript; agents should not invoke these commands for real clients.

```python
from runtime.safe_egress import prepare_packet, send_prepared_packet

packet = prepare_packet(profile_dir, "salary_evidence", {
    "employer_name": local_employer_name,
    "pay_period": "2026-09",
    "bank_credit_present": True,
})
response = send_prepared_packet(packet, model_caller)
```

`profile_dir` and `local_employer_name` are local variables. Never paste a real profile path or value into a prompt, test, or log. A packet uses a random token for the name. This gateway controls repository callbacks; it cannot control a separately configured chat client, shell tool, or historical provider log.
