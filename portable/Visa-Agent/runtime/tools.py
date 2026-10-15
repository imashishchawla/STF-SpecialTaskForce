"""Deterministic migration calculation, evidence auditing, and ANZSCO tools.

All calculations follow Department of Home Affairs Schedule 6D points test
and Australian Computer Society (ACS) payment evidence standards.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Optional

from .contracts import ContractError
from .llm import query_anzsco_public_tool
from .redactor import Redactor, get_or_create_vault_key, decrypt_vault_mapping

# --- 1. DETERMINISTIC SCHEDULE 6D POINTS CALCULATOR ---

def calculate_gsm_points(
    age: int,
    english_level: str,
    overseas_exp_years: float,
    education_level: str,
    partner_status: str,
    australian_exp_years: float = 0.0,
    australian_study: bool = False,
    stem_specialist: bool = False,
    naati_ccl: bool = False,
) -> dict:
    """Calculate Australian GSM points test (Schedule 6D) for Subclasses 189, 190, and 491.

    Args:
        age: Age in years at time of invitation
        english_level: 'competent', 'proficient', or 'superior'
        overseas_exp_years: Years of verifiable skilled employment outside Australia
        education_level: 'doctorate', 'bachelor_or_master', 'diploma_or_trade', 'other'
        partner_status: 'single', 'aus_citizen_pr', 'partner_skilled_english', 'partner_english_only', 'other'
        australian_exp_years: Years of skilled employment in Australia
        australian_study: 2+ academic years completed in Australia
        stem_specialist: Masters by research or PhD in STEM in Australia
        naati_ccl: Credentialed community language
    """
    breakdown = {}

    # 1. Age
    if 18 <= age <= 24:
        age_pts = 25
    elif 25 <= age <= 32:
        age_pts = 30
    elif 33 <= age <= 39:
        age_pts = 25
    elif 40 <= age <= 44:
        age_pts = 15
    else:
        age_pts = 0
    breakdown["age"] = {"value": age, "points": age_pts, "eligible": age < 45}

    # 2. English
    eng_map = {"competent": 0, "proficient": 10, "superior": 20}
    eng_pts = eng_map.get(english_level.lower(), 0)
    breakdown["english"] = {"level": english_level, "points": eng_pts}

    # 3. Overseas Skilled Employment (after Skill Met Date)
    if overseas_exp_years >= 8.0:
        o_exp_pts = 15
    elif overseas_exp_years >= 5.0:
        o_exp_pts = 10
    elif overseas_exp_years >= 3.0:
        o_exp_pts = 5
    else:
        o_exp_pts = 0
    breakdown["overseas_experience"] = {"years": overseas_exp_years, "points": o_exp_pts}

    # 4. Australian Skilled Employment
    if australian_exp_years >= 8.0:
        a_exp_pts = 20
    elif australian_exp_years >= 5.0:
        a_exp_pts = 15
    elif australian_exp_years >= 3.0:
        a_exp_pts = 10
    elif australian_exp_years >= 1.0:
        a_exp_pts = 5
    else:
        a_exp_pts = 0
    # Combined work experience cap = 20 points
    combined_exp = min(20, o_exp_pts + a_exp_pts)
    breakdown["australian_experience"] = {"years": australian_exp_years, "points": a_exp_pts}
    breakdown["total_work_experience_capped"] = combined_exp

    # 5. Educational Qualifications
    edu_map = {
        "doctorate": 20,
        "phd": 20,
        "bachelor_or_master": 15,
        "master": 15,
        "bachelor": 15,
        "diploma_or_trade": 10,
        "other": 0,
    }
    edu_pts = edu_map.get(education_level.lower(), 0)
    breakdown["education"] = {"level": education_level, "points": edu_pts}

    # 6. Partner Skills
    partner_map = {
        "single": 10,
        "aus_citizen_pr": 10,
        "partner_skilled_english": 10,
        "partner_english_only": 5,
        "other": 0,
    }
    partner_pts = partner_map.get(partner_status.lower(), 0)
    breakdown["partner"] = {"status": partner_status, "points": partner_pts}

    # 7. Additional bonuses
    study_pts = 5 if australian_study else 0
    stem_pts = 10 if stem_specialist else 0
    naati_pts = 5 if naati_ccl else 0
    breakdown["australian_study"] = study_pts
    breakdown["stem_specialist"] = stem_pts
    breakdown["naati_ccl"] = naati_pts

    base_score = (
        age_pts
        + eng_pts
        + combined_exp
        + edu_pts
        + partner_pts
        + study_pts
        + stem_pts
        + naati_pts
    )

    return {
        "subclass_189_points": base_score,
        "subclass_190_points": base_score + 5,
        "subclass_491_points": base_score + 15,
        "meets_minimum_pass_mark": base_score >= 65,
        "breakdown": breakdown,
    }


# --- 2. ACS EMPLOYMENT & PAYMENT EVIDENCE AUDITOR ---

def audit_acs_employment_episode(
    employer: str,
    months_duration: float,
    payment_mode: str,
    has_bank_credits: bool,
    has_tax_or_pf: bool,
    has_detailed_roles_letter: bool,
) -> dict:
    """Audit a single employment episode against ACS skills assessment guidelines."""
    findings = []
    status = "eligible"

    # ACS Cash Payment Rule:
    is_cash = payment_mode.lower() == "cash" or (not has_bank_credits and not has_tax_or_pf)
    if is_cash:
        status = "rejected"
        findings.append(
            "CRITICAL ACS VIOLATION: Cash payments are strictly not accepted by ACS under any circumstances. "
            "Must provide independent third-party bank statements or tax/PF records, or omit this episode from points claim."
        )

    if not has_detailed_roles_letter:
        findings.append(
            "WARNING: Reference letter must be on official company letterhead signed by authorized manager/HR, "
            "stating exact dates, weekly hours (≥20 hrs/wk), and detailed duties (5–7 bullet points)."
        )

    if not has_tax_or_pf and has_bank_credits:
        findings.append(
            "NOTE: ACS requires at least two independent types of payment evidence. "
            "Combine bank statements with payslips and employer letter."
        )

    return {
        "employer": employer,
        "duration_months": months_duration,
        "acs_compliance_status": status,
        "recommendation": "Exclude from ACS claim" if status == "rejected" else "Include in ACS claim",
        "findings": findings,
    }


def calculate_acs_skill_met_date(
    degree_type: str,
    career_episodes: list[dict],
) -> dict:
    """Calculate ACS Skill Met Date and verifiable post-qualification experience.

    degree_type: 'btech_ict_major', 'bca_msc_ict_major', 'ict_minor', 'non_ict'
    career_episodes: list of dicts with 'employer', 'months', 'eligible'
    """
    # Standard deduction: 2 years for 4-yr B.Tech ICT Major, 2-4 years for others
    deduction_months = 24.0 if degree_type in ("btech_ict_major", "bachelor_4yr_ict") else 48.0

    total_eligible_months = sum(ep["months"] for ep in career_episodes if ep.get("eligible", True))
    post_skill_met_months = max(0.0, total_eligible_months - deduction_months)
    post_skill_met_years = round(post_skill_met_months / 12.0, 1)

    return {
        "degree_classification": degree_type,
        "acs_deduction_years": deduction_months / 12.0,
        "total_eligible_work_years": round(total_eligible_months / 12.0, 1),
        "post_skill_met_years": post_skill_met_years,
        "overseas_points_bracket": 15 if post_skill_met_years >= 8.0 else (10 if post_skill_met_years >= 5.0 else (5 if post_skill_met_years >= 3.0 else 0)),
        "max_points_achieved": post_skill_met_years >= 8.0,
    }


# --- 3. PUBLIC OCCUPATION & ROUND TOOLS ---

def search_anzsco_occupation(query: str) -> dict:
    """Search Australian occupation codes and synonyms (e.g. '.net developer', 'terraform', 'python')."""
    return query_anzsco_public_tool("search_occupations", {"query": query})


def get_anzsco_occupation_detail(code: str) -> dict:
    """Get occupation lists (MLTSSL/STSOL), assessing authority (ACS/EA), and visa pathways for a 6-digit ANZSCO."""
    return query_anzsco_public_tool("get_occupation", {"code": code})


def get_latest_invitation_round() -> dict:
    """Get the latest official SkillSelect invitation round results and points cutoffs."""
    return query_anzsco_public_tool("get_latest_skillselect_round", {})
