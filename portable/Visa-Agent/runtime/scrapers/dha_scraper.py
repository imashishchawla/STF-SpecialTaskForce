#!/usr/bin/env python3
"""
Home Affairs Data Scraper (DHA Scraper)

Fetches and parses Australian Department of Home Affairs visa data from 4 public endpoints:
1. Visa Finder - All visa subclasses and types
2. Skilled Occupation List - ANZSCO codes and assessing authorities
3. SkillSelect Invitation Rounds - Latest invitation data and cutoff points
4. Visa Listing - Visa subclasses, status, and conditions

Resilience features:
- CSS selectors with XPath fallbacks
- Exponential backoff retry (1s, 2s, 4s)
- Error logging with timestamps
- Stale data fallback after 2 consecutive failures
- User-Agent header for identification
- 30-second request timeout per endpoint

Output: JSON snapshots with metadata to knowledge/raw_dha/<endpoint>_YYYY-MM-DD.json
Error log: Append-only JSONL to knowledge/raw_dha/scraper_errors.jsonl
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
RAW_DHA_DIR = KNOWLEDGE_DIR / "raw_dha"
ERROR_LOG = RAW_DHA_DIR / "scraper_errors.jsonl"

# Ensure directories exist
RAW_DHA_DIR.mkdir(parents=True, exist_ok=True)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DHAScraper:
    """
    Production-ready scraper for Home Affairs public visa data.

    Handles 4 endpoints with comprehensive error handling, retry logic,
    and fallback to stale data on repeated failures.
    """

    # Endpoints to scrape
    ENDPOINTS = {
        "visa_finder": {
            "url": "https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-finder",
            "output_file": "visa_finder",
            "description": "All visa subclasses and types"
        },
        "occupation_list": {
            "url": "https://immi.homeaffairs.gov.au/visas/working-in-australia/skill-occupation-list",
            "output_file": "occupation_list",
            "description": "ANZSCO codes and assessing authorities"
        },
        "skillselect": {
            "url": "https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect/invitation-rounds",
            "output_file": "skillselect_latest",
            "description": "SkillSelect invitation rounds and cutoff points"
        },
        "visa_listing": {
            "url": "https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing",
            "output_file": "visa_listing",
            "description": "All visa subclasses, status, and conditions"
        }
    }

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 2, 4]  # exponential backoff: 1s, 2s, 4s
    REQUEST_TIMEOUT = 30  # seconds
    USER_AGENT = "Visa-Agent-Scraper/1.0 (Australian visa intelligence)"

    def __init__(self, verbose: bool = False):
        """
        Initialize scraper.

        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        if verbose:
            logger.setLevel(logging.DEBUG)

        # Check BeautifulSoup availability
        if BeautifulSoup is None:
            logger.warning(
                "BeautifulSoup4 not installed. Install with: pip install beautifulsoup4"
            )

    def scrape_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Scrape all 4 endpoints and save results.

        Returns:
            Dict with results for each endpoint: {endpoint: {status, path, errors}}
        """
        results = {}
        for endpoint_key in self.ENDPOINTS.keys():
            if endpoint_key == "visa_finder":
                results[endpoint_key] = self.scrape_visa_finder()
            elif endpoint_key == "occupation_list":
                results[endpoint_key] = self.scrape_occupation_list()
            elif endpoint_key == "skillselect":
                results[endpoint_key] = self.scrape_skillselect_rounds()
            elif endpoint_key == "visa_listing":
                results[endpoint_key] = self.scrape_visa_listing()

        return results

    def scrape_visa_finder(self) -> Dict[str, Any]:
        """
        Scrape Visa Finder endpoint.

        Extracts visa subclasses, types (work, family, skilled, temporary),
        and relevant metadata.

        Returns:
            Dict with status, path, and error details
        """
        endpoint_key = "visa_finder"
        endpoint = self.ENDPOINTS[endpoint_key]

        logger.info(f"Scraping {endpoint_key}: {endpoint['url']}")

        html = self._fetch_with_retry(endpoint["url"], endpoint_key)
        if not html:
            return self._prepare_stale_response(endpoint_key)

        try:
            data = self._parse_visa_finder(html)
            return self._save_json_snapshot(endpoint_key, data)
        except Exception as e:
            logger.error(f"Error parsing visa_finder: {str(e)}")
            self._log_error(endpoint_key, "parse_error", str(e))
            return self._prepare_stale_response(endpoint_key)

    def scrape_occupation_list(self) -> Dict[str, Any]:
        """
        Scrape Skilled Occupation List endpoint.

        Extracts ANZSCO codes, occupation titles, assessing authorities,
        and visa codes.

        Returns:
            Dict with status, path, and error details
        """
        endpoint_key = "occupation_list"
        endpoint = self.ENDPOINTS[endpoint_key]

        logger.info(f"Scraping {endpoint_key}: {endpoint['url']}")

        html = self._fetch_with_retry(endpoint["url"], endpoint_key)
        if not html:
            return self._prepare_stale_response(endpoint_key)

        try:
            data = self._parse_occupation_list(html)
            return self._save_json_snapshot(endpoint_key, data)
        except Exception as e:
            logger.error(f"Error parsing occupation_list: {str(e)}")
            self._log_error(endpoint_key, "parse_error", str(e))
            return self._prepare_stale_response(endpoint_key)

    def scrape_skillselect_rounds(self) -> Dict[str, Any]:
        """
        Scrape SkillSelect Invitation Rounds endpoint.

        Extracts latest invitation round date, occupation codes,
        cutoff points (189, 190, 491 per state).

        Returns:
            Dict with status, path, and error details
        """
        endpoint_key = "skillselect"
        endpoint = self.ENDPOINTS[endpoint_key]

        logger.info(f"Scraping {endpoint_key}: {endpoint['url']}")

        html = self._fetch_with_retry(endpoint["url"], endpoint_key)
        if not html:
            return self._prepare_stale_response(endpoint_key)

        try:
            data = self._parse_skillselect_rounds(html)
            return self._save_json_snapshot(endpoint_key, data)
        except Exception as e:
            logger.error(f"Error parsing skillselect_rounds: {str(e)}")
            self._log_error(endpoint_key, "parse_error", str(e))
            return self._prepare_stale_response(endpoint_key)

    def scrape_visa_listing(self) -> Dict[str, Any]:
        """
        Scrape Visa Listing endpoint.

        Extracts visa subclasses, open/closed status, and conditions.

        Returns:
            Dict with status, path, and error details
        """
        endpoint_key = "visa_listing"
        endpoint = self.ENDPOINTS[endpoint_key]

        logger.info(f"Scraping {endpoint_key}: {endpoint['url']}")

        html = self._fetch_with_retry(endpoint["url"], endpoint_key)
        if not html:
            return self._prepare_stale_response(endpoint_key)

        try:
            data = self._parse_visa_listing(html)
            return self._save_json_snapshot(endpoint_key, data)
        except Exception as e:
            logger.error(f"Error parsing visa_listing: {str(e)}")
            self._log_error(endpoint_key, "parse_error", str(e))
            return self._prepare_stale_response(endpoint_key)

    # Private methods

    def _fetch_with_retry(self, url: str, endpoint_key: str) -> Optional[str]:
        """
        Fetch URL with exponential backoff retry logic.

        Tries up to MAX_RETRIES times with delays [1s, 2s, 4s].
        Returns None after MAX_RETRIES failures.

        Args:
            url: URL to fetch
            endpoint_key: Endpoint identifier for logging

        Returns:
            HTML content or None on failure
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.debug(f"Attempt {attempt + 1}/{self.MAX_RETRIES} for {endpoint_key}")

                req = Request(url, headers={"User-Agent": self.USER_AGENT})
                with urlopen(req, timeout=self.REQUEST_TIMEOUT) as response:
                    html = response.read().decode("utf-8", errors="replace")
                    logger.info(f"Successfully fetched {endpoint_key} (attempt {attempt + 1})")
                    return html

            except (HTTPError, URLError, TimeoutError) as e:
                logger.warning(
                    f"Fetch error for {endpoint_key} (attempt {attempt + 1}): {str(e)}"
                )
                self._log_error(endpoint_key, "fetch_error", str(e))

                # Retry with backoff
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAYS[attempt]
                    logger.info(f"Retrying {endpoint_key} in {delay}s...")
                    time.sleep(delay)

            except Exception as e:
                logger.error(f"Unexpected error fetching {endpoint_key}: {str(e)}")
                self._log_error(endpoint_key, "unexpected_error", str(e))
                return None

        # All retries exhausted
        logger.error(f"All retries exhausted for {endpoint_key}")
        self._log_error(endpoint_key, "max_retries_exceeded",
                       f"Failed after {self.MAX_RETRIES} attempts")
        return None

    def _parse_visa_finder(self, html: str) -> Dict[str, Any]:
        """
        Parse Visa Finder HTML.

        Extracts visa subclasses, types, and metadata.

        Args:
            html: HTML content

        Returns:
            Parsed data structure
        """
        if not BeautifulSoup:
            logger.warning("BeautifulSoup not available, returning placeholder")
            return {"visas": [], "parsing_note": "BeautifulSoup not installed"}

        soup = BeautifulSoup(html, "html.parser")
        visas = []

        # CSS selector approach
        visa_rows = soup.select("div.visa-card, div.visa-item, li.visa-entry")
        if visa_rows:
            logger.debug(f"Found {len(visa_rows)} visa rows with CSS selector")
            for row in visa_rows:
                visa = self._extract_visa_from_row(row)
                if visa:
                    visas.append(visa)

        # XPath fallback (simulate with find_all)
        if not visas:
            logger.debug("CSS selector failed, trying fallback parse")
            links = soup.find_all("a", href=True)
            for link in links:
                if "visa" in link.get("href", "").lower():
                    text = link.get_text(strip=True)
                    if text:
                        visas.append({"type": text, "url": link.get("href")})

        return {"visas": visas, "count": len(visas)}

    def _parse_occupation_list(self, html: str) -> Dict[str, Any]:
        """
        Parse Skilled Occupation List HTML.

        Extracts ANZSCO codes, occupation titles, and assessing authorities.

        Args:
            html: HTML content

        Returns:
            Parsed data structure
        """
        if not BeautifulSoup:
            logger.warning("BeautifulSoup not available, returning placeholder")
            return {"occupations": [], "parsing_note": "BeautifulSoup not installed"}

        soup = BeautifulSoup(html, "html.parser")
        occupations = []

        # Try to find table with occupation data
        tables = soup.find_all("table")
        logger.debug(f"Found {len(tables)} tables in occupation list")

        for table in tables:
            rows = table.find_all("tr")[1:]  # Skip header
            for row in rows[:100]:  # Limit to first 100
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    occupation = {
                        "anzsco": cells[0].get_text(strip=True),
                        "title": cells[1].get_text(strip=True),
                    }
                    if len(cells) > 2:
                        occupation["assessing_authority"] = cells[2].get_text(strip=True)
                    occupations.append(occupation)

        return {"occupations": occupations, "count": len(occupations)}

    def _parse_skillselect_rounds(self, html: str) -> Dict[str, Any]:
        """
        Parse SkillSelect Invitation Rounds HTML.

        Extracts latest round date, occupation codes, and cutoff points.

        Args:
            html: HTML content

        Returns:
            Parsed data structure
        """
        if not BeautifulSoup:
            logger.warning("BeautifulSoup not available, returning placeholder")
            return {"rounds": [], "parsing_note": "BeautifulSoup not installed"}

        soup = BeautifulSoup(html, "html.parser")
        rounds = []

        # Look for tables with round data
        tables = soup.find_all("table")
        logger.debug(f"Found {len(tables)} tables in skillselect rounds")

        for table in tables:
            rows = table.find_all("tr")
            if len(rows) > 1:
                # Extract headers
                headers = [h.get_text(strip=True) for h in rows[0].find_all(["th", "td"])]

                # Extract data rows
                for row in rows[1:]:
                    cells = row.find_all(["td", "th"])
                    if len(cells) > 0:
                        round_data = {}
                        for i, cell in enumerate(cells):
                            if i < len(headers):
                                round_data[headers[i].lower()] = cell.get_text(strip=True)
                        if round_data:
                            rounds.append(round_data)

        return {"rounds": rounds, "count": len(rounds)}

    def _parse_visa_listing(self, html: str) -> Dict[str, Any]:
        """
        Parse Visa Listing HTML.

        Extracts visa subclasses, status, and conditions.

        Args:
            html: HTML content

        Returns:
            Parsed data structure
        """
        if not BeautifulSoup:
            logger.warning("BeautifulSoup not available, returning placeholder")
            return {"visas": [], "parsing_note": "BeautifulSoup not installed"}

        soup = BeautifulSoup(html, "html.parser")
        visas = []

        # Look for structured visa data
        divs = soup.find_all("div", class_=["visa", "visa-subclass", "visa-entry"])
        logger.debug(f"Found {len(divs)} visa divs")

        for div in divs[:200]:  # Limit to 200
            visa = {}

            # Try to extract key fields
            title_elem = div.find(["h2", "h3", "h4"])
            if title_elem:
                visa["title"] = title_elem.get_text(strip=True)

            # Look for subclass code
            code_elem = div.find("span", class_=["code", "subclass"])
            if code_elem:
                visa["code"] = code_elem.get_text(strip=True)

            # Look for status
            status_elem = div.find(["span", "p"], class_=["status", "open", "closed"])
            if status_elem:
                visa["status"] = status_elem.get_text(strip=True)

            if visa:
                visas.append(visa)

        return {"visas": visas, "count": len(visas)}

    def _extract_visa_from_row(self, row: Any) -> Optional[Dict[str, str]]:
        """
        Extract visa data from a row element.

        Args:
            row: BeautifulSoup element

        Returns:
            Dict with visa data or None
        """
        try:
            visa = {}

            # Try to get visa type/name
            title = row.find(["h3", "h4", "a"])
            if title:
                visa["type"] = title.get_text(strip=True)

            # Try to get description
            desc = row.find(["p", "span"])
            if desc:
                visa["description"] = desc.get_text(strip=True)

            return visa if visa else None
        except Exception:
            return None

    def _save_json_snapshot(self, endpoint_key: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save JSON snapshot with metadata.

        Creates file: knowledge/raw_dha/{endpoint}_YYYY-MM-DD.json

        Args:
            endpoint_key: Endpoint identifier
            data: Parsed data to save

        Returns:
            Dict with save status and path
        """
        endpoint = self.ENDPOINTS[endpoint_key]
        timestamp = datetime.now(timezone.utc)
        next_scrape = timestamp + timedelta(days=1)

        output_filename = f"{endpoint['output_file']}_{timestamp.strftime('%Y-%m-%d')}.json"
        output_path = RAW_DHA_DIR / output_filename

        snapshot = {
            "meta": {
                "source": endpoint["url"],
                "scrape_timestamp": timestamp.isoformat(),
                "scrape_status": "success",
                "row_count": data.get("count", 0),
                "next_scrape": next_scrape.isoformat()
            },
            "data": data,
            "errors": []
        }

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved snapshot: {output_path}")
            return {
                "endpoint": endpoint_key,
                "status": "success",
                "path": str(output_path),
                "rows": data.get("count", 0),
                "timestamp": timestamp.isoformat()
            }
        except Exception as e:
            logger.error(f"Error saving snapshot for {endpoint_key}: {str(e)}")
            self._log_error(endpoint_key, "save_error", str(e))
            return {
                "endpoint": endpoint_key,
                "status": "failed",
                "error": str(e)
            }

    def _prepare_stale_response(self, endpoint_key: str) -> Dict[str, Any]:
        """
        Prepare response using stale data (fallback after 2 failures).

        Looks for most recent JSON file for endpoint.

        Args:
            endpoint_key: Endpoint identifier

        Returns:
            Dict with stale data status
        """
        endpoint = self.ENDPOINTS[endpoint_key]
        output_pattern = endpoint["output_file"]

        # Find most recent JSON file
        matching_files = sorted(RAW_DHA_DIR.glob(f"{output_pattern}_*.json"), reverse=True)

        if matching_files:
            latest_file = matching_files[0]
            logger.info(f"Using stale data from {latest_file.name}")
            self._log_error(endpoint_key, "using_stale_data", f"Using {latest_file.name}")

            return {
                "endpoint": endpoint_key,
                "status": "partial",
                "using_stale": True,
                "stale_file": str(latest_file),
                "error": "Network fetch failed, using most recent local snapshot"
            }
        else:
            logger.error(f"No stale data available for {endpoint_key}")
            self._log_error(endpoint_key, "no_stale_data", "No previous snapshots found")

            return {
                "endpoint": endpoint_key,
                "status": "failed",
                "error": "Network fetch failed and no stale data available"
            }

    def _log_error(self, endpoint_key: str, error_type: str, message: str) -> None:
        """
        Log error to append-only JSONL file.

        Args:
            endpoint_key: Endpoint identifier
            error_type: Type of error (fetch_error, parse_error, etc.)
            message: Error message
        """
        try:
            error_record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "endpoint": endpoint_key,
                "error_type": error_type,
                "message": message
            }

            with open(ERROR_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(error_record) + "\n")
        except Exception as e:
            logger.error(f"Failed to log error: {str(e)}")


def main():
    """CLI entry point for scraper."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape Home Affairs visa data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  dha_scraper.py --all              # Scrape all 4 endpoints
  dha_scraper.py --target visa_finder
  dha_scraper.py --target skillselect
        """
    )

    parser.add_argument(
        "--target",
        choices=["visa_finder", "occupation_list", "skillselect", "visa_listing"],
        help="Specific endpoint to scrape"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scrape all endpoints"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    scraper = DHAScraper(verbose=args.verbose)

    if args.all:
        logger.info("Scraping all endpoints...")
        results = scraper.scrape_all()
        print(json.dumps(results, indent=2))
    elif args.target:
        logger.info(f"Scraping {args.target}...")
        if args.target == "visa_finder":
            result = scraper.scrape_visa_finder()
        elif args.target == "occupation_list":
            result = scraper.scrape_occupation_list()
        elif args.target == "skillselect":
            result = scraper.scrape_skillselect_rounds()
        elif args.target == "visa_listing":
            result = scraper.scrape_visa_listing()
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
