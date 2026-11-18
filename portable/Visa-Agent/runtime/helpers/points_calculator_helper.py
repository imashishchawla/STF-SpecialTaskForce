#!/usr/bin/env python3
# Source: Adapted from ScriptSavvy's AustraliaVisaSkills
# License: CC BY-NC 4.0 | Attribution: ScriptSavvy/Immigent

# SPDX-License-Identifier: BSD-0-Clause
# Zero-Clause BSD
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.
"""Optional arithmetic only; no factual or legal entitlement verification."""
import json
import sys


# Mechanical baseline only; these bands are not verification of current law.
BANDS = {
    "age": (0, 15, 25, 30), "english": (0, 10, 20),
    "overseas_employment": (0, 5, 10, 15),
    "australian_employment": (0, 5, 10, 15, 20),
    "professional_year": (0, 5), "education": (0, 10, 15, 20),
    "specialist_education": (0, 10), "australian_study": (0, 5),
    "community_language": (0, 5), "regional_study": (0, 5),
    "partner": (0, 5, 10), "nomination": (0, 5, 15),
}


def unique_factors(pairs):
    """Reject repeated JSON keys instead of silently taking the last value."""
    factors = {}
    for name, value in pairs:
        if name in factors:
            raise ValueError("Duplicate factor: " + name)
        factors[name] = value
    return factors


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: python3 points_calculator_helper.py INPUT.json"}))
        return 2
    try:
        with open(sys.argv[1], encoding="utf-8") as source:
            factors = json.load(source, object_pairs_hook=unique_factors)
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}))
        return 2
    error = None
    if not isinstance(factors, dict):
        error = "Input must be a JSON object."
    elif set(factors) - set(BANDS):
        error = "Unknown factors: " + ", ".join(sorted(set(factors) - set(BANDS)))
    else:
        for name, value in factors.items():
            if value is None:
                continue
            if type(value) is not int or value < 0:
                error = name + ": expected a nonnegative integer or null."
                break
            if value not in BANDS[name]:
                error = name + ": invalid point band."
                break
    if error:
        print(json.dumps({"error": error}))
        return 2
    known = {name: value for name in BANDS
             if (value := factors.get(name)) is not None}
    employment = sum(known.get(name, 0) for name in
                     ("overseas_employment", "australian_employment"))
    result = {
        "status": "provisional",
        "notice": "Arithmetic only: factual and legal entitlement not verified; no eligibility judgment.",
        "provisional_supported_subtotal": sum(known.values()) - employment + min(employment, 20),
        "unresolved": [name for name in BANDS if name not in known],
        "employment_raw": employment,
        "employment_capped": min(employment, 20),
    }
    print(json.dumps(result))


if __name__ == "__main__":
    sys.exit(main())
