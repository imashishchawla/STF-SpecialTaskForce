#!/usr/bin/env python3
"""
Master Workflow Integration Module

Provides functions to load daily digests, extract critical alerts, and inject
intelligence context into the Master Coordinator for case management.

Functions:
- load_daily_digest(digest_path) → Dict[str, Any]
- extract_critical_alerts(digest_content) → List[Dict[str, Any]]
- inject_intelligence_context(coordinator_context, digest) → Dict[str, Any]
- flag_occupation_impact(occupation_code, digest) → Optional[Dict[str, Any]]
- parse_digest_metrics(digest_content) → Dict[str, Any]
"""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class WorkflowIntegrationError(Exception):
    """Raised when digest loading or context injection fails."""
    pass


def load_daily_digest(digest_path: str) -> Dict[str, Any]:
    """
    Load and parse a daily markdown digest file.

    Args:
        digest_path: Path to the markdown digest file (e.g., 2026-11-15_daily_digest.md)

    Returns:
        Dictionary containing parsed digest data with structure:
        {
            "digest_date": "2026-11-15",
            "critical_alerts": [...],
            "significant_changes": [...],
            "minor_updates": [...],
            "metrics": {...},
            "data_quality": {...},
            "raw_content": "..."
        }

    Raises:
        WorkflowIntegrationError: If digest file not found or parsing fails
    """
    digest_file = Path(digest_path)

    if not digest_file.exists():
        raise WorkflowIntegrationError(f"Digest file not found: {digest_path}")

    try:
        with open(digest_file, "r") as f:
            content = f.read()
    except IOError as e:
        raise WorkflowIntegrationError(f"Failed to read digest file: {e}")

    # Parse digest content
    result = {
        "digest_date": _extract_digest_date(digest_file.name),
        "file_path": str(digest_file),
        "accessed_at": datetime.now(timezone.utc).isoformat(),
        "raw_content": content,
    }

    # Extract sections
    result["critical_alerts"] = extract_critical_alerts(content)
    result["significant_changes"] = _extract_significant_changes(content)
    result["minor_updates"] = _extract_minor_updates(content)
    result["metrics"] = parse_digest_metrics(content)
    result["data_quality"] = _extract_data_quality(content)

    return result


def extract_critical_alerts(digest_content: str) -> List[Dict[str, Any]]:
    """
    Extract CRITICAL alerts from digest markdown.

    Args:
        digest_content: Full markdown digest content

    Returns:
        List of critical alert dictionaries with structure:
        [
            {
                "occupation_code": "261313",
                "occupation_title": "Software Engineer",
                "alert_type": "tiebreak_change",
                "change_description": "tiebreak moved from ... to ...",
                "confidence": 85,
                "severity": "CRITICAL",
                "detected_date": "2026-11-15"
            },
            ...
        ]
    """
    alerts = []

    # Find CRITICAL ALERTS section
    critical_section = _extract_section(digest_content, r"## 🔴 CRITICAL ALERTS")
    if not critical_section:
        return alerts

    # Parse each alert line
    lines = critical_section.strip().split("\n")
    for line in lines:
        if not line.strip().startswith("-"):
            continue

        # Extract occupation code and details - support multiple formats
        # Format 1: "- **CRITICAL:** 261313 Software Engineer ... [85%]"
        # Format 2: "- 261313 Software Engineer (active → invited) [85%]"
        match = re.search(r"(\d{6})\s+(.+?)\s*(?:\((.+?)\))?\s*\[(\d+)%\]", line)
        if match:
            occupation_code = match.group(1)
            occupation_title = match.group(2).strip()
            change_desc = match.group(3) if match.group(3) else "change detected"
            confidence = int(match.group(4))

            alerts.append(
                {
                    "occupation_code": occupation_code,
                    "occupation_title": occupation_title,
                    "alert_type": _classify_alert_type(change_desc),
                    "change_description": change_desc,
                    "confidence": confidence,
                    "severity": "CRITICAL",
                    "detected_date": _extract_digest_date_from_content(digest_content),
                }
            )

    return alerts


def inject_intelligence_context(
    coordinator_context: Dict[str, Any], digest: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Inject intelligence context from digest into coordinator state.

    Args:
        coordinator_context: Coordinator case context
        digest: Parsed digest data from load_daily_digest()

    Returns:
        Enhanced coordinator context with injected intelligence:
        {
            ...(original context),
            "intelligence": {
                "digest_date": "2026-11-15",
                "digest_file": "/path/to/digest.md",
                "critical_alerts": [...],
                "occupation_impacts": {...},
                "data_freshness": {...},
                "next_update": "2026-11-16T05:00:00Z"
            }
        }
    """
    if not coordinator_context:
        coordinator_context = {}

    # Add intelligence block
    intelligence = {
        "digest_date": digest.get("digest_date"),
        "digest_file": digest.get("file_path"),
        "loaded_at": digest.get("accessed_at"),
        "critical_alerts": digest.get("critical_alerts", []),
        "significant_changes": digest.get("significant_changes", []),
        "metrics": digest.get("metrics", {}),
        "data_freshness": digest.get("data_quality", {}).get("freshness_status"),
        "confidence_level": digest.get("data_quality", {}).get("confidence_level"),
    }

    # Calculate next digest update time (typically UTC+5 hours)
    if intelligence["digest_date"]:
        try:
            digest_dt = datetime.strptime(intelligence["digest_date"], "%Y-%m-%d")
            next_update = digest_dt.replace(hour=5, minute=0, second=0, tzinfo=timezone.utc)
            # If past 5 AM today, next update is tomorrow
            if next_update < datetime.now(timezone.utc):
                from datetime import timedelta

                next_update += timedelta(days=1)
            intelligence["next_update"] = next_update.isoformat()
        except ValueError:
            intelligence["next_update"] = None

    coordinator_context["intelligence"] = intelligence
    return coordinator_context


def flag_occupation_impact(
    occupation_code: str, digest: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Check if an occupation has critical alerts in the digest.

    Args:
        occupation_code: ANZSCO occupation code (e.g., "261313")
        digest: Parsed digest data from load_daily_digest()

    Returns:
        Dictionary with occupation impact info if found:
        {
            "occupation_code": "261313",
            "occupation_title": "Software Engineer",
            "has_critical_alert": True,
            "alert_details": {...},
            "recommendation": "Your application may be affected - review cutoff changes",
            "flag_type": "CRITICAL" | "SIGNIFICANT" | "MINOR" | None
        }
        Or None if occupation not mentioned in digest

    Example:
        impact = flag_occupation_impact("261313", digest)
        if impact["has_critical_alert"]:
            notify_client(impact["recommendation"])
    """
    impact = None

    # Check critical alerts
    for alert in digest.get("critical_alerts", []):
        if alert["occupation_code"] == occupation_code:
            impact = {
                "occupation_code": occupation_code,
                "occupation_title": alert.get("occupation_title"),
                "has_critical_alert": True,
                "alert_details": alert,
                "recommendation": f"⚠️ CRITICAL: {alert.get('change_description')}. "
                f"Your application timeline may be affected. Review SkillSelect "
                f"immediately.",
                "flag_type": "CRITICAL",
            }
            return impact

    # Check significant changes
    for change in digest.get("significant_changes", []):
        if change.get("occupation_code") == occupation_code:
            impact = {
                "occupation_code": occupation_code,
                "occupation_title": change.get("occupation_title"),
                "has_critical_alert": False,
                "alert_details": change,
                "recommendation": f"Status change detected: {change.get('change_description')}. "
                f"Monitor next SkillSelect round.",
                "flag_type": "SIGNIFICANT",
            }
            return impact

    # Check minor updates
    for minor in digest.get("minor_updates", []):
        if minor.get("occupation_code") == occupation_code:
            impact = {
                "occupation_code": occupation_code,
                "occupation_title": minor.get("occupation_title"),
                "has_critical_alert": False,
                "alert_details": minor,
                "recommendation": f"Minor update recorded. No immediate action required.",
                "flag_type": "MINOR",
            }
            return impact

    return None


def parse_digest_metrics(digest_content: str) -> Dict[str, Any]:
    """
    Parse KEY METRICS section from digest.

    Args:
        digest_content: Full markdown digest content

    Returns:
        Dictionary with metrics:
        {
            "active_occupations_189": 18,
            "total_occupations": 20,
            "total_invitations_189": 3094,
            "occupations_with_cap": 18
        }
    """
    metrics = {}

    metrics_section = _extract_section(digest_content, r"## 📊 KEY METRICS")
    if not metrics_section:
        return metrics

    # Extract key metrics
    lines = metrics_section.strip().split("\n")
    for line in lines:
        if "Active occupations" in line:
            match = re.search(r"(\d+)/(\d+)", line)
            if match:
                metrics["active_occupations_189"] = int(match.group(1))
                metrics["total_occupations"] = int(match.group(2))

        if "Total skilled visa invitations" in line:
            match = re.search(r"(\d+)", line.replace(",", ""))
            if match:
                metrics["total_invitations_189"] = int(match.group(1))

        if "Occupations with invitation cap" in line:
            match = re.search(r"(\d+)", line)
            if match:
                metrics["occupations_with_cap"] = int(match.group(1))

    return metrics


# ===== Private Helper Functions =====


def _extract_section(content: str, section_pattern: str) -> Optional[str]:
    """Extract a section from markdown by header pattern."""
    lines = content.split("\n")
    start_idx = None

    for i, line in enumerate(lines):
        if re.search(section_pattern, line):
            start_idx = i + 1
            break

    if start_idx is None:
        return None

    # Collect lines until next section header
    section_lines = []
    for i in range(start_idx, len(lines)):
        if lines[i].startswith("##"):
            break
        section_lines.append(lines[i])

    return "\n".join(section_lines)


def _extract_significant_changes(digest_content: str) -> List[Dict[str, Any]]:
    """Extract SIGNIFICANT CHANGES section."""
    changes = []

    sig_section = _extract_section(digest_content, r"## 🟡 SIGNIFICANT CHANGES")
    if not sig_section:
        return changes

    lines = sig_section.strip().split("\n")
    for line in lines:
        if not line.startswith("-"):
            continue

        # Parse similar to critical alerts
        match = re.search(r"(\d{6})\s+(.+?)\s+\((.+?)\)\s+\[(\d+)%\]", line)
        if match:
            changes.append(
                {
                    "occupation_code": match.group(1),
                    "occupation_title": match.group(2),
                    "change_description": match.group(3),
                    "confidence": int(match.group(4)),
                    "flag_type": "SIGNIFICANT",
                }
            )

    return changes


def _extract_minor_updates(digest_content: str) -> List[Dict[str, Any]]:
    """Extract MINOR UPDATES section."""
    updates = []

    minor_section = _extract_section(digest_content, r"## 🟢 MINOR UPDATES")
    if not minor_section:
        return updates

    lines = minor_section.strip().split("\n")
    for line in lines:
        if not line.startswith("-"):
            continue

        # Minor updates have simpler format
        match = re.search(r"(\d{6})\s+(.+?)\s+\[(\d+)%\]", line)
        if match:
            updates.append(
                {
                    "occupation_code": match.group(1),
                    "occupation_title": match.group(2),
                    "confidence": int(match.group(3)),
                    "flag_type": "MINOR",
                }
            )

    return updates


def _extract_data_quality(digest_content: str) -> Dict[str, Any]:
    """Extract DATA QUALITY section."""
    quality = {}

    dq_section = _extract_section(digest_content, r"## ⚙️ DATA QUALITY")
    if not dq_section:
        return quality

    quality["has_section"] = True

    # Extract freshness status
    if "Fresh" in dq_section:
        quality["freshness_status"] = "current"
    elif "Stale" in dq_section:
        quality["freshness_status"] = "stale"
    else:
        quality["freshness_status"] = "unknown"

    # Extract confidence level
    if "HIGH" in dq_section:
        quality["confidence_level"] = "HIGH"
    elif "MEDIUM" in dq_section:
        quality["confidence_level"] = "MEDIUM"
    elif "LOW" in dq_section:
        quality["confidence_level"] = "LOW"
    else:
        quality["confidence_level"] = "UNKNOWN"

    # Extract specific source status
    if "SkillSelect data:" in dq_section:
        if "✓" in dq_section:
            quality["skillselect_status"] = "loaded"
        else:
            quality["skillselect_status"] = "missing"

    return quality


def _extract_digest_date(filename: str) -> Optional[str]:
    """Extract date from digest filename (e.g., 2026-11-15_daily_digest.md)."""
    match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
    return match.group(1) if match else None


def _extract_digest_date_from_content(content: str) -> Optional[str]:
    """Extract date from digest title line."""
    match = re.search(r"# Daily Intelligence Digest — (\d{4}-\d{2}-\d{2})", content)
    return match.group(1) if match else None


def _classify_alert_type(change_description: str) -> str:
    """Classify alert type based on change description."""
    desc_lower = change_description.lower()

    if "tiebreak" in desc_lower or "cutoff" in desc_lower:
        return "cutoff_change"
    elif "status" in desc_lower:
        return "status_change"
    elif "invite" in desc_lower:
        return "invitation_change"
    elif "revert" in desc_lower:
        return "cutoff_revert"
    else:
        return "other_change"


def create_coordinator_case_context(
    case_id: str, occupation_code: str, points: int, digest: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a complete coordinator case context with intelligence injection.

    Convenience function for typical usage: create case + inject digest context.

    Args:
        case_id: Case identifier
        occupation_code: ANZSCO code (e.g., "261313")
        points: Candidate points
        digest: Parsed digest from load_daily_digest()

    Returns:
        Complete context dictionary ready for coordinator.case()
    """
    context = {
        "case_id": case_id,
        "occupation_code": occupation_code,
        "candidate_points": points,
    }

    # Inject intelligence
    context = inject_intelligence_context(context, digest)

    # Flag occupation impact
    impact = flag_occupation_impact(occupation_code, digest)
    if impact:
        context["occupation_impact"] = impact

    return context


if __name__ == "__main__":
    # Example usage for testing
    import sys

    if len(sys.argv) > 1:
        digest_path = sys.argv[1]
        try:
            digest = load_daily_digest(digest_path)
            print(f"✓ Loaded digest: {digest['digest_date']}")
            print(f"  Critical alerts: {len(digest['critical_alerts'])}")
            print(f"  Significant changes: {len(digest['significant_changes'])}")
            print(f"  Data freshness: {digest['data_quality'].get('freshness_status')}")
        except WorkflowIntegrationError as e:
            print(f"✗ Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python workflow_integration.py <digest_path>")
