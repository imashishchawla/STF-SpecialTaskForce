"""Authoritative registry of agent identities and routing policies."""

from pathlib import Path
from .contracts import ContractError

REGISTERED_AGENTS = {
    "master_migration_coordinator": {
        "role": "Master Migration Coordinator",
        "description": "Orchestrates discovery, task assignment, synthesizes findings, and enforces zero-leakage boundaries.",
        "entry_file": ".agents/master_migration_coordinator.md",
        "allowed_destinations": [
            "agent_pr_gsm_specialist",
            "agent_acs_evidence_auditor",
            "agent_partner_family_specialist",
            "agent_employer_sponsorship_specialist",
            "agent_student_visa_specialist",
            "agent_visitor_visa_specialist",
        ],
    },
    "agent_pr_gsm_specialist": {
        "role": "GSM / PR Specialist",
        "description": "Evaluates Subclasses 189, 190, 491 points testing and state/territory criteria.",
        "entry_file": ".agents/agent_pr_gsm_specialist.md",
        "allowed_destinations": ["master_migration_coordinator"],
    },
    "agent_acs_evidence_auditor": {
        "role": "ACS Evidence Auditor",
        "description": "Audits ICT degrees, work reference letters, and payment evidence per ACS guidelines.",
        "entry_file": ".agents/agent_acs_evidence_auditor.md",
        "allowed_destinations": ["master_migration_coordinator"],
    },
    "agent_partner_family_specialist": {
        "role": "Partner and Family Specialist",
        "description": "Evaluates relationship evidence, marriage records, and partner points eligibility.",
        "entry_file": ".agents/agent_partner_family_specialist.md",
        "allowed_destinations": ["master_migration_coordinator"],
    },
    "agent_employer_sponsorship_specialist": {
        "role": "Employer Sponsorship Specialist",
        "description": "Evaluates Subclasses 482, 186, and 494 work visa streams.",
        "entry_file": ".agents/agent_employer_sponsorship_specialist.md",
        "allowed_destinations": ["master_migration_coordinator"],
    },
    "agent_student_visa_specialist": {
        "role": "Student & Graduate Route Specialist",
        "description": "Evaluates Subclass 500 genuine student criteria and Subclass 485 post-study work streams.",
        "entry_file": ".agents/agent_student_visa_specialist.md",
        "allowed_destinations": ["master_migration_coordinator"],
    },
    "agent_visitor_visa_specialist": {
        "role": "Visitor Visa Specialist",
        "description": "Evaluates Subclass 600 tourist and business visitor genuine temporary stay requirements.",
        "entry_file": ".agents/agent_visitor_visa_specialist.md",
        "allowed_destinations": ["master_migration_coordinator"],
    },
}


def get_agent(agent_id: str) -> dict:
    """Retrieve registered agent details or raise ContractError."""
    if agent_id not in REGISTERED_AGENTS:
        raise ContractError(f"Unknown agent identity: '{agent_id}'")
    return REGISTERED_AGENTS[agent_id]


def is_valid_agent(agent_id: str) -> bool:
    """Check if agent_id is registered."""
    return agent_id in REGISTERED_AGENTS


def validate_route(from_agent: str, to_agent: str) -> bool:
    """Ensure message routing between agents adheres to allowed destinations."""
    sender = get_agent(from_agent)
    receiver = get_agent(to_agent)
    if to_agent not in sender["allowed_destinations"] and from_agent not in receiver["allowed_destinations"]:
        raise ContractError(f"Unauthorized routing: '{from_agent}' cannot send directly to '{to_agent}'")
    return True
