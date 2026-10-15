#!/usr/bin/env python3
"""CLI utility to inspect and decrypt AES-256-GCM client vault files."""

import argparse
import json
from pathlib import Path
import sys

from runtime.redactor import decrypt_vault_mapping

ROOT = Path(__file__).resolve().parent
PROFILES = ROOT / ".profile"


def decrypt_profile_vault(profile_folder: Path) -> dict:
    profile_folder = Path(profile_folder)
    key_path = profile_folder / ".vault.key"
    enc_path = profile_folder / "vault.enc"
    if not key_path.is_file():
        raise FileNotFoundError(f"Vault key missing: {key_path}")
    if not enc_path.is_file():
        raise FileNotFoundError(f"Encrypted vault missing: {enc_path}")

    key = key_path.read_bytes()
    return decrypt_vault_mapping(key, enc_path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", help="Client profile folder name (e.g. Asha_Example) or path")
    parser.add_argument("--profiles-root", type=Path, default=PROFILES, help="Root directory for profiles")
    parser.add_argument("--reveal", action="store_true", help="Display mapping only in a direct interactive terminal")
    args = parser.parse_args(argv)

    if args.reveal and (not sys.stdin.isatty() or not sys.stdout.isatty()):
        print("Error: Vault reveal requires an interactive terminal", file=sys.stderr)
        return 1

    target = Path(args.folder)
    if not target.is_dir():
        target = args.profiles_root / args.folder

    if not target.is_dir():
        print("Error: Profile folder not found", file=sys.stderr)
        return 1

    try:
        mapping = decrypt_profile_vault(target)
        result = {"status": "available", "token_count": len(mapping)}
        if args.reveal:
            result["mapping"] = mapping
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except Exception:
        print(json.dumps({"status": "error", "message": "Local vault inspection failed"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
