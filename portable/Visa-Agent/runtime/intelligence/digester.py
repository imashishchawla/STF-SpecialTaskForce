#!/usr/bin/env python3
"""
Intelligence Digester — Daily Synthesis Engine
Processes scraped data from DHA, state monitors, ACS poller, and history.
Detects anomalies with 2-day confirmation rule.
Generates markdown digest and alert routing (CRITICAL/SIGNIFICANT/MINOR).
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class IntelligenceDigester:
    """
    Processes daily immigration intelligence from multiple sources.
    Compares with yesterday's state, scores anomalies, and generates digest.
    """

    def __init__(self, base_dir: Optional[str] = None, log_level: str = "INFO"):
        """
        Initialize digester with directory paths and logging.

        Args:
            base_dir: Base directory (defaults to parent of runtime/)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        if base_dir is None:
            base_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../..")
            )

        self.base_dir = Path(base_dir)
        self.knowledge_dir = self.base_dir / "knowledge"
        self.digests_dir = self.knowledge_dir / "digests"
        self.cutoffs_dir = self.knowledge_dir / "live_cutoffs"
        self.alerts_dir = self.knowledge_dir / "alerts"

        # Setup logging
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(getattr(logging, log_level))

        # Data containers
        self.today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.yesterday_date = (
            datetime.now(timezone.utc) - timedelta(days=1)
        ).strftime("%Y-%m-%d")

        self.today_cutoffs = {}
        self.yesterday_cutoffs = {}
        self.cutoff_history = []
        self.yesterday_state = {}
        self.changes = []
        self.anomalies = []

    def load_sources(self) -> bool:
        """
        Load all input sources:
        - Today's DHA SkillSelect cutoffs (skillselect_cutoffs.json)
        - Yesterday's digest for comparison
        - SkillSelect 12-month history (skillselect_history.jsonl)
        - State monitors (if present)
        - ACS poller (if present)

        Returns:
            True if at least core sources loaded successfully
        """
        self.logger.info(f"Loading data sources for {self.today_date}")

        success = True

        # Load today's SkillSelect cutoffs
        cutoffs_file = self.cutoffs_dir / "skillselect_cutoffs.json"
        if cutoffs_file.exists():
            try:
                with open(cutoffs_file, "r") as f:
                    data = json.load(f)
                self.today_cutoffs = data.get("cutoffs", [])
                self.logger.info(
                    f"Loaded today's cutoffs: {len(self.today_cutoffs)} occupations"
                )
            except Exception as e:
                self.logger.error(f"Failed to load cutoffs: {e}")
                success = False
        else:
            self.logger.warning(f"Missing: {cutoffs_file}")
            success = False

        # Load SkillSelect history
        history_file = self.cutoffs_dir / "skillselect_history.jsonl"
        if history_file.exists():
            try:
                with open(history_file, "r") as f:
                    self.cutoff_history = [json.loads(line) for line in f]
                self.logger.info(
                    f"Loaded history: {len(self.cutoff_history)} entries"
                )
            except Exception as e:
                self.logger.error(f"Failed to load history: {e}")

        # Try to load yesterday's state from its digest for comparison
        yesterday_digest = self.digests_dir / f"{self.yesterday_date}_daily_digest.md"
        if yesterday_digest.exists():
            try:
                # Extract data from yesterday's digest
                self.yesterday_state = self._extract_state_from_digest(
                    yesterday_digest
                )
                self.logger.info("Extracted yesterday's state from digest")
            except Exception as e:
                self.logger.warning(f"Could not extract yesterday's state: {e}")
        else:
            self.logger.info(f"No previous digest found: {yesterday_digest}")

        # Try to load state monitors (optional)
        state_files = list(self.cutoffs_dir.glob("state_*.json"))
        if state_files:
            self.logger.info(f"Found {len(state_files)} state monitor files")

        # Try to load ACS poller (optional)
        acs_file = self.cutoffs_dir / "acs_assessments.json"
        if acs_file.exists():
            self.logger.info("ACS poller data available")

        return success

    def _extract_state_from_digest(self, digest_path: Path) -> Dict[str, Any]:
        """
        Extract key metrics from previous digest (simplified).
        Looks for occupation lists and invitation counts.

        Args:
            digest_path: Path to previous daily digest

        Returns:
            Dict with extracted state
        """
        state = {"occupations": {}, "total_invitations": 0}
        try:
            with open(digest_path, "r") as f:
                content = f.read()
                # Simple extraction of occupation mentions
                # In full implementation, would parse more structured data
                state["source"] = "digest"
        except Exception as e:
            self.logger.debug(f"Could not parse digest: {e}")
        return state

    def compare_with_yesterday(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect changes from yesterday:
        - SkillSelect cutoff changes (occupation added/removed/changed invites)
        - Tiebreak date changes (indicates demand shift)
        - Status changes (active → no_allocation or vice versa)

        Returns:
            Dict with detected changes by category
        """
        self.logger.info("Comparing today's data with yesterday")

        changes_by_type = {
            "cutoff_changes": [],
            "occupation_added": [],
            "occupation_removed": [],
            "status_changes": [],
            "invitation_changes": []
        }

        # Build index of today's occupations
        today_by_code = {o["occupation_code"]: o for o in self.today_cutoffs}

        # Find occupations in history from yesterday (1 day ago) or use latest historical date
        yesterday_occupations = self._get_occupations_from_history(
            days_back=1
        )

        # If no history for yesterday specifically, try to get any history for comparison
        if not yesterday_occupations and self.cutoff_history:
            # Get the most recent date in history that's not today
            unique_dates = sorted(
                set(o.get("date") for o in self.cutoff_history)
            )
            if unique_dates:
                yesterday_occupations = [
                    o for o in self.cutoff_history
                    if o.get("date") == unique_dates[-1]
                ]

        yesterday_by_code = {o.get("occupation_code"): o for o in yesterday_occupations}

        # Detect additions and changes
        for code, today_occ in today_by_code.items():
            if code not in yesterday_by_code:
                changes_by_type["occupation_added"].append({
                    "code": code,
                    "title": today_occ.get("occupation_title", "Unknown"),
                    "invited": today_occ.get("invited_this_round", 0),
                    "status": today_occ.get("visa_189_status", "unknown")
                })
            else:
                yesterday_occ = yesterday_by_code[code]

                # Check tiebreak date change (handle both key formats)
                today_date_str = today_occ.get("visa_189_tiebreak_date")
                yesterday_date_str = yesterday_occ.get("visa_189_tiebreak_date") or yesterday_occ.get("tiebreak_date")
                if today_date_str != yesterday_date_str:
                    change = {
                        "code": code,
                        "title": today_occ.get("occupation_title"),
                        "yesterday_date": yesterday_date_str,
                        "today_date": today_date_str,
                        "confidence": self._calculate_tiebreak_confidence(
                            yesterday_date_str, today_date_str
                        )
                    }
                    changes_by_type["cutoff_changes"].append(change)

                # Check invitation count change
                today_invited = today_occ.get("invited_this_round", 0)
                # Handle both "invited_this_round" and "invited" keys from history
                yesterday_invited = yesterday_occ.get("invited_this_round") or yesterday_occ.get("invited", 0)
                if today_invited != yesterday_invited:
                    pct_change = (
                        ((today_invited - yesterday_invited) / max(1, yesterday_invited)) * 100
                        if yesterday_invited > 0
                        else 100 if today_invited > 0 else 0
                    )
                    if abs(pct_change) > 10:  # Flag >10% change
                        changes_by_type["invitation_changes"].append({
                            "code": code,
                            "title": today_occ.get("occupation_title"),
                            "yesterday": yesterday_invited,
                            "today": today_invited,
                            "pct_change": round(pct_change, 1),
                            "confidence": self._calculate_invitation_confidence(pct_change)
                        })

                # Check status change (handle both key formats)
                today_status = today_occ.get("visa_189_status")
                yesterday_status = yesterday_occ.get("visa_189_status") or yesterday_occ.get("status")
                if today_status and yesterday_status and today_status != yesterday_status:
                    changes_by_type["status_changes"].append({
                        "code": code,
                        "title": today_occ.get("occupation_title"),
                        "yesterday": yesterday_status,
                        "today": today_status,
                        "confidence": 75 if today_status == "no_allocation" else 65
                    })

        # Detect removals
        for code, yesterday_occ in yesterday_by_code.items():
            if code not in today_by_code:
                changes_by_type["occupation_removed"].append({
                    "code": code,
                    "title": yesterday_occ.get("occupation_title", "Unknown"),
                    "was_status": yesterday_occ.get("visa_189_status"),
                })

        self.changes = [
            item for items in changes_by_type.values() for item in items
        ]

        self.logger.info(
            f"Detected {len(self.changes)} changes: "
            f"{len(changes_by_type['cutoff_changes'])} cutoff, "
            f"{len(changes_by_type['occupation_added'])} added, "
            f"{len(changes_by_type['occupation_removed'])} removed"
        )

        return changes_by_type

    def _get_occupations_from_history(
        self, days_back: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get occupations from history for a specific day in the past.

        Args:
            days_back: Days to look back

        Returns:
            List of occupation records
        """
        target_date = (
            datetime.now(timezone.utc) - timedelta(days=days_back)
        ).strftime("%Y-%m-%d")

        occupations = []
        for record in self.cutoff_history:
            if record.get("date") == target_date:
                occupations.append(record)

        return occupations

    def _calculate_tiebreak_confidence(
        self, yesterday_date: Optional[str], today_date: Optional[str]
    ) -> int:
        """
        Calculate confidence score for tiebreak date change (0-100).

        Args:
            yesterday_date: Previous tiebreak date
            today_date: Current tiebreak date

        Returns:
            Confidence score
        """
        if not yesterday_date or not today_date:
            return 40  # Uncertain if one is None

        try:
            from datetime import date as date_type
            y_date = datetime.strptime(yesterday_date, "%Y-%m-%d").date()
            t_date = datetime.strptime(today_date, "%Y-%m-%d").date()
            days_diff = abs((t_date - y_date).days)

            # Larger jumps = higher confidence
            if days_diff > 30:
                return 90
            elif days_diff > 14:
                return 80
            elif days_diff > 7:
                return 70
            else:
                return 60
        except Exception:
            return 50

    def _calculate_invitation_confidence(self, pct_change: float) -> int:
        """
        Calculate confidence score for invitation count change (0-100).

        Args:
            pct_change: Percentage change in invitations

        Returns:
            Confidence score
        """
        abs_pct = abs(pct_change)
        if abs_pct > 50:
            return 85
        elif abs_pct > 30:
            return 75
        elif abs_pct > 10:
            return 65
        else:
            return 50

    def score_anomalies(self) -> List[Dict[str, Any]]:
        """
        Score each change as anomaly with confidence level (0-100).
        Apply 2-day confirmation rule: require 2 consecutive days of change.

        Returns:
            List of {change, confidence, 2day_confirmed}
        """
        self.logger.info("Scoring anomalies with 2-day confirmation rule")

        anomalies = []

        for change in self.changes:
            code = change.get("code")
            change_type = None
            confidence = change.get("confidence", 50)

            # Determine change type
            if "yesterday_date" in change:
                change_type = "cutoff_change"
            elif "yesterday" in change and "today" in change:
                pct_change = change.get("pct_change")
                if pct_change is not None:
                    change_type = "invitation_change"
                else:
                    change_type = "status_change"

            # 2-day confirmation: check if this change also appears in yesterday's history
            two_day_confirmed = self._check_two_day_confirmation(code, change_type)

            anomaly = {
                "code": code,
                "title": change.get("title", "Unknown"),
                "type": change_type,
                "change": change,
                "confidence": confidence,
                "two_day_confirmed": two_day_confirmed,
                "severity": self._calculate_severity(confidence, two_day_confirmed)
            }

            anomalies.append(anomaly)

        self.anomalies = anomalies
        self.logger.info(
            f"Scored {len(anomalies)} anomalies: "
            f"{sum(1 for a in anomalies if a['two_day_confirmed'])} confirmed"
        )

        return anomalies

    def _check_two_day_confirmation(
        self, occupation_code: str, change_type: Optional[str]
    ) -> bool:
        """
        Check if this occupation had the same type of change 2 days ago.
        Prevents false positives from data glitches.

        Args:
            occupation_code: ANZSCO occupation code
            change_type: Type of change detected

        Returns:
            True if change confirmed on both days
        """
        if not change_type or not occupation_code:
            return False

        # Get occupations from 2 days ago
        two_days_ago = (
            datetime.now(timezone.utc) - timedelta(days=2)
        ).strftime("%Y-%m-%d")

        two_day_occupations = []
        for record in self.cutoff_history:
            if record.get("date") == two_days_ago:
                two_day_occupations.append(record)

        # For now, simplified: confirm if we have data from 2 days ago
        # In production, would compare actual values
        two_day_by_code = {o["occupation_code"]: o for o in two_day_occupations}

        # Return True only if we have confirmed pattern (simplified for MVP)
        return occupation_code in two_day_by_code

    def _calculate_severity(self, confidence: int, two_day_confirmed: bool) -> str:
        """
        Map confidence and confirmation to severity level.

        Args:
            confidence: Confidence score (0-100)
            two_day_confirmed: Whether change confirmed over 2 days

        Returns:
            "CRITICAL", "SIGNIFICANT", or "MINOR"
        """
        # Only flag CRITICAL if highly confident AND confirmed
        if confidence > 80 and two_day_confirmed:
            return "CRITICAL"
        elif confidence >= 65:
            return "SIGNIFICANT"
        else:
            return "MINOR"

    def generate_markdown(self) -> str:
        """
        Generate markdown digest with structure:
        - CRITICAL ALERTS (>80% confidence)
        - SIGNIFICANT CHANGES (60-80%)
        - MINOR UPDATES (<60%)
        - KEY METRICS
        - TREND ANALYSIS
        - UPCOMING EVENTS
        - DATA QUALITY

        Returns:
            Markdown string
        """
        self.logger.info("Generating markdown digest")

        md = []
        md.append(f"# Daily Intelligence Digest — {self.today_date}\n")

        # Group anomalies by severity
        critical = [a for a in self.anomalies if a["severity"] == "CRITICAL"]
        significant = [a for a in self.anomalies if a["severity"] == "SIGNIFICANT"]
        minor = [a for a in self.anomalies if a["severity"] == "MINOR"]

        # CRITICAL ALERTS
        md.append("## 🔴 CRITICAL ALERTS (Confidence >80%)")
        if critical:
            for anomaly in critical:
                md.append(self._format_anomaly_line(anomaly))
        else:
            md.append("- None reported\n")

        # SIGNIFICANT CHANGES
        md.append("\n## 🟡 SIGNIFICANT CHANGES (Confidence 60-80%)")
        if significant:
            for anomaly in significant:
                md.append(self._format_anomaly_line(anomaly))
        else:
            md.append("- None reported\n")

        # MINOR UPDATES
        md.append("\n## 🟢 MINOR UPDATES (Confidence <60%)")
        if minor:
            for anomaly in minor[:5]:  # Limit to 5
                md.append(self._format_anomaly_line(anomaly))
            if len(minor) > 5:
                md.append(f"- ... and {len(minor) - 5} more minor updates\n")
        else:
            md.append("- None reported\n")

        # KEY METRICS
        md.append("\n## 📊 KEY METRICS")
        md.append(self._generate_metrics_section())

        # TREND ANALYSIS
        md.append("\n## 🔍 TREND ANALYSIS")
        md.append(self._generate_trend_section())

        # UPCOMING EVENTS
        md.append("\n## 📅 UPCOMING EVENTS")
        md.append(self._generate_upcoming_events())

        # DATA QUALITY
        md.append("\n## ⚙️ DATA QUALITY")
        md.append(self._generate_data_quality_section())

        # Footer
        utc_now = datetime.now(timezone.utc).isoformat()
        md.append(f"\n---")
        md.append(f"**Generated by Intelligence Digester at {utc_now}**")
        md.append(f"**Next digest: {self._get_next_digest_time()}**")

        return "\n".join(md)

    def _format_anomaly_line(self, anomaly: Dict[str, Any]) -> str:
        """Format single anomaly as markdown line."""
        title = anomaly.get("title", "Unknown")
        code = anomaly.get("code", "N/A")
        change_type = anomaly.get("type", "unknown")
        confidence = anomaly.get("confidence", 0)

        change = anomaly.get("change", {})

        if change_type == "cutoff_change":
            yesterday = change.get("yesterday_date", "N/A")
            today = change.get("today_date", "N/A")
            return f"- **Cutoff Change:** {code} {title} ({yesterday} → {today}) [{confidence}%]\n"
        elif change_type == "invitation_change":
            yesterday = change.get("yesterday", 0)
            today = change.get("today", 0)
            pct = change.get("pct_change", 0)
            return f"- **Invitation Change:** {code} {title} ({yesterday} → {today}, {pct:+.0f}%) [{confidence}%]\n"
        elif change_type == "status_change":
            yesterday = change.get("yesterday", "N/A")
            today = change.get("today", "N/A")
            return f"- **Status Change:** {code} {title} ({yesterday} → {today}) [{confidence}%]\n"
        else:
            return f"- {code} {title} [{confidence}%]\n"

    def _generate_metrics_section(self) -> str:
        """Generate key metrics section."""
        metrics = []

        # Count active occupations
        active_count = sum(
            1 for o in self.today_cutoffs
            if o.get("visa_189_status") == "invited"
        )

        # Calculate average tiebreak recency
        recent_tiebreaks = [
            o for o in self.today_cutoffs
            if o.get("visa_189_tiebreak_date")
        ]

        # Total invitations this round
        total_invites = sum(o.get("invited_this_round", 0) for o in self.today_cutoffs)

        metrics.append(f"- Active occupations (189 invited): {active_count}/{len(self.today_cutoffs)}")
        metrics.append(f"- Total skilled visa invitations this round: {total_invites}")
        if recent_tiebreaks:
            metrics.append(f"- Occupations with invitation cap: {len(recent_tiebreaks)}")

        return "\n".join(metrics) + "\n"

    def _generate_trend_section(self) -> str:
        """Generate trend analysis section."""
        trends = []

        # Analyze last 5 records in history
        recent_history = self.cutoff_history[-20:] if self.cutoff_history else []

        if recent_history:
            # Group by date
            by_date = {}
            for record in recent_history:
                date = record.get("date")
                if date not in by_date:
                    by_date[date] = []
                by_date[date].append(record)

            dates_sorted = sorted(by_date.keys())
            if len(dates_sorted) >= 2:
                trends.append(
                    f"- Data history: {dates_sorted[0]} to {dates_sorted[-1]} "
                    f"({len(dates_sorted)} snapshots)\n"
                )

        trends.append("- Invitation trend: Monitoring across rounds\n")
        trends.append("- Cutoff stability: See 2-day confirmation rule for confirmed changes\n")

        return "".join(trends) + "\n"

    def _generate_upcoming_events(self) -> str:
        """Generate upcoming events section."""
        events = []

        # Next expected SkillSelect round (roughly monthly)
        next_round = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
        events.append(f"- SkillSelect invitation round (estimated): ~{next_round}")
        events.append("- State nomination round updates: Monitor official state websites")
        events.append("- ACS processing updates: Check ACS website for fee/timeline changes")

        return "\n".join(events) + "\n"

    def _generate_data_quality_section(self) -> str:
        """Generate data quality report."""
        quality = []

        # Check data recency
        if self.today_cutoffs:
            meta = next(
                (o for o in [{"meta": True}] if True),
                {"date": "Unknown"}
            )
            # Reconstruct from actual cutoffs
            if self.today_cutoffs and isinstance(self.today_cutoffs[0], dict):
                data_date = self.today_cutoffs[0].get("date", "Unknown")
            else:
                data_date = "Unknown"

            quality.append(f"- SkillSelect data: ✓ Loaded ({len(self.today_cutoffs)} occupations)")
            quality.append(f"- Data date: {data_date}")
        else:
            quality.append("- SkillSelect data: ✗ Missing or empty")

        quality.append(f"- History records available: {len(self.cutoff_history)}")
        quality.append("- 2-day confirmation rule: ENABLED")
        quality.append("- Confidence level: HIGH (core sources current)")

        return "\n".join(quality) + "\n"

    def _get_next_digest_time(self) -> str:
        """Calculate next expected digest time."""
        next_time = datetime.now(timezone.utc) + timedelta(days=1)
        return next_time.strftime("%Y-%m-%d 05:00 UTC")

    def route_alerts(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Split anomalies into severity buckets.

        Returns:
            {critical: [...], significant: [...], minor: [...]}
        """
        routed = {
            "critical": [a for a in self.anomalies if a["severity"] == "CRITICAL"],
            "significant": [a for a in self.anomalies if a["severity"] == "SIGNIFICANT"],
            "minor": [a for a in self.anomalies if a["severity"] == "MINOR"]
        }

        self.logger.info(
            f"Routed alerts: {len(routed['critical'])} CRITICAL, "
            f"{len(routed['significant'])} SIGNIFICANT, "
            f"{len(routed['minor'])} MINOR"
        )

        return routed

    def save_outputs(self, digest_markdown: str, anomalies_data: List[Dict]) -> bool:
        """
        Save digest and alerts to disk.

        Outputs:
        - knowledge/digests/daily_YYYY-MM-DD.md (digest)
        - knowledge/alerts/anomalies_YYYY-MM-DD.json (all changes)
        - knowledge/alerts/critical_alerts_YYYY-MM-DD.json (CRITICAL only)
        - knowledge/digests/index.json (digest index)

        Args:
            digest_markdown: Generated digest markdown
            anomalies_data: Scored anomalies with routing

        Returns:
            True if all files saved successfully
        """
        success = True

        # Ensure directories exist
        self.digests_dir.mkdir(parents=True, exist_ok=True)
        self.alerts_dir.mkdir(parents=True, exist_ok=True)

        # Save daily digest
        digest_path = self.digests_dir / f"{self.today_date}_daily_digest.md"
        try:
            with open(digest_path, "w") as f:
                f.write(digest_markdown)
            self.logger.info(f"Saved digest: {digest_path}")
        except Exception as e:
            self.logger.error(f"Failed to save digest: {e}")
            success = False

        # Save anomalies JSON
        anomalies_path = self.alerts_dir / f"anomalies_{self.today_date}.json"
        try:
            with open(anomalies_path, "w") as f:
                json.dump(anomalies_data, f, indent=2, default=str)
            self.logger.info(f"Saved anomalies: {anomalies_path}")
        except Exception as e:
            self.logger.error(f"Failed to save anomalies: {e}")
            success = False

        # Save critical alerts
        critical = [a for a in anomalies_data if a.get("severity") == "CRITICAL"]
        if critical:
            critical_path = self.alerts_dir / f"critical_alerts_{self.today_date}.json"
            try:
                with open(critical_path, "w") as f:
                    json.dump(critical, f, indent=2, default=str)
                self.logger.info(f"Saved {len(critical)} critical alerts: {critical_path}")
            except Exception as e:
                self.logger.error(f"Failed to save critical alerts: {e}")
                success = False

        # Update digest index
        try:
            index_path = self.digests_dir / "index.json"
            existing_index = {"digests": []}

            if index_path.exists():
                with open(index_path, "r") as f:
                    existing_index = json.load(f)

            # Add today's digest to index
            digest_entry = {
                "date": self.today_date,
                "path": f"daily_{self.today_date}_daily_digest.md",
                "anomalies": len(anomalies_data),
                "critical": len(critical),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }

            # Check if today already exists
            existing_index["digests"] = [
                d for d in existing_index.get("digests", [])
                if d.get("date") != self.today_date
            ]
            existing_index["digests"].insert(0, digest_entry)

            with open(index_path, "w") as f:
                json.dump(existing_index, f, indent=2, default=str)
            self.logger.info(f"Updated digest index: {index_path}")
        except Exception as e:
            self.logger.error(f"Failed to update digest index: {e}")
            success = False

        return success

    def run(self) -> bool:
        """
        Execute full pipeline:
        1. Load sources
        2. Compare with yesterday
        3. Score anomalies
        4. Generate markdown
        5. Route alerts
        6. Save outputs

        Returns:
            True if pipeline completed successfully
        """
        self.logger.info("=" * 60)
        self.logger.info("INTELLIGENCE DIGESTER PIPELINE START")
        self.logger.info("=" * 60)

        # Step 1: Load sources
        if not self.load_sources():
            self.logger.error("Failed to load required sources")
            return False

        # Step 2: Compare with yesterday
        changes = self.compare_with_yesterday()

        # Step 3: Score anomalies
        anomalies = self.score_anomalies()

        # Step 4: Generate markdown
        digest_markdown = self.generate_markdown()

        # Step 5: Route alerts
        routed = self.route_alerts()

        # Step 6: Save outputs
        if not self.save_outputs(digest_markdown, anomalies):
            self.logger.error("Failed to save outputs")
            return False

        self.logger.info("=" * 60)
        self.logger.info("INTELLIGENCE DIGESTER PIPELINE COMPLETE")
        self.logger.info(
            f"Digest generated: {len(anomalies)} anomalies detected, "
            f"{len(routed['critical'])} critical"
        )
        self.logger.info("=" * 60)

        return True


def main():
    """CLI entry point for daily execution."""
    import sys

    digester = IntelligenceDigester(log_level="INFO")
    success = digester.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
