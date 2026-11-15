"""
Master Certification Retrieval & Curation Agent - Central Orchestrator Supervisor
Coordinates Scraper Worker, Deduplication Engine, and Curator Worker in a Hub-and-Spoke topology.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv

# Ensure local imports work cleanly
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

from harness.models import CredentialItem, CurationMatrix
from harness.config import LLMClient
from tools.dedupe_engine import DeduplicationEngine
from tools.search_tools import TavilySearchTool
from tools.scrape_tools import FirecrawlScraperTool


class CertificationOrchestrator:
    def __init__(self, env_path: Optional[Path] = None):
        # Load local .env if present
        load_dotenv(dotenv_path=env_path or (ROOT_DIR / ".env"))

        self.knowledge_seed = ROOT_DIR / "knowledge" / "seed_known_badges.json"
        self.output_dir = ROOT_DIR / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.dedupe = DeduplicationEngine(seed_file=self.knowledge_seed)
        self.search_tool = TavilySearchTool()
        self.scraper_tool = FirecrawlScraperTool()
        self.llm = LLMClient()

    def run_pipeline(self, domain_target: str, max_candidates: int = 5) -> CurationMatrix:
        """
        Executes the end-to-end Hub-and-Spoke workflow:
        1. Formulates deep query
        2. Retrieves target pages via Tavily
        3. Scrapes metadata & syllabus via Firecrawl
        4. Deduplicates against known credentials
        5. Validates with Curator Worker (LLM)
        6. Aggregates into verified CurationMatrix
        """
        print(f"\n[ORCHESTRATOR] Initializing crawl for domain target: '{domain_target}'")
        print(f"[ORCHESTRATOR] Baseline verified badges loaded: {self.dedupe.count()}")

        # Step 1: Execute Deep Search
        search_query = f"{domain_target} (credential OR certification OR badge) (credly OR 'exam blueprint' OR 'self-paced') -site:udemy.com -site:coursera.org"
        print(f"[SCRAPER WORKER] Executing Tavily deep search query...")
        search_results = self.search_tool.search(query=search_query, max_results=max_candidates * 2)

        curated_items: List[CredentialItem] = []

        # Step 2: Iterate and scrape
        for result in search_results:
            title = result.get("title", "")
            url = result.get("url", "")
            print(f"\n[ORCHESTRATOR -> SCRAPER] Inspecting: {title} ({url})")

            # Check deduplication
            if self.dedupe.is_duplicate(candidate_name=title):
                print(f"[DEDUPE ENGINE] Candidate already exists in baseline. Skipping.")
                continue

            # Deep scrape with Firecrawl
            scrape_data = self.scraper_tool.scrape_url(url)
            if not scrape_data.get("success"):
                continue

            # Step 3: Dispatch to Curator Worker for schema validation
            print(f"[ORCHESTRATOR -> CURATOR] Classifying credential metadata...")
            curator_prompt = f"""
            Target Title: {title}
            Target URL: {url}
            Extracted Content: {scrape_data.get('markdown', '')[:2000]}
            Credly Signal: {scrape_data.get('credly_detected', False)}
            LinkedIn Signal: {scrape_data.get('linkedin_detected', False)}

            Strict Instructions:
            Extract the credential attributes into JSON matching:
            {{
                "name": "Exact credential name",
                "issuer": "Issuing vendor or organization",
                "category": "{domain_target.capitalize()}",
                "url": "{url}",
                "cost": "Free / Paid ($X) / Free Course + Paid Exam",
                "exact_format": "Proctored | Non-Proctored / 100% Unproctored | Self-paced Assessment | Short Reading & Quiz | Online Assessment on Skill Builder",
                "credly_badge": true/false,
                "credly_badge_url": "URL or null",
                "linkedin_addable": true/false,
                "linkedin_cert_id_supported": true/false,
                "why_hidden": "1 concise sentence explaining value or obscurity"
            }}
            """
            system_prompt = "You are a master certification verification agent. Output only valid JSON adhering strictly to the schema."
            raw_json = self.llm.generate_json(prompt=curator_prompt, system_prompt=system_prompt)

            try:
                # Validate with Pydantic v2
                item = CredentialItem(**raw_json)
                if not self.dedupe.is_duplicate(item.name, item.issuer):
                    curated_items.append(item)
                    self.dedupe.register({"name": item.name, "issuer": item.issuer, "url": item.url})
                    print(f"[CURATOR] Successfully verified: {item.name}")
                else:
                    print(f"[DEDUPE ENGINE] Normalized duplicate detected: {item.name}")
            except Exception as e:
                print(f"[WARN] Item validation failed: {e}")

            if len(curated_items) >= max_candidates:
                break

        # Step 4: Aggregate into final CurationMatrix
        matrix = CurationMatrix(items=curated_items)
        self.save_artifacts(matrix)
        return matrix

    def save_artifacts(self, matrix: CurationMatrix) -> None:
        """
        Saves curated matrix to markdown and JSON.
        """
        md_file = self.output_dir / "curated_matrix.md"
        json_file = self.output_dir / "curated_matrix.json"

        report_md = matrix.to_markdown_report()
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(report_md)

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump([item.model_dump() for item in matrix.items], f, indent=2)

        print(f"\n[ORCHESTRATOR] Output written to:")
        print(f"  - Markdown: {md_file}")
        print(f"  - JSON:     {json_file}")


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Kubernetes & Cloud Security"
    orchestrator = CertificationOrchestrator()
    result_matrix = orchestrator.run_pipeline(domain_target=query, max_candidates=3)
    print("\n" + "=" * 60)
    print("FINAL CURATED REPORT:")
    print("=" * 60)
    print(result_matrix.to_markdown_report())
