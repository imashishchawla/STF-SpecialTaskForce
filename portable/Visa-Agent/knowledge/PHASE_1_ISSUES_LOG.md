# Phase 1 Issues & Action Items Log

**Generated:** 2026-11-16  
**Test Run:** Manual verification of Phase 1 scrapers  

---

## Critical Blockers

### BLOCKER-001: DHA Scraper Cannot Extract Visa Data

**Priority:** BLOCKER / P0  
**Status:** OPEN  
**Assigned:** DHA Scraper Team  

#### Description
DHA scraper successfully fetches HTML from all 4 Home Affairs endpoints but fails to extract any visa/occupation data. Parser returns 0 rows for:
- Visa Finder endpoint
- Occupation List endpoint  
- SkillSelect Rounds endpoint
- Visa Listing endpoint

#### Root Cause Analysis
Home Affairs website uses JavaScript framework (React/Vue/Next.js) to render visa data client-side. The current scraper uses BeautifulSoup for static HTML parsing, which cannot access dynamically rendered content.

**Evidence:**
- HTML inspection shows ~1.3MB of JavaScript code
- No visa data in initial HTML payload
- Page has `<noscript>` fallback (indicates JS requirement)
- CSS selectors like `div.visa-card` find 0 elements

#### Impact
- Cannot monitor visa changes on official Home Affairs portal
- Intelligence Digester receives 0 visa data
- Reference profile testing cannot verify visa impacts

#### Resolution Options (Ranked by Feasibility)

1. **Implement Browser Rendering (RECOMMENDED)**
   - Use Playwright or Puppeteer to render JavaScript
   - Effort: Medium (3-5 hours implementation + testing)
   - Reliability: High
   - Cost: Minimal (headless browser)

2. **Find Alternative API Endpoint**
   - Check if Home Affairs offers public API or data feed
   - Effort: Low (1-2 hours investigation)
   - Reliability: Depends on API availability
   - Cost: None

3. **Use RSS Feeds or News Aggregators**
   - Monitor RSS feeds from Home Affairs news
   - Effort: Low
   - Reliability: May miss granular visa data
   - Cost: None

4. **Implement Hybrid Approach**
   - Use browser rendering for visa data
   - Fall back to alternative source if rendering fails
   - Effort: Medium
   - Reliability: High

#### Suggested Fix (Priority Order)
1. Investigate Home Affairs API availability (1 hour)
2. If no API, implement Playwright rendering (4 hours)
3. Add fallback to alternative source (2 hours)
4. Comprehensive testing (2 hours)

**Estimated Resolution Time:** 1-2 days  
**Estimated Effort:** 40-60 development hours  

---

### BLOCKER-002: State Monitor URLs Outdated/Invalid

**Priority:** BLOCKER / P0  
**Status:** OPEN  
**Assigned:** State Monitor Team  

#### Description
4 out of 8 state portals return errors:

| State | URL | Error | Status |
|-------|-----|-------|--------|
| Victoria (VIC) | https://immi.vic.gov.au/ | DNS resolution failure | Domain doesn't resolve |
| NSW | https://www.nsw.gov.au/business-and-economy/skilled-migration | HTTP 404 | Endpoint moved/removed |
| Western Australia (WA) | https://www.wa.gov.au/government/migration | HTTP 404 | Endpoint moved/removed |
| Queensland (QLD) | https://www.findazjob.qld.gov.au/nominationskill | DNS resolution failure | Domain doesn't resolve |

#### Root Cause Analysis
Hardcoded state URLs in `runtime/scrapers/state_monitor.py` are outdated or point to invalid endpoints. URLs may be:
- Migrated to different domain
- Restructured within state websites
- Deprecated in favor of new portals
- Regional aliases not accessible from test environment

#### Impact
- 50% of state nominators unreachable
- Cannot monitor nomination quotas for VIC, NSW, WA, QLD
- Reference profiles for these states cannot be validated

#### Resolution Steps

1. **URL Verification (IMMEDIATE)**
   - Manually verify correct URLs for each state:
     - VIC: Check https://immi.vic.gov.au/ alternatives or main portal
     - NSW: Find current skilled migration endpoint on nsw.gov.au
     - WA: Find current migration portal on wa.gov.au
     - QLD: Find current nomination skill endpoint
   - Document correct URLs with working status

2. **Code Update**
   - Update STATES dict in state_monitor.py with verified URLs
   - Add fallback URLs for each state
   - Test each URL returns HTTP 200

3. **Testing**
   - Verify parsing works for each state
   - Confirm occupation data extraction
   - Document expected data format per state

4. **Error Handling**
   - Implement better error messages
   - Add state-specific logging
   - Monitor for future URL changes

**Verified Working States:**
- ✓ South Australia (SA): https://migration.sa.gov.au/
- ✓ Northern Territory (NT): https://migration.nt.gov.au/
- ✓ Australian Capital Territory (ACT): https://www.act.gov.au/
- ⚠ Tasmania (TAS): HTTP 403 but has fallback

**Estimated Resolution Time:** 4-8 hours  
**Estimated Effort:** 20-30 development hours  

---

## Major Issues

### ISSUE-003: State Monitor Parsing Unreliable

**Priority:** MAJOR / P1  
**Status:** OPEN  
**Assigned:** State Monitor Team  

#### Description
Even for working state URLs, occupation data extraction is inconsistent:
- South Australia: 3 occupations extracted
- Tasmania: 2 occupations (with fallback)
- NT: 3 occupations
- ACT: 3 occupations

These low counts suggest parsing may be missing data or pages use different HTML structures per state.

#### Root Cause
State websites have different designs and HTML structures. Single CSS selector strategy doesn't work across all states.

#### Solution
- Implement state-specific parsers
- Add occupation count validation
- Compare against official state portal counts manually

**Estimated Resolution Time:** 1-2 days

---

### ISSUE-004: ACS Poller Using Fallback Defaults

**Priority:** MAJOR / P1  
**Status:** OPEN  
**Assigned:** ACS Scraper Team  

#### Description
ACS poller returns default fee values rather than scraping from live data:

**Returned:**
- Bachelor: $600 (default)
- Masters: $550 (default)
- CDR Processing: 6 weeks (default)

**Cannot verify** against official ACS rates as parser doesn't extract actual values from page.

#### Root Cause
ACS MSA Info Hub page uses JavaScript or complex HTML structure that current parser cannot extract. Parser falls back to hardcoded defaults.

#### Solution
- Implement JavaScript rendering for ACS page
- Or find alternative ACS API/data source
- Validate extracted fees against official ACS website

**Estimated Resolution Time:** 1 day

---

## Minor Issues

### ISSUE-005: No Stale Data Available for Fallback

**Priority:** MINOR / P2  
**Status:** ACKNOWLEDGED  
**Assigned:** DHA Scraper Team  

#### Description
DHA scraper designed to fall back to most recent JSON snapshot if fetch fails. However, no historical snapshots exist yet. First failure will have no fallback.

#### Solution
- Expected once scraper runs multiple days
- Recommend running daily for stability
- Add manual bootstrap snapshots if needed

---

### ISSUE-006: Intelligence Digester 2-Day Rule May Be Too Conservative

**Priority:** MINOR / P2  
**Status:** ACKNOWLEDGED  
**Assigned:** Digester Team  

#### Description
2-day confirmation rule prevents any anomalies from being marked CRITICAL on first detection. In test run:
- 20 occupations detected as changed
- 0 marked as CRITICAL (2-day rule prevented confirmation)
- 5 marked SIGNIFICANT
- 15 marked MINOR

This is working as designed but may delay critical alert generation by up to 48 hours.

#### Impact
- Slow response to real visa changes
- May miss time-sensitive occupation changes

#### Solution
- Consider 1-day confirmation for high-importance occupations
- Implement urgency scoring for common visa codes
- Current 2-day rule is conservative but safe

---

## Recommendations Summary

### Phase 1 Release Criteria (MUST FIX)

- [ ] BLOCKER-001: DHA parser can extract visa data (>100 rows)
- [ ] BLOCKER-002: All 8 state monitors return HTTP 200
- [ ] ISSUE-003: State parsing validated (>5 occupations per state)
- [ ] ISSUE-004: ACS fees scraped from live source (not defaults)

### Phase 1 Testing Criteria (NICE TO HAVE)

- [ ] Stale data fallback tested (run scraper 2 days)
- [ ] Anomaly detection validated against known changes
- [ ] CRITICAL alert routing tested with actual data
- [ ] Processing time < 5 minutes for full pipeline

---

## Action Items by Team

### DHA Scraper Team
- [ ] Investigate Home Affairs API availability
- [ ] Design JavaScript rendering solution
- [ ] Implement browser-based scraper
- [ ] Test against 4 endpoints
- [ ] Validate occupations against SOL
- [ ] Document alternative data sources

### State Monitor Team
- [ ] Verify correct URLs for VIC, NSW, WA, QLD
- [ ] Update STATES configuration
- [ ] Test all 8 states return data
- [ ] Implement state-specific parsers if needed
- [ ] Document parsing rules per state
- [ ] Add occupations count validation

### ACS Poller Team
- [ ] Verify current ACS fees from official website
- [ ] Fix fee extraction (not using defaults)
- [ ] Add JavaScript rendering if needed
- [ ] Test fee extraction accuracy
- [ ] Document expected fee ranges

### Digester Team
- [ ] Monitor anomaly detection accuracy
- [ ] Consider 1-day rule for high-priority occupations
- [ ] Add anomaly validation metrics
- [ ] Document confidence scoring rules

---

## Test Coverage Checklist

- [x] DHA Scraper: 4/4 endpoints fetched
- [x] DHA Scraper: Network connectivity verified (headers fixed)
- [ ] DHA Scraper: Data parsing working (0/4 - BLOCKER)
- [ ] State Monitor: All 8 states fetching (4/8 - BLOCKER)
- [x] ACS Poller: All 4 components functional
- [ ] ACS Poller: Live data extraction (fees using defaults)
- [x] Digester: Full pipeline operational
- [ ] Digester: Anomaly detection validated
- [ ] Integration: DHA → Digester data flow
- [ ] Integration: State → Digester data flow
- [ ] End-to-end: Reference profile testing

---

## Next Steps

1. **Week 1:** Fix BLOCKER-001 and BLOCKER-002
2. **Week 2:** Test Phase 1 with blockers fixed
3. **Week 3:** Reference profile testing with real data
4. **Week 4:** Production deployment

---

**Last Updated:** 2026-11-16 00:30 UTC  
**Next Review:** 2026-11-17 (after fixes)
