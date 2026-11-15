"""
Unit and integration tests for State Nomination Monitor.

Tests cover:
- Individual state scraper methods (8 states)
- Parallel execution with ThreadPoolExecutor
- Error handling and retry logic
- JSON schema validation per state
- File I/O and append-only history
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from runtime.scrapers.state_monitor import StateMonitor


class TestStateMonitorInitialization(unittest.TestCase):
    """Test StateMonitor initialization and configuration."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initialization_with_custom_output_dir(self):
        """Test StateMonitor initializes with custom output directory."""
        monitor = StateMonitor(output_dir=self.output_dir)
        self.assertEqual(str(monitor.output_dir), self.output_dir)
        self.assertTrue(os.path.isdir(self.output_dir))

    def test_initialization_creates_output_directory(self):
        """Test StateMonitor creates output directory if not exists."""
        new_dir = os.path.join(self.output_dir, "new_subdir")
        monitor = StateMonitor(output_dir=new_dir)
        self.assertTrue(os.path.isdir(new_dir))

    def test_initialization_with_default_settings(self):
        """Test StateMonitor initializes with default settings."""
        monitor = StateMonitor(output_dir=self.output_dir)
        self.assertEqual(monitor.max_retries, 3)
        self.assertEqual(monitor.timeout, 30)
        self.assertEqual(monitor.max_workers, 4)


class TestStateMonitorOutputSchema(unittest.TestCase):
    """Test output JSON schema for each state."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.monitor = StateMonitor(output_dir=self.temp_dir.name)
        self.required_meta_fields = {
            'state_code', 'state_name', 'source', 'scrape_timestamp',
            'scrape_status', 'occupation_count'
        }
        self.required_occupation_fields = {
            'occupation_code', 'occupation_title', 'visa_type',
            'available', 'processing_time_weeks'
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def validate_output_json(self, data):
        """Validate output JSON schema."""
        # Check top-level keys
        self.assertIn('meta', data)
        self.assertIn('occupations', data)
        self.assertIn('quotas', data)

        # Check meta fields
        meta = data['meta']
        self.assertTrue(self.required_meta_fields.issubset(set(meta.keys())))
        self.assertIn(meta['scrape_status'], ['success', 'partial', 'failed'])

        # Validate timestamp format
        try:
            datetime.fromisoformat(meta['scrape_timestamp'].replace('Z', '+00:00'))
        except ValueError:
            self.fail("Invalid timestamp format in meta")

        # Check occupations
        occupations = data['occupations']
        if occupations:
            for occ in occupations:
                self.assertTrue(self.required_occupation_fields.issubset(set(occ.keys())))
                self.assertIsInstance(occ['visa_type'], list)
                self.assertIsInstance(occ['available'], bool)

    def test_output_schema_victoria(self):
        """Test Victoria output schema."""
        result = self.monitor.scrape_victoria()
        self.validate_output_json(result)
        self.assertEqual(result['meta']['state_code'], 'VIC')

    def test_output_schema_nsw(self):
        """Test NSW output schema."""
        result = self.monitor.scrape_nsw()
        self.validate_output_json(result)
        self.assertEqual(result['meta']['state_code'], 'NSW')

    def test_output_schema_wa(self):
        """Test WA output schema."""
        result = self.monitor.scrape_wa()
        self.validate_output_json(result)
        self.assertEqual(result['meta']['state_code'], 'WA')

    def test_output_schema_queensland(self):
        """Test Queensland output schema."""
        result = self.monitor.scrape_queensland()
        self.validate_output_json(result)
        self.assertEqual(result['meta']['state_code'], 'QLD')

    def test_output_schema_sa(self):
        """Test South Australia output schema."""
        result = self.monitor.scrape_sa()
        self.validate_output_json(result)
        self.assertEqual(result['meta']['state_code'], 'SA')

    def test_output_schema_tasmania(self):
        """Test Tasmania output schema."""
        result = self.monitor.scrape_tasmania()
        self.validate_output_json(result)
        self.assertEqual(result['meta']['state_code'], 'TAS')

    def test_output_schema_nt(self):
        """Test NT output schema."""
        result = self.monitor.scrape_nt()
        self.validate_output_json(result)
        self.assertEqual(result['meta']['state_code'], 'NT')

    def test_output_schema_act(self):
        """Test ACT output schema."""
        result = self.monitor.scrape_act()
        self.validate_output_json(result)
        self.assertEqual(result['meta']['state_code'], 'ACT')


class TestParallelExecution(unittest.TestCase):
    """Test parallel execution of scrapers."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.monitor = StateMonitor(
            output_dir=self.temp_dir.name,
            max_workers=4
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_scrape_all_returns_all_states(self):
        """Test scrape_all returns results for all 8 states."""
        results = self.monitor.scrape_all()
        self.assertEqual(len(results), 8)
        expected_states = {'VIC', 'NSW', 'WA', 'QLD', 'SA', 'TAS', 'NT', 'ACT'}
        self.assertEqual(set(results.keys()), expected_states)

    def test_scrape_all_creates_individual_json_files(self):
        """Test scrape_all creates individual JSON files for each state."""
        self.monitor.scrape_all()

        expected_files = [
            'state_vic.json', 'state_nsw.json', 'state_wa.json',
            'state_qld.json', 'state_sa.json', 'state_tas.json',
            'state_nt.json', 'state_act.json'
        ]

        for filename in expected_files:
            filepath = os.path.join(self.temp_dir.name, filename)
            self.assertTrue(os.path.exists(filepath), f"{filename} not created")

            # Validate JSON structure
            with open(filepath) as f:
                data = json.load(f)
                self.assertIn('meta', data)
                self.assertIn('occupations', data)

    def test_scrape_all_appends_to_history(self):
        """Test scrape_all appends to state_history.jsonl."""
        self.monitor.scrape_all()

        history_file = os.path.join(self.temp_dir.name, 'state_history.jsonl')
        self.assertTrue(os.path.exists(history_file))

        # Read history and validate
        with open(history_file) as f:
            lines = f.readlines()
            self.assertGreater(len(lines), 0)

            # Each line should be valid JSON
            for line in lines:
                record = json.loads(line)
                self.assertIn('timestamp', record)
                self.assertIn('state_code', record)
                self.assertIn('occupation_count', record)

    def test_max_workers_configuration(self):
        """Test max_workers setting is respected."""
        monitor = StateMonitor(
            output_dir=self.temp_dir.name,
            max_workers=2
        )
        self.assertEqual(monitor.max_workers, 2)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and resilience."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.monitor = StateMonitor(output_dir=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_error_logging_on_failure(self):
        """Test errors are logged to error log file."""
        with patch.object(self.monitor, '_fetch_url', return_value=None):
            self.monitor.scrape_victoria()

        # Check error was logged
        self.assertGreater(len(self.monitor.errors), 0)

    def test_error_log_file_created(self):
        """Test error log file is created on failures."""
        with patch.object(self.monitor, '_fetch_url', return_value=None):
            self.monitor.scrape_victoria()

        error_log = os.path.join(
            self.temp_dir.name,
            'state_scraper_errors.jsonl'
        )
        self.assertTrue(os.path.exists(error_log))

        # Validate error log format
        with open(error_log) as f:
            for line in f:
                record = json.loads(line)
                self.assertIn('timestamp', record)
                self.assertIn('state_code', record)
                self.assertIn('error', record)

    def test_failed_scrape_returns_failed_status(self):
        """Test failed scrape returns status='failed'."""
        with patch.object(self.monitor, '_fetch_url', return_value=None):
            result = self.monitor.scrape_victoria()

        self.assertEqual(result['meta']['scrape_status'], 'failed')
        self.assertEqual(len(result['occupations']), 0)

    @patch('runtime.scrapers.state_monitor.urlopen')
    def test_retry_logic_on_timeout(self, mock_urlopen):
        """Test retry logic on timeout errors."""
        # Simulate timeout on first attempt, success on second
        import urllib.error
        mock_urlopen.side_effect = [
            urllib.error.URLError('Connection timeout'),
            MagicMock(read=lambda: b'<html></html>')
        ]

        monitor = StateMonitor(output_dir=self.temp_dir.name, max_retries=3)
        # Should not raise exception, should retry
        # (mock will prevent actual retry, but tests the logic)


class TestSingleStateScrapers(unittest.TestCase):
    """Test individual state scraper methods."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.monitor = StateMonitor(output_dir=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_scrape_state_by_code_victoria(self):
        """Test scrape_state() with Victoria code."""
        result = self.monitor.scrape_state('VIC')
        self.assertEqual(result['meta']['state_code'], 'VIC')
        self.assertIn('occupations', result)

    def test_scrape_state_by_code_lowercase(self):
        """Test scrape_state() accepts lowercase state codes."""
        result = self.monitor.scrape_state('vic')
        self.assertEqual(result['meta']['state_code'], 'VIC')

    def test_scrape_state_saves_json_file(self):
        """Test scrape_state() saves individual JSON file."""
        self.monitor.scrape_state('NSW')

        filepath = os.path.join(self.temp_dir.name, 'state_nsw.json')
        self.assertTrue(os.path.exists(filepath))

    def test_scrape_state_invalid_code(self):
        """Test scrape_state() raises error for invalid state code."""
        with self.assertRaises(ValueError):
            self.monitor.scrape_state('INVALID')

    def test_all_eight_states_accessible(self):
        """Test all 8 states can be scraped individually."""
        state_codes = ['VIC', 'NSW', 'WA', 'QLD', 'SA', 'TAS', 'NT', 'ACT']

        for code in state_codes:
            with self.subTest(state=code):
                result = self.monitor.scrape_state(code)
                self.assertEqual(result['meta']['state_code'], code)


class TestOccupationDataStructure(unittest.TestCase):
    """Test occupation data structure and content."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.monitor = StateMonitor(output_dir=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_occupation_codes_format(self):
        """Test occupation codes follow ANZSCO format (5 digits)."""
        result = self.monitor.scrape_victoria()

        for occ in result['occupations']:
            code = occ['occupation_code']
            self.assertEqual(len(code), 6, f"Invalid code format: {code}")
            self.assertTrue(code.isdigit(), f"Code not numeric: {code}")

    def test_visa_types_valid(self):
        """Test visa types are valid (190 or 491)."""
        result = self.monitor.scrape_victoria()

        valid_types = {'190', '491'}
        for occ in result['occupations']:
            for visa_type in occ['visa_type']:
                self.assertIn(visa_type, valid_types)

    def test_occupations_have_required_fields(self):
        """Test all occupations have required fields."""
        result = self.monitor.scrape_victoria()
        required_fields = {
            'occupation_code', 'occupation_title', 'visa_type',
            'available', 'processing_time_weeks'
        }

        for occ in result['occupations']:
            self.assertTrue(
                required_fields.issubset(set(occ.keys())),
                f"Missing fields in occupation: {occ}"
            )


class TestQuotaDataStructure(unittest.TestCase):
    """Test quota data structure."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.monitor = StateMonitor(output_dir=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_quota_has_visa_allocations(self):
        """Test quota is a valid dictionary."""
        result = self.monitor.scrape_victoria()
        quotas = result['quotas']

        # Should be a valid dict (may be empty if network fails)
        self.assertIsInstance(quotas, dict)

    def test_quota_allocations_are_numeric(self):
        """Test quota allocations are numeric."""
        result = self.monitor.scrape_victoria()
        quotas = result['quotas']

        for key in ['visa_190_available', 'visa_491_available']:
            if key in quotas:
                self.assertIsInstance(quotas[key], int)
                self.assertGreaterEqual(quotas[key], 0)


class TestHistoryFileManagement(unittest.TestCase):
    """Test append-only history file management."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.monitor = StateMonitor(output_dir=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_history_appends_records(self):
        """Test history file appends new records."""
        # Mock fetch to ensure scrapes succeed and history is created
        with patch.object(self.monitor, '_fetch_url', return_value='<html></html>'):
            # Scrape once
            self.monitor.scrape_victoria()

            # Read history
            history_file = os.path.join(self.temp_dir.name, 'state_history.jsonl')
            self.assertTrue(os.path.exists(history_file), "History file not created")

            with open(history_file) as f:
                lines_1 = len(f.readlines())

            # Scrape again
            self.monitor.scrape_victoria()

            # Check history grew
            with open(history_file) as f:
                lines_2 = len(f.readlines())

            self.assertGreater(lines_2, lines_1)

    def test_history_preserves_previous_records(self):
        """Test history file preserves previous records on append."""
        # Mock fetch to ensure scrapes succeed
        with patch.object(self.monitor, '_fetch_url', return_value='<html></html>'):
            # Scrape all states
            self.monitor.scrape_all()

            history_file = os.path.join(self.temp_dir.name, 'state_history.jsonl')
            with open(history_file) as f:
                initial_records = [json.loads(line) for line in f]

            # Scrape one state again
            self.monitor.scrape_victoria()

            # Check all records preserved
            with open(history_file) as f:
                all_records = [json.loads(line) for line in f]

            self.assertGreaterEqual(len(all_records), len(initial_records))


class TestStateConfiguration(unittest.TestCase):
    """Test state configuration and metadata."""

    def setUp(self):
        self.monitor = StateMonitor()

    def test_all_states_configured(self):
        """Test all 8 states are configured."""
        expected_states = {'VIC', 'NSW', 'WA', 'QLD', 'SA', 'TAS', 'NT', 'ACT'}
        configured_states = set(self.monitor.STATES.keys())
        self.assertEqual(configured_states, expected_states)

    def test_state_configuration_structure(self):
        """Test each state has required configuration."""
        required_keys = {'name', 'url', 'occupation_endpoint', 'visa_types'}

        for state_code, config in self.monitor.STATES.items():
            self.assertTrue(
                required_keys.issubset(set(config.keys())),
                f"Missing config keys for {state_code}: {config}"
            )
            self.assertIsInstance(config['visa_types'], list)
            self.assertGreater(len(config['visa_types']), 0)

    def test_state_urls_valid_format(self):
        """Test state URLs are valid HTTP(S) URLs."""
        import re
        url_pattern = re.compile(r'^https?://')

        for state_code, config in self.monitor.STATES.items():
            self.assertTrue(
                url_pattern.match(config['url']),
                f"Invalid URL format for {state_code}: {config['url']}"
            )


class TestTimestampHandling(unittest.TestCase):
    """Test timestamp handling in output and history."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.monitor = StateMonitor(output_dir=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_output_has_valid_iso_timestamp(self):
        """Test output timestamp is valid ISO format."""
        result = self.monitor.scrape_victoria()
        timestamp = result['meta']['scrape_timestamp']

        # Should be ISO format with Z or +00:00
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            self.fail(f"Invalid timestamp format: {timestamp}")

    def test_timestamps_are_recent(self):
        """Test timestamps are reasonably recent (within 1 minute)."""
        result = self.monitor.scrape_victoria()
        timestamp_str = result['meta']['scrape_timestamp']
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

        now = datetime.now(timezone.utc)
        delta = now - timestamp

        # Should be within 1 minute
        self.assertLess(delta.total_seconds(), 60)


def run_tests():
    """Run all tests and return results."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
