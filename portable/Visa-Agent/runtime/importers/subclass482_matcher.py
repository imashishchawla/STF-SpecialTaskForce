#!/usr/bin/env python3
"""
Subclass 482 Employer Matcher
Matches candidates to potential SID 482 sponsors using company database and 482 requirements.

Source: Adapted from ScriptSavvy's AustraliaVisaSkills
License: CC BY-NC 4.0 | Attribution: ScriptSavvy/Immigent
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Candidate:
    """Candidate profile for matching."""
    name: str
    occupation_code: str
    occupation_name: str
    skills: List[str]
    years_experience: int
    english_level: str  # e.g., "IELTS 7.0", "PTE 65"
    location_preference: Optional[str] = None
    visa_status: Optional[str] = None


@dataclass
class EmployerMatch:
    """Match result for an employer."""
    company_name: str
    abn: str
    industry: str
    location: str
    employees: int
    match_score: float
    matching_skills: List[str]
    gaps: List[str]
    reasons: List[str]
    next_steps: List[str]


class Subclass482Matcher:
    """Matches candidates to SID 482 sponsors."""

    def __init__(self,
                 companies_db_path: Optional[str] = None,
                 requirements_path: Optional[str] = None):
        """
        Initialize the matcher.

        Args:
            companies_db_path: Path to companies JSON database
            requirements_path: Path to Subclass 482 requirements directory
        """
        self.companies_db = {}
        self.requirements = {}

        # Try to load company database
        if companies_db_path is None:
            companies_db_path = str(Path(__file__).parent.parent.parent /
                                   "knowledge" / "companies" / "tech_sponsors_master.json")

        if os.path.exists(companies_db_path):
            with open(companies_db_path, 'r') as f:
                self.companies_db = json.load(f)
        else:
            self.companies_db = self._get_mock_companies()

        # Try to load requirements
        if requirements_path is None:
            requirements_path = str(Path(__file__).parent.parent.parent /
                                   "knowledge" / "australia" / "subclass482")

        self.requirements_path = requirements_path
        self._load_requirements()

    def _get_mock_companies(self) -> Dict[str, Any]:
        """Return mock companies database for testing."""
        return {
            "metadata": {
                "total_companies": 3,
                "last_updated": "2026-11-17",
                "source": "Mock database for testing"
            },
            "companies": [
                {
                    "id": "tech001",
                    "name": "TechFlow Solutions",
                    "abn": "12345678901",
                    "industry": "Information Technology",
                    "location": "Sydney, NSW",
                    "employees": 150,
                    "sponsored_before": True,
                    "is_sbs": True,
                    "occupations_sponsored": ["261311", "261312", "261313"],
                    "tech_skills": ["JavaScript", "Python", "React", "AWS"],
                    "turnover_aud": 15000000,
                    "contact": "hr@techflow.com"
                },
                {
                    "id": "tech002",
                    "name": "DataInsights Pty Ltd",
                    "abn": "98765432109",
                    "industry": "Data Analytics",
                    "location": "Melbourne, VIC",
                    "employees": 75,
                    "sponsored_before": True,
                    "is_sbs": True,
                    "occupations_sponsored": ["261311", "261312"],
                    "tech_skills": ["Python", "SQL", "Machine Learning", "Tableau"],
                    "turnover_aud": 8500000,
                    "contact": "recruitment@datainsights.com"
                },
                {
                    "id": "tech003",
                    "name": "CloudNative Systems",
                    "abn": "11111111111",
                    "industry": "Cloud Infrastructure",
                    "location": "Brisbane, QLD",
                    "employees": 85,
                    "sponsored_before": False,
                    "is_sbs": True,
                    "occupations_sponsored": ["261311", "261313"],
                    "tech_skills": ["Kubernetes", "Go", "DevOps", "AWS", "Azure"],
                    "turnover_aud": 10000000,
                    "contact": "talent@cloudnative.com"
                }
            ]
        }

    def _load_requirements(self):
        """Load Subclass 482 requirements from markdown files."""
        requirements_files = {
            "overview": "integrated-workflow.md",
            "nomination": "nomination.md",
            "visa": "visa-application.md",
            "evidence": "evidence-and-terms.md",
            "updates": "verified-updates.md"
        }

        for key, filename in requirements_files.items():
            filepath = os.path.join(self.requirements_path, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    self.requirements[key] = f.read()[:500]  # Store first 500 chars

    def match_candidate_to_employers(self, candidate: Candidate) -> List[EmployerMatch]:
        """
        Match a candidate to suitable SID 482 employers.

        Args:
            candidate: Candidate profile

        Returns:
            Sorted list of EmployerMatch results (highest score first)
        """
        matches = []

        companies = self.companies_db.get("companies", [])

        for company in companies:
            match_score = 0.0
            matching_skills = []
            gaps = []
            reasons = []

            # 1. Occupation match (40 points max)
            if candidate.occupation_code in company.get("occupations_sponsored", []):
                match_score += 40
                reasons.append(f"Occupation {candidate.occupation_code} previously sponsored")
            else:
                gaps.append(f"Occupation code not in sponsor's history")

            # 2. Skills match (30 points max)
            company_skills = set(s.lower() for s in company.get("tech_skills", []))
            candidate_skills = set(s.lower() for s in candidate.skills)
            matching = candidate_skills & company_skills

            if matching:
                match_score += min(30, len(matching) * 10)
                matching_skills = list(matching)
                reasons.append(f"Strong skill overlap: {', '.join(matching_skills)}")
            else:
                gaps.append("Limited matching skills found")

            # 3. SBS status (15 points)
            if company.get("is_sbs"):
                match_score += 15
                reasons.append("Approved Standard Business Sponsor (SBS)")
            else:
                gaps.append("Not yet an approved SBS")

            # 4. Prior sponsorship (10 points)
            if company.get("sponsored_before"):
                match_score += 10
                reasons.append("Demonstrated track record of sponsoring workers")
            else:
                gaps.append("No prior sponsorship history")

            # 5. Location preference (5 points)
            if candidate.location_preference:
                company_location = company.get("location", "").lower()
                if candidate.location_preference.lower() in company_location:
                    match_score += 5
                    reasons.append(f"Location match: {company.get('location')}")

            # 6. Company size / capacity (depends on results)
            if company.get("employees", 0) >= 50:
                reasons.append("Established company with capacity")
            else:
                gaps.append("Smaller organization - may impact capacity assessment")

            # Normalize score to 0-100
            match_score = min(100, match_score)

            # Build next steps
            next_steps = [
                "Review company Subclass 482 sponsorship history and approvals",
                "Confirm occupation eligibility under current SID 482 rules",
                "Verify salary meets applicable thresholds (SSIT/CSIT)",
                "Prepare Labour Market Testing (LMT) evidence",
                "Contact company to explore sponsorship opportunity",
                "Obtain employment contract draft for visa application",
                "Prepare English language evidence if required"
            ]

            if match_score >= 50:  # Only include reasonable matches
                match = EmployerMatch(
                    company_name=company.get("name"),
                    abn=company.get("abn"),
                    industry=company.get("industry"),
                    location=company.get("location"),
                    employees=company.get("employees"),
                    match_score=match_score,
                    matching_skills=matching_skills,
                    gaps=gaps,
                    reasons=reasons,
                    next_steps=next_steps
                )
                matches.append(match)

        # Sort by match score (highest first)
        matches.sort(key=lambda x: x.match_score, reverse=True)

        return matches

    def generate_matching_report(self, candidate: Candidate) -> str:
        """
        Generate a formatted matching report for a candidate.

        Args:
            candidate: Candidate profile

        Returns:
            Formatted report string
        """
        matches = self.match_candidate_to_employers(candidate)

        report = f"""
# Subclass 482 Employer Matching Report

**Candidate:** {candidate.name}
**Occupation:** {candidate.occupation_code} - {candidate.occupation_name}
**Experience:** {candidate.years_experience} years
**English Level:** {candidate.english_level}
**Skills:** {', '.join(candidate.skills)}

---

## Matching Results

"""

        if not matches:
            report += "No suitable employer matches found in current database.\n"
            report += "\n### Recommended Actions:\n"
            report += "1. Expand skills to match common SID 482 occupations\n"
            report += "2. Consider alternative occupations in ANZSCO Major Groups 1, 2, 4, 5, 6\n"
            report += "3. Contact employers directly for sponsorship opportunities\n"
        else:
            report += f"Found {len(matches)} potential employer(s).\n\n"

            for i, match in enumerate(matches, 1):
                report += f"### Match #{i}: {match.company_name}\n"
                report += f"- **Match Score:** {match.match_score:.0f}%\n"
                report += f"- **Industry:** {match.industry}\n"
                report += f"- **Location:** {match.location}\n"
                report += f"- **Employees:** {match.employees}\n"
                report += f"- **ABN:** {match.abn}\n\n"

                report += "**Reasons for Match:**\n"
                for reason in match.reasons:
                    report += f"- {reason}\n"

                if match.gaps:
                    report += "\n**Considerations:**\n"
                    for gap in match.gaps:
                        report += f"- {gap}\n"

                report += "\n**Next Steps:**\n"
                for step in match.next_steps:
                    report += f"1. {step}\n"
                report += "\n---\n\n"

        report += """
## Subclass 482 Key Requirements Checklist

### Nomination Stage
- [ ] Employer is approved Standard Business Sponsor (SBS) or has executed Labour Agreement
- [ ] Position matches eligible occupation (ANZSCO Major Groups 1, 2, 4, 5, 6 OR Core Skills List)
- [ ] Annual earnings (excluding non-monetary benefits) meet applicable threshold
- [ ] Employment contract signed by both employer and nominee
- [ ] Labour Market Testing (LMT) completed (unless exemption applies)
- [ ] No relevant adverse information about sponsor

### Visa Application Stage
- [ ] Nominee meets occupation requirements and work experience
- [ ] English language skills demonstrated (varies by occupation/country)
- [ ] Health requirements met (health checks)
- [ ] Character requirements met
- [ ] Security and background checks passed
- [ ] Invitation from employer (nomination approval)

### Important Notes
1. This report uses mock data for demonstration purposes
2. All figures and matches should be verified against current official databases
3. Consult official Home Affairs website for current SID 482 requirements
4. Engage a registered migration agent for professional advice
5. Requirements change frequently - verify before lodging

---

**Generated:** {self._get_timestamp()}
**Source:** Subclass 482 Integration System
**License:** CC BY-NC 4.0 (ScriptSavvy/Immigent)
"""

        return report

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    """Test the matcher with sample candidate."""
    # Create matcher
    matcher = Subclass482Matcher()

    # Create test candidate
    candidate = Candidate(
        name="John Smith",
        occupation_code="261311",
        occupation_name="Analyst Programmer",
        skills=["Python", "JavaScript", "React", "AWS", "Docker"],
        years_experience=5,
        english_level="IELTS 7.0",
        location_preference="Sydney",
        visa_status="Skilled Independent visa holder"
    )

    print("=" * 70)
    print("SUBCLASS 482 EMPLOYER MATCHING TEST")
    print("=" * 70)
    print()

    # Get matches
    matches = matcher.match_candidate_to_employers(candidate)

    print(f"Candidate: {candidate.name}")
    print(f"Occupation: {candidate.occupation_code} - {candidate.occupation_name}")
    print(f"Found {len(matches)} potential employer(s)\n")

    for i, match in enumerate(matches, 1):
        print(f"{i}. {match.company_name} - Score: {match.match_score:.0f}%")
        print(f"   Location: {match.location} | Employees: {match.employees}")
        print(f"   Matching Skills: {', '.join(match.matching_skills) or 'None'}")
        print()

    # Generate full report
    print("\n" + "=" * 70)
    print("FULL MATCHING REPORT")
    print("=" * 70)
    report = matcher.generate_matching_report(candidate)
    print(report)


if __name__ == "__main__":
    main()
