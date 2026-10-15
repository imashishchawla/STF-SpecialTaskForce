#!/usr/bin/env python3
"""Local-only salary-slip inventory; never prints document text, names, or paths."""

from collections import Counter
from pathlib import Path
import re
import shutil
import subprocess
import sys

PROFILE_ROOT = Path(__file__).resolve().parent / ".profile"
SALARY_NAME = re.compile(r"salary|pay.?slip|wage.?slip", re.I)
SALARY_TEXT = re.compile(r"salary\s*slip|pay\s*slip|payslip|earnings\s+deductions|gross\s+(?:salary|pay)", re.I)
FIELDS = {
    "pay_amount_label": re.compile(r"\b(?:gross|net|basic)\s*(?:pay|salary|earnings)\b", re.I),
    "bank_account_label": re.compile(r"\b(?:bank\s*(?:account|a/c)|account\s*(?:number|no\.?))\b", re.I),
    "tax_or_pension_label": re.compile(r"\b(?:PAN|UAN|EPF|PF\s*(?:no|number))\b", re.I),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
}


def main() -> int:
    extractor = shutil.which("pdftotext")
    if not extractor:
        print("status=blocked reason=pdftotext_missing")
        return 2
    if not PROFILE_ROOT.is_dir():
        print("status=blocked reason=profile_root_missing")
        return 2
    totals = Counter()
    for profile in sorted(p for p in PROFILE_ROOT.iterdir() if p.is_dir() and not p.is_symlink()):
        totals["profiles"] += 1
        for path in profile.rglob("*"):
            if not path.is_file() or path.is_symlink():
                continue
            if path.suffix.lower() != ".pdf":
                if SALARY_NAME.search(path.name):
                    totals["unsupported_salary_named_files"] += 1
                continue
            totals["pdfs_scanned"] += 1
            try:
                result = subprocess.run([extractor, "-layout", str(path), "-"],
                                        capture_output=True, timeout=20, check=False)
            except subprocess.TimeoutExpired:
                totals["pdf_extraction_timeouts"] += 1
                continue
            text = result.stdout.decode("utf-8", "ignore") if result.returncode == 0 else ""
            if SALARY_NAME.search(path.name) or SALARY_TEXT.search(text):
                totals["salary_candidates"] += 1
                if not text.strip():
                    totals["salary_text_unreadable"] += 1
                if path.stat().st_mode & 0o077:
                    totals["salary_files_overpermissive"] += 1
                for field, pattern in FIELDS.items():
                    if pattern.search(text):
                        totals[field] += 1
    for key in ("profiles", "pdfs_scanned", "salary_candidates", "salary_text_unreadable",
                "salary_files_overpermissive", "unsupported_salary_named_files", "pdf_extraction_timeouts",
                *FIELDS):
        print(f"{key}={totals[key]}")
    return 1 if (totals["salary_text_unreadable"] or totals["salary_files_overpermissive"]
                 or totals["unsupported_salary_named_files"] or totals["pdf_extraction_timeouts"]) else 0


if __name__ == "__main__":
    sys.exit(main())
