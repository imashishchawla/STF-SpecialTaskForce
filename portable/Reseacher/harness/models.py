"""
Master Certification Retrieval & Curation Agent - Pydantic v2 Models
Enforces strict taxonomy validation and formatting.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, HttpUrl, field_validator


ProctoringFormat = Literal[
    "Proctored",
    "Non-Proctored / 100% Unproctored",
    "Self-paced Assessment",
    "Short Reading & Quiz",
    "Online Assessment on Skill Builder"
]

PriceType = Literal[
    "Free",
    "Paid",
    "Freemium",
    "Free Course + Paid Exam"
]


class CredentialItem(BaseModel):
    name: str = Field(..., description="Full credential or certification name")
    issuer: str = Field(..., description="Issuing organization, vendor, or academy")
    category: str = Field(..., description="High-level category, e.g. Cloud, DevSecOps, AI, Security")
    url: str = Field(..., description="Direct link to enrollment or syllabus")
    cost: str = Field(default="Free", description="Cost descriptor (Free, Paid ($X), Free Course + Paid Exam)")
    exact_format: ProctoringFormat = Field(..., description="Strict proctoring classification")
    credly_badge: bool = Field(default=False, description="Whether credential awards official Credly badge")
    credly_badge_url: Optional[str] = Field(None, description="Direct URL to Credly badge template if found")
    linkedin_addable: bool = Field(default=False, description="Whether credential has dedicated LinkedIn Add Cert link")
    linkedin_cert_id_supported: bool = Field(default=False, description="Whether cert includes unique Certificate ID")
    why_hidden: str = Field(..., description="1-sentence explanation of why this is hidden or high-value")

    @field_validator("exact_format", mode="before")
    @classmethod
    def normalize_format(cls, v: str) -> str:
        if not isinstance(v, str):
            return "Self-paced Assessment"
        v_clean = v.strip()
        allowed = [
            "Proctored",
            "Non-Proctored / 100% Unproctored",
            "Self-paced Assessment",
            "Short Reading & Quiz",
            "Online Assessment on Skill Builder"
        ]
        for a in allowed:
            if a.lower() in v_clean.lower():
                return a
        # Fallback mapping
        if "proctor" in v_clean.lower() and "non" not in v_clean.lower() and "un" not in v_clean.lower():
            return "Proctored"
        if "skill builder" in v_clean.lower():
            return "Online Assessment on Skill Builder"
        if "quiz" in v_clean.lower() or "reading" in v_clean.lower():
            return "Short Reading & Quiz"
        return "Self-paced Assessment"

    @property
    def credibility_summary(self) -> str:
        parts = []
        if self.credly_badge:
            parts.append("Issues Credly Badge")
        if self.linkedin_addable or self.linkedin_cert_id_supported:
            parts.append("Includes LinkedIn Cert ID verification link")
        if not parts:
            parts.append("Vendor-verified digital badge")
        return " / ".join(parts)

    def to_markdown(self) -> str:
        return (
            f"- **[{self.name}]** | *Issued by: {self.issuer}*\n"
            f"  - **URL:** {self.url}\n"
            f"  - **Cost:** {self.cost}\n"
            f"  - **Exact Format:** {self.exact_format}\n"
            f"  - **Credibility Integration:** {self.credibility_summary}\n"
            f"  - **Why It's Hidden/High-Value:** {self.why_hidden}\n"
        )


class CurationMatrix(BaseModel):
    title: str = "Curated Master Certification Matrix"
    items: List[CredentialItem] = Field(default_factory=list)

    def group_by_category(self) -> dict[str, List[CredentialItem]]:
        grouped: dict[str, List[CredentialItem]] = {}
        for item in self.items:
            grouped.setdefault(item.category, []).append(item)
        return grouped

    def to_markdown_report(self) -> str:
        grouped = self.group_by_category()
        output_lines = []
        for category, cat_items in grouped.items():
            output_lines.append(f"### {category}")
            for item in cat_items:
                output_lines.append(item.to_markdown().rstrip())
            output_lines.append("")
        return "\n".join(output_lines)
