# STF — Special Task Force

STF is a repository for designing portable, human-governed agents. The first agent is the draft [Terraform Support Agent](portable/terraform-support-agent/README.md). Its Terraform-specific design, dashboard, and planning files live under `portable/terraform-support-agent/`; they are not duplicated at the repository root.

Start with [plan.md](plan.md) for the STF-wide architecture and roadmap. [AGENTS.md](AGENTS.md) gives contributor rules, and [security](docs/security.md) records approval boundaries. The Terraform agent's [active priority plan](portable/terraform-support-agent/plan/portability-readiness-plan.md) distinguishes implemented files from unverified installer and runtime behavior.

## Quick Start — Direct Terminal Installation

Install agents directly from your terminal using the GitHub installer URL:

```bash
# Preview installation (dry-run — no files written):
curl -fsSL https://raw.githubusercontent.com/imashishchawla/STF-SpecialTaskForce/main/install.sh | bash -s -- --agent terraform-support-agent --hosts bob --dry-run

# Direct install to host application (e.g. IBM Bob):
curl -fsSL https://raw.githubusercontent.com/imashishchawla/STF-SpecialTaskForce/main/install.sh | bash -s -- --agent terraform-support-agent --hosts bob
```

Or run interactively from a local clone:
```bash
git clone https://github.com/imashishchawla/STF-SpecialTaskForce.git
cd STF-SpecialTaskForce
bash install.sh
```

## Repository map

| Location | Purpose | Current state |
| :--- | :--- | :--- |
| `docs/` | Shared STF architecture, workflows, and security | Specifications |
| `portable/schemas/` | Shared bundle, agent, task, result, and trace contracts | Draft schemas |
| `portable/terraform-support-agent/` | Terraform agent source, optional A2A scaffold, installer, evaluations, design, and archived inputs | Phase 3b remediation active |
| `harness/`, `builder/`, `evals/` | Future mediation, builder, and platform-level evaluation interfaces | Design stubs |
| `install.sh` | Generic host-skill installer | Has a live copy path; preview with `--dry-run` |

The Terraform agent has its own `installer.sh`; its planned menu, package, update, removal, and release-verification behavior is listed in the active priority plan. A file existing in the repository does not establish that a portable release or A2A service has passed runtime verification.

## Portable library boundary

Approved bundles will be imported per destination account. Runtime-specific adapters must prove discovery and report what they can enforce. The portable source must exclude credentials, customer data, private memory, and raw traces. The network-device inventory in [plan.md](plan.md) is planning context and authorizes no device action.
