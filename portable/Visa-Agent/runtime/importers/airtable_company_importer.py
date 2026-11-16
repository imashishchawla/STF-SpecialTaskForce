#!/usr/bin/env python3
"""
Airtable Company Data Importer for Visa Agent

Imports Australian tech companies, locations, and tech stacks from Airtable.
Creates reference profiles and job market intelligence data.

Features:
- Parse Airtable company data
- Extract location and skill information
- Create occupation mappings
- Generate reference profiles
- Track employer demand by location
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.request import Request, urlopen
import csv
from io import StringIO

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
COMPANIES_DIR = KNOWLEDGE_DIR / "companies"
COMPANIES_DIR.mkdir(parents=True, exist_ok=True)

# Sample company data (parsed from Airtable)
SAMPLE_COMPANIES_DATA = """
Company,URL,Location,Skills
AirTasker,https://www.airtasker.com/careers/,"Sydney CBD, Sydney","Ruby, Ruby on Rails, NodeJs, Javascript, React, Java, Python or Golang"
Atlassian,https://www.atlassian.com/company/careers/sydney,"Sydney CBD, Sydney","Java, NodeJs, Javascript, React"
BCG Digital Ventures,https://careers.bcgdv.com/locations/sydney/,"Sydney CBD, Sydney","JavaScript, Angular, React, Hadoop, NoSQL"
BigCommerce,https://www.bigcommerce.com/careers/,"Sydney CBD, Sydney","Ruby, PHP, Javascript, Puppet"
Canva,https://www.canva.com/careers/,"Sydney CBD, Sydney","Java, Javascript, NodeJs, React, Typescript"
Deputy,https://www.deputy.com/au/careers,"Sydney CBD, Sydney","PHP, Javascript, Android, SQL"
Domain Group,https://domaingroup.csod.com/ux/ats/careersite/4/home?c=domaingroup,"Sydney CBD, Sydney","PHP, Javascript, Nodejs, React, Android, Python, C#, Swift"
Envato,https://envato.com/careers/,"Melbourne CBD, Melbourne","Ruby, Ruby on Rails, NodeJs, Elixir, React"
Expert360,https://expert360.com/company/careers,"Melbourne CBD, Melbourne; Sydney CBD, Sydney","Elixir, Javascript, React, GraphQL, Elasticsearch"
HealthEngine,https://careers.healthengine.com.au/opportunities/,"Perth CBD, Perth; Sydney CBD, Sydney","JavaScript, PHP, NodeJs, React, Symfony/Laravel, Java, Kotlin"
Healthshare,https://www.healthsharedigital.com/company/careers/,"Bondi Junction, Sydney","Python, Javascript, React"
HiPages,https://hipagesgroup.com.au/careers/,"Sydney CBD, Sydney","PHP, NodeJs, MySQL, Swift, Objective-C"
HireUp,https://hireup.com.au/careers/,"Greenwich, Sydney","NodeJs, Javascript, React, Mongo DB"
IRESS,https://www.iress.com/au/company/join-us/,"Melbourne CBD, Melbourne; Sydney CBD, Sydney","Reactjs, Python, JavaScript, TypeScript, AWS"
Learnosity,https://learnosity.com/company/careers/,"Sydney CBD, Sydney","PHP, Go, Javascript, MySQL, PostgreSQL, ElasticSearch, Redshift, AWS"
Lendi,https://lendi.recruiterbox.com/,"Sydney CBD, Sydney","Java, Scala, NodeJs, Javascript, SQL, Python"
Local Measure,https://www.localmeasure.com/company/careers,"Sydney CBD, Sydney","Python, Mongo, Javascript, AWS"
Oliver Wyman Labs,https://tech.labs.oliverwyman.com/ow-join/join-us/,"Sydney CBD, Sydney","Database, SQL, Hadoop, Python, NoSQL"
Optiver,https://www.optiver.com/ap/en/job-opportunities,"Sydney CBD, Sydney","C#, C++, Python"
Propeller,https://www.propelleraero.com/jobs/sydney/,"Sydney CBD, Sydney","Javascript, NodeJs, Python, Django, React, AWS, Kubernetes, Terraform"
Quantium,https://www.quantium.com/careers/,"Melbourne CBD, Melbourne; Sydney CBD, Sydney","Java, Scala, Javascript, NodeJs, postgres"
Qwilr,https://qwilr.com/jobs/,"Melbourne CBD, Melbourne; Sydney CBD, Sydney","MongoDB, Javascript, NodeJs, Angular, ReactJs"
REA Group,https://www.rea-group.com/careers/,"Dulwich, Adelaide; Fortitude Valley, Brisbane; Fyshwick, Canberra; Richmond, Melbourne; Subiaco, Perth; Sydney CBD, Sydney","Scala, Ruby, Javascript, NodeJs, React, Docker, Elasticsearch, AWS, Big Query"
Red Ant,https://redant.com.au/jobs/,"Sydney CBD, Sydney","Ruby, Ruby on Rails, Javascript, Angular"
Rockend,https://www.rockend.com/careers,"St Leonards, Sydney","C#, ASP.NET, Javascript, Angular"
SafetyCulture,https://safetyculture.com/careers/,"Sydney CBD, Sydney","GoLang, C++, Javascript, NodeJs"
SiteMinder,https://www.siteminder.com/jobs/,"Sydney CBD, Sydney","Javascript, Typescript, NodeJs, Vue, Ruby, GoLang, Java"
Spaceship,https://www.spaceship.com.au/careers,"Sydney CBD, Sydney","Go, Javascript, React"
SwitchMedia,https://www.switch.tv/careers/,"Sydney CBD, Sydney","PHP, Javascript, Go"
Tyro,https://www.tyro.com/careers/,"Sydney CBD, Sydney","Java, Scala, Kotlin, Kafka, Spark, AWS"
WiseTech Global,https://www.wisetechglobal.com/careers/current-openings,"Alexandria, Sydney","C#, .net, Javascirpt, Android, Sharepoint"
Zendesk,https://www.zendesk.com/jobs/melbourne/,"Melbourne CBD, Melbourne","Ruby, Scala, Python, Go, PHP, AWS, GCP, MySQL, Redis, Kafka, ELK, Cassandra, Memcache, Kubernetes, Hadoop, Chef, Terraform"
Zip,https://zip.co/careers,"Sydney CBD, Sydney",".net, Javascript, NodeJs, Angular, Python, AWS"
LegalVision,https://legalvision.com.au/careers/,"Sydney CBD, Sydney","PHP, Laravel, Javascript, AWS"
CSIRO's Data61,https://jobs.csiro.au/search/?q=data61&locationsearch=,"Brisbane CBD, Brisbane; Canberra CBD, Canberra; Melbourne CBD, Melbourne; Perth CBD, Perth; Sydney CBD, Sydney","Bigdata, C++, Drones, IOT, JavaScript, Machine Learning, Python, R"
Expedia Group,https://lifeatexpedia.com/jobs?location=Australia,"Brisbane City, Brisbane","Javascript, AWS, Java, React, Node"
Finder,https://www.finder.com.au/careers,"Sydney CBD, Sydney","PHP, JavaScript, NodeJs"
Elmo,https://elmosoftware.com.au/jobs/,"Sydney CBD, Sydney","PHP, .net, Javascript, Angular, AWS"
Papercut Software,https://www.papercut.com/about/careers/,"Camberwell, Melbourne","Java, Go, Javascript, GCP"
Koala,https://www.linkedin.com/company/koala-mattress/jobs/,"Alexandria, Sydney","Go, PHP, Javascript, AWS"
Split Payments,https://www.splitpayments.com.au/careers/,"Porter Street, Byron Bay","Ruby, Ruby on Rails, Javascript, Postgres, Redis, Sidekiq, AWS"
Pragmateam,https://pragma.team/talent#apply,"Sydney CBD, Sydney","Javascript, NodeJs, Angular, React"
GlamCorner,https://www.glamcorner.com.au/opportunities,"Alexandria, Sydney","Ruby, Javascript, Typescript, React, Docker, Jenkins, AWS, MySQL, Redis, PHP"
JXT Global,https://www.jxt.com.au/join-us,"Sydney CBD, Sydney",".NET, C#, React, Angular, AWS"
Kayo Sports,https://www.linkedin.com/company/kayo-sports/jobs/,"Artamon, Sydney","Javascript, NodeJs, Reactjs, Express.js"
RedBubble,https://careers.redbubble.com/jobs,"Melbourne CBD, Melbourne","Ruby, Ruby on Rails, Go, MySQL, NodeJS, ReactJS"
ClipChamp,https://clipchamp.com/en/company/careers,"Fortitude Valley, Brisbane","Javascript, Typescript, Angular, React, Python, C"
Easygo,https://easygo.io/careers/,"Melbourne CBD, Melbourne","JavaScript, NodeJs, React"
Isentia,https://www.isentia.com/careers/,"Sydney CBD, Sydney; Melbourne CBD, Melbourne","Nodejs, Angularjs, Python, AWS, Docker"
Brighte,https://brighte.com.au/careers/,"Sydney CBD, Sydney","PHP, MYSQL, Javascript, AWS"
DigIO,https://digio.com.au/current-opportunities/,"Melbourne CBD, Melbourne; Sydney CBD, Sydney","Java, Javascript, NodeJs, Kubernetes, AWS"
HeadUp Labs,https://www.headuplabs.com/careers,"Balaclava, Victoria","C#, Azure, Cosmos Db, Javascript, React Native, Typescript, Azure Functions"
Home Care Heroes,https://homecareheroes.com.au/careers,"Redfern, Sydney","Javascript, NodeJs, React, Ruby, Ruby on Rails, Rails, Docker"
Shippit,https://www.shippit.com/careers/,"Sydney CBD, Sydney","Ruby, Javascript, NodeJs, ReactJs, AWS"
Simply Wall St,https://simplywall.st/careers,"Surry Hills, Sydney","Javascript, Typescript, NodeJS, ReactJs"
Aiven,https://aiven.io/careers,"Sydney CBD, Sydney","Python, PostgreSQL, MySQL, Elasticsearch, Cassandra, Grafana, InfluxDB, Redis, Kafka"
DriveYello,https://www.driveyello.com/yello-jobs/,"Sydney CBD, Sydney","PHP, JavaScript, NodeJs, React, Python"
Harrison.Ai,https://www.harrison.ai/careers,"Sydney CBD, Sydney","Javascript, Typescript, Python, AWS, React"
MyCompany,https://example.com/jobs,"Melbourne CBD, Melbourne; Sydney CBD, Sydney","PHP, JavaScript, Android, SQL"
Rokt,https://www.rokt.com/careers,"Surry Hills, Sydney","C#, ASP.NET, JavaScript, React, Angular, Go, ML, AWS, Kubernetes, Terraform"
SquareUp,https://careers.squareup.com/,"Melbourne, Sydney","CI/CD, AWS, Data Analyst, DevOps"
"""


class AirtableCompanyImporter:
    """Import and process Australian tech company data."""

    # Skill to occupation code mapping
    SKILL_OCCUPATION_MAPPING = {
        "javascript": "261313",  # Software Engineer
        "react": "261313",       # Software Engineer
        "nodejs": "261313",      # Software Engineer
        "python": "261313",      # Software Engineer
        "java": "261313",        # Software Engineer
        "c#": "261313",          # Software Engineer
        "go": "261313",          # Software Engineer
        "php": "261313",         # Software Engineer
        "ruby": "261313",        # Software Engineer
        "typescript": "261313",  # Software Engineer
        "angular": "261313",     # Software Engineer
        "kubernetes": "263111",  # Systems Administrator
        "devops": "263111",      # Systems Administrator
        "aws": "263111",         # Systems Administrator
        "gcp": "263111",         # Systems Administrator
        "docker": "263111",      # Systems Administrator
        "terraform": "263111",   # Systems Administrator
        "sql": "254411",         # Database Administrator
        "postgres": "254411",    # Database Administrator
        "mysql": "254411",       # Database Administrator
        "mongodb": "254411",     # Database Administrator
        "elasticsearch": "254411", # Database Administrator
        "redis": "254411",       # Database Administrator
    }

    # State mapping
    LOCATION_STATE_MAPPING = {
        "sydney": "NSW",
        "nsw": "NSW",
        "melbourne": "VIC",
        "vic": "VIC",
        "brisbane": "QLD",
        "qld": "QLD",
        "perth": "WA",
        "wa": "WA",
        "adelaide": "SA",
        "sa": "SA",
        "hobart": "TAS",
        "tas": "TAS",
        "darwin": "NT",
        "nt": "NT",
        "canberra": "ACT",
        "act": "ACT",
        "byron bay": "NSW",
    }

    def __init__(self):
        """Initialize importer."""
        self.companies = []
        self.skills_index = {}
        self.location_index = {}
        self.occupation_index = {}

    def parse_companies(self, csv_data: str) -> List[Dict[str, Any]]:
        """Parse CSV company data."""
        companies = []
        reader = csv.DictReader(StringIO(csv_data))

        for row in reader:
            if not row.get("Company"):
                continue

            # Parse locations
            locations = [loc.strip() for loc in row.get("Location", "").split(";")]

            # Parse skills
            skills = [skill.strip() for skill in row.get("Skills", "").split(",")]

            company = {
                "name": row["Company"],
                "url": row.get("URL", ""),
                "locations": locations,
                "skills": skills,
                "states": self._extract_states(locations),
                "occupation_codes": self._map_occupations(skills),
            }
            companies.append(company)

        return companies

    def _extract_states(self, locations: List[str]) -> List[str]:
        """Extract state codes from locations."""
        states = set()
        for location in locations:
            location_lower = location.lower()
            for keyword, state in self.LOCATION_STATE_MAPPING.items():
                if keyword in location_lower:
                    states.add(state)
        return sorted(list(states))

    def _map_occupations(self, skills: List[str]) -> List[str]:
        """Map skills to occupation codes."""
        occupations = set()
        for skill in skills:
            skill_lower = skill.lower().strip()
            occupation = self.SKILL_OCCUPATION_MAPPING.get(skill_lower)
            if occupation:
                occupations.add(occupation)
        return sorted(list(occupations))

    def build_indices(self, companies: List[Dict[str, Any]]) -> None:
        """Build search indices."""
        # Skills index: skill -> companies with that skill
        for company in companies:
            for skill in company["skills"]:
                skill_lower = skill.lower()
                if skill_lower not in self.skills_index:
                    self.skills_index[skill_lower] = []
                self.skills_index[skill_lower].append(company["name"])

        # Location index: state -> companies in that state
        for company in companies:
            for state in company["states"]:
                if state not in self.location_index:
                    self.location_index[state] = []
                self.location_index[state].append(company["name"])

        # Occupation index: occupation code -> companies hiring for that role
        for company in companies:
            for occupation in company["occupation_codes"]:
                if occupation not in self.occupation_index:
                    self.occupation_index[occupation] = []
                self.occupation_index[occupation].append(company["name"])

    def save_companies(self, companies: List[Dict[str, Any]]) -> str:
        """Save companies to JSON."""
        output_file = COMPANIES_DIR / "tech_companies_2026-11-16.json"

        data = {
            "metadata": {
                "source": "Airtable shared view",
                "import_date": datetime.now(timezone.utc).isoformat(),
                "total_companies": len(companies),
                "states_covered": len(self.location_index),
                "occupations_mapped": len(self.occupation_index),
            },
            "companies": companies,
            "indices": {
                "skills": {skill: len(companies) for skill, companies in self.skills_index.items()},
                "locations": {state: len(companies) for state, companies in self.location_index.items()},
                "occupations": {occ: len(companies) for occ, companies in self.occupation_index.items()},
            }
        }

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        return str(output_file)

    def generate_report(self, companies: List[Dict[str, Any]]) -> str:
        """Generate import report."""
        report = f"""
# Airtable Company Data Import Report

**Import Date:** {datetime.now(timezone.utc).isoformat()}
**Total Companies:** {len(companies)}

## Geographic Distribution

| State | Companies | Examples |
|-------|-----------|----------|
"""
        for state in sorted(self.location_index.keys()):
            companies_in_state = self.location_index[state]
            examples = ", ".join(companies_in_state[:3])
            report += f"| {state} | {len(companies_in_state)} | {examples} |\n"

        report += f"""
## Top Skills in Demand

| Skill | Companies | Count |
|-------|-----------|-------|
"""
        sorted_skills = sorted(self.skills_index.items(),
                              key=lambda x: len(x[1]),
                              reverse=True)[:15]
        for skill, companies_with_skill in sorted_skills:
            report += f"| {skill.title()} | {len(companies_with_skill)} | {', '.join(companies_with_skill[:2])} |\n"

        report += f"""
## Occupation Mapping

| ANZSCO Code | Occupation | Companies |
|-------------|-----------|-----------|
"""
        OCCUPATION_TITLES = {
            "261313": "Software Engineer",
            "263111": "Systems Administrator",
            "254411": "Database Administrator",
        }

        for code in sorted(self.occupation_index.keys()):
            title = OCCUPATION_TITLES.get(code, "Unknown")
            companies_count = len(self.occupation_index[code])
            report += f"| {code} | {title} | {companies_count} |\n"

        report += f"""
## Visa Pathway Analysis

Based on this data:
- **High Demand Roles:** Software Engineer (261313) - {len(self.occupation_index.get('261313', []))} companies
- **Infrastructure Roles:** Systems Administrator (263111) - {len(self.occupation_index.get('263111', []))} companies
- **Data Roles:** Database Administrator (254411) - {len(self.occupation_index.get('254411', []))} companies

**Points Impact:**
- Occupations in high-demand areas = +5 bonus points
- Multiple skill matches = Higher visa success likelihood
- State sponsorship available in most states

## Next Steps

1. Match candidate skills against company requirements
2. Identify best visa pathways by location
3. Create personalized route sequences
4. Track skill-to-visa-success mapping
"""
        return report


def main():
    """Run importer."""
    print("=" * 60)
    print("Airtable Company Data Importer")
    print("=" * 60)

    # Read CSV from file
    csv_file = COMPANIES_DIR / "companies_raw.csv"
    if csv_file.exists():
        with open(csv_file, 'r') as f:
            csv_data = f.read()
    else:
        csv_data = SAMPLE_COMPANIES_DATA

    # Parse data
    importer = AirtableCompanyImporter()
    companies = importer.parse_companies(csv_data)

    print(f"\n✓ Parsed {len(companies)} companies")

    # Build indices
    importer.build_indices(companies)
    print(f"✓ Built indices:")
    print(f"  - {len(importer.skills_index)} unique skills")
    print(f"  - {len(importer.location_index)} states")
    print(f"  - {len(importer.occupation_index)} occupation codes")

    # Save data
    output_file = importer.save_companies(companies)
    print(f"✓ Saved to: {output_file}")

    # Generate report
    report = importer.generate_report(companies)
    report_file = COMPANIES_DIR / "import_report_2026-11-16.md"
    with open(report_file, "w") as f:
        f.write(report)
    print(f"✓ Report: {report_file}")

    print("\n" + "=" * 60)
    print("✓ IMPORT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
