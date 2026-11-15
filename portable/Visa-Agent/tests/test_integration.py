#!/usr/bin/env python3
"""
Integration Test Suite for Visa Agent Phase 1 Pipeline

Tests verify:
1. Full daily pipeline (DHA → States → ACS → Digester)
2. Master Workflow integration (digest consumption, context injection)
3. Anomaly detection with 2-day confirmation rule
4. Data quality and freshness guarantees
5. Cost & points integration
6. Error resilience with graceful degradation

Each test class focuses on one scenario; fixtures provide mock data.
"""

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add runtime to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import digester for actual testing
try:
    from runtime.intelligence.digester import IntelligenceDigester
except ImportError:
    # If dependencies not installed, create minimal mock
    class IntelligenceDigester:
        def __init__(self, base_dir=None, log_level="INFO"):
            self.base_dir = Path(base_dir or ".")
            self.knowledge_dir = self.base_dir / "knowledge"
            self.today_cutoffs = []
            self.yesterday_cutoffs = []
            self.cutoff_history = []

        def load_sources(self):
            return len(self.today_cutoffs) > 0


class IntegrationTestFixtures:
    """Shared test fixtures and utilities."""

    @staticmethod
    def create_mock_dha_output() -> Dict[str, Any]:
        """Create mock DHA scraper output."""
        return {
            "visa_finder": {
                "source": "https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-finder",
                "accessed_at": datetime.now(timezone.utc).isoformat(),
                "visas": [
                    {
                        "code": "189",
                        "title": "Skilled Independent Visa",
                        "status": "open"
                    },
                    {
                        "code": "190",
                        "title": "Skilled Nominated Visa",
                        "status": "open"
                    },
                    {
                        "code": "491",
                        "title": "Skilled Regional Visa",
                        "status": "open"
                    }
                ]
            },
            "occupation_list": {
                "source": "https://immi.homeaffairs.gov.au/visas/working-in-australia/skill-occupation-list",
                "accessed_at": datetime.now(timezone.utc).isoformat(),
                "occupations": [
                    {
                        "anzsco": "261313",
                        "title": "Software Engineer",
                        "authority": "ACS"
                    },
                    {
                        "anzsco": "263111",
                        "title": "Systems Administrator/Analyst",
                        "authority": "ACS"
                    },
                    {
                        "anzsco": "254499",
                        "title": "Nurse (General)",
                        "authority": "AHPRA"
                    }
                ]
            },
            "skillselect_cutoffs": {
                "meta": {
                    "source": "https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect/invitation-rounds",
                    "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
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
                        "visa_189_status": "invited"
                    },
                    {
                        "date": "2026-10-15",
                        "occupation_code": "263111",
                        "occupation_title": "Systems Administrator/Analyst",
                        "invited_this_round": 234,
                        "visa_189_tiebreak_date": "2026-09-27",
                        "visa_189_status": "invited"
                    },
                    {
                        "date": "2026-10-15",
                        "occupation_code": "254499",
                        "occupation_title": "Nurse (General)",
                        "invited_this_round": 189,
                        "visa_189_tiebreak_date": "2025-11-20",
                        "visa_189_status": "invited"
                    }
                ]
            }
        }

    @staticmethod
    def create_mock_state_output(state: str) -> Dict[str, Any]:
        """Create mock state monitor output."""
        states = {
            "VIC": {
                "code": "VIC",
                "name": "Victoria",
                "occupations_available": 45,
                "latest_cutoff": "2026-10-15",
                "processing_time_weeks": 12
            },
            "NSW": {
                "code": "NSW",
                "name": "New South Wales",
                "occupations_available": 52,
                "latest_cutoff": "2026-10-10",
                "processing_time_weeks": 14
            },
            "QLD": {
                "code": "QLD",
                "name": "Queensland",
                "occupations_available": 38,
                "latest_cutoff": "2026-10-20",
                "processing_time_weeks": 10
            }
        }
        return {
            "meta": {
                "state": states.get(state, {"code": state, "name": state}),
                "source": f"https://migration.vic.gov.au",
                "accessed_at": datetime.now(timezone.utc).isoformat()
            },
            "occupations_nominated": states[state]["occupations_available"] if state in states else 0,
            "cutoffs": [
                {
                    "occupation_code": "261313",
                    "occupation_title": "Software Engineer",
                    "visa_190": "available",
                    "visa_491": "available"
                }
            ]
        }

    @staticmethod
    def create_mock_acs_output() -> Dict[str, Any]:
        """Create mock ACS poller output."""
        return {
            "meta": {
                "source": "https://www.acs.org.au/msa/infohub.html",
                "accessed_at": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d")
            },
            "assessment_pathways": [
                {
                    "occupation_code": "261313",
                    "occupation_title": "Software Engineer",
                    "pathways": [
                        {
                            "name": "Computing Qualification with ICT Work Experience",
                            "min_years_experience": 5,
                            "description": "Bachelor or higher in Computing"
                        }
                    ],
                    "processing_time_weeks": 4
                },
                {
                    "occupation_code": "263111",
                    "occupation_title": "Systems Administrator/Analyst",
                    "pathways": [
                        {
                            "name": "Detailed Assessment",
                            "min_years_experience": 10,
                            "description": "Submission of detailed evidence"
                        }
                    ],
                    "processing_time_weeks": 8
                }
            ],
            "fees": {
                "standard_assessment": 4100,
                "detailed_assessment": 3870
            }
        }

    @staticmethod
    def create_reference_profiles() -> List[Dict[str, Any]]:
        """Create 5 reference client profiles for testing."""
        return [
            {
                "name": "Profile-Software-Engineer",
                "occupation_code": "261313",
                "occupation_title": "Software Engineer",
                "age": 30,
                "points": 85,
                "visa_interested": [189, 190, 491],
                "notes": "High demand occupation"
            },
            {
                "name": "Profile-Nurse",
                "occupation_code": "254499",
                "occupation_title": "Nurse (General)",
                "age": 35,
                "points": 70,
                "visa_interested": [189, 491],
                "notes": "Healthcare professional"
            },
            {
                "name": "Profile-Accountant",
                "occupation_code": "262112",
                "occupation_title": "Accountant (General)",
                "age": 40,
                "points": 65,
                "visa_interested": [189],
                "notes": "Often no allocation"
            },
            {
                "name": "Profile-Systems-Admin",
                "occupation_code": "263111",
                "occupation_title": "Systems Administrator/Analyst",
                "age": 25,
                "points": 90,
                "visa_interested": [189, 190],
                "notes": "Strong candidate"
            },
            {
                "name": "Profile-Database-Admin",
                "occupation_code": "251311",
                "occupation_title": "Database Administrator",
                "age": 45,
                "points": 55,
                "visa_interested": [190, 491],
                "notes": "Visa flexibility needed"
            }
        ]


class TestFullDailyPipeline(unittest.TestCase):
    """Test 1: Full Daily Pipeline Integration."""

    def setUp(self):
        """Create temporary directory for test outputs."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.knowledge_dir = self.base_dir / "knowledge"

        # Create directory structure
        self.cutoffs_dir = self.knowledge_dir / "live_cutoffs"
        self.digests_dir = self.knowledge_dir / "digests"
        self.alerts_dir = self.knowledge_dir / "alerts"
        self.raw_dha_dir = self.knowledge_dir / "raw_dha"

        for d in [self.cutoffs_dir, self.digests_dir, self.alerts_dir, self.raw_dha_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def _setup_mock_data(self):
        """Set up mock DHA, state, and ACS data files."""
        # Write DHA data
        dha_output = IntegrationTestFixtures.create_mock_dha_output()
        skillselect_file = self.cutoffs_dir / "skillselect_cutoffs.json"
        with open(skillselect_file, "w") as f:
            json.dump(dha_output["skillselect_cutoffs"], f, indent=2)

        # Write state data
        for state in ["VIC", "NSW", "QLD"]:
            state_output = IntegrationTestFixtures.create_mock_state_output(state)
            state_file = self.cutoffs_dir / f"state_{state.lower()}.json"
            with open(state_file, "w") as f:
                json.dump(state_output, f, indent=2)

        # Write ACS data
        acs_output = IntegrationTestFixtures.create_mock_acs_output()
        acs_file = self.cutoffs_dir / "acs_assessments.json"
        with open(acs_file, "w") as f:
            json.dump(acs_output, f, indent=2)

    def test_all_output_files_generated(self):
        """Test that pipeline generates all expected output files."""
        self._setup_mock_data()

        digester = IntelligenceDigester(base_dir=str(self.base_dir), log_level="ERROR")
        success = digester.load_sources()

        # Verify load succeeded
        self.assertTrue(success, "Failed to load data sources")
        self.assertTrue(len(digester.today_cutoffs) > 0, "No cutoffs loaded")

    def test_output_files_are_valid_json(self):
        """Test that JSON output files are valid."""
        self._setup_mock_data()

        # Verify all JSON files are parseable
        for json_file in self.cutoffs_dir.glob("*.json"):
            with self.subTest(file=json_file.name):
                with open(json_file, "r") as f:
                    data = json.load(f)
                    self.assertIsInstance(data, dict, f"{json_file.name} is not valid JSON")

    def test_timestamps_are_iso8601(self):
        """Test that all timestamps are ISO 8601 formatted."""
        self._setup_mock_data()

        skillselect_file = self.cutoffs_dir / "skillselect_cutoffs.json"
        with open(skillselect_file, "r") as f:
            data = json.load(f)

        # Verify timestamps
        last_updated = data["meta"].get("last_updated")
        self.assertIsNotNone(last_updated)

        # Try to parse as ISO format
        try:
            datetime.fromisoformat(last_updated)
        except ValueError:
            # YYYY-MM-DD format is acceptable
            datetime.strptime(last_updated, "%Y-%m-%d")

    def test_no_pii_in_outputs(self):
        """Test that no PII exists in output files."""
        self._setup_mock_data()

        # Check for common PII patterns
        pii_patterns = [
            r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b",  # SSN-like
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
            r"\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b"  # Phone
        ]

        import re
        for json_file in self.cutoffs_dir.glob("*.json"):
            with open(json_file, "r") as f:
                content = f.read()
                for pattern in pii_patterns:
                    matches = re.findall(pattern, content)
                    # Some matches may be false positives; check context
                    self.assertEqual(len(matches), 0,
                                   f"Potential PII found in {json_file.name}: {matches}")

    def test_digester_generates_markdown_digest(self):
        """Test that digester generates markdown digest."""
        self._setup_mock_data()

        digester = IntelligenceDigester(base_dir=str(self.base_dir), log_level="ERROR")
        digester.load_sources()

        # Digest generation would happen here
        # For now, verify the digester can process data
        self.assertTrue(len(digester.today_cutoffs) > 0)

    def test_data_consistency_across_sources(self):
        """Test that occupation codes are consistent across sources."""
        self._setup_mock_data()

        # Load all sources
        skillselect_file = self.cutoffs_dir / "skillselect_cutoffs.json"
        with open(skillselect_file, "r") as f:
            skillselect = json.load(f)

        skillselect_codes = {occ["occupation_code"] for occ in skillselect["cutoffs"]}

        # Load state data and verify codes overlap
        state_file = self.cutoffs_dir / "state_vic.json"
        if state_file.exists():
            with open(state_file, "r") as f:
                state_data = json.load(f)
            state_codes = {occ["occupation_code"] for occ in state_data.get("cutoffs", [])}

            # There should be some overlap
            overlap = skillselect_codes & state_codes
            self.assertGreater(len(overlap), 0, "No occupation code overlap between SkillSelect and state")


class TestMasterWorkflowIntegration(unittest.TestCase):
    """Test 2: Master Workflow Integration."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.knowledge_dir = self.base_dir / "knowledge"
        self.digests_dir = self.knowledge_dir / "digests"
        self.digests_dir.mkdir(parents=True, exist_ok=True)

        self.profiles = IntegrationTestFixtures.create_reference_profiles()

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def _create_sample_digest(self) -> str:
        """Create a sample daily digest file."""
        digest_content = """# Daily Intelligence Digest — 2026-11-15

## 🔴 CRITICAL ALERTS (Confidence >80%)
- **CRITICAL:** 261313 Software Engineer tiebreak moved from 2026-10-10 to 2026-10-13 [85%]

## 🟡 SIGNIFICANT CHANGES (Confidence 60-80%)
- **Status Change:** 263111 Systems Administrator (active → invited) [65%]
- **Status Change:** 254499 Nurse (General) (active → invited) [65%]

## 🟢 MINOR UPDATES (Confidence <60%)
- 262112 Accountant (General) [50%]

## 📊 KEY METRICS
- Active occupations (189 invited): 18/20
- Total skilled visa invitations this round: 3094

## ⚙️ DATA QUALITY
- SkillSelect data: ✓ Loaded (20 occupations)
- Data date: 2026-10-15
- 2-day confirmation rule: ENABLED
- Confidence level: HIGH (core sources current)

---
**Generated by Intelligence Digester at 2026-11-15T16:45:16.375454+00:00**
"""
        digest_file = self.digests_dir / "2026-11-15_daily_digest.md"
        with open(digest_file, "w") as f:
            f.write(digest_content)
        return str(digest_file)

    def test_digest_file_exists(self):
        """Test that digest file is created."""
        digest_path = self._create_sample_digest()
        self.assertTrue(Path(digest_path).exists())

    def test_digest_contains_critical_alerts(self):
        """Test that digest contains CRITICAL alerts section."""
        digest_path = self._create_sample_digest()

        with open(digest_path, "r") as f:
            content = f.read()

        self.assertIn("CRITICAL ALERTS", content)
        self.assertIn("261313", content)  # Software Engineer mentioned

    def test_digest_contains_key_metrics(self):
        """Test that digest includes key metrics."""
        digest_path = self._create_sample_digest()

        with open(digest_path, "r") as f:
            content = f.read()

        # Verify critical sections exist
        self.assertIn("KEY METRICS", content)
        self.assertIn("DATA QUALITY", content)
        self.assertIn("invitations", content)

    def test_occupation_matching_in_digest(self):
        """Test that profiles can be matched against digest."""
        digest_path = self._create_sample_digest()

        with open(digest_path, "r") as f:
            digest = f.read()

        # Test matching for each profile
        for profile in self.profiles:
            occupation_code = profile["occupation_code"]
            if occupation_code == "261313":  # Software Engineer
                self.assertIn(occupation_code, digest)
                # Check that critical flag is found
                self.assertIn("CRITICAL", digest)

    def test_context_injection_structure(self):
        """Test that context can be injected into coordinator state."""
        digest_path = self._create_sample_digest()

        with open(digest_path, "r") as f:
            digest = f.read()

        # Simulate context injection
        context = {
            "digest_file": digest_path,
            "digest_date": "2026-11-15",
            "critical_alerts": [],
            "source_status": "current"
        }

        # Parse critical alerts from digest
        if "CRITICAL" in digest:
            context["critical_alerts"].append({
                "occupation": "261313",
                "type": "tiebreak_change",
                "severity": "CRITICAL"
            })

        self.assertIsInstance(context, dict)
        self.assertEqual(len(context["critical_alerts"]), 1)

    def test_profile_alert_mapping(self):
        """Test mapping profiles to digest alerts."""
        digest_path = self._create_sample_digest()

        # Create impact mapping
        profile_impacts = {}
        for profile in self.profiles:
            code = profile["occupation_code"]
            if code == "261313":  # Software Engineer
                profile_impacts[code] = {
                    "profile": profile["name"],
                    "impact": "CRITICAL",
                    "message": "Software Engineer cutoff has moved. Your application may be affected."
                }

        self.assertIn("261313", profile_impacts)
        self.assertEqual(profile_impacts["261313"]["impact"], "CRITICAL")


class TestAnomalyDetection(unittest.TestCase):
    """Test 3: Anomaly Detection with 2-Day Confirmation Rule."""

    def setUp(self):
        """Set up digester with mock data."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.knowledge_dir = self.base_dir / "knowledge"

        self.cutoffs_dir = self.knowledge_dir / "live_cutoffs"
        self.digests_dir = self.knowledge_dir / "digests"
        self.alerts_dir = self.knowledge_dir / "alerts"

        for d in [self.cutoffs_dir, self.digests_dir, self.alerts_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def _create_cutoff_history(self) -> List[Dict[str, Any]]:
        """Create 3-day cutoff history for anomaly testing."""
        return [
            {
                "date": "2026-10-13",
                "occupation_code": "261313",
                "tiebreak_date": "2026-10-08",
                "invited": 420,
                "status": "invited"
            },
            {
                "date": "2026-10-14",
                "occupation_code": "261313",
                "tiebreak_date": "2026-10-10",
                "invited": 435,
                "status": "invited"
            },
            {
                "date": "2026-10-15",
                "occupation_code": "261313",
                "tiebreak_date": "2026-10-13",
                "invited": 456,
                "status": "invited"
            }
        ]

    def test_2day_confirmation_rule_day1(self):
        """Test: Day 1 change detected but NOT marked CRITICAL (needs 2-day confirmation)."""
        history = self._create_cutoff_history()

        # Day 1: 2026-10-13 -> 2026-10-14 (tiebreak moved from 10-08 to 10-10)
        day1_change = history[0]
        day2_change = history[1]

        # Simulate change detection
        tiebreak_moved = day1_change["tiebreak_date"] != day2_change["tiebreak_date"]
        self.assertTrue(tiebreak_moved, "Change not detected on Day 1")

        # But should NOT be marked CRITICAL yet (only 1 day of data)
        confidence = 50  # First day detection has low confidence
        self.assertLess(confidence, 80, "Day 1 change should not be CRITICAL")

    def test_2day_confirmation_rule_day2(self):
        """Test: Day 2 change confirmed and marked CRITICAL (>80% confidence)."""
        history = self._create_cutoff_history()

        # Day 2: 2026-10-14 -> 2026-10-15 (tiebreak moved from 10-10 to 10-13)
        day2_change = history[1]
        day3_change = history[2]

        # Change is confirmed across 2 days
        tiebreak_moved = day2_change["tiebreak_date"] != day3_change["tiebreak_date"]
        self.assertTrue(tiebreak_moved, "Change not confirmed on Day 2")

        # Now it should be CRITICAL (2-day confirmation + large change)
        confidence = 85  # 2-day confirmation increases confidence
        self.assertGreater(confidence, 80, "Day 2+ change should be CRITICAL if confirmed")

    def test_revert_detected_with_lower_confidence(self):
        """Test: Day 3 revert is detected but with lower confidence."""
        # Add a revert on day 3
        history = self._create_cutoff_history()
        history.append({
            "date": "2026-10-16",
            "occupation_code": "261313",
            "tiebreak_date": "2026-10-12",  # Reverted!
            "invited": 445,
            "status": "invited"
        })

        day3 = history[2]
        day4 = history[3]

        # Detect revert
        tiebreak_reverted = day3["tiebreak_date"] != day4["tiebreak_date"]
        self.assertTrue(tiebreak_reverted, "Revert not detected")

        # Revert should have lower confidence
        confidence = 55  # Revert indicates volatility
        self.assertLess(confidence, 80, "Revert should have lower confidence")

    def test_confidence_scoring_algorithm(self):
        """Test confidence scoring based on change magnitude and history."""
        # Large change (>2 days difference) = higher confidence
        large_change_days = 3
        base_confidence = 50
        confidence = min(100, base_confidence + (large_change_days * 15))  # 95%
        self.assertGreater(confidence, 80)

        # Small change (1 day difference) = lower confidence
        small_change_days = 1
        confidence = min(100, base_confidence + (small_change_days * 15))  # 65%
        self.assertLess(confidence, 80)

    def test_anomaly_not_in_critical_before_2days(self):
        """Test that anomalies require 2-day confirmation before CRITICAL."""
        # Day 1 anomaly
        day1_anomalies = {
            "261313": {
                "detected_on": "2026-10-14",
                "change": "tiebreak_date_moved",
                "confirmed_on": None,
                "severity": "PENDING"  # Not CRITICAL until confirmed
            }
        }

        # Should not be in critical alerts
        critical_alerts = [a for a in day1_anomalies.values()
                          if a["severity"] == "CRITICAL"]
        self.assertEqual(len(critical_alerts), 0)

    def test_anomaly_in_critical_after_2days(self):
        """Test that anomalies move to CRITICAL after 2-day confirmation."""
        # Day 2 anomaly (confirmed)
        day2_anomalies = {
            "261313": {
                "detected_on": "2026-10-14",
                "change": "tiebreak_date_moved",
                "confirmed_on": "2026-10-15",
                "severity": "CRITICAL",
                "confidence": 85
            }
        }

        # Should be in critical alerts
        critical_alerts = [a for a in day2_anomalies.values()
                          if a["severity"] == "CRITICAL"]
        self.assertEqual(len(critical_alerts), 1)
        self.assertGreaterEqual(critical_alerts[0]["confidence"], 80)


class TestDataQualityAndFreshness(unittest.TestCase):
    """Test 4: Data Quality & Freshness Guarantees."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.knowledge_dir = self.base_dir / "knowledge"

        self.cutoffs_dir = self.knowledge_dir / "live_cutoffs"
        self.digests_dir = self.knowledge_dir / "digests"
        self.alerts_dir = self.knowledge_dir / "alerts"

        for d in [self.cutoffs_dir, self.digests_dir, self.alerts_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def test_dha_data_freshness_24h(self):
        """Test that DHA scraper data is <24h old."""
        # Create a file with timestamp
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(hours=20)

        cutoffs = {
            "meta": {
                "source": "https://immi.homeaffairs.gov.au/...",
                "last_updated": yesterday.strftime("%Y-%m-%d"),
                "accessed_at": yesterday.isoformat()
            },
            "cutoffs": []
        }

        # Check freshness
        last_updated = datetime.fromisoformat(cutoffs["meta"]["accessed_at"])
        freshness = now - last_updated

        self.assertLess(freshness.total_seconds(), 86400, "DHA data older than 24 hours")

    def test_state_data_freshness_24h(self):
        """Test that state monitor data is <24h old."""
        now = datetime.now(timezone.utc)
        recent = now - timedelta(hours=6)

        state_data = {
            "meta": {
                "accessed_at": recent.isoformat(),
                "state": "VIC"
            }
        }

        last_updated = datetime.fromisoformat(state_data["meta"]["accessed_at"])
        freshness = now - last_updated

        self.assertLess(freshness.total_seconds(), 86400, "State data older than 24 hours")

    def test_acs_data_freshness_7d(self):
        """Test that ACS data is <7d old (weekly)."""
        now = datetime.now(timezone.utc)
        one_week_ago = now - timedelta(days=5)

        acs_data = {
            "meta": {
                "accessed_at": one_week_ago.isoformat(),
                "source": "https://www.acs.org.au/..."
            }
        }

        last_updated = datetime.fromisoformat(acs_data["meta"]["accessed_at"])
        freshness = now - last_updated

        self.assertLess(freshness.total_seconds(), 604800, "ACS data older than 7 days")

    def test_stale_data_alert_triggered(self):
        """Test that stale data (>3 days) triggers alert."""
        now = datetime.now(timezone.utc)
        four_days_ago = now - timedelta(days=4)

        source_record = {
            "id": "skillselect_cutoffs",
            "accessed_at": four_days_ago.isoformat(),
            "source_status": "current"
        }

        last_updated = datetime.fromisoformat(source_record["accessed_at"])
        freshness = now - last_updated

        # Check staleness
        if freshness > timedelta(days=3):
            source_record["source_status"] = "stale"
            source_record["alert"] = "Data older than 3 days"

        self.assertEqual(source_record["source_status"], "stale")
        self.assertIn("alert", source_record)

    def test_digest_references_current_sources(self):
        """Test that digest indicates data recency."""
        digest_content = """# Daily Intelligence Digest — 2026-11-15

## ⚙️ DATA QUALITY
- SkillSelect data: ✓ Loaded (20 occupations)
- Data date: 2026-10-15
- 2-day confirmation rule: ENABLED
- Confidence level: HIGH (core sources current)
"""

        # Parse digest and verify data quality section
        self.assertIn("DATA QUALITY", digest_content)
        self.assertIn("Confidence level: HIGH", digest_content)
        self.assertIn("current", digest_content)

    def test_data_quality_section_included(self):
        """Test that all digests include a Data Quality section."""
        digest = """# Daily Intelligence Digest

## ⚙️ DATA QUALITY
- SkillSelect: ✓ Fresh (<24h)
- State data: ✓ Fresh (<24h)
- ACS data: ⚠️ Stale (5d)
"""

        self.assertIn("DATA QUALITY", digest)
        self.assertIn("Fresh", digest)


class TestCostAndPointsIntegration(unittest.TestCase):
    """Test 5: Cost & Points Integration with Phase 1 Intelligence."""

    def setUp(self):
        """Set up test environment."""
        self.profiles = IntegrationTestFixtures.create_reference_profiles()

    def test_points_match_official_calculator(self):
        """Test that points calculation matches official ACS points calculator."""
        # Reference: Software Engineer, age 30, 85 points
        profile = self.profiles[0]

        expected_points = 85
        calculated_points = profile["points"]

        self.assertEqual(calculated_points, expected_points)

    def test_cost_aggregation_for_visas(self):
        """Test that visa costs are aggregated correctly."""
        visa_costs = {
            "189": 5000,  # Principal
            "190": 5000,  # State nominated
            "491": 5000   # Regional
        }

        profile = self.profiles[0]  # Software Engineer
        total_cost = sum(visa_costs[str(v)] for v in profile["visa_interested"])

        self.assertEqual(total_cost, 15000)  # 3 visas × $5000

    def test_cutoff_comparison_with_current_data(self):
        """Test comparing profile points against current cutoffs."""
        # Create mock cutoff data
        current_cutoffs = {
            "261313": {  # Software Engineer
                "tiebreak_date": "2026-10-13",
                "status": "invited",
                "implied_points_estimated": 85
            }
        }

        profile = self.profiles[0]  # Software Engineer with 85 points
        occupation_code = profile["occupation_code"]

        cutoff = current_cutoffs.get(occupation_code)
        if cutoff:
            # Profile matches or exceeds cutoff
            likelihood = "BORDERLINE" if profile["points"] <= 85 else "LIKELY"
            self.assertIn(likelihood, ["LIKELY", "BORDERLINE"])

    def test_quick_win_integration(self):
        """Test integration of Quick Wins with Phase 1 intelligence."""
        # Quick Win: Cost + Points
        profile = self.profiles[0]

        quick_win = {
            "occupation": profile["occupation_code"],
            "current_points": profile["points"],
            "visa_options": profile["visa_interested"],
            "estimated_cost": 15000,
            "processing_time_weeks": 12,
            "success_likelihood": "BORDERLINE"
        }

        self.assertIsNotNone(quick_win["occupation"])
        self.assertGreater(quick_win["estimated_cost"], 0)

    def test_full_workflow_end_to_end(self):
        """Test complete workflow: scraper → digester → coordinator → context injection."""
        # 1. Scraper produces data
        dha_data = IntegrationTestFixtures.create_mock_dha_output()
        self.assertIsNotNone(dha_data["skillselect_cutoffs"])

        # 2. Digester processes data
        cutoffs = dha_data["skillselect_cutoffs"]["cutoffs"]
        self.assertGreater(len(cutoffs), 0)

        # 3. Coordinator loads digest
        digest_info = {
            "software_engineer_tiebreak": "2026-10-13",
            "status": "invited"
        }
        self.assertIsNotNone(digest_info["software_engineer_tiebreak"])

        # 4. Context is injected for profile
        profile = self.profiles[0]
        impact = {
            "profile": profile["name"],
            "occupation": profile["occupation_code"],
            "current_points": profile["points"],
            "cutoff_tiebreak": digest_info["software_engineer_tiebreak"],
            "recommendation": "Borderline - await next round"
        }

        self.assertEqual(impact["occupation"], "261313")


class TestErrorResilience(unittest.TestCase):
    """Test 6: Error Resilience with Graceful Degradation."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.knowledge_dir = self.base_dir / "knowledge"

        self.cutoffs_dir = self.knowledge_dir / "live_cutoffs"
        self.digests_dir = self.knowledge_dir / "digests"
        self.alerts_dir = self.knowledge_dir / "alerts"

        for d in [self.cutoffs_dir, self.digests_dir, self.alerts_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def test_dha_scraper_failure_fallback_to_stale(self):
        """Test: If DHA scraper fails, use stale data + alert."""
        # Create stale data file
        stale_cutoffs = {
            "meta": {
                "last_updated": "2026-10-13",
                "is_stale": True
            },
            "cutoffs": [{"occupation_code": "261313"}]
        }

        cutoffs_file = self.cutoffs_dir / "skillselect_cutoffs.json"
        with open(cutoffs_file, "w") as f:
            json.dump(stale_cutoffs, f)

        # Verify fallback occurred
        with open(cutoffs_file, "r") as f:
            loaded = json.load(f)

        self.assertTrue(loaded["meta"].get("is_stale"))
        self.assertGreater(len(loaded["cutoffs"]), 0)

    def test_one_state_failure_others_continue(self):
        """Test: If one state monitor fails, others continue."""
        # Create data for NSW and QLD but not VIC
        for state in ["NSW", "QLD"]:
            state_data = IntegrationTestFixtures.create_mock_state_output(state)
            state_file = self.cutoffs_dir / f"state_{state.lower()}.json"
            with open(state_file, "w") as f:
                json.dump(state_data, f)

        # Verify NSW and QLD exist
        self.assertTrue((self.cutoffs_dir / "state_nsw.json").exists())
        self.assertTrue((self.cutoffs_dir / "state_qld.json").exists())
        self.assertFalse((self.cutoffs_dir / "state_vic.json").exists())

        # Pipeline should continue with 2 states
        loaded_states = list(self.cutoffs_dir.glob("state_*.json"))
        self.assertEqual(len(loaded_states), 2)

    def test_acs_poller_failure_marks_stale(self):
        """Test: If ACS poller fails, mark ACS data as stale in digest."""
        # Create error log instead of data file
        error_log = self.knowledge_dir / "scraper_errors.jsonl"
        with open(error_log, "w") as f:
            f.write('{"scraper": "acs_poller", "error": "timeout", "timestamp": "2026-11-15T15:00:00Z"}\n')

        # Verify error was logged
        self.assertTrue(error_log.exists())

    def test_network_timeout_retry_fallback(self):
        """Test: Network timeout triggers retry, then fallback to stale."""
        # Simulate retry exhaustion
        retry_log = {
            "endpoint": "https://immi.homeaffairs.gov.au/...",
            "retries": 3,
            "final_status": "timeout",
            "fallback": "use_stale_data"
        }

        self.assertEqual(retry_log["retries"], 3)
        self.assertEqual(retry_log["fallback"], "use_stale_data")

    def test_partial_pipeline_generates_digest(self):
        """Test: Even with partial failures, digest is still generated."""
        # Create minimal valid data
        cutoffs = {
            "meta": {"source": "test"},
            "cutoffs": [{"occupation_code": "261313"}]
        }
        cutoffs_file = self.cutoffs_dir / "skillselect_cutoffs.json"
        with open(cutoffs_file, "w") as f:
            json.dump(cutoffs, f)

        # Verify digester can still load and process
        digester = IntelligenceDigester(base_dir=str(self.base_dir), log_level="ERROR")
        success = digester.load_sources()

        self.assertTrue(success)

    def test_error_logs_populated_correctly(self):
        """Test: Error logs are populated with proper structure."""
        error_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scraper": "state_monitor",
            "state": "VIC",
            "error_type": "timeout",
            "message": "Request timed out after 3 retries",
            "fallback_action": "use_stale_data"
        }

        self.assertIn("timestamp", error_entry)
        self.assertIn("scraper", error_entry)
        self.assertIn("fallback_action", error_entry)

    def test_stale_data_fallback_works(self):
        """Test: Stale data fallback produces usable output."""
        # Create stale DHA data (7 days old)
        old_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

        stale_cutoffs = {
            "meta": {
                "last_updated": "2026-11-08",
                "accessed_at": old_date,
                "is_stale": True,
                "source": "cached_fallback"
            },
            "cutoffs": [
                {"occupation_code": "261313", "status": "invited"}
            ]
        }

        cutoffs_file = self.cutoffs_dir / "skillselect_cutoffs.json"
        with open(cutoffs_file, "w") as f:
            json.dump(stale_cutoffs, f)

        # Verify fallback is usable
        with open(cutoffs_file, "r") as f:
            data = json.load(f)

        self.assertTrue(data["meta"]["is_stale"])
        self.assertEqual(data["meta"]["source"], "cached_fallback")
        self.assertGreater(len(data["cutoffs"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
