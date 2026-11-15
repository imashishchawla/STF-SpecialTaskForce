"""
Test suite for Master Certification Retrieval & Curation Agent
Verifies Pydantic v2 taxonomy validation, deduplication engine, and output formatting.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from harness.models import CredentialItem, CurationMatrix
from tools.dedupe_engine import DeduplicationEngine
from tools.search_tools import TavilySearchTool
from tools.scrape_tools import FirecrawlScraperTool
from harness.orchestrator import CertificationOrchestrator


def test_credential_taxonomy_normalization():
    # Test valid 5-item proctoring mapping
    item1 = CredentialItem(
        name="Test Proctored Cert",
        issuer="Test Org",
        category="Tech",
        url="https://example.com/cert",
        cost="Free",
        exact_format="proctored exam by pearson",  # should normalize
        credly_badge=True,
        why_hidden="Rare pilot credential."
    )
    assert item1.exact_format == "Proctored"

    item2 = CredentialItem(
        name="Skill Builder Exam",
        issuer="AWS",
        category="Tech",
        url="https://example.com/cert",
        cost="Free",
        exact_format="online assessment on skill builder portal",
        credly_badge=True,
        why_hidden="Obscure badge."
    )
    assert item2.exact_format == "Online Assessment on Skill Builder"


def test_markdown_output_format():
    item = CredentialItem(
        name="Certified Calico Operator: Level 1",
        issuer="Tigera",
        category="DevSecOps & Kubernetes",
        url="https://academy.tigera.io",
        cost="Free",
        exact_format="Self-paced Assessment",
        credly_badge=True,
        linkedin_addable=True,
        why_hidden="Industry standard Kubernetes CNI certification."
    )
    md = item.to_markdown()
    assert "- **[Certified Calico Operator: Level 1]** | *Issued by: Tigera*" in md
    assert "- **URL:** https://academy.tigera.io" in md
    assert "- **Cost:** Free" in md
    assert "- **Exact Format:** Self-paced Assessment" in md
    assert "- **Credibility Integration:** Issues Credly Badge / Includes LinkedIn Cert ID verification link" in md
    assert "- **Why It's Hidden/High-Value:** Industry standard Kubernetes CNI certification." in md


def test_deduplication_engine():
    seed_file = PROJECT_ROOT / "knowledge" / "seed_known_badges.json"
    engine = DeduplicationEngine(seed_file=seed_file)
    assert engine.count() >= 20

    # Test detection of existing badge in seed
    assert engine.is_duplicate("AWS Educate Introduction to Generative AI") is True
    assert engine.is_duplicate("aws educate generative ai") is True
    assert engine.is_duplicate("Certified Calico Operator Level 1") is True

    # Test novel non-duplicate badge
    assert engine.is_duplicate("Quantum Computing Cryptographic Proofs 2027") is False


def test_search_listicle_filtering():
    tool = TavilySearchTool()
    results = tool.search("Cloud certifications")
    assert len(results) > 0
    for r in results:
        # None of the results should be from banned listicle domains
        assert "medium.com" not in r["url"]
        assert "simplilearn.com" not in r["url"]


def test_orchestrator_dry_run(tmp_path):
    orchestrator = CertificationOrchestrator()
    # Override output dir to temporary path for isolated testing
    orchestrator.output_dir = tmp_path
    matrix = orchestrator.run_pipeline(domain_target="Cloud Architecture", max_candidates=1)

    assert isinstance(matrix, CurationMatrix)
    assert len(matrix.items) >= 1
    assert (tmp_path / "curated_matrix.md").exists()
    assert (tmp_path / "curated_matrix.json").exists()
