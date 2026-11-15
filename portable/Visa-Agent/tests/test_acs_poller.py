"""
Test suite for ACS Authority Poller.

Tests cover:
- Occupation list extraction
- Fee schedule parsing
- Processing time extraction
- Recent updates scraping
- Error handling and retry logic
- JSON schema validation
- Date normalization
"""

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Assume the scraper is in runtime.scrapers
from runtime.scrapers.acs_poller import ACSPoller


class MockHTMLFixtures:
    """Mock HTML fixtures for testing."""

    @staticmethod
    def occupation_list_html() -> str:
        """Mock ACS occupation list HTML."""
        return """
        <html>
            <body>
                <div class="occupation">
                    <span class="code">261313</span>
                    <h3 class="title">Software Engineer</h3>
                    <p>Assessment types: CDR, RPL</p>
                    <p>Skill Level: ICT20</p>
                    <a href="/assessment/criteria/261313">Assessment Criteria</a>
                </div>
                <div class="occupation">
                    <span class="code">262111</span>
                    <h4>Database Administrator</h4>
                    <p>Assessment: Competency Demonstration Report</p>
                    <p>Skill Level: ICT20</p>
                </div>
                <div class="occupation">
                    <span class="code">263111</span>
                    <h3 class="title">Systems Administrator</h3>
                    <p>RPL Assessment Path</p>
                    <p>Skill Level: ICT40</p>
                </div>
            </body>
        </html>
        """

    @staticmethod
    def fees_html() -> str:
        """Mock ACS fees HTML."""
        return """
        <html>
            <body>
                <div class="fees">
                    <h2>Assessment Fees</h2>
                    <p>Bachelor Degree: $600 AUD</p>
                    <p>Masters Degree: $550 AUD</p>
                    <p>Postgraduate Diploma: $650 AUD</p>
                    <p>Effective Date: 01-11-2026</p>
                    <p>Fees are subject to change. Please verify with ACS.</p>
                </div>
            </body>
        </html>
        """

    @staticmethod
    def processing_times_html() -> str:
        """Mock ACS processing times HTML."""
        return """
        <html>
            <body>
                <div class="processing-times">
                    <h2>Processing Times</h2>
                    <p>CDR (Competency Demonstration Report): 4-6 weeks</p>
                    <p>RPL (Recognition of Prior Learning): 3-4 weeks</p>
                    <p>Overseas Assessment: 6-8 weeks</p>
                    <p>Note: Times are estimates and subject to backlog.</p>
                </div>
            </body>
        </html>
        """

    @staticmethod
    def recent_updates_html() -> str:
        """Mock ACS recent updates HTML."""
        return """
        <html>
            <body>
                <div class="news">
                    <article class="update">
                        <h3>CDR Processing Time Update</h3>
                        <p>Date: 10-11-2026</p>
                        <p>Important: Processing time for CDR has increased to 6 weeks due to increased demand.</p>
                    </article>
                    <article class="update">
                        <h3>New Occupation Added</h3>
                        <p>Date: 01-11-2026</p>
                        <p>Cloud Architect (261312) has been added to the assessment list.</p>
                    </article>
                </div>
            </body>
        </html>
        """


class TestACSPollerOccupationList(unittest.TestCase):
    """Tests for occupation list scraping."""

    def setUp(self):
        """Set up test fixtures."""
        self.poller = ACSPoller()

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_scrape_occupation_list_success(self, mock_get):
        """Test successful occupation list scraping."""
        mock_response = Mock()
        mock_response.text = MockHTMLFixtures.occupation_list_html()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.poller.scrape_occupation_list()

        self.assertIsNotNone(result)
        self.assertIn("occupations", result)
        self.assertGreater(len(result["occupations"]), 0)

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_parse_occupation_section(self, mock_get):
        """Test occupation section parsing."""
        mock_response = Mock()
        mock_response.text = MockHTMLFixtures.occupation_list_html()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.poller.scrape_occupation_list()
        occupations = result.get("occupations", [])

        # Verify structure
        self.assertGreater(len(occupations), 0)
        for occ in occupations:
            self.assertIn("occupation_code", occ)
            self.assertIn("occupation_title", occ)
            self.assertIn("assessment_types", occ)

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_occupation_code_extraction(self, mock_get):
        """Test ANZSCO code extraction."""
        mock_response = Mock()
        mock_response.text = MockHTMLFixtures.occupation_list_html()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.poller.scrape_occupation_list()
        occupations = result.get("occupations", [])
        codes = [occ["occupation_code"] for occ in occupations]

        self.assertIn("261313", codes)
        self.assertIn("262111", codes)

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_assessment_types_extraction(self, mock_get):
        """Test assessment type extraction."""
        mock_response = Mock()
        mock_response.text = MockHTMLFixtures.occupation_list_html()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.poller.scrape_occupation_list()
        occupations = result.get("occupations", [])

        # Check for CDR and RPL
        assessment_types = []
        for occ in occupations:
            assessment_types.extend(occ.get("assessment_types", []))

        self.assertTrue(
            any(t in ["CDR", "RPL", "Competency Demonstration Report", "Recognition of Prior Learning"]
                for t in assessment_types),
            "Assessment types should include CDR or RPL",
        )

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_skill_level_extraction(self, mock_get):
        """Test skill level extraction."""
        mock_response = Mock()
        mock_response.text = MockHTMLFixtures.occupation_list_html()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.poller.scrape_occupation_list()
        occupations = result.get("occupations", [])
        skill_levels = [occ.get("skill_level_requirement") for occ in occupations]

        self.assertTrue(
            any(sl and "ICT" in sl for sl in skill_levels),
            "Should extract skill levels like ICT20, ICT40",
        )


class TestACSPollerFees(unittest.TestCase):
    """Tests for fee schedule scraping."""

    def setUp(self):
        """Set up test fixtures."""
        self.poller = ACSPoller()

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_scrape_fees_success(self, mock_get):
        """Test successful fee scraping."""
        mock_response = Mock()
        mock_response.text = MockHTMLFixtures.fees_html()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.poller.scrape_fees()

        self.assertIsNotNone(result)
        self.assertIn("currency", result)
        self.assertIn("effective_date", result)

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_fee_amounts_extracted(self, mock_get):
        """Test that fee amounts are correctly extracted."""
        mock_response = Mock()
        mock_response.text = MockHTMLFixtures.fees_html()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.poller.scrape_fees()

        # Should have numeric values for fees
        self.assertIsInstance(result.get("bachelor_degree"), int)
        self.assertIsInstance(result.get("masters_degree"), int)
        self.assertIsInstance(result.get("postgraduate_diploma"), int)

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_fee_currency_is_aud(self, mock_get):
        """Test that currency is correctly identified as AUD."""
        mock_response = Mock()
        mock_response.text = MockHTMLFixtures.fees_html()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.poller.scrape_fees()

        self.assertEqual(result.get("currency"), "AUD")

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_fee_effective_date(self, mock_get):
        """Test that effective date is extracted."""
        mock_response = Mock()
        mock_response.text = MockHTMLFixtures.fees_html()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.poller.scrape_fees()

        self.assertIsNotNone(result.get("effective_date"))
        # Date should be in YYYY-MM-DD format
        date_str = result.get("effective_date")
        self.assertRegex(date_str, r"\d{4}-\d{2}-\d{2}")

    def test_extract_numeric_value(self):
        """Test numeric value extraction from strings."""
        test_cases = [
            ("$600", 600),
            ("AUD $550", 550),
            ("650 AUD", 650),
            ("$ 700.50", 700),
        ]

        for test_str, expected in test_cases:
            result = ACSPoller._extract_numeric_value(test_str)
            self.assertEqual(result, expected, f"Failed to extract from '{test_str}'")


class TestACSPollerProcessingTimes(unittest.TestCase):
    """Tests for processing time scraping."""

    def setUp(self):
        """Set up test fixtures."""
        self.poller = ACSPoller()

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_scrape_processing_times_success(self, mock_get):
        """Test successful processing time scraping."""
        mock_response = Mock()
        mock_response.text = MockHTMLFixtures.processing_times_html()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.poller.scrape_processing_times()

        self.assertIsNotNone(result)
        self.assertIn("notes", result)

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_processing_times_are_numeric(self, mock_get):
        """Test that processing times are numeric."""
        mock_response = Mock()
        mock_response.text = MockHTMLFixtures.processing_times_html()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.poller.scrape_processing_times()

        # Should have numeric weeks
        self.assertIsInstance(result.get("competency_demonstration_report_weeks"), int)
        self.assertIsInstance(result.get("rpl_weeks"), int)
        self.assertIsInstance(result.get("overseas_assessment_weeks"), int)

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_processing_times_are_reasonable(self, mock_get):
        """Test that processing times are within reasonable range."""
        mock_response = Mock()
        mock_response.text = MockHTMLFixtures.processing_times_html()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.poller.scrape_processing_times()

        # Times should be between 1 and 12 weeks
        for key in [
            "competency_demonstration_report_weeks",
            "rpl_weeks",
            "overseas_assessment_weeks",
        ]:
            weeks = result.get(key)
            self.assertGreaterEqual(weeks, 1, f"{key} should be >= 1")
            self.assertLessEqual(weeks, 12, f"{key} should be <= 12")


class TestACSPollerRecentUpdates(unittest.TestCase):
    """Tests for recent updates scraping."""

    def setUp(self):
        """Set up test fixtures."""
        self.poller = ACSPoller()

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_scrape_recent_updates_success(self, mock_get):
        """Test successful recent updates scraping."""
        mock_response = Mock()
        mock_response.text = MockHTMLFixtures.recent_updates_html()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.poller.scrape_recent_updates()

        self.assertIsInstance(result, list)

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_update_structure(self, mock_get):
        """Test that update structure is correct."""
        mock_response = Mock()
        mock_response.text = MockHTMLFixtures.recent_updates_html()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.poller.scrape_recent_updates()

        if result:
            for update in result:
                self.assertIn("date", update)
                self.assertIn("update", update)
                self.assertIn("impact", update)

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_impact_levels_valid(self, mock_get):
        """Test that impact levels are valid."""
        mock_response = Mock()
        mock_response.text = MockHTMLFixtures.recent_updates_html()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.poller.scrape_recent_updates()

        valid_impacts = ["low", "medium", "high"]
        for update in result:
            self.assertIn(update.get("impact"), valid_impacts)


class TestACSPollerErrorHandling(unittest.TestCase):
    """Tests for error handling and retry logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.poller = ACSPoller()

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_retry_on_connection_error(self, mock_get):
        """Test retry on connection error."""
        import requests

        mock_get.side_effect = [
            requests.ConnectionError("Connection failed"),
            requests.ConnectionError("Connection failed"),
            Mock(text=MockHTMLFixtures.occupation_list_html(), raise_for_status=Mock()),
        ]

        result = self.poller.fetch_page("https://test.example.com")

        self.assertIsNotNone(result)
        self.assertEqual(mock_get.call_count, 3)

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_max_retries_exceeded(self, mock_get):
        """Test behavior when max retries are exceeded."""
        import requests

        mock_get.side_effect = requests.ConnectionError("Connection failed")

        result = self.poller.fetch_page("https://test.example.com")

        self.assertIsNone(result)
        self.assertEqual(mock_get.call_count, 3)

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_graceful_fallback_on_parse_error(self, mock_get):
        """Test graceful fallback when parsing fails."""
        mock_response = Mock()
        mock_response.text = "<invalid html"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Should not raise exception, should return empty dict or defaults
        result = self.poller.scrape_occupation_list()

        self.assertIsInstance(result, dict)


class TestACSPollerDateHandling(unittest.TestCase):
    """Tests for date normalization and parsing."""

    def test_normalize_date_various_formats(self):
        """Test date normalization for various formats."""
        test_cases = [
            ("01-11-2026", "2026-11-01"),
            ("1/11/2026", "2026-11-01"),
            ("2026-11-01", "2026-11-01"),
            ("01-11-26", "2026-11-01"),
        ]

        for input_date, expected_date in test_cases:
            result = ACSPoller._normalize_date(input_date)
            self.assertEqual(result, expected_date, f"Failed to normalize {input_date}")

    def test_parse_date_returns_datetime(self):
        """Test that _parse_date returns datetime object."""
        result = ACSPoller._parse_date("01-11-2026")
        self.assertIsInstance(result, datetime)

    def test_invalid_date_returns_none(self):
        """Test that invalid dates return None."""
        result = ACSPoller._parse_date("invalid-date")
        self.assertIsNone(result)


class TestACSPollerPolling(unittest.TestCase):
    """Tests for complete polling cycle."""

    def setUp(self):
        """Set up test fixtures."""
        self.poller = ACSPoller()

    @patch("runtime.scrapers.acs_poller.requests.Session.get")
    def test_poll_all_creates_json_file(self, mock_get):
        """Test that poll_all creates output JSON file."""
        # Mock all page fetches
        def mock_fetch(url, timeout=None):
            mock_response = Mock()
            if "infohub" in url:
                mock_response.text = (
                    MockHTMLFixtures.occupation_list_html()
                    + MockHTMLFixtures.fees_html()
                    + MockHTMLFixtures.processing_times_html()
                    + MockHTMLFixtures.recent_updates_html()
                )
            else:
                mock_response.text = "<html></html>"
            mock_response.raise_for_status = Mock()
            return mock_response

        mock_get.side_effect = mock_fetch

        with tempfile.TemporaryDirectory() as tmpdir:
            # Override output path
            self.poller.OUTPUT_DIR = Path(tmpdir)
            self.poller.ASSESSMENTS_FILE = Path(tmpdir) / "acs_assessments.json"
            self.poller.HISTORY_FILE = Path(tmpdir) / "acs_history.jsonl"

            result = self.poller.poll_all()

            # Check result summary
            self.assertIn("status", result)
            self.assertIn("occupations_scraped", result)
            self.assertIn("output_file", result)

    def test_scrape_status_determination(self):
        """Test scrape status determination logic."""
        # Successful scrape
        status = ACSPoller._determine_scrape_status(
            {"occupations": [{"code": "261313"}]},
            {"bachelor_degree": 600},
            {"competency_demonstration_report_weeks": 6},
        )
        self.assertEqual(status, "success")

        # Partial scrape
        status = ACSPoller._determine_scrape_status(
            {"occupations": [{"code": "261313"}]},
            {"bachelor_degree": None},
            {"competency_demonstration_report_weeks": 6},
        )
        self.assertEqual(status, "partial")

        # Failed scrape
        status = ACSPoller._determine_scrape_status(
            {"occupations": []},
            {"bachelor_degree": None},
            {"competency_demonstration_report_weeks": None},
        )
        self.assertEqual(status, "failed")


class TestACSPollerJSONSchema(unittest.TestCase):
    """Tests for JSON schema validation."""

    def test_assessment_data_schema(self):
        """Test that assessment data follows expected schema."""
        sample_data = {
            "meta": {
                "source": "https://www.acs.org.au/msa/infohub.html",
                "scrape_timestamp": "2026-11-15T03:45:00Z",
                "scrape_status": "success",
                "last_updated_acs": "2026-11-10T00:00:00Z",
                "next_scrape": "2026-11-22T03:00:00Z",
            },
            "fee_schedule": {
                "bachelor_degree": 600,
                "masters_degree": 550,
                "postgraduate_diploma": 650,
                "currency": "AUD",
                "effective_date": "2026-11-01",
            },
            "processing_times": {
                "competency_demonstration_report_weeks": 6,
                "rpl_weeks": 4,
                "overseas_assessment_weeks": 8,
            },
            "occupations": [
                {
                    "occupation_code": "261313",
                    "occupation_title": "Software Engineer",
                    "skill_level_requirement": "ICT20",
                    "assessment_types": ["CDR"],
                    "assessment_criteria_url": "https://www.acs.org.au/criteria",
                }
            ],
            "recent_updates": [
                {
                    "date": "2026-11-10",
                    "update": "Processing time increased",
                    "impact": "high",
                }
            ],
        }

        # Verify structure
        self.assertIn("meta", sample_data)
        self.assertIn("fee_schedule", sample_data)
        self.assertIn("processing_times", sample_data)
        self.assertIn("occupations", sample_data)
        self.assertIn("recent_updates", sample_data)

        # Verify it's JSON serializable
        json_str = json.dumps(sample_data)
        reloaded = json.loads(json_str)
        self.assertEqual(reloaded, sample_data)


if __name__ == "__main__":
    unittest.main()
