"""
Master Certification Retrieval & Curation Agent - Tavily Search Tool
Performs deep-web queries with anti-listicle filters and domain scoping.
"""

import os
import requests
from typing import List, Dict, Any, Optional

BANNED_LISTICLE_DOMAINS = [
    "medium.com",
    "simplilearn.com",
    "geeksforgeeks.org",
    "forbes.com",
    "businessinsider.com",
    "top10",
    "best-certifications",
    "quora.com",
    "reddit.com"
]


class TavilySearchTool:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self.endpoint = "https://api.tavily.com/search"

    def search(
        self,
        query: str,
        search_depth: str = "advanced",
        max_results: int = 10,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes a deep-web search query via Tavily, stripping listicle domains.
        """
        if not self.api_key or self.api_key.startswith("tvly-your-"):
            return self._mock_fallback_search(query)

        effective_exclude = list(set((exclude_domains or []) + BANNED_LISTICLE_DOMAINS))

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_raw_content": False
        }

        if include_domains:
            payload["include_domains"] = include_domains
        if effective_exclude:
            payload["exclude_domains"] = effective_exclude

        try:
            resp = requests.post(self.endpoint, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])

            # Secondary filter for any remaining blog aggregator titles
            filtered = []
            for r in results:
                title = r.get("title", "").lower()
                if any(kw in title for kw in ["top 10", "best cert", "top 5", "ultimate guide to"]):
                    continue
                filtered.append({
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "content": r.get("content", ""),
                    "score": r.get("score", 0.0)
                })
            return filtered
        except Exception as e:
            print(f"[WARN] Tavily API error ({e}). Using mock/fallback.")
            return self._mock_fallback_search(query)

    def _mock_fallback_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Deterministic mock search results for test environments and dry-runs.
        Includes novel candidates to test discovery beyond the baseline.
        """
        return [
            {
                "title": "Cloud Native eBPF Security Specialist Assessment",
                "url": "https://isovalent.com/labs/ebpf-specialist",
                "content": "Specialized kernel observability and network security credential rarely indexed on mainstream course aggregators.",
                "score": 0.95
            },
            {
                "title": "Databricks Lakehouse Fundamentals Accreditation",
                "url": "https://academy.databricks.com/pathway/lakehouse-fundamentals",
                "content": "Free self-paced assessment on Databricks Academy. Issues an official Credly digital badge upon passing score.",
                "score": 0.92
            },
            {
                "title": "AWS Educate Getting Started with Storage",
                "url": "https://www.awseducate.com",
                "content": "Baseline credential used to test deduplication detection.",
                "score": 0.85
            }
        ]
