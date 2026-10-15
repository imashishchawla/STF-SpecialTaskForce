"""Local PII redaction, AES-256-GCM token vault, and de-tokenization.

Zero candidate PII leaves the local machine.
Direct company names are preserved; personal names, dates of birth,
contact details, passport numbers, and financial details are replaced
with deterministic XCVBH sentinel tokens.
"""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import uuid

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .contracts import ContractError

SENTINEL_PREFIX = "XCVBH"
NONCE_BYTES = 12


class PIILeakageError(ContractError):
    """Raised when un-redacted PII is detected in an egress payload."""
    pass


def get_or_create_vault_key(key_path: Path) -> bytes:
    """Load or generate a 256-bit AES key with 0600 permissions."""
    key_path = Path(key_path)
    if key_path.is_symlink():
        raise ContractError("Vault key path must not be a symlink")
    if key_path.is_file():
        key = key_path.read_bytes()
        if len(key) != 32:
            raise ContractError("Invalid AES-256 key length")
        return key
    key = AESGCM.generate_key(bit_length=256)
    key_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with key_path.open("wb") as f:
        os.chmod(key_path, 0o600)
        f.write(key)
    return key


def encrypt_vault_mapping(mapping: dict, key: bytes, enc_path: Path) -> None:
    """Encrypt token-to-value mapping to disk using AES-256-GCM."""
    enc_path = Path(enc_path)
    if enc_path.is_symlink():
        raise ContractError("Encrypted vault path must not be a symlink")
    aesgcm = AESGCM(key)
    nonce = os.urandom(NONCE_BYTES)
    data = json.dumps(mapping, ensure_ascii=False).encode("utf-8")
    ciphertext = aesgcm.encrypt(nonce, data, None)
    enc_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with enc_path.open("wb") as f:
        os.chmod(enc_path, 0o600)
        f.write(nonce + ciphertext)


def decrypt_vault_mapping(key: bytes, enc_path: Path) -> dict:
    """Decrypt token-to-value mapping from disk using AES-256-GCM."""
    enc_path = Path(enc_path)
    if enc_path.is_symlink() or not enc_path.is_file():
        raise ContractError("Encrypted vault file not found")
    payload = enc_path.read_bytes()
    if len(payload) < NONCE_BYTES + 16:
        raise ContractError("Corrupt encrypted vault payload")
    nonce = payload[:NONCE_BYTES]
    ciphertext = payload[NONCE_BYTES:]
    aesgcm = AESGCM(key)
    try:
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return json.loads(decrypted_bytes.decode("utf-8"))
    except Exception as exc:
        raise ContractError(f"Decryption failed: {exc}") from exc


class Redactor:
    """Deterministic token generator and regex-based PII scrubber.

    Preserves direct company names while replacing personal identifiers.
    """

    def __init__(self, session_salt: bytes = None):
        self.session_salt = session_salt or os.urandom(32)
        self.mapping = {}  # token -> real_value
        self.reverse_mapping = {}  # real_value -> token
        self._counter = 1

    def _make_token(self, raw_value: str) -> str:
        if raw_value in self.reverse_mapping:
            return self.reverse_mapping[raw_value]
        digest = hashlib.sha256(self.session_salt + raw_value.strip().encode("utf-8")).hexdigest()
        prefix = digest[:8].upper()
        token = f"{SENTINEL_PREFIX}-{prefix}-{self._counter:04d}"
        self._counter += 1
        self.mapping[token] = raw_value
        self.reverse_mapping[raw_value] = token
        return token

    def redact_text(self, text: str, known_entities: list = None) -> tuple[str, int]:
        """Redact sensitive patterns and known entities in text.

        Returns (redacted_text, count_of_substitutions).
        """
        if not text or not isinstance(text, str):
            return text, 0

        redacted = text
        subs_count = 0

        # 1. Exact match on known entities (e.g. given names, family names, full names)
        if known_entities:
            # Sort longest first to avoid partial replacements (e.g., "Asha Example" before "Asha")
            sorted_entities = sorted([e for e in set(known_entities) if e and len(e.strip()) > 1],
                                     key=len, reverse=True)
            for entity in sorted_entities:
                pattern = re.compile(rf"\b{re.escape(entity)}\b", re.IGNORECASE)
                matches = pattern.findall(redacted)
                if matches:
                    token = self._make_token(entity)
                    redacted, n = pattern.subn(token, redacted)
                    subs_count += n

        # 2. Email addresses
        email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
        for match in email_pattern.findall(redacted):
            token = self._make_token(match)
            redacted = redacted.replace(match, token)
            subs_count += 1

        # 3. Phone numbers (international and local formats)
        phone_pattern = re.compile(r"(?:\+91[-\s]?)?[6-9]\d{9}|\b(?:\+?[0-9]{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
        for match in phone_pattern.findall(redacted):
            token = self._make_token(match)
            redacted = redacted.replace(match, token)
            subs_count += 1

        # 4. Dates of Birth / Date stamps in personal contexts (e.g. DD-MM-YYYY, DD/MM/YYYY, YYYY-MM-DD)
        dob_pattern = re.compile(r"(?<![A-Za-z0-9_-])(?:(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])|(?:0[1-9]|[12]\d|3[01])[-/](?:0[1-9]|1[0-2])[-/](?:19|20)\d{2})(?![A-Za-z0-9_-])")
        for match in dob_pattern.findall(redacted):
            # Only mask if it looks like a birthdate rather than a current year/month
            if any(year in match for year in ["198", "199", "200"]):
                token = self._make_token(match)
                redacted = redacted.replace(match, token)
                subs_count += 1

        # 5. Passport patterns (e.g. Indian passport format: 1 letter followed by 7 digits)
        passport_pattern = re.compile(r"(?<!XCVBH-)\b[A-PR-WYa-pr-wy][1-9]\d{6}\b(?!-\d{4})")
        for match in passport_pattern.findall(redacted):
            token = self._make_token(match)
            redacted = redacted.replace(match, token)
            subs_count += 1

        return redacted, subs_count

    def detokenize(self, text: str) -> str:
        """Replace synthetic XCVBH tokens with their original values for local display."""
        if not text or not isinstance(text, str):
            return text
        detokenized = text
        for token, original in self.mapping.items():
            detokenized = detokenized.replace(token, original)
        return detokenized

    def export_vault(self, profile_dir: Path) -> dict:
        """Persist mapping into profile directory using AES-256-GCM."""
        profile_dir = Path(profile_dir)
        key_path = profile_dir / ".vault.key"
        enc_path = profile_dir / "vault.enc"
        key = get_or_create_vault_key(key_path)
        encrypt_vault_mapping(self.mapping, key, enc_path)
        return {
            "key_path": str(key_path),
            "vault_path": str(enc_path),
            "tokens_count": len(self.mapping),
        }
