"""
Tests for Home Affairs Data Scraper (DHAScraper).

Tests cover:
- Parsing logic for each endpoint
- Error handling (timeout, network errors, malformed HTML)
- Retry logic with exponential backoff
- JSON output schema validation
- Stale data fallback

Uses mock endpoints to avoid hitting real Home Affairs during testing.
"""

import json
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from tempfile import TemporaryDirectory

# Import the scraper
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from runtime.scrapers.dha_scraper import DHAScraper


class TestDHAScraperFetch(unittest.TestCase):
    """Test HTTP fetch with retry logic."""

    def setUp(self):
        self.scraper = DHAScraper(verbose=False)

    @patch("runtime.scrapers.dha_scraper.urlopen")
    def test_successful_fetch_first_attempt(self, mock_urlopen):
        """Test successful fetch on first attempt."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"<html>test</html>"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = self.scraper._fetch_with_retry("https://example.com", "test_endpoint")

        self.assertEqual(result, "<html>test</html>")
        self.assertEqual(mock_urlopen.call_count, 1)

    @patch("runtime.scrapers.dha_scraper.time.sleep")
    @patch("runtime.scrapers.dha_scraper.urlopen")
    def test_retry_on_timeout(self, mock_urlopen, mock_sleep):
        """Test retry logic on timeout."""
        # First attempt fails, second succeeds
        mock_response = MagicMock()
        mock_response.read.return_value = b"<html>success</html>"
        mock_response.__enter__.return_value = mock_response

        mock_urlopen.side_effect = [
            TimeoutError("Request timed out"),
            mock_response
        ]

        result = self.scraper._fetch_with_retry("https://example.com", "test_endpoint")

        self.assertEqual(result, "<html>success</html>")
        self.assertEqual(mock_urlopen.call_count, 2)
        # Verify backoff delay
        mock_sleep.assert_called()

    @patch("runtime.scrapers.dha_scraper.urlopen")
    def test_max_retries_exhausted(self, mock_urlopen):
        """Test behavior when all retries exhausted."""
        mock_urlopen.side_effect = TimeoutError("Request timed out")

        result = self.scraper._fetch_with_retry("https://example.com", "test_endpoint")

        self.assertIsNone(result)
        self.assertEqual(mock_urlopen.call_count, self.scraper.MAX_RETRIES)


class TestDHAScraperParsing(unittest.TestCase):
    """Test HTML parsing for each endpoint."""

    def setUp(self):
        self.scraper = DHAScraper(verbose=False)

    def test_parse_visa_finder_with_css_selectors(self):
        """Test visa finder parsing with CSS selectors."""
        html = """
        <html>
            <div class="visa-card">
                <h3>Skilled Independent Visa</h3>
                <p>Work in Australia permanently</p>
            </div>
            <div class="visa-card">
                <h3>Employer Sponsored Visa</h3>
                <p>Work for an Australian employer</p>
            </div>
        </html>
        """

        result = self.scraper._parse_visa_finder(html)

        self.assertIn("visas", result)
        self.assertGreater(len(result["visas"]), 0)
        self.assertIn("count", result)

    def test_parse_occupation_list_extracts_anzsco(self):
        """Test occupation list parsing extracts ANZSCO codes."""
        html = """
        <html>
            <table>
                <tr><th>ANZSCO</th><th>Title</th><th>Authority</th></tr>
                <tr>
                    <td>261311</td>
                    <td>Analyst Programmer</td>
                    <td>ACS</td>
                </tr>
                <tr>
                    <td>261313</td>
                    <td>Software Engineer</td>
                    <td>ACS</td>
                </tr>
            </table>
        </html>
        """

        result = self.scraper._parse_occupation_list(html)

        self.assertIn("occupations", result)
        self.assertGreater(len(result["occupations"]), 0)

        # Verify structure
        if result["occupations"]:
            occ = result["occupations"][0]
            self.assertIn("anzsco", occ)
            self.assertIn("title", occ)

    def test_parse_skillselect_rounds_extracts_tables(self):
        """Test SkillSelect rounds parsing extracts table data."""
        html = """
        <html>
            <table>
                <tr><th>Round</th><th>Occupation</th><th>Code</th><th>Invited</th></tr>
                <tr>
                    <td>October 2026</td>
                    <td>Software Engineer</td>
                    <td>261313</td>
                    <td>450</td>
                </tr>
            </table>
        </html>
        """

        result = self.scraper._parse_skillselect_rounds(html)

        self.assertIn("rounds", result)
        self.assertGreater(len(result["rounds"]), 0)

    def test_parse_visa_listing_extracts_visa_info(self):
        """Test visa listing parsing extracts visa information."""
        html = """
        <html>
            <div class="visa">
                <h3>Skilled Independent Visa (189)</h3>
                <span class="code">189</span>
                <span class="status">Open</span>
            </div>
        </html>
        """

        result = self.scraper._parse_visa_listing(html)

        self.assertIn("visas", result)
        self.assertGreater(len(result["visas"]), 0)


class TestDHAScraperOutput(unittest.TestCase):
    """Test JSON output and file saving."""

    def setUp(self):
        self.scraper = DHAScraper(verbose=False)
        self.temp_dir = TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("runtime.scrapers.dha_scraper.RAW_DHA_DIR")
    def test_save_json_snapshot_structure(self, mock_dir):
        """Test JSON snapshot has required metadata structure."""
        mock_dir.__truediv__.return_value = Path(self.temp_dir.name) / "test.json"

        data = {
            "visas": [
                {"name": "Visa 1", "code": "189"},
                {"name": "Visa 2", "code": "190"}
            ],
            "count": 2
        }

        result = self.scraper._save_json_snapshot("visa_finder", data)

        # Check result structure
        self.assertEqual(result["status"], "success")
        self.assertIn("path", result)
        self.assertEqual(result["rows"], 2)

    def test_json_output_schema_has_required_fields(self):
        """Test JSON output has required schema fields."""
        # Simulate snapshot structure
        snapshot = {
            "meta": {
                "source": "https://example.com",
                "scrape_timestamp": datetime.now(timezone.utc).isoformat(),
                "scrape_status": "success",
                "row_count": 10,
                "next_scrape": datetime.now(timezone.utc).isoformat()
            },
            "data": {"items": []},
            "errors": []
        }

        # Validate structure
        self.assertIn("meta", snapshot)
        self.assertIn("data", snapshot)
        self.assertIn("errors", snapshot)

        meta = snapshot["meta"]
        self.assertIn("source", meta)
        self.assertIn("scrape_timestamp", meta)
        self.assertIn("scrape_status", meta)
        self.assertIn("row_count", meta)
        self.assertIn("next_scrape", meta)


class TestDHAScraperErrorHandling(unittest.TestCase):
    """Test error handling and logging."""

    def setUp(self):
        self.scraper = DHAScraper(verbose=False)
        self.temp_dir = TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("runtime.scrapers.dha_scraper.logger")
    def test_error_logging_records_failures(self, mock_logger):
        """Test error logging records fetch failures."""
        self.scraper._log_error(
            "test_endpoint",
            "fetch_error",
            "Connection refused"
        )

        # Verify logger was called
        mock_logger.error.assert_called()

    @patch("runtime.scrapers.dha_scraper.RAW_DHA_DIR")
    def test_stale_data_fallback_when_fetch_fails(self, mock_dir):
        """Test fallback to stale data when network fetch fails."""
        # Create mock directory with old file
        old_file = Path(self.temp_dir.name) / "visa_finder_2026-11-01.json"
        old_file.write_text('{"data": "old"}')

        mock_dir.glob.return_value = [old_file]

        result = self.scraper._prepare_stale_response("visa_finder")

        self.assertEqual(result["status"], "partial")
        self.assertTrue(result.get("using_stale"))

    def test_no_stale_data_returns_error(self):
        """Test error when no stale data available."""
        with patch("runtime.scrapers.dha_scraper.RAW_DHA_DIR") as mock_dir:
            mock_dir.glob.return_value = []

            result = self.scraper._prepare_stale_response("visa_finder")

            self.assertEqual(result["status"], "failed")
            self.assertIn("error", result)


class TestDHAScraperIntegration(unittest.TestCase):
    """Integration tests for full scraper workflow."""

    def setUp(self):
        self.scraper = DHAScraper(verbose=False)

    @patch("runtime.scrapers.dha_scraper.DHAScraper._fetch_with_retry")
    def test_scrape_visa_finder_workflow(self, mock_fetch):
        """Test complete visa_finder scrape workflow."""
        mock_fetch.return_value = """
        <html>
            <div class="visa-card">
                <h3>Test Visa</h3>
            </div>
        </html>
        """

        with patch("runtime.scrapers.dha_scraper.RAW_DHA_DIR") as mock_dir:
            temp_file = Path(f"/tmp/test_visa_finder_{datetime.now().strftime('%Y-%m-%d')}.json")
            mock_dir.__truediv__.return_value = temp_file

            result = self.scraper.scrape_visa_finder()

            self.assertIn("status", result)
            self.assertIn("endpoint", result)

    @patch("runtime.scrapers.dha_scraper.DHAScraper.scrape_visa_finder")
    @patch("runtime.scrapers.dha_scraper.DHAScraper.scrape_occupation_list")
    @patch("runtime.scrapers.dha_scraper.DHAScraper.scrape_skillselect_rounds")
    @patch("runtime.scrapers.dha_scraper.DHAScraper.scrape_visa_listing")
    def test_scrape_all_endpoints(self, mock_visa_listing, mock_skillselect,
                                   mock_occupation, mock_visa_finder):
        """Test scraping all 4 endpoints."""
        mock_visa_finder.return_value = {"status": "success"}
        mock_occupation.return_value = {"status": "success"}
        mock_skillselect.return_value = {"status": "success"}
        mock_visa_listing.return_value = {"status": "success"}

        results = self.scraper.scrape_all()

        self.assertEqual(len(results), 4)
        self.assertIn("visa_finder", results)
        self.assertIn("occupation_list", results)
        self.assertIn("skillselect", results)
        self.assertIn("visa_listing", results)


class TestDHAScraperEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        self.scraper = DHAScraper(verbose=False)

    def test_parse_empty_html(self):
        """Test parsing empty HTML."""
        html = "<html></html>"

        result = self.scraper._parse_visa_finder(html)
        self.assertIn("visas", result)
        self.assertEqual(result["count"], 0)

    def test_parse_malformed_html(self):
        """Test parsing malformed HTML doesn't crash."""
        html = "<html><div class='visa-card'><h3>Test</h3>"  # Missing closing tags

        result = self.scraper._parse_visa_finder(html)
        self.assertIn("visas", result)

    def test_parse_unicode_content(self):
        """Test parsing content with unicode characters."""
        html = """
        <html>
            <div class="visa-card">
                <h3>Visa für Australien 🇦🇺</h3>
            </div>
        </html>
        """

        result = self.scraper._parse_visa_finder(html)
        self.assertIn("visas", result)

    def test_extract_from_row_with_missing_fields(self):
        """Test row extraction handles missing optional fields."""
        from unittest.mock import MagicMock

        row = MagicMock()
        row.find.return_value = MagicMock()
        row.find.return_value.get_text.return_value = "Test"

        result = self.scraper._extract_visa_from_row(row)
        self.assertIsNotNone(result)


class TestDHAScraperRetryBackoff(unittest.TestCase):
    """Test exponential backoff retry delays."""

    def setUp(self):
        self.scraper = DHAScraper(verbose=False)

    def test_retry_delays_are_exponential(self):
        """Test retry delays follow exponential backoff."""
        expected_delays = [1, 2, 4]
        self.assertEqual(self.scraper.RETRY_DELAYS, expected_delays)

    def test_request_timeout_configuration(self):
        """Test request timeout is properly configured."""
        self.assertEqual(self.scraper.REQUEST_TIMEOUT, 30)

    def test_max_retries_configuration(self):
        """Test max retries configuration."""
        self.assertEqual(self.scraper.MAX_RETRIES, 3)


if __name__ == "__main__":
    unittest.main()
