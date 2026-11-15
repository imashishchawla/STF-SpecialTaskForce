"""
Data Scrapers for Australian visa intelligence.

This package provides production-ready scrapers for public endpoints:
- ACS (Australian Computer Society) MSA Info Hub
- Home Affairs (DHA) public endpoints:
  - Visa Finder
  - Skilled Occupation List
  - SkillSelect Invitation Rounds
  - Visa Listing
- State-specific immigration data for all 8 Australian states/territories:
  - Victoria, NSW, WA, QLD, SA, Tasmania, NT, ACT

All scrapers include resilience (retry logic, CSS + XPath fallbacks) and
comprehensive error handling.
"""

from .dha_scraper import DHAScraper

try:
    from .acs_poller import ACSPoller
except ImportError:
    ACSPoller = None

try:
    from .state_monitor import StateMonitor
except ImportError:
    StateMonitor = None

__all__ = ["DHAScraper"]
if ACSPoller:
    __all__.append("ACSPoller")
if StateMonitor:
    __all__.append("StateMonitor")
