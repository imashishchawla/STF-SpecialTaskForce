"""
vault.py — Session vault and local encryption manager.

Implements Design Doc 08 (PII Protection and Encryption) for the STF
Terraform Support Agent.

Key Responsibilities:
1. Generates and manages cryptographically secure session salts.
2. Encrypts sensitive raw values using AES-256-GCM (via cryptography library
   when available, or authenticated fallback with PBKDF2/HMAC-SHA256).
3. Persists mappings in vault/<session_ulid>.jsonl (AES-GCM encrypted values).
4. Provides de-tokenization for local operator display only (never in LLM context).
"""
from __future__ import annotations

import base64
import json
import os
import pathlib
import secrets
import time
from typing import Any, Dict, Optional, Tuple

# Try to import cryptography's AESGCM; fall back to authenticated stdlib cipher if missing.
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _HAS_CRYPTOGRAPHY = True
except ImportError:
    _HAS_CRYPTOGRAPHY = False
    AESGCM = None  # type: ignore

import hashlib
import hmac


# Crockford Base32 alphabet for ULID generation
_CROCKFORD_BASE32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def generate_ulid() -> str:
    """Generate a 26-character ULID string (48-bit timestamp + 80-bit random)."""
    t_ms = int(time.time() * 1000)
    # 48-bit timestamp = 10 chars of base32
    time_chars = []
    temp_t = t_ms
    for _ in range(10):
        time_chars.append(_CROCKFORD_BASE32[temp_t % 32])
        temp_t //= 32
    time_part = "".join(reversed(time_chars))

    # 80-bit random = 16 chars of base32
    rand_bytes = secrets.token_bytes(10)
    rand_int = int.from_bytes(rand_bytes, byteorder="big")
    rand_chars = []
    for _ in range(16):
        rand_chars.append(_CROCKFORD_BASE32[rand_int % 32])
        rand_int //= 32
    rand_part = "".join(reversed(rand_chars))

    return f"{time_part}{rand_part}"


class SessionVault:
    """
    Session-scoped vault storing AES-256-GCM encrypted values for XCVBH tokens.

    Format of vault/<session_ulid>.jsonl:
    {"token": "XCVBH-...", "tier": "redacted|encrypted", "enc_value": "<b64>", "alg": "aes-256-gcm"}
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        vault_dir: Optional[pathlib.Path] = None,
        master_key: Optional[bytes] = None,
    ) -> None:
        self.session_id: str = session_id or generate_ulid()
        if vault_dir is None:
            # Default: ../vault relative to this file's agent directory
            agent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
            self.vault_dir = agent_dir / "vault"
        else:
            self.vault_dir = pathlib.Path(vault_dir)

        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.key_file = self.vault_dir / ".key"
        self.vault_file = self.vault_dir / f"{self.session_id}.jsonl"

        # Initialize or load master encryption key (32 bytes for AES-256)
        self._master_key: bytes = master_key or self._get_or_create_master_key()
        # Per-session salt (32 random bytes)
        self.session_salt: bytes = secrets.token_bytes(32)

        # In-memory session lookup tables for fast execution
        self._raw_to_token: Dict[str, str] = {}
        self._token_to_raw: Dict[str, str] = {}
        self._token_counter: int = 0

    def _get_or_create_master_key(self) -> bytes:
        """Read master key from vault/.key with chmod 600, or generate one."""
        env_key = os.environ.get("STF_VAULT_KEY")
        if env_key:
            return hashlib.sha256(env_key.encode("utf-8")).digest()

        if self.key_file.exists():
            data = self.key_file.read_bytes()
            if len(data) >= 32:
                return data[:32]

        # Generate new 32-byte key
        key = secrets.token_bytes(32)
        try:
            self.key_file.write_bytes(key)
            self.key_file.chmod(0o600)
        except OSError:
            # Fall back to in-memory key if filesystem permission prevents write
            pass
        return key

    def _encrypt(self, plain_text: str) -> Tuple[str, str]:
        """
        Encrypt plain text with AES-256-GCM or authenticated fallback.
        Returns (base64_encoded_ciphertext, algorithm_name).
        """
        data = plain_text.encode("utf-8")
        nonce = secrets.token_bytes(12)  # 96-bit nonce

        if _HAS_CRYPTOGRAPHY and AESGCM is not None:
            aesgcm = AESGCM(self._master_key)
            ct = aesgcm.encrypt(nonce, data, None)
            combined = nonce + ct
            return base64.b64encode(combined).decode("ascii"), "aes-256-gcm"

        # Authenticated stdlib fallback: PBKDF2-derived keystream + HMAC-SHA256
        salt = secrets.token_bytes(16)
        stream_key = hashlib.pbkdf2_hmac("sha256", self._master_key, salt, 10000, 32)
        mac_key = hashlib.sha256(self._master_key + b":mac").digest()

        # Keystream XOR
        keystream = hashlib.sha256(stream_key + nonce).digest()
        while len(keystream) < len(data):
            keystream += hashlib.sha256(keystream).digest()
        cipher_bytes = bytes(b ^ k for b, k in zip(data, keystream[:len(data)]))

        tag = hmac.new(mac_key, salt + nonce + cipher_bytes, hashlib.sha256).digest()
        combined = b"STD1" + salt + nonce + tag + cipher_bytes
        return base64.b64encode(combined).decode("ascii"), "pbkdf2-hmac-sha256"

    def _decrypt(self, b64_ciphertext: str, alg: str) -> str:
        """Decrypt ciphertext back to plain text."""
        raw = base64.b64decode(b64_ciphertext.encode("ascii"))

        if alg == "aes-256-gcm" and _HAS_CRYPTOGRAPHY and AESGCM is not None:
            nonce = raw[:12]
            ct = raw[12:]
            aesgcm = AESGCM(self._master_key)
            plain = aesgcm.decrypt(nonce, ct, None)
            return plain.decode("utf-8")

        if raw.startswith(b"STD1"):
            salt = raw[4:20]
            nonce = raw[20:32]
            tag = raw[32:64]
            cipher_bytes = raw[64:]

            mac_key = hashlib.sha256(self._master_key + b":mac").digest()
            expected_tag = hmac.new(mac_key, salt + nonce + cipher_bytes, hashlib.sha256).digest()
            if not hmac.compare_digest(tag, expected_tag):
                raise ValueError("Vault ciphertext authentication verification failed")

            stream_key = hashlib.pbkdf2_hmac("sha256", self._master_key, salt, 10000, 32)
            keystream = hashlib.sha256(stream_key + nonce).digest()
            while len(keystream) < len(cipher_bytes):
                keystream += hashlib.sha256(keystream).digest()
            plain_bytes = bytes(b ^ k for b, k in zip(cipher_bytes, keystream[:len(cipher_bytes)]))
            return plain_bytes.decode("utf-8")

        raise ValueError(f"Unsupported vault encryption algorithm: {alg}")

    def store_token(self, token: str, raw_value: str, tier: str = "redacted") -> None:
        """Store a token -> raw_value mapping in the encrypted vault file."""
        if token in self._token_to_raw:
            return

        self._raw_to_token[raw_value] = token
        self._token_to_raw[token] = raw_value

        enc_value, alg = self._encrypt(raw_value)
        entry = {
            "token": token,
            "tier": tier,
            "enc_value": enc_value,
            "alg": alg,
        }

        with open(self.vault_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def get_token_for_value(self, raw_value: str) -> Optional[str]:
        """Return existing token for raw_value if already registered in this session."""
        return self._raw_to_token.get(raw_value)

    def next_counter(self) -> int:
        """Return next 1-based sequential counter."""
        self._token_counter += 1
        return self._token_counter

    def detokenize_text(self, text: str) -> str:
        """
        Operator-only display helper: replace XCVBH tokens with plain-text values.
        Never invoke inside LLM context window.
        """
        # If in-memory map is missing tokens, reload from vault file
        if self.vault_file.exists():
            with open(self.vault_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        t = record["token"]
                        if t not in self._token_to_raw:
                            val = self._decrypt(record["enc_value"], record.get("alg", "aes-256-gcm"))
                            self._token_to_raw[t] = val
                    except Exception:
                        continue

        result = text
        for token, raw_val in self._token_to_raw.items():
            result = result.replace(token, raw_val)
        return result
