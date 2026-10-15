"""Purpose-limited model packets. Documents and free text stay in the profile."""

from dataclasses import dataclass
import fcntl
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
from contextlib import contextmanager
from typing import Callable

from .contracts import ContractError
from .redactor import decrypt_vault_mapping, encrypt_vault_mapping, get_or_create_vault_key


TOKEN = re.compile(r"XCVBH-[A-F0-9]{24}")
PERIOD = re.compile(r"(?:19|20)\d{2}-(?:0[1-9]|1[0-2])")
IDENTITY_FIELDS = {"employer_name", "employee_name", "employee_id", "person_name",
                   "phone", "email", "passport_number"}
SALARY_FIELDS = {"employer_name", "employee_name", "employee_id", "pay_period",
                 "currency", "payment_mode", "gross_ge_net", "bank_credit_present",
                 "tax_or_pf_present", "roles_letter_present", "slip_count"}
IDENTITY_CHECK_FIELDS = {"person_name", "phone", "email", "passport_number",
                         "employee_id", "same_identity"}
POLICIES = {"salary_evidence": SALARY_FIELDS, "identity_check": IDENTITY_CHECK_FIELDS}
BOOL_FIELDS = {"gross_ge_net", "bank_credit_present", "tax_or_pf_present",
               "roles_letter_present", "same_identity"}
CURRENCIES = {"AUD", "INR", "USD", "GBP", "EUR"}
PAYMENT_MODES = {"bank_transfer", "cash", "cheque"}
MAX_IDENTITY_LENGTH = 160
_SEAL_KEY = secrets.token_bytes(32)


@dataclass(frozen=True)
class PreparedPacket:
    """Immutable serialized payload; construct only through prepare_packet."""

    wire_json: str
    seal: bytes


def _private_profile(profile_dir: Path) -> Path:
    path = Path(profile_dir).absolute()
    if path.parent.name != ".profile" or not path.is_dir():
        raise ContractError("Expected an existing private client profile")
    if path.is_symlink() or path.parent.is_symlink():
        raise ContractError("Private profile path must not contain symlinks")
    if path.stat().st_mode & 0o077 or path.parent.stat().st_mode & 0o077:
        raise ContractError("Private profile directory must be mode 0700")
    return path


def _validate(task: str, facts: dict) -> None:
    if task not in POLICIES or not isinstance(facts, dict) or not facts:
        raise ContractError("Unsupported task or empty selected facts")
    if set(facts) - POLICIES[task]:
        raise ContractError("Selected facts contain fields outside the task allowlist")
    for field, value in facts.items():
        if field in IDENTITY_FIELDS:
            if (not isinstance(value, str) or not value.strip()
                    or len(value) > MAX_IDENTITY_LENGTH or any(ord(c) < 32 for c in value)):
                raise ContractError("Invalid identity value")
        elif field == "pay_period":
            if not isinstance(value, str) or not PERIOD.fullmatch(value):
                raise ContractError("Pay period must be YYYY-MM")
        elif field == "currency":
            if not isinstance(value, str) or value not in CURRENCIES:
                raise ContractError("Unsupported currency")
        elif field == "payment_mode":
            if not isinstance(value, str) or value not in PAYMENT_MODES:
                raise ContractError("Unsupported payment mode")
        elif field in BOOL_FIELDS:
            if type(value) is not bool:
                raise ContractError("Expected a locally computed boolean")
        elif field == "slip_count":
            if type(value) is not int or not 1 <= value <= 500:
                raise ContractError("Invalid slip count")


def _load_mapping(profile: Path) -> tuple[bytes, dict]:
    key_path = profile / ".llm-vault.key"
    vault_path = profile / "llm-vault.enc"
    if vault_path.is_symlink() or key_path.is_symlink():
        raise ContractError("Model token vault must not be a symlink")
    if vault_path.exists() != key_path.exists():
        raise ContractError("Incomplete model token vault")
    if any(path.stat().st_mode & 0o077 for path in (key_path, vault_path) if path.exists()):
        raise ContractError("Model token vault files must be mode 0600")
    key = get_or_create_vault_key(key_path)
    mapping = decrypt_vault_mapping(key, vault_path) if vault_path.exists() else {}
    if (not isinstance(mapping, dict) or any(
            not isinstance(token, str) or not TOKEN.fullmatch(token) or not isinstance(value, str)
            for token, value in mapping.items())):
        raise ContractError("Invalid model token vault")
    return key, mapping


def _save_mapping(profile: Path, key: bytes, mapping: dict) -> None:
    temporary = profile / (".llm-vault-" + secrets.token_hex(12) + ".enc")
    try:
        encrypt_vault_mapping(mapping, key, temporary)
        os.replace(temporary, profile / "llm-vault.enc")
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def _vault_lock(profile: Path):
    lock_path = profile / ".llm-vault.lock"
    if lock_path.is_symlink():
        raise ContractError("Model token vault lock must not be a symlink")
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(lock_path, flags, 0o600)
    try:
        if os.fstat(descriptor).st_mode & 0o077:
            raise ContractError("Model token vault lock must be mode 0600")
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def prepare_packet(profile_dir: Path, task: str, selected_facts: dict) -> PreparedPacket:
    """Select fixed fields locally and tokenize identities before any model callback."""
    _validate(task, selected_facts)
    profile = _private_profile(profile_dir)
    with _vault_lock(profile):
        key, mapping = _load_mapping(profile)
        reverse = {value: token for token, value in mapping.items()}
        safe = {}
        changed = False
        for field, value in selected_facts.items():
            if field in IDENTITY_FIELDS:
                value = value.strip()
                token = reverse.get(value)
                if token is None:
                    token = "XCVBH-" + secrets.token_hex(12).upper()
                    while token in mapping:
                        token = "XCVBH-" + secrets.token_hex(12).upper()
                    mapping[token] = value
                    reverse[value] = token
                    changed = True
                safe[field] = token
            else:
                safe[field] = value
        if changed or not (profile / "llm-vault.enc").exists():
            _save_mapping(profile, key, mapping)
    packet = {"schema": 1, "task": task, "facts": safe}
    wire = json.dumps(packet, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    if any(value.lower() in wire.lower() for value in mapping.values() if len(value) > 1):
        raise ContractError("Unmasked identity value in prepared packet")
    return PreparedPacket(wire, hmac.new(_SEAL_KEY, wire.encode(), hashlib.sha256).digest())


def send_prepared_packet(packet: PreparedPacket, model_caller: Callable[[str], str]) -> str:
    """The sole model callback; it accepts only a structured prepared packet."""
    if not isinstance(packet, PreparedPacket):
        raise ContractError("Model call requires a prepared packet")
    expected_seal = hmac.new(_SEAL_KEY, packet.wire_json.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(packet.seal, expected_seal):
        raise ContractError("Model packet was not prepared by the local gateway")
    parsed = json.loads(packet.wire_json)
    if set(parsed) != {"schema", "task", "facts"} or parsed["schema"] != 1:
        raise ContractError("Invalid model packet schema")
    _validate(parsed.get("task"), parsed.get("facts"))
    for field, value in parsed["facts"].items():
        if field in IDENTITY_FIELDS and not TOKEN.fullmatch(value):
            raise ContractError("Model packet contains an unmasked identity")
    return model_caller(packet.wire_json)
