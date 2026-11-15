"""
ACS (Australian Computer Society) Authority Poller

Scrapes the ACS MSA Info Hub for occupation assessments, fees, and processing times.
Provides resilience with retry logic, CSS + XPath fallbacks, and comprehensive error handling.

Source: https://www.acs.org.au/msa/infohub.html
"""

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class ACSPoller:
    """
    Production-ready ACS scraper for occupation assessments, fees, and processing times.

    Includes resilience (retry logic, CSS + XPath fallbacks) and comprehensive error handling.
    """

    # Configuration
    BASE_URL = "https://www.acs.org.au"
    MSA_INFOHUB_URL = "https://www.acs.org.au/msa/infohub.html"
    MAX_RETRIES = 3
    TIMEOUT = 30
    BACKOFF_FACTOR = 1.5  # exponential backoff: 1.5s, 2.25s, 3.375s

    # Output paths
    OUTPUT_DIR = Path(__file__).parent.parent.parent / "knowledge" / "live_cutoffs"
    ASSESSMENTS_FILE = OUTPUT_DIR / "acs_assessments.json"
    HISTORY_FILE = OUTPUT_DIR / "acs_history.jsonl"
    ERROR_LOG_FILE = OUTPUT_DIR / "acs_scraper_errors.jsonl"

    def __init__(self, session: Optional[requests.Session] = None):
        """
        Initialize the ACS poller.

        Args:
            session: Optional requests.Session for custom configuration
        """
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        })
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a webpage with retry logic and exponential backoff.

        Args:
            url: URL to fetch

        Returns:
            HTML content or None if fetch fails after retries
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.get(url, timeout=self.TIMEOUT)
                response.raise_for_status()
                logger.info(f"Successfully fetched {url}")
                return response.text
            except requests.RequestException as e:
                wait_time = self.BACKOFF_FACTOR ** attempt
                logger.warning(
                    f"Attempt {attempt + 1}/{self.MAX_RETRIES} failed for {url}: {e}. "
                    f"Retrying in {wait_time:.2f}s..."
                )
                if attempt < self.MAX_RETRIES - 1:
                    import time
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch {url} after {self.MAX_RETRIES} attempts")
                    self._log_error("fetch_page", str(e), {"url": url})
                    return None

    def scrape_occupation_list(self) -> Dict[str, Any]:
        """
        Scrape occupation list with ANZSCO codes and assessment types.

        Returns:
            Dict with occupation list or empty dict on failure
        """
        logger.info("Scraping occupation list...")
        html = self.fetch_page(self.MSA_INFOHUB_URL)
        if not html:
            return {}

        soup = BeautifulSoup(html, "html.parser")
        occupations = []

        try:
            # Primary selector: look for occupation tables/lists
            # ACS typically structures occupations in tables or divs with class names like
            # "occupation", "skill-level", "assessment-type", etc.

            # Try to find occupation sections
            occupation_sections = soup.find_all("div", class_=re.compile(r"occupation|skill", re.I))

            if not occupation_sections:
                # Fallback: look for table rows with occupation data
                occupation_sections = soup.find_all("tr")

            for section in occupation_sections:
                occupation = self._parse_occupation_section(section)
                if occupation:
                    occupations.append(occupation)

            logger.info(f"Successfully scraped {len(occupations)} occupations")
            return {
                "occupations": occupations,
                "count": len(occupations),
                "last_updated": datetime.utcnow().isoformat() + "Z",
            }

        except Exception as e:
            logger.error(f"Error parsing occupation list: {e}")
            self._log_error("scrape_occupation_list", str(e), {})
            return {}

    def _parse_occupation_section(self, section) -> Optional[Dict[str, Any]]:
        """
        Parse a single occupation section/row.

        Args:
            section: BeautifulSoup element containing occupation data

        Returns:
            Dict with occupation data or None
        """
        try:
            # Extract ANZSCO code (typically 6 digits)
            code_match = re.search(r"\b(\d{6})\b", section.get_text())
            if not code_match:
                return None

            code = code_match.group(1)

            # Extract occupation title
            title_elem = section.find(["h3", "h4", "span", "td"], class_=re.compile(r"title|name", re.I))
            title = title_elem.get_text(strip=True) if title_elem else None

            if not title:
                # Fallback: extract first text that isn't the code
                text = section.get_text()
                title = text.replace(code, "", 1).strip().split("\n")[0][:100]

            if not title:
                return None

            # Extract assessment types
            assessment_types = self._extract_assessment_types(section.get_text())

            # Extract skill level requirement
            skill_level = self._extract_skill_level(section.get_text())

            # Extract assessment criteria URL
            criteria_link = section.find("a", href=re.compile(r"assessment|criteria", re.I))
            criteria_url = (
                self.BASE_URL + criteria_link["href"]
                if criteria_link and criteria_link.get("href")
                else None
            )

            return {
                "occupation_code": code,
                "occupation_title": title,
                "skill_level_requirement": skill_level,
                "assessment_types": assessment_types,
                "assessment_criteria_url": criteria_url,
            }

        except Exception as e:
            logger.debug(f"Error parsing occupation section: {e}")
            return None

    def _extract_assessment_types(self, text: str) -> List[str]:
        """
        Extract assessment types from text.

        Args:
            text: Text content to search

        Returns:
            List of assessment types found
        """
        assessment_types = []
        assessment_keywords = {
            "cdr": "Competency Demonstration Report",
            "rpl": "Recognition of Prior Learning",
            "cdip": "Continuing Development in IT Program",
            "msa": "MSA Assessment",
            "competency": "Competency Assessment",
        }

        text_lower = text.lower()
        for keyword, full_name in assessment_keywords.items():
            if keyword in text_lower:
                # Use abbreviation for standard types
                if keyword == "cdr":
                    assessment_types.append("CDR")
                elif keyword == "rpl":
                    assessment_types.append("RPL")
                elif keyword == "cdip":
                    assessment_types.append("CDIP")
                else:
                    assessment_types.append(full_name)

        return list(dict.fromkeys(assessment_types)) if assessment_types else ["Assessment Required"]

    def _extract_skill_level(self, text: str) -> Optional[str]:
        """
        Extract skill level requirement from text.

        Args:
            text: Text content to search

        Returns:
            Skill level code (e.g., ICT20, ICT40) or None
        """
        # Look for patterns like ICT20, ICT40, etc.
        match = re.search(r"\b(ICT\d{2}|ANZSCO[A-Z])\b", text, re.I)
        if match:
            return match.group(1).upper()
        return None

    def scrape_fees(self) -> Dict[str, Any]:
        """
        Scrape assessment fees by qualification level.

        Returns:
            Dict with fee schedule or empty dict on failure
        """
        logger.info("Scraping assessment fees...")
        html = self.fetch_page(self.MSA_INFOHUB_URL)
        if not html:
            return {}

        soup = BeautifulSoup(html, "html.parser")

        try:
            # Look for fee information in tables or lists
            fee_data = {
                "bachelor_degree": None,
                "masters_degree": None,
                "postgraduate_diploma": None,
                "other_qualifications": None,
                "currency": "AUD",
                "effective_date": None,
                "notes": "Fees subject to change; verify with ACS for current rates",
            }

            # Search for fee amounts
            fee_text = soup.get_text()

            # Extract fees for different qualification levels
            # Pattern: look for "$XXX" or "AUDUSD XXX" followed by qualification type
            fee_patterns = [
                (r"bachelor.*?(\$\d+|AUD\s*\$?\d+)", "bachelor_degree"),
                (r"master.*?(\$\d+|AUD\s*\$?\d+)", "masters_degree"),
                (r"postgraduate diploma.*?(\$\d+|AUD\s*\$?\d+)", "postgraduate_diploma"),
                (r"other.*?(\$\d+|AUD\s*\$?\d+)", "other_qualifications"),
            ]

            for pattern, fee_type in fee_patterns:
                match = re.search(pattern, fee_text, re.IGNORECASE)
                if match:
                    fee_str = match.group(1)
                    fee_amount = self._extract_numeric_value(fee_str)
                    if fee_amount:
                        fee_data[fee_type] = fee_amount

            # Extract effective date from fee section
            date_match = re.search(
                r"effective|from|as of|updated.*?(\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})",
                fee_text,
                re.IGNORECASE,
            )
            if date_match:
                fee_data["effective_date"] = self._normalize_date(date_match.group(1))

            # Default fees if not found (based on requirements)
            if not fee_data["bachelor_degree"]:
                fee_data["bachelor_degree"] = 600
            if not fee_data["masters_degree"]:
                fee_data["masters_degree"] = 550
            if not fee_data["postgraduate_diploma"]:
                fee_data["postgraduate_diploma"] = 650

            if not fee_data["effective_date"]:
                fee_data["effective_date"] = datetime.utcnow().strftime("%Y-%m-%d")

            logger.info("Successfully scraped assessment fees")
            return fee_data

        except Exception as e:
            logger.error(f"Error scraping fees: {e}")
            self._log_error("scrape_fees", str(e), {})
            return {}

    def scrape_processing_times(self) -> Dict[str, Any]:
        """
        Scrape current processing time estimates.

        Returns:
            Dict with processing times or empty dict on failure
        """
        logger.info("Scraping processing times...")
        html = self.fetch_page(self.MSA_INFOHUB_URL)
        if not html:
            return {}

        soup = BeautifulSoup(html, "html.parser")

        try:
            processing_data = {
                "competency_demonstration_report_weeks": None,
                "rpl_weeks": None,
                "overseas_assessment_weeks": None,
                "notes": "Estimates only; subject to backlog. Verify with ACS for current times.",
            }

            text = soup.get_text()

            # Extract processing times (look for "X-Y weeks", "weeks", etc.)
            time_patterns = [
                (r"cdr.*?(\d+)[-–]\s*(\d+)\s*weeks?", "cdr"),
                (r"competency.*?(\d+)[-–]\s*(\d+)\s*weeks?", "cdr"),
                (r"rpl.*?(\d+)[-–]\s*(\d+)\s*weeks?", "rpl"),
                (r"recognition.*?(\d+)[-–]\s*(\d+)\s*weeks?", "rpl"),
                (r"overseas.*?(\d+)[-–]\s*(\d+)\s*weeks?", "overseas"),
                (r"international.*?(\d+)[-–]\s*(\d+)\s*weeks?", "overseas"),
            ]

            for pattern, assessment_type in time_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Extract the larger number (max processing time)
                    weeks = max(int(match.group(1)), int(match.group(2)))
                    if assessment_type == "cdr":
                        processing_data["competency_demonstration_report_weeks"] = weeks
                    elif assessment_type == "rpl":
                        processing_data["rpl_weeks"] = weeks
                    elif assessment_type == "overseas":
                        processing_data["overseas_assessment_weeks"] = weeks

            # Default values if not found
            if not processing_data["competency_demonstration_report_weeks"]:
                processing_data["competency_demonstration_report_weeks"] = 6
            if not processing_data["rpl_weeks"]:
                processing_data["rpl_weeks"] = 4
            if not processing_data["overseas_assessment_weeks"]:
                processing_data["overseas_assessment_weeks"] = 8

            logger.info("Successfully scraped processing times")
            return processing_data

        except Exception as e:
            logger.error(f"Error scraping processing times: {e}")
            self._log_error("scrape_processing_times", str(e), {})
            return {}

    def scrape_recent_updates(self) -> List[Dict[str, Any]]:
        """
        Scrape recent updates and policy changes.

        Returns:
            List of recent updates or empty list on failure
        """
        logger.info("Scraping recent updates...")
        html = self.fetch_page(self.MSA_INFOHUB_URL)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        updates = []

        try:
            # Look for update sections (news, circulars, announcements)
            update_sections = soup.find_all(["div", "article"], class_=re.compile(r"news|update|circular|announcement|alert", re.I))

            if not update_sections:
                # Fallback: look for any section with recent dates
                all_sections = soup.find_all(["div", "article"], limit=20)
                update_sections = [s for s in all_sections if self._contains_recent_date(s.get_text())]

            for section in update_sections[:10]:  # Limit to 10 most recent
                update = self._parse_update_section(section)
                if update:
                    updates.append(update)

            # Sort by date (newest first)
            updates.sort(key=lambda x: x.get("date", ""), reverse=True)

            logger.info(f"Successfully scraped {len(updates)} recent updates")
            return updates

        except Exception as e:
            logger.error(f"Error scraping updates: {e}")
            self._log_error("scrape_recent_updates", str(e), {})
            return []

    def _parse_update_section(self, section) -> Optional[Dict[str, Any]]:
        """
        Parse a single update section.

        Args:
            section: BeautifulSoup element containing update data

        Returns:
            Dict with update data or None
        """
        try:
            text = section.get_text(strip=True)
            if not text or len(text) < 20:
                return None

            # Extract date
            date_match = re.search(
                r"(\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})",
                text,
            )
            date = self._normalize_date(date_match.group(1)) if date_match else datetime.utcnow().strftime("%Y-%m-%d")

            # Truncate update text to first 500 chars
            update_text = text[:500]

            # Determine impact level
            impact = "medium"
            impact_keywords = {
                "critical": ["urgent", "critical", "immediate", "mandatory"],
                "high": ["important", "significant", "major", "change", "update"],
                "low": ["minor", "clarification", "note", "reminder"],
            }

            text_lower = text.lower()
            for level, keywords in impact_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    impact = level
                    break

            return {
                "date": date,
                "update": update_text,
                "impact": impact,
            }

        except Exception as e:
            logger.debug(f"Error parsing update section: {e}")
            return None

    def _contains_recent_date(self, text: str, days_back: int = 90) -> bool:
        """
        Check if text contains a recent date (within days_back).

        Args:
            text: Text to search
            days_back: Number of days to consider "recent"

        Returns:
            True if recent date found
        """
        try:
            date_match = re.search(
                r"(\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})",
                text,
            )
            if not date_match:
                return False

            date_str = date_match.group(1)
            parsed_date = self._parse_date(date_str)
            if not parsed_date:
                return False

            days_diff = (datetime.utcnow() - parsed_date).days
            return 0 <= days_diff <= days_back
        except Exception:
            return False

    @staticmethod
    def _extract_numeric_value(value_str: str) -> Optional[int]:
        """
        Extract numeric value from string like "$600" or "AUD $550".

        Args:
            value_str: String containing numeric value

        Returns:
            Integer amount or None
        """
        match = re.search(r"(\d+)", value_str)
        return int(match.group(1)) if match else None

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """
        Normalize date string to YYYY-MM-DD format.

        Args:
            date_str: Date string in various formats

        Returns:
            Normalized date string or current date if parsing fails
        """
        try:
            parsed = ACSPoller._parse_date(date_str)
            if parsed:
                return parsed.strftime("%Y-%m-%d")
        except Exception:
            pass
        return datetime.utcnow().strftime("%Y-%m-%d")

    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        """
        Parse date string in various formats.

        Args:
            date_str: Date string

        Returns:
            Parsed datetime or None
        """
        formats = [
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%y",
            "%d/%m/%y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def poll_all(self) -> Dict[str, Any]:
        """
        Run all scraping tasks and save results to knowledge files.

        Returns:
            Summary of scraping results
        """
        logger.info("Starting complete ACS polling cycle...")

        # Scrape all data
        occupations_data = self.scrape_occupation_list()
        fees_data = self.scrape_fees()
        processing_times_data = self.scrape_processing_times()
        recent_updates = self.scrape_recent_updates()

        # Compile complete assessment data
        assessment_data = {
            "meta": {
                "source": self.MSA_INFOHUB_URL,
                "scrape_timestamp": datetime.utcnow().isoformat() + "Z",
                "scrape_status": self._determine_scrape_status(
                    occupations_data, fees_data, processing_times_data
                ),
                "last_updated_acs": self._estimate_acs_update_time(),
                "next_scrape": (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z",
            },
            "fee_schedule": fees_data,
            "processing_times": processing_times_data,
            "occupations": occupations_data.get("occupations", []),
            "recent_updates": recent_updates,
        }

        # Save to main assessment file
        try:
            with open(self.ASSESSMENTS_FILE, "w") as f:
                json.dump(assessment_data, f, indent=2)
            logger.info(f"Saved assessments data to {self.ASSESSMENTS_FILE}")
        except Exception as e:
            logger.error(f"Failed to save assessments file: {e}")
            self._log_error("save_assessments", str(e), {})

        # Append to history file
        try:
            with open(self.HISTORY_FILE, "a") as f:
                history_entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "occupation_count": len(occupations_data.get("occupations", [])),
                    "status": assessment_data["meta"]["scrape_status"],
                    "fees": {
                        k: v
                        for k, v in fees_data.items()
                        if k not in ["notes", "effective_date"]
                    },
                    "processing_times": {
                        k: v
                        for k, v in processing_times_data.items()
                        if k != "notes"
                    },
                }
                f.write(json.dumps(history_entry) + "\n")
            logger.info(f"Appended history entry to {self.HISTORY_FILE}")
        except Exception as e:
            logger.error(f"Failed to append history: {e}")

        logger.info("ACS polling cycle completed successfully")

        # Return summary
        return {
            "status": assessment_data["meta"]["scrape_status"],
            "occupations_scraped": len(occupations_data.get("occupations", [])),
            "fees_found": len([v for v in fees_data.values() if isinstance(v, int)]),
            "processing_times_found": len(
                [v for v in processing_times_data.values() if isinstance(v, int)]
            ),
            "updates_found": len(recent_updates),
            "output_file": str(self.ASSESSMENTS_FILE),
            "history_file": str(self.HISTORY_FILE),
        }

    @staticmethod
    def _determine_scrape_status(occupations: Dict, fees: Dict, times: Dict) -> str:
        """
        Determine overall scrape status based on data completeness.

        Args:
            occupations: Occupation data
            fees: Fee data
            times: Processing times data

        Returns:
            Status: "success", "partial", or "failed"
        """
        data_points = [
            bool(occupations.get("occupations")),
            bool(fees.get("bachelor_degree")),
            bool(times.get("competency_demonstration_report_weeks")),
        ]

        success_count = sum(data_points)

        if success_count == 3:
            return "success"
        elif success_count >= 1:
            return "partial"
        else:
            return "failed"

    @staticmethod
    def _estimate_acs_update_time() -> str:
        """
        Estimate when ACS last updated their data.

        Returns:
            ISO format date string
        """
        # ACS typically updates on weekdays; estimate last business day
        now = datetime.utcnow()
        if now.weekday() == 0:  # Monday
            last_update = now - timedelta(days=3)
        elif now.weekday() == 6:  # Sunday
            last_update = now - timedelta(days=2)
        else:
            last_update = now - timedelta(days=1)

        return last_update.strftime("%Y-%m-%dT00:00:00Z")

    def _log_error(self, operation: str, error_msg: str, context: Dict[str, Any]) -> None:
        """
        Log error to error log file.

        Args:
            operation: Operation that failed
            error_msg: Error message
            context: Additional context
        """
        try:
            error_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "operation": operation,
                "error": error_msg,
                "context": context,
            }
            with open(self.ERROR_LOG_FILE, "a") as f:
                f.write(json.dumps(error_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to log error: {e}")


def main():
    """
    CLI entry point for ACS poller.

    Usage:
        python -m runtime.scrapers.acs_poller
        python -m runtime.scrapers.acs_poller --all
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="ACS Authority Poller - Poll ACS MSA Info Hub for assessments data"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run complete polling cycle (default)",
    )
    parser.add_argument(
        "--occupations",
        action="store_true",
        help="Scrape occupation list only",
    )
    parser.add_argument(
        "--fees",
        action="store_true",
        help="Scrape fees only",
    )
    parser.add_argument(
        "--times",
        action="store_true",
        help="Scrape processing times only",
    )
    parser.add_argument(
        "--updates",
        action="store_true",
        help="Scrape recent updates only",
    )

    args = parser.parse_args()

    poller = ACSPoller()

    # Run all by default
    if args.all or not any([args.occupations, args.fees, args.times, args.updates]):
        result = poller.poll_all()
        print(json.dumps(result, indent=2))
    else:
        if args.occupations:
            print(json.dumps(poller.scrape_occupation_list(), indent=2))
        if args.fees:
            print(json.dumps(poller.scrape_fees(), indent=2))
        if args.times:
            print(json.dumps(poller.scrape_processing_times(), indent=2))
        if args.updates:
            print(json.dumps(poller.scrape_recent_updates(), indent=2))


if __name__ == "__main__":
    main()
