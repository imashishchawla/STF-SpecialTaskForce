"""
Master Certification Retrieval & Curation Agent - Deduplication Engine
Cross-references candidates against known baseline and prevents duplicate entries.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from difflib import SequenceMatcher

STOP_WORDS = {
    "cert", "certified", "certification", "badge", "program", "course",
    "the", "a", "an", "and", "or", "to", "for", "in", "on", "with", "at", "by", "of"
}


def tokenize(text: str) -> Set[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    return {w for w in cleaned.split() if w and w not in STOP_WORDS}


def normalize_title(text: str) -> str:
    tokens = sorted(list(tokenize(text)))
    return " ".join(tokens)


def token_overlap_ratio(tokens_a: Set[str], tokens_b: Set[str]) -> float:
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a.intersection(tokens_b)
    min_len = min(len(tokens_a), len(tokens_b))
    return len(intersection) / float(min_len)


class DeduplicationEngine:
    def __init__(self, seed_file: Optional[Path] = None):
        self.known_badges: List[Dict[str, Any]] = []
        if seed_file and seed_file.exists():
            try:
                with open(seed_file, "r", encoding="utf-8") as f:
                    self.known_badges = json.load(f)
            except Exception as e:
                print(f"[WARN] Could not load seed file: {e}")

    def is_duplicate(self, candidate_name: str, candidate_issuer: str = "", threshold: float = 0.75) -> bool:
        candidate_tokens = tokenize(candidate_name)
        if not candidate_tokens:
            return False

        for item in self.known_badges:
            known_name = item.get("name", "")
            known_issuer = item.get("issuer", "")
            known_tokens = tokenize(known_name)

            # 1. Exact string match after normalization
            if normalize_title(candidate_name) == normalize_title(known_name):
                return True

            # 2. Token overlap: If key distinctive tokens are a subset
            overlap = token_overlap_ratio(candidate_tokens, known_tokens)
            if overlap >= 0.75 and len(candidate_tokens.intersection(known_tokens)) >= 3:
                return True

            # 3. SequenceMatcher similarity
            sim = SequenceMatcher(None, normalize_title(candidate_name), normalize_title(known_name)).ratio()
            if sim >= threshold:
                return True

            # 4. Issuer match + moderate overlap
            if candidate_issuer and known_issuer:
                if candidate_issuer.lower() in known_issuer.lower() or known_issuer.lower() in candidate_issuer.lower():
                    if overlap >= 0.60 or sim >= 0.60:
                        return True

        return False

    def register(self, item: Dict[str, Any]) -> None:
        self.known_badges.append(item)

    def count(self) -> int:
        return len(self.known_badges)
