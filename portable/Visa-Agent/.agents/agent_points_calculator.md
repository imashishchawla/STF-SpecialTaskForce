# Points Calculator

## Scope

Calculate points for Australian skilled migration visas: 189 (General Skilled Migration), 190 (State Nominated), and 491 (Regional Sponsored Visa).

**Reference**: [Official Home Affairs Points Calculator](https://immi.homeaffairs.gov.au/help-support/tools/points-calculator)

**Data model**: Pure-function calculator; no external API or network calls. All rules deterministic per official Home Affairs specifications.

## Input Contract

```json
{
  "age": <integer, 18-125>,
  "english_test": <string, one of: "IELTS", "TOEFL", "PTE", "Cambridge", "OET">,
  "english_score": <score for chosen test>,
  "experience_years": <integer, 0+>,
  "qualification": <string, one of: "doctorate", "masters", "bachelor", "diploma", "advanced_diploma", "none">,
  "occupation_code": <string, optional, for reference only>,
  "state": <string, optional, state code for 190/491>,
  "spouse_assessment": <boolean, optional, default false>
}
```

### English Test Score Ranges

| Test | Minimum Score | Points |
|------|---------------|--------|
| **IELTS** | 8.5+ | 20 |
| | 8.0–8.5 | 20 |
| | 7.5–8.0 | 20 |
| | 7.0–7.5 | 10 |
| | 6.5–7.0 | 10 |
| | 6.0–6.5 | 0 |
| **TOEFL** | 110+ | 20 |
| | 94–109 | 20 |
| | 79–93 | 10 |
| | 60–78 | 10 |
| **PTE** | 79+ | 20 |
| | 72–78 | 10 |
| | 50–71 | 10 |
| **Cambridge** | 185+ | 20 |
| | 176–184 | 20 |
| | 162–175 | 10 |
| | 147–161 | 10 |
| **OET** | A | 20 |
| | B | 20 |
| | C | 10 |
| | D | 0 |

### Work Experience Rules

- 1–2 years: 5 points
- 3–4 years: 10 points
- 5–7 years: 15 points
- 8–9 years: 20 points
- 10+ years: 20 points

### Qualification Points

- Doctorate (any source): 15 points
- Masters (any source): 15 points
- Bachelor (any source): 15 points
- Advanced Diploma / Diploma: 10 points
- No qualification: 0 points

### Spouse Skills Assessment

- Positive assessment: 5 points
- No assessment or negative: 0 points

### Visa-Specific Bonuses

| Visa | Bonus | Typical Minimum Cutoff (Estimate) |
|------|-------|-----------------------------------|
| 189  | 0     | 65 points (subject to round)     |
| 190  | +5    | 60 points (state nomination)     |
| 491  | +5    | 60 points (regional sponsorship) |

**191 Permanent Residence Path**: 491 holders eligible after 3 years in designated regional area; treated as new application.

## Output Contract

```json
{
  "occupation_code": <string>,
  "visa_189": {
    "visa_type": "189",
    "visa_name": "General Skilled Migration",
    "total_points": <integer>,
    "breakdown": {
      "age": <integer>,
      "english": <integer>,
      "experience": <integer>,
      "qualification": <integer>,
      "spouse": <integer>,
      "visa_bonus": 0
    },
    "metadata": {
      "visa_bonus": 0,
      "estimated_minimum_cutoff": 65
    }
  },
  "visa_190": {
    "visa_type": "190",
    "visa_name": "State Nominated",
    "state": <string>,
    "total_points": <integer>,
    "breakdown": {
      "age": <integer>,
      "english": <integer>,
      "experience": <integer>,
      "qualification": <integer>,
      "spouse": <integer>,
      "visa_bonus": 5
    },
    "metadata": {
      "visa_bonus": 5,
      "estimated_minimum_cutoff": 60,
      "note": "Must be nominated by a State or Territory"
    }
  },
  "visa_491": {
    "visa_type": "491",
    "visa_name": "Regional Sponsored",
    "state": <string>,
    "total_points": <integer>,
    "breakdown": {
      "age": <integer>,
      "english": <integer>,
      "experience": <integer>,
      "qualification": <integer>,
      "spouse": <integer>,
      "visa_bonus": 5
    },
    "metadata": {
      "visa_bonus": 5,
      "provisional_reduction": -10,
      "regional_bonus": 15,
      "estimated_minimum_cutoff": 60,
      "note": "Provisional visa; eligible for 191 after 3 years in designated region"
    }
  },
  "recommended_visa": <string, "189" | "190" | "491">,
  "version": "1.0.0",
  "disclaimer": "..."
}
```

## Invocation Steps

### Python API (runtime/points_calculator.py)

```python
from runtime.points_calculator import PointsCalculator

calc = PointsCalculator()

# Single visa calculation
result_189 = calc.calculate_189({
    'age': 30,
    'english_test': 'IELTS',
    'english_score': 7.5,
    'experience_years': 5,
    'qualification': 'bachelor',
    'spouse_assessment': False
})

# All three visas at once
all_results = calc.calculate_all({
    'age': 30,
    'english_test': 'IELTS',
    'english_score': 7.5,
    'experience_years': 5,
    'qualification': 'bachelor',
    'occupation_code': '261312',
    'state': 'NSW'
})

# Generate improvement scenarios
scenarios = calc.generate_scenarios(client_data, visa='189')

# Assess likelihood vs. current cutoff
likelihood = calc.assess_likelihood('189', points=70, cutoff=65)

# Get current estimated cutoffs
cutoffs = calc.get_current_cutoffs()
```

### Error Handling

All methods raise `PointsCalculationError` if:
- Required fields are missing
- Age is outside 18–125 range
- English test is unknown or score is invalid
- Experience years is negative or > 100
- Qualification is not a recognized level
- Spouse assessment is not a boolean

## Key Limitations & Disclaimers

1. **Estimates only** — This calculator reproduces official Home Affairs rules but is not an official system. Points are indicative only.

2. **Not an EOI** — Results do not constitute an official Expression of Interest (EOI) in SkillSelect.

3. **Current cutoffs estimates** — Suggested minimum cutoff points (65 for 189, 60 for 190/491) are based on recent rounds and vary by occupation, age bracket, and invitation strategy. Verify with [SkillSelect](https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect/expression-of-interest).

4. **Additional gates not modeled** — This calculator scores only on points. The following are separate requirements:
   - Skills assessment (positive for your occupation)
   - Police clearance and health requirements
   - State/territory nomination (for 190)
   - Regional sponsorship (for 491)
   - English minimum (6.0 IELTS or equivalent)
   - Occupation on relevant skilled list (189/190/491 or state list)

5. **Skill assessment validity** — Not all occupations accept all test types. Consult your assessing authority (ACS, AHPRA, etc.).

6. **Points component rules** — All rules per Home Affairs official calculator as of October 2026. Changes may apply; verify with official source.

## Reference

- **Official Calculator**: https://immi.homeaffairs.gov.au/help-support/tools/points-calculator
- **SkillSelect Guidance**: https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect/expression-of-interest
- **Skilled Occupations List**: https://immi.homeaffairs.gov.au/help-support/tools/skilled-occupations-list
- **489 to 191 Transition**: https://immi.homeaffairs.gov.au/visas/skilled-migration/skilled-independent-491
