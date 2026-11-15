#!/usr/bin/env python3
"""
Test Suite for Intelligence Digester
Tests diff detection, anomaly scoring, markdown generation, and alert routing.
"""

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any

import sys
import os

# Add runtime to path
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..")
)

from runtime.intelligence.digester import IntelligenceDigester


class TestIntelligenceDigesterLoad(unittest.TestCase):
    """Test data loading functionality."""

    def setUp(self):
        """Create temporary directory with mock data."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.knowledge_dir = self.base_dir / "knowledge"
        self.cutoffs_dir = self.knowledge_dir / "live_cutoffs"
        self.digests_dir = self.knowledge_dir / "digests"
        self.alerts_dir = self.knowledge_dir / "alerts"

        # Create directories
        for d in [self.cutoffs_dir, self.digests_dir, self.alerts_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def _create_sample_cutoffs(self) -> Dict[str, Any]:
        """Create sample SkillSelect cutoffs data."""
        return {
            "meta": {
                "source": "test",
                "last_updated": "2026-11-15",
                "round_date": "2026-10-15",
                "total_invitations_189": 20000
            },
            "cutoffs": [
                {
                    "date": "2026-10-15",
                    "occupation_code": "261313",
                    "occupation_title": "Software Engineer",
                    "invited_this_round": 456,
                    "visa_189_tiebreak_date": "2026-10-13",
                    "visa_189_status": "invited",
                    "notes": "Test"
                },
                {
                    "date": "2026-10-15",
                    "occupation_code": "263111",
                    "occupation_title": "Systems Administrator",
                    "invited_this_round": 234,
                    "visa_189_tiebreak_date": "2026-09-27",
                    "visa_189_status": "invited",
                    "notes": "Test"
                },
                {
                    "date": "2026-10-15",
                    "occupation_code": "262112",
                    "occupation_title": "Accountant",
                    "invited_this_round": 0,
                    "visa_189_tiebreak_date": None,
                    "visa_189_status": "no_allocation",
                    "notes": "Test"
                }
            ]
        }

    def test_load_sources_success(self):
        """Test successful load of cutoffs data."""
        # Create cutoffs file
        cutoffs_file = self.cutoffs_dir / "skillselect_cutoffs.json"
        with open(cutoffs_file, "w") as f:
            json.dump(self._create_sample_cutoffs(), f)

        digester = IntelligenceDigester(base_dir=str(self.base_dir), log_level="ERROR")
        success = digester.load_sources()

        self.assertTrue(success)
        self.assertEqual(len(digester.today_cutoffs), 3)

    def test_load_sources_missing_cutoffs(self):
        """Test handling of missing cutoffs file."""
        digester = IntelligenceDigester(base_dir=str(self.base_dir), log_level="ERROR")
        success = digester.load_sources()

        self.assertFalse(success)  # Should fail if cutoffs missing
        self.assertEqual(len(digester.today_cutoffs), 0)

    def test_load_history_optional(self):
        """Test that missing history doesn't fail load."""
        # Create cutoffs but no history
        cutoffs_file = self.cutoffs_dir / "skillselect_cutoffs.json"
        with open(cutoffs_file, "w") as f:
            json.dump(self._create_sample_cutoffs(), f)

        digester = IntelligenceDigester(base_dir=str(self.base_dir), log_level="ERROR")
        success = digester.load_sources()

        self.assertTrue(success)
        self.assertEqual(len(digester.cutoff_history), 0)

    def test_load_history_success(self):
        """Test successful load of history data."""
        # Create cutoffs file
        cutoffs_file = self.cutoffs_dir / "skillselect_cutoffs.json"
        with open(cutoffs_file, "w") as f:
            json.dump(self._create_sample_cutoffs(), f)

        # Create history file
        history_file = self.cutoffs_dir / "skillselect_history.jsonl"
        with open(history_file, "w") as f:
            f.write('{"date": "2026-10-14", "occupation_code": "261313", "invited": 445}\n')
            f.write('{"date": "2026-10-13", "occupation_code": "261313", "invited": 434}\n')

        digester = IntelligenceDigester(base_dir=str(self.base_dir), log_level="ERROR")
        success = digester.load_sources()

        self.assertTrue(success)
        self.assertEqual(len(digester.cutoff_history), 2)


class TestIntelligenceDigesterDiff(unittest.TestCase):
    """Test diff and change detection."""

    def setUp(self):
        """Set up test data."""
        self.digester = IntelligenceDigester(log_level="ERROR")

    def test_detect_cutoff_increase(self):
        """Test detection of tiebreak date moving backward (stricter cutoff)."""
        self.digester.today_cutoffs = [
            {
                "occupation_code": "261313",
                "occupation_title": "Software Engineer",
                "visa_189_tiebreak_date": "2026-10-20",  # Later = stricter
                "invited_this_round": 400
            }
        ]

        self.digester.cutoff_history = [
            {
                "date": "2026-10-14",
                "occupation_code": "261313",
                "occupation_title": "Software Engineer",
                "tiebreak_date": "2026-10-13"
            }
        ]

        changes = self.digester.compare_with_yesterday()

        # Should detect cutoff change
        self.assertTrue(len(changes["cutoff_changes"]) > 0)
        change = changes["cutoff_changes"][0]
        self.assertEqual(change["code"], "261313")

    def test_detect_occupation_added(self):
        """Test detection of newly added occupation."""
        self.digester.today_cutoffs = [
            {
                "occupation_code": "261313",
                "occupation_title": "Software Engineer",
                "visa_189_tiebreak_date": "2026-10-13",
                "invited_this_round": 400
            }
        ]

        # No history from yesterday = new occupation
        self.digester.cutoff_history = []

        changes = self.digester.compare_with_yesterday()

        # Should detect as addition
        self.assertTrue(len(changes["occupation_added"]) > 0)

    def test_detect_occupation_removed(self):
        """Test detection of removed occupation."""
        self.digester.today_cutoffs = []

        # Occupation in history but not today
        self.digester.cutoff_history = [
            {
                "date": "2026-10-14",
                "occupation_code": "262112",
                "occupation_title": "Accountant",
                "status": "no_allocation"
            }
        ]

        changes = self.digester.compare_with_yesterday()

        # Should detect as removal
        self.assertTrue(len(changes["occupation_removed"]) > 0)

    def test_detect_invitation_change_significant(self):
        """Test detection of significant invitation count change."""
        self.digester.today_cutoffs = [
            {
                "occupation_code": "263111",
                "occupation_title": "Systems Administrator",
                "invited_this_round": 180,  # Down from 234
                "visa_189_status": "invited"
            }
        ]

        self.digester.cutoff_history = [
            {
                "date": "2026-10-14",
                "occupation_code": "263111",
                "invited": 234
            }
        ]

        changes = self.digester.compare_with_yesterday()

        # Should detect >10% change
        self.assertTrue(len(changes["invitation_changes"]) > 0)
        change = changes["invitation_changes"][0]
        self.assertAlmostEqual(change["pct_change"], -23.1, places=0)

    def test_detect_status_change_to_no_allocation(self):
        """Test detection of occupation becoming unavailable."""
        self.digester.today_cutoffs = [
            {
                "occupation_code": "262112",
                "occupation_title": "Accountant",
                "visa_189_status": "no_allocation"
            }
        ]

        self.digester.cutoff_history = [
            {
                "date": "2026-10-14",
                "occupation_code": "262112",
                "status": "active"
            }
        ]

        changes = self.digester.compare_with_yesterday()

        # Should detect status change
        self.assertTrue(len(changes["status_changes"]) > 0)


class TestIntelligenceDigesterAnomaly(unittest.TestCase):
    """Test anomaly scoring and 2-day confirmation."""

    def setUp(self):
        """Set up test digester."""
        self.digester = IntelligenceDigester(log_level="ERROR")

    def test_score_anomaly_cutoff_high_confidence(self):
        """Test scoring of large cutoff change (high confidence)."""
        self.digester.changes = [
            {
                "code": "261313",
                "title": "Software Engineer",
                "yesterday_date": "2026-10-13",
                "today_date": "2026-10-20",
                "confidence": 90  # Large jump = high confidence
            }
        ]

        # No history for 2-day check (simplified test)
        self.digester.cutoff_history = []

        anomalies = self.digester.score_anomalies()

        self.assertEqual(len(anomalies), 1)
        anomaly = anomalies[0]
        self.assertEqual(anomaly["confidence"], 90)

    def test_score_anomaly_low_confidence(self):
        """Test scoring of small change (low confidence)."""
        self.digester.changes = [
            {
                "code": "253214",
                "title": "Telecom Tech",
                "yesterday_date": "2026-10-13",
                "today_date": "2026-10-14",
                "confidence": 50  # Small jump = low confidence
            }
        ]

        self.digester.cutoff_history = []

        anomalies = self.digester.score_anomalies()

        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["confidence"], 50)

    def test_two_day_confirmation_reduces_false_positives(self):
        """Test that 2-day rule prevents single-day glitches."""
        self.digester.changes = [
            {
                "code": "261313",
                "title": "Software Engineer",
                "type": "cutoff_change",
                "confidence": 85
            }
        ]

        # History only has today's data, not yesterday
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.digester.cutoff_history = [
            {
                "date": today,
                "occupation_code": "261313"
            }
        ]

        anomalies = self.digester.score_anomalies()

        # 2-day confirmation should fail (only 1 day in history)
        self.assertEqual(len(anomalies), 1)
        self.assertFalse(anomalies[0]["two_day_confirmed"])

    def test_severity_critical_with_confirmation(self):
        """Test CRITICAL severity (confidence > 80 AND 2-day confirmed)."""
        anomaly = {
            "confidence": 85,
            "two_day_confirmed": True
        }

        severity = self.digester._calculate_severity(
            anomaly["confidence"],
            anomaly["two_day_confirmed"]
        )

        self.assertEqual(severity, "CRITICAL")

    def test_severity_significant_medium_confidence(self):
        """Test SIGNIFICANT severity (confidence 65-80)."""
        severity = self.digester._calculate_severity(
            confidence=75,
            two_day_confirmed=False
        )

        self.assertEqual(severity, "SIGNIFICANT")

    def test_severity_minor_low_confidence(self):
        """Test MINOR severity (confidence < 65)."""
        severity = self.digester._calculate_severity(
            confidence=50,
            two_day_confirmed=True
        )

        self.assertEqual(severity, "MINOR")


class TestIntelligenceDigesterMarkdown(unittest.TestCase):
    """Test markdown generation."""

    def setUp(self):
        """Set up test digester."""
        self.digester = IntelligenceDigester(log_level="ERROR")

    def test_generate_markdown_contains_sections(self):
        """Test that digest contains all required sections."""
        self.digester.anomalies = [
            {
                "code": "261313",
                "title": "Software Engineer",
                "type": "cutoff_change",
                "severity": "CRITICAL",
                "confidence": 85,
                "change": {
                    "yesterday_date": "2026-10-13",
                    "today_date": "2026-10-20"
                }
            }
        ]

        self.digester.today_cutoffs = [
            {"visa_189_status": "invited"},
            {"visa_189_status": "invited"},
            {"visa_189_status": "no_allocation"}
        ]

        digest = self.digester.generate_markdown()

        # Verify sections present
        self.assertIn("# Daily Intelligence Digest", digest)
        self.assertIn("🔴 CRITICAL ALERTS", digest)
        self.assertIn("🟡 SIGNIFICANT CHANGES", digest)
        self.assertIn("📊 KEY METRICS", digest)
        self.assertIn("🔍 TREND ANALYSIS", digest)
        self.assertIn("📅 UPCOMING EVENTS", digest)
        self.assertIn("⚙️ DATA QUALITY", digest)

    def test_generate_markdown_critical_alert_formatted(self):
        """Test that CRITICAL alert is properly formatted."""
        self.digester.anomalies = [
            {
                "code": "261313",
                "title": "Software Engineer",
                "type": "cutoff_change",
                "severity": "CRITICAL",
                "confidence": 85,
                "change": {
                    "yesterday_date": "2026-10-13",
                    "today_date": "2026-10-20"
                }
            }
        ]

        self.digester.today_cutoffs = []

        digest = self.digester.generate_markdown()

        # Verify format includes code, title, and dates
        self.assertIn("261313", digest)
        self.assertIn("Software Engineer", digest)
        self.assertIn("2026-10-13", digest)
        self.assertIn("2026-10-20", digest)

    def test_generate_markdown_empty_anomalies(self):
        """Test digest generation with no anomalies."""
        self.digester.anomalies = []
        self.digester.today_cutoffs = []

        digest = self.digester.generate_markdown()

        self.assertIn("# Daily Intelligence Digest", digest)
        self.assertIn("None reported", digest)


class TestIntelligenceDigesterRouting(unittest.TestCase):
    """Test alert routing by severity."""

    def setUp(self):
        """Set up test digester."""
        self.digester = IntelligenceDigester(log_level="ERROR")

    def test_route_critical_alerts(self):
        """Test routing of CRITICAL alerts."""
        self.digester.anomalies = [
            {"code": "261313", "severity": "CRITICAL"},
            {"code": "263111", "severity": "CRITICAL"},
            {"code": "254499", "severity": "SIGNIFICANT"}
        ]

        routed = self.digester.route_alerts()

        self.assertEqual(len(routed["critical"]), 2)
        self.assertEqual(len(routed["significant"]), 1)
        self.assertEqual(len(routed["minor"]), 0)

    def test_route_significant_alerts(self):
        """Test routing of SIGNIFICANT alerts."""
        self.digester.anomalies = [
            {"code": "261313", "severity": "SIGNIFICANT"},
            {"code": "263111", "severity": "MINOR"},
            {"code": "254499", "severity": "MINOR"}
        ]

        routed = self.digester.route_alerts()

        self.assertEqual(len(routed["critical"]), 0)
        self.assertEqual(len(routed["significant"]), 1)
        self.assertEqual(len(routed["minor"]), 2)

    def test_route_empty_alerts(self):
        """Test routing with no anomalies."""
        self.digester.anomalies = []

        routed = self.digester.route_alerts()

        self.assertEqual(len(routed["critical"]), 0)
        self.assertEqual(len(routed["significant"]), 0)
        self.assertEqual(len(routed["minor"]), 0)


class TestIntelligenceDigesterSaveOutputs(unittest.TestCase):
    """Test saving outputs to disk."""

    def setUp(self):
        """Create temporary directory."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.knowledge_dir = self.base_dir / "knowledge"

        # Create subdirectories
        self.cutoffs_dir = self.knowledge_dir / "live_cutoffs"
        self.digests_dir = self.knowledge_dir / "digests"
        self.alerts_dir = self.knowledge_dir / "alerts"

        for d in [self.cutoffs_dir, self.digests_dir, self.alerts_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def test_save_digest_file(self):
        """Test saving digest markdown file."""
        digester = IntelligenceDigester(base_dir=str(self.base_dir), log_level="ERROR")

        digest_md = "# Test Digest\n\nTest content"
        anomalies = []

        success = digester.save_outputs(digest_md, anomalies)

        self.assertTrue(success)

        # Verify file created
        digest_path = self.digests_dir / f"{digester.today_date}_daily_digest.md"
        self.assertTrue(digest_path.exists())

        # Verify content
        with open(digest_path, "r") as f:
            content = f.read()
        self.assertIn("Test Digest", content)

    def test_save_anomalies_json(self):
        """Test saving anomalies JSON file."""
        digester = IntelligenceDigester(base_dir=str(self.base_dir), log_level="ERROR")

        digest_md = "# Test"
        anomalies = [
            {
                "code": "261313",
                "title": "Software Engineer",
                "severity": "CRITICAL"
            }
        ]

        success = digester.save_outputs(digest_md, anomalies)

        self.assertTrue(success)

        # Verify file created
        anomalies_path = self.alerts_dir / f"anomalies_{digester.today_date}.json"
        self.assertTrue(anomalies_path.exists())

        # Verify content
        with open(anomalies_path, "r") as f:
            data = json.load(f)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["code"], "261313")

    def test_save_critical_alerts_only(self):
        """Test saving critical alerts subset."""
        digester = IntelligenceDigester(base_dir=str(self.base_dir), log_level="ERROR")

        digest_md = "# Test"
        anomalies = [
            {"code": "261313", "severity": "CRITICAL"},
            {"code": "263111", "severity": "SIGNIFICANT"},
            {"code": "254499", "severity": "MINOR"}
        ]

        success = digester.save_outputs(digest_md, anomalies)

        self.assertTrue(success)

        # Verify critical alerts file created
        critical_path = self.alerts_dir / f"critical_alerts_{digester.today_date}.json"
        self.assertTrue(critical_path.exists())

        # Verify only CRITICAL in file
        with open(critical_path, "r") as f:
            data = json.load(f)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["severity"], "CRITICAL")

    def test_save_updates_digest_index(self):
        """Test that digest index is updated."""
        digester = IntelligenceDigester(base_dir=str(self.base_dir), log_level="ERROR")

        digest_md = "# Test Digest"
        anomalies = [
            {"code": "261313", "severity": "CRITICAL"}
        ]

        success = digester.save_outputs(digest_md, anomalies)

        self.assertTrue(success)

        # Verify index created
        index_path = self.digests_dir / "index.json"
        self.assertTrue(index_path.exists())

        # Verify content
        with open(index_path, "r") as f:
            index = json.load(f)

        self.assertIn("digests", index)
        self.assertEqual(len(index["digests"]), 1)
        self.assertEqual(index["digests"][0]["date"], digester.today_date)


class TestIntelligenceDigesterPipeline(unittest.TestCase):
    """Test full pipeline execution."""

    def setUp(self):
        """Create test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.knowledge_dir = self.base_dir / "knowledge"

        # Create directories
        for subdir in ["live_cutoffs", "digests", "alerts"]:
            (self.knowledge_dir / subdir).mkdir(parents=True, exist_ok=True)

        # Create sample cutoffs
        cutoffs_file = self.knowledge_dir / "live_cutoffs" / "skillselect_cutoffs.json"
        with open(cutoffs_file, "w") as f:
            json.dump({
                "meta": {"source": "test"},
                "cutoffs": [
                    {
                        "occupation_code": "261313",
                        "occupation_title": "Software Engineer",
                        "visa_189_tiebreak_date": "2026-10-15",
                        "invited_this_round": 450,
                        "visa_189_status": "invited"
                    }
                ]
            }, f)

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def test_pipeline_run_success(self):
        """Test full pipeline execution."""
        digester = IntelligenceDigester(base_dir=str(self.base_dir), log_level="ERROR")

        success = digester.run()

        # Pipeline should succeed
        self.assertTrue(success)

        # Verify outputs created
        digest_path = self.knowledge_dir / "digests" / f"{digester.today_date}_daily_digest.md"
        self.assertTrue(digest_path.exists())

        # Verify digest content
        with open(digest_path, "r") as f:
            digest = f.read()
        self.assertIn("# Daily Intelligence Digest", digest)


if __name__ == "__main__":
    unittest.main()
